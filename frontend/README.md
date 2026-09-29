# Meridian Goods — Frontend

Next.js (App Router) storefront frontend, written in JavaScript with Tailwind CSS.

This step contains **only** the storefront shell: layout, navigation, and the
home page. There is no backend, no data fetching, and no cart or auth logic yet.

## Requirements

- Node.js 20.9 or newer

## Getting started

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Scripts

| Script          | Purpose                                              |
| --------------- | ---------------------------------------------------- |
| `npm run dev`   | Start the dev server (Turbopack)                     |
| `npm run build` | Production build                                     |
| `npm run start` | Serve the production build                           |
| `npm run lint`  | Run ESLint (not part of `next build` in Next.js 16)  |

## Structure

```
src/
  app/                  # App Router routes and global styles
    layout.js           # Root layout: Navbar + main + Footer, fonts, metadata
    page.js             # Home page
    globals.css         # Tailwind import, brand theme tokens, base styles
    shop/               # /shop route stub
    categories/         # /categories route stub
    cart/               # /cart route stub
    login/              # /login route stub
  components/
    layout/             # Navbar, Footer
    home/               # Hero, product-section placeholder
    ui/                 # Container, PageStub
  lib/
    site.js             # Store name, tagline, nav link definitions
```

## Conventions

- Route files use `.js`; component files use `.jsx`.
- `@/` is an alias for `src/` (configured in `jsconfig.json`).
- Pages and layouts are React Server Components by default. Add `"use client"`
  only when a component actually needs state or browser APIs.
- Store-level configuration lives in `src/lib/site.js` so it can later be
  swapped for environment variables or backend-provided settings.
