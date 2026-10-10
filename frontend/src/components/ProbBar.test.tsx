import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProbBar } from './ProbBar';

describe('ProbBar', () => {
  it('renders label and percentage', () => {
    render(<ProbBar label="human" value={0.732} />);
    expect(screen.getByText('human')).toBeInTheDocument();
    expect(screen.getByText('73.2%')).toBeInTheDocument();
  });

  it('clamps values to [0,1]', () => {
    render(<ProbBar label="ai" value={2.0} />);
    expect(screen.getByText('100.0%')).toBeInTheDocument();
    render(<ProbBar label="ai" value={-0.5} />);
    expect(screen.getAllByText('0.0%')[0]).toBeInTheDocument();
  });

  it('applies highlight class when highlight=true', () => {
    render(<ProbBar label="plagiarised" value={0.5} highlight />);
    const el = screen.getByTestId('prob-bar-plagiarised');
    expect(el.className).toContain('prob-bar--highlight');
  });

  it('sets aria-valuenow to clamped percentage', () => {
    render(<ProbBar label="human" value={0.4567} />);
    const meter = screen.getByRole('meter');
    expect(meter).toHaveAttribute('aria-valuenow', '46');
    expect(meter).toHaveAttribute('aria-valuemin', '0');
    expect(meter).toHaveAttribute('aria-valuemax', '100');
  });
});
