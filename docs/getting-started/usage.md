# Usage

`make` targets are run from the **project root**. To call the package directly
with Python, run from the `src/` directory (or set `PYTHONPATH=src`).

## Using Make (from the project root)

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

## Using Python directly (from the `src/` directory)

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

## Download data for Germany & Netherlands

=== "Germany"

    ```bash
    python -m data_pipeline pv 2015 2025 germany
    python -m data_pipeline wind 2015 2025 germany
    python -m data_pipeline biomass 2015 2025 germany
    python -m data_pipeline geothermal 2015 2025 germany
    ```

=== "Netherlands"

    ```bash
    python -m data_pipeline pv 2015 2025 netherlands
    python -m data_pipeline wind 2015 2025 netherlands
    python -m data_pipeline biomass 2015 2025 netherlands
    python -m data_pipeline geothermal 2015 2025 netherlands
    ```

!!! note
    NASA servers may return 503 errors during peak load. The pipeline skips
    already-downloaded files, so you can safely re-run the same command to resume.
