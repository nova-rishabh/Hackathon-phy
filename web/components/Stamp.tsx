const MAP: Record<string, [string, string]> = {
  review: ["stamp--review", "Needs human review"],
  benign: ["stamp--benign", "Likely benign"],
  unusual: ["stamp--disputed", "Unusual"],
  mixed: ["stamp--review", "Mixed"],
  verified: ["stamp--verified", "Verified"],
  disputed: ["stamp--disputed", "Disputed"],
  unprovable: ["stamp--unprovable", "Cannot be proven"],
};
export default function Stamp({ kind, label }: { kind: keyof typeof MAP | string; label?: string }) {
  const [c, l] = MAP[kind];
  return <span className={`stamp ${c}`}>{label ?? l}</span>;
}
