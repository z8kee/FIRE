SELECT
    ch.chunk_id,
    d.filing_date,
    ch.section,
    LEFT(ch.text, 1000) AS text
FROM chunks ch
JOIN documents d
    ON ch.document_id = d.document_id
JOIN companies c
    ON d.company_id = c.company_id
WHERE c.ticker = 'NFLX'
  AND d.filing_date <= '2022-12-31'
  AND (
      ch.text ILIKE '%competition%'
      OR ch.text ILIKE '%competitors%'
      OR ch.text ILIKE '%competitive%'
  )
ORDER BY d.filing_date DESC;