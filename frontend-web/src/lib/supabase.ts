// ============================================================
// SafeSkin AI – Supabase Client
// ============================================================
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error(
    '[SafeSkin] Missing Supabase environment variables.\n' +
      'Please copy .env.example to .env.local and fill in your values.',
  );
}

/**
 * Singleton Supabase client instance.
 * Auth state is persisted in localStorage by default.
 */
export const supabase = createClient(
  supabaseUrl ?? 'https://placeholder.supabase.co',
  supabaseAnonKey ?? 'placeholder-key',
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
    global: {
      headers: {
        'x-application-name': 'SafeSkin-AI-Web',
      },
    },
  },
);

export default supabase;
