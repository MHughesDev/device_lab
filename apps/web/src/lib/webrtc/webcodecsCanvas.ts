// Optional WebCodecs low-latency canvas path — Phase 11 (11-11)
// Default is the <video> element; this is an advanced power-user toggle.
// Falls back gracefully if VideoDecoder is unavailable.

export class WebCodecsCanvas {
  private decoder: VideoDecoder | null = null
  private canvas: HTMLCanvasElement
  private ctx: CanvasRenderingContext2D | null

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas
    this.ctx = canvas.getContext("2d")
  }

  static isSupported(): boolean {
    return typeof VideoDecoder !== "undefined"
  }

  async init(): Promise<void> {
    if (!WebCodecsCanvas.isSupported()) throw new Error("VideoDecoder not supported in this browser")

    this.decoder = new VideoDecoder({
      output: (frame) => {
        if (this.ctx) {
          this.canvas.width = frame.displayWidth
          this.canvas.height = frame.displayHeight
          this.ctx.drawImage(frame, 0, 0)
        }
        frame.close()
      },
      error: (e) => console.warn("[WebCodecs] decoder error:", e),
    })

    this.decoder.configure({
      codec: "avc1.640028",
      hardwareAcceleration: "prefer-hardware",
    })
  }

  pushAU(data: Uint8Array, keyFrame: boolean) {
    if (this.decoder?.state !== "configured") return
    this.decoder.decode(
      new EncodedVideoChunk({
        type: keyFrame ? "key" : "delta",
        timestamp: performance.now() * 1_000,
        data,
      }),
    )
  }

  close() {
    try { this.decoder?.close() } catch { /* already closed */ }
  }
}
