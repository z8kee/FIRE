SELECT COUNT(*)
FROM documents
WHERE acceptance_datetime IS NULL;

SELECT
    c.ticker,
    d.filing_type,
    d.filing_date,
    d.acceptance_datetime,
    d.accession_number
FROM documents d
JOIN companies c
    ON d.company_id = c.company_id
ORDER BY d.acceptance_datetime DESC
LIMIT 20;