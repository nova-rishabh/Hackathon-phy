"""A name that is not in the roll must never be answered with someone else's record.

Regression for two live reports (28 Oct): "sonam kumar booth 23" was answered as Shanti Kumar, and
"Munna Bhaiya" as Meena Bhatia. Run: PYTHONPATH=. .venv/Scripts/python.exe tests/test_name_matching.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import citizen as c  # noqa: E402
from contracts.models import CitizenAsk  # noqa: E402


def ask(q: str):
    return c.ask(CitizenAsk(text=q, channel="web", lang="en"))


NOT_IN_ROLL = [
    "sonam kumar booth 23", "Munna Bhaiya", "Munna Bhaiya booth 1", "munna", "praveen verma",
    "priya verma booth 12", "anita sharma booth 23", "amit singh booth 63", "sonam kapoor booth 47",
    "rahul kumar booth 23", "neha kaur booth 63", "pooja kumar booth 23",
]
IN_ROLL = {  # query -> name it must return (spelling slips and other scripts included)
    "meena kumari booth 47": "Meena Kumari", "meena kumaari booth 47": "Meena Kumari",
    "mina kumari booth 47": "Meena Kumari", "मीना कुमारी बूथ 47": "Meena Kumari",
    "ravee verma booth 12": "Ravi Verma", "harprit kaur booth 63": "Harpreet Kaur",
    "ਹਰਪ੍ਰੀਤ ਕੌਰ ਬੂਥ 63": "Harpreet Kaur", "shanthi kumar booth 23": "Shanti Kumar",
}


def test_names_not_in_roll_are_not_listed():
    for q in NOT_IN_ROLL:
        a = ask(q)
        assert a.match is None and a.status == "not_found", f"{q!r} was answered as {a.match.name_lat if a.match else a.status}"
        assert a.answer_text.startswith("Not listed") or "a little more" in a.answer_text, a.answer_text


def test_first_name_alone_asks_for_more():
    a = ask("shanti booth 23")  # four voters named Shanti in this booth
    assert a.match is None and "a little more" in a.answer_text


def test_real_voters_still_found():
    for q, name in IN_ROLL.items():
        a = ask(q)
        assert a.match is not None and a.match.name_lat == name, f"{q!r} -> {a.match.name_lat if a.match else a.status}"


if __name__ == "__main__":
    test_names_not_in_roll_are_not_listed()
    test_first_name_alone_asks_for_more()
    test_real_voters_still_found()
    print(f"name matching: {len(NOT_IN_ROLL)} names not in the roll stay unlisted, {len(IN_ROLL)} real voters found")
