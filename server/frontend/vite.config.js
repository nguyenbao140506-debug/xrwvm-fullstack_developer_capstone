import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  publicDir: "static",
  base: "/static/",
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/djangoapp": "http://127.0.0.1:8000",
      "/admin": "http://127.0.0.1:8000",
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/setupTests.js",
  },
});
