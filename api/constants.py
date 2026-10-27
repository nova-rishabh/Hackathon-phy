"""Procedural templates for the citizen assistant (hi / en / pa).

Exempt from the neutrality guard: only procedural facts and the official portal name.
Every form number / helpline fact is marked VERIFY and must be checked at H0.
"""

PORTAL_URL = "voters.eci.gov.in"  # VERIFY at H0 on voters.eci.gov.in
HELPLINE = "1950"  # VERIFY at H0 on voters.eci.gov.in
FORM_NEW = "6"  # VERIFY at H0 on voters.eci.gov.in  (new registration / re-inclusion)
FORM_OBJECT = "7"  # VERIFY at H0 on voters.eci.gov.in  (objection / deletion)
FORM_CORRECT = "8"  # VERIFY at H0 on voters.eci.gov.in  (shift / correction)

LANGS = ("hi", "en", "pa")

PORTAL_LINE = {  # VERIFY at H0 on voters.eci.gov.in
    "en": "Verify on the official voter portal voters.eci.gov.in or call 1950.",
    "hi": "आधिकारिक मतदाता पोर्टल voters.eci.gov.in पर जाँच करें या 1950 पर कॉल करें।",
    "pa": "ਅਧਿਕਾਰਤ ਵੋਟਰ ਪੋਰਟਲ voters.eci.gov.in 'ਤੇ ਜਾਂਚ ਕਰੋ ਜਾਂ 1950 'ਤੇ ਕਾਲ ਕਰੋ।",
}

SCAM_LINE = {
    "en": "A BLO never asks for an OTP or money.",
    "hi": "बीएलओ कभी ओटीपी या पैसे नहीं माँगता।",
    "pa": "ਬੀਐਲਓ ਕਦੇ ਵੀ ਓਟੀਪੀ ਜਾਂ ਪੈਸੇ ਨਹੀਂ ਮੰਗਦਾ।",
}

# Next steps (VERIFY form numbers at H0 on voters.eci.gov.in)
_BLO = {
    "en": "Meet your Booth Level Officer (BLO) and ask about this record.",
    "hi": "अपने बूथ लेवल ऑफिसर (बीएलओ) से मिलें और इस रिकॉर्ड के बारे में पूछें।",
    "pa": "ਆਪਣੇ ਬੂਥ ਲੈਵਲ ਅਫ਼ਸਰ (ਬੀਐਲਓ) ਨੂੰ ਮਿਲੋ ਅਤੇ ਇਸ ਰਿਕਾਰਡ ਬਾਰੇ ਪੁੱਛੋ।",
}
_F6 = {  # VERIFY at H0 on voters.eci.gov.in
    "en": "If you still live here, file Form 6 on the portal to be added again.",
    "hi": "अगर आप अब भी यहीं रहते हैं, तो दोबारा नाम जुड़वाने के लिए पोर्टल पर फ़ॉर्म 6 भरें।",
    "pa": "ਜੇ ਤੁਸੀਂ ਹਾਲੇ ਵੀ ਇੱਥੇ ਰਹਿੰਦੇ ਹੋ, ਤਾਂ ਦੁਬਾਰਾ ਨਾਂ ਜੁੜਵਾਉਣ ਲਈ ਪੋਰਟਲ 'ਤੇ ਫ਼ਾਰਮ 6 ਭਰੋ।",
}
_F6_NEW = {  # VERIFY at H0 on voters.eci.gov.in
    "en": "If you are not registered, file Form 6 on the portal to register.",
    "hi": "अगर आपका नाम दर्ज नहीं है, तो पंजीकरण के लिए पोर्टल पर फ़ॉर्म 6 भरें।",
    "pa": "ਜੇ ਤੁਹਾਡਾ ਨਾਂ ਦਰਜ ਨਹੀਂ ਹੈ, ਤਾਂ ਰਜਿਸਟਰ ਕਰਨ ਲਈ ਪੋਰਟਲ 'ਤੇ ਫ਼ਾਰਮ 6 ਭਰੋ।",
}
_F7 = {  # VERIFY at H0 on voters.eci.gov.in
    "en": "If this record is wrong or is not yours, file Form 7 to object.",
    "hi": "अगर यह रिकॉर्ड गलत है या आपका नहीं है, तो आपत्ति के लिए फ़ॉर्म 7 भरें।",
    "pa": "ਜੇ ਇਹ ਰਿਕਾਰਡ ਗ਼ਲਤ ਹੈ ਜਾਂ ਤੁਹਾਡਾ ਨਹੀਂ ਹੈ, ਤਾਂ ਇਤਰਾਜ਼ ਲਈ ਫ਼ਾਰਮ 7 ਭਰੋ।",
}
_F8 = {  # VERIFY at H0 on voters.eci.gov.in
    "en": "To fix details or move your entry to a new address, file Form 8.",
    "hi": "विवरण सुधारने या नए पते पर नाम बदलवाने के लिए फ़ॉर्म 8 भरें।",
    "pa": "ਵੇਰਵੇ ਸੁਧਾਰਨ ਜਾਂ ਨਵੇਂ ਪਤੇ 'ਤੇ ਨਾਂ ਬਦਲਵਾਉਣ ਲਈ ਫ਼ਾਰਮ 8 ਭਰੋ।",
}
_NOTHING = {
    "en": "You do not need to do anything. Keep your voter slip safe.",
    "hi": "आपको कुछ करने की ज़रूरत नहीं है। अपनी वोटर पर्ची संभालकर रखें।",
    "pa": "ਤੁਹਾਨੂੰ ਕੁਝ ਕਰਨ ਦੀ ਲੋੜ ਨਹੀਂ ਹੈ। ਆਪਣੀ ਵੋਟਰ ਪਰਚੀ ਸੰਭਾਲ ਕੇ ਰੱਖੋ।",
}
_TRY_AGAIN = {
    "en": "Try again with the full name as printed on your voter slip, and your booth number.",
    "hi": "वोटर पर्ची पर छपे पूरे नाम और अपने बूथ नंबर के साथ दोबारा कोशिश करें।",
    "pa": "ਵੋਟਰ ਪਰਚੀ 'ਤੇ ਛਪੇ ਪੂਰੇ ਨਾਂ ਅਤੇ ਆਪਣੇ ਬੂਥ ਨੰਬਰ ਨਾਲ ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
}

