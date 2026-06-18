# Setup

## 1. Create and activate the conda environment

```bash
conda create -n pysamnrel python=3.10 -y
conda activate pysamnrel
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Configure NASA EarthData credentials

1. Create an account at <https://urs.earthdata.nasa.gov>
2. Copy the example env file and fill in your credentials:

   ```bash
   cp src/data_pipeline/.env.example src/data_pipeline/.env
   ```

3. Edit `src/data_pipeline/.env`:

   ```
   EARTHDATA_USERNAME=your_username
   EARTHDATA_PASSWORD=your_password
   OUTPUT_DIR=./output_tech_data
   RAW_DIR=./raw_data
   ```

!!! note
    The pipeline reads credentials from `src/data_pipeline/.env`, which is
    git-ignored so your credentials are never committed.
