<script>
    import { onMount } from "svelte";
    import { api } from "$lib/api.js";

    export let system;
    export let entryType;
    export let initialData = {};
    export let onSubmit;

    let formSchema = null;
    let formData = { ...initialData };
    let loading = true;
    let error = null;
    let compendiumOptions = {};

    onMount(async () => {
        try {
            formSchema = await api.get(
                `/api/schemas/${encodeURIComponent(
                    system
                )}/${encodeURIComponent(entryType)}`
            );

            // Pre-populate formData with initialData or defaults
            formSchema.fields.forEach((field) => {
                if (!(field.name in formData)) {
                    if (field.type === "number") {
                        formData[field.name] = null;
                    } else if (field.type === "compendium_link_list") {
                        formData[field.name] = [];
                    } else if (field.type === "checkbox") {
                        formData[field.name] = false;
                    } else {
                        formData[field.name] = "";
                    }
                }

                // If it's a compendium link or parent link, fetch options
                if (
                    field.type === "compendium_link" ||
                    field.type === "compendium_link_list"
                ) {
                    fetchCompendiumOptions(field.name, field.query);
                } else if (field.type === "parent_link") {
                    fetchParentOptions(field.name);
                }
            });

            loading = false;
        } catch (e) {
            error = e.message;
            loading = false;
        }
    });

    // Mirrors backend core/field_types.py parse_link_query
    function parseLinkQuery(query) {
        if (!query) return {};
        if (query.startsWith("parent:"))
            return { parent_guid: query.substring(7) };
        if (query.startsWith("type:"))
            return { system, entry_type: query.substring(5) };
        if (query.startsWith("tag:")) return { tag: query.substring(4) };
        if (query.startsWith("prefix:"))
            return { guid_prefix: query.substring(7) };
        // Legacy glob form: "d&d5.0-rule-*"
        return { guid_prefix: query.replace(/\*$/, "") };
    }

    async function fetchCompendiumOptions(fieldName, query) {
        try {
            const data = await api.get(
                "/api/compendium/",
                parseLinkQuery(query),
            );
            compendiumOptions[fieldName] = data.entries;
        } catch (e) {
            console.error(`Failed to fetch options for ${fieldName}:`, e);
        }
    }

    async function fetchParentOptions(fieldName) {
        try {
            // Fetch all entries of the same type for parent selection
            const data = await api.get("/api/compendium/", {
                system,
                entry_type: entryType,
            });
            compendiumOptions[fieldName] = data.entries;
        } catch (e) {
            console.error(
                `Failed to fetch parent options for ${fieldName}:`,
                e
            );
        }
    }

    function handleSubmit(e) {
        e.preventDefault();
        if (onSubmit) {
            // Prepare data (convert numbers, empty selections -> null)
            const cleanData = { ...formData };
            formSchema.fields.forEach((field) => {
                const value = cleanData[field.name];
                if (field.type === "number") {
                    cleanData[field.name] =
                        value === null || value === ""
                            ? null
                            : Number(value);
                } else if (
                    ["compendium_link", "parent_link", "select"].includes(
                        field.type,
                    ) &&
                    value === ""
                ) {
                    cleanData[field.name] = null;
                }
            });
            onSubmit(cleanData);
        }
    }
</script>

