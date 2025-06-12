<script lang="ts">
  import '../app.css';
  import Navbar from '$lib/components/layout/Navbar.svelte';
  import Sidebar from '$lib/components/layout/Sidebar.svelte';
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
  <Navbar />
  <div class="flex">
    <Sidebar />
    <main class="flex-1 ml-64 p-4">
      <slot />
    </main>
  </div>
</div> 