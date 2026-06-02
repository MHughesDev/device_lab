// Reusable setting row — label + description + input — Phase 12

import type { ReactNode } from "react"

interface Props {
  label: string
  description?: string
  children: ReactNode
  indent?: boolean
}

export function SettingRow({ label, description, children, indent }: Props) {
  return (
    <div className={`flex items-start justify-between gap-8 py-3 ${indent ? "ml-4 border-l pl-4" : "border-b"}`}>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium">{label}</p>
        {description && (
          <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
        )}
      </div>
      <div className="shrink-0 w-64">{children}</div>
    </div>
  )
}
