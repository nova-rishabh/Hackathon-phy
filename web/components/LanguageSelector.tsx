"use client";
import React, { useState, useRef, useEffect } from "react";
import { LANGUAGES, Language, useI18n } from "@/lib/i18n";

export default function LanguageSelector() {
  const { lang, setLang } = useI18n();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const current = LANGUAGES.find((l) => l.code === lang) || LANGUAGES[0];

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative inline-block text-left" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label="Select display language"
        className="h-9 px-2.5 rounded-[8px] border border-line bg-surface hover:bg-panel transition-colors text-[13px] font-medium text-ink inline-flex items-center gap-1.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink"
      >
        <span className="text-ink-2 font-mono text-[11px] uppercase tracking-wider">{current.code}</span>
        <span className="text-[13px]">{current.native}</span>
        <svg
          className={`w-3.5 h-3.5 text-ink-3 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div
          role="listbox"
          aria-label="Languages"
          className="absolute right-0 mt-1.5 w-36 rounded-[12px] bg-surface border border-line shadow-lg py-1 z-50 focus:outline-none animate-in fade-in zoom-in-95 duration-100"
        >
          {LANGUAGES.map((item) => {
            const active = item.code === lang;
            return (
              <button
                key={item.code}
                role="option"
                aria-selected={active}
                onClick={() => {
                  setLang(item.code);
                  setOpen(false);
                }}
                className={`w-full text-left px-3 py-1.5 text-[13px] flex items-center justify-between transition-colors ${
                  active ? "bg-panel font-semibold text-ink" : "text-ink-2 hover:bg-page hover:text-ink"
                }`}
              >
                <span>{item.native}</span>
                <span className="text-[11px] font-mono text-ink-3 uppercase">{item.code}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
