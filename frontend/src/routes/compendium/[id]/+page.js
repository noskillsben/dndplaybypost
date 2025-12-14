import { error } from '@sveltejs/kit';
import { getCompendiumItem } from '$lib/api/compendium';

export async function load({ params }) {
    try {
        const item = await getCompendiumItem(params.id);
        return { item };
    } catch (err) {
        console.error('Load error:', err);
        return { error: `Item not found: ${err.message}`, stack: err.stack };
    }
}
