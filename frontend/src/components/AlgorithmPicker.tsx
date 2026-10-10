/**
 * AlgorithmPicker — controlled dropdown listing all 4 supported algorithms.
 */

import type { Algorithm } from '../types/api';

export interface AlgorithmPickerProps {
  value: Algorithm;
  onChange: (next: Algorithm) => void;
  disabled?: boolean;
}

const OPTIONS: { value: Algorithm; description: string }[] = [
  { value: 'jaccard', description: 'N-gram shingling + Jaccard set similarity' },
  { value: 'tfidf', description: 'TF-IDF vectors + cosine similarity' },
  { value: 'embeddings', description: 'sentence-transformers (MiniLM) cosine' },
  { value: 'winnowing', description: 'MOSS-style fingerprinting' },
];

export function AlgorithmPicker({ value, onChange, disabled }: AlgorithmPickerProps) {
  return (
    <label className="algorithm-picker">
      <span className="algorithm-picker__label">Algorithm</span>
      <select
        className="algorithm-picker__select"
        data-testid="algorithm-picker"
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value as Algorithm)}
      >
        {OPTIONS.map((o) => (
          <option key={o.value} value={o.value} title={o.description}>
            {o.value}
          </option>
        ))}
      </select>
    </label>
  );
}
