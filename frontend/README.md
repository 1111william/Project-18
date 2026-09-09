# Project 18 Frontend

Minimal Vue 3 + Vite frontend for the Bangla Learning Platform.
The interface is in English; the learning language is Bangla.

## Requirements

Node.js 22.12+ (or a newer supported LTS version), with npm.

## Run locally

From the repository root:

```sh
cd frontend
npm ci
npm run dev
```

Open the local URL printed in the terminal (normally http://localhost:5173).

## Build

```sh
npm run build
npm run preview
```

## Files

- `src/App.vue`: initial page
- `src/main.js`: Vue entry point
- `src/style.css`: base styles
- `vite.config.js`: Vite configuration

This initial setup does not include routing, authentication, learning modules,
or backend integration. The existing backend is maintained separately.