# status -> (reason category or None) -> list of step dicts, in order
NEXT_STEPS = {
    "present": {None: [_NOTHING]},
    "modified": {
        "boundary_change": [_BLO, _F8],
        None: [_BLO, _F8, _F7],
    },
    "not_in_new_list": {
        "death_registered": [_BLO, _F7],
        "duplicate_cleanup": [_BLO, _NOTHING],
        "boundary_change": [_BLO, _F8],
        "shifted": [_BLO, _F6, _F8],
        "unexplained": [_BLO, _F6, _F7],
        None: [_BLO, _F6, _F7],
    },
    "not_found": {None: [_TRY_AGAIN, _F6_NEW, _BLO]},
}

STATUS_LINE = {
    "present": {
        "en": "Your name ({name}) is in the new list, Booth {booth}.",
        "hi": "आपका नाम ({name}) नई सूची में है, बूथ {booth}।",
        "pa": "ਤੁਹਾਡਾ ਨਾਂ ({name}) ਨਵੀਂ ਸੂਚੀ ਵਿੱਚ ਹੈ, ਬੂਥ {booth}।",
    },
    "modified": {
        "en": "Your name ({name}) is in the new list, but some details changed. Booth {booth}.",
        "hi": "आपका नाम ({name}) नई सूची में है, लेकिन कुछ विवरण बदले हैं। बूथ {booth}।",
        "pa": "ਤੁਹਾਡਾ ਨਾਂ ({name}) ਨਵੀਂ ਸੂਚੀ ਵਿੱਚ ਹੈ, ਪਰ ਕੁਝ ਵੇਰਵੇ ਬਦਲੇ ਹਨ। ਬੂਥ {booth}।",
    },
    "not_in_new_list": {
        "en": "Your name ({name}) is not in the new list.",
        "hi": "आपका नाम ({name}) नई सूची में नहीं है।",
        "pa": "ਤੁਹਾਡਾ ਨਾਂ ({name}) ਨਵੀਂ ਸੂਚੀ ਵਿੱਚ ਨਹੀਂ ਹੈ।",
    },
    "not_found": {
        "en": "We could not find a close match for this name.",
        "hi": "इस नाम से मिलता-जुलता कोई रिकॉर्ड नहीं मिला।",
        "pa": "ਇਸ ਨਾਂ ਨਾਲ ਮਿਲਦਾ-ਜੁਲਦਾ ਕੋਈ ਰਿਕਾਰਡ ਨਹੀਂ ਮਿਲਿਆ।",
    },
}

