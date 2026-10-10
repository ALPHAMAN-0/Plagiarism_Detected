import { apiFetch } from './client';
import type { DocumentUploadResponse } from '../types/api';

export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  const form = new FormData();
  form.append('file', file);
  return apiFetch<DocumentUploadResponse>('/api/v1/documents', {
    method: 'POST',
    body: form,
  });
}
