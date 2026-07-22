import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// En local: API en :8000 y device-agent en :8210. En Docker Compose se
// sobreescriben con VITE_API_URL / VITE_DEVICE_URL.
// (8210 y no 8200: Windows reserva a menudo el 8200 en sus rangos excluidos.)
const apiTarget = process.env.VITE_API_URL ?? "http://localhost:8000";
const deviceTarget = process.env.VITE_DEVICE_URL ?? "http://127.0.0.1:8210";

const proxy = {
  "/api": { target: apiTarget, changeOrigin: true },
  "/health": { target: apiTarget, changeOrigin: true },
  "/device": { target: deviceTarget, changeOrigin: true },
};

export default defineConfig(({ command }) => ({
  // En build usa rutas relativas para poder servir el kiosco bajo /app (la
  // landing ocupa la raíz). En desarrollo se sirve en la raíz como siempre.
  base: command === "build" ? "./" : "/",
  plugins: [react()],
  server: { port: 5173, proxy },
  preview: { port: 5173, proxy },
}));
