-- 002: Add user_id for multi-user data isolation
-- Run in Supabase SQL Editor after 001_initial_schema.sql

-- ── Add user_id columns ───────────────────────────────────────────────────────
ALTER TABLE public.suites    ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE public.test_runs ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE public.apps      ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE;

-- ── Indexes ───────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_suites_user_id    ON public.suites(user_id);
CREATE INDEX IF NOT EXISTS idx_test_runs_user_id ON public.test_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_apps_user_id      ON public.apps(user_id);

-- ── Replace allow-all RLS policies with user-scoped ones ──────────────────────
DROP POLICY IF EXISTS "allow_all_suites"    ON public.suites;
DROP POLICY IF EXISTS "allow_all_test_runs" ON public.test_runs;
DROP POLICY IF EXISTS "allow_all_apps"      ON public.apps;

-- Users can read their own rows + shared rows (user_id IS NULL = seed/template data)
CREATE POLICY "user_read_suites"    ON public.suites    FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);
CREATE POLICY "user_write_suites"   ON public.suites    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "user_update_suites"  ON public.suites    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "user_delete_suites"  ON public.suites    FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "user_read_test_runs"   ON public.test_runs FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);
CREATE POLICY "user_write_test_runs"  ON public.test_runs FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "user_update_test_runs" ON public.test_runs FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "user_delete_test_runs" ON public.test_runs FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "user_read_apps"   ON public.apps FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);
CREATE POLICY "user_write_apps"  ON public.apps FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "user_update_apps" ON public.apps FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "user_delete_apps" ON public.apps FOR DELETE USING (auth.uid() = user_id);

-- Note: Service role key bypasses RLS, so backend admin operations still work.
