<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { userStore } from '$lib/stores/user';
  import { page } from '$app/stores';

  onMount(async () => {
    await userStore.checkAuth();
  });

  $: if ($userStore.isAuthenticated && $page.url.pathname === '/login') {
    goto('/chat');
  }
</script>

{#if $userStore.isLoading}
  <div class="min-h-screen flex items-center justify-center">
    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
  </div>
{:else if !$userStore.isAuthenticated && $page.url.pathname !== '/login' && $page.url.pathname !== '/register'}
  <div class="min-h-screen flex items-center justify-center">
    <div class="text-center">
      <h1 class="text-2xl font-bold text-gray-900 mb-4">Please sign in to continue</h1>
      <a
        href="/login"
        class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
      >
        Sign in
      </a>
    </div>
  </div>
{:else}
  <slot />
{/if} 