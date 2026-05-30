---
doc_id: "6.9"
title: "scaling"
section: "Operations"
summary: "Scaling playbook: horizontal pod autoscaling, workers, cache."
updated: "2026-04-17"
---

# 6.9 — scaling

<!-- Optional per spec §26.12 item 401 -->

**Purpose:** Scaling playbook: horizontal pod autoscaling, workers, cache. Per spec §26.12 item 401.

## 6.9.1 Horizontal Pod Autoscaling

K8s HPA configuration per deploy/k8s/base/hpa.yaml. Trigger thresholds, scale-up/down delays.

## 6.9.2 Worker Scaling

When to scale workers independently from the API. Worker concurrency settings per broker.

## 6.9.3 Caching

When to add caching: identifying hot read paths, Redis integration, cache invalidation patterns.
