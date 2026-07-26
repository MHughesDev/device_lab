import path from "node:path"
import tailwindcss from "@tailwindcss/vite"
import { tanstackRouter } from "@tanstack/router-plugin/vite"
import react from "@vitejs/plugin-react-swc"
import { defineConfig } from "vite"

const API_TARGET = process.env.VITE_API_URL ?? "http://localhost:8000"

// https://vitejs.dev/config/
export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  plugins: [
    tanstackRouter({
      target: "react",
      autoCodeSplitting: true,
    }),
    react(),
    tailwindcss(),
  ],
  server: {
    // Proxy relative /api/ and /mcp/ calls to the backend so `fetch("/api/v1/...")` works
    // in Vite dev mode exactly as it does in the Docker/Nginx setup.
    proxy: {
      "/api": {
        target: API_TARGET,
        changeOrigin: true,
      },
      "/mcp": {
        target: API_TARGET,
        changeOrigin: true,
        ws: true,
      },
    },
  },
})
