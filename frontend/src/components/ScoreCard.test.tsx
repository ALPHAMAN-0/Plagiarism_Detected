import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ScoreCard } from './ScoreCard';

describe('ScoreCard', () => {
  it('renders percentage in center', () => {
    render(<ScoreCard score={0.65} label="top" />);
    expect(screen.getByText('65%')).toBeInTheDocument();
    expect(screen.getByText('top')).toBeInTheDocument();
  });

  it('clamps score to [0,1]', () => {
    render(<ScoreCard score={1.5} label="x" />);
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('renders caption when provided', () => {
    render(<ScoreCard score={0.5} label="x" caption="hello" />);
    expect(screen.getByText('hello')).toBeInTheDocument();
  });

  it('has accessible label with percent', () => {
    render(<ScoreCard score={0.42} label="human" />);
    expect(screen.getByLabelText('human score 42 percent')).toBeInTheDocument();
  });
});
