<script>
    import { createEventDispatcher } from "svelte";

    const dispatch = createEventDispatcher();

    export let characters = [];

    let content = "";
    let isIc = true;
    let selectedCharacterId = "";
    let diceExpression = "";
    let showDiceInput = false;

    function handleSubmit() {
        if (!content.trim()) return;

        dispatch("send", {
            content,
            characterId: selectedCharacterId || null,
            isIc,
            diceExpression: diceExpression.trim() || null,
        });

        content = "";
        diceExpression = "";
        showDiceInput = false;
    }

    function handleKeydown(e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    }
</script>

<div class="bg-gray-800 p-4 border-t border-gray-700">
    <div class="flex flex-col gap-3">
        <!-- Controls -->
        <div class="flex items-center gap-4 text-sm">
            <label class="flex items-center gap-2 cursor-pointer">
                <input
                    type="checkbox"
                    bind:checked={isIc}
                    class="form-checkbox rounded bg-gray-700 border-gray-600 text-indigo-500 focus:ring-indigo-500"
                />
                <span
                    class={isIc ? "text-amber-400 font-bold" : "text-gray-400"}
                >
                    {isIc ? "In-Character" : "Out-of-Character"}
                </span>
            </label>

            {#if characters.length > 0 && isIc}
                <select
                    bind:value={selectedCharacterId}
                    class="bg-gray-700 border-gray-600 rounded px-2 py-1 text-white text-sm focus:ring-indigo-500 focus:border-indigo-500"
                >
                    <option value="">Select Character...</option>
                    {#each characters as char}
                        <option value={char.id}>{char.name}</option>
                    {/each}
                </select>
            {/if}

            <button
                class="ml-auto flex items-center gap-1 text-gray-400 hover:text-white transition-colors {showDiceInput
                    ? 'text-indigo-400'
                    : ''}"
                on:click={() => (showDiceInput = !showDiceInput)}
            >
                <span>🎲</span>
                <span>Roll Dice</span>
            </button>
        </div>

        <!-- Dice Input -->
        {#if showDiceInput}
            <div class="flex items-center gap-2 bg-gray-900/50 p-2 rounded">
                <span class="text-gray-400 text-sm">Expression:</span>
                <input
                    type="text"
                    bind:value={diceExpression}
                    placeholder="e.g. 1d20+5"
                    class="bg-transparent border-none text-white text-sm focus:ring-0 w-full font-mono"
                />
            </div>
        {/if}

        <!-- Message Input -->
        <div class="flex gap-2">
            <textarea
                bind:value={content}
                on:keydown={handleKeydown}
                placeholder={isIc
                    ? "What does your character do?"
                    : "Type a message..."}
                rows="2"
                class="flex-1 bg-gray-700 border-gray-600 rounded-lg text-white placeholder-gray-400 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
            />

            <button
                on:click={handleSubmit}
                disabled={!content.trim()}
                class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors self-end"
            >
                Send
            </button>
        </div>
    </div>
</div>