{#if loading}
    <div class="flex items-center justify-center p-8">
        <div
            class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"
        />
        <span class="ml-2">Loading form schema...</span>
    </div>
{:else if error}
    <div
        class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4"
    >
        <strong class="font-bold">Error:</strong>
        <span class="block sm:inline">{error}</span>
    </div>
{:else if formSchema}
    <form
        on:submit={handleSubmit}
        class="space-y-6 bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4 border border-gray-200"
    >
        <div class="mb-4 border-b pb-4">
            <h2 class="text-xl font-bold text-gray-800 capitalize">
                {entryType.replace("-", " ")} Form
            </h2>
            <p class="text-sm text-gray-500">System: {system}</p>
        </div>

        {#each formSchema.fields as field}
            <div class="field">
                <label
                    for={field.name}
                    class="block text-gray-700 text-sm font-bold mb-2"
                >
                    {field.name
                        .split("_")
                        .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                        .join(" ")}
                    {#if field.required}<span class="text-red-500">*</span>{/if}
                </label>

                {#if field.type === "text"}
                    <input
                        type="text"
                        id={field.name}
                        bind:value={formData[field.name]}
                        maxlength={field.maxLength}
                        placeholder={field.placeholder || ""}
                        required={field.required}
                        class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                {:else if field.type === "textarea"}
                    <textarea
                        id={field.name}
                        bind:value={formData[field.name]}
                        maxlength={field.maxLength}
                        placeholder={field.placeholder || ""}
                        required={field.required}
                        rows="4"
                        class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                {:else if field.type === "number"}
                    <input
                        type="number"
                        id={field.name}
                        bind:value={formData[field.name]}
                        min={field.min}
                        max={field.max}
                        step={field.step}
                        required={field.required}
                        class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                {:else if field.type === "compendium_link"}
                    <div class="relative">
                        <select
                            id={field.name}
                            bind:value={formData[field.name]}
                            required={field.required}
                            class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="">{field.label}</option>
                            {#if compendiumOptions[field.name]}
                                {#each compendiumOptions[field.name] as option}
                                    <option value={option.guid}
                                        >{option.name} ({option.guid})</option
                                    >
                                {/each}
                            {/if}
                        </select>
                    </div>
                {:else if field.type === "compendium_link_list"}
                    <div class="relative">
                        <select
                            id={field.name}
                            multiple
                            bind:value={formData[field.name]}
                            required={field.required}
                            size="5"
                            class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            {#if compendiumOptions[field.name]}
                                {#each compendiumOptions[field.name] as option}
                                    <option value={option.guid}
                                        >{option.name} ({option.guid})</option
                                    >
                                {/each}
                            {/if}
                        </select>
                        <p class="text-xs text-gray-500 mt-1">
                            {field.label} — hold Ctrl/Cmd to select multiple
                        </p>
                    </div>
                {:else if field.type === "checkbox"}
                    <label class="flex items-center cursor-pointer">
                        <input
                            type="checkbox"
                            id={field.name}
                            bind:checked={formData[field.name]}
                            class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                        {#if field.label}
                            <span class="ml-2 text-sm text-gray-700"
                                >{field.label}</span
                            >
                        {/if}
                    </label>
                {:else if field.type === "parent_link"}
                    <div class="relative">
                        <select
                            id={field.name}
                            bind:value={formData[field.name]}
                            required={field.required}
                            class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="">None (Top Level)</option>
                            {#if compendiumOptions[field.name]}
                                {#each compendiumOptions[field.name] as option}
                                    <option value={option.guid}
                                        >{option.name}</option
                                    >
                                {/each}
                            {/if}
                        </select>
                        <p class="text-xs text-gray-500 mt-1">
                            Select a parent entry to create a hierarchical
                            structure
                        </p>
                    </div>
                {:else if field.type === "markdown"}
                    <textarea
                        id={field.name}
                        bind:value={formData[field.name]}
                        maxlength={field.maxLength}
                        placeholder={field.placeholder ||
                            "Supports **markdown** formatting"}
                        required={field.required}
                        rows="6"
                        class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                    />
                    <p class="text-xs text-gray-500 mt-1">
                        Supports markdown: **bold**, *italic*, # headings, etc.
                    </p>
                {:else if field.type === "select"}
                    <select
                        id={field.name}
                        bind:value={formData[field.name]}
                        required={field.required}
                        class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        {#if field.options}
                            {#each field.options as option}
                                <option value={option}>{option}</option>
                            {/each}
                        {/if}
                    </select>
                {/if}

                {#if field.base_field}
                    <p class="text-xs text-blue-500 mt-1 italic">
                        Base field (common across systems)
                    </p>
                {:else}
                    <p class="text-xs text-gray-400 mt-1 italic">
                        System field
                    </p>
                {/if}
            </div>
        {/each}

        <div class="flex items-center justify-end border-t pt-4">
            <button
                type="submit"
                class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
            >
                Save Entry
            </button>
        </div>
    </form>
{/if}

<style>
    .field:focus-within label {
        @apply text-blue-600;
    }
</style>
