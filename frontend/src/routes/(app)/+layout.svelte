<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import { userStore } from '$lib/stores/user';
  import { ws } from '$lib/services/websocket';

  onMount(() => {
    if (!$userStore.isAuthenticated) {
      goto('/login');
    } else {
      ws.connect();
    }
  });

  onDestroy(() => {
    ws.disconnect();
  });

  function handleLogout() {
    userStore.logout();
    goto('/login');
  }
</script>

<div class="min-h-screen bg-gray-100">
  <nav class="bg-white shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16">
        <div class="flex">
          <div class="flex-shrink-0 flex items-center">
            <h1 class="text-xl font-bold text-indigo-600">AI Chat</h1>
          </div>
        </div>
        <div class="flex items-center">
          <span class="text-gray-700 mr-4">{$userStore.user?.username}</span>
          <button
            on:click={handleLogout}
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  </nav>

  <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
    <slot />
  </main>
</div> 