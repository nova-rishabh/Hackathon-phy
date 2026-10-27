"use client";
/** Bring-your-own keys. Stored only in this browser's localStorage; sent only as request headers to our API. */
export type KeyName = "gemini" | "elevenlabs";
const STORE: Record<KeyName, string> = { gemini: "rw:key:gemini", elevenlabs: "rw:key:elevenlabs" };
export const HEADER: Record<KeyName, string> = { gemini: "X-Gemini-Key", elevenlabs: "X-ElevenLabs-Key" };

export function getKey(k: KeyName): string {
  try { return localStorage.getItem(STORE[k]) ?? ""; } catch { return ""; }
}
export function setKey(k: KeyName, v: string) {
  try { if (v.trim()) localStorage.setItem(STORE[k], v.trim()); else localStorage.removeItem(STORE[k]); } catch {}
}
export function keyHeaders(): Record<string, string> {
  const h: Record<string, string> = {};
  (Object.keys(STORE) as KeyName[]).forEach((k) => { const v = getKey(k); if (v) h[HEADER[k]] = v; });
  return h;
}
