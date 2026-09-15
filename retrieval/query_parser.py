import re
from rapidfuzz import fuzz
import dateparser

class QueryParser:
    def __init__(self, companies):
        self.companies = self._normalise_companies(companies)
        self.company_suffixes = {
            "inc", "incorporated", "corp", "corporation",
            "ltd", "limited", "plc", "holdings"}

    def _normalise_companies(self, companies):
        normalised = []

        for company in companies:
            if isinstance(company, dict):
                if "ticker" in company and "name" in company:
                    normalised.append(company)
            elif isinstance(company, str):
                normalised.append({"ticker": company, "name": company})

        return normalised

    def normalise_name(self, name):
        name = re.sub(r"[^\w\s]", " ", name.lower())
        words = [word for word in name.split() if word not in self.company_suffixes]

        return " ".join(words)

    def resolve_tickers(self, query):
        query = self.normalise_name(query)
        query_tokens = set(query.split())
        matches = []
        for company in self.companies:
            ticker = company["ticker"]
            company_name = self.normalise_name(company["name"])
            company_tokens = set(company_name.split())

            if re.search(rf"\b{re.escape(ticker.lower())}\b", query.lower()):
                matches.append(ticker)
                continue

            if company_name in query:
                matches.append(ticker)
                continue

            overlap = len(query_tokens & company_tokens)
            token_ratio = overlap / max(1, len(company_tokens))

            # dynamic threshold
            threshold = 0.6 if len(query_tokens) <= 3 else 0.45

            if token_ratio >= threshold:
                matches.append(ticker)
                continue

            score = fuzz.partial_ratio(company_name, query)
            if score >= 75:
                matches.append(ticker)

        return list(dict.fromkeys(matches))

    def extract_datetime(self, query):
        pattern = (
            r"\b(?:as of|as at|before|after|by|through|up to|prior to|around|"
            r"in|for|during|since|until|at|on|around)"
            r"\s+(.+?)(?:\?|$)"
        )

        match = re.search(pattern, query, flags=re.IGNORECASE)
        # print(f"match whole : {match.group(0).strip()}")
        # print(f"match 1st: {match.group(1).strip()}")
        if not match: return None

        date_text = match.group(1).strip()

        if re.fullmatch(r"\d{4}", date_text):
            parsed = dateparser.parse(f"Dec 31 {date_text}", settings={
                "TIMEZONE": "UTC",
                "RETURN_AS_TIMEZONE_AWARE": True
            })
        else:
            parsed = dateparser.parse(date_text, settings={
                "TIMEZONE": "UTC",
                "RETURN_AS_TIMEZONE_AWARE": True
            })
            
        if parsed is None: return None
    
        return parsed.replace(hour=23, minute=59, second=59, microsecond=0)


    def parse(self, query):
        return {"raw_query": query,
                "tickers": self.resolve_tickers(query),
                "cutoff_datetime":self.extract_datetime(query)
        }

