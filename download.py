"""Download MERRA-2 data from NASA GES DISC via OPeNDAP.

Uses NASA EarthData authentication to download subsetted MERRA-2 data
for specific variables and geographic regions.
"""

import os
import logging
import time
import threading
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

try:
    from tqdm import tqdm
except ImportError:
    # Fallback if tqdm is not installed
    class tqdm:
        def __init__(self, *args, **kwargs):
            self.total = kwargs.get('total', 0)
            self.n = 0
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def update(self, n=1):
            self.n += n

from .config import (
    OPENDAP_BASE_URL, COLLECTIONS, FILE_TEMPLATES, VARIABLES,
    MERRA_LAT_MIN, MERRA_LAT_STEP, MERRA_LON_MIN, MERRA_LON_STEP,
    MAX_WORKERS, CHUNK_SIZE, MAX_RETRIES, RETRY_DELAY,
)

logger = logging.getLogger(__name__)
_thread_local = threading.local()


def _get_thread_session(username, password):
    """Get a thread-local authenticated session."""
    creds = (username, password)
    session = getattr(_thread_local, 'session', None)
    current_creds = getattr(_thread_local, 'credentials', None)
    if session is None or current_creds != creds:
        session = EarthDataSession(username, password)
        _thread_local.session = session
        _thread_local.credentials = creds
    return session


class EarthDataSession(requests.Session):
    """Session that preserves auth headers for NASA EarthData redirects.

    NASA GES DISC redirects to urs.earthdata.nasa.gov for authentication.
    Standard requests.Session strips Authorization on cross-domain redirects.
    This subclass keeps it when redirecting to/from the EarthData auth host.
    """

    AUTH_HOST = 'urs.earthdata.nasa.gov'

    def __init__(self, username, password):
        super().__init__()
        self.auth = (username, password)

    def rebuild_auth(self, prepared_request, response):
        headers = prepared_request.headers
        url = prepared_request.url

        if 'Authorization' in headers:
            original_parsed = requests.utils.urlparse(response.request.url)
            redirect_parsed = requests.utils.urlparse(url)

            if (original_parsed.hostname != redirect_parsed.hostname
                    and redirect_parsed.hostname != self.AUTH_HOST
                    and original_parsed.hostname != self.AUTH_HOST):
                del headers['Authorization']


def get_stream_number(d):
    """Get MERRA-2 stream number for a given date.

    MERRA-2 uses different stream IDs for different time periods:
      100: 1980-1991, 200: 1992-2000, 300: 2001-2010, 400: 2011+
    Stream 401 is used only for specific reprocessed months:
      2020-09, 2021-06, 2021-07, 2021-08, 2021-09
    """
    year = d.year
    month = d.month
    if year < 1992:
        return '100'
    elif year < 2001:
        return '200'
    elif year < 2011:
        return '300'
    elif (year == 2020 and month == 9) or (year == 2021 and month in (6, 7, 8, 9)):
        return '401'
    return '400'


def lat_to_index(lat):
    """Convert latitude to MERRA-2 grid index."""
    return int(round((lat - MERRA_LAT_MIN) / MERRA_LAT_STEP))


def lon_to_index(lon):
    """Convert longitude to MERRA-2 grid index."""
    return int(round((lon - MERRA_LON_MIN) / MERRA_LON_STEP))


