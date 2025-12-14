<script>
    import { api } from "$lib/api";
    import { goto } from "$app/navigation";
    import SystemSelector from "$lib/components/SystemSelector.svelte";

    let name = "";
    let description = "";
    let system = "D&D 5e";
    let settings = "{}";
    let error = "";

    async function handleSubmit() {
        error = "";
        try {
            let parsedSettings = {};
            try {
                parsedSettings = JSON.parse(settings);
            } catch (e) {
                throw new Error("Settings must be valid JSON");
            }

            const campaign = await api.post("/campaigns", {
                name,
                description,
                settings: {
                    ...parsedSettings,
                    system: system,
                },
            });

            goto(`/campaigns/${campaign.id}`);
        } catch (e) {
            error = e.message;
        }
    }
</script>

<div class="max-w-2xl mx-auto mt-10 bg-gray-800 p-6 rounded-lg shadow-lg">
    <h2 class="text-2xl font-bold mb-6 text-purple-400">Create New Campaign</h2>

    {#if error}
        <div class="bg-red-900 text-red-200 p-3 rounded mb-4">{error}</div>
    {/if}

    <form on:submit|preventDefault={handleSubmit} class="space-y-6">
        <div>
            <label for="name" class="block text-gray-400 mb-1"
                >Campaign Name</label
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
            <label for="description" class="block text-gray-400 mb-1"
                >Description</label
            >
            <textarea
                id="description"
                bind:value={description}
                class="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-purple-500 h-32"
            />
        </div>

        <div>
            <SystemSelector bind:selectedSystem={system} />
        </div>

        <div>
            <label for="settings" class="block text-gray-400 mb-1"
                >Settings (JSON)</label
            >
            <textarea
                id="settings"
                bind:value={settings}
                class="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono h-32"
            />
            <p class="text-xs text-gray-500 mt-1">
                Enter valid JSON configuration for your campaign.
            </p>
        </div>

        <div class="flex justify-end space-x-4">
            <a
                href="/campaigns"
                class="bg-gray-600 hover:bg-gray-500 text-white font-bold py-2 px-4 rounded transition duration-200"
            >
                Cancel
            </a>
            <button
                type="submit"
                class="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded transition duration-200"
            >
                Create Campaign
            </button>
        </div>
    </form>
</div>
