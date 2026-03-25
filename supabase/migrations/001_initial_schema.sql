-- Testara initial schema
-- Run this in Supabase SQL Editor: https://supabase.com/dashboard/project/xgehtlrfafsvdmumjowq/sql

-- ── Suites ────────────────────────────────────────────────────────────────────
create table if not exists public.suites (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  description text,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- ── Test Runs ─────────────────────────────────────────────────────────────────
create table if not exists public.test_runs (
  id             uuid primary key default gen_random_uuid(),
  test_name      text not null,
  suite_id       uuid references public.suites(id) on delete set null,
  suite_name     text,
  status         text not null check (status in ('passed', 'failed', 'running', 'queued')),
  device         text,
  os_version     text,
  duration       numeric(8,2),       -- seconds
  logs           text,
  error_message  text,
  screenshot_url text,
  execution_mode text not null default 'cloud' check (execution_mode in ('local', 'cloud')),
  created_at     timestamptz not null default now()
);

-- ── Apps ──────────────────────────────────────────────────────────────────────
create table if not exists public.apps (
  id         uuid primary key default gen_random_uuid(),
  name       text not null,
  bundle_id  text,
  ipa_url    text,
  created_at timestamptz not null default now()
);

-- ── Indexes ───────────────────────────────────────────────────────────────────
create index if not exists idx_test_runs_status     on public.test_runs(status);
create index if not exists idx_test_runs_created_at on public.test_runs(created_at desc);
create index if not exists idx_test_runs_suite_id   on public.test_runs(suite_id);

-- ── Stats view ────────────────────────────────────────────────────────────────
create or replace view public.run_stats as
select
  count(*)                                          as total,
  count(*) filter (where status = 'passed')         as passed,
  count(*) filter (where status = 'failed')         as failed,
  count(*) filter (where status = 'running')        as running,
  max(created_at)                                   as last_run_at
from public.test_runs;

-- ── RLS (Row Level Security) ──────────────────────────────────────────────────
-- For now, allow all access (no auth yet). Tighten when auth is added.
alter table public.suites    enable row level security;
alter table public.test_runs enable row level security;
alter table public.apps      enable row level security;

create policy "allow_all_suites"    on public.suites    for all using (true) with check (true);
create policy "allow_all_test_runs" on public.test_runs for all using (true) with check (true);
create policy "allow_all_apps"      on public.apps      for all using (true) with check (true);

-- ── Seed data (optional) ─────────────────────────────────────────────────────
insert into public.suites (name, description) values
  ('Smoke Tests',      'Quick sanity checks for critical flows'),
  ('Regression Suite', 'Full regression coverage'),
  ('Checkout Flow',    'End-to-end purchase journey'),
  ('Auth & Login',     'Authentication and session management')
on conflict do nothing;
