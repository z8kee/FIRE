import sys, time

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from transformers import AutoTokenizer
from ingestion.secIngestion import SECIngestor
niche = "BAAI/bge-small-en-v1.5"
tokenizer = AutoTokenizer.from_pretrained("gpt2")

def chunk_text(text, size=400, overlap=50):
    '''Splits text into chunks to be tokenised with overlaps'''
    tokens = tokenizer.encode(text, add_special_tokens=False)
    chunks = []
    start = 0

    if overlap >= size:
        raise ValueError("Overlap must be smaller than chunk size.")
    
    while start < len(tokens):
        end = start + size
        chunk_tokens = tokens[start:end]

        chunk_part = tokenizer.decode(
            chunk_tokens,
            skip_special_tokens=True,
        )

        chunks.append(chunk_part)
        start += size - overlap

    return chunks

def build_chunks(filing_data):
    '''build chunks from filing data provided'''
    records = []

    for filings in filing_data:
        for section_name, section_text in filings["sections"].items():
            chunks = chunk_text(section_text)
            for i, chunk in enumerate(chunks):
                record = {
                    "ticker": filings["ticker"],
                    "company_name": filings["company_name"],
                    "cik": filings["cik"],
                    "filing_type": filings["filing_type"],
                    "filing_date": filings["filing_date"],
                    "accession_number": filings["accession_number"],
                    "source_url": filings["source_url"],
                    "section_name": section_name,
                    "chunk_id": i,
                    "chunk_text": chunk,
                }
            records.append(record)

    return records











if __name__ == "__main__":
    f = 0
    while f != 2:
        f = int(input("Enter 0 for test, 1 for user input, or 2 to exit: "))
        if f == 0:
            s = time.time()
            test = SECIngestor("AAPL")
            result = test.retrieve_filing(20)
            records = build_chunks(result)
            e = time.time()
            print(records[0])
            print(f"Number of chunks: {len(records)}")
            print(f"Time taken: {e - s:.2f} seconds")
        elif f == 1:
            ticker = input("Enter a stock ticker symbol: ")
            test = SECIngestor(ticker)
            result = test.retrieve_filing(25)
            records = build_chunks(result)
            print(records[0])
            print(f"Number of chunks: {len(records)}")
        elif f == 2:
            break

    sys.exit()