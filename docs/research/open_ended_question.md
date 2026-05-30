---
doc_id: "23.2"
title: "DeviceLab open-ended design decisions"
section: "Research"
summary: "Answers and confidence levels for open architecture questions before freezing idea.md."
updated: "2026-05-17"
---

# Open-ended design questions — provisional answers

**Purpose:** Capture decisions needed before freezing `idea.md`.  
**Status:** Working baseline from web research + architecture passes (2026-05-17).  
**Confidence:** `H` high / `M` medium / `L` low — revisit when prototyping.

See also: [`SOURCES.md`](SOURCES.md), [`queries/queries-results.md`](queries/queries-results.md), [`notes/`](notes/).

---

## A1 — Local app shell, packaging, distribution

| # | Question | Provisional answer | Conf. | Evidence / notes |
|---|----------|-------------------|-------|------------------|
| 1 | Pure localhost vs Tauri vs Electron? | **Docker Compose + browser localhost** first; **Tauri optional** later for desktop polish/keychain UX. | M | Smaller ops burden than Electron; Tauri adds release/signing work [notes/local-stack-mcp-workers.md]. |
| 2 | Single-user vs multi-user one machine? | **Single-user local workspace** v1; multi-user = separate profiles + auth layer later (not SaaS). | M | Matches BYOC local-first thesis. |
| 3 | Auto-update strategy? | **Container tags + release notes**; optional package managers (`uv pip`) — no silent auto-update until stable channels exist. | H | OSS hygiene. |
| 4 | Telemetry? | **Default off**; optional anonymized diagnostics prompt. | H | Trust-sensitive audience. |
| 5 | Python version floor? | **3.12+** aligned with repo policy; revisit annually. | H | AGENTS / template baseline. |

## A2 — Backend frameworks

| # | Question | Provisional answer | Conf. | Evidence / notes |
|---|----------|-------------------|-------|------------------|
| 6 | MCP server framework? | **MCP Python SDK** core; evaluate **FastMCP** if composition/auth reduces glue code [S023,S024]. | M | FastMCP stats/marketing claims — validate in spike. |
| 7 | Background workers? | **In-process asyncio** default; **Redis + Taskiq/Dramatiq** profile for heavy parallelism [Q3]. | M | Avoid mandatory Redis for solo dev. |
| 8 | State-machine library? | **`transitions`** with exportable YAML definitions [S041]. | H | Fits explicit device FSM requirement. |
| 9 | Event bus? | **In-process pub/sub** first; Redis/NATS only when scaling profile on. | M | Complexity gate. |
| 10 | SQLite beyond WAL? | **Litestream optional** to user-owned S3/MinIO — not default [S040]. | H | DR without Postgres ops. |

## A3 — Runtime agent (`devicelab-agent`)

| # | Question | Provisional answer | Conf. | Evidence / notes |
|---|----------|-------------------|-------|------------------|
| 11 | Language | **Go** default for static cross-compiled agent binary + gRPC; **Python** acceptable for platform-specific scripting inside adapter VMs. | M | Trade velocity vs footprint [Q6]; spike both for Android bring-up. |
| 12 | Distribution | **Baked into AMI** + **SSM Run Command** delta updates [S009]. | M | Fast boot vs patch agility. |
| 13 | Transport | **gRPC bidirectional streams** over multiplexed tunnel; HTTP fallback for constrained environments. | M | Aligns with push observations + low-latency input [S043]. |
| 14 | Cross-compile matrix | Ship tier-1: **linux/amd64+arm64**, **windows/amd64**, **darwin/arm64**; defer darwin/amd64 if AWS Mac ARM-only. | M | AWS Mac ARM focus [S001]. |
| 15 | Code signing | **Recommended** for macOS/Windows agents distributed as binaries; OSS project signs releases via CI attestations [Q43]. | M | UX + malware resistance. |

## A4 — Streaming pipeline

| # | Question | Provisional answer | Conf. | Evidence / notes |
|---|----------|-------------------|-------|------------------|
| 16 | Signaling channel | **HTTPS/WebSocket signaling through local gateway** (localhost holds session state); remote peer is browser viewer. | M | Keeps cloud instances dumb clients of DeviceLab session. |
| 17 | TURN ownership | **User-deployed coturn** (small EC2) with IaC snippet — credentials rotated per workspace [Q8]. | H | No DeviceLab-hosted relay (BYOC). |
| 18 | Codec default | **H.264** baseline compatibility; **AV1** optional on G6 class when browsers/clients ready [Q9]. | M | Encoder availability instance-dependent. |
| 19 | Audio | **Phase 2 template flag** — Opus sidecar once desktop parity demanded. | L | Not blocking core MCP automation. |
| 20 | Input envelope | **Separate channel**: WebRTC data channels or gRPC stream carrying structured input events mirroring gaming/desktop patterns [Q10]. | M | Avoid coupling to video frames. |

