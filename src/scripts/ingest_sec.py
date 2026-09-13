import os, sys, time
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.secIngestion import SECIngestor
from pipeline.documents import build_chunks
from database.connections import SECRepository
from edgar import CompanyNotFoundError
from dotenv import load_dotenv
load_dotenv()


def main():
    #making secingestor objects with tickers
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN","META", "NVDA",
               "JPM", "ORCL", "INTC", "NFLX", "CSCO", "TSLA",
               "MS", "V", "BLK", "PLTR", "UBER", "NBIS",
               "AMD", "NKE", "WMT", "COST", "HD", "CRM",
               "ADBE", "QCOM", "AVGO", "TXN", "AMGN", "PFE",
               "KO", "PEP", "MCD", "DIS", "CAT", "BA", "GS", "C"]
    db = SECRepository(dbname='fire_rag',
                        user='fire_user', 
                        password=os.getenv("POSTGRESPASS")
                        )
    #already did aapl for testing
    for ticker in tickers:
        #if ticker doesnt exist
        print(f"Retrieving filings for {ticker}")
        try:
            ingestor = SECIngestor(ticker)
        except CompanyNotFoundError as e:
            print(f"An error occurred: {type(e).__name__}: {e}")
            continue
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
                filing["acceptance_datetime"],
                filing["source_url"]
            )

            # build chunks from the filing data
            records = build_chunks([filing])

            # insert chunks into the database
            for record in records:
                db.insert_chunk(
                    document_id,
                    record["section_name"],
                    record["chunk_index"],
                    record["chunk_text"]
                )
        db.commit()
        
    db.close()

if __name__ == "__main__":
    s = time.time()
    main()
    e = time.time()
    time_took = round((e - s)/60, 2)
    if time_took > 60:
        print(f"Time taken: {round((time_took/60), 1)} hours")
    else:
        print(f"Time taken: {round((e - s)/60, 2)} minutes")