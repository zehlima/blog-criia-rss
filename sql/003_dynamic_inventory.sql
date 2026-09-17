-- Additive rollout after 001_schema.sql. Enable BORIS_DYNAMIC_INVENTORY=1 in
-- collector, trends, daily and dashboard jobs only after applying this file.
-- This file never changes a historical run, attempt, closure or feed identity.
BEGIN;
CREATE TABLE IF NOT EXISTS public.news_feed_admissions (
 feed_id bigint PRIMARY KEY REFERENCES public.news_feeds(id),
 effective_at timestamptz NOT NULL,
 actor text NOT NULL CHECK (btrim(actor)<>''),
 reason text NOT NULL CHECK (btrim(reason)<>''),
 evidence jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(evidence)='object'),
 admitted_at timestamptz NOT NULL DEFAULT now(),
 revoked_at timestamptz,
 CHECK (effective_at>=admitted_at),
 CHECK (revoked_at IS NULL OR revoked_at>=admitted_at)
);
CREATE INDEX IF NOT EXISTS news_feed_admissions_effective
 ON public.news_feed_admissions(effective_at) WHERE revoked_at IS NULL;

CREATE TABLE IF NOT EXISTS public.news_collection_inventory (
 slot timestamptz PRIMARY KEY,
 captured_at timestamptz NOT NULL DEFAULT now(),
 feeds jsonb NOT NULL CHECK (jsonb_typeof(feeds)='array' AND jsonb_array_length(feeds)>0)
);
ALTER TABLE public.news_feed_admissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.news_collection_inventory ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.news_feed_admissions,public.news_collection_inventory FROM PUBLIC,anon,authenticated;
COMMENT ON TABLE public.news_feed_admissions IS
 'Human approvals for additional sources. Set effective_at to the next six-hour collector boundary; discovery alone does not admit a source.';
COMMENT ON TABLE public.news_collection_inventory IS
 'Collector-captured feed inventory for one six-hour window. Recovery reads the same snapshot; historical closures are never rewritten.';
COMMIT;
