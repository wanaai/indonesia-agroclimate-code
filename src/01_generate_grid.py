"""
Step 5 of the research plan: generate Indonesia's grid points at the final
spatial resolution specified by GRID_RESOLUTION_DEG in config.py. Retain only
points located within Indonesia's land boundary and save them to
metadata/grid_points.csv.

This file serves as the location reference reused by 02_download_weather.py.
It only needs to be generated once, unless the grid resolution or boundary changes.

Usage:
    python 01_generate_grid.py
"""

import sys

import geopandas as gpd
import numpy as np
import pandas as pd

import config


def main():
    print(f"Downloading Indonesia boundary from {config.COUNTRY_BOUNDARY_URL} ...")
    world = gpd.read_file(config.COUNTRY_BOUNDARY_URL)
    indonesia = world[world[config.COUNTRY_NAME_FIELD] == config.COUNTRY_NAME_VALUE]

    if indonesia.empty:
        print(
            "ERROR: Indonesia boundary was not found. Check "
            "config.COUNTRY_BOUNDARY_URL, COUNTRY_NAME_FIELD, "
            "and COUNTRY_NAME_VALUE.",
            file=sys.stderr,
        )
        sys.exit(1)

    indonesia_union = indonesia.union_all()

    res = config.GRID_RESOLUTION_DEG
    print(f"Generating candidate grid points at {res}-degree resolution ...")

    lons = np.arange(
        config.BBOX_MIN_LON,
        config.BBOX_MAX_LON + res,
        res
    )
    lats = np.arange(
        config.BBOX_MIN_LAT,
        config.BBOX_MAX_LAT + res,
        res
    )

    lon_grid, lat_grid = np.meshgrid(lons, lats)

    candidates = gpd.GeoDataFrame(
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

    print(f"Filtering {len(candidates):,} candidate points against the land boundary ...")
    on_land = candidates[
        candidates.geometry.within(indonesia_union)
    ].copy()

    # Generate stable, readable grid IDs, e.g., GRID_-0623_10684
    on_land["grid_id"] = [
        f"GRID_{lat:+07.3f}_{lon:+08.3f}".replace(".", "")
        for lat, lon in zip(
            on_land["latitude"],
            on_land["longitude"]
        )
    ]

    out = on_land[
        ["grid_id", "latitude", "longitude"]
    ].reset_index(drop=True)

    out = out.sort_values(
        ["latitude", "longitude"]
    ).reset_index(drop=True)

    config.GRID_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    out.to_csv(
        config.GRID_PATH,
        index=False
    )

    print(f"\nCompleted. {len(out):,} grid points saved to: {config.GRID_PATH}")
    print("Columns: grid_id, latitude, longitude")

    print(
        "\nSpatial quality-control note (Section 10 of the research plan): "
        "points filtered using 'within land boundary' should exclude offshore "
        "areas. However, coastal points and small islands may be omitted if "
        "they fall exactly on the coastline or are not captured by the boundary. "
        "If grid coverage appears too sparse on small islands, consider applying "
        "a small buffer (e.g., indonesia_union.buffer(0.01))."
    )


if __name__ == "__main__":
    main()