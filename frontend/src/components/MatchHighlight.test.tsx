import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MatchHighlight } from './MatchHighlight';

describe('MatchHighlight', () => {
  it('renders text verbatim (no HTML interpretation)', () => {
    const xss = '<img src=x onerror=alert(1)><script>alert(2)</script>';
    render(<MatchHighlight text={xss} similarity={0.9} />);
    const el = screen.getByTestId('match-highlight');
    // Text content should equal the raw input, not executed/parsed
    expect(el.textContent).toBe(xss);
    expect(el.querySelector('img')).toBeNull();
    expect(el.querySelector('script')).toBeNull();
  });

  it('applies high class for similarity >= 0.8', () => {
    render(<MatchHighlight text="x" similarity={0.9} />);
    expect(screen.getByTestId('match-highlight').className).toContain('match--high');
  });

  it('applies medium class for similarity 0.5..0.8', () => {
    render(<MatchHighlight text="x" similarity={0.6} />);
    expect(screen.getByTestId('match-highlight').className).toContain('match--medium');
  });

  it('applies low class for similarity < 0.5 or undefined', () => {
    const { rerender } = render(<MatchHighlight text="x" similarity={0.1} />);
    expect(screen.getByTestId('match-highlight').className).toContain('match--low');
    rerender(<MatchHighlight text="y" />);
    expect(screen.getByTestId('match-highlight').className).toContain('match--low');
  });
});
