// Central API client. Base URL comes from the environment (VITE_API_URL),
// never hardcode http://localhost:8000 in components.

export const API_URL =
    (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_URL) ||
    'http://localhost:8000';

export class ApiError extends Error {
    constructor(status, message, details = null) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.details = details;
    }
}

export function buildUrl(path, params = null) {
    const url = new URL(path, API_URL);
    if (params) {
        for (const [key, value] of Object.entries(params)) {
            if (value !== null && value !== undefined && value !== '') {
                url.searchParams.append(key, value);
            }
        }
    }
    return url.toString();
}

function extractError(status, payload) {
    if (payload && typeof payload === 'object') {
        // F-06 error envelope: { error: { code, message, details } }
        if (payload.error && typeof payload.error === 'object') {
            return new ApiError(
                status,
                payload.error.message || 'Request failed',
                payload.error.details || null
            );
        }
        // FastAPI default: { detail: "..." } or { detail: [...] }
        if (payload.detail) {
            const message =
                typeof payload.detail === 'string'
                    ? payload.detail
                    : 'Validation error';
            return new ApiError(status, message, payload.detail);
        }
    }
    return new ApiError(status, `Request failed with status ${status}`);
}

export async function apiFetch(path, { method = 'GET', params = null, body = undefined } = {}) {
    const options = { method, headers: {} };
    if (body !== undefined) {
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(body);
    }

    const res = await fetch(buildUrl(path, params), options);

    if (res.status === 204) return null;

    let payload = null;
    try {
        payload = await res.json();
    } catch {
        payload = null;
    }

    if (!res.ok) {
        throw extractError(res.status, payload);
    }
    return payload;
}

export const api = {
    get: (path, params) => apiFetch(path, { params }),
    post: (path, body, params) => apiFetch(path, { method: 'POST', body, params }),
    put: (path, body) => apiFetch(path, { method: 'PUT', body }),
    patch: (path, body) => apiFetch(path, { method: 'PATCH', body }),
    delete: (path) => apiFetch(path, { method: 'DELETE' })
};
