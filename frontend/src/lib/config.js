// API Configuration
// In development: http://localhost:8000/api
// In production: Set VITE_API_URL to your public API endpoint (including /api)
let url = import.meta.env.VITE_API_URL || '/api';
// Force relative path if pointing to localhost:8000 to ensure we go through Nginx
if (url.includes('localhost:8000')) {
    url = '/api';
}
export const API_URL = url;
