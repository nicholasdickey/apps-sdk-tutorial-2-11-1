# Pizzaz MCP server (Node)

This directory contains a minimal Model Context Protocol (MCP) server implemented with the official TypeScript SDK. The server exposes the full suite of Pizzaz demo widgets so you can experiment with UI-bearing tools in ChatGPT developer mode.

The server runs as a **single web service** that serves both:
- **MCP endpoints**: `GET /mcp` (SSE), `POST /mcp/messages`
- **Static assets**: built widget HTML, JS, and CSS at `/`

## Prerequisites

- Node.js 18+
- pnpm (recommended; npm/yarn also work)

## Install and build (from repo root)

```bash
# From openai-apps-sdk-examples root
pnpm install
pnpm run build:pizzaz   # Builds only Pizzaz widgets with origin-relative URLs
```

## Run the server

```bash
# From repo root
pnpm run start:pizzaz
```

Or from this directory:

```bash
pnpm start
```

The server listens on port 8000 (or `PORT` env). It serves MCP over SSE and static assets from the built `assets/` directory. Add the deployment URL to allowed domains in MCP configuration.

## Deploy to Render.com

The repo includes `render.yaml` for one-click deployment. After deploying, add your Render URL (e.g. `https://pizzaz-mcp-xxxx.onrender.com`) to the MCP allowed domains list.

Each tool responds with:

- `content`: a short text confirmation that mirrors the original Pizzaz examples.
- `structuredContent`: a small JSON payload that echoes the topping argument, demonstrating how to ship data alongside widgets.
- `_meta.openai/outputTemplate`: metadata that binds the response to the matching Skybridge widget shell.

Feel free to extend the handlers with real data sources, authentication, and persistence.
