import { defineConfig, devices } from "@playwright/test";

// Tests de accesibilidad (TT-701). Se ejecutan contra el build servido por
// `vite preview`. Sin backend, el kiosco entra en modo demostración: las
// pantallas se renderizan igual, así que la auditoría de accesibilidad no
// necesita la API.
export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  reporter: process.env.CI ? "line" : "list",
  use: {
    baseURL: "http://localhost:4173",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npm run preview -- --port 4173 --strictPort",
    url: "http://localhost:4173",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
