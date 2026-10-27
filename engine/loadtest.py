"""python -m engine.loadtest [--base http://localhost:8020] [--n 600] [--c 50]

Measured throughput of the API on one process (one uvicorn worker), offline (DEMO_MODE=1, no model calls):
requests per second and p50/p95 latency for the citizen and claim paths. Writes cache/loadtest.json.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import platform
import time
from pathlib import Path

import httpx

ROUTES = {
    "overview (cached aggregates)": ("GET", "/overview", None),
    "name search": ("GET", "/search?q=meena%20kumari&booth_id=B047", None),
    "citizen answer": ("POST", "/citizen/ask", {"text": "Meena Kumari booth 47", "channel": "web"}),
    "claim check (cached split)": ("POST", "/claims/check",
                                   {"text": "Booth 47 mein 600 naam kaat diye, sabse zyada, aur sab ek community ke!", "mirror": True}),
}


async def hammer(base: str, method: str, path: str, body, n: int, c: int) -> dict:
    lat: list[float] = []
    sem = asyncio.Semaphore(c)
    async with httpx.AsyncClient(base_url=base, timeout=60) as cl:
        async def one():
            async with sem:
                t = time.perf_counter()
                r = await (cl.get(path) if method == "GET" else cl.post(path, json=body))
                r.raise_for_status()
                lat.append(time.perf_counter() - t)
        await one()  # warm
        lat.clear()
        t0 = time.perf_counter()
        await asyncio.gather(*(one() for _ in range(n)))
        wall = time.perf_counter() - t0
    lat.sort()
    return {"n": n, "concurrency": c, "rps": round(n / wall, 1), "p50_ms": round(lat[len(lat) // 2] * 1000, 1),
            "p95_ms": round(lat[int(len(lat) * 0.95)] * 1000, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8020")
    ap.add_argument("--n", type=int, default=600)
    ap.add_argument("--c", type=int, default=50)
    a = ap.parse_args()
    out = {"measured": True, "machine": {"cpus": os.cpu_count(), "platform": platform.platform()},
           "setup": "one uvicorn worker (one process), DEMO_MODE=1 (no model calls), localhost", "routes": {}}
    for name, (m, p, b) in ROUTES.items():
        out["routes"][name] = r = asyncio.run(hammer(a.base, m, p, b, a.n, a.c))
        print(f"{name:32s} {r['rps']:>8} req/s   p50 {r['p50_ms']} ms   p95 {r['p95_ms']} ms")
    Path("cache").mkdir(exist_ok=True)
    Path("cache/loadtest.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
