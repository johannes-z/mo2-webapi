# Frontend Integration Guide

## Development Workflow

### 1. Project Structure

```
mo2-webapi-plugin/
├── frontend/              # Your Vite/Bun project
│   ├── src/
│   ├── dist/             # Built files (gitignore this)
│   ├── package.json
│   ├── vite.config.ts
│   └── ...
├── server_http.py
├── webapi_plugin.py
└── ...
```

### 2. Development Mode (with HMR)

**In your frontend project (`vite.config.ts`):**

```typescript
import { defineConfig } from "vite";

export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      "/mods": "http://localhost:5000",
      "/health": "http://localhost:5000",
      "/profile": "http://localhost:5000",
    },
  },
});
```

**Run both:**

```bash
# Terminal 1: MO2 with plugin running (API on port 5000)
# Start Mod Organizer 2

# Terminal 2: Frontend dev server (on port 5173)
cd frontend
bun dev
```

Open `http://localhost:5173` - you get full HMR + API calls proxied to the plugin!

### 3. Production Build

**Build for distribution:**

```bash
cd frontend
bun run build
```

This creates `frontend/dist/` with:

- `index.html`
- `assets/*.js`
- `assets/*.css`
- etc.

**The plugin automatically serves these files:**

- `http://localhost:5000/` → serves `index.html`
- `http://localhost:5000/assets/main.js` → serves JS
- API endpoints like `/mods` still work as normal

### 4. Package.json Scripts

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "build:watch": "vite build --watch"
  }
}
```

### 5. API Client Setup

**In your frontend (`src/api.ts`):**

```typescript
const API_BASE = import.meta.env.DEV
  ? "http://localhost:5000" // Dev: direct to plugin
  : ""; // Prod: same origin

export async function getMods() {
  const res = await fetch(`${API_BASE}/mods`);
  return res.json();
}

export async function enableMod(name: string) {
  await fetch(`${API_BASE}/mods/enable`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
}
```

### 6. WebSocket Setup

```typescript
const WS_URL = import.meta.env.DEV
  ? "ws://localhost:5001"
  : `ws://${window.location.hostname}:5001`;

const ws = new WebSocket(WS_URL);
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Event:", data);
};
```

## Distribution

When distributing your plugin:

1. **Build the frontend:**

   ```bash
   cd frontend && bun run build
   ```

2. **Include `frontend/dist/` in your plugin folder**

3. **Users get:**
   - API at `http://localhost:5000`
   - UI at `http://localhost:5000/` (automatically served)
   - WebSocket at `ws://localhost:5001`

## Tips

### Hot Reload During Dev

Run `bun run build --watch` in a terminal to auto-rebuild on save. Then just refresh browser (not full HMR but close).

### CORS

The plugin already sets CORS headers, so dev mode works seamlessly.

### Debugging

- Check MO2 logs for plugin errors
- Check browser console for frontend errors
- API available at `http://localhost:5000/health`

### .gitignore

```gitignore
frontend/dist/
frontend/node_modules/
```

## Example Frontend (React/Vue/Svelte)

**Quick start:**

```bash
cd mo2-webapi-plugin
mkdir frontend && cd frontend

# Pick one:
bun create vite . --template react-ts
bun create vite . --template vue-ts
bun create vite . --template svelte-ts

bun install
bun dev
```

Then just follow the API client setup above!

## No Frontend?

If `frontend/dist/` doesn't exist, the plugin runs in API-only mode. You can:

- Use it from scripts
- Use it from external apps
- Build a frontend later
