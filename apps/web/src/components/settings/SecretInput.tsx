// Write-only secret input — shows "configured" sentinel — Phase 12
// Never echoes back the stored secret value.

import { useState } from "react"
import { Eye, EyeOff } from "lucide-react"

interface Props {
  value: string | null  // "***" means stored; null/empty means not configured
  onChange(v: string): void
  placeholder?: string
}

export function SecretInput({ value, onChange, placeholder }: Props) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState("")
  const [show, setShow] = useState(false)

  const isConfigured = value === "***"

  if (!editing && isConfigured) {
    return (
      <div className="flex items-center gap-2">
        <span className="flex-1 rounded-md border bg-muted px-3 py-1.5 text-sm text-muted-foreground font-mono">
          ••••••••  (configured)
        </span>
        <button
          onClick={() => { setEditing(true); setDraft("") }}
          className="text-xs text-primary underline shrink-0"
        >
          Update
        </button>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <div className="relative flex-1">
        <input
          type={show ? "text" : "password"}
          className="w-full rounded-md border bg-background px-3 py-1.5 text-sm pr-8 focus:outline-none focus:ring-2 focus:ring-ring"
          placeholder={placeholder ?? "Enter value…"}
          value={editing ? draft : (value ?? "")}
          onChange={(e) => {
            if (editing) {
              setDraft(e.target.value)
              onChange(e.target.value)
            } else {
              onChange(e.target.value)
            }
          }}
          autoFocus={editing}
        />
        <button
          type="button"
          onClick={() => setShow(!show)}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground"
        >
          {show ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
        </button>
      </div>
      {editing && (
        <button
          onClick={() => { setEditing(false); setDraft("") }}
          className="text-xs text-muted-foreground underline shrink-0"
        >
          Cancel
        </button>
      )}
    </div>
  )
}
