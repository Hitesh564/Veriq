import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://svxbeirlashsvlmkwdxr.supabase.co";
// Fallback placeholder is used to prevent Next.js build compilation failures when keys aren't set
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "placeholder_anon_key";

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
