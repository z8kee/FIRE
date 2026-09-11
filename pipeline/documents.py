import sys

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-small-en-v1.5")
tokenizer.model_max_length = 10**9

def chunk_text(text, size=400, overlap=50):
    '''Splits text into chunks to be tokenised with overlaps'''
    tokens = tokenizer.encode(text, add_special_tokens=False, truncation=False)
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

            if len(chunks) == 0:
                continue
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
                    "chunk_index": i,
                    "chunk_text": chunk,
                }
                records.append(record)

    return records