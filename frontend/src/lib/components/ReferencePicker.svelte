<script>
    import { api } from "$lib/api.js";
    import { parseLinkQuery } from "$lib/formModel.js";

    export let value; // string guid (single) or array of guids (multiple)
    export let query = "";
    export let system;
    export let multiple = false;
    export let placeholder = "Type to search...";
    export let inputId = undefined;

    let search = "";
    let results = [];
    let open = false;
    let searching = false;
    let names = {}; // guid -> display name cache
    let debounceTimer;

    $: selectedGuids = multiple ? value || [] : value ? [value] : [];

    async function runSearch() {
        searching = true;
        try {
            const data = await api.get("/api/compendium/", {
                ...parseLinkQuery(query, system),
                search: search.trim(),
                limit: 20
            });
            results = data.entries;
            for (const entry of results) names[entry.guid] = entry.name;
            names = names;
            open = true;
        } catch (e) {
            console.error("Reference search failed:", e);
            results = [];
        } finally {
            searching = false;
        }
    }

    function handleInput() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(runSearch, 250);
    }

    function pick(entry) {
        names[entry.guid] = entry.name;
        names = names;
        if (multiple) {
            if (!(value || []).includes(entry.guid)) {
                value = [...(value || []), entry.guid];
            }
        } else {
            value = entry.guid;
            open = false;
        }
        search = "";
    }

    function remove(guid) {
        if (multiple) {
            value = (value || []).filter((g) => g !== guid);
        } else {
            value = "";
        }
    }

    function handleBlur() {
        // Delay so option mousedown still registers
        setTimeout(() => (open = false), 150);
    }
</script>

<div class="relative">
    {#if selectedGuids.length}
        <div class="flex flex-wrap gap-1 mb-1">
            {#each selectedGuids as guid}
                <span
                    class="inline-flex items-center gap-1 bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded-full"
                >
                    <span>{names[guid] || guid}</span>
                    <button
                        type="button"
                        on:click={() => remove(guid)}
                        class="font-bold hover:text-blue-900"
                        aria-label="Remove {names[guid] || guid}"
                    >
                        ×
                    </button>
                </span>
            {/each}
        </div>
    {/if}
    {#if multiple || !selectedGuids.length}
        <input
            type="text"
            id={inputId}
            bind:value={search}
            on:input={handleInput}
            on:focus={runSearch}
            on:blur={handleBlur}
            {placeholder}
            autocomplete="off"
            class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
    {/if}
    {#if open}
        <div
            class="absolute z-10 mt-1 w-full bg-white border rounded shadow-lg max-h-60 overflow-auto"
        >
            {#if searching}
                <p class="px-3 py-2 text-sm text-gray-400">Searching...</p>
            {:else}
                {#each results as entry}
                    <button
                        type="button"
                        on:mousedown|preventDefault={() => pick(entry)}
                        class="block w-full text-left px-3 py-2 text-sm hover:bg-blue-50"
                        class:opacity-40={selectedGuids.includes(entry.guid)}
                    >
                        {entry.name}
                        <span class="text-xs font-mono text-gray-400 ml-1"
                            >{entry.guid}</span
                        >
                    </button>
                {:else}
                    <p class="px-3 py-2 text-sm text-gray-400">No matches</p>
                {/each}
            {/if}
        </div>
    {/if}
</div>
