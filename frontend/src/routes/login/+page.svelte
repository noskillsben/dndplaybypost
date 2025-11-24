<script>
  import { goto } from "$app/navigation";
  import { auth } from "../../stores/auth";

  let username = "";
  let password = "";
  let error = "";

  async function handleLogin() {
    error = "";
    try {
      const res = await fetch("http://localhost:8000/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Login failed");
      }

      // Store token
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("is_admin", data.is_admin);

      // Update store
      auth.set({
        isAuthenticated: true,
        isAdmin: data.is_admin,
        user: null,
      });

      // Redirect
      if (data.is_admin) {
        goto("/admin");
      } else {
        goto("/");
      }
    } catch (e) {
      error = e.message;
    }
  }
</script>

<div class="max-w-md mx-auto mt-10 bg-gray-800 p-6 rounded-lg shadow-lg">
  <h2 class="text-2xl font-bold mb-6 text-purple-400">Login</h2>

  {#if error}
    <div class="bg-red-900 text-red-200 p-3 rounded mb-4">{error}</div>
  {/if}

  <form on:submit|preventDefault={handleLogin} class="space-y-4">
    <div>
      <label class="block text-gray-400 mb-1">Username</label>
      <input
        type="text"
        bind:value={username}
        class="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
        required
      />
    </div>

    <div>
      <label class="block text-gray-400 mb-1">Password</label>
      <input
        type="password"
        bind:value={password}
        class="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
        required
      />
    </div>

    <button
      type="submit"
      class="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded transition duration-200"
    >
      Login
    </button>
  </form>
</div>
