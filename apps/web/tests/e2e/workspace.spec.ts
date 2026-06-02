// E2E smoke test for the device workspace — Phase 11 (11-15)
// Mocks the API and stream so no real hardware is required.

import { expect, test } from "@playwright/test"

// These tests use a real browser against a running dev server.
// Stream and GPU functionality is mocked; UI state is asserted.

test.describe("Device workspace", () => {
  test.beforeEach(async ({ page }) => {
    // Mock device list
    await page.route("/api/v1/devices/", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            id: "00000000-0000-0000-0000-000000000001",
            family: "linux",
            name: "Test Env",
            display_mode: "headless",
            mcp_exposed: true,
            state: "ready",
            phase: null,
            cost_estimate: null,
            source_manifest_id: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ]),
      }),
    )

    // Mock templates
    await page.route("/api/v1/templates/", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          { id: "tmpl-1", family: "linux", location: "local", name: "Linux local", spec: {} },
        ]),
      }),
    )

    // Mock manifests
    await page.route("/api/v1/manifests/", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      }),
    )

    // Mock host resources
    await page.route("/api/v1/host/resources", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          total_ram_mb: 16384,
          committed_ram_mb: 2048,
          available_ram_mb: 14336,
          total_cpu_cores: 8,
          committed_cpu_cores: 2,
          device_count: 1,
          max_devices: 10,
        }),
      }),
    )

    // Mock device create
    await page.route("/api/v1/devices/", async (route) => {
      if (route.request().method() === "POST") {
        return route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            id: "00000000-0000-0000-0000-000000000002",
            family: "linux",
            name: "Test Env",
            display_mode: "headless",
            mcp_exposed: true,
            state: "requested",
            phase: null,
            cost_estimate: null,
            source_manifest_id: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }),
        })
      }
      return route.continue()
    })

    // Mock log stream (empty SSE)
    await page.route("/api/v1/devices/**/logs/stream", (route) =>
      route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: "",
      }),
    )

    // Mock PATCH device
    await page.route("/api/v1/devices/**", async (route) => {
      if (route.request().method() === "PATCH") {
        return route.fulfill({ status: 200, contentType: "application/json", body: "{}" })
      }
      return route.continue()
    })
  })

  test("workspace page loads with empty state when no tabs open", async ({ page }) => {
    // Clear localStorage tab state
    await page.addInitScript(() => {
      localStorage.removeItem("devicelab-tabs-v1")
    })

    await page.goto("/workspace")

    await expect(page.getByText("No devices open")).toBeVisible()
    await expect(page.getByRole("button", { name: /open a device/i })).toBeVisible()
  })

  test("+ button opens the New/Existing chooser dialog", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.removeItem("devicelab-tabs-v1")
    })

    await page.goto("/workspace")
    await page.getByRole("button", { name: "Open a device" }).click()

    await expect(page.getByRole("dialog")).toBeVisible()
    await expect(page.getByText("New device")).toBeVisible()
    await expect(page.getByText("From manifest")).toBeVisible()
  })

  test("New device wizard collects OS / display-mode / MCP / name", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.removeItem("devicelab-tabs-v1")
    })

    await page.goto("/workspace")

    // open chooser → new
    await page.getByRole("button", { name: "Open a device" }).click()
    await page.getByText("New device").click()

    // step 1: OS
    await expect(page.getByText("Operating system")).toBeVisible()
    await page.getByRole("button", { name: /next/i }).click()

    // step 2: display mode
    await expect(page.getByText("Display mode")).toBeVisible()
    await page.getByText("Headless (agent-only)").click()
    await page.getByRole("button", { name: /next/i }).click()

    // step 3: MCP
    await expect(page.getByText("MCP exposure")).toBeVisible()
    await page.getByRole("button", { name: /next/i }).click()

    // step 4: name
    await expect(page.getByPlaceholder(/linux/i)).toBeVisible()
    await page.getByPlaceholder(/linux/i).fill("Test Env")

    // summary shows chosen values
    await expect(page.getByText("headless")).toBeVisible()
    await expect(page.getByText("exposed")).toBeVisible()
  })

  test("tab opens after device creation and close does not terminate", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.removeItem("devicelab-tabs-v1")
    })

    // Track terminate calls — should remain 0
    const terminateCalls: string[] = []
    await page.route("**/lifecycle/terminate", (route) => {
      terminateCalls.push(route.request().url())
      return route.fulfill({ status: 200, contentType: "application/json", body: "{}" })
    })

    await page.goto("/workspace")
    await page.getByRole("button", { name: "Open a device" }).click()
    await page.getByText("New device").click()

    // skip through wizard quickly
    await page.getByRole("button", { name: /next/i }).click()
    await page.getByRole("button", { name: /next/i }).click()
    await page.getByRole("button", { name: /next/i }).click()
    await page.getByRole("button", { name: /create device/i }).click()

    // wait for tab to appear
    await expect(page.getByText("Test Env")).toBeVisible({ timeout: 5_000 })

    // close the tab
    await page.getByRole("button", { name: /close test env/i }).click()

    // no terminate calls made
    expect(terminateCalls).toHaveLength(0)
  })

  test("device from list opens in workspace as tab", async ({ page }) => {
    await page.goto("/devices")

    // The mock device "Test Env" should appear with an Open button
    await expect(page.getByText("Test Env")).toBeVisible({ timeout: 5_000 })
    await page.getByRole("button", { name: "Open" }).first().click()

    // Should navigate to workspace
    await expect(page).toHaveURL("/workspace")
    await expect(page.getByText("Test Env")).toBeVisible()
  })

  test("resource HUD shows host budget", async ({ page }) => {
    await page.goto("/workspace")
    // HUD pulls from /api/v1/host/resources which we mocked
    await expect(page.getByText(/host budget/i)).toBeVisible({ timeout: 5_000 })
    await expect(page.getByText(/1\/10 devices/i)).toBeVisible()
  })
})
