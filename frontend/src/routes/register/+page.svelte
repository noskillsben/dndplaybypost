<script>
  import { goto } from "$app/navigation";
  import { auth } from "$lib/stores/auth";
  import { API_URL } from "$lib/config";

  let username = "";
  let email = "";
  let password = "";
  let confirmPassword = "";
  let error = "";
  let message = "";

  async function handleRegister() {
    error = "";

    // Validate passwords match
    if (password !== confirmPassword) {
      error = "Passwords do not match";
      return;
    }

    try {
      const res = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Registration failed");
      }

      message = "Registration successful! You can now login.";
      if (data.is_admin) {
        message += " You have been assigned ADMIN privileges.";
      }
    } catch (e) {
      error = e.message;
    }
  }
</script>

<div class="max-w-md mx-auto mt-10 bg-gray-800 p-6 rounded-lg shadow-lg">
  <h2 class="text-2xl font-bold mb-6 text-purple-400">Register</h2>

  {#if error}
    <div class="bg-red-900 text-red-200 p-3 rounded mb-4">{error}</div>
  {/if}

  {#if message}
    <div class="bg-green-900 text-green-200 p-3 rounded mb-4">{message}</div>
  {/if}

  <form on:submit|preventDefault={handleRegister} class="space-y-4">
    <div>
      <label for="username" class="block text-gray-400 mb-1">Username</label>
      <input
        id="username"
        type="text"
        bind:value={username}
        class="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
        required
      />
    </div>

    <div>
      <label for="email" class="block text-gray-400 mb-1">Email</label>
      <input
        id="email"
        type="email"
        bind:value={email}
        class="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
        required
      />
    </div>

    <div>
      <label for="password" class="block text-gray-400 mb-1">Password</label>
      <input
        id="password"
        type="password"
        bind:value={password}
        class="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
        required
      />
    </div>

    <div>
      <label for="confirmPassword" class="block text-gray-400 mb-1">Retype Password</label>
      <input
        id="confirmPassword"
        type="password"
        bind:value={confirmPassword}
        class="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
        required
      />
    </div>

    <button
      type="submit"
      class="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded transition duration-200"
    >
      Register
    </button>
  </form>
</div>
