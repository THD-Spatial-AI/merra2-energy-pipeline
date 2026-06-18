# Data Reference

## Output structure

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

- **PV / Wind**: Output is a single NetCDF file per year containing the full
  MERRA-2 grid.
- **Biomass / Geothermal**: Additionally generates per-grid-point CSV files with
  Temperature (°C), Pressure (hPa), and Relative Humidity (%) — the format
  required by PySAM.

## MERRA-2 variables by simulation type

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

## Available countries

Run `python -m data_pipeline --list-countries` to see the full list. Includes:

Germany, France, Spain, Italy, United Kingdom, Poland, Netherlands, Belgium,
Austria, Switzerland, Portugal, Sweden, Norway, Finland, Denmark, Ireland,
Czech Republic, Romania, Hungary, Greece, Croatia, Bulgaria, Slovakia, Slovenia,
Luxembourg, Estonia, Latvia, Lithuania, and a combined Europe region.
