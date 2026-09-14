-- Execute uma vez no SQL Editor do Supabase. Não apaga tabelas existentes.
BEGIN;
CREATE TABLE IF NOT EXISTS public.news_feeds (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 rss_url text NOT NULL UNIQUE, name text NOT NULL, region text NOT NULL,
 country text NOT NULL, site_url text NOT NULL, justification text NOT NULL,
 etag text, last_modified text, last_success_at timestamptz
);
CREATE TABLE IF NOT EXISTS public.news_runs (
 slot timestamptz PRIMARY KEY, started_at timestamptz NOT NULL DEFAULT now(),
 finished_at timestamptz, status text NOT NULL DEFAULT 'running', report jsonb
);
CREATE TABLE IF NOT EXISTS public.news_feed_runs (
 slot timestamptz NOT NULL REFERENCES public.news_runs(slot),
 feed_id bigint NOT NULL REFERENCES public.news_feeds(id),
 status text NOT NULL, items integer NOT NULL DEFAULT 0, error text,
 checked_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(slot,feed_id)
);
CREATE TABLE IF NOT EXISTS public.news_articles (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, url text NOT NULL UNIQUE,
 title text NOT NULL, summary text NOT NULL DEFAULT '', published_at timestamptz,
 source_updated_at timestamptz, first_seen_at timestamptz NOT NULL DEFAULT now(),
 last_seen_at timestamptz NOT NULL DEFAULT now(), metadata_hash text NOT NULL,
 content_key text, content_hash text, rss_content_key text, content_status text NOT NULL DEFAULT 'pending',
 content_chars integer, extracted_at timestamptz, final_url text,
 page_etag text, page_last_modified text, page_checked_at timestamptz,
 next_attempt_at timestamptz NOT NULL DEFAULT now(), attempts integer NOT NULL DEFAULT 0,
 last_error text
);
CREATE TABLE IF NOT EXISTS public.news_article_feeds (
 article_id bigint NOT NULL REFERENCES public.news_articles(id),
 feed_id bigint NOT NULL REFERENCES public.news_feeds(id),
 in_latest boolean NOT NULL DEFAULT true,
 PRIMARY KEY(article_id,feed_id)
);
CREATE TABLE IF NOT EXISTS public.news_article_versions (
 article_id bigint NOT NULL REFERENCES public.news_articles(id),
 content_hash text NOT NULL, content_key text NOT NULL, captured_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(article_id,content_hash)
);
CREATE INDEX IF NOT EXISTS news_articles_due ON public.news_articles(next_attempt_at);
CREATE INDEX IF NOT EXISTS news_articles_date ON public.news_articles(published_at DESC,id DESC);
CREATE INDEX IF NOT EXISTS news_article_feeds_source ON public.news_article_feeds(feed_id,article_id);
-- O coletor usa conexão PostgreSQL privada. Nenhuma credencial fica no front.
ALTER TABLE public.news_feeds ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.news_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.news_feed_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.news_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.news_article_feeds ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.news_article_versions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.news_feeds, public.news_runs, public.news_feed_runs,
 public.news_articles, public.news_article_feeds, public.news_article_versions FROM anon,authenticated;
COMMIT;

-- Additive analysis schema, also applied through Supabase migration history.
CREATE TABLE IF NOT EXISTS public.news_analysis_runs (
 id text PRIMARY KEY, collection_slot timestamptz NOT NULL,
 collection_finished_at timestamptz NOT NULL, started_at timestamptz NOT NULL DEFAULT now(),
 finished_at timestamptz, status text NOT NULL CHECK(status IN ('building','ready','failed')),
 model_version text NOT NULL, model_revision text, snapshot_key text,
 coverage jsonb NOT NULL DEFAULT '{}'::jsonb, error text
);
CREATE TABLE IF NOT EXISTS public.news_topic_snapshots (
 run_id text NOT NULL REFERENCES public.news_analysis_runs(id), scope text NOT NULL CHECK(scope IN ('country','continent','globe')),
 place text NOT NULL, scheduled_at timestamptz NOT NULL, started_at timestamptz NOT NULL,
 report_key text NOT NULL, payload jsonb NOT NULL, PRIMARY KEY(run_id,scope,place)
);
ALTER TABLE public.news_analysis_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.news_topic_snapshots ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.news_analysis_runs, public.news_topic_snapshots FROM anon,authenticated;
CREATE INDEX IF NOT EXISTS news_analysis_runs_finished ON public.news_analysis_runs(finished_at DESC);
CREATE TABLE IF NOT EXISTS public.news_collection_attempts (id text PRIMARY KEY,slot timestamptz NOT NULL,finished_at timestamptz NOT NULL,report jsonb NOT NULL,feeds jsonb NOT NULL);
ALTER TABLE public.news_collection_attempts ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.news_collection_attempts FROM anon,authenticated;

-- Daily accounting. Historical observations are deliberately not fabricated.
CREATE TABLE IF NOT EXISTS public.news_article_observations (
 slot timestamptz NOT NULL, feed_id bigint NOT NULL REFERENCES public.news_feeds(id),
 article_id bigint NOT NULL REFERENCES public.news_articles(id),
 observed_at timestamptz NOT NULL DEFAULT now(), source jsonb NOT NULL,
 title text NOT NULL, summary text NOT NULL DEFAULT '',
 PRIMARY KEY(slot,feed_id,article_id)
);
CREATE INDEX IF NOT EXISTS news_article_observations_article ON public.news_article_observations(article_id);
CREATE TABLE IF NOT EXISTS public.news_observation_batches (
 slot timestamptz NOT NULL, feed_id bigint NOT NULL REFERENCES public.news_feeds(id),
 recorded_at timestamptz NOT NULL DEFAULT now(), articles integer NOT NULL,
 PRIMARY KEY(slot,feed_id)
);
CREATE TABLE IF NOT EXISTS public.news_daily_closures (
 id text PRIMARY KEY, day date NOT NULL, mode text NOT NULL CHECK(mode IN ('preview','closed')),
 source_attempt text, version text NOT NULL, cutoff timestamptz NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(), report_key text NOT NULL,
 summary jsonb NOT NULL, coverage jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS news_daily_closures_day ON public.news_daily_closures(day,created_at DESC);
ALTER TABLE public.news_article_observations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.news_observation_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.news_daily_closures ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.news_article_observations,public.news_observation_batches,public.news_daily_closures FROM anon,authenticated;
