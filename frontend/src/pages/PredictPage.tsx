/**
 * PredictPage — drop doc → POST /predict → 3-class probabilities + verdict chip.
 */

import { useState } from 'react';
import { FileDropzone } from '../components/FileDropzone';
import { ProbBar } from '../components/ProbBar';
import { ScoreCard } from '../components/ScoreCard';
import { Spinner } from '../components/Spinner';
import { useUpload } from '../hooks/useUpload';
import { predict } from '../api/predict';
import type { Label, PredictResponse } from '../types/api';

const LABELS: Label[] = ['human', 'ai', 'plagiarised'];

export function PredictPage() {
  const { upload, loading: uploading, error: uploadErr, data: doc, reset } = useUpload();
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [runErr, setRunErr] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  async function runPredict() {
    if (!doc) return;
    setRunning(true);
    setRunErr(null);
    setResult(null);
    try {
      const r = await predict(doc.document_id);
      setResult(r);
    } catch (e) {
      setRunErr(e instanceof Error ? e.message : 'Failed');
    } finally {
      setRunning(false);
    }
  }

  return (
    <main className="page page--predict" data-testid="predict-page">
      <h1>Predict Authenticity</h1>
      {!doc ? (
        <section>
          <FileDropzone
            onFile={(f) => {
              upload(f).catch(() => {});
            }}
            disabled={uploading}
          />
          {uploading ? <Spinner label="Uploading" /> : null}
          {uploadErr ? (
            <p role="alert" className="error">
              {uploadErr}
            </p>
          ) : null}
        </section>
      ) : (
        <section className="predict__config">
          <p>
            <strong>{doc.filename}</strong> — {doc.chunks} chunks
          </p>
          <button type="button" onClick={reset} data-testid="reset-predict">
            Use a different file
          </button>
          <button
            type="button"
            onClick={runPredict}
            disabled={running}
            data-testid="run-predict"
          >
            {running ? 'Running…' : 'Predict'}
          </button>
          {running ? <Spinner label="Predicting" /> : null}
          {runErr ? (
            <p role="alert" className="error">
              {runErr}
            </p>
          ) : null}
        </section>
      )}

      {result ? (
        <section className="predict__result" data-testid="predict-result">
          <div className={`verdict verdict--${result.label}`} data-testid="verdict">
            <ScoreCard
              score={result.probabilities[result.label] ?? 0}
              label={result.label}
              caption={`model ${result.model_version}`}
            />
            <p>
              The classifier judged this document most likely to be{' '}
              <strong>{result.label}</strong>.
            </p>
          </div>
          <div className="predict__probs" data-testid="predict-probs">
            {LABELS.map((l) => (
              <ProbBar
                key={l}
                label={l}
                value={result.probabilities[l] ?? 0}
                highlight={l === result.label}
              />
            ))}
          </div>
          <details className="predict__features">
            <summary>Features</summary>
            <ul>
              {Object.entries(result.features).map(([k, v]) => (
                <li key={k}>
                  {k}: {Number(v).toFixed(4)}
                </li>
              ))}
            </ul>
          </details>
        </section>
      ) : null}
    </main>
  );
}
