<script>
    import { page } from "$app/stores";
    import { onMount } from "svelte";
    import { api } from "$lib/api";
    import { goto } from "$app/navigation";

    let campaigns = [];
    let selectedCampaignId = "";
    let name = "";
    let avatarUrl = "";
    let sheetData = "{}";
    let notes = "";
    let error = "";

    onMount(async () => {
        try {
            campaigns = await api.get("/campaigns");
            const queryCampaignId = $page.url.searchParams.get("campaign");
            if (queryCampaignId) {
                selectedCampaignId = queryCampaignId;
            } else if (campaigns.length > 0) {
                selectedCampaignId = campaigns[0].id;
            }
        } catch (e) {
            error = e.message;
        }
    });

    async function handleSubmit() {
        error = "";
        try {
            let parsedSheetData = {};
            try {
                parsedSheetData = JSON.parse(sheetData);
            } catch (e) {
                throw new Error("Sheet Data must be valid JSON");
            }

            if (!selectedCampaignId) {
                throw new Error("Please select a campaign");
            }

            const character = await api.post("/characters", {
                campaign_id: selectedCampaignId,
                name,
                avatar_url: avatarUrl || null,
                sheet_data: parsedSheetData,
                notes: notes || null,
            });

            goto(`/characters/${character.id}`);
        } catch (e) {
            error = e.message;
        }
    }
</script>

<div class="max-w-2xl mx-auto mt-10 bg-gray-800 p-6 rounded-lg shadow-lg">
    <h2 class="text-2xl font-bold mb-6 text-purple-400">
        Create New Character
    </h2>

    {#if error}
        <div class="bg-red-900 text-red-200 p-3 rounded mb-4">{error}</div>
    {/if}

    <form on:submit|preventDefault={handleSubmit} class="space-y-6">
        <div>
            <label for="campaign" class="block text-gray-400 mb-1"
                >Campaign</label
            >
            <select
                id="campaign"
                bind:value={selectedCampaignId}
                class="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                required
            >
                <option value="" disabled>Select a campaign</option>
                {#each campaigns as campaign}
                    <option value={campaign.id}>{campaign.name}</option>
                {/each}
            </select>
        </div>

        <div>
            <label for="name" class="block text-gray-400 mb-1"
                >Character Name</label
            >
            <input
                id="name"
                type="text"
                bind:value={name}
                class="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                required
            />
        </div>

        <div>
            <label for="avatarUrl" class="block text-gray-400 mb-1"
                >Avatar URL (Optional)</label
            >
            <input
                id="avatarUrl"
                type="url"
                bind:value={avatarUrl}
                class="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
        </div>

        <div>
            <label for="sheetData" class="block text-gray-400 mb-1"
                >Sheet Data (JSON)</label
            >
            <textarea
                id="sheetData"
                bind:value={sheetData}
                class="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono h-32"
            />
        </div>

        <div>
            <label for="notes" class="block text-gray-400 mb-1"
                >Notes (Optional)</label
            >
            <textarea
                id="notes"
                bind:value={notes}
                class="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-purple-500 h-24"
            />
        </div>

        <div class="flex justify-end space-x-4">
            <a
                href="/characters"
                class="bg-gray-600 hover:bg-gray-500 text-white font-bold py-2 px-4 rounded transition duration-200"
            >
                Cancel
            </a>
            <button
                type="submit"
                class="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded transition duration-200"
            >
                Create Character
            </button>
        </div>
    </form>
</div>
