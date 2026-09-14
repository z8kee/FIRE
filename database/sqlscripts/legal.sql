SELECT
	ch.section,
	c.name AS company,
	LEFT(ch.text, 1000) AS text
FROM chunks ch
JOIN documents d
	ON ch.document_id = d.document_id
JOIN companies c
	ON d.company_id = c.company_id
WHERE ch.section ILIKE '%legal_proceedings%';