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

## Final verification and cleanup, 2026-10-05

Everything produced in this continuation is committed to the public `main` branch. The obsolete source-transfer blobs and recovery-only delivery workflows were removed after the real source tree was established. The remaining automatic verification workflow tests the actual product surfaces; the real-Devnet smoke workflow is manual-only because it depends on external Devnet funding.

### Automatic release verification

GitHub Actions run **#16** (`37362146515`) completed successfully on the cleaned tree.

- Python/API/security suite: **47 passed, 5 skipped**. The five skipped cases are the compiled-SBF cases, intentionally exercised in the separate program job rather than double-counted.
- Browser/Javascript unit tests: **9 passed, 0 failed**.
- Ruff and static JS syntax checks: passed.
- Real three-process CPU training exercise: baseline accuracy **84.7222%**, winning candidate **95.2778%**, improvement **10.5556 percentage points** on 360 held-out examples. This is a local ML result, not a paid Devnet result.
- Playwright Chromium live-HTTP QA: passed, including Wallet Standard authentication with a test-only ephemeral Ed25519 wallet, authenticated local bounty creation, policy hash inspection, responsive 360/390px layouts, recorded-run read-only mode, expected-validator receipt verification and no browser JavaScript exceptions.
- Dependency audit: **no known vulnerabilities found**.
- Rust escrow crate tests: **6 passed, 0 failed**.
- Fresh SBF build: passed.
- Freshly built SBF executed through LiteSVM chain tests: **14 passed**.

Successful verification URL:
https://github.com/kapasainitishreddy/Gradientmine/actions/runs/37362146515

### Real Devnet attempts

A disposable, secret-free real-Devnet smoke harness was added in `.github/workflows/devnet-smoke.yml` and `scripts/devnet_smoke.py`. It is designed to build the exact SBF program, create temporary identities, deploy to Devnet, fund a bounty, register a worker commitment, wait for cutoff, pay the registered worker, verify finalized balances/state and upload only public evidence.

No Devnet success is claimed. The shared public funding infrastructure blocked the attempts before deployment:

1. Run `37359575775`: standard `solana airdrop` was rate-limited after five bounded retries.
2. Run `37360168681`: the official `devnet-pow` client could not compile with its historical locked dependency graph on current Rust; this was fixed by resolving current compatible transitive dependencies.
3. Run `37360512990`: the client compiled, but automatic faucet discovery returned no usable faucet and the disposable creator remained unfunded.
4. Run `37361441119`: using the Solana-published proof-of-work faucet parameters still required initial transaction fee funding; that starter airdrop was rate-limited.

The workflow is now **manual-only** so external faucet instability does not create red release CI. Completing the Devnet loop requires a dedicated test identity with a small amount of Devnet SOL or an available faucet/RPC. Never place its private key in the repository or chat.

### Hosting attempts

- Railway: free resource provisioning limit exceeded; no paid upgrade was authorized.
- Vercel Hobby: project creation returned HTTP 403, no permission to create the project.
- GitHub Pages: the workflow token had `pages: write`, but GitHub refused Pages-site creation with `Resource not accessible by integration`. The knowingly failing Pages workflow was removed.

Therefore the recorded viewer is implemented and testable from `web/`, but there is **no verified public hosted URL** yet.

### Remaining owner/external actions

- Provide or locally control a dedicated Devnet test identity with enough **Devnet-only** SOL to deploy/test the program, or rerun the manual smoke workflow when public funding becomes available. Never share a seed phrase or private key.
- Enable/authorize a hosting target if a public recorded-viewer URL is desired.
- Perform one actual wallet-extension Devnet interaction for human UX evidence.
- Record and upload the 2–3 minute presentation and <=3 minute product demo.
- Complete the Colosseum registration/submission through the signed-in owner account and save the confirmation.
- Any customer interviews, traction, revenue or willingness-to-pay claims remain unverified until actually obtained.

## Product completion pass, October 5, 2026

Native Git fetch confirmed the supplied `d0b3143` was the current upstream starting point. The following coherent changes were committed and pushed to `main`, without rewriting history:

