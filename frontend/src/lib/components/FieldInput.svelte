<script>
    import ReferencePicker from "$lib/components/ReferencePicker.svelte";
    import {
        defaultValueFor,
        defaultTableRow,
        isValidDiceExpression
    } from "$lib/formModel.js";

    export let field;
    export let value;
    export let system;
    export let entryType;
    export let inputId = undefined;

    const inputClass =
        "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500";

    function addItem() {
        value = [...(value || []), defaultValueFor(field.item)];
    }

    function removeItem(i) {
        value = value.filter((_, idx) => idx !== i);
    }

    function addRow() {
        value = [...(value || []), defaultTableRow(field)];
    }

    function removeRow(i) {
        value = value.filter((_, idx) => idx !== i);
    }

    $: diceValid =
        field.type !== "dice_expression" ||
        !value ||
        !String(value).trim() ||
        isValidDiceExpression(value);
</script>

{#if field.type === "text"}
    <input
        type="text"
        id={inputId}
        bind:value
        maxlength={field.maxLength}
        placeholder={field.placeholder || ""}
        class={inputClass}
    />
{:else if field.type === "textarea"}
    <textarea
        id={inputId}
        bind:value
        maxlength={field.maxLength}
        placeholder={field.placeholder || ""}
        rows="4"
        class={inputClass}
    />
{:else if field.type === "markdown"}
    <textarea
        id={inputId}
        bind:value
        maxlength={field.maxLength}
        placeholder={field.placeholder || "Supports **markdown** formatting"}
        rows="6"
        class="{inputClass} font-mono text-sm"
    />
    <p class="text-xs text-gray-500 mt-1">
        Supports markdown: **bold**, *italic*, # headings, etc.
    </p>
{:else if field.type === "number"}
    <input
        type="number"
        id={inputId}
        bind:value
        min={field.min}
        max={field.max}
        step={field.step}
        class={inputClass}
    />
{:else if field.type === "checkbox"}
    <label class="flex items-center cursor-pointer">
        <input
            type="checkbox"
            id={inputId}
            bind:checked={value}
            class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
        />
        {#if field.label}
            <span class="ml-2 text-sm text-gray-700">{field.label}</span>
        {/if}
    </label>
{:else if field.type === "select"}
    <select id={inputId} bind:value class={inputClass}>
        <option value="">{field.label || "Select..."}</option>
        {#each field.options || [] as option}
            <option value={option}>{option}</option>
        {/each}
    </select>
{:else if field.type === "dice_expression"}
    <input
        type="text"
        id={inputId}
        bind:value
        placeholder={field.placeholder || "e.g. 2d6+3"}
        class="{inputClass} font-mono {diceValid
            ? ''
            : 'border-red-400 focus:ring-red-400'}"
    />
    {#if !diceValid}
        <p class="text-xs text-red-500 mt-1">
            Invalid dice expression — try "d20", "2d6+3", "1d8 + 2d4 - 1"
        </p>
    {/if}
{:else if field.type === "compendium_link"}
    <ReferencePicker
        bind:value
        query={field.query}
        {system}
        {inputId}
        placeholder={field.label || "Search entries..."}
    />
{:else if field.type === "compendium_link_list" || field.type === "grant"}
    <ReferencePicker
        bind:value
        query={field.query}
        {system}
        {inputId}
        multiple
        placeholder={field.label || "Search entries..."}
    />
    {#if field.minItems !== undefined || field.maxItems !== undefined}
        <p class="text-xs text-gray-500 mt-1">
            {#if field.minItems !== undefined}Min {field.minItems}.{/if}
            {#if field.maxItems !== undefined}Max {field.maxItems}.{/if}
        </p>
    {/if}
{:else if field.type === "parent_link"}
    <ReferencePicker
        bind:value
        query={"type:" + entryType}
        {system}
        {inputId}
        placeholder="Search for a parent entry (optional)..."
    />
    <p class="text-xs text-gray-500 mt-1">
        Select a parent entry to create a hierarchical structure
    </p>
{:else if field.type === "list"}
    <div class="space-y-2">
        {#each value || [] as _, i}
            <div class="flex items-start gap-2">
                <div class="flex-1">
                    <svelte:self
                        field={field.item}
                        bind:value={value[i]}
                        {system}
                        {entryType}
                    />
                </div>
                <button
                    type="button"
                    on:click={() => removeItem(i)}
                    class="text-xs font-bold text-red-600 hover:text-red-800 border border-red-200 rounded px-2 py-1 mt-1"
                >
                    Remove
                </button>
            </div>
        {/each}
        <button
            type="button"
            on:click={addItem}
            class="text-xs font-bold text-blue-600 hover:text-blue-800 border border-blue-200 rounded px-2 py-1"
        >
            + Add {field.label || "item"}
        </button>
    </div>
{:else if field.type === "table"}
    <div class="space-y-2">
        <div class="overflow-x-auto border rounded">
            <table class="min-w-full text-sm">
                <thead class="bg-gray-50">
                    <tr>
                        {#each field.columns || [] as col}
                            <th
                                class="px-3 py-2 text-left text-xs font-semibold text-gray-500 uppercase"
                            >
                                {col.name.replace(/_/g, " ")}
                            </th>
                        {/each}
                        <th class="w-16" />
                    </tr>
                </thead>
                <tbody>
                    {#each value || [] as _, i}
                        <tr class="border-t">
                            {#each field.columns || [] as col}
                                <td class="px-2 py-1 align-top">
                                    <svelte:self
                                        field={col}
                                        bind:value={value[i][col.name]}
                                        {system}
                                        {entryType}
                                    />
                                </td>
                            {/each}
                            <td class="px-2 py-1 align-top">
                                <button
                                    type="button"
                                    on:click={() => removeRow(i)}
                                    class="text-xs font-bold text-red-600 hover:text-red-800"
                                >
                                    ×
                                </button>
                            </td>
                        </tr>
                    {:else}
                        <tr class="border-t">
                            <td
                                colspan={(field.columns || []).length + 1}
                                class="px-3 py-2 text-gray-400 italic text-center"
                            >
                                No rows yet
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
        <button
            type="button"
            on:click={addRow}
            class="text-xs font-bold text-blue-600 hover:text-blue-800 border border-blue-200 rounded px-2 py-1"
        >
            + Add row
        </button>
    </div>
{:else if field.type === "choice"}
    <div class="space-y-2 border rounded p-3 bg-gray-50">
        <label class="block text-xs font-semibold text-gray-500">
            Choose how many
            <input
                type="number"
                min="1"
                bind:value={value.choose}
                class="block shadow-sm border rounded py-1 px-2 text-sm w-24"
            />
        </label>
        <label class="block text-xs font-semibold text-gray-500">
            From query (e.g. type:skill)
            <input
                type="text"
                bind:value={value.query}
                class="block shadow-sm border rounded py-1 px-2 text-sm w-full font-mono"
            />
        </label>
        <div>
            <p class="text-xs font-semibold text-gray-500 mb-1">
                Or an explicit option list
            </p>
            <ReferencePicker
                bind:value={value.options}
                query={value.query || field.query}
                {system}
                multiple
                placeholder="Search options..."
            />
        </div>
    </div>
{:else}
    <input type="text" id={inputId} bind:value class={inputClass} />
    <p class="text-xs text-gray-400 mt-1 italic">
        Unknown field type "{field.type}" — edited as raw text
    </p>
{/if}
