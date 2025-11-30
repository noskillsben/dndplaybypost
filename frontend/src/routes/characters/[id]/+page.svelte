<script>
    import { page } from "$app/stores";
    import { onMount } from "svelte";
    import { api } from "$lib/api";
    import { auth } from "$lib/stores/auth";
    import { goto } from "$app/navigation";

    let character = null;
    let campaign = null;
    let error = "";
    let loading = true;
    let isOwner = false;
    let isDm = false;
    let isEditing = false;

    // Edit form data
    let editName = "";
    let editAvatarUrl = "";
    let editSheetData = "";
    let editNotes = "";

    $: characterId = $page.params.id;

    onMount(async () => {
        await loadData();
    });

    async function loadData() {
        try {
            loading = true;
            character = await api.get(`/characters/${characterId}`);

            // Check ownership
            if ($auth.user) {
                // We don't have the user ID in $auth.user (only username), so we can't strictly check ID match
                // without fetching "me" or decoding token.
                // However, we can check if we can fetch the campaign and see our role.
                // For now, let's fetch the campaign to check DM status and get campaign name.
                try {
                    campaign = await api.get(
                        `/campaigns/${character.campaign_id}`
                    );
                    const myMember = campaign.members.find(
                        (m) => m.username === $auth.user.username
                    );

                    if (myMember) {
                        isDm = myMember.role === "dm";
                        // If we are the player, we are the owner.
                        // Wait, character.player_id is a UUID. $auth.user only has username.
                        // We need to know our own UUID to check ownership reliably if we aren't DM.
                        // But we can infer it if we are in the member list.
                        isOwner = myMember.user_id === character.player_id;
                    }
                } catch (e) {
                    console.error("Failed to load campaign details", e);
                }
            }
        } catch (e) {
            error = e.message;
        } finally {
            loading = false;
        }
    }

    function startEdit() {
        editName = character.name;
        editAvatarUrl = character.avatar_url || "";
        editSheetData = JSON.stringify(character.sheet_data, null, 2);
        editNotes = character.notes || "";
        isEditing = true;
    }

    function cancelEdit() {
        isEditing = false;
    }

    async function saveEdit() {
        try {
            let parsedSheetData = {};
            try {
                parsedSheetData = JSON.parse(editSheetData);
            } catch (e) {
                throw new Error("Sheet Data must be valid JSON");
            }

            const updated = await api.patch(`/characters/${characterId}`, {
                name: editName,
                avatar_url: editAvatarUrl || null,
                sheet_data: parsedSheetData,
                notes: editNotes || null,
            });

            character = updated;
            isEditing = false;
        } catch (e) {
            alert(e.message);
        }
    }

    async function deleteCharacter() {
        if (!confirm("Are you sure you want to delete this character?")) return;
        try {
            await api.delete(`/characters/${characterId}`);
            goto("/characters");
        } catch (e) {
            alert(e.message);
        }
    }
</script>

<div class="container mx-auto p-4">
    {#if loading}
        <div class="text-center text-gray-400 mt-10">Loading...</div>
    {:else if error}
        <div class="bg-red-900 text-red-200 p-3 rounded mb-4">{error}</div>
    {:else if character}
        <div class="bg-gray-800 p-6 rounded-lg shadow-lg mb-6">
            <div class="flex flex-col md:flex-row gap-6">
                <!-- Avatar -->
                <div class="flex-shrink-0">
                    {#if character.avatar_url}
                        <img
                            src={character.avatar_url}
                            alt={character.name}
                            class="w-32 h-32 rounded-lg object-cover bg-gray-700"
                        />
                    {:else}
                        <div
                            class="w-32 h-32 rounded-lg bg-gray-700 flex items-center justify-center text-4xl text-gray-400"
                        >
                            {character.name[0]}
                        </div>
                    {/if}
                </div>

                <!-- Details -->
                <div class="flex-grow">
                    {#if isEditing}
                        <div class="space-y-4">
                            <div>
                                <label
                                    for="edit-name"
                                    class="block text-gray-400 text-sm mb-1"
                                    >Name</label
                                >
                                <input
                                    id="edit-name"
                                    type="text"
                                    bind:value={editName}
                                    class="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                                />
                            </div>
                            <div>
                                <label
                                    for="edit-avatar"
                                    class="block text-gray-400 text-sm mb-1"
                                    >Avatar URL</label
                                >
                                <input
                                    id="edit-avatar"
                                    type="text"
                                    bind:value={editAvatarUrl}
                                    class="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                                />
                            </div>
                            <div>
                                <label
                                    for="edit-sheet"
                                    class="block text-gray-400 text-sm mb-1"
                                    >Sheet Data (JSON)</label
                                >
                                <textarea
                                    id="edit-sheet"
                                    bind:value={editSheetData}
                                    class="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono h-32"
                                />
                            </div>
                            <div>
                                <label
                                    for="edit-notes"
                                    class="block text-gray-400 text-sm mb-1"
                                    >Notes</label
                                >
                                <textarea
                                    id="edit-notes"
                                    bind:value={editNotes}
                                    class="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-purple-500 h-24"
                                />
                            </div>
                            <div class="flex space-x-3">
                                <button
                                    on:click={saveEdit}
                                    class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded transition duration-200"
                                >
                                    Save
                                </button>
                                <button
                                    on:click={cancelEdit}
                                    class="bg-gray-600 hover:bg-gray-500 text-white px-4 py-2 rounded transition duration-200"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    {:else}
                        <div class="flex justify-between items-start">
                            <div>
                                <h1
                                    class="text-3xl font-bold text-purple-400 mb-1"
                                >
                                    {character.name}
                                </h1>
                                {#if campaign}
                                    <p class="text-gray-400 mb-4">
                                        Campaign: <a
                                            href="/campaigns/{campaign.id}"
                                            class="text-purple-300 hover:underline"
                                            >{campaign.name}</a
                                        >
                                    </p>
                                {/if}
                            </div>
                            {#if isOwner || isDm}
                                <div class="flex space-x-2">
                                    <button
                                        on:click={startEdit}
                                        class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm transition duration-200"
                                    >
                                        Edit
                                    </button>
                                    <button
                                        on:click={deleteCharacter}
                                        class="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm transition duration-200"
                                    >
                                        Delete
                                    </button>
                                </div>
                            {/if}
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
                            <div>
                                <h3
                                    class="text-lg font-bold text-white mb-2 border-b border-gray-700 pb-1"
                                >
                                    Stats & Data
                                </h3>
                                <pre
                                    class="bg-gray-900 p-4 rounded overflow-x-auto text-sm text-green-400 font-mono">{JSON.stringify(
                                        character.sheet_data,
                                        null,
                                        2
                                    )}</pre>
                            </div>
                            <div>
                                <h3
                                    class="text-lg font-bold text-white mb-2 border-b border-gray-700 pb-1"
                                >
                                    Notes
                                </h3>
                                <div class="text-gray-300 whitespace-pre-wrap">
                                    {character.notes || "No notes."}
                                </div>
                            </div>
                        </div>
                    {/if}
                </div>
            </div>
        </div>
    {/if}
</div>
