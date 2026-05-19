// joblab web — Vite config
// Purpose: React + TS dev server on 0.0.0.0:5173 with HMR via polling (Docker bind mount).
// Created: 2026-05-19

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
    watch: { usePolling: true, interval: 300 },
  },
});
