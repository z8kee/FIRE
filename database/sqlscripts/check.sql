-- Checking if everything joined correctly.

SELECT COUNT(*) FROM companies;
SELECT COUNT(*) FROM documents;
SELECT COUNT(*) FROM chunks;

SELECT
    c.ticker,
    d.filing_type,
    d.filing_date,
    ch.section,
    ch.chunk_index,
    LEFT(ch.text, 300) AS preview
FROM chunks ch
JOIN documents d
    ON ch.document_id = d.document_id
JOIN companies c
    ON d.company_id = c.company_id
ORDER BY d.filing_date DESC, ch.section, ch.chunk_index
LIMIT 50;

