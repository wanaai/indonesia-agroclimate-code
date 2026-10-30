"""
Step 8 of the research plan (Section 7): derive agroclimatic indicators
from the quality-controlled data in data/processed/agroclimate_qc.parquet.

Indicators are calculated for each grid_id using rolling windows in
chronological order:
- rainfall_7d, rainfall_30d, rainfall_90d: cumulative precipitation
- rainy_days_30d, rainy_days_90d: number of rainy days
  (> DRY_DAY_THRESHOLD_MM)
- max_daily_rainfall_30d: maximum daily precipitation over 30 days
- consecutive_dry_days: consecutive dry days (precipitation < threshold)
- temperature_range: temperature_2m_max - temperature_2m_min
- rolling_temperature_mean_7d: 7-day mean temperature
- cumulative_et0_30d: cumulative ET0 over 30 days
- water_balance: daily precipitation_sum - et0_fao_evapotranspiration
- rolling_water_balance_30d: cumulative water balance over 30 days

Indicator definitions and thresholds must be explained in the Data in Brief
manuscript (Section 7 and metadata/indicator_definitions.csv). Do not make
claims without supporting literature.

Usage:
    python 04_derive_indicators.py
"""

import numpy as np
import pandas as pd

import config


INDICATOR_DEFINITIONS = [
    ("rainfall_7d", "mm", "Sum of precipitation_sum over the current day and previous 6 days"),
    ("rainfall_30d", "mm", "Sum of precipitation_sum over the current day and previous 29 days"),
    ("rainfall_90d", "mm", "Sum of precipitation_sum over the current day and previous 89 days"),
    ("rainy_days_30d", "days", "Number of days with precipitation_sum > 1.0 mm over the current day and previous 29 days"),
    ("rainy_days_90d", "days", "Number of days with precipitation_sum > 1.0 mm over the current day and previous 89 days"),
    ("max_daily_rainfall_30d", "mm", "Maximum precipitation_sum over the current day and previous 29 days"),
    ("consecutive_dry_days", "days", "Number of consecutive days with precipitation_sum < 1.0 mm up to and including the current day; the count resets to 0 on a wet day (precipitation_sum >= 1.0 mm)"),
    ("temperature_range", "°C", "Difference between temperature_2m_max and temperature_2m_min on the same day"),
    ("rolling_temperature_mean_7d", "°C", "Mean of temperature_2m_mean over the current day and previous 6 days"),
    ("cumulative_et0_30d", "mm", "Sum of et0_fao_evapotranspiration over the current day and previous 29 days"),
    ("water_balance", "mm", "Difference between precipitation_sum and et0_fao_evapotranspiration on the same day"),
    ("rolling_water_balance_30d", "mm", "Sum of daily water_balance over the current day and previous 29 days"),
]


def consecutive_dry_days(precip: pd.Series, threshold: float) -> pd.Series:
    """Count consecutive dry days up to and including the current day.
    Reset the count to 0 whenever precipitation is greater than or equal
    to the threshold."""
    is_dry = (precip < threshold).astype(int)

    # Group by the cumulative count of wet days, then calculate the
    # cumulative sum within each group to obtain the current dry-day run.
    group = (~is_dry.astype(bool)).cumsum()

    return is_dry.groupby(group).cumsum()


def add_indicators(group: pd.DataFrame) -> pd.DataFrame:
    group = group.sort_values("date").copy()

    precip = group["precipitation_sum"]
    group["rainfall_7d"] = precip.rolling(7, min_periods=1).sum()
    group["rainfall_30d"] = precip.rolling(30, min_periods=1).sum()
    group["rainfall_90d"] = precip.rolling(90, min_periods=1).sum()

    is_rainy = (precip > config.DRY_DAY_THRESHOLD_MM).astype(int)
    group["rainy_days_30d"] = is_rainy.rolling(30, min_periods=1).sum()
    group["rainy_days_90d"] = is_rainy.rolling(90, min_periods=1).sum()
    group["max_daily_rainfall_30d"] = precip.rolling(30, min_periods=1).max()

    group["consecutive_dry_days"] = consecutive_dry_days(
        precip,
        config.DRY_DAY_THRESHOLD_MM
    )

    if {"temperature_2m_max", "temperature_2m_min"}.issubset(group.columns):
        group["temperature_range"] = (
            group["temperature_2m_max"] - group["temperature_2m_min"]
        )

    if "temperature_2m_mean" in group.columns:
        group["rolling_temperature_mean_7d"] = (
            group["temperature_2m_mean"]
            .rolling(7, min_periods=1)
            .mean()
        )

    if "et0_fao_evapotranspiration" in group.columns:
        et0 = group["et0_fao_evapotranspiration"]
        group["cumulative_et0_30d"] = et0.rolling(30, min_periods=1).sum()
        group["water_balance"] = precip - et0
        group["rolling_water_balance_30d"] = (
            group["water_balance"].rolling(30, min_periods=1).sum()
        )

    return group


def main():
    in_path = config.PROCESSED_DIR / "agroclimate_qc.parquet"

    if not in_path.exists():
        raise FileNotFoundError(
            f"{in_path} not found. Run 03_quality_control.py first."
        )

    print(f"Reading {in_path} ...")
    df = pd.read_parquet(in_path)
    df["date"] = pd.to_datetime(df["date"])

    print(
        f"Total rows: {len(df):,} | "
        f"Total grid points: {df['grid_id'].nunique():,}"
    )

    print("Calculating derived agroclimatic indicators for each grid_id using rolling windows ...")
    df = df.groupby("grid_id", group_keys=False).apply(add_indicators)

    out_path = config.PROCESSED_DIR / "agroclimate_with_indicators.parquet"
    df.to_parquet(out_path, index=False)

    print(f"Completed. Final dataset with indicators saved to: {out_path}")

    # Save indicator definitions for the manuscript metadata (Section 13).
    defs_df = pd.DataFrame(
        INDICATOR_DEFINITIONS,
        columns=["variable", "unit", "description"]
    )

    defs_path = config.METADATA_DIR / "indicator_definitions.csv"
    defs_df.to_csv(defs_path, index=False)

    print(f"Indicator definitions saved to: {defs_path}")

    # Split the output by year into data/processed/by_year/.
    print("Writing yearly output files to data/processed/by_year/ ...")

    by_year_dir = config.PROCESSED_DIR / "by_year"
    by_year_dir.mkdir(parents=True, exist_ok=True)

    df["year"] = df["date"].dt.year

    for year, group in df.groupby("year"):
        group.drop(columns=["year"]).to_parquet(
            by_year_dir / f"agroclimate_{year}.parquet",
            index=False
        )

    print(
        f"Completed writing {df['year'].nunique()} yearly files "
        f"to {by_year_dir}"
    )


if __name__ == "__main__":
    main()