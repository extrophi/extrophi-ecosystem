<script>
  // Svelte 5 props using runes
  let { title, description, children } = $props();
</script>

<div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
  <h3 class="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-2">
    {title}
  </h3>
  {#if description}
    <p class="text-gray-600 dark:text-gray-300 mb-4">
      {description}
    </p>
  {/if}
  {#if children}
    <div class="mt-4">
      {@render children()}
    </div>
  {/if}
</div>
