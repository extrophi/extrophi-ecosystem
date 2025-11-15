<!-- Source: https://svelte.dev/docs/svelte/$bindable -->

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

# $bindable

 [ ]

### On this page

* [$bindable](/docs/svelte/%24bindable)

Ordinarily, props go one way, from parent to child. This makes it easy to understand how data flows around your app.

In Svelte, component props can be *bound*, which means that data can also flow *up* from child to parent. This isn’t something you should do often, but it can simplify your code if used sparingly and carefully.

It also means that a state proxy can be *mutated* in the child.

> Mutation is also possible with normal props, but is strongly discouraged — Svelte will warn you if it detects that a component is mutating state it does not ‘own’.

To mark a prop as bindable, we use the `$bindable` rune:

FancyInput[x]

```
<script>
	let { value = $bindable(), ...props } = $props();
</script>

<input bind:value={value} {...props} />

<style>
	input {
		font-family: 'Comic Sans MS';
		color: deeppink;
	}
</style>
```

```
<script lang="ts">
	let { value = $bindable(), ...props } = $props();
</script>

<input bind:value={value} {...props} />

<style>
	input {
		font-family: 'Comic Sans MS';
		color: deeppink;
	}
</style>
```

Now, a component that uses `<FancyInput>` can add the [`bind:`](bind) directive ([demo](/playground/untitled#H4sIAAAAAAAAE3WQwWrDMBBEf2URBSfg2nfFMZRCoYeecqx6UJx1IyqvhLUONcb_XqSkTUOSk1az7DBvJtEai0HI90nw6FHIJIhckO7i78n7IhzQctS2OuAtvXHESByEFFVoeuO5VqTYdN71DC-amvGV_MDQ9q6DrCjP0skkWymKJxYZOgxBfyKs4SGwZlxke7TWZcuVoqo8-1P1z3lraCcP2g64nk4GM5S1osrXf0JV-lrkgvGbheR-wDm_g30V8JL-1vpOCZFogpQsEsWcemtxscyhKArfOx9gjps0Lq4hzRVfemaYfu-PoIqqwKPFY_XpaIqj4tYRP7a6M3aUkD27zjSw0RTgbZN6Z8WNs66XsEP03tBXUueUJFlelvYx_wCuI3leNwIAAA==)):

App[x]

```
<script>
	import FancyInput from './FancyInput.svelte';

	let message = $state('hello');
</script>

<FancyInput bind:value={message} />
<p>{message}</p>
```

```
<script lang="ts">
	import FancyInput from './FancyInput.svelte';

	let message = $state('hello');
</script>

<FancyInput bind:value={message} />
<p>{message}</p>
```

The parent component doesn’t *have* to use `bind:` — it can just pass a normal prop. Some parents don’t want to listen to what their children have to say.

In this case, you can specify a fallback value for when no prop is passed at all:

FancyInput

```
let { let value: anyvalue =

```
function $bindable<"fallback">(fallback?: "fallback" | undefined): "fallback"
namespace $bindable
```

Declares a prop as bindable, meaning the parent component can use bind:propName={value} to bind to it.

```
let { propName = $bindable() }: { propName: boolean } = $props();
```

https://svelte.dev/docs/svelte/$bindable

$bindable('fallback'), ...let props: anyprops } =

```
function $props(): any
namespace $props
```

Declares the props that a component accepts. Example:

```
let { optionalProp = 42, requiredProp, bindableProp = $bindable() }: { optionalProp?: number; requiredProps: string; bindableProp: boolean } = $props();
```

https://svelte.dev/docs/svelte/$props

$props();
```

[Edit this page on GitHub](https://github.com/sveltejs/svelte/edit/main/documentation/docs/02-runes/06-%24bindable.md)  [llms.txt](/docs/svelte/%24bindable/llms.txt)

previous next

[$props](/docs/svelte/%24props) [$inspect](/docs/svelte/%24inspect)