import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AlgorithmPicker } from './AlgorithmPicker';

describe('AlgorithmPicker', () => {
  it('renders all 4 algorithms as options', () => {
    render(<AlgorithmPicker value="jaccard" onChange={() => {}} />);
    const select = screen.getByTestId('algorithm-picker') as HTMLSelectElement;
    const values = Array.from(select.options).map((o) => o.value);
    expect(values).toEqual(['jaccard', 'tfidf', 'embeddings', 'winnowing']);
  });

  it('calls onChange with the new value', async () => {
    const onChange = vi.fn();
    render(<AlgorithmPicker value="jaccard" onChange={onChange} />);
    await userEvent.selectOptions(screen.getByTestId('algorithm-picker'), 'tfidf');
    expect(onChange).toHaveBeenCalledWith('tfidf');
  });

  it('respects disabled prop', () => {
    render(<AlgorithmPicker value="jaccard" onChange={() => {}} disabled />);
    expect(screen.getByTestId('algorithm-picker')).toBeDisabled();
  });
});
