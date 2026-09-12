import os, sys, edgar as et
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
from database.connections import SECRepository

load_dotenv()

def backfill():
    db = SECRepository(dbname='fire_rag',
                            user='fire_user', 
                            password=os.getenv("POSTGRESPASS")
                            )

    docs = db.get_docs_missing_timestamp()
    print(f"{len(docs)} documents that need to be updated")

    #group existing db docs by company
    docs_by_ticker = defaultdict(list)

    for doc in docs:
        docs_by_ticker[doc["ticker"]].append(doc)

    updated = 0
    failed = 0

    for ticker, company_docs in docs_by_ticker.items():
        print(f"\nRetrieving metadata for {ticker}...")

        try:
            company = et.Company(ticker)

            # EntityFilings -> contains acceptance_datetime
            filings = company.get_filings(
                form=["10-K", "10-Q"],
                amendments=False,
                trigger_full_load=True
            )

            # accession -> EntityFiling
            filing_lookup = {filing.accession_no: filing for filing in filings}

            for document in company_docs:
                accession = document["accession_number"]

                filing = filing_lookup.get(accession)

                if filing is None:
                    print(f"Could not find {accession}")
                    failed += 1
                    continue

                acceptance_datetime = (filing.acceptance_datetime)

                db.update_acceptance_datetime(
                    document["document_id"],
                    acceptance_datetime
                )

                updated += 1

            # commit once per company
            db.commit()

            print(
                f"{ticker}: updated "
                f"{len(company_docs)} documents"
            )

        except Exception as e:
            print(
                f"Failed {ticker}: "
                f"{type(e).__name__}: {e}"
            )

    db.close()

    print("\nFinished.")
    print(f"Updated: {updated}")
    print(f"Failed: {failed}")
if __name__ == "__main__":
    backfill()