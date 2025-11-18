# Writer Module Documentation

This is the Astro-powered documentation site for the Writer module of the Extrophi Ecosystem.

## Tech Stack

- **Astro** - Static site generator with islands architecture
- **Svelte 5** - Interactive islands using runes for reactivity
- **TailwindCSS** - Utility-first CSS framework

## Project Structure

```
writer-docs/
├── public/              # Static assets
├── src/
│   ├── components/      # Reusable Astro/Svelte components
│   ├── islands/         # Interactive Svelte islands (client-side)
│   ├── lib/            # Utility functions and helpers
│   ├── pages/          # Astro pages (routes)
│   ├── stores/         # Svelte stores for state management
│   └── styles/         # Global styles
├── astro.config.mjs    # Astro configuration
├── svelte.config.js    # Svelte configuration
├── tailwind.config.mjs # Tailwind configuration
└── tsconfig.json       # TypeScript configuration
```

## Development

### Prerequisites

- Node.js v18.20.8 or higher
- npm or pnpm

### Commands

```bash
# Install dependencies (when connected to internet)
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Features

### Islands Architecture

Astro's islands architecture allows you to:
- Ship only the JavaScript needed for interactive components
- Keep the majority of your site as fast, static HTML
- Use Svelte 5 components for interactive "islands" of interactivity

### Svelte 5 Runes

This project uses Svelte 5's new runes syntax:

```svelte
<script>
  // State
  let count = $state(0);

  // Derived state
  let doubled = $derived(count * 2);

  // Effects
  $effect(() => {
    console.log('Count changed:', count);
  });
</script>
```

### TailwindCSS

Utility-first CSS with:
- Dark mode support
- Responsive design utilities
- Custom configuration in `tailwind.config.mjs`

## Directory Guide

### `/src/pages/`
Astro pages that become routes. Each `.astro` file becomes a page.

### `/src/islands/`
Interactive Svelte 5 components that are hydrated on the client. Use the `client:*` directive in Astro pages to control when they load:
- `client:load` - Load immediately
- `client:idle` - Load when browser is idle
- `client:visible` - Load when component becomes visible

### `/src/components/`
Reusable components (both Astro and Svelte) that are NOT automatically hydrated. These are rendered as static HTML unless explicitly imported into islands.

### `/src/stores/`
Svelte stores for state management across components.

### `/src/lib/`
Utility functions, types, and helpers.

## Integration with Writer Module

This documentation site is separate from the main Writer Tauri application but shares documentation resources. It provides:

- User-facing documentation
- Developer guides
- API reference
- Architecture documentation

## Success Criteria

✅ `npm run dev` starts Astro dev server
✅ `npm run build` produces static HTML
✅ Svelte components work with runes
✅ TailwindCSS classes work

## References

- [Astro Documentation](https://docs.astro.build)
- [Svelte 5 Documentation](https://svelte.dev)
- [TailwindCSS Documentation](https://tailwindcss.com)
