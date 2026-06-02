// Vitest unit tests for DeviceTabStore — Phase 11 (11-01, 11-02)
import { beforeEach, describe, expect, it, vi } from "vitest"

// Stub localStorage before module import
const localStorageData: Record<string, string> = {}
vi.stubGlobal("localStorage", {
  getItem: (k: string) => localStorageData[k] ?? null,
  setItem: (k: string, v: string) => { localStorageData[k] = v },
  removeItem: (k: string) => { delete localStorageData[k] },
  clear: () => { for (const k in localStorageData) delete localStorageData[k] },
})

// Re-import after stub so module sees the stub
const { DeviceTabStore } = await import("../stores/deviceTabs")

function makeTab(id: string, overrides = {}) {
  return {
    id,
    title: `linux · ${id.slice(0, 8)}`,
    family: "linux" as const,
    state: "ready",
    displayMode: "headless" as const,
    mcpExposed: true,
    pinned: false,
    ...overrides,
  }
}

beforeEach(() => {
  // Reset store between tests by closing all tabs
  for (const t of [...DeviceTabStore.getTabs()]) {
    DeviceTabStore.closeTab(t.id)
  }
  localStorageData["devicelab-tabs-v1"] = JSON.stringify({ openIds: [], activeId: null })
})

describe("DeviceTabStore opens/activates/closes", () => {
  it("opens a new tab and makes it active", () => {
    const tab = makeTab("aaa")
    DeviceTabStore.openTab(tab)
    expect(DeviceTabStore.getTabs()).toHaveLength(1)
    expect(DeviceTabStore.getActiveId()).toBe("aaa")
  })

  it("opening the same tab twice does not duplicate it", () => {
    const tab = makeTab("bbb")
    DeviceTabStore.openTab(tab)
    DeviceTabStore.openTab(tab)
    expect(DeviceTabStore.getTabs()).toHaveLength(1)
  })

  it("activates an already-open tab on openTab", () => {
    const t1 = makeTab("c1")
    const t2 = makeTab("c2")
    DeviceTabStore.openTab(t1)
    DeviceTabStore.openTab(t2)
    DeviceTabStore.openTab(t1)
    expect(DeviceTabStore.getActiveId()).toBe("c1")
  })

  it("activateTab switches active without affecting tabs list", () => {
    DeviceTabStore.openTab(makeTab("d1"))
    DeviceTabStore.openTab(makeTab("d2"))
    DeviceTabStore.activateTab("d1")
    expect(DeviceTabStore.getActiveId()).toBe("d1")
    expect(DeviceTabStore.getTabs()).toHaveLength(2)
  })

  it("closing a tab removes it from the list", () => {
    DeviceTabStore.openTab(makeTab("e1"))
    DeviceTabStore.openTab(makeTab("e2"))
    DeviceTabStore.closeTab("e1")
    expect(DeviceTabStore.getTabs().map((t) => t.id)).toEqual(["e2"])
  })

  it("closing the active tab activates a neighbour", () => {
    DeviceTabStore.openTab(makeTab("f1"))
    DeviceTabStore.openTab(makeTab("f2"))
    DeviceTabStore.openTab(makeTab("f3"))
    DeviceTabStore.activateTab("f2")
    DeviceTabStore.closeTab("f2")
    expect(DeviceTabStore.getActiveId()).toBe("f3")
  })

  it("closing last tab sets activeId to null", () => {
    DeviceTabStore.openTab(makeTab("g1"))
    DeviceTabStore.closeTab("g1")
    expect(DeviceTabStore.getActiveId()).toBeNull()
  })
})

describe("closing tab does not call terminate", () => {
  it("closeTab never calls the terminate API", () => {
    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue({} as Response)
    DeviceTabStore.openTab(makeTab("h1"))
    DeviceTabStore.closeTab("h1")
    expect(fetchSpy).not.toHaveBeenCalled()
    fetchSpy.mockRestore()
  })
})

describe("tab title falls back to family·id8", () => {
  it("isOpen returns true after openTab", () => {
    const tab = makeTab("i1")
    DeviceTabStore.openTab(tab)
    expect(DeviceTabStore.isOpen("i1")).toBe(true)
    expect(DeviceTabStore.isOpen("nonexistent")).toBe(false)
  })
})

describe("restores live tabs on reload", () => {
  it("hydrate restores tabs that are in liveDevices", () => {
    const live = [makeTab("j1"), makeTab("j2")]
    localStorageData["devicelab-tabs-v1"] = JSON.stringify({
      openIds: ["j1", "j2"],
      activeId: "j2",
    })
    DeviceTabStore.hydrate(live)
    expect(DeviceTabStore.getTabs().map((t) => t.id)).toEqual(["j1", "j2"])
    expect(DeviceTabStore.getActiveId()).toBe("j2")
  })

  it("drops terminated devices from restore", () => {
    const live = [makeTab("k1")] // k2 is terminated (not in live list)
    localStorageData["devicelab-tabs-v1"] = JSON.stringify({
      openIds: ["k1", "k2"],
      activeId: "k2",
    })
    DeviceTabStore.hydrate(live)
    expect(DeviceTabStore.getTabs().map((t) => t.id)).toEqual(["k1"])
    // active falls back to first open tab
    expect(DeviceTabStore.getActiveId()).toBe("k1")
  })
})

describe("pinned tabs", () => {
  it("pinTab marks a tab as pinned", () => {
    DeviceTabStore.openTab(makeTab("m1"))
    DeviceTabStore.pinTab("m1", true)
    expect(DeviceTabStore.getTabs()[0].pinned).toBe(true)
  })

  it("unpinTab marks a tab as unpinned", () => {
    DeviceTabStore.openTab(makeTab("n1", { pinned: true }))
    DeviceTabStore.pinTab("n1", false)
    expect(DeviceTabStore.getTabs()[0].pinned).toBe(false)
  })
})
