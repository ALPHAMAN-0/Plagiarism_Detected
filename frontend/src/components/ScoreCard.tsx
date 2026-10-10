/**
 * ScoreCard — circular SVG progress ring around a numeric score.
 * Pure SVG, no extra dependencies.
 */

export interface ScoreCardProps {
  /** Score in [0, 1] */
  score: number;
  label: string;
  caption?: string;
}

export function ScoreCard({ score, label, caption }: ScoreCardProps) {
  const clamped = Math.max(0, Math.min(1, score));
  const r = 36;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - clamped);

  return (
    <div className="score-card" data-testid={`score-card-${label}`}>
      <svg
        className="score-card__ring"
        viewBox="0 0 100 100"
        width="100"
        height="100"
        role="img"
        aria-label={`${label} score ${(clamped * 100).toFixed(0)} percent`}
      >
        <circle cx="50" cy="50" r={r} className="score-card__track" />
        <circle
          cx="50"
          cy="50"
          r={r}
          className="score-card__fill"
          strokeDasharray={c}
          strokeDashoffset={offset}
          transform="rotate(-90 50 50)"
        />
      </svg>
      <div className="score-card__center">
        <div className="score-card__pct">{(clamped * 100).toFixed(0)}%</div>
        <div className="score-card__label">{label}</div>
      </div>
      {caption ? <div className="score-card__caption">{caption}</div> : null}
    </div>
  );
}
