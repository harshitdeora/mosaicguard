import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  timeout: 180000,
  expect: { timeout: 15000 },
  workers: 1,
  retries: 0,
  use: {
    baseURL: "http://127.0.0.1:8028",
    channel: process.platform === "win32" ? "msedge" : undefined,
    actionTimeout: 15000,
    navigationTimeout: 15000,
    viewport: { width: 1440, height: 1000 },
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  reporter: [
    ["list"],
    ["json", { outputFile: "../docs/browser-results.json" }],
  ],
  webServer: {
    command:
      (process.platform === "win32"
        ? "..\\.venv\\Scripts\\python.exe"
        : "../.venv/bin/python") + " ../scripts/browser_server.py",
    url: "http://127.0.0.1:8028/api/health",
    reuseExistingServer: false,
    timeout: 30000,
  },
});
