// Input event serialization over WebRTC data channel — Phase 11 (11-07)
// Events are JSON-encoded; the backend InputEvent dataclass mirrors these fields.

export interface InputSender {
  move(x: number, y: number): void
  mousedown(x: number, y: number, button: number): void
  mouseup(x: number, y: number, button: number): void
  scroll(x: number, y: number, dx: number, dy: number): void
  keydown(key: string, modifiers: string[]): void
  keyup(key: string, modifiers: string[]): void
  keytext(text: string): void
}

function send(ch: RTCDataChannel, obj: object) {
  if (ch.readyState === "open") {
    try { ch.send(JSON.stringify(obj)) } catch { /* channel closing */ }
  }
}

export function createInputSender(channel: RTCDataChannel): InputSender {
  return {
    move: (x, y) =>
      send(channel, { kind: "move", x, y }),
    mousedown: (x, y, button) =>
      send(channel, { kind: "mousedown", x, y, button }),
    mouseup: (x, y, button) =>
      send(channel, { kind: "mouseup", x, y, button }),
    scroll: (x, y, dx, dy) =>
      send(channel, { kind: "scroll", x, y, dx, dy }),
    keydown: (key, modifiers) =>
      send(channel, { kind: "keydown", key, modifiers }),
    keyup: (key, modifiers) =>
      send(channel, { kind: "keyup", key, modifiers }),
    keytext: (text) =>
      send(channel, { kind: "keytext", text }),
  }
}

export function getModifiers(e: KeyboardEvent | MouseEvent): string[] {
  const mods: string[] = []
  if (e.ctrlKey) mods.push("ctrl")
  if (e.shiftKey) mods.push("shift")
  if (e.altKey) mods.push("alt")
  if (e.metaKey) mods.push("meta")
  return mods
}
