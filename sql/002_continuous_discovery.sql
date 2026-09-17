-- Additive Bóris schema. Apply explicitly before enabling discovery; no cron.
BEGIN;
CREATE TABLE IF NOT EXISTS public.news_discovery_tasks (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 kind text NOT NULL CHECK(kind IN ('site','feed')),
 url text NOT NULL, parent_url text, depth integer NOT NULL DEFAULT 0 CHECK(depth BETWEEN 0 AND 4),
 status text NOT NULL DEFAULT 'queued' CHECK(status IN ('queued','leased','complete')),
 next_attempt_at timestamptz NOT NULL DEFAULT now(), attempts integer NOT NULL DEFAULT 0,
 lease_token uuid, lease_until timestamptz, last_error text, last_success_at timestamptz,
 link_cursor integer NOT NULL DEFAULT 0 CHECK(link_cursor>=0),
 sample_cursor integer NOT NULL DEFAULT 0 CHECK(sample_cursor>=0),
 created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(kind,url),
 CHECK((status='leased')=(lease_token IS NOT NULL AND lease_until IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS news_discovery_tasks_due ON public.news_discovery_tasks(next_attempt_at,id) WHERE status<>'complete';
CREATE TABLE IF NOT EXISTS public.news_discovery_candidates (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 rss_url text NOT NULL UNIQUE, site_url text NOT NULL,
 status text NOT NULL DEFAULT 'observing' CHECK(status IN ('observing','awaiting_editorial_review','admitted','rejected')),
 first_seen_at timestamptz NOT NULL DEFAULT now(), last_checked_at timestamptz,
 last_error text, technical_evaluation jsonb NOT NULL DEFAULT '{}'::jsonb,
 feed_id bigint REFERENCES public.news_feeds(id), reviewed_at timestamptz,
 reviewer text, review_reason text, review_evidence jsonb,
 CHECK(status NOT IN ('admitted','rejected') OR (reviewed_at IS NOT NULL AND reviewer IS NOT NULL AND review_reason IS NOT NULL))
);
CREATE TABLE IF NOT EXISTS public.news_discovery_observations (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 candidate_id bigint NOT NULL REFERENCES public.news_discovery_candidates(id),
 observed_at timestamptz NOT NULL DEFAULT now(), payload jsonb NOT NULL,
 task_id bigint NOT NULL REFERENCES public.news_discovery_tasks(id), lease_token uuid NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS news_discovery_observations_candidate ON public.news_discovery_observations(candidate_id,observed_at DESC);
CREATE TABLE IF NOT EXISTS public.news_discovery_budget (
 day date PRIMARY KEY, requests_reserved integer NOT NULL DEFAULT 0 CHECK(requests_reserved BETWEEN 0 AND 120),
 bytes_reserved bigint NOT NULL DEFAULT 0 CHECK(bytes_reserved BETWEEN 0 AND 134217728),
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS public.news_discovery_audit (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, occurred_at timestamptz NOT NULL DEFAULT now(),
 actor text NOT NULL, action text NOT NULL, candidate_id bigint REFERENCES public.news_discovery_candidates(id),
 details jsonb NOT NULL
);
CREATE TABLE IF NOT EXISTS public.news_discovery_dispatch (
 id boolean PRIMARY KEY DEFAULT true CHECK(id), claims bigint NOT NULL DEFAULT 0 CHECK(claims>=0)
);
INSERT INTO public.news_discovery_dispatch(id) VALUES(true) ON CONFLICT DO NOTHING;
ALTER TABLE public.news_discovery_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.news_discovery_candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.news_discovery_observations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.news_discovery_budget ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.news_discovery_audit ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.news_discovery_dispatch ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.news_discovery_tasks,public.news_discovery_candidates,public.news_discovery_observations,
 public.news_discovery_budget,public.news_discovery_audit,public.news_discovery_dispatch FROM PUBLIC,anon,authenticated;
COMMIT;
