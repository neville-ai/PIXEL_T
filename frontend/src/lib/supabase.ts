import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://placeholder.supabase.co';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'placeholder-anon-key';

/**
 * Indicates whether the Supabase frontend environment variables
 * (VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY) are configured.
 */
export const isSupabaseConfigured = Boolean(
  import.meta.env.VITE_SUPABASE_URL && import.meta.env.VITE_SUPABASE_ANON_KEY
);

/**
 * Shared singleton Supabase client for client-side operations.
 * Uses anon key only. NEVER use or expose service role key on the frontend.
 *
 * Auto-refresh token is enabled to handle token expiration during long-running
 * analysis operations. The client will automatically refresh the access token
 * using the refresh token stored in localStorage.
 */
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
  },
});
