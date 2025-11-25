<script>
    import { onMount } from "svelte";
    import { API_URL } from "../../lib/config";

    let stats = { user_count: 0, campaign_count: 0 };
    let error = "";

    onMount(async () => {
        try {
            const token = localStorage.getItem("token");
            const res = await fetch(`${API_URL}/admin/stats`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (!res.ok) throw new Error("Failed to fetch stats");

            stats = await res.json();
        } catch (e) {
            error = e.message;
        }
    });
</script>

<h2 class="text-3xl font-bold mb-6">Dashboard Overview</h2>

{#if error}
    <div class="bg-red-500 text-white p-4 rounded mb-4">{error}</div>
{/if}

<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    <!-- User Count Card -->
    <div class="bg-gray-800 p-6 rounded-lg shadow-lg border border-gray-700">
        <h3 class="text-gray-400 text-sm font-medium uppercase">Total Users</h3>
        <p class="text-3xl font-bold text-white mt-2">{stats.user_count}</p>
    </div>

    <!-- Campaign Count Card -->
    <div class="bg-gray-800 p-6 rounded-lg shadow-lg border border-gray-700">
        <h3 class="text-gray-400 text-sm font-medium uppercase">
            Active Campaigns
        </h3>
        <p class="text-3xl font-bold text-white mt-2">{stats.campaign_count}</p>
    </div>
</div>
