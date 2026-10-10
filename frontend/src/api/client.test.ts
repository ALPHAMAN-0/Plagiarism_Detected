import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' },
  });
}

describe('apiFetch', () => {
  beforeEach(() => {
    (import.meta.env as { VITE_API_BASE_URL?: string }).VITE_API_BASE_URL = 'http://api.test';
    vi.resetModules();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns parsed JSON on 2xx and sets Accept header', async () => {
    const { apiFetch } = await import('./client');
    const body = { ok: true, value: 42 };
    const fetchSpy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(jsonResponse(body));
    const data = await apiFetch<typeof body>('/ping');
    expect(data).toEqual(body);
    expect(fetchSpy).toHaveBeenCalledWith(
      'http://api.test/ping',
      expect.objectContaining({
        headers: expect.objectContaining({ Accept: 'application/json' }),
      }),
    );
  });

  it('sets Content-Type for string JSON bodies, not for FormData', async () => {
    const { apiFetch } = await import('./client');
    const fetchSpy = vi
      .spyOn(globalThis, 'fetch')
      .mockImplementation(async () => jsonResponse({}));
    await apiFetch('/x', { method: 'POST', body: JSON.stringify({ a: 1 }) });
    const h0 = (fetchSpy.mock.calls[0]?.[1]?.headers ?? {}) as Record<string, string>;
    expect(h0['Content-Type']).toBe('application/json');

    const fd = new FormData();
    await apiFetch('/x', { method: 'POST', body: fd });
    const h1 = (fetchSpy.mock.calls[1]?.[1]?.headers ?? {}) as Record<string, string>;
    expect(h1['Content-Type']).toBeUndefined();
  });

  it('throws ApiError with detail message on non-2xx JSON', async () => {
    const { apiFetch } = await import('./client');
    vi.spyOn(globalThis, 'fetch').mockImplementation(async () =>
      jsonResponse({ detail: 'nope' }, 400),
    );
    await expect(apiFetch('/bad')).rejects.toMatchObject({ status: 400, message: 'nope' });
  });

  it('falls back to a useful message when body is empty and statusText is missing', async () => {
    const { apiFetch, ApiError } = await import('./client');
    vi.spyOn(globalThis, 'fetch').mockImplementation(
      async () => new Response(null, { status: 500, statusText: '' }),
    );
    let caught: unknown;
    try {
      await apiFetch('/boom');
    } catch (e) {
      caught = e;
    }
    expect(caught).toBeInstanceOf(ApiError);
    const err = caught as InstanceType<typeof ApiError>;
    expect(err.status).toBe(500);
    expect(err.message).toMatch(/500/);
  });

  it('preserves raw text when body is non-JSON', async () => {
    const { apiFetch, ApiError } = await import('./client');
    vi.spyOn(globalThis, 'fetch').mockImplementation(
      async () => new Response('plain text error', { status: 502 }),
    );
    let caught: unknown;
    try {
      await apiFetch('/html');
    } catch (e) {
      caught = e;
    }
    expect(caught).toBeInstanceOf(ApiError);
    const err = caught as InstanceType<typeof ApiError>;
    expect(err.status).toBe(502);
    expect(err.body).toBe('plain text error');
  });
});
