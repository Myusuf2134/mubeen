import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      manifest: {
        name: "Mubeen — Masjid Directory & Khutbah Captions",
        short_name: "Mubeen",
        description: "Find masjid prayer times and follow live khutbah captions",
        start_url: "/",
        display: "standalone",
        background_color: "#f9fafb",
        theme_color: "#059669",
        lang: "en",
        icons: [
          {
            src: "/icon-192.png",
            sizes: "192x192",
            type: "image/png",
            purpose: "any maskable",
          },
          {
            src: "/icon-512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "any maskable",
          },
        ],
      },
      workbox: {
        // Cache the API search results briefly so the directory is usable offline
        runtimeCaching: [
          {
            urlPattern: /^\/api\/masjids\/[^/]+$/,
            handler: "StaleWhileRevalidate",
            options: {
              cacheName: "masjid-detail",
              expiration: { maxEntries: 50, maxAgeSeconds: 3600 },
            },
          },
        ],
      },
    }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
