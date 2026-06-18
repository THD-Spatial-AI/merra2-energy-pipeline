"""Combine daily MERRA-2 files into yearly NetCDF4 datasets.

Produces output compatible with the existing PV/wind simulation code:
  - Dimensions: [lat, lon, time]
  - Time: 8760 hours (non-leap) or 8784 hours (leap year)
  - Global attribute 'year' set on the dataset

For biomass/geothermal: also exports per-grid-point weather CSV files
with Temperature (°C), Pressure (hPa), and Relative Humidity (%).
"""

import os
import logging
from datetime import datetime
from calendar import isleap

import numpy as np
import pandas as pd
from netCDF4 import Dataset

from .config import VARIABLES

logger = logging.getLogger(__name__)


def combine_yearly(
    sim_type, year, raw_dir, output_dir, fail_on_missing_days=True
):
    """Combine daily MERRA-2 files into a single yearly NetCDF4 file.

    Args:
        sim_type: 'pv', 'wind', 'biomass', or 'geothermal'
        year: year to combine
        raw_dir: directory with downloaded files (containing slv/ and rad/ subdirs)
        output_dir: directory for the combined output file
        fail_on_missing_days: if True, treat missing input days as fatal
            and remove the incomplete combined output file.

    Returns:
        Path to the combined output file.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'combined_merra_{year}.nc')

    variables = VARIABLES[sim_type]
    all_vars = []
    for var_list in variables.values():
        all_vars.extend(var_list)

    days_in_year = 366 if isleap(year) else 365
    hours_in_year = days_in_year * 24

    # Read first file to get lat/lon dimensions
    first_file = _find_first_file(raw_dir, year, variables)
    if first_file is None:
        raise FileNotFoundError(
            f'No downloaded files found for year {year} in {raw_dir}'
        )

    with Dataset(first_file, 'r') as ds:
        lats = ds.variables['lat'][:]
        lons = ds.variables['lon'][:]

    lat_count = len(lats)
    lon_count = len(lons)

    logger.info(f'Creating combined file: {output_path}')
    logger.info(f'  Grid: {lat_count} x {lon_count}, Hours: {hours_in_year}')
    logger.info(f'  Variables: {all_vars}')

    with Dataset(output_path, 'w', format='NETCDF4') as out_ds:
        # Dimensions
        out_ds.createDimension('lat', lat_count)
        out_ds.createDimension('lon', lon_count)
        out_ds.createDimension('time', hours_in_year)

        # Coordinate variables
        lat_var = out_ds.createVariable('lat', 'f8', ('lat',))
        lat_var[:] = lats
        lat_var.units = 'degrees_north'

        lon_var = out_ds.createVariable('lon', 'f8', ('lon',))
        lon_var[:] = lons
        lon_var.units = 'degrees_east'

        # Global attribute (used by simulation code: self.year = ds.year)
        out_ds.year = year

        # Data variables: [lat, lon, time]
        data_vars = {}
        for var_name in all_vars:
            v = out_ds.createVariable(
                var_name, 'f8', ('lat', 'lon', 'time'),
                zlib=True, complevel=4
            )
            data_vars[var_name] = v

        # Fill data day by day (including Feb 29 for leap years)
        day = 0
        missing_days = 0

        for merra_date in pd.date_range(
            datetime(year, 1, 1), datetime(year, 12, 31)
        ):
            date_str = merra_date.strftime('%Y%m%d')
            day_data = {}
            all_found = True

            for collection_key, var_list in variables.items():
                if not var_list:
                    continue

                filepath = os.path.join(
                    raw_dir, collection_key,
                    f'merra2_{collection_key}_{date_str}.nc4'
                )

                if not os.path.exists(filepath):
                    logger.warning(f'Missing file: {filepath}')
                    all_found = False
                    break

                try:
                    with Dataset(filepath, 'r') as ds:
                        for var_name in var_list:
                            data = ds.variables[var_name][:]
                            if hasattr(data, 'filled'):
                                data = data.filled(np.nan)
                            day_data[var_name] = data
                except Exception as e:
                    logger.warning(f'Error reading {filepath}: {e}')
                    all_found = False
                    break

            if not all_found:
                missing_days += 1
                day += 1
                continue

            # Write data: input [time, lat, lon] -> output [lat, lon, time]
            start_hour = day * 24
            end_hour = (day + 1) * 24

            for var_name, data in day_data.items():
                reordered = np.transpose(data, (1, 2, 0))
                data_vars[var_name][:, :, start_hour:end_hour] = reordered

            day += 1

            if day % 30 == 0:
                logger.info(f'  Processed {day}/{days_in_year} days')

        if missing_days > 0:
            msg = f'{missing_days} days were missing from the input data'
            logger.warning(msg)

    if missing_days > 0 and fail_on_missing_days:
        try:
            os.remove(output_path)
            logger.warning(f'Removed incomplete combined file: {output_path}')
        except OSError as e:
            logger.warning(
                f'Failed to remove incomplete file {output_path}: {e}'
            )
        raise RuntimeError(
            f'{msg}. Re-run download, or pass --allow-missing-days.'
        )

    logger.info(f'Combined file saved: {output_path}')
    return output_path


def _find_first_file(raw_dir, year, variables):
    """Find the first available daily file to read lat/lon dimensions."""
    for collection_key, var_list in variables.items():
        if not var_list:
            continue

        collection_dir = os.path.join(raw_dir, collection_key)
        if not os.path.isdir(collection_dir):
            continue

        # Try Jan 1 first
        filepath = os.path.join(
            collection_dir, f'merra2_{collection_key}_{year}0101.nc4'
        )
        if os.path.exists(filepath):
            return filepath

        # Fall back to any file from this year
        for f in sorted(os.listdir(collection_dir)):
            if (f.startswith(f'merra2_{collection_key}_{year}')
                    and f.endswith('.nc4')):
                return os.path.join(collection_dir, f)

    return None


def _specific_humidity_to_rh(q, t_celsius, p_hpa):
    """Convert specific humidity to relative humidity.

    Args:
        q: Specific humidity (kg/kg) from MERRA-2 QV2M.
        t_celsius: Temperature in °C.
        p_hpa: Surface pressure in hPa.

    Returns:
        Relative humidity in % (clipped to 0-100).
    """
    # Tetens formula for saturation vapor pressure (hPa)
    e_sat = 6.112 * np.exp((17.67 * t_celsius) / (t_celsius + 243.5))
    # Saturation specific humidity
    q_sat = 0.622 * e_sat / (p_hpa - 0.378 * e_sat)
    rh = (q / q_sat) * 100.0
    return np.clip(rh, 0.0, 100.0)


def export_weather_csvs(nc_path, year, output_dir, tz_offset=0):
    """Export per-grid-point weather CSV files from a combined NC file.

    Creates CSV files in the format expected by PySAM Biomass/Geothermal:
        - 3-line header: Latitude/Longitude/Time Zone, values, column names
        - Hourly data: Year, Month, Day, Hour, Minute, Temperature(°C),
          Pressure(hPa), Relative Humidity(%)

    Args:
        nc_path: Path to combined_merra_{year}.nc
        year: Year of the data
        output_dir: Base directory for output (CSV files go into {output_dir}/{year}/)
        tz_offset: UTC timezone offset (e.g., 1 for CET)

    Returns:
        Number of CSV files exported.
    """
    year_dir = os.path.join(output_dir, str(year))
    os.makedirs(year_dir, exist_ok=True)

    with Dataset(nc_path, 'r') as ds:
        lats = ds.variables['lat'][:]
        lons = ds.variables['lon'][:]

        for var_name in ('T2M', 'PS', 'QV2M'):
            if var_name not in ds.variables:
                raise KeyError(
                    f"Variable '{var_name}' not found in {nc_path}. "
                    f"Available: {list(ds.variables.keys())}. "
                    f"Run the biomass/geothermal download first: "
                    f"make biomass <year> <country>"
                )

        # Read and convert masked arrays to plain float64, filling missing with NaN
        def _read_var(ds, name):
            data = ds.variables[name][:]
            if hasattr(data, 'filled'):
                data = data.filled(np.nan)
            return np.array(data, dtype=np.float64)

        t2m_all = _read_var(ds, 'T2M')       # [lat, lon, time] in K
        ps_all = _read_var(ds, 'PS')          # [lat, lon, time] in Pa
        qv2m_all = _read_var(ds, 'QV2M')      # [lat, lon, time] in kg/kg

    # Replace any remaining NaN with physical defaults
    np.nan_to_num(t2m_all, copy=False, nan=273.15)   # 0°C
    np.nan_to_num(ps_all, copy=False, nan=101325.0)   # sea-level pressure
    np.nan_to_num(qv2m_all, copy=False, nan=0.005)    # ~50% RH at 10°C

    hours_in_year = t2m_all.shape[2]

    # Build timestamp arrays
    timestamps = pd.date_range(
        start=datetime(year, 1, 1),
        periods=hours_in_year,
        freq='h',
    )
    years = timestamps.year.values
    months = timestamps.month.values
    days = timestamps.day.values
    hours = timestamps.hour.values
    # MERRA-2 uses 30-minute offset (data represents half-hour averages)
    minutes = np.full(hours_in_year, 30, dtype=int)

    count = 0
    for i, lat in enumerate(lats):
        for j, lon in enumerate(lons):
            lat_val = float(lat)
            lon_val = float(lon)

            # Extract time series for this grid point
            t2m = t2m_all[i, j, :]       # K
            ps = ps_all[i, j, :]          # Pa
            qv2m = qv2m_all[i, j, :]     # kg/kg

            # Convert units
            temp_c = np.round(t2m - 273.15, 2)         # K → °C
            pres_hpa = np.round(ps / 100.0, 2)         # Pa → hPa
            rh = np.round(_specific_humidity_to_rh(qv2m, temp_c, pres_hpa), 2)

            # Round coordinates for filename (match existing convention)
            lat_str = f'{lat_val:.2f}'.rstrip('0').rstrip('.')
            lon_str = f'{lon_val:.2f}'.rstrip('0').rstrip('.')
            filename = f'weather_{lat_str}_{lon_str}.csv'
            filepath = os.path.join(year_dir, filename)

            with open(filepath, 'w') as f:
                f.write('Latitude,Longitude,Time Zone\n')
                f.write(f'{lat_str},{lon_str},{tz_offset}\n')
                f.write(
                    'Year,Month,Day,Hour,Minute,'
                    'Temperature,Pressure,Relative Humidity\n'
                )
                for t in range(hours_in_year):
                    f.write(
                        f'{years[t]},{months[t]},{days[t]},'
                        f'{hours[t]},{minutes[t]},'
                        f'{temp_c[t]},{pres_hpa[t]},'
                        f'{rh[t]}\n'
                    )

            count += 1

    logger.info(f'Exported {count} weather CSV files to {year_dir}')
    return count
