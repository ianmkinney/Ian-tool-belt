---
name: verify-browser-flow
description: Verify a web application user journey using browser evidence. Use for React or Next.js UI checks, regression reproduction and frontend-to-API troubleshooting.
---

# Verify a browser flow

1. Establish the target URL, environment, allowed actions and expected visible outcome. Prefer local or staging environments and synthetic test accounts.
2. Confirm a browser tool is actually available. Use the host-approved browser interface; do not bypass its access controls with another automation path.
3. Observe the rendered UI before interacting. Follow the primary user journey, then one meaningful failure or recovery path. Capture console or network errors only when relevant and redact secrets.
4. Verify the outcome from the UI and, where authorized, the persisted application state. A clicked button or HTTP 200 alone is not proof of success.
5. Preserve screenshots or minimal reproduction steps. Distinguish observed results, inferred causes and untested behavior.
6. Avoid purchases, messages to real people, destructive actions and production changes unless separately authorized. Do not claim test success when login, missing dependencies or a blocked browser prevented the run.

Example request: Verify a failed login shows an actionable error and does not create a signed-in session.
