<script>
    import { onMount } from "svelte";
    import { API_URL } from "../../lib/config";

    let users = [];
    let error = "";

    onMount(async () => {
        try {
            const token = localStorage.getItem("token");
            const res = await fetch(`${API_URL}/admin/users`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (!res.ok) throw new Error("Failed to fetch users");

            users = await res.json();
        } catch (e) {
            error = e.message;
        }
    });
</script>

<h2 class="text-3xl font-bold mb-6">User Management</h2>

{#if error}
    <div class="bg-red-500 text-white p-4 rounded mb-4">{error}</div>
{/if}

<div
    class="bg-gray-800 rounded-lg shadow-lg border border-gray-700 overflow-hidden"
>
    <table class="w-full text-left">
        <thead class="bg-gray-700 text-gray-300 uppercase text-sm">
            <tr>
                <th class="py-3 px-6">Username</th>
                <th class="py-3 px-6">Email</th>
                <th class="py-3 px-6">Role</th>
                <th class="py-3 px-6">Created At</th>
            </tr>
        </thead>
        <tbody class="text-gray-300">
            {#each users as user}
                <tr class="border-b border-gray-700 hover:bg-gray-750">
                    <td class="py-4 px-6 font-medium text-white"
                        >{user.username}</td
                    >
                    <td class="py-4 px-6">{user.email}</td>
                    <td class="py-4 px-6">
                        {#if user.is_admin}
                            <span
                                class="bg-purple-600 text-white py-1 px-3 rounded-full text-xs"
                                >Admin</span
                            >
                        {:else}
                            <span
                                class="bg-gray-600 text-white py-1 px-3 rounded-full text-xs"
                                >User</span
                            >
                        {/if}
                    </td>
                    <td class="py-4 px-6"
                        >{new Date(user.created_at).toLocaleDateString()}</td
                    >
                </tr>
            {/each}
        </tbody>
    </table>
</div>
