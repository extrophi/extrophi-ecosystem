<!-- Source: https://svelte.dev/docs/svelte/overview -->

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

SvelteIntroduction

# Overview

 [ ]

### On this page

* [Overview](/docs/svelte/overview)

Svelte is a framework for building user interfaces on the web. It uses a compiler to turn declarative components written in HTML, CSS and JavaScript...

App[x]

```
<script>
	function greet() {
		alert('Welcome to Svelte!');
	}
</script>

<button onclick={greet}>click me</button>

<style>
	button {
		font-size: 2em;
	}
</style>
```

```
<script lang="ts">
	function greet() {
		alert('Welcome to Svelte!');
	}
</script>

<button onclick={greet}>click me</button>

<style>
	button {
		font-size: 2em;
	}
</style>
```

...into lean, tightly optimized JavaScript.

You can use it to build anything on the web, from standalone components to ambitious full stack apps (using Svelte’s companion application framework, [SvelteKit](../kit)) and everything in between.

These pages serve as reference documentation. If you’re new to Svelte, we recommend starting with the [interactive tutorial](/tutorial) and coming back here when you have questions.

You can also try Svelte online in the [playground](/playground) or, if you need a more fully-featured environment, on [StackBlitz](https://sveltekit.new).

[Edit this page on GitHub](https://github.com/sveltejs/svelte/edit/main/documentation/docs/01-introduction/01-overview.md)  [llms.txt](/docs/svelte/overview/llms.txt)

previous next

[Getting started](/docs/svelte/getting-started)