<script>
    import { FIELD_TYPES, emptyFieldSpec } from "$lib/templateSpec.js";

    export let spec;
    export let showName = true;
    export let showFlags = true;
    export let locked = false;

    $: meta = FIELD_TYPES[spec.type] || { params: [] };

    $: if (spec.type === "list_of" && !spec.params.item) {
        spec.params.item = emptyFieldSpec();
    }
    $: if (spec.type === "table" && !spec.params.columns) {
        spec.params.columns = [emptyFieldSpec()];
    }

    function handleTypeChange() {
        spec.params = {};
        if (spec.type === "list_of") {
            spec.params.item = emptyFieldSpec();
        } else if (spec.type === "table") {
            spec.params.columns = [emptyFieldSpec()];
        }
    }

    function addColumn() {
        spec.params.columns = [...(spec.params.columns || []), emptyFieldSpec()];
    }

    function removeColumn(i) {
        spec.params.columns = spec.params.columns.filter((_, idx) => idx !== i);
    }
</script>

<div class="space-y-3">
    <div class="flex flex-wrap items-end gap-3">
        {#if showName}
            <div>
                <label class="block text-xs font-semibold text-gray-500 mb-1">
                    Field name
                    <input
                        type="text"
                        bind:value={spec.name}
                        disabled={locked}
                        placeholder="e.g. hit_die"
                        class="block shadow-sm border rounded py-1 px-2 text-sm text-gray-700 font-mono disabled:bg-gray-100 disabled:text-gray-400"
                    />
                </label>
            </div>
        {/if}
        <div>
            <label class="block text-xs font-semibold text-gray-500 mb-1">
                Type
                <select
                    bind:value={spec.type}
                    on:change={handleTypeChange}
                    disabled={locked}
                    class="block shadow-sm border rounded py-1 px-2 text-sm text-gray-700 disabled:bg-gray-100 disabled:text-gray-400"
                >
                    {#each Object.entries(FIELD_TYPES) as [typeName, typeMeta]}
                        <option value={typeName}>{typeMeta.label}</option>
                    {/each}
                </select>
            </label>
        </div>
        {#if showFlags}
            <label class="flex items-center gap-1 text-sm text-gray-700 pb-1">
                <input
                    type="checkbox"
                    bind:checked={spec.required}
                    disabled={locked}
                    class="w-4 h-4 text-blue-600 border-gray-300 rounded"
                />
                Required
            </label>
            <label class="flex items-center gap-1 text-sm text-gray-700 pb-1">
                <input
                    type="checkbox"
                    bind:checked={spec.base_field}
                    disabled={locked}
                    class="w-4 h-4 text-blue-600 border-gray-300 rounded"
                />
                Base field
            </label>
        {/if}
    </div>

    {#if meta.params.length}
        <div class="flex flex-wrap items-end gap-3 pl-3 border-l-2 border-gray-200">
            {#each meta.params as param (spec.type + ":" + param.name)}
                {#if param.kind === "item"}
                    <div class="w-full bg-gray-50 rounded p-2">
                        <p class="text-xs font-semibold text-gray-500 mb-2">
                            {param.label}
                        </p>
                        {#if spec.params.item}
                            <svelte:self
                                bind:spec={spec.params.item}
                                showName={false}
                                showFlags={false}
                                {locked}
                            />
                        {/if}
                    </div>
                {:else if param.kind === "columns"}
                    <div class="w-full bg-gray-50 rounded p-2 space-y-2">
                        <p class="text-xs font-semibold text-gray-500">
                            {param.label}
                        </p>
                        {#each spec.params.columns || [] as _, i}
                            <div class="flex items-start gap-2">
                                <div class="flex-1">
                                    <svelte:self
                                        bind:spec={spec.params.columns[i]}
                                        showName={true}
                                        showFlags={false}
                                        {locked}
                                    />
                                </div>
                                {#if !locked}
                                    <button
                                        type="button"
                                        on:click={() => removeColumn(i)}
                                        class="text-xs font-bold text-red-600 hover:text-red-800 border border-red-200 rounded px-2 py-1"
                                    >
                                        Remove
                                    </button>
                                {/if}
                            </div>
                        {/each}
                        {#if !locked}
                            <button
                                type="button"
                                on:click={addColumn}
                                class="text-xs font-bold text-blue-600 hover:text-blue-800 border border-blue-200 rounded px-2 py-1"
                            >
                                + Column
                            </button>
                        {/if}
                    </div>
                {:else if param.kind === "int" || param.kind === "number"}
                    <label class="block text-xs font-semibold text-gray-500">
                        {param.label}
                        <input
                            type="number"
                            step={param.kind === "int" ? "1" : "any"}
                            bind:value={spec.params[param.name]}
                            disabled={locked}
                            class="block shadow-sm border rounded py-1 px-2 text-sm text-gray-700 w-24 disabled:bg-gray-100 disabled:text-gray-400"
                        />
                    </label>
                {:else}
                    <label class="block text-xs font-semibold text-gray-500">
                        {param.label}
                        <input
                            type="text"
                            bind:value={spec.params[param.name]}
                            disabled={locked}
                            class="block shadow-sm border rounded py-1 px-2 text-sm text-gray-700 w-64 disabled:bg-gray-100 disabled:text-gray-400"
                        />
                    </label>
                {/if}
            {/each}
        </div>
    {/if}
</div>
