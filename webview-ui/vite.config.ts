import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { resolve } from "path";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],

  build: {
    // Output the built webview app where the extension can find it
    outDir: resolve(__dirname, "../dist/webview-ui"),
    emptyOutDir: true,
  },

  // Webviews must load assets from relative paths (no leading slash)
  base: "./",
});
