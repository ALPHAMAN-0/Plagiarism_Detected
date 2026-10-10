/**
 * MatchHighlight — renders a chunk of text with optional <mark> highlights
 * keyed by similarity score.
 *
 * Security: every chunk's `text` is rendered as text, NEVER as HTML.
 * The backend already escapes HTML in `snippet`, but we defensively render
 * with React text nodes (no dangerouslySetInnerHTML) to guarantee safety
 * even if the contract ever breaks.
 */

import type { ReactNode } from 'react';

export interface MatchHighlightProps {
  text: string;
  /** Optional similarity in [0,1] — controls mark intensity. */
  similarity?: number;
}

function intensity(similarity: number | undefined): string {
  if (similarity === undefined) return 'low';
  if (similarity >= 0.8) return 'high';
  if (similarity >= 0.5) return 'medium';
  return 'low';
}

export function MatchHighlight({ text, similarity }: MatchHighlightProps): ReactNode {
  const lvl = intensity(similarity);
  return (
    <span
      className={`match match--${lvl}`}
      data-testid="match-highlight"
      data-similarity={similarity ?? 0}
    >
      {text}
    </span>
  );
}
