"""
Step 7 of the research plan: perform quality control on the raw data generated
by 02_download_weather.py, including missing values, duplicates, range checks,
and temporal continuity (Section 9).

Read all data/raw/agroclimate_<year>.parquet files, run quality checks,
write reports to metadata/quality_control_report.csv, and save the QC-processed
data to data/processed/. Rows with range violations are flagged rather than
immediately removed to keep cleaning decisions transparent.

Usage:
    python 03_quality_control.py
"""

import sys
from pathlib import Path

import pandas as pd

import config


def load_raw_data(raw_dir: Path) -> pd.DataFrame:
    files = sorted(raw_dir.glob("agroclimate_*.parquet"))

    if not files:
        print(
            f"ERROR: no agroclimate_*.parquet files found in {raw_dir}. "
            "Run 02_download_weather.py first.",
            file=sys.stderr
        )
        sys.exit(1)

    print(f"Reading {len(files)} files: {[f.name for f in files]}")

    return pd.concat(
        (pd.read_parquet(f) for f in files),
        ignore_index=True
    )


def check_missing(df: pd.DataFrame) -> pd.DataFrame:
    missing = df.isna().sum()
    missing = missing[missing > 0]

    report = pd.DataFrame({
        "check": "missing_values",
        "column": missing.index,
        "count": missing.values,
        "pct_of_rows": (missing.values / len(df) * 100).round(4),
    })

    return report


def check_duplicates(
    df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    dup_mask = df.duplicated(
        subset=["grid_id", "date"],
        keep="first"
    )

    n_dup = int(dup_mask.sum())

    report = pd.DataFrame([{
        "check": "duplicate_grid_id_date",
        "column": "grid_id+date",
        "count": n_dup,
        "pct_of_rows": round(n_dup / len(df) * 100, 4),
    }])

    return report, df[dup_mask]


def check_ranges(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    flags = pd.Series(False, index=df.index)

    for col, (lo, hi) in config.QC_RANGES.items():
        if col not in df.columns:
            continue

        violation = (df[col] < lo) | (df[col] > hi)
        violation = violation.fillna(False)
        flags |= violation

        rows.append({
            "check": "range_violation",
            "column": col,
            "count": int(violation.sum()),
            "pct_of_rows": round(violation.sum() / len(df) * 100, 4),
        })

    return pd.DataFrame(rows), flags


def check_temporal_continuity(df: pd.DataFrame) -> pd.DataFrame:
    """Check whether dates for each grid_id form a continuous daily sequence
    without gaps, as described in Section 9."""
    rows = []

    for grid_id, group in df.groupby("grid_id"):
        dates = pd.to_datetime(group["date"]).sort_values()
        expected_days = (dates.max() - dates.min()).days + 1
        actual_days = dates.nunique()
        gap = expected_days - actual_days

        if gap > 0:
            rows.append({
                "grid_id": grid_id,
                "missing_days": gap,
                "first_date": dates.min().date(),
                "last_date": dates.max().date()
            })

    if not rows:
        return pd.DataFrame(
            columns=[
                "grid_id",
                "missing_days",
                "first_date",
                "last_date"
            ]
        )

    return pd.DataFrame(rows).sort_values(
        "missing_days",
        ascending=False
    )


def main():
    df = load_raw_data(config.RAW_DIR)
    df["date"] = pd.to_datetime(df["date"])

    print(f"Total raw rows: {len(df):,}")

    reports = []

    print("Checking missing values ...")
    reports.append(check_missing(df))

    print("Checking duplicates (grid_id + date) ...")
    dup_report, dup_rows = check_duplicates(df)
    reports.append(dup_report)

    df = df.drop_duplicates(
        subset=["grid_id", "date"],
        keep="first"
    )

    print("Checking variable value ranges ...")
    range_report, range_flags = check_ranges(df)
    reports.append(range_report)

    df["qc_range_flag"] = range_flags

    print(
        "Checking temporal continuity for each grid_id "
        "(this may take some time) ..."
    )
    continuity_report = check_temporal_continuity(df)

    full_report = pd.concat(
        reports,
        ignore_index=True
    )

    config.METADATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    report_path = (
        config.METADATA_DIR / "quality_control_report.csv"
    )
    full_report.to_csv(
        report_path,
        index=False
    )

    continuity_path = (
        config.METADATA_DIR / "temporal_continuity_gaps.csv"
    )
    continuity_report.to_csv(
        continuity_path,
        index=False
    )

    out_path = (
        config.PROCESSED_DIR / "agroclimate_qc.parquet"
    )
    df.to_parquet(
        out_path,
        index=False
    )

    print("\n=== QC SUMMARY ===")
    print(full_report.to_string(index=False))

    print(
        f"\nGrid points with date gaps: {len(continuity_report)} "
        f"out of {df['grid_id'].nunique()} grid points"
    )

    print(f"\nQC report           : {report_path}")
    print(f"Temporal continuity : {continuity_path}")

    print(
        f"QC-flagged data     : {out_path} "
        "(qc_range_flag=True identifies rows with values outside "
        "the configured ranges; decide whether to remove or retain "
        "them with appropriate documentation)"
    )


if __name__ == "__main__":
    main()