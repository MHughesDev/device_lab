---
doc_id: "23.12"
title: "External reference registry and direct-read digest"
section: "Research"
summary: "Tracked upstream URLs/repos for DeviceLab plus skim notes from direct documentation reads."
updated: "2026-05-17"
---

# External reference — registry & direct-read digest

## Part A — Registry (tracked upstreams)

_Add a row before citing an upstream in `idea.md` or implementation specs._

| Slug | Kind | Canonical entry point | License / terms | Notes |
|------|------|----------------------|-----------------|-------|
| `mcp-python-sdk` | Repo | https://github.com/modelcontextprotocol/python-sdk | MIT | Stable docs on **`v1.x` branch**; `main` tracks pre-alpha v2 (`README.v2.md`). |
| `mcp-spec` | Spec | https://modelcontextprotocol.io/specification/latest | Spec license per site | Transports: **stdio** + **Streamable HTTP** (replaces older HTTP+SSE); session + Origin rules. |
| `fastmcp` | Repo/docs | https://gofastmcp.com / https://pypi.org/project/fastmcp/ | See PyPI classifiers & repo `LICENSE` | Pin **`fastmcp<3`** per upstream docs; docs MCP server at `https://gofastmcp.com/mcp`. |
| `playwright-mcp` | Repo | https://github.com/microsoft/playwright-mcp | Apache-2.0 | Large `browser_*` tool surface; accessibility-first; compare for Browser family MCP. |
| `playwright` | Repo/docs | https://github.com/microsoft/playwright / https://playwright.dev | Apache-2.0 | Codegen, extensions MV3, stealth **not** officially endorsed for evasion. |
| `appium` | Docs | https://appium.io/docs/en/latest/ | Apache-2.0 | Appium 3 + multi-platform drivers (mobile/desktop/TV). |
| `appium-uiautomator2-driver` | Repo | https://github.com/appium/appium-uiautomator2-driver | Apache-2.0 | Driver **≥5** requires **Appium 3**; Android API min **26** since driver 6.0.0; `appium driver doctor uiautomator2`. |
| `appium-xcuitest-driver` | Repo | https://github.com/appium/appium-xcuitest-driver | Apache-2.0 | **macOS host only**; driver **≥10** requires **Appium 3**; hosted docs on GitHub Pages. |
| `pywinauto` | Repo/docs | https://github.com/pywinauto/pywinauto | BSD-3-Clause | `win32` + **`uia`** backends; README examples for UIA Explorer. |
| `mitmproxy` | Repo/docs | https://github.com/mitmproxy/mitmproxy / https://docs.mitmproxy.org | MIT | Addons API + programmatic `Master`; stable docs for embedding. |
| `omniparser` | Repo | https://github.com/microsoft/OmniParser | MIT | V2 weights on Hugging Face; OmniTool Windows harness; GUI grounding pipeline. |
| `selkies` | Repo/docs | https://github.com/selkies-project/selkies / https://selkies-project.github.io/selkies/ | See repo `LICENSE` | Linux WebRTC/X11 streaming; GPU path; README asks for maintainers/contributors. |
| `coturn` | Repo/wiki | https://github.com/coturn/coturn | BSD-3-Clause | TURN/STUN reference implementation; deploy guides in wiki + community articles. |
| `aws-ec2-mac` | Docs | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-mac-instances.html | AWS terms | Dedicated Host billing unit; **24h minimum** allocation; **mac-m4 / mac-m4pro** + earlier generations; launch **6–20+ min** readiness; **no Spot**; avoid FileVault; EBS recommended over internal SSD. |
| `aws-dcv` | Docs | https://docs.aws.amazon.com/dcv/latest/adminguide/what-is-dcv.html | AWS + separate licensing note | Pixel-stream remote display; **no extra charge on EC2** otherwise license rules apply per admin guide; multi-session/GPU share **Linux server only**. |
| `aws-device-farm` | Docs | https://docs.aws.amazon.com/devicefarm/latest/developerguide/welcome.html | AWS terms | **Region: us-west-2 only**; remote access + managed Appium; **150-minute** remote access limit (see limits doc); automated runs + VPC egress option. |
| `aws-pricing-api` | Docs | https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/using-price-list-query-api.html | AWS terms | `DescribeServices` / `GetAttributeValues` / `GetProducts`; API **endpoint region** (`us-east-1`, etc.) unrelated to workload region. |
| `libimobiledevice` | Repo | https://github.com/libimobiledevice/libimobiledevice | LGPL-2.1 | Cross-platform iOS protocols without jailbreak; large **tools/** utility matrix; **not Apple-affiliated**. |

