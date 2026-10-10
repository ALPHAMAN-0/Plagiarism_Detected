import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useUpload } from './useUpload';

vi.mock('../api/documents', () => ({
  uploadDocument: vi.fn(),
}));

import { uploadDocument } from '../api/documents';
import { ApiError } from '../api/client';

const mockedUpload = vi.mocked(uploadDocument);

function fakeFile(): File {
  return new File(['hello'], 'a.txt', { type: 'text/plain' });
}

describe('useUpload', () => {
  beforeEach(() => {
    mockedUpload.mockReset();
  });

  it('starts idle', () => {
    const { result } = renderHook(() => useUpload());
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.data).toBeNull();
  });

  it('sets data on success', async () => {
    const fake = {
      document_id: 'd1',
      filename: 'a.txt',
      sha256: 'abc',
      size: 5,
      text_length: 5,
      chunks: 1,
    };
    mockedUpload.mockResolvedValue(fake);
    const { result } = renderHook(() => useUpload());
    await act(async () => {
      await result.current.upload(fakeFile());
    });
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.data).toEqual(fake);
  });

  it('captures error message on failure', async () => {
    mockedUpload.mockRejectedValue(new ApiError(413, 'too big', null));
    const { result } = renderHook(() => useUpload());
    await act(async () => {
      try {
        await result.current.upload(fakeFile());
      } catch {
        // expected
      }
    });
    expect(result.current.error).toBe('too big');
    expect(result.current.data).toBeNull();
  });

  it('resets state', async () => {
    mockedUpload.mockResolvedValue({
      document_id: 'd1',
      filename: 'a.txt',
      sha256: 'abc',
      size: 5,
      text_length: 5,
      chunks: 1,
    });
    const { result } = renderHook(() => useUpload());
    await act(async () => {
      await result.current.upload(fakeFile());
    });
    act(() => result.current.reset());
    expect(result.current.data).toBeNull();
  });
});
