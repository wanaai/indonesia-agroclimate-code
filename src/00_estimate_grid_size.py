"""
Steps 1-3 of the research plan: before downloading any data, estimate the
number of grid points generated at a given resolution and the number of
daily records produced for the selected year range.

Run this script with different combinations of spatial resolution
(0.1 vs. 0.25 degrees) and year range (2010-2025 vs. 2015-2025)
before deciding on the final configuration in config.py.

Usage:
    python 00_estimate_grid_size.py
    python 00_estimate_grid_size.py --resolution 0.25 --start-year 2015
"""

import argparse
import sys

import geopandas as gpd
import numpy as np

import config


def build_land_grid(resolution_deg: float) -> gpd.GeoDataFrame:
    """Generate candidate grid points within the bounding box, then retain
    only points located within or on the boundary of Indonesia's land area."""
    print(f"[1/3] Downloading Indonesia boundary from {config.COUNTRY_BOUNDARY_URL} ...")
    world = gpd.read_file(config.COUNTRY_BOUNDARY_URL)
    indonesia = world[world[config.COUNTRY_NAME_FIELD] == config.COUNTRY_NAME_VALUE]

    if indonesia.empty:
        raise RuntimeError(
            "Indonesia boundary was not found in the GeoJSON source. "
            "Update config.COUNTRY_BOUNDARY_URL, COUNTRY_NAME_FIELD, "
            "or COUNTRY_NAME_VALUE."
        )

    indonesia_union = indonesia.union_all()

    print(f"[2/3] Generating candidate grid points at {resolution_deg}-degree resolution within Indonesia's bounding box ...")
    lons = np.arange(
        config.BBOX_MIN_LON,
        config.BBOX_MAX_LON + resolution_deg,
        resolution_deg
    )
    lats = np.arange(
        config.BBOX_MIN_LAT,
        config.BBOX_MAX_LAT + resolution_deg,
        resolution_deg
    )

    lon_grid, lat_grid = np.meshgrid(lons, lats)

    candidate_points = gpd.GeoDataFrame(
        {
            "longitude": lon_grid.ravel(),
            "latitude": lat_grid.ravel()
        },
        geometry=gpd.points_from_xy(
            lon_grid.ravel(),
            lat_grid.ravel()
        ),
        crs="EPSG:4326",
    )

    n_candidates = len(candidate_points)

    print(f"[3/3] Filtering {n_candidates:,} candidate points against Indonesia's land boundary ...")
    on_land = candidate_points[
        candidate_points.geometry.within(indonesia_union)
    ]

    return on_land, n_candidates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--resolution",
        type=float,
        default=config.GRID_RESOLUTION_DEG
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=config.START_YEAR
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=config.END_YEAR
    )

    args = parser.parse_args()

    grid, n_candidates = build_land_grid(args.resolution)
    n_points = len(grid)

    n_years = args.end_year - args.start_year + 1
    approx_days = n_years * 365.25
    n_rows = int(n_points * approx_days)
    n_variables = len(config.DAILY_VARIABLES)
    n_cells = n_rows * n_variables

    # Rough file-size estimate: 4 bytes per numeric cell (float32) plus
    # approximately 20 bytes per row for non-numeric columns (date, lat, lon).
    # Compressed Parquet files are typically 3-6 times smaller than this raw estimate.
    raw_bytes = n_rows * (20 + n_variables * 4)
    est_parquet_gb = raw_bytes / 1e9 / 4  # Assume approximately 4x compression

    n_batches = -(-n_points // config.BATCH_SIZE)  # Ceiling division
    n_requests = n_batches * n_years  # One request per batch per year (see 02_download_weather.py)
    est_download_minutes = (
        n_requests * config.REQUEST_SLEEP_SECONDS / 60
    )

    print("\n=== DATASET SIZE ESTIMATE ===")
    print(f"Grid resolution          : {args.resolution} degrees")
    print(f"Candidate points (bbox)  : {n_candidates:,}")
    print(f"Grid points on land      : {n_points:,}")
    print(f"Year range               : {args.start_year}-{args.end_year} ({n_years} years)")
    print(f"Daily variables          : {n_variables}")
    print(f"Estimated data rows      : {n_rows:,}")
    print(f"Estimated numeric cells  : {n_cells:,}")
    print(f"Estimated Parquet size   : ~{est_parquet_gb:.2f} GB (rough estimate, depends on compression)")
    print(f"Estimated requests       : {n_requests:,} (batch of {config.BATCH_SIZE} points per request)")
    print(
        f"Estimated download time  : ~{est_download_minutes:.0f} minutes "
        "(request intervals only, excluding server response time)"
    )
    print(
        "\nUse these estimates to select the final spatial resolution and year range "
        "before running 01_generate_grid.py and 02_download_weather.py."
    )


if __name__ == "__main__":
    sys.exit(main())