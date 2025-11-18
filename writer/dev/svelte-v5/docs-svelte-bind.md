<!-- Source: https://svelte.dev/docs/svelte/bind -->

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

SvelteTemplate syntax

# bind:

 [ ]

### On this page

* [bind:](/docs/svelte/bind)
* [Function bindings](#Function-bindings)
* [<input bind:value>](#input-bind:value)
* [<input bind:checked>](#input-bind:checked)
* [<input bind:indeterminate>](#input-bind:indeterminate)
* [<input bind:group>](#input-bind:group)
* [<input bind:files>](#input-bind:files)
* [<select bind:value>](#select-bind:value)
* [<audio>](#audio)
* [<video>](#video)
* [<img>](#img)
* [<details bind:open>](#details-bind:open)
* [window and document](#window-and-document)
* [Contenteditable bindings](#Contenteditable-bindings)
* [Dimensions](#Dimensions)
* [bind:this](#bind:this)
* [bind:*property* for components](#bind:property-for-components)

Data ordinarily flows down, from parent to child. The `bind:` directive allows data to flow the other way, from child to parent.

The general syntax is `bind:property={expression}`, where `expression` is an [*lvalue*](https://press.rebus.community/programmingfundamentals/chapter/lvalue-and-rvalue/) (i.e. a variable or an object property). When the expression is an identifier with the same name as the property, we can omit the expression — in other words these are equivalent:

```
<input bind:value={value} />
<input bind:value />
```

Svelte creates an event listener that updates the bound value. If an element already has a listener for the same event, that listener will be fired before the bound value is updated.

Most bindings are *two-way*, meaning that changes to the value will affect the element and vice versa. A few bindings are *readonly*, meaning that changing their value will have no effect on the element.

## Function bindings

You can also use `bind:property={get, set}`, where `get` and `set` are functions, allowing you to perform validation and transformation:

```
<input bind:value={
	() => value,
	(v) => value = v.toLowerCase()}
/>
```

In the case of readonly bindings like [dimension bindings](#Dimensions), the `get` value should be `null`:

```
<div
	bind:clientWidth={null, redraw}
	bind:clientHeight={null, redraw}
>...</div>
```

> Function bindings are available in Svelte 5.9.0 and newer.

## <input bind:value>

A `bind:value` directive on an `<input>` element binds the input’s `value` property:

```
<script>
	let message = $state('hello');
</script>

<input bind:value={message} />
<p>{message}</p>
```

In the case of a numeric input (`type="number"` or `type="range"`), the value will be coerced to a number ([demo](/playground/untitled#H4sIAAAAAAAAE6WPwYoCMQxAfyWEPeyiOOqx2w74Hds9pBql0IllmhGXYf5dKqwiyILsLXnwwsuI-5i4oPkaUX8yo7kCnKNQV7dNzoty4qSVBSr8jG-Poixa0KAt2z5mbb14TaxA4OCtKCm_rz4-f2m403WltrlrYhMFTtcLNkoeFGqZ8yhDF7j3CCHKzpwoDexGmqCL4jwuPUJHZ-dxVcfmyYGe5MAv-La5pbxYFf5Z9Zf_UJXb-sEMquFgJJhBmGyTW5yj8lnRaD_w9D1dAKSSj7zqAQAA)):

```
<script>
	let a = $state(1);
	let b = $state(2);
</script>

<label>
	<input type="number" bind:value={a} min="0" max="10" />
	<input type="range" bind:value={a} min="0" max="10" />
</label>

<label>
	<input type="number" bind:value={b} min="0" max="10" />
	<input type="range" bind:value={b} min="0" max="10" />
</label>

<p>{a} + {b} = {a + b}</p>
```

If the input is empty or invalid (in the case of `type="number"`), the value is `undefined`.

Since 5.6.0, if an `<input>` has a `defaultValue` and is part of a form, it will revert to that value instead of the empty string when the form is reset. Note that for the initial render the value of the binding takes precedence unless it is `null` or `undefined`.

```
<script>
	let value = $state('');
</script>

<form>
	<input bind:value defaultValue="not the empty string">
	<input type="reset" value="Reset">
</form>
```

> Use reset buttons sparingly, and ensure that users won’t accidentally click them while trying to submit the form.

## <input bind:checked>

Checkbox inputs can be bound with `bind:checked`:

```
<label>
	<input type="checkbox" bind:checked={accepted} />
	Accept terms and conditions
</label>
```

Since 5.6.0, if an `<input>` has a `defaultChecked` attribute and is part of a form, it will revert to that value instead of `false` when the form is reset. Note that for the initial render the value of the binding takes precedence unless it is `null` or `undefined`.

```
<script>
	let checked = $state(true);
</script>

<form>
	<input type="checkbox" bind:checked defaultChecked={true}>
	<input type="reset" value="Reset">
</form>
```

> Use `bind:group` for radio inputs instead of `bind:checked`.

## <input bind:indeterminate>

Checkboxes can be in an [indeterminate](https://developer.mozilla.org/en-US/docs/Web/API/HTMLInputElement/indeterminate) state, independently of whether they are checked or unchecked:

```
<script>
	let checked = $state(false);
	let indeterminate = $state(true);
</script>

<form>
	<input type="checkbox" bind:checked bind:indeterminate>

	{#if indeterminate}
		waiting...
	{:else if checked}
		checked
	{:else}
		unchecked
	{/if}
</form>
```

## <input bind:group>

Inputs that work together can use `bind:group` ([demo](/playground/untitled#H4sIAAAAAAAAE62T32_TMBDH_5XDQkpbrct7SCMGEvCEECDxsO7BSW6L2c227EvbKOv_jp0f6jYhQKJv5_P3PvdL1wstH1Bk4hMSGdgbRzUssFaM9VJciFtF6EV23QvubNRFR_BPUVfWXvodEkdfKT3-zl8Zzag5YETuK6csF1u9ZUIGNo4VkYQNvPYsGRfJF5JKJ8s3QRJE6WoFb2Nq6K-ck13u2Sl9Vxxhlc6QUBIFnz9Brm9ifJ6esun81XoNd860FmtwslYGlLYte5AO4aHlVhJ1gIeKWq92COt1iMtJlkhFPkgh1rHZiiF6K6BUus4G5KafGznCTlIbVUMfQZUWMJh5OrL-C_qjMYSwb1DyiH7iOEuCb1ZpWTUjfHqcwC_GWDVY3ZfmME_SGttSmD9IHaYatvWHIc6xLyqad3mq6KuqcCwnWn9p8p-p71BqP2IH81zc9w2in-od7XORP7ayCpd5YCeXI_-p59mObPF9WmwGpx3nqS2Gzw8TO3zOaS5_GqUXyQUkS3h8hOSz0ZhMESHGc0c4Hm3MAn00t1wrb0l2GZRkqvt4sXwczm6Qh8vnUJzI2LV4vAkvqWgfehTZrSSPx19WiVfFfAQAAA==)):

BurritoChooser[x]

```
<script>
	let tortilla = $state('Plain');

	/** @type {string[]} */
	let fillings = $state([]);
</script>

<!-- grouped radio inputs are mutually exclusive -->
<label><input type="radio" bind:group={tortilla} value="Plain" /> Plain</label>
<label><input type="radio" bind:group={tortilla} value="Whole wheat" /> Whole wheat</label>
<label><input type="radio" bind:group={tortilla} value="Spinach" /> Spinach</label>

<!-- grouped checkbox inputs populate an array -->
<label><input type="checkbox" bind:group={fillings} value="Rice" /> Rice</label>
<label><input type="checkbox" bind:group={fillings} value="Beans" /> Beans</label>
<label><input type="checkbox" bind:group={fillings} value="Cheese" /> Cheese</label>
<label><input type="checkbox" bind:group={fillings} value="Guac (extra)" /> Guac (extra)</label>
```

```
<script lang="ts">
	let tortilla = $state('Plain');
	let fillings: string[] = $state([]);
</script>

<!-- grouped radio inputs are mutually exclusive -->
<label><input type="radio" bind:group={tortilla} value="Plain" /> Plain</label>
<label><input type="radio" bind:group={tortilla} value="Whole wheat" /> Whole wheat</label>
<label><input type="radio" bind:group={tortilla} value="Spinach" /> Spinach</label>

<!-- grouped checkbox inputs populate an array -->
<label><input type="checkbox" bind:group={fillings} value="Rice" /> Rice</label>
<label><input type="checkbox" bind:group={fillings} value="Beans" /> Beans</label>
<label><input type="checkbox" bind:group={fillings} value="Cheese" /> Cheese</label>
<label><input type="checkbox" bind:group={fillings} value="Guac (extra)" /> Guac (extra)</label>
```

> `bind:group` only works if the inputs are in the same Svelte component.

## <input bind:files>

On `<input>` elements with `type="file"`, you can use `bind:files` to get the [`FileList` of selected files](https://developer.mozilla.org/en-US/docs/Web/API/FileList). When you want to update the files programmatically, you always need to use a `FileList` object. Currently `FileList` objects cannot be constructed directly, so you need to create a new [`DataTransfer`](https://developer.mozilla.org/en-US/docs/Web/API/DataTransfer) object and get `files` from there.

```
<script>
	let files = $state();

	function clear() {
		files = new DataTransfer().files; // null or undefined does not work
	}
</script>

<label for="avatar">Upload a picture:</label>
<input accept="image/png, image/jpeg" bind:files id="avatar" name="avatar" type="file" />
<button onclick={clear}>clear</button>
```

`FileList` objects also cannot be modified, so if you want to e.g. delete a single file from the list, you need to create a new `DataTransfer` object and add the files you want to keep.

> `DataTransfer` may not be available in server-side JS runtimes. Leaving the state that is bound to `files` uninitialized prevents potential errors if components are server-side rendered.

## <select bind:value>

A `<select>` value binding corresponds to the `value` property on the selected `<option>`, which can be any value (not just strings, as is normally the case in the DOM).

```
<select bind:value={selected}>
	<option value={a}>a</option>
	<option value={b}>b</option>
	<option value={c}>c</option>
</select>
```

A `<select multiple>` element behaves similarly to a checkbox group. The bound variable is an array with an entry corresponding to the `value` property of each selected `<option>`.

```
<select multiple bind:value={fillings}>
	<option value="Rice">Rice</option>
	<option value="Beans">Beans</option>
	<option value="Cheese">Cheese</option>
	<option value="Guac (extra)">Guac (extra)</option>
</select>
```

When the value of an `<option>` matches its text content, the attribute can be omitted.

```
<select multiple bind:value={fillings}>
	<option>Rice</option>
	<option>Beans</option>
	<option>Cheese</option>
	<option>Guac (extra)</option>
</select>
```

You can give the `<select>` a default value by adding a `selected` attribute to the`<option>` (or options, in the case of `<select multiple>`) that should be initially selected. If the `<select>` is part of a form, it will revert to that selection when the form is reset. Note that for the initial render the value of the binding takes precedence if it’s not `undefined`.

```
<select bind:value={selected}>
	<option value={a}>a</option>
	<option value={b} selected>b</option>
	<option value={c}>c</option>
</select>
```

## <audio>

`<audio>` elements have their own set of bindings — five two-way ones...

* [`currentTime`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/currentTime)
* [`playbackRate`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/playbackRate)
* [`paused`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/paused)
* [`volume`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/volume)
* [`muted`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/muted)

...and six readonly ones:

* [`duration`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/duration)
* [`buffered`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/buffered)
* [`seekable`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/seekable)
* [`seeking`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/seeking_event)
* [`ended`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/ended)
* [`readyState`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/readyState)
* [`played`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/played)

```
<audio src={clip} bind:duration bind:currentTime bind:paused></audio>
```

## <video>

`<video>` elements have all the same bindings as [`<audio>`](#audio) elements, plus readonly [`videoWidth`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLVideoElement/videoWidth) and [`videoHeight`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLVideoElement/videoHeight) bindings.

## <img>

`<img>` elements have two readonly bindings:

* [`naturalWidth`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLImageElement/naturalWidth)
* [`naturalHeight`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLImageElement/naturalHeight)

## <details bind:open>

`<details>` elements support binding to the `open` property.

```
<details bind:open={isOpen}>
	<summary>How do you comfort a JavaScript bug?</summary>
	<p>You console it.</p>
</details>
```

## window and document

To bind to properties of `window` and `document`, see [`<svelte:window>`](svelte-window) and [`<svelte:document>`](svelte-document).

## Contenteditable bindings

Elements with the `contenteditable` attribute support the following bindings:

* [`innerHTML`](https://developer.mozilla.org/en-US/docs/Web/API/Element/innerHTML)
* [`innerText`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/innerText)
* [`textContent`](https://developer.mozilla.org/en-US/docs/Web/API/Node/textContent)

> There are [subtle differences between `innerText` and `textContent`](https://developer.mozilla.org/en-US/docs/Web/API/Node/textContent#differences_from_innertext).

```
<div contenteditable="true" bind:innerHTML={html}></div>
```

## Dimensions

All visible elements have the following readonly bindings, measured with a `ResizeObserver`:

* [`clientWidth`](https://developer.mozilla.org/en-US/docs/Web/API/Element/clientWidth)
* [`clientHeight`](https://developer.mozilla.org/en-US/docs/Web/API/Element/clientHeight)
* [`offsetWidth`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/offsetWidth)
* [`offsetHeight`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/offsetHeight)
* [`contentRect`](https://developer.mozilla.org/en-US/docs/Web/API/ResizeObserverEntry/contentRect)
* [`contentBoxSize`](https://developer.mozilla.org/en-US/docs/Web/API/ResizeObserverEntry/contentBoxSize)
* [`borderBoxSize`](https://developer.mozilla.org/en-US/docs/Web/API/ResizeObserverEntry/borderBoxSize)
* [`devicePixelContentBoxSize`](https://developer.mozilla.org/en-US/docs/Web/API/ResizeObserverEntry/devicePixelContentBoxSize)

```
<div bind:offsetWidth={width} bind:offsetHeight={height}>
	<Chart {width} {height} />
</div>
```

> `display: inline` elements do not have a width or height (except for elements with ‘intrinsic’ dimensions, like `<img>` and `<canvas>`), and cannot be observed with a `ResizeObserver`. You will need to change the `display` style of these elements to something else, such as `inline-block`. Note that CSS transformations do not trigger `ResizeObserver` callbacks.

## bind:this

```
bind:this={dom_node}
```

To get a reference to a DOM node, use `bind:this`. The value will be `undefined` until the component is mounted — in other words, you should read it inside an effect or an event handler, but not during component initialisation:

```
<script>
	/** @type {HTMLCanvasElement} */
	let canvas;

	$effect(() => {
		const ctx = canvas.getContext('2d');
		drawStuff(ctx);
	});
</script>

<canvas bind:this={canvas}></canvas>
```

Components also support `bind:this`, allowing you to interact with component instances programmatically.

App

```
<ShoppingCart bind:this={cart} />

<button onclick={() => cart.empty()}> Empty shopping cart </button>
```

ShoppingCart[x]

```
<script>
	// All instance exports are available on the instance object
	export function empty() {
		// ...
	}
</script>
```

```
<script lang="ts">
	// All instance exports are available on the instance object
	export function empty() {
		// ...
	}
</script>
```

> In case of using [the function bindings](#Function-bindings), the getter is required to ensure that the correct value is nullified on component or element destruction.

## bind:*property* for components

```
bind:property={variable}
```

You can bind to component props using the same syntax as for elements.

```
<Keypad bind:value={pin} />
```

While Svelte props are reactive without binding, that reactivity only flows downward into the component by default. Using `bind:property` allows changes to the property from within the component to flow back up out of the component.

To mark a property as bindable, use the [`$bindable`](%24bindable) rune:

```
<script>
	let { readonlyProperty, bindableProperty = $bindable() } = $props();
</script>
```

Declaring a property as bindable means it *can* be used using `bind:`, not that it *must* be used using `bind:`.

Bindable properties can have a fallback value:

```
<script>
	let { bindableProperty = $bindable('fallback value') } = $props();
</script>
```

This fallback value *only* applies when the property is *not* bound. When the property is bound and a fallback value is present, the parent is expected to provide a value other than `undefined`, else a runtime error is thrown. This prevents hard-to-reason-about situations where it’s unclear which value should apply.

[Edit this page on GitHub](https://github.com/sveltejs/svelte/edit/main/documentation/docs/03-template-syntax/12-bind.md)  [llms.txt](/docs/svelte/bind/llms.txt)

previous next

[{@debug ...}](/docs/svelte/%40debug) [use:](/docs/svelte/use)