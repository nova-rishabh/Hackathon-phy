"use client";
import React, { useState, useEffect } from "react";
import Link from "next/link";

export interface TourStep {
  id: string;
  badge: string;
  title: string;
  description: string;
  evidence: string;
  actionText?: string;
  actionHref?: string;
  targetBooth?: string;
}

export const TOUR_STEPS: TourStep[] = [
  {
    id: "booth-47",
    badge: "Outlier Spike",
    title: "Booth 47: 53 Removals (p < 10⁻⁶)",
    description:
      "Statistically anomalous deletion spike. 53 voters removed against 6 expected for this age band. Zero deaths or boundary shifts registered.",
    evidence: "Residual share unexplained: 100%. Confidence: 94% (fit on training cases). Needs human field verification.",
    targetBooth: "B047",
    actionText: "Inspect Booth 47",
  },
  {
    id: "booth-12",
    badge: "Cleared Decoy",
    title: "Booth 12: Cleared Benign Hostel Move-out",
    description:
      "118 electors were removed from Booth 12. Instead of generating a false accusation, RollWatch cross-referenced context registers.",
    evidence: "Matched to College Hostel Graduation register (118/118 verified). Automatically cleared as likely benign.",
    targetBooth: "B012",
    actionText: "Inspect Booth 12",
  },
  {
    id: "claim-court",
    badge: "Claim Court",
    title: "Mirror Fact-Checking with Mathematical Proofs",
    description:
      "Paste any viral political claim (e.g. '50,000 voters illegally deleted'). The engine executes identical mathematical tests on both the claim and its mirror opposite.",
    evidence: "Neutral, procedural verdicts with zero hallucinated figures. Outputs downloadable card image.",
    actionHref: "/check",
    actionText: "Test a Claim",
  },
  {
    id: "citizen-ask",
    badge: "Citizen Assistant",
    title: "Phonetic Multi-Script Name & BLO Search",
    description:
      "Citizens search their status via text or WhatsApp. Translates across 7 Indian languages with procedural BLO guidance and Form 6/7/8 links.",
    evidence: "Official helpline 1950 and anti-scam advisories included in every answer.",
    actionHref: "/ask",
    actionText: "Try Citizen Search",
  },
  {
    id: "provenance-ledger",
    badge: "Trust & Provenance",
    title: "Tamper-Evident SHA-256 Audit Trail",
    description:
      "Every review verdict and flag escalation enters an immutable cryptographically linked hash chain with newsroom exportable CSVs and Markdown.",
    evidence: "Zero party or candidate bias. Fully reproducible using open-source Python scripts.",
    actionHref: "/trust",
    actionText: "View Trust & Error Rates",
  },
];

interface DemoTourProps {
  onSelectBooth?: (boothId: string) => void;
}

export default function DemoTour({ onSelectBooth }: DemoTourProps) {
  const [active, setActive] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (!active) return;
      if (e.key === "Escape") setActive(false);
      if (e.key === "ArrowRight") setCurrentStep((s) => Math.min(s + 1, TOUR_STEPS.length - 1));
      if (e.key === "ArrowLeft") setCurrentStep((s) => Math.max(s - 1, 0));
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [active]);

  const step = TOUR_STEPS[currentStep];

  const handleAction = () => {
    if (step.targetBooth && onSelectBooth) {
      onSelectBooth(step.targetBooth);
    }
  };

  return (
    <>
      {/* Floating Presentation launcher pill */}
      {!active && (
        <div className="fixed bottom-6 right-6 z-40">
          <button
            onClick={() => setActive(true)}
            aria-label="Start interactive presentation tour"
            className="flex items-center gap-2.5 bg-ink text-surface hover:bg-neutral-800 transition-all shadow-xl px-4 py-2.5 rounded-full text-[14px] font-medium border border-line focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal"
          >
            <span className="w-2.5 h-2.5 rounded-full bg-signal animate-pulse" />
            <span>Interactive Demo Tour</span>
            <span className="mono text-[11px] text-ink-3 bg-surface/10 px-1.5 py-0.5 rounded">5 stops</span>
          </button>
        </div>
      )}

      {/* Presentation Tour Modal Panel */}
      {active && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="tour-heading"
          className="fixed bottom-6 right-6 z-50 w-[92vw] max-w-[460px] bg-surface border border-line rounded-[20px] shadow-2xl p-5 animate-in fade-in slide-in-from-bottom-4 duration-200"
        >
          <div className="flex items-center justify-between pb-3 border-b border-line mb-3">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded-[6px] bg-panel mono text-[11px] font-semibold text-ink">
                Stop {currentStep + 1} of {TOUR_STEPS.length}
              </span>
              <span className="px-2 py-0.5 rounded-[6px] bg-signal/20 text-ink mono text-[11px] font-medium">
                {step.badge}
              </span>
            </div>
            <button
              onClick={() => setActive(false)}
              aria-label="Close demo tour"
              className="text-ink-3 hover:text-ink text-[18px] w-7 h-7 flex items-center justify-center rounded-full hover:bg-panel transition-colors"
            >
              ✕
            </button>
          </div>

          <h2 id="tour-heading" className="text-[17px] font-semibold text-ink tracking-tight mb-2">
            {step.title}
          </h2>

          <p className="text-[14px] text-ink-2 leading-relaxed mb-3">{step.description}</p>

          <div className="bg-panel rounded-[10px] p-2.5 mb-4 mono text-[12px] text-ink border border-line">
            <span className="text-ink-3 block text-[10px] uppercase tracking-wider mb-1">Empirical Evidence</span>
            {step.evidence}
          </div>

          <div className="flex items-center justify-between gap-2 pt-2 border-t border-line">
            <div className="flex gap-1">
              <button
                disabled={currentStep === 0}
                onClick={() => setCurrentStep((s) => Math.max(s - 1, 0))}
                className="px-2.5 py-1.5 rounded-[8px] border border-line text-[13px] disabled:opacity-40 disabled:cursor-not-allowed hover:bg-panel transition-colors"
              >
                Previous
              </button>
              <button
                disabled={currentStep === TOUR_STEPS.length - 1}
                onClick={() => setCurrentStep((s) => Math.min(s + 1, TOUR_STEPS.length - 1))}
                className="px-2.5 py-1.5 rounded-[8px] border border-line text-[13px] disabled:opacity-40 disabled:cursor-not-allowed hover:bg-panel transition-colors"
              >
                Next
              </button>
            </div>

            {step.actionHref ? (
              <Link
                href={step.actionHref}
                onClick={() => setActive(false)}
                className="px-3.5 py-1.5 rounded-[8px] bg-ink text-surface hover:bg-neutral-800 text-[13px] font-medium transition-colors"
              >
                {step.actionText} →
              </Link>
            ) : (
              <button
                onClick={handleAction}
                className="px-3.5 py-1.5 rounded-[8px] bg-ink text-surface hover:bg-neutral-800 text-[13px] font-medium transition-colors"
              >
                {step.actionText} →
              </button>
            )}
          </div>
        </div>
      )}
    </>
  );
}
