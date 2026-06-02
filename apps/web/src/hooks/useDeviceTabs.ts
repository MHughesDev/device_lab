// React hook that subscribes to DeviceTabStore — Phase 11

import { useEffect, useSyncExternalStore } from "react"
import { DeviceTabStore } from "@/stores/deviceTabs"

export function useDeviceTabs() {
  const tabs = useSyncExternalStore(
    DeviceTabStore.subscribe,
    DeviceTabStore.getTabs,
    DeviceTabStore.getTabs,
  )
  const activeId = useSyncExternalStore(
    DeviceTabStore.subscribe,
    DeviceTabStore.getActiveId,
    DeviceTabStore.getActiveId,
  )
  return { tabs, activeId }
}
