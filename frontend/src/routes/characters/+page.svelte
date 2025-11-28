<script>
    import { onMount } from "svelte";
    import { api } from "$lib/api";

    let characters = [];
    let error = "";

    onMount(async () => {
        try {
            characters = await api.get("/characters");
        } catch (e) {
            error = e.message;
        }
    });
</script>

<div class="container mx-auto p-4">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-bold text-purple-400">My Characters</h1>
        <a
            href="/characters/new"
            class="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded transition duration-200"
        >
            Create Character
        </a>
    </div>

    {#if error}
        <div class="bg-red-900 text-red-200 p-3 rounded mb-4">{error}</div>
    {/if}

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {#each characters as character}
            <a
                href="/characters/{character.id}"
                class="block bg-gray-800 p-6 rounded-lg shadow-lg hover:bg-gray-750 transition duration-200 border border-gray-700 hover:border-purple-500"
            >
                <div class="flex items-center space-x-4">
                    {#if character.avatar_url}
                        <img
                            src={character.avatar_url}
                            alt={character.name}
                            class="w-16 h-16 rounded-full object-cover"
                        />
                    {:else}
                        <div
                            class="w-16 h-16 rounded-full bg-gray-700 flex items-center justify-center text-2xl text-gray-400"
                        >
                            {character.name[0]}
                        </div>
                    {/if}
                    <div>
                        <h2 class="text-xl font-bold text-white">
                            {character.name}
                        </h2>
                        <p class="text-sm text-gray-500">
                            Created: {new Date(
                                character.created_at
                            ).toLocaleDateString()}
                        </p>
                    </div>
                </div>
            </a>
        {/each}
    </div>

    {#if characters.length === 0 && !error}
        <p class="text-gray-400 text-center mt-10">
            You don't have any characters yet.
        </p>
    {/if}
</div>
