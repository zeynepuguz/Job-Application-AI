import { defineConfig } from "vite";

/** Geliştirme: tarayıcı istekleri Vite'a gider, proxy backend'e iletir (CORS gerekmez). */
export default defineConfig({
  server: {
    port: 5174,
    strictPort: true,
    proxy: {
      "/auth": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/applications": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/companies": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
