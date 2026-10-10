/**
 * DetectPage — 3-step wizard: drop file → pick algorithm → view report.
 */

import { useState } from 'react';
import { FileDropzone } from '../components/FileDropzone';
import { AlgorithmPicker } from '../components/AlgorithmPicker';
import { MatchHighlight } from '../components/MatchHighlight';
import { ScoreCard } from '../components/ScoreCard';
import { Spinner } from '../components/Spinner';
import { useUpload } from '../hooks/useUpload';
import { detect } from '../api/analyses';
import type { Algorithm, DetectResponse } from '../types/api';

export function DetectPage() {
  const { upload, loading: uploading, error: uploadErr, data: doc, reset } = useUpload();
  const [algo, setAlgo] = useState<Algorithm>('jaccard');
  const [report, setReport] = useState<DetectResponse | null>(null);
  const [runErr, setRunErr] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  async function runDetect() {
    if (!doc) return;
    setRunning(true);
    setRunErr(null);
    setReport(null);
    try {
      const r = await detect(doc.document_id, algo, 5, 0.0);
      setReport(r);
    } catch (e) {
      setRunErr(e instanceof Error ? e.message : 'Failed');
    } finally {
      setRunning(false);
    }
  }

  return (
    <main className="page page--detect" data-testid="detect-page">
      <h1>Detect Plagiarism</h1>

      {!doc ? (
        <section>
          <FileDropzone
            onFile={(f) => {
              upload(f).catch(() => {
                /* error captured in hook */
              });
            }}
            disabled={uploading}
          />
          {uploading ? <Spinner label="Uploading" /> : null}
          {uploadErr ? (
            <p role="alert" data-testid="upload-error" className="error">
              {uploadErr}
            </p>
          ) : null}
        </section>
      ) : (
        <section className="detect__config">
          <p>
            <strong>{doc.filename}</strong> — {doc.chunks} chunks, {doc.text_length} chars
          </p>
          <button type="button" onClick={reset} data-testid="reset-button">
            Use a different file
          </button>
          <AlgorithmPicker value={algo} onChange={setAlgo} disabled={running} />
          <button
            type="button"
            onClick={runDetect}
            disabled={running}
            data-testid="run-detect"
          >
            {running ? 'Running…' : `Run ${algo} detection`}
          </button>
          {running ? <Spinner label="Running detection" /> : null}
          {runErr ? (
            <p role="alert" className="error">
              {runErr}
            </p>
          ) : null}
        </section>
      )}

      {report ? (
        <section className="detect__report" data-testid="detect-report">
          <div className="detect__summary">
            <ScoreCard
              score={report.summary.top_similarity}
              label="top similarity"
              caption={`${report.summary.num_matches} matches`}
            />
            <dl>
              <dt>Algorithm</dt>
              <dd>{report.algorithm}</dd>
              <dt>Document</dt>
              <dd>{report.document_id}</dd>
              <dt>Max chunk index</dt>
              <dd>{report.summary.max_chunk_index}</dd>
            </dl>
          </div>

          {report.matches.length === 0 ? (
            <p data-testid="no-matches">No matching passages above threshold.</p>
          ) : (
            <ul className="detect__matches" data-testid="detect-matches">
              {report.matches.map((m, i) => (
                <li key={`${m.chunk_index}-${i}`} className="detect__match">
                  <header>
                    chunk #{m.chunk_index} · source #{m.source_ref} ·{' '}
                    {(m.similarity * 100).toFixed(1)}%
                  </header>
                  <MatchHighlight text={m.snippet} similarity={m.similarity} />
                </li>
              ))}
            </ul>
          )}
        </section>
      ) : null}
    </main>
  );
}
