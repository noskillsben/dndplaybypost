<script>
    import { onMount } from "svelte";
    import { goto } from "$app/navigation";
    import "../../app.css";

    let is_admin = false;
    let loaded = false;

    onMount(() => {
        const token = localStorage.getItem("token");
        is_admin = localStorage.getItem("is_admin") === "true";

        if (!token || !is_admin) {
            goto("/login");
        }
        loaded = true;
    });
</script>

{#if loaded}
    <div class="flex h-screen bg-gray-900 text-gray-100">
        <!-- Sidebar -->
        <aside class="w-64 bg-gray-800 border-r border-gray-700">
            <div class="p-4">
                <h1 class="text-xl font-bold text-purple-400">Admin Panel</h1>
            </div>
            <nav class="mt-4">
                <a
                    href="/admin"
                    class="block py-2.5 px-4 rounded transition duration-200 hover:bg-gray-700 hover:text-white"
                >
                    Dashboard
                </a>
                <a
                    href="/admin/users"
                    class="block py-2.5 px-4 rounded transition duration-200 hover:bg-gray-700 hover:text-white"
                >
                    Users
                </a>
                <a
                    href="/"
                    class="block py-2.5 px-4 rounded transition duration-200 hover:bg-gray-700 hover:text-white mt-8 border-t border-gray-700 pt-4"
                >
                    Back to Site
                </a>
            </nav>
        </aside>

        <!-- Main Content -->
        <main class="flex-1 p-8 overflow-y-auto">
            <slot />
        </main>
    </div>
{/if}
