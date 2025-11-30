<script>
    export let message;
    export let isOwnMessage = false;

    function formatTime(isoString) {
        return new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
</script>

<div class="flex flex-col mb-4 {isOwnMessage ? 'items-end' : 'items-start'}">
    <div class="flex items-baseline gap-2 mb-1">
        <span class="font-bold text-sm {message.is_ic ? 'text-amber-400' : 'text-gray-400'}">
            {message.character_id ? 'Character Name' : message.username}
        </span>
        <span class="text-xs text-gray-500">{formatTime(message.created_at)}</span>
    </div>

    <div class="max-w-[80%] rounded-lg p-3 {isOwnMessage ? 'bg-indigo-600 text-white' : 'bg-gray-700 text-gray-100'} {message.is_ic ? 'border-l-4 border-amber-500' : ''}">
        <p class="whitespace-pre-wrap">{message.content}</p>

        {#if message.extra_data && message.extra_data.dice_roll}
            <div class="mt-2 pt-2 border-t border-white/20 text-sm font-mono">
                <div class="flex items-center gap-2">
                    <span class="text-xs uppercase opacity-75">Rolling:</span>
                    <span class="font-bold">{message.extra_data.dice_roll.expression}</span>
                </div>
                <div class="mt-1">
                    <span class="opacity-75">{message.extra_data.dice_roll.breakdown}</span>
                </div>
            </div>
        {/if}
    </div>
</div>
