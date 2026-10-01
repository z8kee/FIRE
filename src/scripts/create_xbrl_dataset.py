import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.financial_features import FinancialFeatureBuilder
from ingestion.xbrl import XBRLIngestor
import pandas as pd
from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

tickers = ["AAPL", "MSFT", "GOOGL", "AMZN","META", "NVDA",
               "JPM", "ORCL", "INTC", "NFLX", "CSCO", "TSLA",
               "MS", "V", "BLK", "PLTR", "UBER", "NBIS",
               "AMD", "NKE", "WMT", "COST", "HD", "CRM",
               "ADBE", "QCOM", "AVGO", "TXN", "AMGN", "PFE",
               "KO", "PEP", "MCD", "DIS", "CAT", "BA", "GS", "C"]
dataset = []

def build_company_dataset(ticker):
    xbrl = XBRLIngestor(ticker)

    raw = xbrl.get_raw_financials()
    raw["start"] = pd.to_datetime(raw["start"], errors="coerce")
    raw["end"] = pd.to_datetime(raw["end"], errors="coerce")
    raw["duration_days"] = (raw["end"] - raw["start"]).dt.days
    raw["period_type"] = raw.apply(xbrl.classify_period, axis=1)

    quarterly = xbrl.add_acceptance_datetime(
        xbrl.derive_total_debt(
            xbrl.derive_q4_metrics(
                xbrl.derive_quarterly_cash_metrics(
                    xbrl.build_quarterly_observations(
                        raw
                        )
                    )
                )
            )
        )

    features = FinancialFeatureBuilder().build(quarterly)

    return features

if __name__ == "__main__":
    for ticker in tickers[:5]:
        try:
            print(f"Building dataset for {ticker}")
            company_dataset = build_company_dataset(ticker)
            dataset.append(company_dataset)
        except Exception as e:
            print(f"An error occurred while processing {ticker}: {type(e).__name__}: {e}")

    if not dataset:
        raise RuntimeError("No company datasets were built; check the errors above.")

    dataset = pd.concat(dataset, ignore_index=True)
    print("Head: ", dataset.head())
    print("Shape: ", dataset.shape)

    print("Groupby Ticker Size: ", dataset.groupby("ticker").size())

    feature_cols = [
    "current_ratio",
    "operating_margin",
    "net_margin",
    "ocf_margin",
    "fcf_margin",
    "cash_to_assets",
    "revenue_growth_yoy",
    "net_income_change_yoy",
    ]

    missing = (
        dataset[feature_cols]
        .isna()
        .mean()
        .mul(100)
        .sort_values(ascending=False)
    )

    print(missing)

    print(
    dataset.groupby("ticker")[feature_cols]
    .apply(lambda x: x.isna().mean() * 100)
    )
