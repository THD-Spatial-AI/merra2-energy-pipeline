# MERRA-2 Data Pipeline

Unified data pipeline for downloading and processing **NASA MERRA-2** reanalysis
data for energy simulations — **PV, Wind, Biomass, and Geothermal**.

The pipeline downloads daily MERRA-2 files for a chosen country and year range,
combines them into yearly NetCDF files, and (for biomass/geothermal) exports
per-grid-point weather CSVs in the format required by **PySAM**.

## Highlights

- Four simulation types: `pv`, `wind`, `biomass`, `geothermal`
- 28 European countries plus a combined Europe region
- Resumable downloads — already-downloaded files are skipped
- Yearly NetCDF output, plus PySAM-ready weather CSVs for biomass/geothermal

## Quick start

```bash
# Install
pip install -r requirements.txt

# Configure NASA EarthData credentials
cp src/data_pipeline/.env.example src/data_pipeline/.env
# edit the file with your username/password

# Run (PV for Germany, 2019)
make pv 2019 germany
```

## Documentation

- [Setup](getting-started/setup.md) — environment, dependencies, and credentials
- [Usage](getting-started/usage.md) — running the pipeline with Make or Python
- [Data Reference](reference/data.md) — output structure, variables, and countries

## Project layout

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
