<script>
  // Svelte 5 runes syntax
  let count = $state(0);

  function increment() {
    count += 1;
  }

  function decrement() {
    count -= 1;
  }

  function reset() {
    count = 0;
  }
</script>

<div class="flex items-center gap-4 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg">
  <button
    onclick={decrement}
    class="px-4 py-2 bg-red-500 hover:bg-red-600 text-white font-semibold rounded-lg transition-colors"
  >
    -
  </button>

  <div class="flex flex-col items-center min-w-[120px]">
    <span class="text-3xl font-bold text-gray-800 dark:text-gray-100">
      {count}
    </span>
    <span class="text-xs text-gray-500 dark:text-gray-400 mt-1">
      Using Svelte 5 $state
    </span>
  </div>

  <button
    onclick={increment}
    class="px-4 py-2 bg-green-500 hover:bg-green-600 text-white font-semibold rounded-lg transition-colors"
  >
    +
  </button>

  <button
    onclick={reset}
    class="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white font-semibold rounded-lg transition-colors"
  >
    Reset
  </button>
</div>
