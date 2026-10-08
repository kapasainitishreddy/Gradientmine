# GradientMine hardening and visual polish, October 8, 2026

This release preserves the approved warm editorial homepage, SVG artwork, original Digits bounty and Rust/Solana LiteSVM escrow protocol. It hardens the separate Research Lab and improves UX without paid extras or unsupported payout claims.

## Security and access

- Sealed candidate visibility: while OPEN, public and private details expose only worker, time, artifact hash, entry ID and state. Competing adapters, signed manifests and scores stay hidden until evaluation.
- Workspace management: owner-only member listing, role updates, revocation, protected owner identity, fresh authorization on every private request. Revocation cannot claw back a previously downloaded file.
- Audit trail: events for workspaces, member management, benchmark creation, submissions, evaluation and signed reviewer attestations, with actor/subject ID/time. Owner/reviewer-only read access. These ordinary SQLite records are NOT tamper-evident against the server operator.
- Evaluation evidence is rechecked against worker signatures, task/worker/policy/artifact commitments and candidate digest. Corrupt encrypted holdouts yield a fail-closed 503 instead of a winner.
- Optional offline LLM prompt evaluation is limited to 12 development cases, 16 held-out cases, and 2 candidates. This is not a hard CPU timeout or sandbox isolation.

## UI polish

- Workspace member roster, revocation, and activity history in expandable panels.
- Collapsible benchmark builder to avoid excessive scrolling.
- Appropriate candidate template for the selected competition; existing edits are preserved across refresh.
- Disabled invalid actions for disconnected wallets, unavailable API, closed competitions and incomplete evaluation.
- Measured success-rate meters from actual evaluator results and cryptographically verified receipt status.
- Python-compatible canonical ASCII JSON for browser-signed payloads, including Unicode, and wallet-change detection.
- Sticky editorial navigation, subtle scroll reveals and original sculpture light sweep, supporting reduced-motion users.
- Proof Canvas draws a static evidence view but pauses continuous animation offscreen and when the page is hidden.
- Mobile navigation and layout improvements for 360/390px.

## Verify

    python -m compileall -q gradientmine scripts tests
    python -m pytest -q
    python -m ruff check gradientmine scripts tests
    node --test tests/web/*.test.mjs
    npm run check
    python -m scripts.browser_qa --out evidence/browser

Browser QA uses a test-only ephemeral Ed25519 wallet and verifies workspace creation, sealed submissions, cutoff, signed results, audit records and responsive layouts. It does not establish Phantom browser QA or real Devnet transactions.

## Remaining limits

Cloudflare Pages hosts a read-only viewer, not the Python/PyTorch evaluator, private state or live wallet actions. No public HTTPS backend, funded Devnet payout, independent validator consensus, real-money billing, licensed enterprise evaluation sets or external security audit has been established. Actual remote LLM LoRA artifact admission still requires secure large-artifact uploads and trusted isolated model evaluation. Keep encrypted data, validator keys and SQLite backups private and consistent.
