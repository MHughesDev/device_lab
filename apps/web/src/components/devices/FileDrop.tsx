// File push via drag-and-drop over the screen pane — Phase 11 (11-09)
// File pull available via the options menu.

import { useState, useCallback } from "react"
import { Upload } from "lucide-react"
import { toast } from "sonner"

const MAX_BYTES = 500 * 1024 * 1024 // 500 MB

interface Props {
  deviceId: string
  children: React.ReactNode
}

export function FileDrop({ deviceId, children }: Props) {
  const [dragging, setDragging] = useState(false)

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault()
      setDragging(false)

      const files = Array.from(e.dataTransfer.files)
      if (!files.length) return

      for (const file of files) {
        if (file.size > MAX_BYTES) {
          toast.error(`${file.name} exceeds 500 MB limit`)
          continue
        }
        const formData = new FormData()
        formData.append("file", file)
        formData.append("remote_path", `/tmp/${file.name}`)

        const toastId = toast.loading(`Pushing ${file.name}…`)
        try {
          const res = await fetch(`/api/v1/devices/${deviceId}/files/push`, {
            method: "POST",
            body: formData,
          })
          if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: res.statusText }))
            throw new Error(err.detail ?? res.statusText)
          }
          toast.success(`${file.name} pushed to /tmp/`, { id: toastId })
        } catch (err: unknown) {
          toast.error(`Failed to push ${file.name}: ${err instanceof Error ? err.message : String(err)}`, {
            id: toastId,
          })
        }
      }
    },
    [deviceId],
  )

  return (
    <div
      className="relative h-full"
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
    >
      {children}

      {dragging && (
        <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-primary/20 border-2 border-dashed border-primary rounded-lg pointer-events-none">
          <Upload className="h-10 w-10 text-primary mb-2" />
          <p className="text-sm font-medium text-primary">Drop to push to /tmp/</p>
        </div>
      )}
    </div>
  )
}
