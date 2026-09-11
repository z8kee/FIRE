SELECT c.ticker, COUNT(*)
FROM chunks ch
JOIN documents d ON ch.document_id = d.document_id
JOIN companies c ON d.company_id = c.company_id
WHERE c.ticker = 'MSFT'
GROUP BY c.ticker;