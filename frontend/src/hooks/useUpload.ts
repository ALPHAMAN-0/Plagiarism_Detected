/**
 * useUpload — uploads a file via the documents API and returns the result.
 * Exposes loading, error, and result state.
 */

import { useState, useCallback } from 'react';
import { uploadDocument } from '../api/documents';
import type { DocumentUploadResponse } from '../types/api';
import { ApiError } from '../api/client';

export interface UseUploadState {
  loading: boolean;
  error: string | null;
  data: DocumentUploadResponse | null;
}

export function useUpload() {
  const [state, setState] = useState<UseUploadState>({
    loading: false,
    error: null,
    data: null,
  });

  const upload = useCallback(async (file: File) => {
    setState({ loading: true, error: null, data: null });
    try {
      const data = await uploadDocument(file);
      setState({ loading: false, error: null, data });
      return data;
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : e instanceof Error ? e.message : 'Upload failed';
      setState({ loading: false, error: msg, data: null });
      throw e;
    }
  }, []);

  const reset = useCallback(() => setState({ loading: false, error: null, data: null }), []);

  return { ...state, upload, reset };
}
