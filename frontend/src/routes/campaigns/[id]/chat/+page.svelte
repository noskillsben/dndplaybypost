<script>
    import { onMount, onDestroy, afterUpdate } from "svelte";
    import { page } from "$app/stores";
    import { campaignChat } from "$lib/websocket";
    import { api } from "$lib/api";
    import { auth } from "$lib/stores/auth";
    import ChatMessage from "$lib/components/ChatMessage.svelte";
    import ChatInput from "$lib/components/ChatInput.svelte";

    let campaignId = $page.params.id;
    let chatContainer;
    let characters = [];
    let loading = true;

    // Subscribe to WebSocket store
    $: ({ isConnected, messages, error, users } = $campaignChat);
    $: currentUser = $auth.user;

    onMount(async () => {
        try {
            // Note: Initial messages will be loaded via WebSocket connection
            // The backend should send recent messages when client connects

            // Load user's characters for this campaign
            // TODO: Add endpoint to get my characters for a campaign
            // For now we'll just fetch all characters and filter client-side (not ideal but works for prototype)
            // const myChars = await api.get(`/campaigns/${campaignId}/my-characters`);
            // characters = myChars;

            // Connect to WebSocket
            campaignChat.connect(campaignId);
        } catch (err) {
            console.error("Failed to load chat:", err);
        } finally {
            loading = false;
        }
    });

    onDestroy(() => {
        campaignChat.disconnect();
    });

    // Auto-scroll to bottom when messages change
    afterUpdate(() => {
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    });

    function handleSend(event) {
        const { content, characterId, isIc, diceExpression } = event.detail;
        campaignChat.sendMessage(content, characterId, isIc, diceExpression);
    }
</script>

<div class="flex flex-col h-[calc(100vh-4rem)] bg-gray-900">
    <!-- Header -->
    <div
        class="bg-gray-800 border-b border-gray-700 p-4 flex justify-between items-center shadow-md z-10"
    >
        <div class="flex items-center gap-3">
            <h2 class="text-xl font-bold text-white">Campaign Chat</h2>
            <div
                class="flex items-center gap-2 text-sm px-3 py-1 rounded-full {isConnected
                    ? 'bg-green-900/50 text-green-400'
                    : 'bg-red-900/50 text-red-400'}"
            >
                <span
                    class="w-2 h-2 rounded-full {isConnected
                        ? 'bg-green-500'
                        : 'bg-red-500'}"
                />
                {isConnected ? "Connected" : "Disconnected"}
            </div>
        </div>

        <div class="text-sm text-gray-400">
            {users.length} user{users.length !== 1 ? "s" : ""} online
        </div>
    </div>

    <!-- Messages Area -->
    <div
        bind:this={chatContainer}
        class="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth"
    >
        {#if loading}
            <div class="flex justify-center items-center h-full text-gray-500">
                Loading messages...
            </div>
        {:else if messages.length === 0}
            <div class="flex justify-center items-center h-full text-gray-500">
                No messages yet. Start the conversation!
            </div>
        {:else}
            {#each messages as msg (msg.id || msg.created_at)}
                <ChatMessage
                    message={msg}
                    isOwnMessage={currentUser && msg.user_id === currentUser.id}
                />
            {/each}
        {/if}

        {#if error}
            <div
                class="bg-red-900/50 border border-red-500 text-red-200 p-3 rounded-lg mx-4 mb-4"
            >
                Error: {error}
            </div>
        {/if}
    </div>

    <!-- Input Area -->
    <ChatInput {characters} on:send={handleSend} />
</div>
