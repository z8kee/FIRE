import edgar as et, os, bs4
from dotenv import load_dotenv
load_dotenv()

class SECIngestor:
    def __init__(self, ticker: str):
        '''Initialize the sec ingestor with a stock ticker symbol.'''
        self.ticker = ticker.upper()
        self.company = et.Company(self.ticker)
        self.ten_k_sections = {
            "business": "Item 1",
            "risk_factors": "Item 1A",
            "cybersecurity": "Item 1C",
            "legal_proceedings": "Item 3",
            "mda": "Item 7",
            "market_risk": "Item 7A",
        }
        self.ten_q_sections = {
            "mda": ("Part I", "Item 2"),
            "market_risk": ("Part I", "Item 3"),
            "legal_proceedings": ("Part II", "Item 1"),
            "risk_factors": ("Part II", "Item 1A"),
            "other_information": ("Part II", "Item 5"),
        }

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

    def _extract_sections(self, filing_obj, types):
        sections = {}
        if types == "10-K":
            for section_name, item in self.ten_k_sections.items():
                try:
                    text = filing_obj[item]
                except Exception:
                    text = None

                sections[section_name] = self._clean_section(text)

        elif types == "10-Q":
            for section_name, (part, item) in self.ten_q_sections.items():
                try:
                    text = filing_obj.get_item_with_part(part, item)
                except Exception:
                    text = None
    
                sections[section_name] = self._clean_section(text)

        return sections

    def retrieve_filing(self, limit=35):
        filings = self._get_filings(limit=limit)
        results = []
        for filing in filings:
            try:
                print(
                    "Processing: ",
                    self.ticker,
                    filing.form,
                    filing.filing_date,
                    filing.accession_no
                )
                if filing.homepage.primary_html_document is None:
                    print(f"Skipping {filing.accession_no} due to missing primary HTML document.")
                    continue
                filing_obj = filing.obj()

                if filing.form == "10-Q":
                    sections = self._extract_sections(filing_obj, "10-Q")
                elif filing.form == "10-K":
                    sections = self._extract_sections(filing_obj, "10-K") 
                else:
                    continue

                results.append({
                    "ticker": self.ticker,
                    "company_name": self.company.name,
                    "cik": self.company.cik,
                    "filing_type": filing.form,
                    "filing_date": filing.filing_date,
                    "acceptance_datetime": filing.acceptance_datetime,
                    "accession_number": filing.accession_no,
                    "source_url": filing.url,
                    "sections": sections
                    }
                )
            except Exception as e:
                print(
                    f"Skipping {filing.accession_no}: "
                    f"{type(e).__name__}: {e}"
                )
            continue
        
        return results