### Wishlist (not yet skimmed into Part B)

| Slug | URL | Reason |
|------|-----|--------|
| `aws-ssm-runcommand` | https://docs.aws.amazon.com/systems-manager/latest/userguide/run-command.html | Agent bootstrap procedures |
| `kasmvnc` | https://kasmweb.com/kasmvnc/docs/master/index.html | Compare to Selkies / noVNC path |
| `flaui` | https://github.com/FlaUI/FlaUI | Windows .NET UIA alternative |
| `awesome-mcp-servers` | Curated lists / https://github.com/punkpeye/awesome-mcp-servers | Ecosystem conventions |
| `apple-simctl` | Apple Xcode docs / `man simctl` | Simulator automation surface |
| `xctree` | https://github.com/ldomaradzki/xctree | Simulator AX JSON CLI |

---

## Part B — Direct-read digest (authoritative summaries only)

**Retrieved:** 2026-05-17 via repository fetch tool (markdown extraction). These are **skims**, not substitutes for upstream docs.

### B.1 MCP Python SDK (`modelcontextprotocol/python-sdk` README, `main`)

- README states **v1.x is current stable**; full v1 docs live on **`v1.x` branch**; **`main`** documents upcoming **v2 (pre-alpha)** with `README.v2.md`.
- SDK implements full MCP: **clients + servers**, **stdio / SSE / Streamable HTTP**, resources/tools/prompts, **structured output**, **elicitation**, **sampling**, logging, auth hooks, ASGI mounting patterns.
- **Implication:** Pin SDK major branch explicitly in DeviceLab; do not assume `main` README matches PyPI stable behavior.

### B.2 MCP specification — Transports (`modelcontextprotocol.io/specification/latest/basic/transports`)

- Standard transports: **stdio** and **Streamable HTTP** (successor to deprecated HTTP+SSE from 2024-11-05).
- Streamable HTTP: POST + GET; optional **SSE** streams; **`MCP-Session-Id`** header for stateful servers; **`MCP-Protocol-Version`** header required; strict **Origin** validation + localhost bind guidance for DNS rebinding mitigation.
- **Custom transports** allowed if JSON-RPC + lifecycle preserved.

### B.3 FastMCP 2.0 (`gofastmcp.com/v2/getting-started/welcome`)

- Positions as production layer over MCP SDK: composition, proxying, OpenAPI/FastAPI generation, tool transforms, enterprise auth providers.
- FastMCP 1.0 merged into official SDK (2024); **FastMCP 2.0** is separate maintained line; **FastMCP 3.0** in development — docs advise **`fastmcp<3`** pin.
- Docs expose **LLM-friendly** formats: `llms.txt`, `llms-full.txt`, `.md` suffix on URLs, plus **`https://gofastmcp.com/mcp`** MCP server for doc search.

### B.4 AWS EC2 Mac instances (User Guide page)

- Billing unit = **Dedicated Host**; instances on host **no separate instance charge**.
- Generations listed include **mac1** (Intel Coffee Lake), **mac2** / **mac2-m2** / **mac2-m2pro** / **mac2-m1ultra**, **mac-m4** / **mac-m4pro** (Apple silicon tiers with stated CPU/GPU/RAM).
- **Minimum allocation 24 hours** before host release; **no Spot/RI**, Savings Plans available.
- Practical: **boot readiness ~6–20+ minutes** on AWS AMIs (longer with large EBS / user data).
- Warnings: **do not use FileVault**; prefer **EBS encryption**; internal Apple SSD not managed by AWS; **Apple Intelligence unavailable** when booting from external EBS default layout.
- **EC2 macOS Init** plist path `/Library/LaunchDaemons/com.amazon.ec2.macos-init.plist`; upstream **`aws/ec2-macos-init`** GitHub.

### B.5 Amazon DCV admin — What is DCV?

- Remote display protocol streaming **pixels** (not geometry) using **H.264-style** compression with optional **lossless** when conditions allow.
- **No additional charge** for DCV server on EC2 beyond instance cost — **otherwise licensing applies** (see admin licensing guide).
- Features: multi-monitor, collaboration, clipboard/file transfer, USB/WebAuthn/stylus remotization, HTML5 client.
- **Linux-only extras:** multiple sessions per server, GPU sharing across sessions.

### B.6 AWS Device Farm — What is Device Farm?

