import edgar as et, os, bs4
from dotenv import load_dotenv
load_dotenv()

class SECIngestor:
    def __init__(self, ticker: str):
        '''Initialize the sec ingestor with a stock ticker symbol.'''
        self.ticker = ticker.upper()
        self.company = et.Company(self.ticker)

    def _get_latest_10q(self):
        filings = self.company.get_filings(form="10-Q")
        return filings.latest()

    def _clean_section(self, section):
        if section is None:
            return ""

        lines = [
            line.strip()
            for line in str(section).splitlines()
            if line.strip()
        ]

        return "\n".join(lines)

    def retrieve_filing(self):
        filing = self._get_latest_10q()
        ten_q = filing.obj()

        mda = ten_q.get_item_with_part("Part I", "Item 2")
        risk_factors = ten_q.get_item_with_part(
            "Part II",
            "Item 1A"
        )

        return {
            "ticker": self.ticker,
            "company_name": self.company.name,
            "cik": self.company.cik,
            "filing_type": filing.form,
            "filing_date": filing.filing_date,
            "accession_number": filing.accession_no,
            "source_url": filing.url,
            "sections": {
                "mda": self._clean_section(mda),
                "risk_factors": self._clean_section(risk_factors),
            },
        }