import { apiFetch } from './client';
import type { Algorithm, DetectResponse } from '../types/api';

export async function detect(
  documentId: string,
  algorithm: Algorithm,
  topK = 5,
  threshold = 0.0,
): Promise<DetectResponse> {
  return apiFetch<DetectResponse>('/api/v1/analyses/detect', {
    method: 'POST',
    body: JSON.stringify({
      document_id: documentId,
      algorithm,
      top_k: topK,
      threshold,
    }),
  });
}
