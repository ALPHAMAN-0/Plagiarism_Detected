/**
 * ProbBar — a labelled horizontal bar showing a probability (0..1) with % label.
 * Used for the 3-class prediction output.
 *
 * Security: text values are rendered as text (no dangerouslySetInnerHTML) to
 * guarantee no XSS via backend-supplied label names.
 */

export interface ProbBarProps {
  label: string;
  value: number;
  highlight?: boolean;
}

export function ProbBar({ label, value, highlight = false }: ProbBarProps) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  return (
    <div
      className={`prob-bar${highlight ? ' prob-bar--highlight' : ''}`}
      data-testid={`prob-bar-${label}`}
      role="meter"
      aria-valuenow={Math.round(pct)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`${label} probability`}
    >
      <div className="prob-bar__label">{label}</div>
      <div className="prob-bar__track" aria-hidden="true">
        <div className="prob-bar__fill" style={{ width: `${pct}%` }} />
      </div>
      <div className="prob-bar__value">{pct.toFixed(1)}%</div>
    </div>
  );
}
