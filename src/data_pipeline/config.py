"""Configuration and constants for the MERRA-2 data pipeline."""

import os
from pathlib import Path

# Package directory (where this file and .env live)
PACKAGE_DIR = Path(__file__).parent

try:
    from dotenv import load_dotenv
    load_dotenv(PACKAGE_DIR / '.env')
except ImportError:
    pass

# NASA EarthData credentials
EARTHDATA_USERNAME = os.getenv('EARTHDATA_USERNAME', '')
EARTHDATA_PASSWORD = os.getenv('EARTHDATA_PASSWORD', '')

# MERRA-2 OPeNDAP base URL
OPENDAP_BASE_URL = 'https://goldsmr4.gesdisc.eosdis.nasa.gov/opendap/MERRA2'

# MERRA-2 collections
COLLECTIONS = {
    'slv': 'M2T1NXSLV.5.12.4',
    'rad': 'M2T1NXRAD.5.12.4',
    'lnd': 'M2T1NXLND.5.12.4',
}

# File naming templates
FILE_TEMPLATES = {
    'slv': 'MERRA2_{stream}.tavg1_2d_slv_Nx.{date}.nc4',
    'rad': 'MERRA2_{stream}.tavg1_2d_rad_Nx.{date}.nc4',
    'lnd': 'MERRA2_{stream}.tavg1_2d_lnd_Nx.{date}.nc4',
}

# Variables needed for each simulation type
VARIABLES = {
    'pv': {
        'slv': ['U2M', 'V2M', 'U10M', 'V10M', 'T2M', 'PS'],
        'rad': ['SWGDN'],
        'lnd': ['SNODP', 'PRECSNOLAND'],
    },
    'wind': {
        'slv': ['U2M', 'U10M', 'U50M', 'V2M', 'V10M', 'V50M', 'T2M', 'PS'],
        'rad': [],
        'lnd': [],
    },
    'biomass': {
        'slv': ['T2M', 'PS', 'QV2M'],
        'rad': [],
        'lnd': [],
    },
    'geothermal': {
        'slv': ['T2M', 'PS', 'QV2M'],
        'rad': [],
        'lnd': [],
    },
}

# MERRA-2 grid specifications
MERRA_LAT_MIN = -90.0
MERRA_LAT_STEP = 0.5
MERRA_LON_MIN = -180.0
MERRA_LON_STEP = 0.625

# Directories (relative to package dir)
DEFAULT_OUTPUT_DIR = os.getenv('OUTPUT_DIR', str(PACKAGE_DIR / 'output'))
DEFAULT_RAW_DIR = os.getenv('RAW_DIR', str(PACKAGE_DIR / 'raw_data'))

# Download settings
MAX_WORKERS = 4
CHUNK_SIZE = 1024 * 1024  # 1MB
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
