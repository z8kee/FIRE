import os, sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.secIngestion import SECIngestor
from pipeline.documents import build_chunks
from database.connections import SECRepository
from dotenv import load_dotenv
load_dotenv()


def main():
    #making secingestor objects with tickers
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "JPM"]
    ingestor = SECIngestor(tickers[0])

    db = SECRepository(dbname='sec_data',
                        user='postgres', 
                        password=os.getenv("POSTGRESPASS")
                        )

    filings = ingestor.retrieve_filing()

    for filing in filings:
        # insert company into the database
        company_id = db.insert_company(
            filing["ticker"],
            filing["company_name"],
            filing["cik"]
        )

        # insert document into the database
        document_id = db.insert_document(
            company_id,
            filing["accession_number"],
            filing["filing_type"],
            filing["filing_date"],
            filing["source_url"]
        )

        # build chunks from the filing data
        records = build_chunks([filing])

        # insert chunks into the database
        for record in records:
            db.insert_chunk(
                document_id,
                record["section_name"],
                record["chunk_id"],
                record["chunk_text"]
            )
    db.commit()
    db.close()

if __name__ == "__main__":
    main()