def build_opendap_url(collection_key, d, variables, bbox):
    """Build an OPeNDAP subset URL for downloading one day of MERRA-2 data.

    Args:
        collection_key: 'slv' or 'rad'
        d: date object
        variables: list of variable names to include
        bbox: (lon_min, lat_min, lon_max, lat_max)

    Returns:
        Full OPeNDAP URL with subset constraint expression.
    """
    import math
    lon_min, lat_min, lon_max, lat_max = bbox

    # Ensure bounding box points are strictly inclusive
    lat_start = int(math.floor((lat_min - MERRA_LAT_MIN) / MERRA_LAT_STEP))
    lat_end = int(math.ceil((lat_max - MERRA_LAT_MIN) / MERRA_LAT_STEP))
    lon_start = int(math.floor((lon_min - MERRA_LON_MIN) / MERRA_LON_STEP))
    lon_end = int(math.ceil((lon_max - MERRA_LON_MIN) / MERRA_LON_STEP))

    stream = get_stream_number(d)
    date_str = d.strftime('%Y%m%d')
    year_str = d.strftime('%Y')
    month_str = d.strftime('%m')

    filename = FILE_TEMPLATES[collection_key].format(
        stream=stream, date=date_str
    )
    collection = COLLECTIONS[collection_key]

    # Build OPeNDAP constraint expression
    parts = []
    for var in variables:
        parts.append(
            f'{var}[0:23][{lat_start}:{lat_end}][{lon_start}:{lon_end}]'
        )
    # Include coordinate variables
    parts.append(f'lat[{lat_start}:{lat_end}]')
    parts.append(f'lon[{lon_start}:{lon_end}]')
    parts.append('time[0:23]')

    constraint = ','.join(parts)

    # .nc4 suffix requests NetCDF4 binary format from OPeNDAP
    return (
        f'{OPENDAP_BASE_URL}/{collection}/{year_str}/{month_str}/'
        f'{filename}.nc4?{constraint}'
    )


def generate_dates(start_year, end_year):
    """Generate all dates for the given year range."""
    dates = []
    for year in range(start_year, end_year + 1):
        d = date(year, 1, 1)
        end = date(year, 12, 31)
        while d <= end:
            dates.append(d)
            d += timedelta(days=1)
    return dates


def download_file(url, output_path, username, password):
    """Download a single file with retry logic. Skips if already exists."""
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return output_path

    for attempt in range(MAX_RETRIES):
        try:
            session = _get_thread_session(username, password)
            response = session.get(url, stream=True, timeout=120)
            response.raise_for_status()

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    f.write(chunk)

            return output_path

        except (requests.RequestException, IOError) as e:
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAY * (attempt + 1)
                logger.warning(
                    f'Retry {attempt + 1}/{MAX_RETRIES} for '
                    f'{os.path.basename(output_path)}: {e}'
                )
                time.sleep(wait)
            else:
                logger.error(
                    f'Failed to download {os.path.basename(output_path)}: {e}'
                )
                if os.path.exists(output_path):
                    os.remove(output_path)
                raise


def download_merra_data(
    sim_type, start_year, end_year, bbox,
    output_dir, username, password, max_workers=MAX_WORKERS
):
    """Download MERRA-2 data for a simulation type and region.

    Args:
        sim_type: 'pv' or 'wind'
        start_year: start year (inclusive)
        end_year: end year (inclusive)
        bbox: (lon_min, lat_min, lon_max, lat_max)
        output_dir: base directory for raw downloaded files
        username: NASA EarthData username
        password: NASA EarthData password
        max_workers: number of parallel download threads

    Returns:
        Tuple of (success_count, failure_count).
    """
    variables = VARIABLES[sim_type]
    dates = generate_dates(start_year, end_year)
    download_tasks = []

    for collection_key, var_list in variables.items():
        if not var_list:
            continue

        collection_dir = os.path.join(output_dir, collection_key)
        os.makedirs(collection_dir, exist_ok=True)

        for d in dates:
            url = build_opendap_url(collection_key, d, var_list, bbox)
            date_str = d.strftime('%Y%m%d')
            filename = f'merra2_{collection_key}_{date_str}.nc4'
            output_path = os.path.join(collection_dir, filename)
            download_tasks.append((url, output_path))

    total_files = len(download_tasks)
    logger.info(
        f'Downloading {total_files} files for {sim_type} '
        f'({start_year}-{end_year})'
    )

    failed = []

    with tqdm(total=total_files, desc='Downloading', unit='file') as pbar:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    download_file, url, path, username, password
                ): (url, path)
                for url, path in download_tasks
            }

            for future in as_completed(futures):
                url, path = futures[future]
                try:
                    future.result()
                except Exception as e:
                    failed.append((url, str(e)))
                pbar.update(1)

    if failed:
        logger.warning(f'{len(failed)} files failed to download:')
        for url, err in failed[:10]:
            logger.warning(f'  {os.path.basename(url)}: {err}')
        if len(failed) > 10:
            logger.warning(f'  ... and {len(failed) - 10} more')

    return total_files - len(failed), len(failed)
