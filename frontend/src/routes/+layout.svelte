<script>
  import '../app.css';
</script>

<div class="min-h-screen bg-gray-900 text-gray-100 font-sans">
  <nav class="p-4 bg-gray-800 border-b border-gray-700 flex justify-between items-center">
    <a href="/" class="text-xl font-bold text-purple-400">D&D PBP</a>
    <div class="space-x-4">
      <a href="/login" class="hover:text-white">Login</a>
      <a href="/register" class="hover:text-white">Register</a>
    </div>
  </nav>
  <main class="container mx-auto p-4">
    <slot />
  </main>
</div>
