"use client";
import { useEffect, useState } from "react";
import { keyHeaders } from "./keys";
import { authHeaders } from "./auth";

export const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
/** The RollWatch WhatsApp bot (a public, demo-only number). */
export const WA_NUMBER = process.env.NEXT_PUBLIC_WA_NUMBER || "918076499841";

// Requests still waiting after SLOW_MS: the free server sleeps when idle and takes ~30 s to wake.
const SLOW_MS = 2500;
let slow = 0;
const subs = new Set<(n: number) => void>();
function watchSlow(): () => void {
  let fired = false;
  const t = setTimeout(() => { fired = true; slow++; subs.forEach((f) => f(slow)); }, SLOW_MS);
  return () => { clearTimeout(t); if (fired) { slow--; subs.forEach((f) => f(slow)); } };
}
/** True while any API request has been waiting longer than SLOW_MS. */
export function useSlowApi(): boolean {
  const [n, setN] = useState(slow);
  useEffect(() => { subs.add(setN); return () => { subs.delete(setN); }; }, []);
  return n > 0;
}

async function call<T>(path: string, init?: RequestInit, ms = 4000): Promise<T> {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), ms);
  const done = watchSlow();
  try {
    const r = await fetch(API + path, { ...init, headers: { ...keyHeaders(), ...authHeaders(), ...(init?.headers as Record<string, string> | undefined) }, signal: ctl.signal });
    if (!r.ok) throw new ApiError(r.status);
    return (await r.json()) as T;
  } finally {
    clearTimeout(t);
    done();
  }
}

export class ApiError extends Error {
  constructor(public status: number) { super(String(status)); }
}

/** POST JSON, get a binary body back (e.g. audio/mpeg from /voice/tts). Throws ApiError on non-2xx. */
export async function postBlob(path: string, body: unknown, ms = 30000): Promise<Blob> {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), ms);
  const done = watchSlow();
  try {
    const r = await fetch(API + path, {
      method: "POST", headers: { ...keyHeaders(), ...authHeaders(), "Content-Type": "application/json" }, body: JSON.stringify(body), signal: ctl.signal,
    });
    if (!r.ok) throw new ApiError(r.status);
    return await r.blob();
  } finally {
    clearTimeout(t);
    done();
  }
}

/** GET with an optional mock fallback. mock === undefined means "no fallback": data stays null. */
export async function getJson<T>(path: string, mock?: T): Promise<{ data: T | null; mocked: boolean }> {
  try {
    return { data: await call<T>(path), mocked: false };
  } catch {
    return { data: mock ?? null, mocked: mock !== undefined };
  }
}

export async function postJson<T>(path: string, body: unknown, ms = 20000): Promise<T> {
  return call<T>(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }, ms);
}

export function useApi<T>(path: string, mock?: T) {
  const [state, set] = useState<{ data: T | null; mocked: boolean; done: boolean }>({ data: null, mocked: false, done: false });
  useEffect(() => {
    let live = true;
    getJson<T>(path, mock).then((r) => live && set({ ...r, done: true }));
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path]);
  return state;
}

export const fmt = (n: number) => Math.round(n).toLocaleString("en-IN");
export const pct = (x: number, d = 0) => (x * 100).toFixed(d) + "%";
export const boothNo = (id: string) => Number(id.replace(/\D/g, ""));
