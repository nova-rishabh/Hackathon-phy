"""Bot-only UI strings (hi / en / pa). Procedural and neutral; facts come from api/constants.py."""
from api import constants as C

VERDICT = {
    "verified": {"en": "Verified", "hi": "सही पाया गया", "pa": "ਸਹੀ ਪਾਇਆ ਗਿਆ"},
    "disputed": {"en": "Disputed", "hi": "आँकड़ों से मेल नहीं खाता", "pa": "ਅੰਕੜਿਆਂ ਨਾਲ ਮੇਲ ਨਹੀਂ ਖਾਂਦਾ"},
    "unprovable": {"en": "Cannot be proven", "hi": "साबित नहीं किया जा सकता", "pa": "ਸਾਬਤ ਨਹੀਂ ਕੀਤਾ ਜਾ ਸਕਦਾ"},
    "mixed": {"en": "Partly true, partly not", "hi": "कुछ हिस्सा सही, कुछ नहीं", "pa": "ਕੁਝ ਹਿੱਸਾ ਸਹੀ, ਕੁਝ ਨਹੀਂ"},
}

L = {
    "claim_head": {"en": "Claim check (synthetic demo district Sampleabad)",
                   "hi": "दावे की जाँच (काल्पनिक डेमो ज़िला सैम्पलाबाद)",
                   "pa": "ਦਾਅਵੇ ਦੀ ਜਾਂਚ (ਕਾਲਪਨਿਕ ਡੈਮੋ ਜ਼ਿਲ੍ਹਾ ਸੈਂਪਲਾਬਾਦ)"},
    "overall": {"en": "Overall: {v} · confidence {pct}%", "hi": "कुल नतीजा: {v} · भरोसा {pct}%",
                "pa": "ਕੁੱਲ ਨਤੀਜਾ: {v} · ਭਰੋਸਾ {pct}%"},
    "mirror": {"en": "Mirror check: the opposite claim got the same treatment.",
               "hi": "मिरर जाँच: उल्टे दावे की भी बिल्कुल इसी तरह जाँच हुई।",
               "pa": "ਮਿਰਰ ਜਾਂਚ: ਉਲਟੇ ਦਾਅਵੇ ਦੀ ਵੀ ਬਿਲਕੁਲ ਇਸੇ ਤਰ੍ਹਾਂ ਜਾਂਚ ਹੋਈ।"},
    "review": {"en": "Needs human review. Numbers are computed from the roll, not by AI.",
               "hi": "इंसानी समीक्षा ज़रूरी है। सभी आँकड़े सूची से गिने गए हैं, AI से नहीं।",
               "pa": "ਇਨਸਾਨੀ ਸਮੀਖਿਆ ਜ਼ਰੂਰੀ ਹੈ। ਸਾਰੇ ਅੰਕੜੇ ਸੂਚੀ ਤੋਂ ਗਿਣੇ ਗਏ ਹਨ, AI ਤੋਂ ਨਹੀਂ।"},
    "busy": {"en": "Checking…", "hi": "जाँच हो रही है…", "pa": "ਜਾਂਚ ਹੋ ਰਹੀ ਹੈ…"},
    "api_down": {"en": "The checking service is not reachable right now. Please try again in a minute.",
                 "hi": "जाँच सेवा अभी उपलब्ध नहीं है। कृपया एक मिनट बाद फिर कोशिश करें।",
                 "pa": "ਜਾਂਚ ਸੇਵਾ ਹੁਣ ਉਪਲਬਧ ਨਹੀਂ ਹੈ। ਕਿਰਪਾ ਕਰਕੇ ਇੱਕ ਮਿੰਟ ਬਾਅਦ ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।"},
    "unsupported": {"en": "I can read text, screenshots and voice notes. Send your name and booth, e.g. \"meena kumari booth 47\", or forward a message to check it.",
                    "hi": "मैं टेक्स्ट, स्क्रीनशॉट और वॉइस नोट पढ़ सकता हूँ। अपना नाम और बूथ भेजें, जैसे \"मीना कुमारी बूथ 47\", या कोई मैसेज फ़ॉरवर्ड करें।",
                    "pa": "ਮੈਂ ਟੈਕਸਟ, ਸਕ੍ਰੀਨਸ਼ਾਟ ਅਤੇ ਵੌਇਸ ਨੋਟ ਪੜ੍ਹ ਸਕਦਾ ਹਾਂ। ਆਪਣਾ ਨਾਂ ਅਤੇ ਬੂਥ ਭੇਜੋ, ਜਾਂ ਕੋਈ ਮੈਸੇਜ ਫਾਰਵਰਡ ਕਰੋ।"},
    "check_usage": {"en": "Reply to a forwarded message or screenshot with /check, or send /check <claim text>.",
                    "hi": "किसी फ़ॉरवर्ड संदेश या स्क्रीनशॉट का /check से जवाब दें, या /check <दावा> भेजें।",
                    "pa": "ਕਿਸੇ ਫ਼ਾਰਵਰਡ ਸੁਨੇਹੇ ਜਾਂ ਸਕ੍ਰੀਨਸ਼ਾਟ ਦਾ /check ਨਾਲ ਜਵਾਬ ਦਿਓ, ਜਾਂ /check <ਦਾਅਵਾ> ਭੇਜੋ।"},
    "start": {
        "en": ("RollWatch helps you check a voter roll entry and check viral claims about the roll. "
               "This demo uses a synthetic district, Sampleabad.\n"
               "• Type your name and booth, e.g. \"meena kumari booth 47\".\n"
               "• Forward a message or screenshot, or send /check <claim>, to check a claim.\n"
               "• Send a Hindi voice note to ask by voice.\n"
               "• Got a notice? Send \"documents\" and your date of birth, e.g. \"documents 15/08/1990\"."),
        "hi": ("RollWatch से आप मतदाता सूची में अपना नाम और सूची के बारे में वायरल दावे जाँच सकते हैं। "
               "यह डेमो काल्पनिक ज़िले सैम्पलाबाद पर चलता है।\n"
               "• अपना नाम और बूथ लिखें, जैसे \"मीना कुमारी बूथ 47\"।\n"
               "• दावा जाँचने के लिए संदेश या स्क्रीनशॉट फ़ॉरवर्ड करें, या /check <दावा> भेजें।\n"
               "• आवाज़ से पूछने के लिए हिंदी वॉइस नोट भेजें।\n"
               "• नोटिस आया? \"दस्तावेज़\" और अपनी जन्म-तिथि भेजें, जैसे \"दस्तावेज़ 15/08/1990\"।"),
        "pa": ("RollWatch ਨਾਲ ਤੁਸੀਂ ਵੋਟਰ ਸੂਚੀ ਵਿੱਚ ਆਪਣਾ ਨਾਂ ਅਤੇ ਸੂਚੀ ਬਾਰੇ ਵਾਇਰਲ ਦਾਅਵੇ ਜਾਂਚ ਸਕਦੇ ਹੋ। "
               "ਇਹ ਡੈਮੋ ਕਾਲਪਨਿਕ ਜ਼ਿਲ੍ਹੇ ਸੈਂਪਲਾਬਾਦ 'ਤੇ ਚੱਲਦਾ ਹੈ।\n"
               "• ਆਪਣਾ ਨਾਂ ਅਤੇ ਬੂਥ ਲਿਖੋ।\n"
               "• ਦਾਅਵਾ ਜਾਂਚਣ ਲਈ ਸੁਨੇਹਾ ਜਾਂ ਸਕ੍ਰੀਨਸ਼ਾਟ ਫ਼ਾਰਵਰਡ ਕਰੋ, ਜਾਂ /check <ਦਾਅਵਾ> ਭੇਜੋ।\n"
               "• ਨੋਟਿਸ ਆਇਆ? \"ਦਸਤਾਵੇਜ਼\" ਅਤੇ ਆਪਣੀ ਜਨਮ-ਤਾਰੀਖ਼ ਭੇਜੋ, ਜਿਵੇਂ \"ਦਸਤਾਵੇਜ਼ 15/08/1990\"।"),
    },
}


def footer(lang: str) -> str:
    return C.PORTAL_LINE[lang] + "\n" + C.SCAM_LINE[lang]


def with_footer(text: str, lang: str) -> str:
    """Every bot answer ends with the portal line + the BLO-scam line (once)."""
    text = (text or "").rstrip()
    if C.SCAM_LINE[lang] in text and C.PORTAL_LINE[lang] in text:
        return text
    return (text + "\n\n" if text else "") + footer(lang)
