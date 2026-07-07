<script>
    import { onMount } from "svelte";
    import { api } from "$lib/api.js";
    import FieldSpecEditor from "$lib/components/FieldSpecEditor.svelte";
    import {
        emptyFieldSpec,
        nameFieldSpec,
        cleanFieldSpec,
        editableFieldSpec
    } from "$lib/templateSpec.js";

    let systems = [];
    let selectedSystem = null;
    let templates = [];
    let error = null;

    // New-system form
    let showSystemForm = false;
    let newSystemName = "";
    let newSystemGuid = "";
    let newSystemDescription = "";

    // Template editor state
    let editing = false;
    let isNew = false;
    let entryType = "";
    let label = "";
    let description = "";
    let fields = [];
    let saving = false;

    onMount(loadSystems);

    async function loadSystems() {
        try {
            const data = await api.get("/api/schemas/systems");
            systems = data.systems;
        } catch (e) {
            error = e.message;
        }
    }

    async function selectSystem(system) {
        selectedSystem = system;
        editing = false;
        error = null;
        await loadTemplates();
    }

    async function loadTemplates() {
        try {
            const data = await api.get("/api/templates", {
                system: selectedSystem
            });
            templates = data.templates;
        } catch (e) {
            error = e.message;
        }
    }

    async function createSystem() {
        error = null;
        try {
            const created = await api.post("/api/systems", {
                name: newSystemName,
                ...(newSystemGuid.trim() && { guid: newSystemGuid.trim() }),
                ...(newSystemDescription.trim() && {
                    description: newSystemDescription.trim()
                })
            });
            showSystemForm = false;
            newSystemName = "";
            newSystemGuid = "";
            newSystemDescription = "";
            await loadSystems();
            await selectSystem(created.guid);
        } catch (e) {
            error = e.message;
        }
    }

    function startNewTemplate() {
        editing = true;
        isNew = true;
        entryType = "";
        label = "";
        description = "";
        fields = [nameFieldSpec()];
        error = null;
    }

    async function startEditTemplate(template) {
        error = null;
        try {
            const data = await api.get(
                `/api/templates/${encodeURIComponent(
                    template.system
                )}/${encodeURIComponent(template.entry_type)}`
            );
            editing = true;
            isNew = false;
            entryType = data.entry_type;
            label = data.label || "";
            description = data.description || "";
            fields = data.fields.map(editableFieldSpec);
        } catch (e) {
            error = e.message;
        }
    }

    function cancelEdit() {
        editing = false;
        error = null;
    }

    function addField() {
        fields = [...fields, emptyFieldSpec()];
    }

    function removeField(i) {
        fields = fields.filter((_, idx) => idx !== i);
    }

    function moveField(i, delta) {
        const j = i + delta;
        if (j < 0 || j >= fields.length) return;
        const next = [...fields];
        [next[i], next[j]] = [next[j], next[i]];
        fields = next;
    }

    async function saveTemplate() {
        error = null;
        saving = true;
        try {
            const payload = {
                label: label.trim() || null,
                description: description.trim() || null,
                fields: fields.map((f) => cleanFieldSpec(f))
            };
            if (isNew) {
                await api.post("/api/templates", {
                    system: selectedSystem,
                    entry_type: entryType,
                    ...payload
                });
            } else {
                await api.put(
                    `/api/templates/${encodeURIComponent(
                        selectedSystem
                    )}/${encodeURIComponent(entryType)}`,
                    payload
                );
            }
            editing = false;
            await loadTemplates();
        } catch (e) {
            error = e.message;
        } finally {
            saving = false;
        }
    }

    async function deleteTemplate(template) {
        if (
            !confirm(
                `Delete template "${template.entry_type}" from ${template.system}?`
            )
        )
            return;
        error = null;
        try {
            await api.delete(
                `/api/templates/${encodeURIComponent(
                    template.system
                )}/${encodeURIComponent(template.entry_type)}`
            );
            await loadTemplates();
        } catch (e) {
            error = e.message;
        }
    }
</script>