REASON_LINE = {
    "death_registered": {
        "en": "The likely reason: a death was registered for this entry.",
        "hi": "संभावित कारण: इस प्रविष्टि के लिए मृत्यु दर्ज है।",
        "pa": "ਸੰਭਾਵੀ ਕਾਰਨ: ਇਸ ਐਂਟਰੀ ਲਈ ਮੌਤ ਦਰਜ ਹੈ।",
    },
    "duplicate_cleanup": {
        "en": "The likely reason: this was a duplicate entry, and the other copy remains.",
        "hi": "संभावित कारण: यह दोहरी प्रविष्टि थी, और दूसरी प्रति सूची में बनी है।",
        "pa": "ਸੰਭਾਵੀ ਕਾਰਨ: ਇਹ ਦੋਹਰੀ ਐਂਟਰੀ ਸੀ, ਅਤੇ ਦੂਜੀ ਕਾਪੀ ਸੂਚੀ ਵਿੱਚ ਹੈ।",
    },
    "boundary_change": {
        "en": "The likely reason: the booth boundary changed and your entry moved to another booth.",
        "hi": "संभावित कारण: बूथ की सीमा बदली और आपकी प्रविष्टि दूसरे बूथ में चली गई।",
        "pa": "ਸੰਭਾਵੀ ਕਾਰਨ: ਬੂਥ ਦੀ ਹੱਦ ਬਦਲੀ ਅਤੇ ਤੁਹਾਡੀ ਐਂਟਰੀ ਦੂਜੇ ਬੂਥ ਵਿੱਚ ਚਲੀ ਗਈ।",
    },
    "shifted": {
        "en": "The likely reason: the address looks like a place people move out of (shifted).",
        "hi": "संभावित कारण: यह पता ऐसा है जहाँ से लोग स्थानांतरित हो जाते हैं (स्थान बदला)।",
        "pa": "ਸੰਭਾਵੀ ਕਾਰਨ: ਇਹ ਪਤਾ ਅਜਿਹਾ ਹੈ ਜਿੱਥੋਂ ਲੋਕ ਚਲੇ ਜਾਂਦੇ ਹਨ (ਟਿਕਾਣਾ ਬਦਲਿਆ)।",
    },
    "unexplained": {
        "en": "We cannot tell the reason from the records. Please check with your BLO.",
        "hi": "रिकॉर्ड से कारण पता नहीं चलता। कृपया अपने बीएलओ से पूछें।",
        "pa": "ਰਿਕਾਰਡ ਤੋਂ ਕਾਰਨ ਪਤਾ ਨਹੀਂ ਲੱਗਦਾ। ਕਿਰਪਾ ਕਰਕੇ ਆਪਣੇ ਬੀਐਲਓ ਨਾਲ ਸੰਪਰਕ ਕਰੋ।",
    },
}

LABELS = {
    "next": {"en": "What to do next:", "hi": "आगे क्या करें:", "pa": "ਅੱਗੇ ਕੀ ਕਰਨਾ ਹੈ:"},
    "sure": {
        "en": "How sure: {pct}% name match. A human (your BLO) should confirm.",
        "hi": "कितना भरोसा: नाम {pct}% मिलता है। अंतिम पुष्टि इंसान (आपका बीएलओ) करे।",
        "pa": "ਕਿੰਨਾ ਭਰੋਸਾ: ਨਾਂ {pct}% ਮਿਲਦਾ ਹੈ। ਆਖ਼ਰੀ ਪੁਸ਼ਟੀ ਇਨਸਾਨ (ਤੁਹਾਡਾ ਬੀਐਲਓ) ਕਰੇ।",
    },
    "sure_none": {
        "en": "How sure: no close match, so please double-check the spelling.",
        "hi": "कितना भरोसा: कोई नज़दीकी मेल नहीं, कृपया वर्तनी दोबारा जाँचें।",
        "pa": "ਕਿੰਨਾ ਭਰੋਸਾ: ਕੋਈ ਨੇੜਲਾ ਮੇਲ ਨਹੀਂ, ਕਿਰਪਾ ਕਰਕੇ ਸਪੈਲਿੰਗ ਦੁਬਾਰਾ ਜਾਂਚੋ।",
    },
}

VOICE_SOON = {
    "en": "Voice messages are coming soon. Please type your name for now.",
    "hi": "आवाज़ वाले संदेश जल्द आ रहे हैं। अभी कृपया अपना नाम लिखकर भेजें।",
    "pa": "ਆਵਾਜ਼ ਵਾਲੇ ਸੁਨੇਹੇ ਜਲਦ ਆ ਰਹੇ ਹਨ। ਹੁਣ ਕਿਰਪਾ ਕਰਕੇ ਆਪਣਾ ਨਾਂ ਲਿਖ ਕੇ ਭੇਜੋ।",
}

NO_QUERY = {
    "en": "Please type your name as printed on your voter slip.",
    "hi": "कृपया वोटर पर्ची पर छपा अपना नाम लिखें।",
    "pa": "ਕਿਰਪਾ ਕਰਕੇ ਵੋਟਰ ਪਰਚੀ 'ਤੇ ਛਪਿਆ ਆਪਣਾ ਨਾਂ ਲਿਖੋ।",
}

