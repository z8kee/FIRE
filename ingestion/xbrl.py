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

    a