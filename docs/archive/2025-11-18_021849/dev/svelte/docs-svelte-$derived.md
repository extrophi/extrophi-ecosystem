<!-- Source: https://svelte.dev/docs/svelte/$derived -->

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

# $derived

 [ ]

### On this page

* [$derived](/docs/svelte/%24derived)
* [$derived.by](#$derived.by)
* [Understanding dependencies](#Understanding-dependencies)
* [Overriding derived values](#Overriding-derived-values)
* [Deriveds and reactivity](#Deriveds-and-reactivity)
* [Destructuring](#Destructuring)
* [Update propagation](#Update-propagation)

Derived state is declared with the `$derived` rune:

```
<script>
	let count = $state(0);
	let doubled = $derived(count * 2);
</script>

<button onclick={() => count++}>
	{doubled}
</button>

<p>{count} doubled is {doubled}</p>
```

The expression inside `$derived(...)` should be free of side-effects. Svelte will disallow state changes (e.g. `count++`) inside derived expressions.

As with `$state`, you can mark class fields as `$derived`.

> Code in Svelte components is only executed once at creation. Without the `$derived` rune, `doubled` would maintain its original value even when `count` changes.

## $derived.by

Sometimes you need to create complex derivations that don’t fit inside a short expression. In these cases, you can use `$derived.by` which accepts a function as its argument.

```
<script>
	let numbers = $state([1, 2, 3]);
	let total = $derived.by(() => {
		let total = 0;
		for (const n of numbers) {
			total += n;
		}
		return total;
	});
</script>

<button onclick={() => numbers.push(numbers.length + 1)}>
	{numbers.join(' + ')} = {total}
</button>
```

In essence, `$derived(expression)` is equivalent to `$derived.by(() => expression)`.

## Understanding dependencies

Anything read synchronously inside the `$derived` expression (or `$derived.by` function body) is considered a *dependency* of the derived state. When the state changes, the derived will be marked as *dirty* and recalculated when it is next read.

To exempt a piece of state from being treated as a dependency, use [`untrack`](svelte#untrack).

## Overriding derived values

Derived expressions are recalculated when their dependencies change, but you can temporarily override their values by reassigning them (unless they are declared with `const`). This can be useful for things like *optimistic UI*, where a value is derived from the ‘source of truth’ (such as data from your server) but you’d like to show immediate feedback to the user:

```
<script>
	let { post, like } = $props();

	let likes = $derived(post.likes);

	async function onclick() {
		// increment the `likes` count immediately...
		likes += 1;

		// and tell the server, which will eventually update `post`
		try {
			await like();
		} catch {
			// failed! roll back the change
			likes -= 1;
		}
	}
</script>

<button {onclick}>🧡 {likes}</button>
```

> Prior to Svelte 5.25, deriveds were read-only.

## Deriveds and reactivity

Unlike `$state`, which converts objects and arrays to [deeply reactive proxies](%24state#Deep-state), `$derived` values are left as-is. For example, [in a case like this](/playground/untitled#H4sIAAAAAAAAE4VU22rjMBD9lUHd3aaQi9PdstS1A3t5XvpQ2Ic4D7I1iUUV2UjjNMX431eS7TRdSosxgjMzZ45mjt0yzffIYibvy0ojFJWqDKCQVBk2ZVup0LJ43TJ6rn2aBxw-FP2o67k9oCKP5dziW3hRaUJNjoYltjCyplWmM1JIIAn3FlL4ZIkTTtYez6jtj4w8WwyXv9GiIXiQxLVs9pfTMR7EuoSLIuLFbX7Z4930bZo_nBrD1bs834tlfvsBz9_SyX6PZXu9XaL4gOWn4sXjeyzftv4ZWfyxubpzxzg6LfD4MrooxELEosKCUPigQCMPKCZh0OtQE1iSxcsmdHuBvCiHZXALLXiN08EL3RRkaJ_kDVGle0HcSD5TPEeVtj67O4Nrg9aiSNtBY5oODJkrL5QsHtN2cgXp6nSJMWzpWWGasdlsGEMbzi5jPr5KFr0Ep7pdeM2-TCelCddIhDxAobi1jqF3cMaC1RKp64bAW9iFAmXGIHfd4wNXDabtOLN53w8W53VvJoZLh7xk4Rr3CoL-UNoLhWHrT1JQGcM17u96oES5K-kc2XOzkzqGCKL5De79OUTyyrg1zgwXsrEx3ESfx4Bz0M5UjVMHB24mw9SuXtXFoN13fYKOM1tyUT3FbvbWmSWCZX2Er-41u5xPoml45svRahl9Wb9aasbINJixDZwcPTbyTLZSUsAvrg_cPuCR7s782_WU8343Y72Qtlb8OYatwuOQvuN13M_hJKNfxann1v1U_B1KZ_D_mzhzhz24fw85CSz2irtN9w9HshBK7AQAAA==)...

```
let items =

```
function $state<never[]>(initial: never[]): never[] (+1 overload)
namespace $state
```

Declares reactive state.

Example:

```
let count = $state(0);
```

https://svelte.dev/docs/svelte/$state

@paraminitial The initial value

$state([ /*...*/ ]);

let let index: numberindex =

```
function $state<0>(initial: 0): 0 (+1 overload)
namespace $state
```

Declares reactive state.

Example:

```
let count = $state(0);
```

https://svelte.dev/docs/svelte/$state

@paraminitial The initial value

$state(0);
let let selected: anyselected =

```
function $derived<any>(expression: any): any
namespace $derived
```

Declares derived state, i.e. one that depends on other state variables.
The expression inside $derived(...) should be free of side-effects.

Example:

```
let double = $derived(count * 2);
```

https://svelte.dev/docs/svelte/$derived

@paramexpression The derived state expression

$derived(let items: any[]items[let index: numberindex]);
```

...you can change (or `bind:` to) properties of `selected` and it will affect the underlying `items` array. If `items` was *not* deeply reactive, mutating `selected` would have no effect.

## Destructuring

If you use destructuring with a `$derived` declaration, the resulting variables will all be reactive — this...

```
let { let a: numbera, let b: numberb, let c: numberc } =

```
function $derived<{
    a: number;
    b: number;
    c: number;
}>(expression: {
    a: number;
    b: number;
    c: number;
}): {
    a: number;
    b: number;
    c: number;
}
namespace $derived
```

Declares derived state, i.e. one that depends on other state variables.
The expression inside $derived(...) should be free of side-effects.

Example:

```
let double = $derived(count * 2);
```

https://svelte.dev/docs/svelte/$derived

@paramexpression The derived state expression

$derived(

```
function stuff(): {
    a: number;
    b: number;
    c: number;
}
```

stuff());
```

...is roughly equivalent to this:

```
let

```
let _stuff: {
    a: number;
    b: number;
    c: number;
}
```

_stuff =

```
function $derived<{
    a: number;
    b: number;
    c: number;
}>(expression: {
    a: number;
    b: number;
    c: number;
}): {
    a: number;
    b: number;
    c: number;
}
namespace $derived
```

Declares derived state, i.e. one that depends on other state variables.
The expression inside $derived(...) should be free of side-effects.

Example:

```
let double = $derived(count * 2);
```

https://svelte.dev/docs/svelte/$derived

@paramexpression The derived state expression

$derived(

```
function stuff(): {
    a: number;
    b: number;
    c: number;
}
```

stuff());
let let a: numbera =

```
function $derived<number>(expression: number): number
namespace $derived
```

Declares derived state, i.e. one that depends on other state variables.
The expression inside $derived(...) should be free of side-effects.

Example:

```
let double = $derived(count * 2);
```

https://svelte.dev/docs/svelte/$derived

@paramexpression The derived state expression

$derived(

```
let _stuff: {
    a: number;
    b: number;
    c: number;
}
```

_stuff.a: numbera);
let let b: numberb =

```
function $derived<number>(expression: number): number
namespace $derived
```

Declares derived state, i.e. one that depends on other state variables.
The expression inside $derived(...) should be free of side-effects.

Example:

```
let double = $derived(count * 2);
```

https://svelte.dev/docs/svelte/$derived

@paramexpression The derived state expression

$derived(

```
let _stuff: {
    a: number;
    b: number;
    c: number;
}
```

_stuff.b: numberb);
let let c: numberc =

```
function $derived<number>(expression: number): number
namespace $derived
```

Declares derived state, i.e. one that depends on other state variables.
The expression inside $derived(...) should be free of side-effects.

Example:

```
let double = $derived(count * 2);
```

https://svelte.dev/docs/svelte/$derived

@paramexpression The derived state expression

$derived(

```
let _stuff: {
    a: number;
    b: number;
    c: number;
}
```

_stuff.c: numberc);
```

## Update propagation

Svelte uses something called *push-pull reactivity* — when state is updated, everything that depends on the state (whether directly or indirectly) is immediately notified of the change (the ‘push’), but derived values are not re-evaluated until they are actually read (the ‘pull’).

If the new value of a derived is referentially identical to its previous value, downstream updates will be skipped. In other words, Svelte will only update the text inside the button when `large` changes, not when `count` changes, even though `large` depends on `count`:

```
<script>
	let count = $state(0);
	let large = $derived(count > 10);
</script>

<button onclick={() => count++}>
	{large}
</button>
```

[Edit this page on GitHub](https://github.com/sveltejs/svelte/edit/main/documentation/docs/02-runes/03-%24derived.md)  [llms.txt](/docs/svelte/%24derived/llms.txt)

previous next

[$state](/docs/svelte/%24state) [$effect](/docs/svelte/%24effect)