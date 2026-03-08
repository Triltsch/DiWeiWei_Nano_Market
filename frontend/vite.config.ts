import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  // Set the third parameter to '' to load all env regardless of the `VITE_` prefix.
  const env = loadEnv(mode, process.cwd(), '');

  return {
    plugins: [react()],
    server: {
      host: env.VITE_DEV_SERVER_HOST ?? "localhost",
      port: 5173,
      proxy: {
        "/api": {
          target: env.VITE_API_BASE_URL ?? "http://localhost:8000",
          changeOrigin: true,
          // No rewrite - backend routes are already under /api/v1/*
        },
      },
    },
    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: ["./vitest.setup.ts"],
    },
  };
});
