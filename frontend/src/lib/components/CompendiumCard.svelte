<script>
    export let item;

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

    function getTypeColor(type) {
        const colors = {
            class: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
            race: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
            spell: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
            item: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
            background:
                "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
            feature:
                "bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200",
        };
        return (
            colors[type] ||
            "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200"
        );
    }

    function getDescription(item) {
        if (item.data.description) {
            return (
                item.data.description.substring(0, 150) +
                (item.data.description.length > 150 ? "..." : "")
            );
        }
        return "No description available";
    }

    function getQuickInfo(item) {
        switch (item.type) {
            case "class":
                return `Hit Die: ${item.data.hit_die || "Unknown"}`;
            case "spell":
                return `Level ${item.data.level} ${item.data.school || ""}`;
            case "item":
                return item.data.rarity || "Common";
            case "race":
                return `${item.data.size || "Medium"} • Speed ${
                    item.data.speed || 30
                }ft`;
            default:
                return "";
        }
    }
</script>

<a
    href="/compendium/{item.id}"
    class="block bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-lg transition-shadow p-6 border border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-400"
>
    <!-- Header -->
    <div class="flex items-start justify-between mb-3">
        <div class="flex items-center gap-2">
            <span class="text-2xl">{getTypeIcon(item.type)}</span>
            <div>
                <h3 class="text-lg font-bold text-gray-900 dark:text-white">
                    {item.name}
                </h3>
                <span
                    class="text-xs px-2 py-1 rounded {getTypeColor(item.type)}"
                >
                    {item.type.charAt(0).toUpperCase() + item.type.slice(1)}
                </span>
            </div>
        </div>
        {#if item.is_official}
            <span
                class="text-xs px-2 py-1 rounded bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
            >
                Official
            </span>
        {:else}
            <span
                class="text-xs px-2 py-1 rounded bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200"
            >
                Homebrew
            </span>
        {/if}
    </div>

    <!-- Quick Info -->
    {#if getQuickInfo(item)}
        <div class="text-sm font-medium text-blue-600 dark:text-blue-400 mb-2">
            {getQuickInfo(item)}
        </div>
    {/if}

    <!-- Description -->
    <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">
        {getDescription(item)}
    </p>

    <!-- Tags -->
    {#if item.tags && item.tags.length > 0}
        <div class="flex flex-wrap gap-1">
            {#each item.tags.slice(0, 3) as tag}
                <span
                    class="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                >
                    {tag}
                </span>
            {/each}
            {#if item.tags.length > 3}
                <span
                    class="text-xs px-2 py-1 text-gray-500 dark:text-gray-400"
                >
                    +{item.tags.length - 3} more
                </span>
            {/if}
        </div>
    {/if}
</a>
