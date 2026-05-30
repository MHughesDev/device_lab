---
doc_id: "23.8"
title: "Research notes — automation OCR and VLM"
section: "Research"
summary: "Skim notes on cross-platform AX/UIA, OCR tiers, OmniParser/VLM escalation, Wayland and TCC risks."
updated: "2026-05-17"
---

# Notes — Cross-platform automation, OCR/VLM, trees

## Observation pyramid (default → escalation)

1. **Structured:** AX / DOM / UIAutomator tree / UIA — always preferred [S025,S034,S032,S033].
2. **OCR:** Run **Tesseract** baseline + optional **Surya**/Paddle tier when GPU available — benchmark per template [Q17].
3. **Structured vision parsing:** **OmniParser-class** models before generic multimodal chat [S039].
4. **Full VLM:** BYO API keys only; budget-guarded; never default [S026–S028].

## Linux / Wayland

- Ship templates defaulting to **X11 or XWayland-known-good** stacks for automation reliability until GNOME/KDE Wayland AX maturity crosses threshold [Q11].
- Track **Newton** / AccessKit long-term.

## macOS / TCC

- Prefer **pre-baked AMI** attempts + documented sqlite/`tccutil` flows with clear warning: **fragile across macOS upgrades** [Q12].
- Surface permission gaps early via health checks.

## Windows

- Primary driver: **UIA via pywinauto** and/or **Appium Windows driver** [S031,S032].
- **FlaUI** optional speed path via hosted helper binary / Python.NET bridge when justified [Q13].

## Android

- Standardize **uiautomator2** server bootstrap in AMI bake step [Q14].
- Support **nested KVM** hosts **and** **Graviton+ARM images** per workload [S007,S008,S019].

## iOS Simulator

- Prefer structured snapshots via XCTest APIs; evaluate **`xctree`**-style exports for agent-friendly JSON trees [Q15].

## AX tree token pressure

- Implement pruning/diff strategies informed by **A11y-Compressor / FocusAgent / Prune4Web** literature — configurable aggression levels [Q16].

## Computer-use APIs benchmark context

- Claude/OpenAI/Gemini computer-use loops are **screenshot-heavy** — DeviceLab differentiates on structured observation + server-side waits [S026–S028].
