"use client";
import { useEffect, useState } from "react";

const KEY = "rw_token";
const EVT = "rw-auth";

export type User = { mobile_masked: string };
export type SavedCheck = { claim_id: string; claim_text: string; overall: string; created_at: string };
export type WatchedBooth = { booth_id: string; created_at: string };

export function getToken(): string | null {
  try { return localStorage.getItem(KEY); } catch { return null; }
}

export function setToken(t: string | null) {
  try { if (t) localStorage.setItem(KEY, t); else localStorage.removeItem(KEY); } catch { /* storage blocked */ }
  try { window.dispatchEvent(new Event(EVT)); } catch { /* no window */ }
}

export function authHeaders(): Record<string, string> {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

/** Raw auth fetch: returns status + parsed body (never throws on HTTP errors). */
export async function authFetch<T = unknown>(path: string, init?: RequestInit, ms = 15000): Promise<{ status: number; body: T | null }> {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), ms);
  try {
    const r = await fetch(API + path, {
      ...init,
      headers: { ...authHeaders(), ...(init?.body ? { "Content-Type": "application/json" } : {}), ...(init?.headers as Record<string, string> | undefined) },
      signal: ctl.signal,
    });
    let body: T | null = null;
    try { body = (await r.json()) as T; } catch { body = null; }
    if (r.status === 401 && path.startsWith("/me")) setToken(null);
    return { status: r.status, body };
  } catch {
    return { status: 0, body: null };
  } finally {
    clearTimeout(t);
  }
}

let cache: { token: string; user: User } | null = null;

export function useSession() {
  const [state, set] = useState<{ user: User | null; loading: boolean }>({ user: null, loading: true });
  useEffect(() => {
    let live = true;
    const load = async () => {
      const token = getToken();
      if (!token) { cache = null; if (live) set({ user: null, loading: false }); return; }
      if (cache?.token === token) { if (live) set({ user: cache.user, loading: false }); return; }
      const r = await authFetch<User>("/auth/me");
      if (r.status === 200 && r.body) { cache = { token, user: r.body }; if (live) set({ user: r.body, loading: false }); }
      else {
        if (r.status === 401) setToken(null);
        if (live) set({ user: null, loading: false });
      }
    };
    load();
    const on = () => { set((s) => ({ ...s, loading: true })); load(); };
    window.addEventListener(EVT, on);
    window.addEventListener("storage", on);
    return () => { live = false; window.removeEventListener(EVT, on); window.removeEventListener("storage", on); };
  }, []);
  return { ...state, signOut: () => { cache = null; setToken(null); } };
}
