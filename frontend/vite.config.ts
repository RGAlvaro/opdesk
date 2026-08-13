// Vite and Vitest configuration for the React frontend.

import react from "@vitejs/plugin-react";
import { configDefaults, defineConfig } from "vitest/config";

const workspaceRoot = new URL("..", import.meta.url).pathname;
const apiProxyTarget =
  process.env.VITE_API_PROXY_TARGET ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    allowedHosts: ["frontend", "localhost", "127.0.0.1"],
    fs: {
      allow: [workspaceRoot],
    },
    proxy: {
      "/api": {
        target: apiProxyTarget,
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: "jsdom",
    exclude: [...configDefaults.exclude, "e2e/**"],
    globals: true,
    setupFiles: "./vitest.setup.ts",
  },
});
