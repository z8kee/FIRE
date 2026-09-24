import os, time, sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"

for path in (PROJECT_ROOT, SRC_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from ingestion.xbrl import XBRLIngestor
from dotenv import load_dotenv

load_dotenv()

def main():
    xbrl = XBRLIngestor("AAPL")
    df = xbrl.get_raw_financials()
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns}")
    print(f"Lengh of dataset: {df.__len__()}")

    #print(
    #    df[
    #        ["metric", "value", "start", "end", "form", "fy", "fp", "accession_number"]
    #    ].tail(30)
    #)

    revenue = df[df["metric"] == "revenue"]

    quarter = revenue[
        revenue["form"] == "10-Q"
    ]

    print(
        quarter[
            ["start", "end", "value", "form", "fy", "fp", "filed", "frame", "accession_number"]
        ].tail(40)
    )

    print(revenue["fp"].value_counts())

    df["start"] = pd.to_datetime(df["start"])
    df["end"] = pd.to_datetime(df["end"])

    df["duration_days"] = (
        df["end"] - df["start"]
    ).dt.days

    def classify_period(row):
        if pd.isna(row["start"]):
            return "instant"

        days = row["duration_days"]

        if 70 <= days <= 110:
            return "quarter"

        if 150 <= days <= 210:
            return "ytd_6m"

        if 240 <= days <= 300:
            return "ytd_9m"

        if 330 <= days <= 400:
            return "annual"

        return "other"

    df["period_type"] = df.apply(
        classify_period,
        axis=1,
    )

    print(
        df[df["metric"] == "revenue"][
            ["start", "end", "duration_days", "period_type", "value", "form", "fp", "frame",]
        ].tail(50)
    )

if __name__ == "__main__":
    main()