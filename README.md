# Nationwide Agroclimatic Dataset for Indonesia: Daily Weather and Agricultural Indicators

## Overview

This repository contains the processing code, spatial metadata generation notebook, visualization notebooks, and validation notebook for the **Nationwide Agroclimatic Dataset for Indonesia: Daily Weather and Agricultural Indicators**.

The dataset provides daily weather data and derived agroclimatic indicators for **612 land-only grid points** across Indonesia from **2016-01-01 to 2025-12-31**, at **0.5° spatial spacing**.

Weather data were obtained from the **Open-Meteo Historical Weather API** using the **ERA5-Seamless** model.

The complete dataset is published separately on Mendeley Data.

## Dataset

- **Spatial coverage:** Indonesia
- **Grid points:** 612 land-only locations
- **Spatial spacing:** 0.5°
- **Period:** 2016-2025
- **Temporal resolution:** Daily
- **Records:** 2,235,636
- **Columns:** 23
- **Raw weather variables:** 6
- **Derived agroclimatic indicators:** 12
- **Quality-control flag:** 1

### Raw Variables

- `temperature_2m_mean`
- `temperature_2m_max`
- `temperature_2m_min`
- `precipitation_sum`
- `relative_humidity_2m_mean`
- `et0_fao_evapotranspiration`

### Derived Indicators

- `rainfall_7d`
- `rainfall_30d`
- `rainfall_90d`
- `rainy_days_30d`
- `rainy_days_90d`
- `max_daily_rainfall_30d`
- `consecutive_dry_days`
- `temperature_range`
- `rolling_temperature_mean_7d`
- `cumulative_et0_30d`
- `water_balance`
- `rolling_water_balance_30d`

Precipitation-based indicators use a **1.0 mm threshold**. Rolling indicators include the current day and preceding days within the specified window. The treatment of incomplete rolling windows is defined in the processing code.

## Repository Structure

```text
.
├── README.md
├── requirements.txt
├── .gitignore
├── calibri.ttf
├── src/
│   ├── config.py
│   ├── 00_estimate_grid_size.py
│   ├── 01_generate_grid.py
│   ├── 02_download_weather.py
│   ├── 03_quality_control.py
│   └── 04_derive_indicators.py
├── spatial_metadata/
│   └── generate_spatial_metadata.ipynb
├── figure_scripts/
│   ├── 01_spatial_coverage_map.ipynb
│   ├── 02_temporal_patterns.ipynb
│   ├── 03_raw_variable_distributions.ipynb
│   ├── 04_derived_indicator_distributions.ipynb
│   ├── 05_agroclimatic_profiles.ipynb
│   └── 06_bmkg_openmeteo_comparison.ipynb
└── validation_monthly/
    └── validate_monthly_bmkg.ipynb
```

The `dataset/` directory and generated files in `figure_scripts/outputs/` are maintained separately and are not included in this GitHub repository. The dataset files are available through Mendeley Data.

The `calibri.ttf` file is used by the figure-generation notebooks. If the font file is unavailable, the notebooks use a fallback font.

## Requirements

Install the required Python packages:

```bash
pip install -r requirements.txt
```

The requirements include the packages used by the processing scripts and notebooks, including `requests`, `pandas`, `numpy`, `geopandas`, `shapely`, `pyarrow`, `matplotlib`, `scipy`, and `rasterio`.

Jupyter Notebook or JupyterLab is required to run the `.ipynb` files.

## Processing Pipeline

Run the scripts in the following order:

1. `src/00_estimate_grid_size.py`: estimates the grid size.
2. `src/01_generate_grid.py`: generates the spatial grid.
3. `src/02_download_weather.py`: retrieves daily weather data.
4. `src/03_quality_control.py`: performs quality-control checks.
5. `src/04_derive_indicators.py`: computes derived agroclimatic indicators.

Review `src/config.py` before running the pipeline to verify the configured years, grid resolution, variables, and input/output paths.

The pipeline generates intermediate and processed files locally. Running it may require access to the Open-Meteo Historical Weather API and the geographic boundary data source configured in the code.

## Spatial Metadata Generation

The notebook `spatial_metadata/generate_spatial_metadata.ipynb` generates enriched spatial metadata for the grid points, including administrative and elevation information.

The notebook uses the project directory structure to locate input and output files. Administrative boundary data may be retrieved from the configured public geographic data service if the local reference file is unavailable.

## Figure Generation

The `figure_scripts/` directory contains six notebooks for generating the dataset figures:

1. `01_spatial_coverage_map.ipynb`
2. `02_temporal_patterns.ipynb`
3. `03_raw_variable_distributions.ipynb`
4. `04_derived_indicator_distributions.ipynb`
5. `05_agroclimatic_profiles.ipynb`
6. `06_bmkg_openmeteo_comparison.ipynb`

Generated figures are saved in `figure_scripts/outputs/`. This output directory is excluded from the GitHub repository.

The notebooks require the corresponding dataset files and, for the BMKG comparison, the relevant validation data.

## Quality Control and Validation

The processing workflow includes checks for missing values, duplicate records, plausible value ranges, and temporal continuity.

The notebook `validation_monthly/validate_monthly_bmkg.ipynb` recomputes monthly validation metrics using paired BMKG and Open-Meteo observations. The calculations include bias, MAE, RMSE, Pearson correlation, its 95% confidence interval, and p-value.

The input file `bmkg_openmeteo_monthly_2025.csv`, containing paired monthly BMKG and Open-Meteo observations, is maintained separately and is not included in this repository. The file must be placed in the `validation_monthly/` directory before running the notebook.

Refer to the published dataset and its accompanying metadata for the dataset characteristics and reported validation details.

## Dataset Access

The complete dataset, including the processed data files, is available from Mendeley Data:

**DOI:** https://doi.org/10.17632/3pfbdbzfff.1

The data files are maintained separately from this code repository to avoid duplicating the published dataset.

## Citation

Iwan, Wana Ardilah; Sari, Sabrina Adinda; Isnan, Mahmud; Pardamean, Bens (2026). *Nationwide Agroclimatic Dataset for Indonesia*. Mendeley Data, V1. https://doi.org/10.17632/3pfbdbzfff.1

## License

The code license for this repository has not yet been specified. Refer to the Mendeley Data record for the dataset license.