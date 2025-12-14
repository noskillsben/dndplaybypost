/**
 * API client for compendium endpoints
 */

import { API_URL } from '$lib/config';

/**
 * Get compendium statistics
 */
export async function getCompendiumStats() {
    const response = await fetch(`${API_URL}/v1/compendium/stats`);
    if (!response.ok) {
        throw new Error('Failed to fetch compendium stats');
    }
    return response.json();
}

/**
 * Search compendium items with filters
 */
export async function searchCompendiumItems(params = {}) {
    const queryParams = new URLSearchParams();

    if (params.query) queryParams.append('query', params.query);
    if (params.type) queryParams.append('type', params.type);
    if (params.is_official !== undefined) queryParams.append('is_official', params.is_official);
    if (params.page) queryParams.append('page', params.page);
    if (params.page_size) queryParams.append('page_size', params.page_size);
    if (params.sort_by) queryParams.append('sort_by', params.sort_by);
    if (params.sort_order) queryParams.append('sort_order', params.sort_order);

    const response = await fetch(`${API_URL}/v1/compendium/items?${queryParams}`);
    if (!response.ok) {
        throw new Error('Failed to search compendium items');
    }
    return response.json();
}

/**
 * Get items by type
 */
export async function getItemsByType(type) {
    const response = await fetch(`${API_URL}/v1/compendium/items/type/${type}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch ${type} items`);
    }
    return response.json();
}

/**
 * Get a single compendium item by ID
 */
export async function getCompendiumItem(id) {
    const url = `${API_URL}/v1/compendium/items/${id}`;
    console.log('Fetching item from:', url);
    const response = await fetch(url);
    if (!response.ok) {
        console.error('Fetch failed:', response.status, response.statusText);
        throw new Error(`Failed to fetch compendium item from ${url}: ${response.status} ${response.statusText}`);
    }
    return response.json();
}

/**
 * Get all component templates
 */
export async function getComponentTemplates() {
    const response = await fetch(`${API_URL}/v1/compendium/templates`);
    if (!response.ok) {
        throw new Error('Failed to fetch component templates');
    }
    return response.json();
}
