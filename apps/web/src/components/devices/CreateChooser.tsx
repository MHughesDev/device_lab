// New/Existing chooser dialog — Phase 11 (11-03)
// Opens from the "+" button in the workspace tab strip.

import { Monitor, FolderOpen } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

interface Props {
  open: boolean
  onClose(): void
  onNew(): void
  onExisting(): void
}

export function CreateChooser({ open, onClose, onNew, onExisting }: Props) {
  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Open a device</DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-2 gap-3 pt-2">
          <button
            onClick={onNew}
            className="flex flex-col items-center gap-3 rounded-lg border-2 border-transparent bg-muted p-6 text-sm font-medium hover:border-primary hover:bg-muted/80 transition-colors"
          >
            <Monitor className="h-8 w-8 text-primary" />
            <div className="text-center">
              <p className="font-semibold">New device</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                Fresh environment from a template
              </p>
            </div>
          </button>

          <button
            onClick={onExisting}
            className="flex flex-col items-center gap-3 rounded-lg border-2 border-transparent bg-muted p-6 text-sm font-medium hover:border-primary hover:bg-muted/80 transition-colors"
          >
            <FolderOpen className="h-8 w-8 text-primary" />
            <div className="text-center">
              <p className="font-semibold">From manifest</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                Restore a saved environment
              </p>
            </div>
          </button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
