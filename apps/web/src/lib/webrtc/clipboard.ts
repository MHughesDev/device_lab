// Bidirectional clipboard sync over a dedicated RTCDataChannel — Phase 11 (11-08)
// Off by default; enabled via the options menu.

interface ClipboardMessage {
  direction: "host_to_device" | "device_to_host"
  text: string
}

export class ClipboardSync {
  private channel: RTCDataChannel
  private _enabled = false
  private pasteHandler: ((e: ClipboardEvent) => void) | null = null

  constructor(channel: RTCDataChannel) {
    this.channel = channel
    channel.onmessage = (e) => {
      if (!this._enabled) return
      try {
        const msg: ClipboardMessage = JSON.parse(e.data as string)
        if (msg.direction === "device_to_host") {
          navigator.clipboard.writeText(msg.text).catch(() => {})
        }
      } catch { /* ignore malformed */ }
    }
  }

  get enabled() { return this._enabled }

  enable() {
    if (this._enabled) return
    this._enabled = true
    this.pasteHandler = (e) => {
      const text = e.clipboardData?.getData("text/plain") ?? ""
      if (text && this.channel.readyState === "open") {
        this.channel.send(
          JSON.stringify({ direction: "host_to_device", text } satisfies ClipboardMessage),
        )
      }
    }
    document.addEventListener("paste", this.pasteHandler)
  }

  disable() {
    if (!this._enabled) return
    this._enabled = false
    if (this.pasteHandler) {
      document.removeEventListener("paste", this.pasteHandler)
      this.pasteHandler = null
    }
  }

  toggle() {
    this._enabled ? this.disable() : this.enable()
  }
}
