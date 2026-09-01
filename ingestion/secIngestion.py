import edgar as et, os, bs4
from dotenv import load_dotenv
load_dotenv()

class SECIngestor:
    def __init__(self, ticker: str):
        '''Initialize the sec ingestor with a stock ticker symbol.'''
        self.ticker = ticker.upper()
        self.company = et.Company(self.ticker)

    def _get_filings(self, forms=["10-K", "10-Q"], limit=35):
        filings = self.company.get_filings(form=forms, amendments=False)
        return filings[:limit]

    def _clean_section(self, section):
        if section is None:
            return ""

        lines = [
            line.strip()
            for line in str(section).splitlines()
            if line.strip()
        ]

        return "\n".join(lines)

    def retrieve_filing(self, limit=35):
        filings = self._get_filings(limit=limit)
        results = []
        for filing in filings:
            filing_obj = filing.obj()

            if filing.form == "10-Q":
                mda = filing_obj.get_item_with_part("Part I", "Item 2")
                risk_factors = filing_obj.get_item_with_part("Part II", "Item 1A")
            elif filing.form == "10-K":
                mda = filing_obj.get_item_with_part("Part II", "Item 7")
                risk_factors = filing_obj.get_item_with_part("Part II", "Item 1A")
            else:
                continue

            results.append({
            "ticker": self.ticker,
            "company_name": self.company.name,
            "cik": self.company.cik,
            "filing_type": filing.form,
            "filing_date": filing.filing_date,
            "accession_number": filing.accession_no,
            "source_url": filing.url,
            "sections": {
                "mda": self._clean_section(mda),
                "risk_factors": self._clean_section(
                    risk_factors
                ),
            },
        })

        return results