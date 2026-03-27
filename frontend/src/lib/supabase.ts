// Supabase is accessed through the backend API, not directly from the frontend.
// The backend .env contains SUPABASE_URL, SUPABASE_ANON_KEY, etc.
// Frontend hooks in lib/hooks.ts call /db/* endpoints on the backend.
//
// This file is kept as a placeholder — remove @supabase/ssr and @supabase/supabase-js
// from package.json if you want to clean up unused dependencies.
