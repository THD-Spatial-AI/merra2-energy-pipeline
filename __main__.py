"""CLI entry point for the MERRA-2 data pipeline.

Usage (from inside data_pipeline/):
    make pv 2019 germany
    make pv 2019 2020 germany
    make wind 2019 2022 europe
    make biomass 2019 germany
    make geothermal 2019 germany

Or directly:
    python -m data_pipeline pv 2019 germany
    python -m data_pipeline pv 2019 2020 germany
    python -m data_pipeline pv 2023 2023 austria --skip-download
    python -m data_pipeline biomass 2019 germany
    python -m data_pipeline geothermal 2019 germany
"""

import argparse
import logging
import sys
import os

from .countries import (
    get_bbox,
    get_timezone,
    list_countries,
    normalize_country,
)
from .config import DEFAULT_OUTPUT_DIR, DEFAULT_RAW_DIR, PACKAGE_DIR


def setup_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
    )


def main():
    parser = argparse.ArgumentParser(
        description='MERRA-2 Data Pipeline for PV, Wind, Biomass, and Geothermal Simulations',
        usage='python -m data_pipeline <type> <year> <country>\n'
              '       python -m data_pipeline <type> <start_year> <end_year> <country>',
    )
    parser.add_argument('type', choices=['pv', 'wind', 'biomass', 'geothermal'],
                        help='Simulation type')
    parser.add_argument('start_year', type=int,
                        help='Start year (or single year)')
    parser.add_argument('end_year_or_country',
                        help='End year (if 4 args) or country (if 3 args)')
    parser.add_argument('country', nargs='?', default=None,
                        help='Country name (e.g., germany, france, europe)')
    parser.add_argument('--output-dir', default=DEFAULT_OUTPUT_DIR,
                        help='Output directory for combined files')
    parser.add_argument('--raw-dir', default=DEFAULT_RAW_DIR,
                        help='Directory for raw downloaded files')
    parser.add_argument('--workers', type=int, default=4,
                        help='Number of parallel download threads')
    parser.add_argument('--skip-download', action='store_true',
                        help='Skip download step (use existing raw files)')
    parser.add_argument('--skip-combine', action='store_true',
                        help='Skip combine step (download only)')
    parser.add_argument('--allow-missing-days', action='store_true',
                        help='Keep yearly outputs even when some source days '
                             'are missing')
    parser.add_argument('--list-countries', action='store_true',
                        help='List all supported countries and exit')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose logging')

    # Handle --list-countries before requiring positional args
    if '--list-countries' in sys.argv:
        for c in list_countries():
            print(c)
        sys.exit(0)

    args = parser.parse_args()

    # Resolve flexible positional args: 3-arg or 4-arg form
    if args.country is None:
        # 3-arg form: type year country (end_year_or_country is the country)
        args.end_year = args.start_year
        args.country = args.end_year_or_country
    else:
        # 4-arg form: type start_year end_year country
        try:
            args.end_year = int(args.end_year_or_country)
        except ValueError:
            parser.error(
                f"Invalid end_year: '{args.end_year_or_country}'. "
                "Usage: <type> <start_year> [end_year] <country>"
            )

    args.country_key = normalize_country(args.country)

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Credentials come from data_pipeline/.env (loaded by config.py)
    username = os.getenv('EARTHDATA_USERNAME', '')
    password = os.getenv('EARTHDATA_PASSWORD', '')

    if not args.skip_download and (not username or not password):
        env_path = PACKAGE_DIR / '.env'
        logger.error('NASA EarthData credentials not found.')
        logger.error(
            f'Set EARTHDATA_USERNAME and EARTHDATA_PASSWORD in {env_path}'
        )
        logger.error(
            'Create an account at https://urs.earthdata.nasa.gov/users/new'
        )
        sys.exit(1)

    # Validate country
    try:
        bbox = get_bbox(args.country_key)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    logger.info(
        f'Pipeline: {args.type.upper()} | '
        f'{args.start_year}-{args.end_year} | {args.country}'
    )
    logger.info(f'Bounding box (lon_min, lat_min, lon_max, lat_max): {bbox}')

    # Each sim type gets its own raw and output subdirectory
    # so different variable sets don't collide.
    raw_dir = os.path.join(args.raw_dir, args.type, args.country_key)
    output_dir = os.path.join(args.output_dir, args.type, args.country_key)

    had_errors = False
    combined_years = []

    # Step 1: Download
    if not args.skip_download:
        from .download import download_merra_data

        logger.info('=== Step 1: Downloading MERRA-2 data ===')
        success, failed = download_merra_data(
            sim_type=args.type,
            start_year=args.start_year,
            end_year=args.end_year,
            bbox=bbox,
            output_dir=raw_dir,
            username=username,
            password=password,
            max_workers=args.workers,
        )
        logger.info(f'Download complete: {success} succeeded, {failed} failed')
        if failed > 0:
            had_errors = True
            logger.warning(
                'Some files failed to download. Re-run to retry '
                '(existing files are skipped).'
            )

    # Step 2: Combine into yearly files
    if not args.skip_combine:
        from .combine import combine_yearly, export_weather_csvs

        logger.info('=== Step 2: Combining into yearly files ===')
        for year in range(args.start_year, args.end_year + 1):
            try:
                out_path = combine_yearly(
                    sim_type=args.type,
                    year=year,
                    raw_dir=raw_dir,
                    output_dir=output_dir,
                    fail_on_missing_days=not args.allow_missing_days,
                )
                logger.info(f'Year {year}: {out_path}')
                combined_years.append(year)
            except Exception as e:
                had_errors = True
                logger.error(f'Failed to combine year {year}: {e}')

        # Step 3: Export per-grid-point weather CSVs (biomass/geothermal)
        if args.type in ('biomass', 'geothermal'):
            logger.info(
                '=== Step 3: Exporting per-grid-point weather CSVs ==='
            )
            tz_offset = get_timezone(args.country_key)
            for year in combined_years:
                try:
                    nc_path = os.path.join(
                        output_dir, f'combined_merra_{year}.nc'
                    )
                    count = export_weather_csvs(
                        nc_path=nc_path,
                        year=year,
                        output_dir=output_dir,
                        tz_offset=tz_offset,
                    )
                    logger.info(
                        f'Year {year}: exported {count} weather CSV files'
                    )
                except Exception as e:
                    had_errors = True
                    logger.error(
                        f'Failed to export CSVs for year {year}: {e}'
                    )

    if had_errors:
        logger.error('Pipeline finished with errors.')
        return 1

    logger.info('Pipeline complete!')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