- `dc11dff`: strict finalized transaction header/program privilege checks, including boolean/count and invoked-program mutations.
- `b434363`: deployed executable/loader/ProgramData inspection, exact ELF-byte comparison and explicit upgrade-authority trust.
- `2d65b33`: bounded JSON/numeric inputs, exact persisted-origin authentication, directory fsync and atomic failed-evaluation rollback.
- `8277ab6`: CPU PyTorch 2.14.1 and pip 26.2.1, complete installed dependency inventory audit. CPU build tags are mapped explicitly to upstream advisories rather than silently skipped.
- `cb96b80`, `c56acfd`: authenticated durable worker checkpoints; exact signed-byte recovery, finalized registration discovery, bounded expiry/absence replacement; confirmation retries remain idempotent after evaluation.
- `d4d14db`: wallet/disconnect and stale-response protection, exact pending-transaction recovery, accessible evidence dialogs, full/copy hashes, explicit trusted evaluator and eligible-versus-paid states.
- `f231b5c`: actual API bounty → CPU CLI training → signed artifact → compiled-SBF registration → evaluation/receipt → exact payout integration. Its automated execution is explicitly **local LiteSVM**, not Devnet.
- `19578cf`: CI SBF upload allowlist excludes the automatically generated private keypair. Fresh locked program and complete ML/program integration tests run in the program job.
- `a3d3c49`: freshly verified recorded CPU run and submission package. Upgrading PyTorch changed exact floating-point merge bytes for the older recording; historical evidence remains in Git history. The new viewer anchors the same independently remeasured scores to job `d348dcd2-90f3-49a0-949d-4c7801699346`, not the old run.
- `eb61007`: actual container testing found restrictive source permissions prevented UID 10001 from importing the application. Explicit copy ownership fixes this; a real container regression recreates the private volume and verifies bounty/validator continuity. CI builds from restrictive permissions and audits the installed container inventory. Optional BuildKit CA trust remains confined to the build; TLS verification is preserved.

### Fresh verification

With the fresh SBF supplied, `python -m pytest -q` passed **119 tests, zero skips**, including all compiled tests. This was rerun after container and recording-script changes. `node --test tests/web/*.test.mjs` passed **19**, `npm run check`, Ruff and compileall passed. Locked native Rust tests passed **6**. A new empty Cargo target built the locked SBF with Agave 4.3.0/platform-tools v1.57; **31** chain/deployment/integrated-product tests passed against it. ELF size is **84,720 bytes**, SHA-256 `6a19d26db5f7e5f4a67a021aa55d7f1984064718762bd17276a143745e6e18fb`.

`python -m gradientmine.cli demo --out .local/final-verification` completed three independent CPU worker processes, all exit zero, on one host. Baseline **84.7222%**, winning candidate **95.2778%**, delta **10.5556 percentage points**, **360** held-out examples. State `EVALUATED`; **no on-chain funds moved**. All **14** public referenced artifacts passed hashes, expected worker/validator signatures, cross-artifact provenance, exact current-runtime model merge and deterministic winner selection before export. This is a deliberately budget-limited Digits proof of function, not an LLM/general benchmark or independent-node claim.

Playwright Chromium live-HTTP and recorded QA passed **12** substantive checks, including test-only Wallet Standard authentication, mobile 360/390px layouts, keyboard/focus, stale async responses, hostile strings and expected-signer receipts. It is **not Phantom QA**. Dependency audit found **zero known advisories** across **69** installed development releases, with no silent CPU skip. Real non-root Docker startup/persistence passed; its separate **38**-release installed inventory audit also found zero known advisories. Container health is local verification, not public deployment.

