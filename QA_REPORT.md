# BhumiRokkhi — Simplified Upload-and-Verify QA

## Verified

- 36 backend Pytest cases passed, including 28 carried-forward V4 tests and 8 new cases.
- Sign-in requirement for active reference endpoints, guest and member ownership scope and session isolation.
- No saved sample -> verification returns a clear HTTP 409.
- Upload a PDF and save only SHA-256 + metadata (no document body persisted).
- Same PDF gives an exact match; altered sample gives mismatch.
- Saving a new sample replaces the old active reference without deleting named legacy references.
- Member's sample persists across logout/login; separate members cannot access it.
- Consent is required and unsupported executable uploads are rejected.
- Client UI no longer displays reference code/name inputs or reference selector; only two file pickers.
- 24 frontend TypeScript/TSX files parsed without syntax errors.
- Two-language key parity and duplicate key check performed.

## Not verified here

- Full `npm run build` and Docker Compose startup (build environment lacks Docker / reachable npm registry).
- Pixel-level browser QA, mobile input behavior, and actual deployment on user's Windows host.

**Caution:** hash matching is byte-identical file matching, not a signature or legal authenticity certificate.
