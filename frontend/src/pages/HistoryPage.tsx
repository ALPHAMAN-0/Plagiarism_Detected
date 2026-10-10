/**
 * HistoryPage — view past analyses stored in localStorage.
 * Entries are pushed by DetectPage/PredictPage when they finish.
 *
 * Storage key: `pd_history_v1` → JSON array of entries.
 */

import { useEffect, useState } from 'react';
import type { Algorithm } from '../types/api';

export interface HistoryEntry {
  id: string;
  kind: 'detect' | 'predict';
  filename: string;
  at: number; // epoch ms
  // detect fields
  algorithm?: Algorithm;
  top_similarity?: number;
  num_matches?: number;
  // predict fields
  label?: string;
  probabilities?: Record<string, number>;
}

const KEY = 'pd_history_v1';

function load(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (x): x is HistoryEntry =>
        x && typeof x === 'object' && typeof x.id === 'string' && typeof x.at === 'number',
    );
  } catch {
    return [];
  }
}

export function HistoryPage() {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);

  useEffect(() => {
    setEntries(load());
  }, []);

  function clearAll() {
    localStorage.removeItem(KEY);
    setEntries([]);
  }

  return (
    <main className="page page--history" data-testid="history-page">
      <h1>History</h1>
      {entries.length === 0 ? (
        <p data-testid="history-empty">No analyses recorded on this device yet.</p>
      ) : (
        <>
          <button type="button" onClick={clearAll} data-testid="history-clear">
            Clear history
          </button>
          <table className="history__table" data-testid="history-table">
            <thead>
              <tr>
                <th>When</th>
                <th>Kind</th>
                <th>File</th>
                <th>Detail</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.id}>
                  <td>{new Date(e.at).toLocaleString()}</td>
                  <td>{e.kind}</td>
                  <td>{e.filename}</td>
                  <td>
                    {e.kind === 'detect' ? (
                      <span>
                        {e.algorithm} · top {(e.top_similarity ?? 0).toFixed(2)} · {e.num_matches} matches
                      </span>
                    ) : (
                      <span>label: {e.label}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </main>
  );
}