GitHub Actions [37386118051](https://github.com/kapasainitishreddy/Gradientmine/actions/runs/37386118051) at `a3d3c491cc9f5b236e2eb38126cdb56e5fa3b82c` completed successfully. The authenticated GitHub run/job API confirmed every Python/browser/audit/Rust/SBF/VM step succeeded. Artifact/log CDN downloads returned proxy 403, so test counts here come from actual local commands, not inferred CI logs. The subsequent [container verification run 37387430095](https://github.com/kapasainitishreddy/Gradientmine/actions/runs/37387430095) at `eb61007ab8d8911e206f4c56126a00be73337f47` also succeeded in all four jobs, including actual container startup/persistence and its installed-inventory audit. Both are recorded in final provenance.

Public machine-readable records are under [evidence/2026-10-05](../evidence/2026-10-05/verification.json). Private identities, databases, worker recovery state and video originals remain outside Git. The retained local API was restarted with current code and its original durable validator identity.

### Actual external attempts and boundaries

Later verified-TLS requests retrieved current official Colosseum rules/FAQ, research and dataset/license sources with HTTP 200. This supersedes the earlier proxy block; saving the environment configuration draft is not itself proof of publication. Official rules confirm presentation **2–3 minutes**, demo **≤3 minutes**, deadline **October 12, 2026, 11:59 PM Pacific**. Signed-in entrant fields, identity declarations and submission remain owner actions.

Live Devnet RPC returned the pinned genesis. Exactly **one** legitimate free 2 SOL request failed; finalized balances remained zero. Fresh creator **public** funding address: `9hkeGMLra72RUkdAngRQgmzRRovkMXHircWce2cRkkU8`. The fresh planned program identity has **not** been deployed; there is no bounty account, funding/registration/settlement signature or Explorer payout to claim. [devnet-attempt.json](../evidence/2026-10-05/devnet-attempt.json) records this boundary. Only free Devnet SOL is authorized; no mainnet, purchase, repeated blocked faucet loop or historical exposed identity was used.

Authenticated GitHub access reported repository admin rights, providing a new reason to check Pages creation. The actual Pages POST still returned **403 “Resource not accessible by integration.”** No site or failing deployment workflow was created. No other authorized hosting credential/capacity or default external Solana identity was available. A public live service or static viewer URL remains unverified.

Real extension-wallet approval, free Devnet funding, suitable hosting account access, video public uploads, factual entrant/team review and signed-in Colosseum submission require owner actions. No customer, revenue, private-task validation, independent operator, decentralized evaluation, formal external security audit or submitted entry is invented.

### Actual rendered media

A genuine 150.000-second captioned presentation and 165.000-second captioned product demo now exist. Both use actual continuous Chromium capture of the read-only local viewer; the presentation also shows exact source/document excerpts. Their hashes, complete captions, measured formats, evidence-source commit and full-file decode/visual-review records are in [PRESENTATION_VIDEO.md](../submission/PRESENTATION_VIDEO.md) and [DEMO_VIDEO.md](../submission/DEMO_VIDEO.md). No human narrator is claimed. Owner review of the silent format and final portal acceptance remain outstanding.

The official MIT `/brag` workflow and Hyperframes produced actual 22.000-second landscape and 20.000-second portrait launch films. The original evidence-thread composition uses actual UI, exact worker losses and the current verified 14-artifact bundle. Plans, original reproducible source, licenses, share copy, lightweight poster and render hashes are under [submission/tour](../submission/tour/README.md). Original synthesized ambient audio uses no third-party music samples or narrator. Both renders passed full decode and end-to-end frame review; automated checks reported zero errors and 40/40 contrast checks. Closing text states live payout evidence pending. OneTake code was not copied or executed. Large MP4 files remain outside Git history.

GitHub release creation at `dfa77c7` succeeded, but the actual public-only asset upload returned HTTP 403 from `uploads.github.com`; the release API confirmed zero assets. The release was changed to a draft and its notes corrected. [MEDIA_DELIVERY.md](../submission/MEDIA_DELIVERY.md) and [media-delivery.json](../evidence/2026-10-05/media-delivery.json) provide the owner handoff. No successful public video delivery or playback is claimed. The network draft now includes the concrete upload host; publication/runtime permission still needs environment review.

### Final pushed-source verification

[Verify GradientMine run 37388405319](https://github.com/kapasainitishreddy/Gradientmine/actions/runs/37388405319) at exact commit `dfa77c7a9a793c1ffb91ac07fef39b32baa0c7be` succeeded. Authenticated GitHub run/job API confirms all four jobs and all executed steps passed, including source readiness, actual non-root container recreation, installed-container advisory audit, Python/JS/static checks, real three-process CPU training, browser QA, complete development advisory audit, locked Rust tests, fresh SBF compilation and compiled LiteSVM integration. The separate verification-toolchain and reproducible-source-bundle workflows also succeeded for that source. Local test counts above remain explicitly local, not inferred from blocked log downloads.

Current cloud-instance development setup is tested and running. Complete install/start instructions and the additive network requirements are saved in the environment draft, including `uploads.github.com` following the observed failure. Review/Save/Publish in environment settings is still required to activate future-task configuration; draft saving does not publish or prove fresh-task restoration. No secret values were requested or saved.


### Public judge viewer hosting

- On October 5, 2026 (October 6 UTC), a Cloudflare Pages project named `gradientmine` was created on the connected Cloudflare account and linked to `kapasainitishreddy/Gradientmine` branch `main`.
- Build output is the committed `web/` directory with no build command. This is intentionally the **read-only recorded evidence viewer**, not the live API/validator and not Devnet payout proof.
- Canonical Pages hostname: `https://gradientmine.pages.dev`. The first production deployment is pending the next linked-source commit; do not cite the URL as working until the deployment is observed ready and signed-out HTTP access is verified.
- Railway remains blocked by the connected account's free resource limit. Vercel project creation again returned HTTP 403 for project-create permission. No paid upgrade was authorized.

- Cloudflare Pages deployment `4acdbbc2-2027-4b3d-a184-907d965ecdd4` completed successfully from commit `5d2da202434e75e9cbf22ea3acd413797cc7e8ae`; canonical hostname is `https://gradientmine.pages.dev`.
- Signed-out browser verification succeeded for `https://gradientmine.pages.dev/` using Cloudflare Browser Rendering. The page loaded the committed JavaScript/CSS, rendered the recorded bounty, disabled live wallet/create actions, and visibly stated: `Recorded local experiment ... Read-only evidence, not a live network. No blockchain payment.`
- The verified page shows the disclosed local evidence: frozen parent 84.72%, best eligible model 95.28%, +10.56 percentage points across 360 held-out examples, the negative-control result, named validator, policy/evaluation commitments, lineage, and no finalized payout claim.


## Assurance-market release verification

- Product code merged through PR #2 at commit `87200f39f25eeead7551461fd878c47845374089` (`feat: turn GradientMine into an assurance market (#2)`). The follow-up judge-tour documentation is commit `10fc2af975f2a0eb7228f26d2d0909fd1633b1c4`.
- GitHub Actions run [37402699747](https://github.com/kapasainitishreddy/Gradientmine/actions/runs/37402699747) completed **successfully** against exact product commit `87200f39f25eeead7551461fd878c47845374089`. All four jobs passed: source, container, python and program.
- The general Python job reported **109 passed / 10 skipped**. Those ten skips are the compiled-SBF-only cases when `GM_SBF_PATH` is absent in the general job; the dedicated program job built fresh SBF and reran the compiled integration subset with **31 passed**.
- JavaScript/browser-unit coverage reported **25 passed / 0 failed**. The added assurance tests pin development-vs-assurance separation, local no-payout behavior, Artifact Firewall non-overclaiming, Model Passport provenance and the sealed-before-evaluation state.
- Browser QA passed **13 substantive checks**, including the new Assurance Contract, GradientMine Arena, Artifact Firewall and downloadable Model Passport, plus Wallet Standard test-harness authentication, real local bounty creation, XSS/shell-quoting resistance, stale-response protection, mobile 360/390px overflow checks, artifact hash/signature verification and zero JavaScript exceptions. The wallet harness remains explicitly test-only and is not Phantom-extension QA.
- The fresh CI demo launched **three actual worker OS processes**, all exit zero, and again selected a held-out winner at **95.2778%** from a **84.7222%** parent: **+10.5556 percentage points** over **360 held-out examples**, adjusted lower bound **+6.1111 pp**. This run was local; `on_chain=false`.
- Native Rust unit tests passed **6 / 6**. The program job compiled fresh SBF with the pinned toolchain and the compiled LiteSVM integration suite passed **31 / 31**.
- Development dependency audit inspected **69 installed releases** and reported **zero known advisories**. The non-root container build, HTTP health, durable validator/bounty state across recreation, and exact container inventory audit also passed.
- CI retained three evidence artifacts for this release: `python-verification` SHA-256 `718dd72f7fe720177ee46dec9e6928407bb6997cc9316b44f6756034b1f8e891`, `escrow-verification` SHA-256 `60324994e3c2f3df573bf4ab92a1708dd81f1f5a8d80adedc2a905608c156976`, and `container-verification` SHA-256 `464ab80204346f8f8014f16e7b063bea214a3dd5f0ceb93f41148d4236f8a0d2`.
- Cloudflare Pages production deployment `c81c5599-3e4e-4b69-a61d-2de6b091741c` deployed the assurance-market UI successfully from commit `87200f39f25eeead7551461fd878c47845374089`. Canonical public viewer remains `https://gradientmine.pages.dev`.
- Independent signed-out Cloudflare Browser Rendering returned HTTP 200 for the canonical viewer and confirmed the new `ASSURANCE CONTRACT`, `GRADIENTMINE ARENA`, `ARTIFACT FIREWALL` and `MODEL PASSPORT` surfaces, the recorded `95.28%`, `+10.56 pp`, `+6.11 pp` values, the downloadable passport control, and the explicit text `Read-only evidence, not a live network. No blockchain payment.`
- Submission materials now use [FINAL_FORM_COPY.md](../submission/FINAL_FORM_COPY.md) as the paste-ready portal source, [PITCH.md](../submission/PITCH.md) as the 2–3 minute founder pitch, [DEMO.md](../submission/DEMO.md) as the ≤3-minute technical walkthrough, and [ASSURANCE_RESEARCH.md](ASSURANCE_RESEARCH.md) for the implemented-vs-roadmap research boundary.

### Remaining assurance-release boundaries

No integrated live Devnet training-to-payout transaction was created by this release. No deployed program ID, funding/registration/settlement signatures, payout Explorer URL, actual Phantom-extension QA, new assurance-interface recording, external customer validation or official Colosseum submission is claimed. The existing 150-second presentation and 165-second demo were recorded before this assurance-interface redesign and should be re-recorded if the new story is used in the final submission.
