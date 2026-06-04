// stores/deviceTabs.ts — tabbed workspace state (Phase 11, tasks 11-01 + 11-02)
//
// Manages the set of open device tabs. Tab close never terminates a device.
// Persists open tab IDs to localStorage for session restore on reload.

const STORAGE_KEY = "devicelab-tabs-v1"

export interface DeviceTab {
  id: string
  title: string
  family: string
  state: string
  displayMode: "headless" | "interactive"
  mcpExposed: boolean
  pinned: boolean
}

type StoredState = { openIds: string[]; activeId: string | null }

function loadStored(): StoredState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : { openIds: [], activeId: null }
  } catch {
    return { openIds: [], activeId: null }
  }
}

function saveStored(state: StoredState) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch {}
}

// ── In-memory tab registry (not React state — avoids prop-drilling)
//    React components subscribe via event listeners.

let _tabs: DeviceTab[] = []
let _activeId: string | null = null
const _listeners = new Set<() => void>()

function notify() {
  _listeners.forEach((fn) => fn())
}

function persist() {
  saveStored({
    openIds: _tabs.map((t) => t.id),
    activeId: _activeId,
  })
}

export const DeviceTabStore = {
  // Hydrate from localStorage given a list of live devices
  hydrate(liveDevices: DeviceTab[]) {
    const stored = loadStored()
    const liveMap = new Map(liveDevices.map((d) => [d.id, d]))
    _tabs = stored.openIds
      .filter((id) => liveMap.has(id))
      .map((id) => liveMap.get(id)!)
    _activeId = _tabs.find((t) => t.id === stored.activeId)?.id ?? _tabs[0]?.id ?? null
    notify()
  },

  getTabs() { return _tabs },
  getActiveId() { return _activeId },

  openTab(tab: DeviceTab) {
    if (_tabs.some((t) => t.id === tab.id)) {
      _activeId = tab.id
    } else {
      _tabs = [..._tabs, tab]
      _activeId = tab.id
    }
    persist()
    notify()
  },

  closeTab(id: string) {
    const idx = _tabs.findIndex((t) => t.id === id)
    _tabs = _tabs.filter((t) => t.id !== id)
    if (_activeId === id) {
      _activeId = _tabs[idx]?.id ?? _tabs[idx - 1]?.id ?? null
    }
    persist()
    notify()
  },

  activateTab(id: string) {
    _activeId = id
    persist()
    notify()
  },

  updateTab(id: string, patch: Partial<DeviceTab>) {
    _tabs = _tabs.map((t) => (t.id === id ? { ...t, ...patch } : t))
    notify()
  },

  pinTab(id: string, pinned: boolean) {
    _tabs = _tabs.map((t) => (t.id === id ? { ...t, pinned } : t))
    persist()
    notify()
  },

  isOpen(id: string) { return _tabs.some((t) => t.id === id) },

  subscribe(fn: () => void) {
    _listeners.add(fn)
    return () => _listeners.delete(fn)
  },
}
