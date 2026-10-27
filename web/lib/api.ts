"use client";
import { useEffect, useState } from "react";

export const API = process.env.NEXT_PUBLIC_API || "http://localhost:8000";

export async function getJson<T>(path: string, mock: T): Promise<{ data: T; mocked: boolean }> {
  try {
    const ctl = new AbortController();
    const t = setTimeout(() => ctl.abort(), 2500);
    const r = await fetch(API + path, { signal: ctl.signal });
    clearTimeout(t);
    if (!r.ok) throw new Error(String(r.status));
    return { data: (await r.json()) as T, mocked: false };
  } catch {
    return { data: mock, mocked: true };
  }
}

export function useApi<T>(path: string, mock: T) {
  const [state, set] = useState<{ data: T | null; mocked: boolean }>({ data: null, mocked: false });
  useEffect(() => {
    let live = true;
    getJson<T>(path, mock).then((r) => live && set(r));
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path]);
  return state;
}

export const fmt = (n: number) => n.toLocaleString("en-IN");
export const pct = (x: number, d = 0) => (x * 100).toFixed(d) + "%";