## A5 — Accessibility layer per OS

| # | Question | Provisional answer | Conf. | Evidence / notes |
|---|----------|-------------------|-------|------------------|
| 21 | Linux AX | Default templates target **X11 / known-good XWayland**; Wayland-pure flagged **experimental** until AX maturity improves [Q11]. | M | GNOME/KDE progress ongoing. |
| 22 | macOS TCC | **AMI bake + documented sqlite flows** with explicit fragility warnings; health checks detect missing permissions [Q12]. | L | CI vendor variance — expect breakage on upgrades. |
| 23 | Windows UIA libs | **pywinauto + Appium Windows driver** primary; **FlaUI** helper microservice if latency demands [S032,Q13]. | M | WinAppDriver abandoned [S031]. |
| 24 | Android AX | Preinstall **uiautomator2** server components during bake [`init` patterns] [Q14]. | H | Standard ecosystem path. |
| 25 | iOS Sim AX | XCTest snapshots + explore **xctree JSON export** for lighter observability [Q15]. | M | Tooling still evolving. |
| 26 | AX compression | Implement **diff + prune + optional research-informed compressor stage** (configurable aggressiveness) [Q16]. | M | Start heuristic; cite literature when tuning. |

## A6 — OCR / VLM tier

| # | Question | Provisional answer | Conf. | Evidence / notes |
|---|----------|-------------------|-------|------------------|
| 27 | Default OCR | **Tesseract** baseline + template toggle for **Surya**/Paddle when GPU present — benchmark per device family [Q17]. | M | Data-dependent accuracy. |
| 28 | Default local VLM | **OmniParser-style** small parser before general VLMs; **SmolVLM-class** optional experimental profile [Q18,S039]. | L | Model churn fast — isolate plugin interface. |
| 29 | Where models run | **Local DeviceLab host GPU** preferred for privacy; **Bedrock/open APIs** optional BYOK — never silent cloud routing. | H | BYOC principle extension. |
| 30 | Vision routing | Deterministic policy: structured tree → OCR bbox union → OmniParser → VLM; expose overrides via MCP settings + cost tier. | M | Prevent cost bombs. |

## A7 — Identity Broker

| # | Question | Provisional answer | Conf. | Evidence / notes |
|---|----------|-------------------|-------|------------------|
| 31 | Keychain APIs | **`keyring` + OS backends**; Linux fallback **cryptfile** / Secret Service dbus wrapper docs [Q20]. | H | jaraco/keyring issue corpus. |
| 32 | Secret schema | Start **credential refs + OAuth browser flows** where applicable; cookie jars supplied via Playwright storage state files for browser family [S025]. | M | Compose higher-level later. |
| 33 | Elicitation | Yes — integrate MCP **elicitation** modes per spec for confirmations/secrets routing [S022]. | H | Protocol-native UX. |

## A8 — Network proxy

| # | Question | Provisional answer | Conf. | Evidence / notes |
|---|----------|-------------------|-------|------------------|
| 34 | mitmproxy embedding | **In-process addons** driving mitmproxy core library where supported; subprocess fallback for edge cases [Q21]. | M | Operational simplicity vs isolation — revisit sandbox. |
| 35 | Pinning defeat | **Android emulator-only recipes** using Frida/Objection — never marketed as universal; iOS limited [Q23]. | M | Legal/ethical guardrails. |
| 36 | HTTP/3 | Support mitmproxy **v11+** paths; document Chrome QUIC limitations with user CA [Q22,S038]. | M | Offer downgrade-to-H2 test mode. |

## A9 — Recipes / macros

| # | Question | Provisional answer | Conf. | Evidence / notes |
|---|----------|-------------------|-------|------------------|
| 37 | DSL | **YAML v1** + sandboxed templates; **Python v2** isolated containers only [Q24]. | M | Safety ladder. |
| 38 | Variables | **`${var}` + Sandboxed Jinja** (`SandboxedEnvironment`) — block introspection escapes [Q24]. | H | OWASP template injection lessons. |
| 39 | Sharing | Git-based recipe repos + import URI; optional signed recipe bundles later. | L | Community mechanics TBD. |
| 40 | Authoring UX | **Playwright codegen export** for browser; mobile analog via structured action recorder phase 2 [Q25]. | M | Strong leverage. |

## A10 — Snapshots & state