# words dropped when extracting the name from a chat sentence
STOPWORDS = set("""
is my name in the list voter roll new check please find search for me i am a an of
booth number no status does exist there are what hai mera meri naam nam mein me suchi
list ka ki ke kya hain main hun
मेरा मेरी नाम क्या है सूची में लिस्ट वोटर बूथ नंबर का की के हूँ हूं मैं कृपया देखें
ਮੇਰਾ ਮੇਰੀ ਨਾਂ ਨਾਮ ਕੀ ਹੈ ਸੂਚੀ ਵਿੱਚ ਵਿੱਚ ਬੂਥ ਨੰਬਰ ਦਾ ਦੀ ਦੇ ਮੈਂ ਕਿਰਪਾ
""".split())


# ------------------------------------------------------------------ ops / LLM (A1)
# ASSUMPTION: per-token prices in INR, for the ops strip only. Update from the provider's price page.
USD_INR = 84.0  # ASSUMPTION

# National scale projection (Trust page). Per-state electors: ECI's official Lok Sabha 2024 report 9 (api/data);
# the national total is their sum, 97.8 crore (ECI reported 99.1 crore by 2025).
ELECTORS_FILE = "api/data/electors_2024_states.csv"
ELECTORS_SOURCE = "ECI Lok Sabha 2024, report 9 (state-wise electors); 99.1 crore by 2025"
STATE_AUDIT_CORES = 16  # one ordinary server
# ASSUMPTION for request sizing: share of electors who check once during a revision window, its length, peak/average.
SCALE_SHARE_CHECKING, SCALE_WINDOW_DAYS, SCALE_PEAK_FACTOR = 0.10, 30, 5
PRICE_INR_PER_MTOK = {  # ASSUMPTION: USD list price per 1M tokens x USD_INR
    "claude-sonnet-5-5": {"in": 3.0 * USD_INR, "out": 15.0 * USD_INR},
    "claude-haiku-5-5": {"in": 1.0 * USD_INR, "out": 5.0 * USD_INR},
    "gemini-3.5-flash": {"in": 0.0, "out": 0.0},  # free tier
    "template": {"in": 0.0, "out": 0.0},
}
MODEL_GEMINI = "gemini-3.5-flash"  # the only live model (free tier); 2.5-flash is closed to new keys
MODEL_SPLIT = MODEL_GEMINI
MODEL_PHRASE = MODEL_GEMINI

# ------------------------------------------------------------------ voice (ElevenLabs)
ELEVEN_TTS_MODEL = "eleven_multilingual_v2"
ELEVEN_STT_MODEL = "scribe_v1"
ELEVEN_VOICE_ID = "diwmCoikrXSjiTKbIHz9"  # "Devi", a native Hindi conversational voice (ElevenLabs library)
ELEVEN_VOICE_SETTINGS = {"stability": 0.45, "similarity_boost": 0.8, "style": 0.25, "use_speaker_boost": True}

# Spoken replies (voice notes): what a helpful person would say, not the written card read aloud.
# Filled with the citizen's own name and booth only; numbers are words where a reader would stumble.
SPOKEN = {
    "hello": {"hi": "नमस्ते।", "en": "Hello."},
    "not_in_new_list": {"hi": "{name} जी, इस बार की वोटर लिस्ट में आपका नाम नहीं है।",
                        "en": "{name}, your name is not on this year's voter list."},
    "modified": {"hi": "{name} जी, आपका नाम नई लिस्ट में है, लेकिन कुछ जानकारी बदली है।",
                 "en": "{name}, your name is on the new list, but some details have changed."},
    "present": {"hi": "{name} जी, अच्छी खबर है। आपका नाम नई लिस्ट में है, बूथ {booth} में।",
                "en": "{name}, good news. Your name is on the new list, in booth {booth}."},
    "not_found": {"hi": "माफ़ कीजिए, इस नाम से कोई मिलती-जुलती एंट्री नहीं मिली। अपना पूरा नाम और बूथ नंबर, जैसा वोटर पर्ची पर लिखा है, एक बार फिर बोलिए।",
                  "en": "Sorry, I couldn't find a close match for that name. Please say your full name and booth number again, the way they are printed on your voter slip."},
    "reason": {
        "unexplained": {"hi": "और रिकॉर्ड से इसकी वजह पता नहीं चलती।", "en": "And the records don't show why."},
        "shifted": {"hi": "रिकॉर्ड में लगता है कि आप इस पते से कहीं और चले गए हैं।",
                    "en": "The records suggest you moved away from this address."},
        "death_registered": {"hi": "रिकॉर्ड में इस नाम पर एक मृत्यु दर्ज है। अगर यह गलत है, तो इसे ठीक करवाया जा सकता है।",
                             "en": "A death is registered against this name. If that's wrong, it can be corrected."},
        "duplicate_cleanup": {"hi": "आपका नाम लिस्ट में दो बार था, और एक एंट्री हटाई गई है। देख लीजिए कि बची हुई एंट्री सही है।",
                              "en": "Your name was listed twice, and one entry was removed. Check that the remaining one is right."},
        "boundary_change": {"hi": "बूथ की सीमा बदलने से अब आपका नाम बूथ {booth} में है।",
                            "en": "Because the booth boundary changed, you're now listed in booth {booth}."},
    },
    "do_not_in_list": {"hi": "घबराइए मत। अपने बीएलओ से मिलिए और नाम दोबारा जुड़वाने के लिए फ़ॉर्म छह भरिए।",
                       "en": "Don't worry. Meet your BLO and fill Form 6 to get your name added back."},
    "do_modified": {"hi": "अगर कुछ गलत लगे, तो फ़ॉर्म आठ भरकर ठीक करवाइए।",
                    "en": "If anything looks wrong, fill Form 8 to correct it."},
    "helpline": {"hi": "कोई सवाल हो, तो उन्नीस सौ पचास पर फ़ोन कीजिए।", "en": "If you have questions, call nineteen fifty."},
    "scam": {"hi": "और हाँ, बीएलओ कभी ओटीपी या पैसे नहीं माँगता।", "en": "And remember, a BLO never asks for an OTP or money."},
}
ELEVEN_LANG = {"hi": "hin", "en": "eng", "pa": "pan"}
TTS_MAX_CHARS = 1400

