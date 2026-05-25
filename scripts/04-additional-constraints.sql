ALTER TABLE embeddings
ALTER COLUMN content_tsv
SET EXPRESSION AS (to_tsvector('english', content));