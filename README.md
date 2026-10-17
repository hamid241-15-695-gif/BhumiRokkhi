# BhumiRokkhi — ভূমিরক্ষী (simplified document verification update)

TwinRoots · LandTech Innovation Hackathon 2026 · P3

The **visible product name remains only BhumiRokkhi / ভূমিরক্ষী**. This updated source is based directly on V4 and retains the V4 design and all other existing features. Only the custom saved-sample document-verification form and its backend integration are simplified.

## What changed on `/check`

The previous **Reference Code**, **Reference Name** and **Choose a Reference** dropdown are **removed from the website**.

Now the flow is:

1. Upload **your own sample PDF/JPG/PNG** (up to 8 MB), confirm you are permitted to use it, and press **Save sample document**.
2. The server computes SHA-256 and saves **only the hash and limited filename/deed metadata** — not the PDF itself.
3. Below, upload **the document to verify** and press **Verify document**.
4. The app automatically compares the uploaded document's SHA-256 with the **one currently saved sample** for the logged-in member/guest session.
5. Identical file bytes => **Exact match**. Modified/resaved/other bytes => **Mismatch**. Neither outcome is a government authenticity or fraud certificate.
6. Uploading another sample replaces your previous active sample. Old named references created using the previous V4 feature are preserved in the database but not shown in the simplified interface.

**Guest:** current sample belongs to that guest session. **Member:** current sample belongs to the account and survives logout/relogin. Different accounts cannot access each other's samples.

The older reference endpoints remain available **for backwards compatibility**, but are not used by the simplified UI. V4's other document comparison tool (two separate files) is unchanged.

## Everything else is unchanged

- Home page / branding / forest-green design / বাংলা-English toggle, with no visible V3/V4/Final text
- Phone/password login, create account with demo OTP `1234`, guest full access, profile, logout
- Plot Search, detail map and transaction timeline
- Six prepared fraud-detection cases including partial double selling and ownership-chain gaps
- Editable OCR fields for PDF/images, two-PDF comparison, and SHA-256 comparison
- Evidence-linked risk results, ownership graph and print-to-PDF report
- Demo-only/no-government-service warnings and security limitations

## Windows setup (keep existing V4 data/accounts)

1. In your **currently running V4** VS Code terminal, run: `docker compose down`.
2. **Never add `-v`** — doing so can delete your saved PostgreSQL data.
3. Download/extract `BhumiRokkhi_V4_Updated.zip` to a **different folder**, then open its inner `BhumiRokkhi_V4` folder in VS Code.
4. Keep Docker Desktop running. Inside the extracted V4 project root:

   ```powershell
   docker compose up --build -d
   docker compose ps
   ```

5. Open <http://localhost:3000/check> and sign in/guest if needed.
6. Verify the lower-right panel now has only **Upload sample → Save** and **Upload document → Verify**. No name/code/selector fields.

The Compose project name is still `bhumirokkhi-v4`; the **same V4 PostgreSQL volume** is reused. Existing V4 accounts/data persist when you use `docker compose down` without `-v`. The old source directory and V1/V2/V3 are left untouched.

## How to test

- From `backend/samples/`, upload `D-4001_reference.pdf` in the *sample* field and press Save.
- Upload the **same** `D-4001_reference.pdf` in the *verification* field => `Exact match`.
- Upload `D-4001_changed_version.pdf` in the verification field => `Hash mismatch`.
- Upload `D-4001_changed_version.pdf` as the **new saved sample**, then verify it again => `Exact match` for this newly saved version. Original PDF now mismatches.
- The file used as the saved sample is not automatically uploaded to the verification field. You must choose the file to check separately.

## API

New endpoints (authenticated member or guest):

- `GET /api/documents/active-reference` -> `{ "reference": null }` or current user's saved sample metadata
- `POST /api/documents/active-reference` -> multipart `file`, `acknowledge=true`; upserts the current saved sample hash
- `POST /api/documents/active-reference-check` -> multipart `file`; automatically checks that user's active sample; returns `match`, `reference_sha256`, `submitted_sha256`, etc.

Existing endpoints such as `/api/documents/references` and `/api/documents/reference-check?ref_key=...` are unchanged for backwards compatibility, but the visible form no longer uses them.

Backend automated regression suite: **36 tests passed** (original 28 plus 8 new tests for the simplified workflow). To re-run in the Docker project root: `docker compose exec api python -m pytest -q`.

Frontend `.tsx/.ts` source files were syntax-parsed. Full Next.js production build/Docker browser testing could not be completed here because the npm registry and Docker CLI were unavailable. First-run build on Windows is still necessary.

**Important:** The fixed registration OTP `1234` and Guest full access are only for hackathon use, not true secure identity verification. Do not use real sensitive legal documents or real personal phone numbers. A hash difference does not prove forgery, and a matching hash does not prove title authenticity.
