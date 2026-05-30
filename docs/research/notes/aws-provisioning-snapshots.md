---
doc_id: "23.6"
title: "Research notes — AWS provisioning and snapshots"
section: "Research"
summary: "Skim notes on VPC, AMIs, SSM, EBS/VSS snapshots, Device Farm, Marketplace EULA constraints."
updated: "2026-05-17"
---

# Notes — AWS provisioning, networking, snapshots, cost

## Regions & accounts

- **v1:** Single AWS account, multi-region allowed; workspace default region + per-device override [prior design].
- **v2:** `AssumeRole` profiles for secondary accounts — standard STS profile chains [Q49].

## VPC strategy

- Provide **bootstrap CloudFormation/Terraform snippet** creating a **dedicated “lab” VPC** (private subnets + endpoints optional) instead of relying on default VPC for anything beyond quickstart [S011, Q34].
- Ephemeral devices still benefit from predictable SG naming/tagging.

## AMI / agent delivery

- **Golden images via Packer**: base layer (SSM, Docker, codecs) + family layers (Android/macOS/Windows) [S049].
- **Runtime install:** complement with **SSM Run Command** / **State Manager** for agent updates without rebaking every patch [S009].

## macOS specifics

- **EC2 macOS AMIs:** SSM agent commonly present — verify version on boot [S010].
- **Instance types:** Standardize on documented **mac2-m2 / mac2-m2pro** families per AWS EC2 Mac docs [S001]. 
- **Host minimum:** 24-hour dedicated-host allocation remains cost-design driver [S003].

## Snapshots

- **EBS:** Always async UX — poll `DescribeSnapshots` progress until `completed` [S013].
- **Windows:** Prefer **VSS-consistent** snapshots for desktop workloads when freezing filesystem matters [S012].
- **Android emulator:** Quick Boot + `adb emu avd snapshot *` patterns; invalidate on image upgrades [S048].

## Cost estimation

- Use **AWS Pricing API** with aggressive caching (pricing endpoint regions fixed) [S014].

## Device Farm / real iOS

- Treat as **provider adapter** with hard session/time limits and pricing surfaced in MCP responses [S004–S006].

## Marketplace integrations (Genymotion etc.)

- Never bundle proprietary AMIs inside OSS repo — users subscribe in **their** AWS account; document EULA constraints [S019,S020,Q47].
