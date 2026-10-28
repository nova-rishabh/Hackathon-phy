"""Wake the live demo before going on stage: one pass over every page and route the demo touches.

Run 5 minutes before presenting:  python scripts/warmup.py
Local fallback instead:            python scripts/warmup.py --local   (API :8000, web :3000)

One request per target, in order, with a long timeout (a sleeping Render service takes ~40 s to wake).
No retry loop: if a line says FAIL, open that URL by hand or switch to the local fallback (scripts/demo_local.ps1).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request

LIVE = ("https://rollwatch-api.onrender.com", "https://rollwatch-web.onrender.com")
LOCAL = ("http://127.0.0.1:8000", "http://127.0.0.1:3000")  # not localhost: Windows tries IPv6 first (+2 s a call)
DEMO_CLAIM = "Booth 47 mein 600 naam kaat diye, sabse zyada, aur sab ek community ke!"
DEMO_NAME = "मीना कुमारी बूथ 47"


def hit(method: str, url: str, body: dict | None = None, timeout: float = 90) -> tuple[bool, str]:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    t = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            r.read()
            return r.status < 400, f"{r.status} in {time.perf_counter() - t:.1f}s"
    except Exception as e:  # noqa: BLE001 - report and move on, never retry
        return False, f"{type(e).__name__}: {e}"[:120]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", action="store_true", help="warm the local DEMO_MODE fallback instead of Render")
    ap.add_argument("--api", help="override the API base URL")
    ap.add_argument("--web", help="override the web base URL")
    args = ap.parse_args()
    api, web = LOCAL if args.local else LIVE
    api, web = args.api or api, args.web or web
    targets = [
        ("GET", f"{api}/health", None),
        ("GET", f"{api}/overview", None),
        ("GET", f"{api}/flags", None),
        ("GET", f"{api}/eval/blind", None),
        ("GET", f"{api}/rules", None),
        ("POST", f"{api}/stories/B047", {"context_on": ["death_register", "hostel_list", "boundary_changes", "duplicates"]}),
        ("POST", f"{api}/claims/check", {"text": DEMO_CLAIM, "mirror": True}),
        ("POST", f"{api}/citizen/ask", {"text": DEMO_NAME, "channel": "web"}),
        ("GET", f"{web}/", None),
        ("GET", f"{web}/check", None),
        ("GET", f"{web}/ask", None),
        ("GET", f"{web}/trust", None),
        ("GET", f"{web}/run", None),
        ("GET", f"{web}/pricing", None),
    ]
    bad = 0
    for method, url, body in targets:
        ok, note = hit(method, url, body)
        bad += not ok
        print(f"  [{'OK  ' if ok else 'FAIL'}] {method:4} {url}  {note}")
    print("All warm. Render sleeps after 15 idle minutes: re-run if the pitch is later than that." if not bad else
          f"{bad} failed. Open those by hand, or run scripts/demo_local.ps1 and present from localhost.")
    return 1 if bad else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
