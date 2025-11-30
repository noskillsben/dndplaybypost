import { writable } from 'svelte/store';
import { browser } from '$app/environment';

const initialState = {
    isAuthenticated: false,
    isAdmin: false,
    user: null
};

// Initialize from localStorage if available
const storedAuth = browser ? localStorage.getItem('auth_state') : null;
const initial = storedAuth ? JSON.parse(storedAuth) : initialState;

export const auth = writable(initial);

// Subscribe to changes and update localStorage
if (browser) {
    auth.subscribe(value => {
        localStorage.setItem('auth_state', JSON.stringify(value));
    });
}
