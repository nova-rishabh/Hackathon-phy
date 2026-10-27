"""B2 smoke checks (TRD 9). smoke_test.py can call `check_citizen_fixture()`; run all: python -m bot.smoke_checks

No network, no keys: the bot logic is driven against the in-process FastAPI citizen router plus a stub
/claims/check, through httpx's ASGI transport.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FIX = ROOT / "contracts" / "fixtures"


def check_citizen_fixture() -> None:
    """Citizen search finds the fixture query (expected.json citizen_search) with the right status."""
    exp = json.loads((FIX / "expected.json").read_text(encoding="utf-8"))["citizen_search"]
    old = os.environ.get("ROLLWATCH_DATA")
    os.environ["ROLLWATCH_DATA"] = str(FIX)
    try:
        from api import citizen
        from contracts.models import CitizenAsk
        res = citizen.search(exp["query"])
        assert res.matches and res.matches[0].voter_id == exp["expect_voter_id"], res
        assert res.matches[0].status_v2 == exp["expect_status"], res.matches[0]
        a = citizen.ask(CitizenAsk(text=exp["query"], channel="telegram"))
        assert a.match and a.match.voter_id == exp["expect_voter_id"] and a.status == exp["expect_status"]
        assert "1950" in a.answer_text and "OTP" in a.answer_text
    finally:
        if old is None:
            os.environ.pop("ROLLWATCH_DATA", None)
        else:
            os.environ["ROLLWATCH_DATA"] = old


_PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 16


def _stub_app():
    from fastapi import FastAPI, Response
    from api.citizen import router
    app = FastAPI()
    app.include_router(router)
    seen = {}

    @app.post("/claims/check")
    def claims(body: dict):
        seen["body"] = body
        return {"claim_id": "c1", "input": {"text": body.get("text") or "from image", "lang": "hi",
                                            "source": "image" if body.get("image_b64") else "text"},
                "normalized_claim": "Booth 47 mein 600 naam kaat diye", "sub_claims": [
                    {"id": "s1", "text": "600 names removed in Booth 47", "tool": "deletion_count",
                     "query_shown": "q", "verdict": "disputed", "reason": "The count is 412.",
                     "confidence": 0.8}],
                "overall": "mixed", "confidence": 0.76, "card_png": "/cards/c1.png",
                "mirror": {"claim_text": "x", "sub_claim_verdicts": ["disputed"], "identical_treatment": True},
                "guard": {"passed": True}}

    @app.get("/cards/c1.png")
    def card():
        return Response(_PNG, media_type="image/png")
    return app, seen


def check_bot_offline() -> None:
    """Bot: name lookup, claim text, screenshot (image_b64), every answer ends with the footer."""
    import base64
    import httpx
    from api import constants as C
    from bot import core
    os.environ["ROLLWATCH_DATA"] = str(FIX)
    app, seen = _stub_app()

    async def run():
        api = core.Api(client=httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t"))
        r = await core.handle_text(api, "meena kumaari booth 1")
        assert r[0].text.rstrip().endswith(C.SCAM_LINE["en"]) and "Meena Kumari" in r[0].text, r[0].text
        r = await core.handle_text(api, "मीना कुमारी बूथ 1")
        assert r[0].text.rstrip().endswith(C.SCAM_LINE["hi"]), r[0].text
        r = await core.handle_text(api, "claim: Booth 47 mein 600 naam kaat diye, sabse zyada")
        assert seen["body"]["text"].startswith("Booth 47") and [x.kind for x in r] == ["text", "photo"], r
        assert r[0].text.rstrip().endswith(C.SCAM_LINE["en"])
        r = await core.handle_claim(api, image=b"fakejpeg")
        assert base64.b64decode(seen["body"]["image_b64"]) == b"fakejpeg"
        assert r[0].text.rstrip().endswith(C.SCAM_LINE["hi"]) and r[1].data == _PNG
        r = await core.handle_voice(api, b"OggS")  # no SARVAM_API_KEY -> graceful text
        assert r[0].kind == "text" and C.SCAM_LINE["hi"] in r[0].text
    if not os.environ.get("SARVAM_API_KEY"):
        asyncio.run(run())
    os.environ.pop("ROLLWATCH_DATA", None)


if __name__ == "__main__":
    for fn in (check_citizen_fixture, check_bot_offline):
        fn()
        print("ok", fn.__name__)