- Real **physical** iOS/Android hosting in AWS.
- **Only `us-west-2`.**
- Two modes: **remote access** (browser + Appium against managed endpoint) and **automated runs** (upload app/tests, managed hosts; optional VPC linkage).
- Remote access doc link cites **150-minute** session ceiling (detail in limits guide).

### B.7 AWS Price List Query API (Billing docs page)

- Workflow: **DescribeServices** → **GetAttributeValues** → **GetProducts** with `TERM_MATCH` filters (AND-only semantics).
- Reinforces: **Pricing API endpoint region** is independent of product region.

### B.8 Microsoft Playwright MCP (`README` on `main`)

- Confirms **accessibility snapshot-first** design; extensive tools (`browser_click`, `browser_fill_form`, `browser_snapshot`, `browser_network_requests`, cookie/storage, tracing, video, etc.).
- Documents MCP vs **Playwright CLI + SKILLS** tradeoff (CLI more token-efficient for coding agents).
- **Implication:** Treat Playwright MCP tool naming/schema as compatibility reference for Browser family.

### B.9 Microsoft OmniParser (`README` on `master`)

- Parses UI screenshots into structured elements to ground VLMs; **V2** checkpoints on Hugging Face; **OmniTool** drives Windows 11 VM with pluggable models (OpenAI, DeepSeek, Qwen, Anthropic Computer Use).
- Install via conda + pip requirements; documented weight download paths for **icon_detect** / **icon_caption** (Florence caption folder naming caveat).

### B.10 Appium documentation (`appium.io/docs/en/latest/`)

- Appium positions as automation ecosystem for **mobile, browser, desktop, TV** platforms with drivers/plugins ecosystem page.

### B.11 Appium UiAutomator2 driver README (`master`)

- Driver proxies commands to **UiAutomator2 server** + **ADB** helpers.
- **Version gate:** driver **5.x+** requires **Appium 3** (`appium driver install uiautomator2`).
- **Android minimum:** API **26+** recommended since driver **6.0.0** (older API 21–25 discouraged).
- Rich **capabilities** tables: ports `8200–8299`, install timeouts, hybrid WebView support hooks — blueprint for Android template capability UI.

### B.12 Appium XCUITest driver README (`master`)

- **Host must be macOS** (Xcode).
- Driver **10.x+** requires **Appium 3**.
- Documentation hosted separately at `appium.github.io/appium-xcuitest-driver`.

### B.13 pywinauto README (`master`)

- Backends: **`win32`** default and **`uia`** for MS UI Automation; includes cross-platform **mouse/keyboard** helpers (README mentions Linux roadmap historically).
- Practical UIA example manipulating Explorer context menus — basis for Windows desktop MCP adapter patterns.

### B.14 Selkies README (`main`)

- Describes Linux **WebRTC** remote desktop targeting **60 FPS FHD**, GPU/CPU accelerated, embeddable HTML5; originates from Google GPU streaming recipe; docs site **selkies-project.github.io/selkies**.
- README signals **maintainer help wanted**.

### B.15 mitmproxy Addons API (`docs.mitmproxy.org/stable/addons-api/`)

- Fetch returned navigation skeleton — treat **addon hooks + examples** as canonical (`docs.mitmproxy.org` examples + GitHub `docs/src/content/addons-api.md`) when implementing embedded proxy.

### B.16 libimobiledevice README (`master`)

- LGPL-2.1 library + CLI tools (`idevice*`, `afcclient`, …) covering backup, install, syslog, screenshots (with developer image), WebKit remote debug relay, etc.
- Explicitly **not Apple-sponsored**.

### B.17 coturn (`README` on `master`)

- Free **TURN + STUN** server; official Docker image **`coturn/coturn`** with published port ranges (`3478`, `5349`, UDP relay range example `49152–65535`).
- Supports TLS/DTLS, multiple user DB backends (SQLite, Redis, Postgres, …), Prometheus option, RFC references listed in README.
- **Implication:** Reference Dockerfile/README for BYOC TURN snippet; wiki pages may be stale — prefer README + `docker/coturn` docs.

---

### Revision history

| Date | Change |
|------|--------|
| 2026-05-17 | Initial registry + Part B direct reads for MCP, AWS Mac/DCV/Device Farm/Pricing, Playwright MCP, Appium drivers, pywinauto, OmniParser, Selkies, libimobiledevice, mitmproxy landing. |
| 2026-05-17 | Added coturn README direct-read (replaced wiki-only stub for B.17). |
