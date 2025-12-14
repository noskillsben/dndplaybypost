<script>
    import { onMount } from "svelte";
    import {
        getCompendiumStats,
        searchCompendiumItems,
    } from "$lib/api/compendium";
    import CompendiumCard from "$lib/components/CompendiumCard.svelte";
    import SearchBar from "$lib/components/SearchBar.svelte";
    import SystemSelector from "$lib/components/SystemSelector.svelte";

    let stats = null;
    let items = [];
    let loading = true;
    let error = null;
    let selectedType = "all";
    let selectedSystem = "D&D 5.2 (2024)";
    let searchQuery = "";
    let currentPage = 1;
    let totalItems = 0;
    let hasMore = false;

    const itemTypes = [
        { value: "all", label: "All Items", icon: "📚" },
        { value: "class", label: "Classes", icon: "⚔️" },
        { value: "race", label: "Races", icon: "👤" },
        { value: "spell", label: "Spells", icon: "✨" },
        { value: "item", label: "Items", icon: "🎒" },
        { value: "background", label: "Backgrounds", icon: "📜" },
        { value: "feature", label: "Features", icon: "🌟" },
    ];

    onMount(async () => {
        await loadStats();
        await loadItems();
    });

    async function loadStats() {
        try {
            stats = await getCompendiumStats();
        } catch (err) {
            console.error("Failed to load stats:", err);
        }
    }

    async function loadItems() {
        loading = true;
        error = null;

        try {
            const params = {
                page: currentPage,
                page_size: 20,
            };

            if (selectedType !== "all") {
                params.type = selectedType;
            }

            if (selectedSystem) {
                params.system = selectedSystem;
            }

            if (searchQuery) {
                params.query = searchQuery;
            }

            const result = await searchCompendiumItems(params);
            items = result.items;
            totalItems = result.total;
            hasMore = result.has_more;
        } catch (err) {
            error = err.message;
            console.error("Failed to load items:", err);
        } finally {
            loading = false;
        }
    }

    function handleTypeChange(type) {
        selectedType = type;
        currentPage = 1;
        loadItems();
    }

    function handleSystemChange(event) {
        selectedSystem = event.detail;
        currentPage = 1;
        loadItems();
    }

    function handleSearch(query) {
        searchQuery = query;
        currentPage = 1;
        loadItems();
    }

    function nextPage() {
        if (hasMore) {
            currentPage++;
            loadItems();
        }
    }

    function prevPage() {
        if (currentPage > 1) {
            currentPage--;
            loadItems();
        }
    }
</script>

<svelte:head>
    <title>Compendium - D&D Play-by-Post</title>
</svelte:head>

<div class="container mx-auto px-4 py-8">
    <!-- Header -->
    <div class="mb-8">
        <h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            📚 Compendium
        </h1>
        <p class="text-gray-600 dark:text-gray-400">
            Browse D&D 5e content - classes, races, spells, items, and more
        </p>
    </div>

    <!-- Stats Overview -->
    {#if stats}
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                <div
                    class="text-2xl font-bold text-blue-600 dark:text-blue-400"
                >
                    {stats.total_items}
                </div>
                <div class="text-sm text-gray-600 dark:text-gray-400">
                    Total Items
                </div>
            </div>
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                <div
                    class="text-2xl font-bold text-green-600 dark:text-green-400"
                >
                    {stats.official_count}
                </div>
                <div class="text-sm text-gray-600 dark:text-gray-400">
                    Official SRD
                </div>
            </div>
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                <div
                    class="text-2xl font-bold text-purple-600 dark:text-purple-400"
                >
                    {stats.homebrew_count}
                </div>
                <div class="text-sm text-gray-600 dark:text-gray-400">
                    Homebrew
                </div>
            </div>
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                <div
                    class="text-2xl font-bold text-orange-600 dark:text-orange-400"
                >
                    {Object.keys(stats.by_type).length}
                </div>
                <div class="text-sm text-gray-600 dark:text-gray-400">
                    Categories
                </div>
            </div>
        </div>
    {/if}

    <!-- System Selector -->
    <div class="mb-6">
        <SystemSelector bind:selectedSystem on:change={handleSystemChange} />
    </div>

    <!-- Search and Filters -->
    <div class="mb-6">
        <SearchBar
            on:search={(e) => handleSearch(e.detail)}
            placeholder="Search compendium..."
        />
    </div>

    <!-- Type Filters -->
    <div class="flex flex-wrap gap-2 mb-6">
        {#each itemTypes as type}
            <button
                on:click={() => handleTypeChange(type.value)}
                class="px-4 py-2 rounded-lg font-medium transition-colors {selectedType ===
                type.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'}"
            >
                <span class="mr-2">{type.icon}</span>
                {type.label}
                {#if stats && stats.by_type[type.value]}
                    <span class="ml-2 text-sm opacity-75"
                        >({stats.by_type[type.value]})</span
                    >
                {/if}
            </button>
        {/each}
    </div>

    <!-- Results -->
    {#if loading}
        <div class="flex justify-center items-center py-12">
            <div
                class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"
            />
        </div>
    {:else if error}
        <div
            class="bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-200 px-4 py-3 rounded"
        >
            <p class="font-bold">Error loading compendium</p>
            <p>{error}</p>
        </div>
    {:else if items.length === 0}
        <div class="text-center py-12">
            <p class="text-gray-600 dark:text-gray-400 text-lg">
                No items found. Try adjusting your filters.
            </p>
        </div>
    {:else}
        <!-- Items Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
            {#each items as item (item.id)}
                <CompendiumCard {item} />
            {/each}
        </div>

        <!-- Pagination -->
        <div class="flex justify-between items-center">
            <div class="text-sm text-gray-600 dark:text-gray-400">
                Showing {items.length} of {totalItems} items
            </div>
            <div class="flex gap-2">
                <button
                    on:click={prevPage}
                    disabled={currentPage === 1}
                    class="px-4 py-2 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                    Previous
                </button>
                <span
                    class="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg"
                >
                    Page {currentPage}
                </span>
                <button
                    on:click={nextPage}
                    disabled={!hasMore}
                    class="px-4 py-2 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                    Next
                </button>
            </div>
        </div>
    {/if}
</div>

<style>
    .container {
        max-width: 1200px;
    }
</style>
