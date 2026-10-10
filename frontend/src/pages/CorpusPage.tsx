/**
 * CorpusPage — upload a document to the local reference corpus.
 * Uses a name input for the corpus entry.
 */

import { useState } from 'react';
import { FileDropzone } from '../components/FileDropzone';
import { Spinner } from '../components/Spinner';
import { useUpload } from '../hooks/useUpload';
import { addToCorpus } from '../api/predict';

export function CorpusPage() {
  const { upload, loading: uploading, error: uploadErr, data: doc, reset } = useUpload();
  const [name, setName] = useState('');
  const [adding, setAdding] = useState(false);
  const [addedMsg, setAddedMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function handleAdd() {
    if (!doc || !name.trim()) return;
    setAdding(true);
    setErr(null);
    setAddedMsg(null);
    try {
      const r = await addToCorpus(doc.document_id, name.trim());
      setAddedMsg(`Added "${r.name}" with ${r.chunks} chunks (id: ${r.corpus_id})`);
      setName('');
      reset();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed');
    } finally {
      setAdding(false);
    }
  }

  return (
    <main className="page page--corpus" data-testid="corpus-page">
      <h1>Manage Reference Corpus</h1>
      <p>
        Upload documents to your local index. The detect endpoint will search across this corpus
        when comparing new documents.
      </p>

      {!doc ? (
        <FileDropzone
          onFile={(f) => {
            upload(f).catch(() => {});
          }}
          disabled={uploading}
        />
      ) : (
        <section>
          <p>
            Uploaded <strong>{doc.filename}</strong> ({doc.chunks} chunks).
          </p>
          <label>
            Corpus name
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. wiki-2025"
              data-testid="corpus-name"
            />
          </label>
          <button
            type="button"
            onClick={handleAdd}
            disabled={adding || !name.trim()}
            data-testid="corpus-add"
          >
            {adding ? 'Adding…' : 'Add to corpus'}
          </button>
          <button type="button" onClick={reset}>
            Cancel
          </button>
        </section>
      )}

      {uploading ? <Spinner label="Uploading" /> : null}
      {adding ? <Spinner label="Adding to corpus" /> : null}
      {uploadErr ? <p className="error">{uploadErr}</p> : null}
      {err ? <p className="error">{err}</p> : null}
      {addedMsg ? (
        <p className="ok" data-testid="corpus-added">
          {addedMsg}
        </p>
      ) : null}
    </main>
  );
}
