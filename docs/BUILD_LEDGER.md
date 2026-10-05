# GradientMine implementation ledger

## Goal and binding decisions
Complete the user-requested wallet → escrow → real training → held-out evaluation → winner → payout loop. No simulated chain receipts, network usage, customer claims or verification. Work continues inline with no optional approval pauses, as explicitly requested.

- Preserve the existing native Rust escrow, low-rank PyTorch worker primitives and canonical evidence format.
- Use an explicitly trusted evaluator. The existing UCI public-source benchmark is educational, not leakage-resistant and not an LLM benchmark.
- Keep a zero-reward local mode separate from Devnet. Refuse mainnet by genesis hash.
- Native browser modules retain the existing lightweight Python architecture; no CDN runtime, framework scaffold or paid services.
- Use a dedicated local checkout/feature branch; publish coherent commits to the user-authorized main branch without force-push.

## Acquisition and initial audit
- Direct git clone failed: container DNS cannot resolve github.com.
- Retrieved public source via a checksum-verified GitHub Actions source bundle, then cloned its full Git bundle locally.
- Starting application commit: 2210521754a46be79d22ee1efbb6de1ff5ea9f6e.
- Source-bundle commit: eb53db41a07e1c045ed6678bc4b24caf59b88e39.
- Remote run 37325921028: six Rust tests pass; SBF .so compiled. Python suite was gated off because API/CLI/tests were absent.
- Local baseline: pytest exits 5: no tests. README references missing files; these are not complete.
- Artifact upload incorrectly included a generated program keypair. Treat it as public/disposable, never use it as an authority, remove key files from future uploads.

## Cycles
1. Durable API, authentication, scoring/receipts, actual worker CLI and reproducible multiprocess demo.
2. SDK chain adapter, exact transaction checks, SBF local execution and Devnet attempt.
3. Wallet Standard browser UI, accessible evidence inspection, failure states, responsive/browser tests.
4. Packaging, deployment attempt, research/legal sources, submission copy, security and full verification.

## Review focus
Untrusted uploads; replayed/expired authentication; cutoff and timestamp races; crashed/ambiguous settlements; hidden-data leakage; unauthorized signer/recipient; stored-XSS; artifact integrity across restart.

## Cycle 1: real API, workers and chain boundary
- Added bounded JSON API, single-use wallet nonces, expiring bearer sessions, immutable policies,
  idempotent job creation, persisted numeric artifacts, pre-cutoff score withholding, signed receipts,
  deterministic winner selection and model lineage.
- Added actual CPU PyTorch low-rank head adaptation CLI. No LLM or GPU claim is made.
- Added Solana SDK transaction construction, local intent reconstruction before signing, finalized
  transaction/account/balance verification, and persisted settlement intents before RPC broadcast.
- Test-first evidence: `tests/test_security.py` initially reported 6 passed / 9 errors because the API
  did not exist. After implementation, the complete current suite reports **44 passed**.
- `python -m ruff check gradientmine tests`: passed. `compileall`: passed.
- The compiled SBF artifact from source commit 2210521754a46be79d22ee1efbb6de1ff5ea9f6e has SHA-256
  `6a19d26db5f7e5f4a67a021aa55d7f1984064718762bd17276a143745e6e18fb`.
  LiteSVM executed it for escrow funding, registered artifacts, exact payouts, rejected double payouts,
  wrong validator/recipient, early settlement, timeout refund, duplicate/late registration and prefunded PDA.
  These are local Solana VM results, **not Devnet transactions**.
- A prefunding test initially failed in setup because 1,000 lamports cannot rent-fund a new system account.
  Corrected the fixture to use the VM's actual zero-data rent exemption; no contract change was needed.
- Three separate worker processes completed an API run in `.local/verified-run`. The third used
  deliberately shuffled training labels and is labelled a negative control, not a detected malicious miner.
  The run wrote hash-checked artifacts and receipts. Local mode cannot claim or display a paid reward.
- The combined test/demo shell invocation hit the tool time limit after the run file was written.
  Its whole-command exit is therefore not recorded as successful. A fresh standalone run is required
  for final release evidence.

## Continuation: wallet/evidence release, 2026-10-05

Recovered source from the upstream CI artifact at `8f85345ab3b644f012e19f54154e17274fe16f98`. Direct clone/network access was unavailable in the authoring runtime; no unrelated repository was used.

Implemented: responsive wallet interface; exact client/server transaction intent verification; receipt/hash inspector; real recorded-run exporter; settlement recovery; API-independent creator refund command; Docker and submission documentation. These are implementation claims, not proof of a production deployment.

Fresh local verification:

- `GM_SBF_PATH=program/target/deploy/gradientmine_escrow.so python -m pytest -q`: **52 passed**.
- `node --test tests/web/*.test.mjs`: **9 passed**.
- `python -m ruff check gradientmine scripts tests`: **All checks passed**.
- `npm run check` and `python -m compileall -q gradientmine scripts`: passed.
- `python -m gradientmine.cli demo --out .local/release-run`: three separate real training processes; 360 held-out examples; baseline 84.7222%, winning candidate 95.2778%, delta 10.5556 percentage points. This run has **no on-chain payments**.
- Compiled SBF artifact SHA-256: `6a19d26db5f7e5f4a67a021aa55d7f1984064718762bd17276a143745e6e18fb`; 84,720 bytes. Exercised in LiteSVM, not an internet cluster.

Remaining evidence gaps at this checkpoint:

- Local Chromium cannot navigate due to `ERR_BLOCKED_BY_ADMINISTRATOR`. A CI browser test has been added; its result must be inspected separately, never inferred from unit tests.
- Railway refused a new project: **Free plan resource provision limit exceeded**. No upgrade or paid resource was authorized or created.
- No Devnet program address, funding transaction or payout signature has been verified at this checkpoint.
- No actual Phantom-extension test, final uploaded pitch/demo video, customer interview or organizer submission receipt exists.
- Worker registration currently persists its transaction when an output directory is supplied; robust CLI resume after a lost response still needs verification. The public API will not silently accept replacement submissions.

The release-delivery workflow verifies transport checksums and baseline file hashes, runs tests, commits actual source, then runs browser QA on a permitted runner. Publishing source and passing browser QA are separate gates.
