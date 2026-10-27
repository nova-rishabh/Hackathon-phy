export default function Glyph({ id, size = 20 }: { id: string; size?: number }) {
  return <svg width={size} height={size} aria-hidden="true"><use href={`/glyphs.svg#${id}`} /></svg>;
}
