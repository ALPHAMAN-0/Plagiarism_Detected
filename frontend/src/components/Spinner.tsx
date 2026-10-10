/**
 * Spinner — minimal accessible loading indicator.
 */

export interface SpinnerProps {
  label?: string;
}

export function Spinner({ label = 'Loading' }: SpinnerProps) {
  return (
    <div className="spinner" role="status" aria-live="polite" data-testid="spinner">
      <span className="spinner__dot" />
      <span className="spinner__dot" />
      <span className="spinner__dot" />
      <span className="spinner__sr">{label}…</span>
    </div>
  );
}
