---
name: build-api-slice
description: Build a narrow API feature with a usable frontend path. Use for Python, Rails, Spring, React or Next.js feature requests, API contracts and micro-SaaS prototypes.
---

# Build an API slice

1. Read the repository instructions, dependency versions, existing routes and database conventions. Preserve the established framework; do not migrate stacks to match a preference.
2. Define one user outcome, request/response examples, authentication boundary and failure cases. Identify migrations or external writes before implementing them.
3. Use Context7 or official documentation for version-specific APIs; match the installed version. Never send secrets or private source code in documentation queries.
4. Implement the smallest vertical slice through endpoint, persistence and UI when needed. Validate inputs, authorize resources per user, and make retried writes idempotent where duplication matters.
5. Test the consequential behavior: rejected authorization, invalid inputs, persistence and the primary successful path. Run existing relevant checks, not an unrelated whole-system rebuild.
6. Report files changed, actual test results and remaining limitations. Prepare a reviewable diff; deployment is a separate action unless already authorized.

Example request: Add a paid-API usage endpoint and a React view without replacing the existing backend.
