---
doc_id: "23.9"
title: "Research notes — network proxy and recipes"
section: "Research"
summary: "Skim notes on mitmproxy HTTP/3, pinning bypass ethics, YAML recipes, Playwright codegen, test outputs."
updated: "2026-05-17"
---

# Notes — Network interception, recipes, testing artifacts

## mitmproxy embedding

- Prefer **addon architecture** inside DeviceLab agent process for programmable routing/HAR capture [Q21].
- Document **HTTP/3**: mitmproxy 11 improves coverage but **Chrome QUIC + custom CA** remains painful — fall back to HTTP/2-only test modes when needed [Q22].

## TLS pinning / hardened apps

- Provide **optional recipes** using Frida/Objection-class tooling **only on disposable Android emulators** with explicit legal/ethical banner [Q23].
- iOS pinning bypass not a core promise — route through Device Farm / enterprise builds.

## Recipes DSL

- **Phase 1:** YAML declarative steps + **sandboxed Jinja** (`SandboxedEnvironment`) for variables [Q24].
- **Phase 2:** Signed Python recipes executed in **container-isolated** subprocess with syscall filtering — never raw `exec` in host context.
- **Recording:** Start from **Playwright codegen** output for browser flows; parallel patterns for mobile desktop factories later [Q25].

## Testing outputs

- Emit **JUnit XML** for CI interop + optional **Allure** richer UX / agent rerun helpers [Q30].

## Extension / stealth testing ethics

- Playwright supports **MV3 extension testing** via persistent Chromium contexts — document service worker suspension [S047].
- **Anti-bot stealth:** feature-flagged **only** for self-owned apps; reference Playwright stance against generic evasion [Q45].
