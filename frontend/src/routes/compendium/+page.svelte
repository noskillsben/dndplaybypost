<script>
    import { onMount } from "svelte";
    import DynamicForm from "$lib/components/DynamicForm.svelte";

    let systems = [];
    let selectedSystem = null;
    let selectedType = null;
    let types = [];
    let entries = [];
    let showCreateForm = false;
    let search = "";
    let loading = false;

    const API_URL = "http://localhost:8000";

    onMount(async () => {
        try {
            const res = await fetch(`${API_URL}/api/schemas/systems`);
            const data = await res.json();
            systems = data.systems;
        } catch (e) {
            console.error("Failed to load systems", e);
        }
    });

    async function selectSystem(system) {
        selectedSystem = system;
        selectedType = null;
        entries = [];
        showCreateForm = false;
        try {
            const res = await fetch(
                `${API_URL}/api/schemas/${encodeURIComponent(system)}/types`,
            );
            const data = await res.json();
            types = data.types;
        } catch (e) {
            console.error("Failed to load types", e);
        }
    }

    async function selectType(type) {
        selectedType = type;
        showCreateForm = false;
        await fetchEntries();
    }

    async function fetchEntries() {
        loading = true;
        try {
            const url = new URL(`${API_URL}/api/compendium/`);
            if (selectedSystem)
                url.searchParams.append("system", selectedSystem);
            if (selectedType)
                url.searchParams.append("entry_type", selectedType);
            if (search) url.searchParams.append("search", search);

            const res = await fetch(url);
            const data = await res.json();
            entries = data.entries;
        } catch (e) {
            console.error("Failed to load entries", e);
        } finally {
            loading = false;
        }
    }

    async function handleCreateSubmit(formData) {
        try {
            const res = await fetch(`${API_URL}/api/compendium/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    system: selectedSystem,
                    entry_type: selectedType,
                    name: formData.name,
                    data: formData,
                    source: "User Homebrew",
                    homebrew: true,
                }),
            });

            if (res.ok) {
                showCreateForm = false;
                await fetchEntries();
            } else {
                const err = await res.json();
                alert(`Error: ${err.detail}`);
            }
        } catch (e) {
            console.error("Failed to create entry", e);
        }
    }

    function toggleCreateForm() {
        showCreateForm = !showCreateForm;
    }
</script>

<div class="container mx-auto p-4 max-w-6xl">
    <header class="mb-8 border-b pb-4 flex justify-between items-center">
        <div>
            <h1 class="text-4xl font-extrabold text-gray-900 tracking-tight">
                Compendium
            </h1>
            <p class="text-gray-500 mt-1">
                Explore and manage game system data
            </p>
        </div>
        {#if selectedSystem && selectedType}
            <button
                on:click={toggleCreateForm}
                class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded shadow transition-colors"
            >
                {showCreateForm ? "Cancel" : "New Entry"}
            </button>
        {/if}
    </header>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
        <!-- Sidebar: System & Type Selection -->
        <div class="space-y-6">
            <section>
                <h2
                    class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3"
                >
                    1. Select System
                </h2>
                <div class="space-y-1">
                    {#each systems as system}
                        <button
                            on:click={() => selectSystem(system)}
                            class="w-full text-left px-3 py-2 rounded-md transition-colors font-medium text-sm"
                            class:bg-blue-100={selectedSystem === system}
                            class:text-blue-700={selectedSystem === system}
                            class:text-gray-600={selectedSystem !== system}
                            class:hover:bg-gray-100={selectedSystem !== system}
                        >
                            {system}
                        </button>
                    {:else}
                        <p class="text-gray-400 text-sm italic">
                            No systems found
                        </p>
                    {/each}
                </div>
            </section>

            {#if selectedSystem}
                <section>
                    <h2
                        class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3"
                    >
                        2. Select Type
                    </h2>
                    <div class="space-y-1">
                        {#each types as type}
                            <button
                                on:click={() => selectType(type)}
                                class="w-full text-left px-3 py-2 rounded-md transition-colors font-medium text-sm capitalize"
                                class:bg-blue-100={selectedType === type}
                                class:text-blue-700={selectedType === type}
                                class:text-gray-600={selectedType !== type}
                                class:hover:bg-gray-100={selectedType !== type}
                            >
                                {type.replace("-", " ")}
                            </button>
                        {:else}
                            <p class="text-gray-400 text-sm italic">
                                No types found
                            </p>
                        {/each}
                    </div>
                </section>
            {/if}
        </div>

        <!-- Main Content: Entry List or Form -->
        <div class="md:col-span-3">
            {#if !selectedSystem}
                <div
                    class="bg-blue-50 border-l-4 border-blue-400 p-8 rounded-r-lg text-center"
                >
                    <svg
                        class="h-12 w-12 text-blue-400 mx-auto mb-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                    </svg>
                    <h3 class="text-lg font-bold text-blue-800">
                        Welcome to the Compendium
                    </h3>
                    <p class="text-blue-600">
                        Please select a game system from the left to begin
                        browsing or creating content.
                    </p>
                </div>
            {:else if !selectedType && !showCreateForm}
                <div
                    class="bg-gray-50 border border-dashed border-gray-300 p-8 rounded-lg text-center"
                >
                    <h3 class="text-lg font-medium text-gray-600">
                        Now select an entry type
                    </h3>
                    <p class="text-gray-400">
                        Choose "item", "spell", etc. to see entries for {selectedSystem}.
                    </p>
                </div>
            {:else if showCreateForm}
                <DynamicForm
                    system={selectedSystem}
                    entryType={selectedType}
                    onSubmit={handleCreateSubmit}
                />
            {:else}
                <div class="space-y-4">
                    <!-- Search UI -->
                    <div class="flex space-x-2">
                        <input
                            type="text"
                            bind:value={search}
                            on:input={() => fetchEntries()}
                            placeholder="Search {selectedType}s..."
                            class="flex-grow shadow-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 sm:text-sm border p-2"
                        />
                    </div>

                    <!-- Entry List -->
                    <div class="grid grid-cols-1 gap-4">
                        {#if loading}
                            <div class="text-center py-12">
                                <div
                                    class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"
                                ></div>
                            </div>
                        {:else}
                            {#each entries as entry}
                                <div
                                    class="bg-white border rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
                                >
                                    <div
                                        class="flex justify-between items-start"
                                    >
                                        <div>
                                            <h4
                                                class="text-lg font-bold text-gray-900"
                                            >
                                                {entry.name}
                                            </h4>
                                            <p
                                                class="text-xs font-mono text-gray-400"
                                            >
                                                {entry.guid}
                                            </p>
                                        </div>
                                        {#if entry.homebrew}
                                            <span
                                                class="bg-purple-100 text-purple-700 text-xs px-2 py-1 rounded-full font-bold"
                                                >Homebrew</span
                                            >
                                        {:else}
                                            <span
                                                class="bg-green-100 text-green-700 text-xs px-2 py-1 rounded-full font-bold"
                                                >Official</span
                                            >
                                        {/if}
                                    </div>
                                    <div
                                        class="mt-3 text-sm text-gray-600 line-clamp-2"
                                    >
                                        {entry.data.description ||
                                            "No description available."}
                                    </div>
                                    <div
                                        class="mt-4 flex space-x-4 text-xs text-gray-400 italic"
                                    >
                                        {#if entry.data.weight}
                                            <span
                                                >Weight: {entry.data.weight} lb</span
                                            >
                                        {/if}
                                        {#if entry.data.damage_dice}
                                            <span
                                                >Damage: {entry.data
                                                    .damage_dice}</span
                                            >
                                        {/if}
                                        <span>Source: {entry.source}</span>
                                    </div>
                                </div>
                            {:else}
                                <div
                                    class="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200"
                                >
                                    <p class="text-gray-500">
                                        No entries found matching your criteria.
                                    </p>
                                    <button
                                        on:click={toggleCreateForm}
                                        class="mt-2 text-blue-600 font-bold hover:underline"
                                    >
                                        Create the first one!
                                    </button>
                                </div>
                            {/each}
                        {/if}
                    </div>
                </div>
            {/if}
        </div>
    </div>
</div>

<style>
    /* Any additional styles */
</style>
