import { writable } from 'svelte/store';

export const auth = writable({
    isAuthenticated: false,
    isAdmin: false,
    user: null
});
