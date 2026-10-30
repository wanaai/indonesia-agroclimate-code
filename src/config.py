"""
Main configuration for the Indonesia Nationwide Agroclimatic Dataset pipeline.

Modify the settings below to change the grid resolution, year range,
or variables retrieved from the Open-Meteo Historical Weather API:
https://open-meteo.com/en/docs/historical-weather-api
"""

from pathlib import Path


# Project paths
ROOT_DIR = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT_DIR / "dataset"

DATA_DIR = DATASET_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
METADATA_DIR = DATASET_DIR / "metadata"
GRID_PATH = METADATA_DIR / "grid_points.csv"

for d in (RAW_DIR, PROCESSED_DIR, METADATA_DIR):
    d.mkdir(parents=True, exist_ok=True)


# Spatial grid
# Grid resolution in degrees. A resolution of 0.1 degrees is approximately
# 11 km (consistent with ERA5-Land), while 0.25 degrees is approximately
# 25 km (consistent with ERA5). See Steps 1-3 of the research plan:
# estimate the number of grid points before downloading the full dataset.
GRID_RESOLUTION_DEG = 0.5

# Approximate bounding box for Indonesia, used to generate candidate grid
# points before clipping them to the actual country boundary in
# 01_generate_grid.py.
BBOX_MIN_LON = 94.5
BBOX_MAX_LON = 141.5
BBOX_MIN_LAT = -11.5
BBOX_MAX_LAT = 6.5

# Source of the Indonesia country boundary. This GeoJSON file is hosted
# on GitHub and can be accessed without an API key. Replace it with an
# official BIG/BPS shapefile or GeoJSON if available to improve boundary
# accuracy for publication.
COUNTRY_BOUNDARY_URL = (
    "https://raw.githubusercontent.com/datasets/geo-countries/main/data/countries.geojson"
)
COUNTRY_NAME_FIELD = "name"
COUNTRY_NAME_VALUE = "Indonesia"


# Time range
# The initial research plan specifies 2010-2025. The range can be narrowed
# to 2015-2025 if the estimated dataset size is too large, as assessed by
# 00_estimate_grid_size.py.
START_YEAR = 2016
END_YEAR = 2025  # Inclusive; the script automatically truncates to the current date if necessary.


# Open-Meteo Historical Weather API
ARCHIVE_API_URL = "https://archive-api.open-meteo.com/v1/archive"

# Reanalysis model. "best_match" combines ERA5-Land and ERA5, but may use
# different models depending on the year (including IFS from 2017 onward).
# This may reduce consistency for climate trend analysis in the Data in Brief
# manuscript.
#
# "era5_land" (0.1-degree resolution) does not directly provide precipitation,
# wind speed, or shortwave radiation. These variables are sourced from ERA5
# (see footnote *1 in the Data Sources table of the Historical Weather API
# documentation). Using "era5_land" alone would result in missing values
# for these variables, and ET0, which requires wind and radiation data,
# would also be affected.
#
# "era5_seamless" is an official combination: temperature and humidity from
# ERA5-Land (0.1-degree resolution), and wind and radiation from ERA5
# (0.25-degree resolution). It maintains consistency across years without
# combining the data with IFS forecasts.
WEATHER_MODEL = "era5_seamless"

TIMEZONE = "auto"

# Daily variables relevant to agroclimatic analysis, as described in
# Sections 6 and 7 of the research plan. These names correspond to the
# official daily parameters supported by the Open-Meteo Historical Weather API.
DAILY_VARIABLES = [
    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "relative_humidity_2m_mean",
    "et0_fao_evapotranspiration",
]


# Download settings
# Open-Meteo calculates quota usage fractionally based on the number of
# locations, variables, and time range in each request, rather than counting
# each request as one unit. With 6 variables over 10 years, a batch of
# 10 grid points per request is estimated to use approximately 234 units,
# leaving room for additional daily requests before reaching the 10,000-unit
# quota.
BATCH_SIZE = 10

REQUEST_SLEEP_SECONDS = 10
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 10


# Quality control
QC_RANGES = {
    "temperature_2m_mean": (-10, 45),
    "temperature_2m_max": (-10, 50),
    "temperature_2m_min": (-15, 40),
    "precipitation_sum": (0, 600),  # mm/day; a broad range for tropical extremes
    "relative_humidity_2m_mean": (0, 100),
    "wind_speed_10m_mean": (0, 150),
    "shortwave_radiation_sum": (0, 45),  # MJ/m^2
    "et0_fao_evapotranspiration": (0, 15),
    "vapour_pressure_deficit_max": (0, 10),
    "soil_moisture_0_to_7cm_mean": (0, 1),
    "soil_moisture_7_to_28cm_mean": (0, 1),
    "soil_temperature_0_to_7cm_mean": (-10, 50),
}


# Dry-day threshold for the consecutive_dry_days indicator (mm).
# Define and support this threshold with literature in the manuscript
# (see Section 7).
DRY_DAY_THRESHOLD_MM = 1.0