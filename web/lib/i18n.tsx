"use client";
import React, { createContext, useContext, useEffect, useState } from "react";

export type Language = "en" | "hi" | "bn" | "mr" | "ta" | "te" | "pa";

export interface LanguageInfo {
  code: Language;
  label: string;
  native: string;
}

export const LANGUAGES: LanguageInfo[] = [
  { code: "en", label: "English", native: "English" },
  { code: "hi", label: "Hindi", native: "हिन्दी" },
  { code: "bn", label: "Bengali", native: "বাংলা" },
  { code: "mr", label: "Marathi", native: "मराठी" },
  { code: "ta", label: "Tamil", native: "தமிழ்" },
  { code: "te", label: "Telugu", native: "తెలుగు" },
  { code: "pa", label: "Punjabi", native: "ਪੰਜਾਬੀ" },
];

export const DICT: Record<Language, Record<string, string>> = {
  en: {
    nav_audit: "Audit",
    nav_check: "Check",
    nav_ask: "Ask",
    nav_run: "Run it",
    nav_pricing: "Pricing",
    nav_trust: "Trust",
    nav_keys: "Keys",
    nav_account: "Account",
    nav_signin: "Sign in",
    skip_to_content: "Skip to main content",
    banner_note: "synthetic data · sampleabad is fictional · flags are patterns for human review, not findings",
    search_placeholder: "Search voter by name (e.g. Meena Kumari) or booth number...",
    status_verified: "Verified",
    status_disputed: "Disputed",
    status_mixed: "Mixed",
    status_unprovable: "Unprovable",
    demo_tour_title: "Guided Tour",
    demo_tour_start: "Start Tour",
    a11y_high_contrast: "High contrast mode",
  },
  hi: {
    nav_audit: "ऑडिट",
    nav_check: "दावा जाँच",
    nav_ask: "सवाल पूछें",
    nav_run: "रन करें",
    nav_pricing: "मूल्य",
    nav_trust: "विश्वसनीयता",
    nav_keys: "कुंजियाँ",
    nav_account: "खाता",
    nav_signin: "साइन इन",
    skip_to_content: "मुख्य सामग्री पर जाएँ",
    banner_note: "काल्पनिक डेटा · सैम्पलाबाद एक काल्पनिक ज़िला है · फ़्लैग इंसानी समीक्षा के लिए हैं, अंतिम निष्कर्ष नहीं",
    search_placeholder: "मतदाता का नाम या बूथ नंबर खोजें...",
    status_verified: "पुष्टि हुई",
    status_disputed: "खारिज",
    status_mixed: "मिश्रित",
    status_unprovable: "अपुष्ट",
    demo_tour_title: "मार्गदर्शित दौरा",
    demo_tour_start: "दौरा शुरू करें",
    a11y_high_contrast: "उच्च कंट्रास्ट मोड",
  },
  bn: {
    nav_audit: "অডিট",
    nav_check: "যাচাই",
    nav_ask: "প্রশ্ন করুন",
    nav_run: "চালান",
    nav_pricing: "মূল্য",
    nav_trust: "বিশ্বাসযোগ্যতা",
    nav_keys: "কীসমূহ",
    nav_account: "অ্যাকাউন্ট",
    nav_signin: "সাইন ইন",
    skip_to_content: "মূল বিষয়ে যান",
    banner_note: "কৃত্রিম ডেটা · স্যাম্পলাবাদ কাল্পনিক জেলা · ফ্ল্যাগগুলি মানবিক পর্যালোচনার নিদর্শন, চূড়ান্ত রায় নয়",
    search_placeholder: "নাম বা বুথ নম্বর দিয়ে ভোটার খুঁজুন...",
    status_verified: "যাচাইকৃত",
    status_disputed: "বিতর্কিত",
    status_mixed: "মিশ্র",
    status_unprovable: "প্রমাণহীন",
    demo_tour_title: "ট্যুর গাইড",
    demo_tour_start: "ট্যুর শুরু করুন",
    a11y_high_contrast: "উচ্চ কনট্রাস্ট মোড",
  },
  mr: {
    nav_audit: "ऑडिट",
    nav_check: "तपासा",
    nav_ask: "विचारा",
    nav_run: "सुरू करा",
    nav_pricing: "दर",
    nav_trust: "विश्वासार्हता",
    nav_keys: "चाव्या",
    nav_account: "खाते",
    nav_signin: "साइन इन",
    skip_to_content: "मुख्य मजकुरावर जा",
    banner_note: "काल्पनिक माहिती · सॅम्पलाबाद हा काल्पनिक जिल्हा आहे · फ्लॅग मानवी पुनरावलोकनासाठी आहेत",
    search_placeholder: "नावाने किंवा बूथ क्रमांकाने मतदार शोधा...",
    status_verified: "पडताळलेले",
    status_disputed: "अस्वीकृत",
    status_mixed: "मिश्र",
    status_unprovable: "असिद्ध",
    demo_tour_title: "मार्गदर्शित टूर",
    demo_tour_start: "टूर सुरू करा",
    a11y_high_contrast: "हाय कॉन्ट्रास्ट मोड",
  },
  ta: {
    nav_audit: "தணிக்கை",
    nav_check: "சரிபார்",
    nav_ask: "கேள்வி",
    nav_run: "இயக்கு",
    nav_pricing: "விலை",
    nav_trust: "நம்பகத்தன்மை",
    nav_keys: "சாவிகள்",
    nav_account: "கணக்கு",
    nav_signin: "உள்நுழைக",
    skip_to_content: "முதன்மை உள்ளடக்கத்திற்குச் செல்",
    banner_note: "மாதிரித் தரவு · மாதிரி மாவட்டம் சாம்பிளாபாத் · குறிகள் மனித மறுஆய்வுக்கானவை",
    search_placeholder: "பெயர் அல்லது வாக்குச்சாவடி எண்ணைத் தேடுங்கள்...",
    status_verified: "சரிபார்க்கப்பட்டது",
    status_disputed: "மறுக்கப்பட்டது",
    status_mixed: "கலப்பு",
    status_unprovable: "நிரூபிக்க இயலாது",
    demo_tour_title: "வழிகாட்டப்பட்ட பயணம்",
    demo_tour_start: "பயணத்தைத் தொடங்கு",
    a11y_high_contrast: "உயர் மாறுபட்ட பயன்முறை",
  },
  te: {
    nav_audit: "ఆడిట్",
    nav_check: "పరిశీలన",
    nav_ask: "ప్రశ్నించండి",
    nav_run: "రన్ చేయండి",
    nav_pricing: "ధరలు",
    nav_trust: "విశ్వసనీయత",
    nav_keys: "కీలు",
    nav_account: "ఖాతా",
    nav_signin: "సైన్ ఇన్",
    skip_to_content: "ముఖ్య విషయానికి వెళ్లండి",
    banner_note: "నమూనా సమాచారం · శాంపిలాబాద్ కల్పిత జిల్లా · ఫ్లాగ్‌లు మానవ సమీక్ష కోసం మాత్రమే",
    search_placeholder: "పేరు లేదా బూత్ సంఖ్యతో ఓటరును శోధించండి...",
    status_verified: "ధృవీకరించబడింది",
    status_disputed: "తిరస్కరించబడింది",
    status_mixed: "మిశ్రమ",
    status_unprovable: "నిరూపించలేనిది",
    demo_tour_title: "గైడెడ్ టూర్",
    demo_tour_start: "టూర్ ప్రారంభించండి",
    a11y_high_contrast: "హై కాంట్రాస్ట్ మోడ్",
  },
  pa: {
    nav_audit: "ਆਡਿਟ",
    nav_check: "ਜਾਂਚ",
    nav_ask: "ਪੁੱਛੋ",
    nav_run: "ਚਲਾਓ",
    nav_pricing: "ਮੁੱਲ",
    nav_trust: "ਭਰੋਸੇਯੋਗਤਾ",
    nav_keys: "ਕੁੰਜੀਆਂ",
    nav_account: "ਖਾਤਾ",
    nav_signin: "ਸਾਇਨ ਇਨ",
    skip_to_content: "ਮੁੱਖ ਸਮੱਗਰੀ 'ਤੇ ਜਾਓ",
    banner_note: "ਕਾਲਪਨਿਕ ਡੇਟਾ · ਸੈਂਪਲਾਬਾਦ ਕਾਲਪਨਿਕ ਜ਼ਿਲ੍ਹਾ ਹੈ · ਫਲੈਗ ਮਨੁੱਖੀ ਸਮੀਖਿਆ ਲਈ ਹਨ",
    search_placeholder: "ਨਾਮ ਜਾਂ ਬੂਥ ਨੰਬਰ ਨਾਲ ਵੋਟਰ ਲੱਭੋ...",
    status_verified: "ਸਹੀ ਪਾਇਆ ਗਿਆ",
    status_disputed: "ਅਸਵੀਕਾਰ",
    status_mixed: "ਮਿਸ਼ਰਤ",
    status_unprovable: "ਅਸਾਬਤ",
    demo_tour_title: "ਗਾਈਡਡ ਟੂਰ",
    demo_tour_start: "ਟੂਰ ਸ਼ੁਰੂ ਕਰੋ",
    a11y_high_contrast: "ਉੱਚ ਕੰਟਰਾਸਟ ਮੋਡ",
  },
};

interface I18nContextType {
  lang: Language;
  setLang: (l: Language) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nContextType>({
  lang: "en",
  setLang: () => {},
  t: (k) => DICT.en[k] || k,
});

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Language>("en");

  useEffect(() => {
    const saved = localStorage.getItem("rw_lang") as Language;
    if (saved && saved in DICT) {
      setLangState(saved);
      document.documentElement.lang = saved;
    }
  }, []);

  const setLang = (l: Language) => {
    setLangState(l);
    localStorage.setItem("rw_lang", l);
    document.documentElement.lang = l;
  };

  const t = (key: string) => {
    return DICT[lang]?.[key] || DICT.en[key] || key;
  };

  return (
    <I18nContext.Provider value={{ lang, setLang, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  return useContext(I18nContext);
}