# ------------------------------------------------------------------ Claim Court (A1)
CLAIM_TOLERANCE = 0.15
REASON_MOTIVE = "Motive can't be measured from roll data."
REASON_COMMUNITY = "We never infer religion, caste or community from names."
REASON_PLACE = "This tool only has data for the demo district (Sampleabad)."
REASON_NO_NUMBER = "The claim gives no number or comparison we can check."
REASON_UNKNOWN = "This part does not map to any check we can run on roll data."
SETTLE_COMMUNITY = "Cannot be settled from roll data; no attribute of this kind is recorded."
SETTLE_MOTIVE = "A formal objection (Form 7) or an inquiry by the electoral officer, not roll arithmetic."
SETTLE_DEFAULT = "Ask your Booth Level Officer (BLO) or check voters.eci.gov.in."
NEEDS_REVIEW = "Needs human review."

# Neutral fallback text for guard failures (templates; already neutral).
GUARD_FALLBACK = {
    "en": "This text was replaced by a neutral summary. The numbers above are computed from the roll. Needs human review.",
    "hi": "यह पाठ एक तटस्थ सारांश से बदला गया। ऊपर की संख्याएँ सूची से गणना की गई हैं। मानवीय समीक्षा ज़रूरी है।",
    "pa": "ਇਹ ਲਿਖਤ ਇੱਕ ਨਿਰਪੱਖ ਸਾਰ ਨਾਲ ਬਦਲੀ ਗਈ। ਉੱਪਰਲੇ ਅੰਕੜੇ ਸੂਚੀ ਤੋਂ ਗਿਣੇ ਗਏ ਹਨ। ਮਨੁੱਖੀ ਸਮੀਖਿਆ ਲੋੜੀਂਦੀ ਹੈ।",
}
# Documents if an ERO notice arrives (the SIR "Information Sheet for Enumeration Form", as handed out by BLOs).
# Which documents depends on date of birth; we only know age on the roll's qualifying date, so the bracket is
# estimated from age and both cases are shown when the birth window straddles a cutoff.
ROLL_QUALIFYING_DATE = "2025-01-01"  # synthetic district's qualifying date (ASSUMPTION for the demo roll)
DOB_CUTOFFS = ("1987-07-01", "2004-12-02")
DOCS_HEAD = {
    "en": "If you get a notice, the documents you need depend on when you were born:",
    "hi": "अगर नोटिस आए, तो ज़रूरी दस्तावेज़ इस पर निर्भर हैं कि आपका जन्म कब हुआ:",
    "pa": "ਜੇ ਨੋਟਿਸ ਆਵੇ, ਤਾਂ ਲੋੜੀਂਦੇ ਦਸਤਾਵੇਜ਼ ਇਸ 'ਤੇ ਨਿਰਭਰ ਹਨ ਕਿ ਤੁਹਾਡਾ ਜਨਮ ਕਦੋਂ ਹੋਇਆ:",
}
DOCS_BRACKET = {
    "before": {"en": "Born before 1 July 1987: one document for yourself.",
               "hi": "1 जुलाई 1987 से पहले जन्म: अपने लिए एक दस्तावेज़।",
               "pa": "1 ਜੁਲਾਈ 1987 ਤੋਂ ਪਹਿਲਾਂ ਜਨਮ: ਆਪਣੇ ਲਈ ਇੱਕ ਦਸਤਾਵੇਜ਼।"},
    "between": {"en": "Born 1 July 1987 to 2 December 2004: one for yourself, and one for your father or mother.",
                "hi": "1 जुलाई 1987 से 2 दिसंबर 2004 के बीच जन्म: एक अपने लिए, और एक पिता या माता के लिए।",
                "pa": "1 ਜੁਲਾਈ 1987 ਤੋਂ 2 ਦਸੰਬਰ 2004 ਵਿਚਕਾਰ ਜਨਮ: ਇੱਕ ਆਪਣੇ ਲਈ, ਅਤੇ ਇੱਕ ਪਿਤਾ ਜਾਂ ਮਾਤਾ ਲਈ।"},
    "after": {"en": "Born after 2 December 2004: one for yourself, one for your father and one for your mother "
                    "(a passport and visa copy if a parent was not Indian at your birth).",
              "hi": "2 दिसंबर 2004 के बाद जन्म: एक अपने लिए, एक पिता के लिए और एक माता के लिए "
                    "(अगर जन्म के समय कोई अभिभावक भारतीय नहीं थे, तो उनके पासपोर्ट और वीज़ा की कॉपी)।",
              "pa": "2 ਦਸੰਬਰ 2004 ਤੋਂ ਬਾਅਦ ਜਨਮ: ਇੱਕ ਆਪਣੇ ਲਈ, ਇੱਕ ਪਿਤਾ ਲਈ ਅਤੇ ਇੱਕ ਮਾਤਾ ਲਈ "
                    "(ਜੇ ਜਨਮ ਸਮੇਂ ਕੋਈ ਮਾਪਾ ਭਾਰਤੀ ਨਹੀਂ ਸੀ, ਤਾਂ ਉਸਦੇ ਪਾਸਪੋਰਟ ਅਤੇ ਵੀਜ਼ਾ ਦੀ ਕਾਪੀ)।"},
}
DOCS_UNSURE = {
    "en": "Your age puts your birth near a cutoff date, so check which of these applies:",
    "hi": "आपकी उम्र के हिसाब से जन्म-तिथि सीमा के पास है, इसलिए देखें कि इनमें से कौन-सा लागू है:",
    "pa": "ਤੁਹਾਡੀ ਉਮਰ ਮੁਤਾਬਕ ਜਨਮ-ਤਾਰੀਖ਼ ਹੱਦ ਦੇ ਨੇੜੇ ਹੈ, ਇਸ ਲਈ ਵੇਖੋ ਕਿ ਇਨ੍ਹਾਂ ਵਿੱਚੋਂ ਕਿਹੜਾ ਲਾਗੂ ਹੈ:",
}
DOCS_OTHER = {
    "en": ["Born outside India: proof of birth registration from the Indian Mission abroad.",
           "Citizen by registration or naturalisation: the Certificate of Registration of Citizenship."],
    "hi": ["भारत के बाहर जन्म: विदेश में भारतीय मिशन से जन्म पंजीकरण का प्रमाण।",
           "पंजीकरण या देशीकरण से नागरिकता: नागरिकता पंजीकरण प्रमाणपत्र।"],
    "pa": ["ਭਾਰਤ ਤੋਂ ਬਾਹਰ ਜਨਮ: ਵਿਦੇਸ਼ ਵਿੱਚ ਭਾਰਤੀ ਮਿਸ਼ਨ ਤੋਂ ਜਨਮ ਰਜਿਸਟ੍ਰੇਸ਼ਨ ਦਾ ਸਬੂਤ।",
           "ਰਜਿਸਟ੍ਰੇਸ਼ਨ ਜਾਂ ਨੈਚੁਰਲਾਈਜ਼ੇਸ਼ਨ ਨਾਲ ਨਾਗਰਿਕਤਾ: ਨਾਗਰਿਕਤਾ ਰਜਿਸਟ੍ਰੇਸ਼ਨ ਸਰਟੀਫਿਕੇਟ।"],
}
DOCS_SOURCE = "SIR Information Sheet for Enumeration Form, as handed out by BLOs. Indicative, not exhaustive: confirm with your BLO."
DOCS_LIST = {
    "en": "Accepted documents include a birth certificate, passport, school-board (matriculation) certificate, a "
          "government or PSU employee ID or pension order, a permanent residence certificate, a family register or "
          "a government land or house allotment certificate (indicative list; Aadhaar as per ECI directions).",
    "hi": "मान्य दस्तावेज़ों में जन्म प्रमाणपत्र, पासपोर्ट, मैट्रिक प्रमाणपत्र, सरकारी या सार्वजनिक उपक्रम कर्मचारी पहचान-पत्र "
          "या पेंशन आदेश, स्थायी निवास प्रमाणपत्र, परिवार रजिस्टर या सरकारी ज़मीन या मकान आवंटन प्रमाणपत्र शामिल हैं "
          "(सूची पूरी नहीं है; आधार के लिए आयोग के निर्देश लागू)।",
    "pa": "ਮੰਨਣਯੋਗ ਦਸਤਾਵੇਜ਼ਾਂ ਵਿੱਚ ਜਨਮ ਸਰਟੀਫਿਕੇਟ, ਪਾਸਪੋਰਟ, ਮੈਟ੍ਰਿਕ ਸਰਟੀਫਿਕੇਟ, ਸਰਕਾਰੀ ਜਾਂ ਜਨਤਕ ਅਦਾਰੇ ਦਾ ਕਰਮਚਾਰੀ ਪਛਾਣ-ਪੱਤਰ "
          "ਜਾਂ ਪੈਨਸ਼ਨ ਹੁਕਮ, ਪੱਕੀ ਰਿਹਾਇਸ਼ ਸਰਟੀਫਿਕੇਟ, ਪਰਿਵਾਰ ਰਜਿਸਟਰ ਜਾਂ ਸਰਕਾਰੀ ਜ਼ਮੀਨ ਜਾਂ ਮਕਾਨ ਅਲਾਟਮੈਂਟ ਸਰਟੀਫਿਕੇਟ ਸ਼ਾਮਲ ਹਨ "
          "(ਸੂਚੀ ਪੂਰੀ ਨਹੀਂ; ਆਧਾਰ ਲਈ ਕਮਿਸ਼ਨ ਦੀਆਂ ਹਦਾਇਤਾਂ ਲਾਗੂ)।",
}

