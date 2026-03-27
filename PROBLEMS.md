# Testara Frontend & Backend Problems

Issues discovered while auditing the codebase against the stitch design reference.

---

## Supabase / Database Issues

### 1. `run_stats` view ignores `user_id` (CRITICAL)
- **File:** `supabase/migrations/001_initial_schema.sql`
- Migration 002 adds `user_id` to `test_runs`, `suites`, and `apps` with per-user RLS policies, but the `run_stats` **view** was never updated. It still aggregates ALL rows regardless of user.
- **Impact:** Every user sees global stats instead of their own. The view needs to be recreated with a `WHERE user_id = auth.uid() OR user_id IS NULL` filter, or the backend must compute stats with a manual query filtered by user.

### 2. No migration to update `run_stats` view for multi-user
- **File:** `supabase/migrations/002_add_user_id.sql`
- The second migration adds `user_id` columns and RLS policies for tables, but does not `CREATE OR REPLACE VIEW run_stats` to filter by the authenticated user.
- **Fix:** Add a `003_fix_run_stats_view.sql` migration that drops and recreates the view with user filtering, or replace the view with a Postgres function that accepts `user_id` as a parameter.

### 3. Backend `/db/run-stats` uses service-role client (bypasses RLS)
- **File:** `backend/app/api/routes/db.py`
- The `get_supabase_client()` returns a **service role** client which bypasses RLS entirely. Even if the view were fixed, the backend would ignore RLS.
- **Impact:** The stats endpoint returns data for ALL users regardless of who's asking.
- **Fix:** Either use the anon client with the user's JWT, or manually filter by `user_id` in the query.

### 4. `/db/test-runs` user filtering is fragile
- **File:** `backend/app/api/routes/db.py`
- Uses `get_current_user` (optional auth) — unauthenticated requests get **all** seed data (rows where `user_id IS NULL`). This is acceptable for development but a data leak risk in production.
- Authenticated users see their own rows + seed data, which could be confusing.

### 5. No `apps` CRUD API
- **File:** `backend/app/api/routes/db.py`
- The `apps` table exists in the schema with `user_id` support, but there are no API endpoints to list, create, or delete apps. The cloud page uploads to BrowserStack but doesn't persist app records to the database.

---

## Frontend Code Issues

### 6. Hardcoded upload URL in cloud page
- **File:** `frontend/src/app/(app)/cloud/page.tsx` (line 161)
- `fetch('http://localhost:8000/cloud/upload', ...)` — hardcoded instead of using `API_BASE` from `@/lib/api`.
- **Impact:** Will break in any non-localhost deployment.

### 7. `localStorage` accessed during SSR render
- **File:** `frontend/src/app/(app)/cloud/page.tsx` (line 339)
- `localStorage.getItem('testara_cloud_os_version')` is called directly in the Select's `value` prop, which runs during server-side rendering where `localStorage` doesn't exist.
- **Impact:** Hydration mismatch warnings or crashes in SSR mode.

### 8. Missing React `key` on Fragment in runs page
- **File:** `frontend/src/app/(app)/runs/page.tsx` (line 233)
- Uses `<>...</>` (shorthand Fragment) to wrap table row + expanded row, but shorthand Fragments can't receive a `key` prop. Should use `<React.Fragment key={run.id}>`.
- **Impact:** React key warning in console, potential rendering bugs when rows reorder.

### 9. Multiple pages use only mock data
- **Files:** `runs/page.tsx`, `suites/page.tsx`, `cloud/page.tsx`
- These pages define `mockRuns`, `mockSuites`, `mockCloudRuns` arrays and never fetch from the actual API. The dashboard page does use real hooks (`useRunStats`, `useRecentRuns`) but the other pages don't.
- **Impact:** Pages show stale placeholder data instead of real user data.

### 10. Test Generator page says "Swift / XCUITest" but code is Python
- **File:** `frontend/src/app/(app)/page.tsx` (line 380)
- The label says "Swift / XCUITest" but the syntax highlighter is set to `language="python"`, and the backend generates Python/Appium code.
- **Fix:** Change the label to "Python / Appium" or make it dynamic.

