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
