<script>
    export let data;
    $: item = data.item;
    $: error = data.error;

    function getTypeIcon(type) {
        const icons = {
            class: "⚔️",
            race: "👤",
            spell: "✨",
            item: "🎒",
            background: "📜",
            feature: "🌟",
            subclass: "🛡️",
        };
        return icons[type] || "📄";
    }

    function formatDate(dateString) {
        return new Date(dateString).toLocaleDateString("en-US", {
            year: "numeric",
            month: "long",
            day: "numeric",
        });
    }
</script>

<svelte:head>
    <title>{item.name} - Compendium</title>
</svelte:head>

<div class="container mx-auto px-4 py-8 max-w-4xl">
    {#if error}
        <div
            class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative"
            role="alert"
        >
            <strong class="font-bold">Error!</strong>
            <span class="block sm:inline">{error}</span>
        </div>
    {:else}
        <!-- Back Button -->
        <a
            href="/compendium"
            class="inline-flex items-center text-blue-600 dark:text-blue-400 hover:underline mb-6"
        >
            <svg
                class="w-5 h-5 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M15 19l-7-7 7-7"
                />
            </svg>
            Back to Compendium
        </a>

        <!-- Header -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 mb-6">
            <div class="flex items-start justify-between mb-4">
                <div class="flex items-center gap-4">
                    <span class="text-5xl">{getTypeIcon(item.type)}</span>
                    <div>
                        <h1
                            class="text-3xl font-bold text-gray-900 dark:text-white mb-2"
                        >
                            {item.name}
                        </h1>
                        <div class="flex gap-2">
                            <span
                                class="px-3 py-1 rounded text-sm font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                            >
                                {item.type.charAt(0).toUpperCase() +
                                    item.type.slice(1)}
                            </span>
                            {#if item.is_official}
                                <span
                                    class="px-3 py-1 rounded text-sm font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                                >
                                    Official SRD
                                </span>
                            {:else}
                                <span
                                    class="px-3 py-1 rounded text-sm font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200"
                                >
                                    Homebrew
                                </span>
                            {/if}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tags -->
            {#if item.tags && item.tags.length > 0}
                <div class="flex flex-wrap gap-2 mb-4">
                    {#each item.tags as tag}
                        <span
                            class="px-2 py-1 rounded text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                        >
                            {tag}
                        </span>
                    {/each}
                </div>
            {/if}

            <!-- Metadata -->
            <div class="text-sm text-gray-600 dark:text-gray-400">
                <p>Version: {formatDate(item.version)}</p>
                <p>Created: {formatDate(item.created_at)}</p>
            </div>
        </div>

        <!-- Content Sections -->
        <div class="space-y-6">
            <!-- Description -->
            {#if item.data.description}
                <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                    <h2
                        class="text-xl font-bold text-gray-900 dark:text-white mb-3"
                    >
                        Description
                    </h2>
                    <p
                        class="text-gray-700 dark:text-gray-300 whitespace-pre-wrap"
                    >
                        {item.data.description}
                    </p>
                </div>
            {/if}

            <!-- Type-Specific Content -->
            {#if item.type === "class"}
                <!-- Class Details -->
                <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                    <h2
                        class="text-xl font-bold text-gray-900 dark:text-white mb-4"
                    >
                        Class Details
                    </h2>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <span
                                class="font-medium text-gray-700 dark:text-gray-300"
                                >Hit Die:</span
                            >
                            <span class="ml-2 text-gray-600 dark:text-gray-400"
                                >{item.data.hit_die}</span
                            >
                        </div>
                        <div>
                            <span
                                class="font-medium text-gray-700 dark:text-gray-300"
                                >Primary Abilities:</span
                            >
                            <span class="ml-2 text-gray-600 dark:text-gray-400"
                                >{item.data.primary_abilities?.join(", ")}</span
                            >
                        </div>
                    </div>

                    {#if item.data.saving_throw_proficiencies}
                        <div class="mt-4">
                            <span
                                class="font-medium text-gray-700 dark:text-gray-300"
                                >Saving Throw Proficiencies:</span
                            >
                            <span class="ml-2 text-gray-600 dark:text-gray-400"
                                >{item.data.saving_throw_proficiencies.join(
                                    ", "
                                )}</span
                            >
                        </div>
                    {/if}

                    {#if item.data.features_by_level}
                        <div class="mt-6">
                            <h3
                                class="font-bold text-gray-900 dark:text-white mb-3"
                            >
                                Features by Level
                            </h3>
                            {#each Object.entries(item.data.features_by_level) as [level, features]}
                                <div class="mb-4">
                                    <h4
                                        class="font-medium text-blue-600 dark:text-blue-400"
                                    >
                                        Level {level}
                                    </h4>
                                    <ul
                                        class="list-disc list-inside ml-4 text-gray-700 dark:text-gray-300"
                                    >
                                        {#each features as feature}
                                            <li>{feature.name}</li>
                                        {/each}
                                    </ul>
                                </div>
                            {/each}
                        </div>
                    {/if}
                </div>
            {:else if item.type === "spell"}
                <!-- Spell Details -->
                <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                    <h2
                        class="text-xl font-bold text-gray-900 dark:text-white mb-4"
                    >
                        Spell Details
                    </h2>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <span
                                class="font-medium text-gray-700 dark:text-gray-300"
                                >Level:</span
                            >
                            <span class="ml-2 text-gray-600 dark:text-gray-400"
                                >{item.data.level}</span
                            >
                        </div>
                        <div>
                            <span
                                class="font-medium text-gray-700 dark:text-gray-300"
                                >School:</span
                            >
                            <span class="ml-2 text-gray-600 dark:text-gray-400"
                                >{item.data.school}</span
                            >
                        </div>
                        <div>
                            <span
                                class="font-medium text-gray-700 dark:text-gray-300"
                                >Casting Time:</span
                            >
                            <span class="ml-2 text-gray-600 dark:text-gray-400"
                                >{item.data.casting_time?.type}</span
                            >
                        </div>
                        <div>
                            <span
                                class="font-medium text-gray-700 dark:text-gray-300"
                                >Range:</span
                            >
                            <span class="ml-2 text-gray-600 dark:text-gray-400"
                                >{item.data.range?.distance}
                                {item.data.range?.unit}</span
                            >
                        </div>
                    </div>

                    {#if item.data.damage}
                        <div class="mt-4">
                            <span
                                class="font-medium text-gray-700 dark:text-gray-300"
                                >Damage:</span
                            >
                            <span class="ml-2 text-gray-600 dark:text-gray-400"
                                >{item.data.damage.base}
                                {item.data.damage.type}</span
                            >
                        </div>
                    {/if}
                </div>
            {:else if item.type === "race"}
                <!-- Race Details -->
                <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                    <h2
                        class="text-xl font-bold text-gray-900 dark:text-white mb-4"
                    >
                        Race Details
                    </h2>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <span
                                class="font-medium text-gray-700 dark:text-gray-300"
                                >Size:</span
                            >
                            <span class="ml-2 text-gray-600 dark:text-gray-400"
                                >{item.data.size}</span
                            >
                        </div>
                        <div>
                            <span
                                class="font-medium text-gray-700 dark:text-gray-300"
                                >Speed:</span
                            >
                            <span class="ml-2 text-gray-600 dark:text-gray-400"
                                >{item.data.speed} ft</span
                            >
                        </div>
                    </div>

                    {#if item.data.languages}
                        <div class="mt-4">
                            <span
                                class="font-medium text-gray-700 dark:text-gray-300"
                                >Languages:</span
                            >
                            <span class="ml-2 text-gray-600 dark:text-gray-400"
                                >{item.data.languages.join(", ")}</span
                            >
                        </div>
                    {/if}
                </div>
            {:else if item.type === "item"}
                <!-- Item Details -->
                <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                    <h2
                        class="text-xl font-bold text-gray-900 dark:text-white mb-4"
                    >
                        Item Details
                    </h2>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <span
                                class="font-medium text-gray-700 dark:text-gray-300"
                                >Category:</span
                            >
                            <span class="ml-2 text-gray-600 dark:text-gray-400"
                                >{item.data.category}</span
                            >
                        </div>
                        {#if item.data.rarity}
                            <div>
                                <span
                                    class="font-medium text-gray-700 dark:text-gray-300"
                                    >Rarity:</span
                                >
                                <span
                                    class="ml-2 text-gray-600 dark:text-gray-400"
                                    >{item.data.rarity}</span
                                >
                            </div>
                        {/if}
                        {#if item.data.cost}
                            <div>
                                <span
                                    class="font-medium text-gray-700 dark:text-gray-300"
                                    >Cost:</span
                                >
                                <span
                                    class="ml-2 text-gray-600 dark:text-gray-400"
                                    >{item.data.cost.gp} gp</span
                                >
                            </div>
                        {/if}
                        {#if item.data.weight_lbs}
                            <div>
                                <span
                                    class="font-medium text-gray-700 dark:text-gray-300"
                                    >Weight:</span
                                >
                                <span
                                    class="ml-2 text-gray-600 dark:text-gray-400"
                                    >{item.data.weight_lbs} lbs</span
                                >
                            </div>
                        {/if}
                    </div>

                    {#if item.data.damage}
                        <div class="mt-4">
                            <span
                                class="font-medium text-gray-700 dark:text-gray-300"
                                >Damage:</span
                            >
                            <span class="ml-2 text-gray-600 dark:text-gray-400">
                                {item.data.damage.one_handed ||
                                    item.data.damage.base}
                                {item.data.damage.type}
                            </span>
                        </div>
                    {/if}
                </div>
            {/if}

            <!-- Raw Data (for debugging/advanced users) -->
            <details class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <summary
                    class="cursor-pointer font-bold text-gray-900 dark:text-white"
                >
                    Raw Data (Advanced)
                </summary>
                <pre
                    class="mt-4 p-4 bg-gray-100 dark:bg-gray-900 rounded overflow-x-auto text-sm text-gray-700 dark:text-gray-300">{JSON.stringify(
                        item.data,
                        null,
                        2
                    )}</pre>
            </details>
        </div>
    {/if}
</div>

<style>
    .container {
        max-width: 1024px;
    }
</style>
