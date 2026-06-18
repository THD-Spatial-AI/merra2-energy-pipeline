# MERRA-2 Data Pipeline

Unified data pipeline for downloading and processing NASA MERRA-2 reanalysis data for energy simulations (PV, Wind, Biomass, Geothermal).

## Setup

### 1. Create and activate the conda environment

```bash
conda create -n pysamnrel python=3.10 -y
conda activate pysamnrel
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure NASA EarthData credentials

1. Create an account at <https://urs.earthdata.nasa.gov>
2. Copy the example env file and fill in your credentials:

```bash
cp src/data_pipeline/.env.example src/data_pipeline/.env
```

Edit `src/data_pipeline/.env`:

```
EARTHDATA_USERNAME=your_username
EARTHDATA_PASSWORD=your_password
OUTPUT_DIR=./output_tech_data
RAW_DIR=./raw_data
```

## Project Layout

```
.
├── src/
│   └── data_pipeline/        # Python package (run as `python -m data_pipeline`)
│       ├── __main__.py
│       ├── config.py
│       ├── countries.py
│       ├── download.py
│       └── combine.py
├── Makefile
├── requirements.txt
└── README.md
```

## Usage

`make` targets are run from the **project root**. To call the package directly
with Python, run from the `src/` directory (or set `PYTHONPATH=src`).

### Using Make (from the project root)

```bash
# Single year
make pv 2019 germany
make wind 2019 germany
make biomass 2019 germany
make geothermal 2019 germany

# Year range
make pv 2015 2025 germany

# Skip download (combine only)
make combine-pv 2019 germany

# List available countries
make list-countries

# Show all targets
make help
```

### Using Python directly (from the `src/` directory)

```bash
cd src

# Single year
python -m data_pipeline pv 2019 germany
python -m data_pipeline wind 2019 germany
python -m data_pipeline biomass 2019 germany
python -m data_pipeline geothermal 2019 germany

# Year range
python -m data_pipeline pv 2015 2025 germany

# Options
python -m data_pipeline pv 2019 germany --skip-download    # combine only
python -m data_pipeline pv 2019 germany --skip-combine     # download only
python -m data_pipeline pv 2019 germany --verbose           # debug logging
python -m data_pipeline --list-countries                    # show countries
```

## Download Data for Germany & Netherlands

### Germany

```bash
# PV (2015–2025)
python -m data_pipeline pv 2015 2025 germany

# Wind (2015–2025)
python -m data_pipeline wind 2015 2025 germany

# Biomass (2015–2025)
python -m data_pipeline biomass 2015 2025 germany

# Geothermal (2015–2025)
python -m data_pipeline geothermal 2015 2025 germany
```

### Netherlands

```bash
# PV (2015–2025)
python -m data_pipeline pv 2015 2025 netherlands

# Wind (2015–2025)
python -m data_pipeline wind 2015 2025 netherlands

# Biomass (2015–2025)
python -m data_pipeline biomass 2015 2025 netherlands

# Geothermal (2015–2025)
python -m data_pipeline geothermal 2015 2025 netherlands
```

> **Note:** NASA servers may return 503 errors during peak load. The pipeline skips already-downloaded files, so you can safely re-run the same command to resume.

## Output Structure

```
.
├── raw_data/                          # Raw MERRA-2 daily downloads
│   ├── pv/germany/slv/
│   ├── wind/germany/slv/
│   ├── biomass/germany/slv/
│   ├── geothermal/germany/slv/
│   ├── pv/netherlands/slv/
│   └── ...
├── output_tech_data/                  # Processed output
│   ├── pv/
│   │   ├── germany/                   # combined_merra_{year}.nc
│   │   └── netherlands/
│   ├── wind/
│   │   ├── germany/                   # combined_merra_{year}.nc
│   │   └── netherlands/
│   ├── biomass/
│   │   ├── germany/{year}/            # combined_merra_{year}.nc + weather_*.csv
│   │   └── netherlands/{year}/
│   └── geothermal/
│       ├── germany/{year}/            # combined_merra_{year}.nc + weather_*.csv
│       └── netherlands/{year}/
```

- **PV / Wind**: Output is a single NetCDF file per year containing the full MERRA-2 grid.
- **Biomass / Geothermal**: Additionally generates per-grid-point CSV files with Temperature (°C), Pressure (hPa), and Relative Humidity (%) — the format required by PySAM.

## MERRA-2 Variables by Simulation Type

| Variable | PV | Wind | Biomass | Geothermal | Description |
|----------|:--:|:----:|:-------:|:----------:|-------------|
| T2M      | ✓  | ✓    | ✓       | ✓          | 2m air temperature (K) |
| PS       | ✓  | ✓    | ✓       | ✓          | Surface pressure (Pa) |
| U2M      | ✓  | ✓    |         |            | 2m eastward wind (m/s) |
| V2M      | ✓  | ✓    |         |            | 2m northward wind (m/s) |
| U10M     | ✓  | ✓    |         |            | 10m eastward wind (m/s) |
| V10M     | ✓  | ✓    |         |            | 10m northward wind (m/s) |
| SWGDN    | ✓  |      |         |            | Surface shortwave flux (W/m²) |
| SNODP    | ✓  |      |         |            | Snow depth (m) |
| PRECSNOLAND | ✓ |    |         |            | Snowfall rate (kg/m²/s) |
| QV2M     |    |      | ✓       | ✓          | 2m specific humidity (kg/kg) |

## Available Countries

Run `python -m data_pipeline --list-countries` to see the full list. Includes:

Germany, France, Spain, Italy, United Kingdom, Poland, Netherlands, Belgium, Austria, Switzerland, Portugal, Sweden, Norway, Finland, Denmark, Ireland, Czech Republic, Romania, Hungary, Greece, Croatia, Bulgaria, Slovakia, Slovenia, Luxembourg, Estonia, Latvia, Lithuania, and a combined Europe region.
