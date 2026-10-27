const MAP: Record<string, [string, string]> = {
  review: ["chip--review", "Needs human review"],
  unusual: ["chip--unusual", "Unusual · needs human review"],
  likely_benign: ["chip--benign", "Likely benign"],
  benign: ["chip--benign", "Likely benign"],
  mixed: ["hatch-chip", "Mixed · needs human review"],
  verified: ["chip--verified", "Verified"],
  disputed: ["chip--disputed", "Disputed"],
  unprovable: ["chip--unprovable", "Cannot be proven"],
};

export default function Chip({ kind, label, big }: { kind: string; label?: string; big?: boolean }) {
  const [c, l] = MAP[kind] ?? ["chip--unprovable", kind];
  const style = big ? { height: 40, padding: "0 16px", fontSize: 18, borderRadius: 8 } : undefined;
  if (c === "hatch-chip")
    return (
      <span className="chip chip--review" style={style}>
        <i className="hatch" style={{ width: 10, height: 10, borderRadius: 2, display: "inline-block" }} />{label ?? l}
      </span>
    );
  return <span className={`chip ${c}`} style={style}>{label ?? l}</span>;
}
