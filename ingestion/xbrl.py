import edgar as et, os, requests, pandas as pd

class XBRLIngestor:
    def __init__(self, ticker: str):
        et.set_identity(os.getenv("EDGAR_IDENTITY"))
        self.ticker = ticker.upper()
        company = et.Company(self.ticker)
        self.cik = int(company.cik)

        self.headers = {
            "User-Agent": os.getenv("EDGAR_IDENTITY")
        }

        self.concepts = {
            "revenue": [
                "RevenueFromContractWithCustomerExcludingAssessedTax",
                "Revenues",
                "SalesRevenueNet",
            ],

            "net_income": [
                "NetIncomeLoss",
            ],

            "operating_income": [
                "OperatingIncomeLoss",
            ],

            "current_assets": [
                "AssetsCurrent",
            ],

            "current_liabilities": [
                "LiabilitiesCurrent",
            ],

            "total_assets": [
                "Assets",
            ],

            "equity": [
                "StockholdersEquity",
                "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
            ],

            "cash": [
                "CashAndCashEquivalentsAtCarryingValue",
            ],

            "operating_cash_flow": [
                "NetCashProvidedByUsedInOperatingActivities",
            ],

            "capex": [
                "PaymentsToAcquirePropertyPlantAndEquipment",
            ],
            "debt_current": [
                "DebtCurrent",
            ],

            "short_term_borrowings": [
                "ShortTermBorrowings",
                "CommercialPaper",
            ],

            "long_term_debt_current": [
                "LongTermDebtCurrent",
            ],

            "long_term_debt_noncurrent": [
                "LongTermDebtNoncurrent",
            ],

            "long_term_debt_total": [
                "LongTermDebt",
            ],
        }

        self.quarter_metrics = {
            "revenue",
            "net_income",
            "operating_income"
        }

        self.instant_metrics = {
            "current_assets",
            "current_liabilities",
            "total_assets",
            "equity",
            "cash"
        }

        self.cumulative_metrics = {
            "operating_cash_flow",
            "capex"
        }

    def get_company_facts(self):
        cik = str(self.cik).zfill(10)

        url = (
            "https://data.sec.gov/api/xbrl/"
            f"companyfacts/CIK{cik}.json"
        )

        response = requests.get(
            url,
            headers=self.headers,
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    def get_concept(self, concept, unit="USD"):
        data = self.get_company_facts()

        gaap = data["facts"]["us-gaap"]

        if concept not in gaap:
            return []

        concept_data = gaap[concept]

        units = concept_data.get("units", {})

        return units.get(unit, [])

    def get_raw_financials(self):
        data = self.get_company_facts()
        gaap = data["facts"]["us-gaap"]
        rows = []

        for metric, cand in self.concepts.items():
            for priority, concept in enumerate(cand):
                if concept not in gaap:
                    continue

                concept_data = gaap[concept]

                for unit, facts in concept_data.get("units", {}).items():
                    if unit != "USD":
                        continue

                    for fact in facts:
                        if fact.get("form") not in {"10-K", "10-Q"}:
                            continue

                        rows.append({
                            "ticker": self.ticker,
                            "metric": metric,
                            "concept": concept,
                            "concept_priority": priority,
                            "value": fact.get("val", ""),
                            "start": fact.get("start", ""),
                            "end": fact.get("end", ""),
                            "filed": fact.get("filed", ""),
                            "form": fact.get("form", ""),
                            "fy": fact.get("fy", ""),
                            "fp": fact.get("fp", ""),
                            "accession_number": fact.get("accn", ""),
                            "frame": fact.get("frame", ""),
                        })

        return pd.DataFrame(rows)


    def get_fiscal_quarter(self, form, fp):
        if form == "10-Q":
            mapping = {
                "Q1": 1,
                "Q2": 2,
                "Q3": 3,
            }
            return mapping.get(fp)

        if form == "10-K":
            return 4

        return None

    def build_quarterly_observations(self, df):
        df = df.copy()

        df["start"] = pd.to_datetime(
            df["start"],
            errors="coerce"
        )

        df["end"] = pd.to_datetime(
            df["end"],
            errors="coerce"
        )

        df["fiscal_quarter"] = df.apply(
            lambda row: self.get_fiscal_quarter(
                row["form"],
                row["fp"]
            ),
            axis=1
        )

        df = df[
            df["fiscal_quarter"].notna()
        ]

        observations = []

        for accession, filing in df.groupby(
            "accession_number"
        ):
            quarter = int(
                filing["fiscal_quarter"].iloc[0]
            )

            # Latest period represented by this filing
            current_end = filing["end"].max()

            row = {
                "ticker": filing["ticker"].iloc[0],
                "accession_number": accession,
                "filing_date": filing["filed"].iloc[0],
                "fiscal_year": filing["fy"].iloc[0],
                "fiscal_quarter": quarter,
                "period_end": current_end,
            }

            for metric in self.quarter_metrics:
                if quarter in {1,2,3}:
                    candidates = filing[
                        (filing["metric"] == metric)
                        & (filing["period_type"] == "quarter")
                        & (filing["end"] == current_end)
                    ]

                else:
                    candidates = filing[
                        (filing["metric"] == metric)
                        & (filing["period_type"] == "annual")
                        & (filing["end"] == current_end)
                    ]

                if not candidates.empty:
                    candidates = candidates.sort_values(
                        "concept_priority"
                    )
                    if quarter == 4:
                        row[f"{metric}_annual"] = (
                            candidates.iloc[0]["value"]
                        )

                        row[metric] = None
                    else:
                        row[metric] = (
                            candidates.iloc[0]["value"]
                        )

                else:
                    row[metric] = None

                    if quarter == 4:
                        row[f"{metric}_annual"] = None

            for metric in self.instant_metrics:

                candidates = filing[
                    (filing["metric"] == metric)
                    & (filing["end"] == current_end)
                ].copy()

                if not candidates.empty:
                    candidates = candidates.sort_values(
                        "concept_priority"
                    )

                    row[metric] = (
                        candidates.iloc[0]["value"]
                    )

                else:
                    row[metric] = None

            for metric in self.cumulative_metrics:

                metric_rows = filing[
                    filing["metric"] == metric
                ].copy()

                if metric_rows.empty:
                    row[f"{metric}_cumulative"] = None
                    continue

                if quarter == 1:
                    wanted_type = "quarter"

                elif quarter == 2:
                    wanted_type = "ytd_6m"

                elif quarter == 3:
                    wanted_type = "ytd_9m"

                else:
                    wanted_type = "annual"

                candidates = metric_rows[
                    metric_rows["period_type"] == wanted_type
                ]

                candidates = candidates[
                    candidates["end"] == current_end
                ]

                if not candidates.empty:
                    candidates = candidates.sort_values(
                        "concept_priority"
                    )

                    row[f"{metric}_cumulative"] = (
                        candidates.iloc[0]["value"]
                    )
                else:
                    row[f"{metric}_cumulative"] = None

            observations.append(row)

        result = pd.DataFrame(observations)

        return result.sort_values(
            ["fiscal_year", "fiscal_quarter"]
        )

    def classify_period(self, row):
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
    
    def derive_quarterly_cash_metrics(self, df):
        df = df.copy()

        df = df.sort_values(
            ["ticker", "fiscal_year", "fiscal_quarter"]
            )

        for metric in ["operating_cash_flow", "capex"]:
            cumulative = f"{metric}_cumulative"
            df[metric] = None

            for _, group in df.groupby(
                ["ticker", "fiscal_year"]
            ):
                group = group.sort_values(
                    "fiscal_quarter"
                )

                previous_cumulative = 0

                for idx, row in group.iterrows():
                    current = row[cumulative]

                    if pd.isna(current):
                        continue

                    df.loc[idx, metric] = (
                        current - previous_cumulative
                    )

                    previous_cumulative = current

        return df

    def derive_q4_metrics(self, df):
        df = df.copy()

        df = df.sort_values(["ticker", "fiscal_year", "fiscal_quarter"])

        for metric in ["revenue", "net_income", "operating_income"]:
            annual_col = f"{metric}_annual"

            if annual_col not in df.columns:
                continue

            for _, group in df.groupby(
                ["ticker", "fiscal_year"]
            ):

                q4 = group[group["fiscal_quarter"] == 4]

                if q4.empty:
                    continue

                q4_idx = q4.index[0]
                annual = df.loc[q4_idx, annual_col]

                if pd.isna(annual):
                    continue

                first_three = group[
                    group["fiscal_quarter"].isin(
                        [1, 2, 3]
                    )
                ][metric]

                if (len(first_three) != 3 or first_three.isna().any()):
                    continue

                df.loc[q4_idx, metric] = (
                    annual - first_three.sum()
                )

        return df