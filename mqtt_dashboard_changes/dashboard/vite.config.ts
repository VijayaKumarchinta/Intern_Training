import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// Flask (waitress) runs on :8080; proxying avoids CORS in development.
export default defineConfig({
  plugins: [vue()],
  server: { proxy: { "/dashboard": "http://localhost:8080" } },
});
