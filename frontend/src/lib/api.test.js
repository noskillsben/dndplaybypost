import { describe, it, expect, vi, afterEach } from 'vitest';
import { api, apiFetch, buildUrl, ApiError, API_URL } from './api.js';

function mockFetch(status, jsonBody) {
    return vi.fn(async () => ({
        ok: status >= 200 && status < 300,
        status,
        json: async () => {
            if (jsonBody === undefined) throw new Error('no body');
            return jsonBody;
        }
    }));
}

afterEach(() => {
    vi.unstubAllGlobals();
});

describe('buildUrl', () => {
    it('joins path onto the base URL', () => {
        expect(buildUrl('/api/compendium/')).toBe(`${API_URL}/api/compendium/`);
    });

    it('appends non-empty params only', () => {
        const url = buildUrl('/api/compendium/', { system: 'd&d5.0', search: '', skip: null });
        expect(url).toContain('system=d%26d5.0');
        expect(url).not.toContain('search');
        expect(url).not.toContain('skip');
    });
});

describe('apiFetch', () => {
    it('returns parsed JSON on success', async () => {
        vi.stubGlobal('fetch', mockFetch(200, { hello: 'world' }));
        const data = await api.get('/thing');
        expect(data).toEqual({ hello: 'world' });
    });

    it('sends JSON body with content-type header', async () => {
        const fetchMock = mockFetch(201, { ok: true });
        vi.stubGlobal('fetch', fetchMock);
        await api.post('/thing', { name: 'Sword' });
        const [, options] = fetchMock.mock.calls[0];
        expect(options.method).toBe('POST');
        expect(options.headers['Content-Type']).toBe('application/json');
        expect(JSON.parse(options.body)).toEqual({ name: 'Sword' });
    });

    it('returns null for 204 responses', async () => {
        vi.stubGlobal('fetch', mockFetch(204, undefined));
        expect(await api.delete('/thing/1')).toBeNull();
    });

    it('throws ApiError with detail message from FastAPI errors', async () => {
        vi.stubGlobal('fetch', mockFetch(404, { detail: 'Entry not found' }));
        await expect(api.get('/thing/x')).rejects.toThrowError(ApiError);
        await expect(api.get('/thing/x')).rejects.toThrow('Entry not found');
    });

    it('throws ApiError with envelope message and details', async () => {
        vi.stubGlobal(
            'fetch',
            mockFetch(400, {
                error: { code: 'validation_error', message: 'Validation failed', details: [{ field: 'name' }] }
            })
        );
        try {
            await apiFetch('/thing', { method: 'POST', body: {} });
            expect.unreachable();
        } catch (e) {
            expect(e).toBeInstanceOf(ApiError);
            expect(e.status).toBe(400);
            expect(e.message).toBe('Validation failed');
            expect(e.details).toEqual([{ field: 'name' }]);
        }
    });

    it('falls back to a generic message when the body is not JSON', async () => {
        vi.stubGlobal('fetch', mockFetch(500, undefined));
        await expect(api.get('/boom')).rejects.toThrow('Request failed with status 500');
    });
});