<div class="container mx-auto p-4 max-w-6xl">
    <header class="mb-8 border-b pb-4 flex justify-between items-center">
        <div>
            <h1 class="text-4xl font-extrabold text-gray-900 tracking-tight">
                Entry Templates
            </h1>
            <p class="text-gray-500 mt-1">
                Define what fields each entry type has — per game system
            </p>
        </div>
        <nav class="text-sm">
            <a href="/compendium" class="text-blue-600 font-bold hover:underline"
                >Compendium Browser</a
            >
        </nav>
    </header>

    {#if error}
        <div
            class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4"
        >
            <strong class="font-bold">Error:</strong>
            <span class="block sm:inline">{error}</span>
        </div>
    {/if}

    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
        <!-- Sidebar: systems -->
        <div class="space-y-6">
            <section>
                <h2
                    class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3"
                >
                    Systems
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
                <button
                    on:click={() => (showSystemForm = !showSystemForm)}
                    class="mt-3 text-xs font-bold text-blue-600 hover:text-blue-800 border border-blue-200 rounded px-3 py-1"
                >
                    {showSystemForm ? "Cancel" : "+ New System"}
                </button>
                {#if showSystemForm}
                    <form
                        on:submit|preventDefault={createSystem}
                        class="mt-3 space-y-2 bg-white shadow rounded border border-gray-200 p-3"
                    >
                        <input
                            type="text"
                            bind:value={newSystemName}
                            placeholder="Name (e.g. Lasers & Feelings)"
                            required
                            class="w-full shadow-sm border rounded py-1 px-2 text-sm"
                        />
                        <input
                            type="text"
                            bind:value={newSystemGuid}
                            placeholder="guid (optional, from name)"
                            class="w-full shadow-sm border rounded py-1 px-2 text-sm font-mono"
                        />
                        <input
                            type="text"
                            bind:value={newSystemDescription}
                            placeholder="Description (optional)"
                            class="w-full shadow-sm border rounded py-1 px-2 text-sm"
                        />
                        <button
                            type="submit"
                            class="w-full bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold py-1 rounded"
                        >
                            Create System
                        </button>
                    </form>
                {/if}
            </section>
        </div>

        <!-- Main content -->
        <div class="md:col-span-3">
            {#if !selectedSystem}
                <div
                    class="bg-blue-50 border-l-4 border-blue-400 p-8 rounded-r-lg text-center"
                >
                    <h3 class="text-lg font-bold text-blue-800">
                        Template Editor
                    </h3>
                    <p class="text-blue-600">
                        Select a game system on the left, or create a new one,
                        to manage its entry-type templates.
                    </p>
                </div>
            {:else if editing}
                <form
                    on:submit|preventDefault={saveTemplate}
                    class="space-y-6 bg-white shadow-md rounded px-8 pt-6 pb-8 border border-gray-200"
                >
                    <div
                        class="flex justify-between items-center border-b pb-4"
                    >
                        <h2 class="text-xl font-bold text-gray-800">
                            {isNew ? "New Template" : `Editing: ${entryType}`}
                            <span class="text-sm font-normal text-gray-400"
                                >({selectedSystem})</span
                            >
                        </h2>
                        <button
                            type="button"
                            on:click={cancelEdit}
                            class="text-sm text-gray-500 hover:text-gray-700 font-bold"
                        >
                            Cancel
                        </button>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <label
                            class="block text-sm font-bold text-gray-700"
                        >
                            Entry type
                            <input
                                type="text"
                                bind:value={entryType}
                                disabled={!isNew}
                                required
                                placeholder="e.g. ship"
                                class="mt-1 block w-full shadow-sm border rounded py-2 px-3 text-sm font-mono disabled:bg-gray-100 disabled:text-gray-400"
                            />
                        </label>
                        <label
                            class="block text-sm font-bold text-gray-700"
                        >
                            Label
                            <input
                                type="text"
                                bind:value={label}
                                placeholder="e.g. Ship"
                                class="mt-1 block w-full shadow-sm border rounded py-2 px-3 text-sm"
                            />
                        </label>
                        <label
                            class="block text-sm font-bold text-gray-700"
                        >
                            Description
                            <input
                                type="text"
                                bind:value={description}
                                class="mt-1 block w-full shadow-sm border rounded py-2 px-3 text-sm"
                            />
                        </label>
                    </div>

                    <div class="space-y-4">
                        <h3
                            class="text-xs font-semibold text-gray-400 uppercase tracking-wider"
                        >
                            Fields
                        </h3>
                        {#each fields as _, i}
                            <div
                                class="border rounded-lg p-4 bg-gray-50 flex items-start gap-3"
                            >
                                <div class="flex-1">
                                    <FieldSpecEditor
                                        bind:spec={fields[i]}
                                        locked={fields[i].name === "name" &&
                                            fields[i].base_field}
                                    />
                                </div>
                                <div
                                    class="flex flex-col gap-1 items-end shrink-0"
                                >
                                    <div class="flex gap-1">
                                        <button
                                            type="button"
                                            on:click={() => moveField(i, -1)}
                                            disabled={i === 0}
                                            class="text-xs font-bold text-gray-500 hover:text-gray-700 border rounded px-2 py-1 disabled:opacity-30"
                                            >↑</button
                                        >
                                        <button
                                            type="button"
                                            on:click={() => moveField(i, 1)}
                                            disabled={i === fields.length - 1}
                                            class="text-xs font-bold text-gray-500 hover:text-gray-700 border rounded px-2 py-1 disabled:opacity-30"
                                            >↓</button
                                        >
                                    </div>
                                    {#if !(fields[i].name === "name" && fields[i].base_field)}
                                        <button
                                            type="button"
                                            on:click={() => removeField(i)}
                                            class="text-xs font-bold text-red-600 hover:text-red-800 border border-red-200 rounded px-2 py-1"
                                        >
                                            Remove
                                        </button>
                                    {/if}
                                </div>
                            </div>
                        {/each}
                        <button
                            type="button"
                            on:click={addField}
                            class="text-sm font-bold text-blue-600 hover:text-blue-800 border border-blue-200 rounded px-3 py-1"
                        >
                            + Add Field
                        </button>
                    </div>

                    <div class="flex justify-end border-t pt-4">
                        <button
                            type="submit"
                            disabled={saving}
                            class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded disabled:opacity-50"
                        >
                            {saving
                                ? "Saving..."
                                : isNew
                                  ? "Create Template"
                                  : "Save Template"}
                        </button>
                    </div>
                </form>
            {:else}
                <div class="space-y-4">
                    <div class="flex justify-between items-center">
                        <h2 class="text-lg font-bold text-gray-800 capitalize">
                            Templates for {selectedSystem}
                        </h2>
                        <button
                            on:click={startNewTemplate}
                            class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded shadow transition-colors"
                        >
                            New Template
                        </button>
                    </div>
                    <div class="grid grid-cols-1 gap-3">
                        {#each templates as template}
                            <div
                                class="bg-white border rounded-lg p-4 shadow-sm flex justify-between items-center"
                            >
                                <div>
                                    <h4
                                        class="text-lg font-bold text-gray-900"
                                    >
                                        {template.label || template.entry_type}
                                        <span
                                            class="text-xs font-mono text-gray-400 ml-2"
                                            >{template.entry_type}</span
                                        >
                                    </h4>
                                    <p class="text-xs text-gray-500">
                                        {template.field_count} field{template.field_count ===
                                        1
                                            ? ""
                                            : "s"}
                                        {#if template.description}
                                            — {template.description}
                                        {/if}
                                    </p>
                                </div>
                                <div class="flex gap-2">
                                    <button
                                        on:click={() =>
                                            startEditTemplate(template)}
                                        class="text-xs font-bold text-blue-600 hover:text-blue-800 border border-blue-200 hover:border-blue-400 rounded px-3 py-1 transition-colors"
                                    >
                                        Edit
                                    </button>
                                    <button
                                        on:click={() =>
                                            deleteTemplate(template)}
                                        class="text-xs font-bold text-red-600 hover:text-red-800 border border-red-200 hover:border-red-400 rounded px-3 py-1 transition-colors"
                                    >
                                        Delete
                                    </button>
                                </div>
                            </div>
                        {:else}
                            <div
                                class="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200"
                            >
                                <p class="text-gray-500">
                                    No templates yet for this system.
                                </p>
                                <button
                                    on:click={startNewTemplate}
                                    class="mt-2 text-blue-600 font-bold hover:underline"
                                >
                                    Create the first one!
                                </button>
                            </div>
                        {/each}
                    </div>
                </div>
            {/if}
        </div>
    </div>
</div>