DEADLINE_LINE = {  # VERIFY the claims/objections window at H0 on voters.eci.gov.in
    "en": "Claims and objections have a deadline. Check the current dates on the portal and act before then.",
    "hi": "दावे और आपत्तियों की एक अंतिम तिथि होती है। पोर्टल पर मौजूदा तारीखें देखें और उससे पहले कार्रवाई करें।",
    "pa": "ਦਾਅਵਿਆਂ ਅਤੇ ਇਤਰਾਜ਼ਾਂ ਦੀ ਇੱਕ ਆਖ਼ਰੀ ਤਾਰੀਖ਼ ਹੁੰਦੀ ਹੈ। ਪੋਰਟਲ 'ਤੇ ਮੌਜੂਦਾ ਤਾਰੀਖ਼ਾਂ ਵੇਖੋ ਅਤੇ ਉਸ ਤੋਂ ਪਹਿਲਾਂ ਕਾਰਵਾਈ ਕਰੋ।",
}

STOPWORDS |= set("boot age umar umr saal sal years old naam: hello hi namaste".split())
# Spoken filler: voice notes come in full sentences ("namaste, mera naam ... hai, booth 47").
STOPWORDS |= set("""from hey hii hiii sir madam ji namaskar can you tell check please this here
नमस्ते नमस्कार हेलो हैलो हाय जी बताइए बताइये बताओ बताएं चेक करो करें कीजिए कीजिये देखो देखिए यह ये वाला वाली से
ਸਤ ਸ੍ਰੀ ਅਕਾਲ ਹੈਲੋ ਜੀ ਦੱਸੋ ਚੈੱਕ ਕਰੋ""".split())

