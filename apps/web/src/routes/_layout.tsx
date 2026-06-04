import { createFileRoute, Outlet, redirect, useRouterState } from "@tanstack/react-router"

import { Footer } from "@/components/Common/Footer"
import AppSidebar from "@/components/Sidebar/AppSidebar"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout")({
  component: Layout,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
      })
    }
  },
})

function Layout() {
  const pathname = useRouterState({ select: (s) => s.location.pathname })
  const isWorkspace = pathname === "/workspace"

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className={isWorkspace ? "overflow-hidden" : ""}>
        <header className="sticky top-0 z-10 flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1 text-muted-foreground" />
        </header>
        {isWorkspace ? (
          <div className="flex-1 min-h-0 overflow-hidden">
            <Outlet />
          </div>
        ) : (
          <>
            <main className="flex-1 p-6 md:p-8">
              <div className="mx-auto max-w-7xl">
                <Outlet />
              </div>
            </main>
            <Footer />
          </>
        )}
      </SidebarInset>
    </SidebarProvider>
  )
}

export default Layout
