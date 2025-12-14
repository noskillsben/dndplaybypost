import { browser } from '$app/environment';

// API Configuration
let url;

if (browser) {
    // Client-side: use relative path or public URL
    url = import.meta.env.VITE_API_URL || '/api';
    // Force relative path if pointing to localhost:8000 to ensure we go through Nginx
    if (url.includes('localhost:8000')) {
        url = '/api';
    }
} else {
    // Server-side (SSR): use internal Docker URL
    // This allows the frontend container to talk directly to the backend container
    url = 'http://backend:8000/api';
}

export const API_URL = url;