# ------------------------------------------------------------------ rule cards (Trust page, M10)
# Per rule: (innocent explanations, what resolves it). Rates come from engine/eval.py -> rules.json.
RULE_CONTEXT = {
    "official_parent_age_gap": (["A grandparent or guardian named as the relative", "An age written wrongly at enrolment",
                                 "A late child or a young step-parent"],
                                "Ask the family; a Form 8 correction fixes the relation or the age."),
    "official_grandparent_age_gap": (["Ages written as estimates at enrolment", "A step-family or an adoptive link"],
                                     "Ask the family; a Form 8 correction fixes an age."),
    "official_many_children": (["A large or joint family", "Cousins listed under the head of the house"],
                               "A BLO visit confirms the household; nothing to correct if it is right."),
    "official_name_changed": (["A spelling corrected between rolls", "The same name written in another script or style"],
                              "Compare with the elector's ID; Form 8 if the new spelling is wrong."),
    "official_relative_name_changed": (["A spelling corrected between rolls", "Father's name replaced by husband's after marriage"],
                                       "Ask the elector; Form 8 fixes the relative's name."),
    "official_relation_type_changed": (["Marriage: father's name replaced by husband's", "The old form's 'father's/husband's name' field"],
                                       "Ask the elector; Form 8 fixes the relation type."),
    "official_age_progression": (["An age corrected after a document check", "A data-entry slip in either roll"],
                                 "Compare with the elector's birth document; Form 8 fixes the age."),
    "deletion_spike": (["Deaths recorded in the death register", "A hostel or institution emptying",
                        "A boundary redraw moving records out", "Duplicate cleanup"],
                       "Match the removals against death, hostel and boundary records; then the BLO's field check."),
    "addition_spike": (["New housing or a new colony in the booth area",
                        "A registration drive (for example, first-time voters turning 18)",
                        "Records moved in by a boundary change"],
                       "Compare with Form 6 receipts and the boundary change log."),
    "duplicate_cluster": (["Two different people with similar names in one family",
                           "The same name typed in two scripts"],
                          "A field check by the BLO; a Form 7 objection if one record is truly extra."),
    "gender_ratio_swing": (["A hostel or institution for one gender opening or closing",
                            "A boundary change"],
                           "Check institution lists and the boundary change log for the booth."),
    "impossible_age": (["A data entry error in the age or birth year"],
                       "A Form 8 correction after the voter confirms their age."),
    "oversized_household": (["A hostel, ashram or other shared residence", "Several flats sharing one house number"],
                            "A BLO field check of the address."),
    "relation_conflict": (["A typing error in the relative's name or age", "Two people with the same name in one house"],
                          "A Form 8 correction after the family confirms the relation."),
}

