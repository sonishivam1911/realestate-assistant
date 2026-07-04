-- Real estate CMA chat schema
-- Target: Contabo homelab Postgres (same stack as minaki — supabase_db / POSTGRES_URI_CONTABO)
-- Apply: psql "$POSTGRES_URI" -f db/schema.sql

CREATE SCHEMA IF NOT EXISTS realestate;

-- ---------------------------------------------------------------------------
-- Conversations (ChatGPT-style threads)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS realestate.conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           TEXT,
    user_id         TEXT,                          -- optional auth subject
    user_email      TEXT,                          -- for CMA report delivery
    subject_address TEXT,                          -- primary property address
    radius_miles    NUMERIC(4,1) DEFAULT 5.0,
    status          TEXT NOT NULL DEFAULT 'active', -- active | archived
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_re_conversations_user
    ON realestate.conversations (user_id, updated_at DESC);

-- ---------------------------------------------------------------------------
-- Messages (user + assistant turns)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS realestate.messages (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id  UUID NOT NULL REFERENCES realestate.conversations(id) ON DELETE CASCADE,
    role             TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content          TEXT NOT NULL,
    metadata         JSONB NOT NULL DEFAULT '{}',   -- model, tokens, node, etc.
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_re_messages_conversation
    ON realestate.messages (conversation_id, created_at ASC);

-- ---------------------------------------------------------------------------
-- CMA workflow runs (one per analysis request)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS realestate.cma_runs (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id  UUID REFERENCES realestate.conversations(id) ON DELETE SET NULL,
    message_id       UUID REFERENCES realestate.messages(id) ON DELETE SET NULL,
    status           TEXT NOT NULL DEFAULT 'pending', -- pending | researching | synthesizing | complete | failed
    subject_property JSONB NOT NULL DEFAULT '{}',
    geo              JSONB NOT NULL DEFAULT '{}',
    radius_miles     NUMERIC(4,1),
    timeframe_months INT DEFAULT 3,
    comp_research    JSONB,
    market_pulse     JSONB,
    macro_context    JSONB,
    cma_report       JSONB,
    errors           JSONB NOT NULL DEFAULT '[]',
    started_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at     TIMESTAMPTZ,
    duration_ms      INT
);

CREATE INDEX IF NOT EXISTS idx_re_cma_runs_conversation
    ON realestate.cma_runs (conversation_id, started_at DESC);

-- ---------------------------------------------------------------------------
-- Citations (URLs from web search — comps, macro, market)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS realestate.citations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cma_run_id  UUID NOT NULL REFERENCES realestate.cma_runs(id) ON DELETE CASCADE,
    branch      TEXT NOT NULL CHECK (branch IN ('comps', 'market', 'macro', 'other')),
    url         TEXT NOT NULL,
    title       TEXT,
    snippet     TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_re_citations_run
    ON realestate.citations (cma_run_id);

-- ---------------------------------------------------------------------------
-- Comparable sales extracted from CMA (queryable)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS realestate.comparables (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cma_run_id      UUID NOT NULL REFERENCES realestate.cma_runs(id) ON DELETE CASCADE,
    address         TEXT NOT NULL,
    sold_date       DATE,
    sold_price      NUMERIC(12,2),
    sqft            INT,
    bedrooms        NUMERIC(3,1),
    bathrooms       NUMERIC(3,1),
    price_per_sqft  NUMERIC(10,2),
    distance_miles  NUMERIC(5,2),
    property_type   TEXT,
    source_url      TEXT,
    source_name     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_re_comparables_run
    ON realestate.comparables (cma_run_id);

-- ---------------------------------------------------------------------------
-- updated_at trigger for conversations
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION realestate.touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_conversations_updated ON realestate.conversations;
CREATE TRIGGER trg_conversations_updated
    BEFORE UPDATE ON realestate.conversations
    FOR EACH ROW EXECUTE FUNCTION realestate.touch_updated_at();

-- Migrations (safe to re-run)
ALTER TABLE realestate.conversations
    ADD COLUMN IF NOT EXISTS user_email TEXT;

ALTER TABLE realestate.cma_runs
    ADD COLUMN IF NOT EXISTS email_sent_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_re_conversations_email
    ON realestate.conversations (user_email) WHERE user_email IS NOT NULL;
