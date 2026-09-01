from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-small-en-v1.5")

def chunk_text(text, size=400, overlap=50):
    '''Splits text into chunks to be tokenised with overlaps'''

    tokens = tokenizer.encode(text, add_special_tokens=False)
    chunks = []
    start = 0
    while start < len(tokens):
        end = start + size
        chunk_tokens = tokens[start:end]

        chunk_text = tokenizer.decode(
            chunk_tokens,
            skip_special_tokens = True
        )

        chunks.append(chunk_text)
        start += size - overlap

    return chunks
