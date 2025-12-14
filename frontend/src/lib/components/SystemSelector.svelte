<script>
    import { createEventDispatcher } from "svelte";

    export let selectedSystem = "D&D 5.2 (2024)";
    export let label = "Game System";
    export let showLabel = true;

    const dispatch = createEventDispatcher();

    // Available game systems
    const systems = [
        { value: "D&D 5e", label: "D&D 5e", icon: "🐉" },
        { value: "D&D 5.2 (2024)", label: "D&D 5.2 (2024)", icon: "🐲" },
        { value: "Pathfinder 2e", label: "Pathfinder 2e", icon: "⚔️" },
    ];

    function handleChange(event) {
        selectedSystem = event.target.value;
        dispatch("change", selectedSystem);
    }

    function getSystemIcon(systemValue) {
        const system = systems.find((s) => s.value === systemValue);
        return system ? system.icon : "📚";
    }
</script>

<div class="system-selector">
    {#if showLabel}
        <label
            for="system-select"
            class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
        >
            {label}
        </label>
    {/if}
    <div class="relative">
        <span
            class="absolute left-3 top-1/2 transform -translate-y-1/2 text-xl pointer-events-none"
        >
            {getSystemIcon(selectedSystem)}
        </span>
        <select
            id="system-select"
            bind:value={selectedSystem}
            on:change={handleChange}
            class="w-full pl-12 pr-10 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none cursor-pointer"
        >
            {#each systems as system}
                <option value={system.value}>
                    {system.label}
                </option>
            {/each}
        </select>
        <div
            class="absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none"
        >
            <svg
                class="w-5 h-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M19 9l-7 7-7-7"
                />
            </svg>
        </div>
    </div>
</div>

<style>
    select {
        background-image: none;
    }
</style>
