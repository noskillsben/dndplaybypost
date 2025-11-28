<script>
    import { onMount } from "svelte";
    import { api } from "$lib/api";

    let campaigns = [];
    let error = "";

    onMount(async () => {
        try {
            campaigns = await api.get("/campaigns");
        } catch (e) {
            error = e.message;
        }
    });
</script>

<div class="container mx-auto p-4">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-bold text-purple-400">My Campaigns</h1>
        <a
            href="/campaigns/new"
            class="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded transition duration-200"
        >
            Create Campaign
        </a>
    </div>

    {#if error}
        <div class="bg-red-900 text-red-200 p-3 rounded mb-4">{error}</div>
    {/if}

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {#each campaigns as campaign}
            <a
                href="/campaigns/{campaign.id}"
                class="block bg-gray-800 p-6 rounded-lg shadow-lg hover:bg-gray-750 transition duration-200 border border-gray-700 hover:border-purple-500"
            >
                <h2 class="text-xl font-bold mb-2 text-white">
                    {campaign.name}
                </h2>
                <p class="text-gray-400 mb-4 line-clamp-2">
                    {campaign.description || "No description"}
                </p>
                <div class="text-sm text-gray-500">
                    Created: {new Date(
                        campaign.created_at
                    ).toLocaleDateString()}
                </div>
            </a>
        {/each}
    </div>

    {#if campaigns.length === 0 && !error}
        <p class="text-gray-400 text-center mt-10">
            You are not a member of any campaigns yet.
        </p>
    {/if}
</div>
