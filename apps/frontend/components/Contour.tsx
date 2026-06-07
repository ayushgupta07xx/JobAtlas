// Faint topographic contour motif — the "Atlas" signature. Pure SVG (no image),
// deterministic (no Math.random) so server and client render identically.
// Decorative only: aria-hidden + pointer-events-none at the call site.

function ringPath(cx: number, cy: number, r: number, seed: number): string {
  const steps = 72;
  const pts: string[] = [];
  for (let i = 0; i <= steps; i++) {
    const t = (i / steps) * Math.PI * 2;
    const wobble =
      Math.sin(t * 3 + seed) * (r * 0.06) +
      Math.sin(t * 5 + seed * 1.7) * (r * 0.03);
    const rr = r + wobble;
    const x = cx + Math.cos(t) * rr;
    const y = cy + Math.sin(t) * rr * 0.86; // slight vertical squash
    pts.push(`${x.toFixed(1)},${y.toFixed(1)}`);
  }
  return `M${pts.join(" L")} Z`;
}

export function Contour({ className = "" }: { className?: string }) {
  const cx = 300;
  const cy = 300;
  const rings = Array.from({ length: 8 }, (_, i) => 70 + i * 30);

  return (
    <svg
      viewBox="0 0 600 600"
      fill="none"
      aria-hidden="true"
      className={className}
    >
      {rings.map((r, i) => (
        <path
          key={r}
          d={ringPath(cx, cy, r, i * 1.3)}
          stroke={i < 2 ? "var(--accent)" : "var(--ink)"}
          strokeWidth={1}
          strokeOpacity={i < 2 ? 0.22 : 0.1}
        />
      ))}
    </svg>
  );
}
