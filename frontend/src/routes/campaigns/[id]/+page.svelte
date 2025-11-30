<script>
    import { page } from "$app/stores";
    import { onMount } from "svelte";
    import { api } from "$lib/api";
    import { auth } from "$lib/stores/auth";
    import { goto } from "$app/navigation";

    let campaign = null;
    let error = "";
    let loading = true;
    let userSearch = "";
    let searchResults = [];
    let isDm = false;

    $: campaignId = $page.params.id;

    onMount(async () => {
        await loadCampaign();
    });

    async function loadCampaign() {
        try {
            loading = true;
            campaign = await api.get(`/campaigns/${campaignId}`);
            checkDmStatus();
        } catch (e) {
            error = e.message;
        } finally {
            loading = false;
        }
    }

    function checkDmStatus() {
        if (!$auth.user || !campaign) return;
        const myMember = campaign.members.find(
            (m) => m.username === $auth.user.username
        );
        isDm = myMember?.role === "dm";
    }

    async function deleteCampaign() {
        if (!confirm("Are you sure you want to delete this campaign?")) return;
        try {
            await api.delete(`/campaigns/${campaignId}`);
            goto("/campaigns");
        } catch (e) {
            alert(e.message);
        }
    }

    async function searchUsers() {
        if (userSearch.length < 3) {
            searchResults = [];
            return;
        }
        try {
            searchResults = await api.get(`/users/search?q=${userSearch}`);
        } catch (e) {
            console.error(e);
        }
    }

    async function addMember(userId) {
        try {
            await api.post(`/campaigns/${campaignId}/members`, {
                user_id: userId,
                role: "player",
            });
            userSearch = "";
            searchResults = [];
            await loadCampaign();
        } catch (e) {
            alert(e.message);
        }
    }

    async function removeMember(userId) {
        if (!confirm("Remove this member?")) return;
        try {
            await api.delete(`/campaigns/${campaignId}/members/${userId}`);
            await loadCampaign();
        } catch (e) {
            alert(e.message);
        }
    }

    async function updateRole(userId, newRole) {
        try {
            await api.patch(`/campaigns/${campaignId}/members/${userId}`, {
                role: newRole,
            });
            await loadCampaign();
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
    {:else if campaign}
        <div class="bg-gray-800 p-6 rounded-lg shadow-lg mb-6">
            <div class="flex justify-between items-start">
                <div>
                    <h1 class="text-3xl font-bold text-purple-400 mb-2">
                        {campaign.name}
                    </h1>
                    <p class="text-gray-300 whitespace-pre-wrap">
                        {campaign.description || "No description"}
                    </p>
                </div>
                {#if isDm}
                    <div class="flex space-x-2">
                        <button
                            on:click={deleteCampaign}
                            class="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm transition duration-200"
                        >
                            Delete
                        </button>
                    </div>
                    <div class="flex gap-4 mb-6">
                        <a
                            href="/campaigns/{campaign.id}/chat"
                            class="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors flex items-center gap-2"
                        >
                            <span>💬</span>
                            Open Chat
                        </a>
                        {#if isDm}
                            <a
                                href="/campaigns/{campaign.id}/edit"
                                class="px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600 transition-colors"
                            >
                                Edit Settings
                            </a>
                        {/if}
                    </div>
                {/if}
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Members -->
            <div class="bg-gray-800 p-6 rounded-lg shadow-lg">
                <h2 class="text-xl font-bold text-white mb-4">Members</h2>
                <div class="space-y-4">
                    {#each campaign.members as member}
                        <div
                            class="flex justify-between items-center bg-gray-700 p-3 rounded"
                        >
                            <div>
                                <div class="font-bold text-white">
                                    {member.username}
                                </div>
                                <div class="text-sm text-gray-400 capitalize">
                                    {member.role}
                                </div>
                            </div>
                            {#if isDm && member.username !== $auth.user.username}
                                <div class="flex space-x-2">
                                    {#if member.role === "player"}
                                        <button
                                            on:click={() =>
                                                updateRole(
                                                    member.user_id,
                                                    "dm"
                                                )}
                                            class="text-blue-400 hover:text-blue-300 text-sm"
                                        >
                                            Promote
                                        </button>
                                    {:else}
                                        <button
                                            on:click={() =>
                                                updateRole(
                                                    member.user_id,
                                                    "player"
                                                )}
                                            class="text-yellow-400 hover:text-yellow-300 text-sm"
                                        >
                                            Demote
                                        </button>
                                    {/if}
                                    <button
                                        on:click={() =>
                                            removeMember(member.user_id)}
                                        class="text-red-400 hover:text-red-300 text-sm"
                                    >
                                        Remove
                                    </button>
                                </div>
                            {/if}
                        </div>
                    {/each}
                </div>

                {#if isDm}
                    <div class="mt-6 border-t border-gray-700 pt-4">
                        <h3 class="text-lg font-bold text-white mb-2">
                            Add Member
                        </h3>
                        <div class="relative">
                            <label for="user-search" class="sr-only"
                                >Search username</label
                            >
                            <input
                                id="user-search"
                                type="text"
                                bind:value={userSearch}
                                on:input={searchUsers}
                                placeholder="Search username..."
                                class="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                            />
                            {#if searchResults.length > 0}
                                <div
                                    class="absolute w-full bg-gray-700 mt-1 rounded shadow-lg z-10 max-h-48 overflow-y-auto border border-gray-600"
                                >
                                    {#each searchResults as user}
                                        <button
                                            on:click={() => addMember(user.id)}
                                            class="w-full text-left p-2 hover:bg-gray-600 text-white border-b border-gray-600 last:border-0"
                                        >
                                            {user.username}
                                        </button>
                                    {/each}
                                </div>
                            {/if}
                        </div>
                    </div>
                {/if}
            </div>

            <!-- Characters -->
            <div class="bg-gray-800 p-6 rounded-lg shadow-lg">
                <h2 class="text-xl font-bold text-white mb-4">Characters</h2>
                <p class="text-gray-400 mb-4">Character list coming soon...</p>
                <a
                    href="/characters/new?campaign={campaignId}"
                    class="text-purple-400 hover:text-purple-300 inline-block"
                >
                    Create Character
                </a>
            </div>
        </div>
    {/if}
</div>
