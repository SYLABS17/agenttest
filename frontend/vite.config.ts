import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: "0.0.0.0"
  },
  build: {
    outDir: "dist",
    sourcemap: true
  },
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version || "0.1.0")
  },
  test: {
    environment: "jsdom",
    setupFiles: "./vitest.setup.ts",
    css: true
  }
});
