# skills/frontend/expo-auth-storage.md

<!-- CROSS-REFERENCES -->
<!-- - Profile: optional web/mobile profile -->
<!-- - Related docs: docs/optional-clients/ -->

**Purpose:** [OPTIONAL] Frontend/mobile skill. Enable the web or mobile profile before relying on this.

## Purpose
What this frontend skill enables.

## When to Invoke
When web or mobile profile is active.

## Prerequisites
Profile enabled, Node.js/Expo installed.

## Relevant Files/Areas
apps/web/ or apps/mobile/, docs/optional-clients/

## Step-by-Step Method
Store access/refresh tokens with `expo-secure-store`; clear on logout; refresh before expiry.

## Command Examples
`npx expo install expo-secure-store`

## Validation Checklist
- [ ] Frontend/mobile connects to API
- [ ] Auth flow works end-to-end

## Common Failure Modes
CORS configuration, auth token storage.

## Handoff Expectations
Frontend connected, tested.

## Related Procedures
docs/procedures/add-optional-app-profile.md

## Related Prompts
prompts/profile_configurator.md

## Related Rules
.cursor/rules/security.md
