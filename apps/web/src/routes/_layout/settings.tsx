import { createFileRoute } from "@tanstack/react-router"

import ChangePassword from "@/components/UserSettings/ChangePassword"
import DeleteAccount from "@/components/UserSettings/DeleteAccount"
import UserInformation from "@/components/UserSettings/UserInformation"
import { InfraSettings } from "@/components/settings/InfraSettings"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/settings")({
  component: UserSettings,
  head: () => ({
    meta: [{ title: "DeviceLab — Settings" }],
  }),
})

function UserSettings() {
  const { user: currentUser } = useAuth()

  if (!currentUser) return null

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Manage your account and DeviceLab infrastructure configuration
        </p>
      </div>

      <Tabs defaultValue="my-profile">
        <TabsList>
          <TabsTrigger value="my-profile">My profile</TabsTrigger>
          <TabsTrigger value="password">Password</TabsTrigger>
          {currentUser.is_superuser && (
            <TabsTrigger value="infrastructure">Infrastructure</TabsTrigger>
          )}
          <TabsTrigger value="danger-zone">Danger zone</TabsTrigger>
        </TabsList>

        <TabsContent value="my-profile">
          <UserInformation />
        </TabsContent>
        <TabsContent value="password">
          <ChangePassword />
        </TabsContent>
        {currentUser.is_superuser && (
          <TabsContent value="infrastructure">
            <div className="mt-4">
              <InfraSettings />
            </div>
          </TabsContent>
        )}
        <TabsContent value="danger-zone">
          <DeleteAccount />
        </TabsContent>
      </Tabs>
    </div>
  )
}
