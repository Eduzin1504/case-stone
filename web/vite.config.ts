import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

const API = "http://localhost:8600";

export default defineConfig(({ mode }) => {
  const exemplos = loadEnv(mode, ".", "VITE_").VITE_EXEMPLOS === "1";
  return {
    plugins: [react()],
    server: { port: 5173, strictPort: true, proxy: { "/api": API, "/midia": API } },
    build: { outDir: "dist" },
    // public/ só tem as mídias do modo exemplos: fora dele, não vai para o dist
    publicDir: exemplos ? "public" : false,
  };
});
