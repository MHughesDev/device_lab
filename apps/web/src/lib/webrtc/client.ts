// WebRTC session negotiation — Phase 11 (11-07)

export interface WebRTCSession {
  peer: RTCPeerConnection
  videoTrack: MediaStreamTrack | null
  audioTrack: MediaStreamTrack | null
  inputChannel: RTCDataChannel
  clipboardChannel: RTCDataChannel
  sessionToken: string
  close(): void
}

interface NegotiateResponse {
  sdp_answer: string
  session_token: string
  ice_servers?: RTCIceServer[]
}

export async function negotiateSession(deviceId: string): Promise<WebRTCSession> {
  const peer = new RTCPeerConnection({ iceServers: [] })

  // Reliable channel for clipboard; unreliable for low-latency input moves
  const inputChannel = peer.createDataChannel("input", {
    ordered: false,
    maxRetransmits: 0,
  })
  const clipboardChannel = peer.createDataChannel("clipboard", { ordered: true })

  peer.addTransceiver("video", { direction: "recvonly" })
  peer.addTransceiver("audio", { direction: "recvonly" })

  const offer = await peer.createOffer()
  await peer.setLocalDescription(offer)

  // Wait up to 2 s for ICE gathering to complete
  await new Promise<void>((resolve) => {
    if (peer.iceGatheringState === "complete") { resolve(); return }
    const done = () => { if (peer.iceGatheringState === "complete") resolve() }
    peer.addEventListener("icegatheringstatechange", done)
    setTimeout(resolve, 2_000)
  })

  const res = await fetch("/api/v1/stream/negotiate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      device_id: deviceId,
      sdp_offer: peer.localDescription?.sdp,
    }),
  })
  if (!res.ok) throw new Error(`Stream negotiate failed: ${res.status}`)

  const { sdp_answer, session_token, ice_servers }: NegotiateResponse = await res.json()

  if (ice_servers?.length) {
    peer.setConfiguration({ iceServers: ice_servers })
  }

  await peer.setRemoteDescription({ type: "answer", sdp: sdp_answer })

  let videoTrack: MediaStreamTrack | null = null
  let audioTrack: MediaStreamTrack | null = null

  await new Promise<void>((resolve) => {
    let count = 0
    peer.ontrack = ({ track }) => {
      if (track.kind === "video") videoTrack = track
      if (track.kind === "audio") audioTrack = track
      if (++count >= 2) resolve()
    }
    setTimeout(resolve, 5_000)
  })

  return {
    peer,
    videoTrack,
    audioTrack,
    inputChannel,
    clipboardChannel,
    sessionToken: session_token,
    close() { peer.close() },
  }
}
