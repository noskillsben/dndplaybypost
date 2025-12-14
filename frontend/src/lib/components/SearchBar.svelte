<script>
    import { createEventDispatcher } from "svelte";

    export let placeholder = "Search...";
    export let value = "";

    const dispatch = createEventDispatcher();
    let searchTimeout;

    function handleInput(e) {
        value = e.target.value;

        // Debounce search
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            dispatch("search", value);
        }, 300);
    }

    function handleClear() {
        value = "";
        dispatch("search", "");
    }
</script>

<div class="relative">
    <div
        class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none"
    >
        <svg
            class="w-5 h-5 text-gray-500 dark:text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
        >
            <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
        </svg>
    </div>
    <input
        type="text"
        {placeholder}
        {value}
        on:input={handleInput}
        class="block w-full pl-10 pr-10 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
    />
    {#if value}
        <button
            on:click={handleClear}
            class="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
            <svg
                class="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M6 18L18 6M6 6l12 12"
                />
            </svg>
        </button>
    {/if}
</div>
