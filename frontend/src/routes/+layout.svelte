<script>
  import "../app.css";
  import { onMount } from "svelte";
  import { auth } from "../stores/auth";
  import { goto } from "$app/navigation";

  onMount(() => {
    const token = localStorage.getItem("token");
    const is_admin = localStorage.getItem("is_admin") === "true";

    if (token) {
      auth.set({
        isAuthenticated: true,
        isAdmin: is_admin,
        user: null, // We could decode the token here if needed
      });
    }
  });

  function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("is_admin");
    auth.set({ isAuthenticated: false, isAdmin: false, user: null });
    goto("/login");
  }
</script>

<div class="min-h-screen bg-gray-900 text-gray-100 font-sans">
  <nav
    class="p-4 bg-gray-800 border-b border-gray-700 flex justify-between items-center"
  >
    <a href="/" class="text-xl font-bold text-purple-400">D&D PBP</a>
    <div class="space-x-4">
      {#if $auth.isAuthenticated}
        {#if $auth.isAdmin}
          <a href="/admin" class="hover:text-white">Admin Dashboard</a>
        {/if}
        <button on:click={logout} class="hover:text-white">Logout</button>
      {:else}
        <a href="/login" class="hover:text-white">Login</a>
        <a href="/register" class="hover:text-white">Register</a>
      {/if}
    </div>
  </nav>
  <main class="container mx-auto p-4">
    <slot />
  </main>
</div>
