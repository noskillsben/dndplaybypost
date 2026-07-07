<script>
    import { onMount } from "svelte";
    import { api } from "$lib/api.js";
    import FieldInput from "$lib/components/FieldInput.svelte";
    import {
        defaultValueFor,
        validateForm,
        cleanFormData
    } from "$lib/formModel.js";

    export let system;
    export let entryType;
    export let initialData = {};
    export let onSubmit;

    let formSchema = null;
    let formData = {};
    let fieldErrors = {};
    let loading = true;
    let error = null;

    onMount(async () => {
        try {
            formSchema = await api.get(
                `/api/schemas/${encodeURIComponent(
                    system
                )}/${encodeURIComponent(entryType)}`
            );

            for (const field of formSchema.fields) {
                if (field.name in initialData && initialData[field.name] !== null) {
                    formData[field.name] = initialData[field.name];
                } else {
                    formData[field.name] = defaultValueFor(field);
                }
            }

            loading = false;
        } catch (e) {
            error = e.message;
            loading = false;
        }
    });

    function labelFor(field) {
        return field.name
            .split("_")
            .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
            .join(" ");
    }

    function handleSubmit(e) {
        e.preventDefault();
        fieldErrors = validateForm(formSchema.fields, formData);
        if (Object.keys(fieldErrors).length) return;
        if (onSubmit) {
            onSubmit(cleanFormData(formSchema.fields, formData));
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

        {#each formSchema.fields as field (field.name)}
            <div class="field">
                <label
                    for={field.name}
                    class="block text-gray-700 text-sm font-bold mb-2"
                >
                    {labelFor(field)}
                    {#if field.required}<span class="text-red-500">*</span>{/if}
                </label>

                <FieldInput
                    {field}
                    bind:value={formData[field.name]}
                    {system}
                    {entryType}
                    inputId={field.name}
                />

                {#if fieldErrors[field.name]}
                    <p class="text-xs text-red-600 font-bold mt-1">
                        {fieldErrors[field.name]}
                    </p>
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
            {#if Object.keys(fieldErrors).length}
                <p class="text-sm text-red-600 font-bold mr-4">
                    Fix the highlighted fields before saving.
                </p>
            {/if}
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
