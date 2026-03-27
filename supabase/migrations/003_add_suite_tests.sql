-- 003: Add suite_tests table for persistent test definitions within suites
-- Run in Supabase SQL Editor after 002_add_user_id.sql

-- ── New table: suite_tests ──────────────────────────────────────────────────
create table if not exists public.suite_tests (
  id              uuid primary key default gen_random_uuid(),
  suite_id        uuid not null references public.suites(id) on delete cascade,
  name            text not null,
  description     text,
  test_code       text not null,
  class_name      text,
  quality_score   integer,
  quality_grade   text,
  last_status     text default 'not_run' check (last_status in ('passed', 'failed', 'running', 'not_run')),
  last_run_at     timestamptz,
  last_run_id     uuid,
  position        integer not null default 0,
  user_id         uuid references auth.users(id) on delete cascade,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

-- ── Add suite_test_id to test_runs ──────────────────────────────────────────
alter table public.test_runs add column if not exists suite_test_id uuid references public.suite_tests(id) on delete set null;

-- ── Add last_run_id FK (deferred because test_runs must exist first) ────────
alter table public.suite_tests
  add constraint fk_suite_tests_last_run
  foreign key (last_run_id) references public.test_runs(id) on delete set null;

-- ── Indexes ─────────────────────────────────────────────────────────────────
create index if not exists idx_suite_tests_suite_id on public.suite_tests(suite_id);
create index if not exists idx_suite_tests_user_id  on public.suite_tests(user_id);
create index if not exists idx_test_runs_suite_test_id on public.test_runs(suite_test_id);

-- ── RLS ─────────────────────────────────────────────────────────────────────
alter table public.suite_tests enable row level security;

create policy "user_read_suite_tests"   on public.suite_tests for select using (auth.uid() = user_id or user_id is null);
create policy "user_write_suite_tests"  on public.suite_tests for insert with check (auth.uid() = user_id);
create policy "user_update_suite_tests" on public.suite_tests for update using (auth.uid() = user_id);
create policy "user_delete_suite_tests" on public.suite_tests for delete using (auth.uid() = user_id);
