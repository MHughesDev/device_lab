---
doc_id: "23.1"
title: "DeviceLab research bibliography"
section: "Research"
summary: "Numbered external sources [Snnn] used for DeviceLab BYOC platform decisions."
updated: "2026-05-17"
---

# Research bibliography — DeviceLab platform

**Convention:** Cite as `[Snnn]` in design docs. **Accessed:** 2026-05-17 unless noted.

| ID | Title / resource | URL | One-line use |
|----|------------------|-----|--------------|
| S001 | AWS EC2 Mac instances (User Guide) | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-mac-instances.html | Mac instance families, host billing unit |
| S002 | EC2 Dedicated Host billing | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/dedicated-hosts-billing.html | Per-second billing, minimums |
| S003 | EC2 Mac FAQs | https://aws.amazon.com/ec2/instance-types/mac/faqs/ | 24-hour allocation / Apple SLA context |
| S004 | AWS Device Farm limits | https://docs.aws.amazon.com/devicefarm/latest/developerguide/limits.html | Remote access session caps |
| S005 | AWS Device Farm remote access | https://docs.aws.amazon.com/devicefarm/latest/developerguide/remote-access.html | Session semantics |
| S006 | AWS Device Farm pricing | https://aws.amazon.com/device-farm/pricing/ | Cost models reference |
| S007 | EC2 nested virtualization | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html | Android emulator hosting |
| S008 | AWS What's New: nested virt on virtual EC2 | https://aws.amazon.com/about-aws/whats-new/2026/02/amazon-ec2-nested-virtualization-on-virtual | C8i/M8i/R8i note |
| S009 | SSM Run Command | https://docs.aws.amazon.com/systems-manager/latest/userguide/run-command.html | Agent bootstrap pattern |
| S010 | Install SSM Agent on macOS EC2 | https://docs.aws.amazon.com/systems-manager/latest/userguide/manually-install-ssm-agent-macos.html | Darwin pkg / preinstall notes |
| S011 | AWS VPC security best practices | https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html | Custom VPC rationale |
| S012 | Application-consistent Windows VSS EBS snapshots | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/application-consistent-snapshots.html | Windows snapshot adapter |
| S013 | DescribeSnapshots API | https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeSnapshots.html | Async snapshot progress |
| S014 | AWS Price List API / boto3 pricing | https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/pricing.html | Cost estimation |
| S015 | Amazon DCV (what is) | https://docs.aws.amazon.com/dcv/latest/adminguide/what-is-dcv.html | Windows/Linux streaming |
| S016 | Selkies (GitHub) | https://github.com/selkies-project/selkies | OSS Linux WebRTC desktop |
| S017 | KasmVNC docs | https://kasmweb.com/kasmvnc/docs/master/index.html | WebRTC/WebSocket VNC variant |
| S018 | scrcpy upstream | https://github.com/Genymobile/scrcpy | Android device streaming reference |
| S019 | Genymotion on AWS docs | https://docs.genymotion.com/paas/02_Get_Started/021_AWS/ | ARM cloud Android pattern |
| S020 | Genymotion AWS EULA | https://genymotion.com/aws/genymotion-device-image-aws | Commercial integration constraints |
| S021 | MCP transports (spec) | https://spec.modelcontextprotocol.io/specification/2025-03-26/basic/transports/ | stdio / Streamable HTTP |
| S022 | MCP elicitation (spec) | https://modelcontextprotocol.io/specification/2025-11-25/client/elicitation | User confirmation / secrets routing |
| S023 | MCP Python SDK server docs | https://modelcontextprotocol.github.io/python-sdk/server/ | Baseline server implementation |
| S024 | FastMCP | https://gofastmcp.com/ | Higher-level Python MCP framework |
| S025 | Playwright MCP README | https://github.com/microsoft/playwright-mcp/blob/main/README.md | Browser MCP tool patterns |
| S026 | Anthropic computer use | https://docs.anthropic.com/en/docs/agents-and-tools/computer-use | Industry screenshot-loop baseline |
| S027 | OpenAI computer use guide | https://developers.openai.com/docs/guides/tools-computer-use | CUA integration caution |
| S028 | Vertex / Gemini computer use | https://docs.cloud.google.com/vertex-ai/generative-ai/docs/computer-use | Competitor tool-loop pattern |
| S029 | Appium 3 announcement | https://appium.io/docs/en/3.0/blog/2025/08/07/-appium-3/ | Mobile automation baseline |
| S030 | Appium WebDriver BiDi | https://appium.io/docs/en/latest/reference/api/bidi/ | Event subscription hooks |
| S031 | WinAppDriver issue (maintenance) | https://github.com/microsoft/WinAppDriver/issues/2018 | Avoid WinAppDriver-long-term |
| S032 | Appium Windows driver | https://github.com/appium/appium-windows-driver | Windows automation path |
| S033 | pywinauto wiki tool ratings | https://github.com/pywinauto/pywinauto/wiki/UI-Automation-tools-ratings | Windows stack comparison |
| S034 | uiautomator2 README | https://github.com/openatx/uiautomator2/blob/master/README.md | Android tree/input stack |
| S035 | W3C WebDriver BiDi (WD) | https://www.w3.org/TR/webdriver-bidi/ | Browser event protocol status |
| S036 | mitmproxy certificates | https://docs.mitmproxy.org/dev/concepts/certificates/ | TLS proxy assumptions |
| S037 | mitmproxy Android system CA howto | https://docs.mitmproxy.org/stable/howto/install-system-trusted-ca-android/ | Emulator MITM setup |
| S038 | mitmproxy 11 HTTP/3 release post | https://www.mitmproxy.org/posts/releases/mitmproxy-11/ | QUIC interception status |
| S039 | Microsoft OmniParser | https://github.com/microsoft/OmniParser | Structured screen parsing tier |
| S040 | litestream.io | https://litestream.io/ | Optional SQLite DR |
| S041 | pytransitions PyPI | https://pypi.org/project/pytransitions/ | Device FSM implementation |
| S042 | CycloneDX cyclonedx-py | https://github.com/CycloneDX/cyclonedx-python | SBOM generation |
| S043 | OWASP gRPC Security Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/gRPC_Security_Cheat_Sheet.html | mTLS guidance |
| S044 | Cursor MCP install links | https://cursor.com/docs/mcp/install-links | Deeplink onboarding UX |
| S045 | Python Packaging — plugin entry points | https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/ | Adapter SPI |
| S046 | Playwright codegen docs | https://playwright.dev/python/docs/codegen | Recipe recording |
| S047 | Playwright Chrome extensions | https://playwright.dev/docs/chrome-extensions | MV3/extension testing |
| S048 | Android Emulator snapshots | https://developer.android.com/studio/run/emulator-snapshots | AVD snapshot semantics |
| S049 | HashiCorp Packer CI/CD | https://developer.hashicorp.com/packer/guides/packer-on-cicd/pipelineing-builds | AMI pipeline |
| S050 | OpenTelemetry FastAPI instrumentation | https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html | Local API telemetry |

_Add sources as new rows when adding research rounds. For slug cross-links and upstream licenses, see **[reference/EXTERNAL_REFERENCE.md](reference/EXTERNAL_REFERENCE.md)** Part A._
