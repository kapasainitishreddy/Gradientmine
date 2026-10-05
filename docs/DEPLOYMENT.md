# Deployment and operator runbook

## Local setup

Python 3.11+ (3.12 recommended), Node 22 for frontend tests. Start in an isolated environment. CPU training does not require a GPU. Windows PowerShell: `.venv\Scripts\Activate.ps1`; Linux/macOS: `. .venv/bin/activate`.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip==26.2.1
python -m pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -e '.[chain,dev]'
python -m gradientmine.cli demo --out .local/demo
python -m scripts.publish_demo --run .local/demo/run.json
python -m gradientmine.cli serve
```

Open http://127.0.0.1:8000 . The demo is an isolated recorded run. The separately started live server has its own database and initially no bounties. A static host displays the recorded run only when it cannot connect to an API; the read-only banner and disabled actions make the distinction explicit.

The managed cloud checkout already has an isolated environment. Use `. /workspace/.gradientmine-setup/activate.sh` there instead of replacing it; the helper activates the installed Python, Cargo and Solana tools. That absolute path is cloud-local setup, not a portable prerequisite. Do not publish `.local/demo/private/` or serve it as a static directory. Only `scripts.publish_demo`'s public export belongs in the viewer. The loopback URL is for operator-local checks, not a submission deployment URL.

## Container, existing server

`docker compose up --build -d` binds the app to loopback port 8000 with a named durable volume. Before putting it behind an HTTPS reverse proxy, configure `GM_ORIGIN` to the exact public origin without path, credentials or query. Permit only that origin. Do not expose port 8000 to the world directly. The image uses non-root UID 10001; the persistent volume must be writable by that UID. Docker configuration must be executed and health-checked in your target environment; its presence in the repo is not deployment evidence.

The container regression check runs a disposable image with UID 10001, a read-only root filesystem and a private writable volume; it authenticates a local bounty and verifies that the policy and validator identity survive container recreation. Run `python -m scripts.container_qa --out .local/container-report.json` after `docker build -t gradientmine:verified .`. CI deliberately builds from owner-only source permissions to catch non-root copy failures. Only the checked public report/inventory is uploaded; the disposable test volume is removed.

For an authorized build network with a private CA, BuildKit optionally accepts `--secret id=build_ca,src=YOUR_CA_BUNDLE`. That bundle supplies pip's trust only during installation, remains absent from the runtime image, and does not disable TLS verification. Configure your network proxy/DNS separately if required.

Keep one worker process for the API. Its evaluation scheduler shares SQLite and in-process locking. Do not scale multiple independent validator instances over diverging filesystems. Workers doing experiments are separate CLI processes, not API replicas.

## Solana Devnet

Use dedicated test identities only. Never use a mainnet wallet or send a seed/private key to the API, support or chat. Generate locally with `gradientmine identity --out .local/worker.json`. A locally generated Solana CLI JSON keypair is also accepted by the CLI if its file permissions are private.

Build and test the program using the checked-in Cargo lock:

```sh
cargo test --manifest-path program/Cargo.toml
cargo build-sbf --manifest-path program/Cargo.toml
sha256sum program/target/deploy/gradientmine_escrow.so
```

Follow https://solana.com/docs/programs/deploying to deploy the freshly built SBF with a dedicated locally controlled identity and free Devnet SOL. Check genesis `EtWTRABZaYq6iMfeYKouRu166VU2xqa1wcaWoxPkrZBG`, actual deployed program bytes, executable status and upgrade authority. Do not set `GM_PROGRAM_ID` to a placeholder or the System Program. Do not finalize or transfer authority over an existing deployment casually.

The official deployment page was retrieved with HTTP 200 and TLS verification on October 5, 2026 after the earlier proxy block. It confirms build/deploy commands, target/deploy output, cluster selection, binary-size-dependent rent and default upgrade authority; check the live page for later changes. `cargo build-sbf --sbf-out-dir` changes the binary location; hash the actual output you deploy. Native CLI compilation and LiteSVM execution do not establish a deployment or upgrade-authority configuration.

For a real product proof, one evidence bundle must join the current source commit, exact SBF SHA-256, deployed-byte check, program ID and upgrade-authority assumption with the bounty account, creator/worker/validator public addresses, funding/registration/settlement signatures, policy hash, trained winning artifact hash and signed receipt hash. Verify each finalized transaction, matching on-chain state, recipient balance delta and Explorer URL. A chain-only smoke test using synthetic commitments is a separate mechanics test; it is not proof of payment for an actual trained artifact. Record only public evidence. No successful integrated Devnet run is inferred from this runbook.

Set `GM_MODE=devnet`, the verified public `GM_PROGRAM_ID`, and the exact HTTPS `GM_ORIGIN`. The server creates/persists its own validator identity on the private volume and returns **only its public address** through `/health`. Fund that address with a small amount of test SOL for settlement fees. The creator funds its bounty and rent through its own wallet; each worker needs test SOL for registration rent and fees. Program deployment rent is separate and depends on binary size, not a hardcoded guessed cost.

On a live bounty: connect wallet -> create draft -> inspect transaction terms -> approve funding -> wait for finalized escrow -> run workers -> register before deadline -> evaluator waits through the 120-second registration-confirmation grace -> evaluate -> verify winning receipt -> finalized payout. The UI always keeps eligibility separate from payment.

## Worker

```sh
gradientmine identity --out .local/worker.json
gradientmine worker --api YOUR_CONFIRMED_HTTPS_ORIGIN --job YOUR_BOUNTY_UUID --identity .local/worker.json --program-id YOUR_CONFIRMED_PROGRAM_ID --out .local/worker-run
```

The placeholders above must come from your running deployment, not this document. For a local job, use http://127.0.0.1:8000 and omit `--program-id`. Workers check public training-package hashes before training and independently reconstruct transaction intents before signing. `--negative-control` deliberately shuffles labels for testing; it is never described as fraud detection.

Keep a persistent worker output/checkpoint path for retries using the current CLI's supported `--out` option. Use `--resume --out YOUR_EXISTING_WORKER_OUTPUT` with the same job and identity after an ambiguous response; check finalized registration and public account state rather than generating a different artifact or concluding that a lost response means failure. Read the current `gradientmine worker --help` and release verification evidence for recovery behavior; do not delete an unresolved signed pending transaction to force a fresh registration.

## Timeout and recovery

Keep public bounty addresses and transaction signatures. A broadcast response is not settlement. Refresh after RPC delays. The browser keeps pending public signatures, not wallet secrets or login tokens, in local storage.

For an expired validator settlement, an authenticated call to `/api/jobs/JOB_ID/recover-settlement` examines finalized status and the bounty state before a new attempt. The UI exposes recovery when the server records a settlement warning. A live original transaction is never replaced merely because its response was lost.

When the coordinator is unavailable, refund from public account data after the immutable timeout:

```sh
gradientmine refund-address --bounty YOUR_PUBLIC_BOUNTY_ADDRESS --program YOUR_CONFIRMED_PROGRAM_ID --identity .local/creator.json --out refund-public-receipt.json
```

The identity remains on the creator's machine. The CLI persists the public pending transaction before sending, then verifies the exact finalized transaction and refund balance. Rent remains in protocol accounts. Losing an identity file is not something the coordinator can undo.

## Backup and costs

Encrypted consistent backups must include SQLite, artifacts, the private task and validator identity. Never expose that volume as a static directory. Test restoring a copy before accepting bounties. A host restart must retain the volume.

Earlier October 5, 2026 deployment notes report that the connected Railway account refused a new project with **“Free plan resource provision limit exceeded. Please upgrade to provision more resources!”** This is historical evidence, not a new provider check in this pass. The user's supplied blocker history also reports Vercel project-creation 403 and unavailable GitHub Pages creation. No paid upgrade is authorized. Use an existing server or free capacity explicitly made available by the owner; do not mislabel a static recorded viewer as a live full-stack deployment. Inspect the latest build ledger for the current provider/network boundary before retrying.
