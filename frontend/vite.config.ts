import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "/acc/",
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      "/api/v1": {
        target: "http://127.0.0.1:8005",
        changeOrigin: true,
      },
      "/acc-api/v1": {
        target: "http://127.0.0.1:8005",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/acc-api\/v1/, "/api/v1"),
      },
    },
  },
  // @ts-ignore
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/__tests__/setup.ts",
  },
});
