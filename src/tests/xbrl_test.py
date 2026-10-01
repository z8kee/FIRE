import os, time, sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"

for path in (PROJECT_ROOT, SRC_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from ingestion.xbrl import XBRLIngestor
from pipeline.financial_features import FinancialFeatureBuilder
from dotenv import load_dotenv

load_dotenv()

def main():
    xbrl = XBRLIngestor("AAPL")
    builder = FinancialFeatureBuilder()
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


    df["period_type"] = df.apply(
        xbrl.classify_period,
        axis=1,
    )

    # print(
    #     df[df["metric"] == "revenue"][
    #         ["start", "end", "duration_days", "period_type", "value", "form", "fp", "frame",]
    #     ].tail(50)
    # )

    # quarter = xbrl.build_quarterly_observations(df)
    # print(
    #     quarter[
    #         [
    #             "fiscal_year",
    #             "fiscal_quarter",
    #             "revenue",
    #             "net_income",
    #             "operating_income",
    #             "current_assets",
    #             "current_liabilities",
    #             "total_assets",
    #             "equity",
    #             "cash"
    #         ]
    #     ].tail(12)
    # )

    # print(df[df["form"]=="10-K"][["fy", "fp", "accession_number"]].drop_duplicates().tail(10))

    quarterly = xbrl.build_quarterly_observations(df)
    quarterly = xbrl.derive_quarterly_cash_metrics(quarterly)
    quarterly = xbrl.derive_q4_metrics(quarterly)
    features = builder.build(quarterly)
    print(
        features[
            [
                "fiscal_year",
                "fiscal_quarter",
                "current_ratio",
                "operating_margin",
                "net_margin",
                "ocf_margin",
                "fcf_margin",
                "cash_to_assets",
                "revenue_growth_yoy",
                "net_income_change_yoy"
            ]
        ].tail(12)
    )
if __name__ == "__main__":
    main()