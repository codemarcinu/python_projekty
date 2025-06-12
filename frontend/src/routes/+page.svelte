<script lang="ts">
  import Chat from '$lib/components/Chat.svelte';
  import { chatStore } from '$lib/stores/chat';
  import { onMount } from 'svelte';

  onMount(() => {
    // Create initial conversation if none exists
    if ($chatStore.conversations.length === 0) {
      chatStore.createConversation('New Conversation');
    }
  });
</script>

<main class="container mx-auto max-w-4xl h-screen">
  <Chat />
</main>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
  }
</style>
