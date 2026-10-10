import { apiFetch } from './client';
import type { PredictResponse } from '../types/api';

export async function predict(documentId: string): Promise<PredictResponse> {
  return apiFetch<PredictResponse>('/api/v1/predict', {
    method: 'POST',
    body: JSON.stringify({ document_id: documentId }),
  });
}

export async function addToCorpus(
  documentId: string,
  name: string,
): Promise<{ corpus_id: string; name: string; chunks: number }> {
  return apiFetch('/api/v1/corpus', {
    method: 'POST',
    body: JSON.stringify({ document_id: documentId, name }),
  });
}
