<!-- Source: https://svelte.dev/docs/svelte/stores -->

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

SvelteRuntime

# Stores

 [ ]

### On this page

* [Stores](/docs/svelte/stores)
* [When to use stores](#When-to-use-stores)
* [svelte/store](#svelte-store)
* [Store contract](#Store-contract)

A *store* is an object that allows reactive access to a value via a simple *store contract*. The [`svelte/store` module](../svelte-store) contains minimal store implementations which fulfil this contract.

Any time you have a reference to a store, you can access its value inside a component by prefixing it with the `$` character. This causes Svelte to declare the prefixed variable, subscribe to the store at component initialisation and unsubscribe when appropriate.

Assignments to `$`-prefixed variables require that the variable be a writable store, and will result in a call to the store’s `.set` method.

Note that the store must be declared at the top level of the component — not inside an `if` block or a function, for example.

Local variables (that do not represent store values) must *not* have a `$` prefix.

```
<script>
	import { writable } from 'svelte/store';

	const count = writable(0);
	console.log($count); // logs 0

	count.set(1);
	console.log($count); // logs 1

	$count = 2;
	console.log($count); // logs 2
</script>
```

## When to use stores

Prior to Svelte 5, stores were the go-to solution for creating cross-component reactive states or extracting logic. With runes, these use cases have greatly diminished.

* when extracting logic, it’s better to take advantage of runes’ universal reactivity: You can use runes outside the top level of components and even place them into JavaScript or TypeScript files (using a `.svelte.js` or `.svelte.ts` file ending)
* when creating shared state, you can create a `$state` object containing the values you need and then manipulate said state

state.svelte

```
export const

```
const userState: {
    name: string;
}
```

userState =

```
function $state<{
    name: string;
}>(initial: {
    name: string;
}): {
    name: string;
} (+1 overload)
namespace $state
```

Declares reactive state.

Example:

```
let count = $state(0);
```

https://svelte.dev/docs/svelte/$state

@paraminitial The initial value

$state({
	name: stringname: 'name',
	/* ... */
});
```

App[x]

```
<script>
	import { userState } from './state.svelte.js';
</script>

<p>User name: {userState.name}</p>
<button onclick={() => {
	userState.name = 'new name';
}}>
	change name
</button>
```

```
<script lang="ts">
	import { userState } from './state.svelte.js';
</script>

<p>User name: {userState.name}</p>
<button onclick={() => {
	userState.name = 'new name';
}}>
	change name
</button>
```

Stores are still a good solution when you have complex asynchronous data streams or it’s important to have more manual control over updating values or listening to changes. If you’re familiar with RxJs and want to reuse that knowledge, the `$` also comes in handy for you.

## svelte/store

The `svelte/store` module contains a minimal store implementation which fulfil the store contract. It provides methods for creating stores that you can update from the outside, stores you can only update from the inside, and for combining and deriving stores.

### writable

Function that creates a store which has values that can be set from ‘outside’ components. It gets created as an object with additional `set` and `update` methods.

`set` is a method that takes one argument which is the value to be set. The store value gets set to the value of the argument if the store value is not already equal to it.

`update` is a method that takes one argument which is a callback. The callback takes the existing store value as its argument and returns the new value to be set to the store.

store

```
import { function writable<T>(value?: T | undefined, start?: StartStopNotifier<T> | undefined): Writable<T>

Create a Writable store that allows both updating and reading by subscription.

@paramvalue initial value

writable } from 'svelte/store';

const const count: Writable<number>count = writable<number>(value?: number | undefined, start?: StartStopNotifier<number> | undefined): Writable<number>

Create a Writable store that allows both updating and reading by subscription.

@paramvalue initial value

writable(0);

const count: Writable<number>count.Readable<number>.subscribe(this: void, run: Subscriber<number>, invalidate?: () => void): Unsubscriber

Subscribe on value changes.

@paramrun subscription callback

@paraminvalidate cleanup callback

subscribe((value: numbervalue) => {
	var console: Console

The console module provides a simple debugging console that is similar to the
JavaScript console mechanism provided by web browsers.

The module exports two specific components:

* A Console class with methods such as console.log(), console.error() and console.warn() that can be used to write to any Node.js stream.
* A global console instance configured to write to process.stdout and
  process.stderr. The global console can be used without importing the node:console module.

Warning: The global console object’s methods are neither consistently
synchronous like the browser APIs they resemble, nor are they consistently
asynchronous like all other Node.js streams. See the note on process I/O for
more information.

Example using the global console:

```
console.log('hello world');
// Prints: hello world, to stdout
console.log('hello %s', 'world');
// Prints: hello world, to stdout
console.error(new Error('Whoops, something bad happened'));
// Prints error message and stack trace to stderr:
//   Error: Whoops, something bad happened
//     at [eval]:5:15
//     at Script.runInThisContext (node:vm:132:18)
//     at Object.runInThisContext (node:vm:309:38)
//     at node:internal/process/execution:77:19
//     at [eval]-wrapper:6:22
//     at evalScript (node:internal/process/execution:76:60)
//     at node:internal/main/eval_string:23:3

const name = 'Will Robinson';
console.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to stderr
```

Example using the Console class:

```
const out = getStreamSomehow();
const err = getStreamSomehow();
const myConsole = new console.Console(out, err);

myConsole.log('hello world');
// Prints: hello world, to out
myConsole.log('hello %s', 'world');
// Prints: hello world, to out
myConsole.error(new Error('Whoops, something bad happened'));
// Prints: [Error: Whoops, something bad happened], to err

const name = 'Will Robinson';
myConsole.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to err
```

@seesource

console.Console.log(message?: any, ...optionalParams: any[]): void (+1 overload)

Prints to stdout with newline. Multiple arguments can be passed, with the
first used as the primary message and all additional used as substitution
values similar to printf(3)
(the arguments are all passed to util.format()).

```
const count = 5;
console.log('count: %d', count);
// Prints: count: 5, to stdout
console.log('count:', count);
// Prints: count: 5, to stdout
```

See util.format() for more information.

@sincev0.1.100

log(value: numbervalue);
}); // logs '0'

const count: Writable<number>count.Writable<number>.set(this: void, value: number): void

Set value and inform subscribers.

@paramvalue to set

set(1); // logs '1'

const count: Writable<number>count.Writable<number>.update(this: void, updater: Updater<number>): void

Update value using callback and inform subscribers.

@paramupdater callback

update((n: numbern) => n: numbern + 1); // logs '2'
```

If a function is passed as the second argument, it will be called when the number of subscribers goes from zero to one (but not from one to two, etc). That function will be passed a `set` function which changes the value of the store, and an `update` function which works like the `update` method on the store, taking a callback to calculate the store’s new value from its old value. It must return a `stop` function that is called when the subscriber count goes from one to zero.

store

```
import { function writable<T>(value?: T | undefined, start?: StartStopNotifier<T> | undefined): Writable<T>

Create a Writable store that allows both updating and reading by subscription.

@paramvalue initial value

writable } from 'svelte/store';

const const count: Writable<number>count = writable<number>(value?: number | undefined, start?: StartStopNotifier<number> | undefined): Writable<number>

Create a Writable store that allows both updating and reading by subscription.

@paramvalue initial value

writable(0, () => {
	var console: Console

The console module provides a simple debugging console that is similar to the
JavaScript console mechanism provided by web browsers.

The module exports two specific components:

* A Console class with methods such as console.log(), console.error() and console.warn() that can be used to write to any Node.js stream.
* A global console instance configured to write to process.stdout and
  process.stderr. The global console can be used without importing the node:console module.

Warning: The global console object’s methods are neither consistently
synchronous like the browser APIs they resemble, nor are they consistently
asynchronous like all other Node.js streams. See the note on process I/O for
more information.

Example using the global console:

```
console.log('hello world');
// Prints: hello world, to stdout
console.log('hello %s', 'world');
// Prints: hello world, to stdout
console.error(new Error('Whoops, something bad happened'));
// Prints error message and stack trace to stderr:
//   Error: Whoops, something bad happened
//     at [eval]:5:15
//     at Script.runInThisContext (node:vm:132:18)
//     at Object.runInThisContext (node:vm:309:38)
//     at node:internal/process/execution:77:19
//     at [eval]-wrapper:6:22
//     at evalScript (node:internal/process/execution:76:60)
//     at node:internal/main/eval_string:23:3

const name = 'Will Robinson';
console.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to stderr
```

Example using the Console class:

```
const out = getStreamSomehow();
const err = getStreamSomehow();
const myConsole = new console.Console(out, err);

myConsole.log('hello world');
// Prints: hello world, to out
myConsole.log('hello %s', 'world');
// Prints: hello world, to out
myConsole.error(new Error('Whoops, something bad happened'));
// Prints: [Error: Whoops, something bad happened], to err

const name = 'Will Robinson';
myConsole.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to err
```

@seesource

console.Console.log(message?: any, ...optionalParams: any[]): void (+1 overload)

Prints to stdout with newline. Multiple arguments can be passed, with the
first used as the primary message and all additional used as substitution
values similar to printf(3)
(the arguments are all passed to util.format()).

```
const count = 5;
console.log('count: %d', count);
// Prints: count: 5, to stdout
console.log('count:', count);
// Prints: count: 5, to stdout
```

See util.format() for more information.

@sincev0.1.100

log('got a subscriber');
	return () => var console: Console

The console module provides a simple debugging console that is similar to the
JavaScript console mechanism provided by web browsers.

The module exports two specific components:

* A Console class with methods such as console.log(), console.error() and console.warn() that can be used to write to any Node.js stream.
* A global console instance configured to write to process.stdout and
  process.stderr. The global console can be used without importing the node:console module.

Warning: The global console object’s methods are neither consistently
synchronous like the browser APIs they resemble, nor are they consistently
asynchronous like all other Node.js streams. See the note on process I/O for
more information.

Example using the global console:

```
console.log('hello world');
// Prints: hello world, to stdout
console.log('hello %s', 'world');
// Prints: hello world, to stdout
console.error(new Error('Whoops, something bad happened'));
// Prints error message and stack trace to stderr:
//   Error: Whoops, something bad happened
//     at [eval]:5:15
//     at Script.runInThisContext (node:vm:132:18)
//     at Object.runInThisContext (node:vm:309:38)
//     at node:internal/process/execution:77:19
//     at [eval]-wrapper:6:22
//     at evalScript (node:internal/process/execution:76:60)
//     at node:internal/main/eval_string:23:3

const name = 'Will Robinson';
console.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to stderr
```

Example using the Console class:

```
const out = getStreamSomehow();
const err = getStreamSomehow();
const myConsole = new console.Console(out, err);

myConsole.log('hello world');
// Prints: hello world, to out
myConsole.log('hello %s', 'world');
// Prints: hello world, to out
myConsole.error(new Error('Whoops, something bad happened'));
// Prints: [Error: Whoops, something bad happened], to err

const name = 'Will Robinson';
myConsole.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to err
```

@seesource

console.Console.log(message?: any, ...optionalParams: any[]): void (+1 overload)

Prints to stdout with newline. Multiple arguments can be passed, with the
first used as the primary message and all additional used as substitution
values similar to printf(3)
(the arguments are all passed to util.format()).

```
const count = 5;
console.log('count: %d', count);
// Prints: count: 5, to stdout
console.log('count:', count);
// Prints: count: 5, to stdout
```

See util.format() for more information.

@sincev0.1.100

log('no more subscribers');
});

const count: Writable<number>count.Writable<number>.set(this: void, value: number): void

Set value and inform subscribers.

@paramvalue to set

set(1); // does nothing

const const unsubscribe: Unsubscriberunsubscribe = const count: Writable<number>count.Readable<number>.subscribe(this: void, run: Subscriber<number>, invalidate?: () => void): Unsubscriber

Subscribe on value changes.

@paramrun subscription callback

@paraminvalidate cleanup callback

subscribe((value: numbervalue) => {
	var console: Console

The console module provides a simple debugging console that is similar to the
JavaScript console mechanism provided by web browsers.

The module exports two specific components:

* A Console class with methods such as console.log(), console.error() and console.warn() that can be used to write to any Node.js stream.
* A global console instance configured to write to process.stdout and
  process.stderr. The global console can be used without importing the node:console module.

Warning: The global console object’s methods are neither consistently
synchronous like the browser APIs they resemble, nor are they consistently
asynchronous like all other Node.js streams. See the note on process I/O for
more information.

Example using the global console:

```
console.log('hello world');
// Prints: hello world, to stdout
console.log('hello %s', 'world');
// Prints: hello world, to stdout
console.error(new Error('Whoops, something bad happened'));
// Prints error message and stack trace to stderr:
//   Error: Whoops, something bad happened
//     at [eval]:5:15
//     at Script.runInThisContext (node:vm:132:18)
//     at Object.runInThisContext (node:vm:309:38)
//     at node:internal/process/execution:77:19
//     at [eval]-wrapper:6:22
//     at evalScript (node:internal/process/execution:76:60)
//     at node:internal/main/eval_string:23:3

const name = 'Will Robinson';
console.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to stderr
```

Example using the Console class:

```
const out = getStreamSomehow();
const err = getStreamSomehow();
const myConsole = new console.Console(out, err);

myConsole.log('hello world');
// Prints: hello world, to out
myConsole.log('hello %s', 'world');
// Prints: hello world, to out
myConsole.error(new Error('Whoops, something bad happened'));
// Prints: [Error: Whoops, something bad happened], to err

const name = 'Will Robinson';
myConsole.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to err
```

@seesource

console.Console.log(message?: any, ...optionalParams: any[]): void (+1 overload)

Prints to stdout with newline. Multiple arguments can be passed, with the
first used as the primary message and all additional used as substitution
values similar to printf(3)
(the arguments are all passed to util.format()).

```
const count = 5;
console.log('count: %d', count);
// Prints: count: 5, to stdout
console.log('count:', count);
// Prints: count: 5, to stdout
```

See util.format() for more information.

@sincev0.1.100

log(value: numbervalue);
}); // logs 'got a subscriber', then '1'

const unsubscribe: () => voidunsubscribe(); // logs 'no more subscribers'
```

Note that the value of a `writable` is lost when it is destroyed, for example when the page is refreshed. However, you can write your own logic to sync the value to for example the `localStorage`.

### readable

Creates a store whose value cannot be set from ‘outside’, the first argument is the store’s initial value, and the second argument to `readable` is the same as the second argument to `writable`.

```
import { function readable<T>(value?: T | undefined, start?: StartStopNotifier<T> | undefined): Readable<T>

Creates a Readable store that allows reading by subscription.

@paramvalue initial value

readable } from 'svelte/store';

const const time: Readable<Date>time = readable<Date>(value?: Date | undefined, start?: StartStopNotifier<Date> | undefined): Readable<Date>

Creates a Readable store that allows reading by subscription.

@paramvalue initial value

readable(new

```
var Date: DateConstructor
new () => Date (+4 overloads)
```

Date(), (set: (value: Date) => voidset) => {
	set: (value: Date) => voidset(new

```
var Date: DateConstructor
new () => Date (+4 overloads)
```

Date());

	const const interval: NodeJS.Timeoutinterval = function setInterval<[]>(callback: () => void, delay?: number): NodeJS.Timeout (+2 overloads)

Schedules repeated execution of callback every delay milliseconds.

When delay is larger than 2147483647 or less than 1, the delay will be
set to 1. Non-integer delays are truncated to an integer.

If callback is not a function, a TypeError will be thrown.

This method has a custom variant for promises that is available using
timersPromises.setInterval().

@sincev0.0.1

@paramcallback The function to call when the timer elapses.

@paramdelay The number of milliseconds to wait before calling the
callback. Default: 1.

@paramargs Optional arguments to pass when the callback is called.

@returnsfor use with clearInterval()

setInterval(() => {
		set: (value: Date) => voidset(new

```
var Date: DateConstructor
new () => Date (+4 overloads)
```

Date());
	}, 1000);

	return () => function clearInterval(timeout: NodeJS.Timeout | string | number | undefined): void (+1 overload)

Cancels a Timeout object created by setInterval().

@sincev0.0.1

@paramtimeout A Timeout object as returned by setInterval()
or the primitive of the Timeout object as a string or a number.

clearInterval(const interval: NodeJS.Timeoutinterval);
});

const const ticktock: Readable<string>ticktock = readable<string>(value?: string | undefined, start?: StartStopNotifier<string> | undefined): Readable<string>

Creates a Readable store that allows reading by subscription.

@paramvalue initial value

readable('tick', (set: (value: string) => voidset, update: (fn: Updater<string>) => voidupdate) => {
	const const interval: NodeJS.Timeoutinterval = function setInterval<[]>(callback: () => void, delay?: number): NodeJS.Timeout (+2 overloads)

Schedules repeated execution of callback every delay milliseconds.

When delay is larger than 2147483647 or less than 1, the delay will be
set to 1. Non-integer delays are truncated to an integer.

If callback is not a function, a TypeError will be thrown.

This method has a custom variant for promises that is available using
timersPromises.setInterval().

@sincev0.0.1

@paramcallback The function to call when the timer elapses.

@paramdelay The number of milliseconds to wait before calling the
callback. Default: 1.

@paramargs Optional arguments to pass when the callback is called.

@returnsfor use with clearInterval()

setInterval(() => {
		update: (fn: Updater<string>) => voidupdate((sound: stringsound) => (sound: stringsound === 'tick' ? 'tock' : 'tick'));
	}, 1000);

	return () => function clearInterval(timeout: NodeJS.Timeout | string | number | undefined): void (+1 overload)

Cancels a Timeout object created by setInterval().

@sincev0.0.1

@paramtimeout A Timeout object as returned by setInterval()
or the primitive of the Timeout object as a string or a number.

clearInterval(const interval: NodeJS.Timeoutinterval);
});
```

### derived

Derives a store from one or more other stores. The callback runs initially when the first subscriber subscribes and then whenever the store dependencies change.

In the simplest version, `derived` takes a single store, and the callback returns a derived value.

```
import { function derived<S extends Stores, T>(stores: S, fn: (values: StoresValues<S>, set: (value: T) => void, update: (fn: Updater<T>) => void) => Unsubscriber | void, initial_value?: T | undefined): Readable<T> (+1 overload)

Derived value store by synchronizing one or more readable stores and
applying an aggregation function over its input values.

derived } from 'svelte/store';

const const doubled: Readable<number>doubled = derived<Writable<number>, number>(stores: Writable<number>, fn: (values: number) => number, initial_value?: number | undefined): Readable<number> (+1 overload)

Derived value store by synchronizing one or more readable stores and
applying an aggregation function over its input values.

derived(const a: Writable<number>a, ($a: number$a) => $a: number$a * 2);
```

The callback can set a value asynchronously by accepting a second argument, `set`, and an optional third argument, `update`, calling either or both of them when appropriate.

In this case, you can also pass a third argument to `derived` — the initial value of the derived store before `set` or `update` is first called. If no initial value is specified, the store’s initial value will be `undefined`.

```
import { function derived<S extends Stores, T>(stores: S, fn: (values: StoresValues<S>, set: (value: T) => void, update: (fn: Updater<T>) => void) => Unsubscriber | void, initial_value?: T | undefined): Readable<T> (+1 overload)

Derived value store by synchronizing one or more readable stores and
applying an aggregation function over its input values.

derived } from 'svelte/store';

const const delayed: Readable<number>delayed = derived<Writable<number>, number>(stores: Writable<number>, fn: (values: number, set: (value: number) => void, update: (fn: Updater<number>) => void) => Unsubscriber | void, initial_value?: number | undefined): Readable<...> (+1 overload)

Derived value store by synchronizing one or more readable stores and
applying an aggregation function over its input values.

derived(
	const a: Writable<number>a,
	($a: number$a, set: (value: number) => voidset) => {
		function setTimeout<[]>(callback: () => void, delay?: number): NodeJS.Timeout (+2 overloads)

Schedules execution of a one-time callback after delay milliseconds.

The callback will likely not be invoked in precisely delay milliseconds.
Node.js makes no guarantees about the exact timing of when callbacks will fire,
nor of their ordering. The callback will be called as close as possible to the
time specified.

When delay is larger than 2147483647 or less than 1 or NaN, the delay
will be set to 1. Non-integer delays are truncated to an integer.

If callback is not a function, a TypeError will be thrown.

This method has a custom variant for promises that is available using
timersPromises.setTimeout().

@sincev0.0.1

@paramcallback The function to call when the timer elapses.

@paramdelay The number of milliseconds to wait before calling the
callback. Default: 1.

@paramargs Optional arguments to pass when the callback is called.

@returnsfor use with clearTimeout()

setTimeout(() => set: (value: number) => voidset($a: number$a), 1000);
	},
	2000
);

const const delayedIncrement: Readable<unknown>delayedIncrement = derived<Writable<number>, unknown>(stores: Writable<number>, fn: (values: number, set: (value: unknown) => void, update: (fn: Updater<unknown>) => void) => Unsubscriber | void, initial_value?: unknown): Readable<...> (+1 overload)

Derived value store by synchronizing one or more readable stores and
applying an aggregation function over its input values.

derived(const a: Writable<number>a, ($a: number$a, set: (value: unknown) => voidset, update: (fn: Updater<unknown>) => voidupdate) => {
	set: (value: unknown) => voidset($a: number$a);
	function setTimeout<[]>(callback: () => void, delay?: number): NodeJS.Timeout (+2 overloads)

Schedules execution of a one-time callback after delay milliseconds.

The callback will likely not be invoked in precisely delay milliseconds.
Node.js makes no guarantees about the exact timing of when callbacks will fire,
nor of their ordering. The callback will be called as close as possible to the
time specified.

When delay is larger than 2147483647 or less than 1 or NaN, the delay
will be set to 1. Non-integer delays are truncated to an integer.

If callback is not a function, a TypeError will be thrown.

This method has a custom variant for promises that is available using
timersPromises.setTimeout().

@sincev0.0.1

@paramcallback The function to call when the timer elapses.

@paramdelay The number of milliseconds to wait before calling the
callback. Default: 1.

@paramargs Optional arguments to pass when the callback is called.

@returnsfor use with clearTimeout()

setTimeout(() => update: (fn: Updater<unknown>) => voidupdate((x: unknownx) => x + 1), 1000);
	// every time $a produces a value, this produces two
	// values, $a immediately and then $a + 1 a second later
});
```

If you return a function from the callback, it will be called when a) the callback runs again, or b) the last subscriber unsubscribes.

```
import { function derived<S extends Stores, T>(stores: S, fn: (values: StoresValues<S>, set: (value: T) => void, update: (fn: Updater<T>) => void) => Unsubscriber | void, initial_value?: T | undefined): Readable<T> (+1 overload)

Derived value store by synchronizing one or more readable stores and
applying an aggregation function over its input values.

derived } from 'svelte/store';

const const tick: Readable<number>tick = derived<Writable<number>, number>(stores: Writable<number>, fn: (values: number, set: (value: number) => void, update: (fn: Updater<number>) => void) => Unsubscriber | void, initial_value?: number | undefined): Readable<...> (+1 overload)

Derived value store by synchronizing one or more readable stores and
applying an aggregation function over its input values.

derived(
	const frequency: Writable<number>frequency,
	($frequency: number$frequency, set: (value: number) => voidset) => {
		const const interval: NodeJS.Timeoutinterval = function setInterval<[]>(callback: () => void, delay?: number): NodeJS.Timeout (+2 overloads)

Schedules repeated execution of callback every delay milliseconds.

When delay is larger than 2147483647 or less than 1, the delay will be
set to 1. Non-integer delays are truncated to an integer.

If callback is not a function, a TypeError will be thrown.

This method has a custom variant for promises that is available using
timersPromises.setInterval().

@sincev0.0.1

@paramcallback The function to call when the timer elapses.

@paramdelay The number of milliseconds to wait before calling the
callback. Default: 1.

@paramargs Optional arguments to pass when the callback is called.

@returnsfor use with clearInterval()

setInterval(() => {
			set: (value: number) => voidset(var Date: DateConstructor

Enables basic storage and retrieval of dates and times.

Date.DateConstructor.now(): number

Returns the number of milliseconds elapsed since midnight, January 1, 1970 Universal Coordinated Time (UTC).

now());
		}, 1000 / $frequency: number$frequency);

		return () => {
			function clearInterval(timeout: NodeJS.Timeout | string | number | undefined): void (+1 overload)

Cancels a Timeout object created by setInterval().

@sincev0.0.1

@paramtimeout A Timeout object as returned by setInterval()
or the primitive of the Timeout object as a string or a number.

clearInterval(const interval: NodeJS.Timeoutinterval);
		};
	},
	2000
);
```

In both cases, an array of arguments can be passed as the first argument instead of a single store.

```
import { function derived<S extends Stores, T>(stores: S, fn: (values: StoresValues<S>, set: (value: T) => void, update: (fn: Updater<T>) => void) => Unsubscriber | void, initial_value?: T | undefined): Readable<T> (+1 overload)

Derived value store by synchronizing one or more readable stores and
applying an aggregation function over its input values.

derived } from 'svelte/store';

const const summed: Readable<number>summed = derived<[Writable<number>, Writable<number>], number>(stores: [Writable<number>, Writable<number>], fn: (values: [number, number]) => number, initial_value?: number | undefined): Readable<...> (+1 overload)

Derived value store by synchronizing one or more readable stores and
applying an aggregation function over its input values.

derived([const a: Writable<number>a, const b: Writable<number>b], ([$a: number$a, $b: number$b]) => $a: number$a + $b: number$b);

const const delayed: Readable<unknown>delayed = derived<[Writable<number>, Writable<number>], unknown>(stores: [Writable<number>, Writable<number>], fn: (values: [number, number], set: (value: unknown) => void, update: (fn: Updater<...>) => void) => Unsubscriber | void, initial_value?: unknown): Readable<...> (+1 overload)

Derived value store by synchronizing one or more readable stores and
applying an aggregation function over its input values.

derived([const a: Writable<number>a, const b: Writable<number>b], ([$a: number$a, $b: number$b], set: (value: unknown) => voidset) => {
	function setTimeout<[]>(callback: () => void, delay?: number): NodeJS.Timeout (+2 overloads)

Schedules execution of a one-time callback after delay milliseconds.

The callback will likely not be invoked in precisely delay milliseconds.
Node.js makes no guarantees about the exact timing of when callbacks will fire,
nor of their ordering. The callback will be called as close as possible to the
time specified.

When delay is larger than 2147483647 or less than 1 or NaN, the delay
will be set to 1. Non-integer delays are truncated to an integer.

If callback is not a function, a TypeError will be thrown.

This method has a custom variant for promises that is available using
timersPromises.setTimeout().

@sincev0.0.1

@paramcallback The function to call when the timer elapses.

@paramdelay The number of milliseconds to wait before calling the
callback. Default: 1.

@paramargs Optional arguments to pass when the callback is called.

@returnsfor use with clearTimeout()

setTimeout(() => set: (value: unknown) => voidset($a: number$a + $b: number$b), 1000);
});
```

### readonly

This simple helper function makes a store readonly. You can still subscribe to the changes from the original one using this new readable store.

```
import { function readonly<T>(store: Readable<T>): Readable<T>

Takes a store and returns a new one derived from the old one that is readable.

@paramstore - store to make readonly

readonly, function writable<T>(value?: T | undefined, start?: StartStopNotifier<T> | undefined): Writable<T>

Create a Writable store that allows both updating and reading by subscription.

@paramvalue initial value

writable } from 'svelte/store';

const const writableStore: Writable<number>writableStore = writable<number>(value?: number | undefined, start?: StartStopNotifier<number> | undefined): Writable<number>

Create a Writable store that allows both updating and reading by subscription.

@paramvalue initial value

writable(1);
const const readableStore: Readable<number>readableStore = readonly<number>(store: Readable<number>): Readable<number>

Takes a store and returns a new one derived from the old one that is readable.

@paramstore - store to make readonly

readonly(const writableStore: Writable<number>writableStore);

const readableStore: Readable<number>readableStore.Readable<number>.subscribe(this: void, run: Subscriber<number>, invalidate?: () => void): Unsubscriber

Subscribe on value changes.

@paramrun subscription callback

@paraminvalidate cleanup callback

subscribe(var console: Console

The console module provides a simple debugging console that is similar to the
JavaScript console mechanism provided by web browsers.

The module exports two specific components:

* A Console class with methods such as console.log(), console.error() and console.warn() that can be used to write to any Node.js stream.
* A global console instance configured to write to process.stdout and
  process.stderr. The global console can be used without importing the node:console module.

Warning: The global console object’s methods are neither consistently
synchronous like the browser APIs they resemble, nor are they consistently
asynchronous like all other Node.js streams. See the note on process I/O for
more information.

Example using the global console:

```
console.log('hello world');
// Prints: hello world, to stdout
console.log('hello %s', 'world');
// Prints: hello world, to stdout
console.error(new Error('Whoops, something bad happened'));
// Prints error message and stack trace to stderr:
//   Error: Whoops, something bad happened
//     at [eval]:5:15
//     at Script.runInThisContext (node:vm:132:18)
//     at Object.runInThisContext (node:vm:309:38)
//     at node:internal/process/execution:77:19
//     at [eval]-wrapper:6:22
//     at evalScript (node:internal/process/execution:76:60)
//     at node:internal/main/eval_string:23:3

const name = 'Will Robinson';
console.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to stderr
```

Example using the Console class:

```
const out = getStreamSomehow();
const err = getStreamSomehow();
const myConsole = new console.Console(out, err);

myConsole.log('hello world');
// Prints: hello world, to out
myConsole.log('hello %s', 'world');
// Prints: hello world, to out
myConsole.error(new Error('Whoops, something bad happened'));
// Prints: [Error: Whoops, something bad happened], to err

const name = 'Will Robinson';
myConsole.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to err
```

@seesource

console.Console.log(...data: any[]): void (+1 overload)

MDN Reference

log);

const writableStore: Writable<number>writableStore.Writable<number>.set(this: void, value: number): void

Set value and inform subscribers.

@paramvalue to set

set(2); // console: 2
const readableStore: Readable<number>readableStore.set(2); // ERROR
```

### get

Generally, you should read the value of a store by subscribing to it and using the value as it changes over time. Occasionally, you may need to retrieve the value of a store to which you’re not subscribed. `get` allows you to do so.

> This works by creating a subscription, reading the value, then unsubscribing. It’s therefore not recommended in hot code paths.

```
import { function get<T>(store: Readable<T>): T

Get the current value from a store by subscribing and immediately unsubscribing.

get } from 'svelte/store';

const const value: stringvalue = get<string>(store: Readable<string>): string

Get the current value from a store by subscribing and immediately unsubscribing.

get(const store: Writable<string>store);
```

## Store contract

```
store = { subscribe: (subscription: (value: any) => void) => () => undefinedsubscribe: (subscription: (value: any) => voidsubscription: (value: anyvalue: any) => void) => (() => void), set: (value: any) => undefinedset?: (value: anyvalue: any) => void }
```

You can create your own stores without relying on [`svelte/store`](../svelte-store), by implementing the *store contract*:

1. A store must contain a `.subscribe` method, which must accept as its argument a subscription function. This subscription function must be immediately and synchronously called with the store’s current value upon calling `.subscribe`. All of a store’s active subscription functions must later be synchronously called whenever the store’s value changes.
2. The `.subscribe` method must return an unsubscribe function. Calling an unsubscribe function must stop its subscription, and its corresponding subscription function must not be called again by the store.
3. A store may *optionally* contain a `.set` method, which must accept as its argument a new value for the store, and which synchronously calls all of the store’s active subscription functions. Such a store is called a *writable store*.

For interoperability with RxJS Observables, the `.subscribe` method is also allowed to return an object with an `.unsubscribe` method, rather than return the unsubscription function directly. Note however that unless `.subscribe` synchronously calls the subscription (which is not required by the Observable spec), Svelte will see the value of the store as `undefined` until it does.

[Edit this page on GitHub](https://github.com/sveltejs/svelte/edit/main/documentation/docs/06-runtime/01-stores.md)  [llms.txt](/docs/svelte/stores/llms.txt)

previous next

[<svelte:options>](/docs/svelte/svelte-options) [Context](/docs/svelte/context)