| # | Question | Provisional answer | Conf. | Evidence / notes |
|---|----------|-------------------|-------|------------------|
| 41 | EBS async | Expose **`snapshot_start` + `snapshot_status`** — never block CLI/MCP on completion [S013]. | H | AWS API semantics. |
| 42 | Cross-region copy | Supported via AWS snapshot copy APIs — template warns time+cost; async polling surfaced in UI. | M | Standard AWS patterns. |
| 43 | App-state | **Per-family strategies**: Android emulator snapshots [S048]; Windows VSS where needed [S012]; iOS Sim via Apple-supported checkpoints — document limits [Q27–Q29]. | M | Heterogeneous fidelity unavoidable. |
| 44 | Fork from snapshot | Treat as **new device + copied snapshot IDs** — orchestration wrapper around AWS primitives. | H | Clear billing attribution. |

## A11 — Test harness

| # | Question | Provisional answer | Conf. | Evidence / notes |
|---|----------|-------------------|-------|------------------|
| 45 | Report formats | **JUnit XML required**; **Allure optional** rich UX/agent reruns [Q30]. | M | Allure agent mode emerging [research]. |
| 46 | Artifact bundle | Standard tarball: logs + AX dumps + screenshots + HAR + Playwright trace optional + diagnostics JSON manifest. | M | Inspired by Playwright artifacts practice. |
| 47 | Parallelism | Both patterns: matrix across devices **and** parallel tests per device — gated by quotas/cost guardrails. | M | Template/profile controlled. |
| 48 | Fixtures | Workspace-scoped fixture vault + secrets by reference — never embed secrets in repo recipes. | H | Identity Broker alignment. |

## A12 — Cost guardrails

| # | Question | Provisional answer | Conf. | Evidence / notes |
|---|----------|-------------------|-------|------------------|
| 49 | Prevent vs reactive | **Both**: soft warnings + hard stops configurable per workspace; expensive families default hard-stop until acknowledged [S014]. | H | Aligns with cost transparency principle. |
| 50 | Attribution | Tag devices & sessions with **MCP client ID** from tracing metadata for chargeback-style summaries [OTel patterns]. | M | Requires client cooperation — document headers. |

## A13 — Multi-region / multi-account

| # | Question | Provisional answer | Conf. | Evidence / notes |
|---|----------|-------------------|-------|------------------|
| 51 | Region pinning | Workspace default + per-device override already in template model — enforce allowed-region lists per template [prior design]. | H | Reduces footguns. |
| 52 | Cross-account | **Phase 2**: standard AWS profile `role_arn` chaining — document trust policies only (no shared keys) [Q49]. | M | STS well-understood. |

## A14 — AWS internals

| # | Question | Provisional answer | Conf. | Evidence / notes |
|---|----------|-------------------|-------|------------------|
| 53 | AMI strategy | **Packer pipelines** producing versioned AMIs + semantic tags (`DeviceLabVersion`) [S049]. | H | Repeatable golden images. |
| 54 | SSM on macOS | Validate agent presence/version during **Booting** phase; self-heal via documented pkg install [S010]. | H | AWS docs + ops blog. |
| 55 | VPC strategy | **Dedicated lab VPC IaC** recommended over default VPC for anything beyond sandbox quickstart [Q34,S011]. | M | Educate users on defaults risk. |
| 56 | Partial failures | Implement compensating cleanup jobs + `CleanupRequired` state with downloadable diagnostics bundle — CloudFormation optional bootstrap only for IAM/VPC baseline [prior architecture]. | M | Avoid CFN for every ephemeral device if boto3 simpler. |

## A15 — Browser family

| # | Question | Provisional answer | Conf. | Evidence / notes |
|---|----------|-------------------|-------|------------------|
| 57 | Headless default | **Headless profiles for CI**; **headed profiles for anti-bot sensitive suites** — template-selectable; warn about detection trade-offs [Q45]. | M | Playwright ethical stance matters. |
| 58 | Extensions | Follow Playwright **persistent Chromium + MV3** guidance; handle worker lifecycle quirks [S047]. | H | Official docs + PR #36286 context. |
| 59 | Mobile emulation vs real device | Expose **explicit template**: Playwright emulation lane vs Device Farm lane — never silently substitute. | H | Prevents false confidence. |
| 60 | Downloads/PDFs | Uniform MCP helpers atop Playwright download APIs + filesystem staging through artifact service [S025]. | M | Thin adapter layer. |

## A16 — Mobile family

| # | Question | Provisional answer | Conf. | Evidence / notes |
|---|----------|-------------------|-------|------------------|
| 61 | Genymotion licensing | **Optional Marketplace path** — users accept EULA & billing; OSS repo never redistributes appliance bits [S020,Q47]. | H | Legal clarity. |
| 62 | iOS Sim concurrency | Encode **RAM-aware scheduler** on Mac hosts — conservative defaults (2–3 interactive sims typical on 24–32GB) [Q37]. | M | Vendor guides anecdotal — tune empirically. |
| 63 | Push testing | Support **simulated push fixtures** first; real APNs later via Device Farm / physical racks plugin [open question — medium confidence]. | L | Needs Apple capability matrix per year. |

