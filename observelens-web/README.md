# observelens-web

ObserveLens web console, built with Next.js App Router and TypeScript.

## Getting started

```bash
pnpm install
cp .env.example .env.local
pnpm dev
```

Open [http://localhost:3080](http://localhost:3080).

The same workflows are available through `make`, for example `make install`, `make env`, and `make dev`.

## Quality checks

```bash
pnpm typecheck
pnpm lint
pnpm format:check
pnpm test
pnpm build
```

## Project conventions

- Place route UI in `src/app` and reusable UI in `src/components`.
- Keep service queries and mutations in feature-specific modules; route components must not perform low-level HTTP requests.
- Use TanStack Query for server state and Zustand only for lightweight client UI state.
- Validate user-entered forms with React Hook Form and Zod.
- Read `../Agent.md` before adding or changing features.