### 11. Supabase client libraries installed but unused
- **File:** `frontend/package.json`
- `@supabase/ssr` and `@supabase/supabase-js` are installed as dependencies. `frontend/src/lib/supabase.ts` is a placeholder that exports nothing useful. All Supabase access goes through the backend API.
- **Impact:** Unnecessary bundle size. Should remove unused packages or use them for direct client-side auth.

---

## Design Drift (Current vs. Stitch Reference)

### 12. Wrong color palette
- **Current:** Blue-purple Vercel/Linear inspired (`#3b82f6` primary, purple accents)
- **Stitch:** Cyan-black Kinetic Vault (`#81ecff` primary, `#00e3fd` container, pure `#000000` void)
- Every color token needs to change.

### 13. Wrong typography stack
- **Current:** Only Inter + JetBrains Mono
- **Stitch:** Inter (headlines) + JetBrains Mono (data) + **Space Grotesk** (labels/meta)
- Space Grotesk is missing from the font imports and tailwind config.

### 14. Cards use borders instead of glass-morphism
- **Current:** `rounded-xl border border-border bg-surface-1 shadow-card`
- **Stitch:** `glass-card` — `rgba(19,19,19,0.6)` + `backdrop-blur(24px)` + `1px solid rgba(255,255,255,0.1)`
- The Card component needs to use the glass-card pattern.

### 15. Sidebar doesn't match stitch layout
- **Current:** Collapsible sidebar with lucide icons, group headers, collapse toggle
- **Stitch:** Fixed 264px sidebar with Material Symbols icons, cyan active-state border-right indicator, Space Grotesk uppercase labels, V-ALPHA version badge
- Major structural difference.

### 16. Header doesn't match stitch layout
- **Current:** Minimal header with search trigger, theme toggle, notifications, avatar
- **Stitch:** Full top navigation bar with logo, Overview/Intelligence/Environments tabs, search input, notification + settings icons, user avatar
- Major structural difference — stitch has nav tabs IN the header.

### 17. No mobile bottom navigation
- **Stitch:** Has a fixed bottom nav for mobile (HOME, GEN, RUNS, ME)
- **Current:** No mobile navigation at all.

### 18. No floating action button
- **Stitch:** Has a cyan FAB (floating action button) in bottom-right corner
- **Current:** None.

### 19. Stat cards missing progress bars and background icons
- **Current:** Simple text-based stat cards
- **Stitch:** Glass cards with large background watermark icons, progress bars, percentage badges
- Dashboard needs significant visual enhancement.

### 20. Charts use blue instead of cyan
- **Current:** `#3b82f6` blue gradient fills and strokes
- **Stitch:** `#81ecff` cyan gradient fills and strokes

### 21. Table design doesn't match
- **Current:** Standard shadcn table
- **Stitch:** Glass-card table container, Space Grotesk uppercase tracking-widest headers, monospace body text, colored status pills with animated dots

---

## Auth Issues

### 22. No token refresh mechanism in frontend
- **File:** `frontend/src/lib/auth-context.tsx`
- The auth context stores `testara_refresh_token` but never uses it. When the access token expires, the user is silently logged out (token validation fails, user set to null).
- The backend has a `/auth/refresh` endpoint but the frontend never calls it.

### 23. OAuth callback doesn't handle errors
- **File:** `frontend/src/app/(auth)/auth/callback/page.tsx`
- If the OAuth flow fails (user denies permission, invalid state), the callback page may not show a useful error — depends on implementation but error handling should be explicit.

---

## Configuration Issues

### 24. CORS allows all origins
- **File:** `backend/app/main.py`
- `allow_origins=["*"]` — fine for development but a security issue in production.

### 25. API key auth excludes too many paths
- **File:** `backend/app/main.py`
- When `API_KEY` is set, many sensitive endpoints like `/run-test`, `/generate-test-with-rag`, and `/cloud/discover` are in the public paths list and bypass API key authentication.