## A17 — macOS specifics

| # | Question | Provisional answer | Conf. | Evidence / notes |
|---|----------|-------------------|-------|------------------|
| 64 | Xcode channel | Template parameter **stable vs beta** with explicit unsupported warnings for beta stacks [operator choice]. | M | Standard Apple risk management. |
| 65 | TCC automation | Same as A5#22 — prefer bake + documented scripts; track SIP constraints [Q12]. | L | Fragile surface. |
| 66 | Apple Silicon vs Intel Mac EC2 | Target **Apple Silicon Mac instances** primarily; treat Intel as legacy if AWS narrows catalog [S001]. | M | Industry direction + AWS announcements. |

## A18 — Real iOS

| # | Question | Provisional answer | Conf. | Evidence / notes |
|---|----------|-------------------|-------|------------------|
| 67 | TestFlight automation | Integrate **App Store Connect API / Transporter** flows async — abstract behind `RealIOSProvider` [Q39]. | M | Apple toolchain churn — adapter isolation critical. |
| 68 | libimobiledevice | Position as **experimental USB rack plugin** on Linux hosts — document known kernel/USBmux bugs [Q40]. | L | Not v1 core path. |

## A19 — Plugin SPI

| # | Question | Provisional answer | Conf. | Evidence / notes |
|---|----------|-------------------|-------|------------------|
| 69 | Discovery | **`importlib.metadata` entry points** (`devicelab.plugins.adapter`) + optional `~/.devicelab/plugins/` scan for dev mode [S045]. | H | Python standard packaging patterns. |
| 70 | Sandboxing | **Trust local plugins by default** (OSS mental model) — optional subprocess isolation for unsigned third-party plugins later. | M | Balance UX vs security. |
| 71 | ABI versioning | Semantic version gate + protobuf/service contract major bumps isolated per adapter package. | H | Prevents silent breakage. |

## A20 — Security

| # | Question | Provisional answer | Conf. | Evidence / notes |
|---|----------|-------------------|-------|------------------|
| 72 | mTLS | **Yes** between MCP gateway channel to runtime agent alongside tunnel encryption [S043]. | M | Cheap incremental safety. |
| 73 | SBOM | **CycloneDX on releases** + Sigstore/cosign optional roadmap [S042,Q43]. | M | Supply-chain maturity signal. |
| 74 | Prompt injection | Implement **tool-output firewall** (sanitize/minimize) especially for browser/mobile fetched content [Q32]. | M | Defense-in-depth; monitor research. |

## A21 — Observability

| # | Question | Provisional answer | Conf. | Evidence / notes |
|---|----------|-------------------|-------|------------------|
| 75 | OpenTelemetry | **Yes** — traces for provisioning pipeline + MCP gateway spans [S050]. | H | Industry default. |
| 76 | Trace propagation | Propagate `traceparent` from MCP HTTP/SSE down to agent RPC metadata. | M | Needs client adoption — graceful degrade. |
| 77 | Diagnostics bundle | Zip `.devicelab-diagnostic.zip` manifest schema — logs + configs redacted + snapshot IDs [ops pattern]. | M | Support playbook friendliness. |

## A22 — First-run UX

| # | Question | Provisional answer | Conf. | Evidence / notes |
|---|----------|-------------------|-------|------------------|
| 78 | Wizard | Guided flow: credentials → region → bootstrap IaC → smoke Linux device → copy MCP config/deeplink [S044]. | H | Activation funnel critical. |
| 79 | Sample recipes | Ship **3 reference recipes** (browser login smoke, Android install+launch, screenshot diff) in-repo under `examples/recipes/` (future path). | L | Placeholder until repo layout finalized. |

## A23 — AI optimization specifics

| # | Question | Provisional answer | Conf. | Evidence / notes |
|---|----------|-------------------|-------|------------------|
| 80 | Round-trip metering | Expose MCP meta-tool **`session_metrics`** summarizing tool calls, observation bytes, estimated tokens — powered by OTel + local aggregates [design goal]. | L | Speculative — validate usefulness in beta. |
| 81 | Lazy AX drill-down | Return **summary slice + `tree_handle`** on oversized trees; follow-up `observe_expand(handle)` tool [aligns with pruning research Q16]. | M | Token economics core feature. |

---

### Revision protocol

1. Any answer promoted to **canonical spec** must cite `[Snnn]` or primary doc URL in `SOURCES.md`.
2. Flip **Confidence L→H** only after prototype spike or AWS quota empirical measurement.