# WhatsApp sign-in code (sent by the wa/ worker). Plain text, no emoji.
WA_OTP_TEXT = {
    "en": "Your RollWatch code is {code}. It expires in 5 minutes. Never share it with anyone, including a BLO.",
}

# Watched booths (numbers filled in from the engine). Plain text, no emoji.
WA_BOOTH_STATUS = {
    "en": "Booth {b}: {removed} names removed between the two lists, {unexplained}% not explained by any record. {label}.",
    "en_normal": "Booth {b}: {removed} names removed between the two lists, about what a booth like this usually loses. {label}.",
}
WA_BOOTH_LABEL = {
    "review": "Needs human review",
    "benign": "Likely benign: a record explains most of it",
    "normal": "In line with a normal booth",
}
WA_WATCH_TEXT = {
    "en": "You are watching Booth {b} on RollWatch.\n{status}\nWe will message you when a new audit changes it. "
          "Synthetic demo district. Patterns for human review, not findings.",
}
WA_ALERT_TEXT = {
    "en": "RollWatch: a new audit ran.\n{status}\nSee why: {link}\nPatterns for human review, not findings.",
}

# ------------------------------------------------------------------ pricing (Pricing page; Razorpay subscriptions)
# ASSUMPTION: list prices in INR per month, set by the team. Citizens never pay. Python computes every total.
PRICING = {
    "platform": {"label": "Platform: audit dashboard, Trust page, open API", "inr": 4999},
    "constituency": {"label": "Constituency audited on every roll revision", "inr": 1500, "unit": "per constituency"},
    "whatsapp": {"label": "WhatsApp bot on your own number", "inr": 2999},
    "language": {"label": "Extra language (beyond Hindi, English, Punjabi)", "inr": 1000, "unit": "per language"},
    "reviewer": {"label": "Human-review seat", "inr": 499, "unit": "per seat"},
    "voice": {"label": "Voice replies", "inr": 0.6, "unit": "per reply"},
    "onprem": {"label": "Run on your own servers (private deployment, support)", "inr": 25000},
}
PRICING_LIMITS = {"constituencies": (1, 543), "languages": (0, 19), "reviewers": (0, 200), "voice_replies": (0, 1_000_000)}
PRICING_DISCOUNTS = {"annual_months_free": 2, "nonprofit_off": 0.5}  # newsrooms, NGOs, researchers
PRICING_PRESETS = {
    "newsroom": {"label": "Newsroom data desk", "constituencies": 5, "whatsapp": True, "languages": 0, "reviewers": 3,
                 "voice_replies": 2000, "onprem": False, "nonprofit": True},
    "watch": {"label": "Election-watch group", "constituencies": 20, "whatsapp": True, "languages": 2, "reviewers": 10,
              "voice_replies": 20000, "onprem": False, "nonprofit": True},
    "office": {"label": "Election office (check drafts before publishing)", "constituencies": 50, "whatsapp": True,
               "languages": 4, "reviewers": 25, "voice_replies": 100000, "onprem": True, "nonprofit": False},
}
PRICING_FREE = ["Name lookup on web, WhatsApp and Telegram", "Claim checks with share image",
                "Which documents a notice asks for", "Hindi, English and Punjabi, with voice"]
