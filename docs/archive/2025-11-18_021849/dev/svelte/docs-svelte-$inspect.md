<!-- Source: https://svelte.dev/docs/svelte/$inspect -->

[Skip to main content](#main)

Docs

[Docs](/docs)

[Svelte](/docs/svelte)[SvelteKit](/docs/kit)[CLI](/docs/cli)[MCP](/docs/mcp)

[Tutorial](/tutorial)[Packages](/packages)[Playground](/playground)[Blog](/blog)

* ### Introduction

  + [Overview](/docs/svelte/overview)
  + [Getting started](/docs/svelte/getting-started)
  + [.svelte files](/docs/svelte/svelte-files)
  + [.svelte.js and .svelte.ts files](/docs/svelte/svelte-js-files)
* ### Runes

  + [What are runes?](/docs/svelte/what-are-runes)
  + [$state](/docs/svelte/%24state)
  + [$derived](/docs/svelte/%24derived)
  + [$effect](/docs/svelte/%24effect)
  + [$props](/docs/svelte/%24props)
  + [$bindable](/docs/svelte/%24bindable)
  + [$inspect](/docs/svelte/%24inspect)
  + [$host](/docs/svelte/%24host)
* ### Template syntax

  + [Basic markup](/docs/svelte/basic-markup)
  + [{#if ...}](/docs/svelte/if)
  + [{#each ...}](/docs/svelte/each)
  + [{#key ...}](/docs/svelte/key)
  + [{#await ...}](/docs/svelte/await)
  + [{#snippet ...}](/docs/svelte/snippet)
  + [{@render ...}](/docs/svelte/%40render)
  + [{@html ...}](/docs/svelte/%40html)
  + [{@attach ...}](/docs/svelte/%40attach)
  + [{@const ...}](/docs/svelte/%40const)
  + [{@debug ...}](/docs/svelte/%40debug)
  + [bind:](/docs/svelte/bind)
  + [use:](/docs/svelte/use)
  + [transition:](/docs/svelte/transition)
  + [in: and out:](/docs/svelte/in-and-out)
  + [animate:](/docs/svelte/animate)
  + [style:](/docs/svelte/style)
  + [class](/docs/svelte/class)
  + [await](/docs/svelte/await-expressions)
* ### Styling

  + [Scoped styles](/docs/svelte/scoped-styles)
  + [Global styles](/docs/svelte/global-styles)
  + [Custom properties](/docs/svelte/custom-properties)
  + [Nested <style> elements](/docs/svelte/nested-style-elements)
* ### Special elements

  + [<svelte:boundary>](/docs/svelte/svelte-boundary)
  + [<svelte:window>](/docs/svelte/svelte-window)
  + [<svelte:document>](/docs/svelte/svelte-document)
  + [<svelte:body>](/docs/svelte/svelte-body)
  + [<svelte:head>](/docs/svelte/svelte-head)
  + [<svelte:element>](/docs/svelte/svelte-element)
  + [<svelte:options>](/docs/svelte/svelte-options)
* ### Runtime

  + [Stores](/docs/svelte/stores)
  + [Context](/docs/svelte/context)
  + [Lifecycle hooks](/docs/svelte/lifecycle-hooks)
  + [Imperative component API](/docs/svelte/imperative-component-api)
* ### Misc

  + [Testing](/docs/svelte/testing)
  + [TypeScript](/docs/svelte/typescript)
  + [Custom elements](/docs/svelte/custom-elements)
  + [Svelte 4 migration guide](/docs/svelte/v4-migration-guide)
  + [Svelte 5 migration guide](/docs/svelte/v5-migration-guide)
  + [Frequently asked questions](/docs/svelte/faq)
* ### Reference

  + [svelte](/docs/svelte/svelte)
  + [svelte/action](/docs/svelte/svelte-action)
  + [svelte/animate](/docs/svelte/svelte-animate)
  + [svelte/attachments](/docs/svelte/svelte-attachments)
  + [svelte/compiler](/docs/svelte/svelte-compiler)
  + [svelte/easing](/docs/svelte/svelte-easing)
  + [svelte/events](/docs/svelte/svelte-events)
  + [svelte/legacy](/docs/svelte/svelte-legacy)
  + [svelte/motion](/docs/svelte/svelte-motion)
  + [svelte/reactivity/window](/docs/svelte/svelte-reactivity-window)
  + [svelte/reactivity](/docs/svelte/svelte-reactivity)
  + [svelte/server](/docs/svelte/svelte-server)
  + [svelte/store](/docs/svelte/svelte-store)
  + [svelte/transition](/docs/svelte/svelte-transition)
  + [Compiler errors](/docs/svelte/compiler-errors)
  + [Compiler warnings](/docs/svelte/compiler-warnings)
  + [Runtime errors](/docs/svelte/runtime-errors)
  + [Runtime warnings](/docs/svelte/runtime-warnings)
* ### Legacy APIs

  + [Overview](/docs/svelte/legacy-overview)
  + [Reactive let/var declarations](/docs/svelte/legacy-let)
  + [Reactive $: statements](/docs/svelte/legacy-reactive-assignments)
  + [export let](/docs/svelte/legacy-export-let)
  + [$$props and $$restProps](/docs/svelte/legacy-%24%24props-and-%24%24restProps)
  + [on:](/docs/svelte/legacy-on)
  + [<slot>](/docs/svelte/legacy-slots)
  + [$$slots](/docs/svelte/legacy-%24%24slots)
  + [<svelte:fragment>](/docs/svelte/legacy-svelte-fragment)
  + [<svelte:component>](/docs/svelte/legacy-svelte-component)
  + [<svelte:self>](/docs/svelte/legacy-svelte-self)
  + [Imperative component API](/docs/svelte/legacy-component-api)

SvelteRunes

# $inspect

 [ ]

### On this page

* [$inspect](/docs/svelte/%24inspect)
* [$inspect(...).with](#$inspect().with)
* [$inspect.trace(...)](#$inspect.trace())

> `$inspect` only works during development. In a production build it becomes a noop.

The `$inspect` rune is roughly equivalent to `console.log`, with the exception that it will re-run whenever its argument changes. `$inspect` tracks reactive state deeply, meaning that updating something inside an object or array using fine-grained reactivity will cause it to re-fire ([demo](/playground/untitled#H4sIAAAAAAAACkWQ0YqDQAxFfyUMhSotdZ-tCvu431AXtGOqQ2NmmMm0LOK_r7Utfby5JzeXTOpiCIPKT5PidkSVq2_n1F7Jn3uIcEMSXHSw0evHpAjaGydVzbUQCmgbWaCETZBWMPlKj29nxBDaHj_edkAiu12JhdkYDg61JGvE_s2nR8gyuBuiJZuDJTyQ7eE-IEOzog1YD80Lb0APLfdYc5F9qnFxjiKWwbImo6_llKRQVs-2u91c_bD2OCJLkT3JZasw7KLA2XCX31qKWE6vIzNk1fKE0XbmYrBTufiI8-_8D2cUWBA_AQAA)):

```
<script>
	let count = $state(0);
	let message = $state('hello');

	$inspect(count, message); // will console.log when `count` or `message` change
</script>

<button onclick={() => count++}>Increment</button>
<input bind:value={message} />
```

On updates, a stack trace will be printed, making it easy to find the origin of a state change (unless you’re in the playground, due to technical limitations).

## $inspect(...).with

`$inspect` returns a property `with`, which you can invoke with a callback, which will then be invoked instead of `console.log`. The first argument to the callback is either `"init"` or `"update"`; subsequent arguments are the values passed to `$inspect` ([demo](/playground/untitled#H4sIAAAAAAAACkVQ24qDMBD9lSEUqlTqPlsj7ON-w7pQG8c2VCchmVSK-O-bKMs-DefKYRYx6BG9qL4XQd2EohKf1opC8Nsm4F84MkbsTXAqMbVXTltuWmp5RAZlAjFIOHjuGLOP_BKVqB00eYuKs82Qn2fNjyxLtcWeyUE2sCRry3qATQIpJRyD7WPVMf9TW-7xFu53dBcoSzAOrsqQNyOe2XUKr0Xi5kcMvdDB2wSYO-I9vKazplV1-T-d6ltgNgSG1KjVUy7ZtmdbdjqtzRcphxMS1-XubOITJtPrQWMvKnYB15_1F7KKadA_AQAA)):

```
<script>
	let count = $state(0);

	$inspect(count).with((type, count) => {
		if (type === 'update') {
			debugger; // or `console.trace`, or whatever you want
		}
	});
</script>

<button onclick={() => count++}>Increment</button>
```

## $inspect.trace(...)

This rune, added in 5.14, causes the surrounding function to be *traced* in development. Any time the function re-runs as part of an [effect](%24effect) or a [derived](%24derived), information will be printed to the console about which pieces of reactive state caused the effect to fire.

```
<script>
	import { doSomeWork } from './elsewhere';

	$effect(() => {
		// $inspect.trace must be the first statement of a function body
		$inspect.trace();
		doSomeWork();
	});
</script>
```

`$inspect.trace` takes an optional first argument which will be used as the label.

[Edit this page on GitHub](https://github.com/sveltejs/svelte/edit/main/documentation/docs/02-runes/07-%24inspect.md)  [llms.txt](/docs/svelte/%24inspect/llms.txt)

previous next

[$bindable](/docs/svelte/%24bindable) [$host](/docs/svelte/%24host)