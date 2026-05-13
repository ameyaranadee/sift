-- Run this in your Supabase SQL editor

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE artworks (
    id BIGINT PRIMARY KEY,                  -- Harvard objectid
    object_number TEXT,
    title TEXT,
    dated TEXT,
    date_begin INT,
    date_end INT,
    medium TEXT,
    technique TEXT,
    classification TEXT,
    period TEXT,
    century TEXT,
    -- Artwork-level geographic/cultural context
    culture TEXT,                           -- e.g. "Dutch", "American"
    division TEXT,                          -- e.g. "European and American Art"
    department TEXT,
    -- Artist info (first artist from people array)
    artist_name TEXT,
    artist_culture TEXT,
    artist_display_date TEXT,
    artist_birthplace TEXT,
    artist_deathplace TEXT,
    -- Physical dimensions parsed from the dimensions string
    dimensions TEXT,                        -- raw string, e.g. "34.5 x 45 cm (13 9/16 x 17 11/16 in.)"
    dim_height_cm FLOAT,
    dim_width_cm FLOAT,
    -- Image
    primary_image_url TEXT,                 -- IIIF base URL
    artwork_url TEXT,                       -- Harvard collections page URL
    -- Text
    description TEXT,
    label_text TEXT,
    credit_line TEXT,
    -- Quality signals
    access_level INT,
    verification_level INT,
    total_page_views INT,
    total_unique_page_views INT,
    raw JSONB,                              -- full API response
    embedding vector(3072),                 -- gemini-embedding-2
    embedding_type TEXT,                    -- 'multimodal' | 'text'
    source TEXT NOT NULL DEFAULT 'harvard',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- HNSW index for fast cosine similarity search.
-- vector(3072) exceeds pgvector's HNSW limit of 2000 dims, so we cast to halfvec
-- (16-bit floats) which halves memory and lifts the dimension limit with negligible
-- accuracy loss at this scale.
CREATE INDEX artworks_embedding_idx
    ON artworks USING hnsw ((embedding::halfvec(3072)) halfvec_cosine_ops);

-- Metadata filters used in search
CREATE INDEX artworks_classification_idx ON artworks (classification);
CREATE INDEX artworks_century_idx ON artworks (century);
CREATE INDEX artworks_culture_idx ON artworks (culture);
CREATE INDEX artworks_division_idx ON artworks (division);
CREATE INDEX artworks_dates_idx ON artworks (date_begin, date_end);
CREATE INDEX artworks_source_idx ON artworks (source);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER artworks_updated_at
    BEFORE UPDATE ON artworks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Random artwork sampler — used for the home page discovery grid.
-- ORDER BY RANDOM() is fine at ~40k rows; revisit with tablesample if the table grows large.
CREATE OR REPLACE FUNCTION random_artworks(count INT DEFAULT 20)
RETURNS TABLE (
    id BIGINT,
    title TEXT,
    artist_name TEXT,
    culture TEXT,
    division TEXT,
    dated TEXT,
    century TEXT,
    medium TEXT,
    classification TEXT,
    primary_image_url TEXT,
    artwork_url TEXT,
    similarity FLOAT
)
LANGUAGE sql AS $$
    SELECT
        id, title, artist_name, culture, division, dated, century, medium,
        classification, primary_image_url, artwork_url,
        0.0::FLOAT AS similarity
    FROM artworks
    WHERE primary_image_url IS NOT NULL
    ORDER BY RANDOM()
    LIMIT count;
$$;

-- Similarity search function (returns matches above threshold, filtered by metadata).
-- Casts both sides to halfvec(3072) so the query uses the HNSW index.
CREATE OR REPLACE FUNCTION search_artworks(
    query_embedding vector(3072),
    match_threshold FLOAT DEFAULT 0.3,
    match_count INT DEFAULT 20,
    filter_classification TEXT DEFAULT NULL,
    filter_century TEXT DEFAULT NULL,
    filter_culture TEXT DEFAULT NULL,
    filter_division TEXT DEFAULT NULL
)
RETURNS TABLE (
    id BIGINT,
    title TEXT,
    artist_name TEXT,
    culture TEXT,
    division TEXT,
    dated TEXT,
    century TEXT,
    medium TEXT,
    classification TEXT,
    primary_image_url TEXT,
    artwork_url TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql AS $$
DECLARE
    query_halfvec halfvec(3072) := query_embedding::halfvec(3072);
BEGIN
    RETURN QUERY
    SELECT
        a.id,
        a.title,
        a.artist_name,
        a.culture,
        a.division,
        a.dated,
        a.century,
        a.medium,
        a.classification,
        a.primary_image_url,
        a.artwork_url,
        1 - (a.embedding::halfvec(3072) <=> query_halfvec) AS similarity
    FROM artworks a
    WHERE
        a.embedding IS NOT NULL
        AND 1 - (a.embedding::halfvec(3072) <=> query_halfvec) > match_threshold
        AND (filter_classification IS NULL OR a.classification = filter_classification)
        AND (filter_century IS NULL OR a.century = filter_century)
        AND (filter_culture IS NULL OR a.culture = filter_culture)
        AND (filter_division IS NULL OR a.division = filter_division)
    ORDER BY a.embedding::halfvec(3072) <=> query_halfvec
    LIMIT match_count;
END;
$$;
