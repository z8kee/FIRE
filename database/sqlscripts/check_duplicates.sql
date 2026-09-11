SELECT
    document_id,
    section,
    chunk_index,
    COUNT(*)
FROM chunks
GROUP BY document_id, section, chunk_index
HAVING COUNT(*) > 1;