<script lang="ts">
  import { onMount } from 'svelte';
  import { userStore } from '$lib/stores/user';
  import '../app.css';
  import Navbar from '$lib/components/layout/Navbar.svelte';
  import Sidebar from '$lib/components/layout/Sidebar.svelte';
</script>

<svelte:head>
  <title>AI Chat</title>
  <meta name="description" content="AI Chat application with local LLM models" />
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
  <Navbar />
  <div class="flex">
    <Sidebar />
    <main class="flex-1 ml-64 p-4">
      <slot />
    </main>
  </div>
</div> 