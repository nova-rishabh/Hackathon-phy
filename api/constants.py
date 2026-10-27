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
