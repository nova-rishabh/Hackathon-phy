"use client";
import { createClient, type SupabaseClient, type Session } from "@supabase/supabase-js";
import { useEffect, useState } from "react";

const SB_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const ANON = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

/** null when accounts are not configured: every caller must handle that and keep working. */
export const supabase: SupabaseClient | null = SB_URL && ANON ? createClient(SB_URL, ANON) : null;

export type SavedCheck = { id: string; claim_id: string; claim_text: string; overall: string; created_at: string };
export type WatchedBooth = { booth_id: string; created_at: string };

export function useSession() {
  const [state, set] = useState<{ session: Session | null; ready: boolean }>({ session: null, ready: !supabase });
  useEffect(() => {
    if (!supabase) return;
    supabase.auth.getSession().then(({ data }) => set({ session: data.session, ready: true }));
    const { data } = supabase.auth.onAuthStateChange((_e, s) => set({ session: s, ready: true }));
    return () => data.subscription.unsubscribe();
  }, []);
  return state;
}

export async function signOut() {
  if (supabase) await supabase.auth.signOut();
}
