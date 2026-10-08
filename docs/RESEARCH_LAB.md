# GradientMine Research Lab v1

**Implementation status: working local research competitions, NOT a funded production marketplace.**

This adds a separate, backward-compatible family of research competitions alongside the original Digits LoRA/Solana escrow path. It does not modify the trusted Digits settlement protocol or advertise a completed Devnet payment.

## Available competition types

| Type | Actual current implementation | Not yet supported |
| --- | --- | --- |
| retrieval | Deterministic lexical document retrieval, title boosts, bounded synonym expansion, held-out hit accuracy | Embedding retrieval, managed vector databases |
| grounded_qa | Retrieval + extractive evidence-sentence selection; judged against held-out references | Unrestricted LLM generation or certification against hallucinations |
| safety_refusal | Bounded, declarative refusal/allow keyword policies; paired private test accuracy | True jailbreak-resistant LLM guardrails |
| efficiency | Document-work/operation-count optimization with held-out quality guardrail and measured local runtime | Reliable model-token-dollar/energy cost benchmarking |
| llm_prompt | Optional offline cached HF causal/seq2seq model inference; compare prompt templates on hidden QA | Production LLM fine-tune uploads or distributed evaluator jobs |

Other implemented capabilities:
- The hardening pass seals competing artifacts until evaluation, adds workspace member revocation, owner/reviewer audit history, and signed evidence revalidation. Audit events are ordinary SQLite rows, not tamper-evident consensus.
- Native editorial animations respect reduced-motion preferences. Proof Canvas pauses continuous offscreen animation. See [hardening notes](HARDENING_2026-10-08.md).

- Wallet-authenticated team/enterprise workspaces with owner, researcher, reviewer roles and member limits; no emails are invented.
- Workspaces can host public or private competitions. Only workspace members may inspect a private competition. Public development examples, corpus and challenge policy are distinct from the held-out evaluation split.
- Server-side Fernet encryption of the private held-out cases with an owner-only key on the persistent volume. Public evaluation commitment is SALTED before hashing to reduce low-entropy data guessing. Data is decrypted locally by one named validator at cutoff. Public corpora/development splits are not encrypted.
- Immutable, hash-committed policies; bounded non-executable numeric/text-rule artifacts, worker Ed25519 signed submissions, duplicate rejection, capacity limits.
- Recomputed scoring from private examples after deadline, paired/multiple-candidate-adjusted bootstrap gate for accuracy tasks, explicit quality guardrails for efficiency.
- Signed evaluator receipts, deterministic winner selection, receipt verification and re-evaluation idempotence.
- Reviewer-signed result-hash attestations. They do not constitute independent private evaluation, reviewer consensus or trustless blockchain settlement.
- Autonomous local worker searches only the public development set, with bounded candidate budgets and signed submission opt-in.
- Enterprise workspace label, roles and quotas are implemented. Subscription billing is not connected. The 10% fee endpoint is an illustrative fee quote only. No charges, revenue, custody or fees.
- The approved editorial homepage remains untouched visually; a separate Research Lab page links to the new workflow.

## Run locally

Use the same supported Python/Node dependencies and root runtime as README. For example, after creating a Python venv and installing dependencies:

    python -m pip install -e '.[chain,dev]'
    GM_MODE=local GM_ORIGIN=http://127.0.0.1:8000 python -m gradientmine.cli serve

Open http://127.0.0.1:8000/lab and connect a Solana Wallet Standard wallet for wallet-authenticated API actions. A compatible browser wallet is required for the web UI. The standalone worker uses locally stored worker Ed25519 identity.

On the static Cloudflare Pages site, /lab.html is an explanatory/read-only UI; /api/lab does not exist there. Do not show static frontend controls as an active competition backend.

### API (same origin, JSON)

- GET /api/lab/types (always public, reports LLM runtime availability)
- POST /api/lab/workspaces (wallet auth)
- GET /api/lab/workspaces (wallet auth)
- GET /api/lab/workspaces/{id}/members (owner only)
- GET /api/lab/workspaces/{id}/audit (owner and reviewer)
- POST /api/lab/workspaces/{id}/members/{address}/revoke (owner only, cannot revoke owner)
- POST /api/lab/workspaces/{id}/members (owner only; wallet address + researcher/reviewer role)
- POST /api/lab/benchmarks (researcher/owner; documents, public development, encrypted holdout, kind, visibility, duration and threshold)
- GET /api/lab/benchmarks (public list plus joined workspaces, if authenticated)
- GET /api/lab/benchmarks/{id} (public, or workspace-only if private)
- GET /api/lab/benchmarks/{id}/development (only the PUBLIC development data, never hidden labels)
- POST /api/lab/benchmarks/{id}/submissions (worker-signed manifest, bounded JSON adapter)
- POST /api/lab/benchmarks/{id}/evaluate (workspace owner/researcher/reviewer, only after cutoff)
- POST /api/lab/benchmarks/{id}/reviews (owner/reviewer Ed25519 result-hash attestation)
- GET /api/lab/fee-quote?reward_lamports=1000000 (simulation, never collectible)

### Candidate submission manifest

Sign the canonical JSON payload with the authenticated wallet/worker Ed25519 private key. The server compares the submitted artifact's SHA-256 with the signed digest, and compares the frozen policy digest:

    {
      "format":"gradientmine.lab-submission.v1",
      "benchmark_id":"<UUID>",
      "policy_sha256":"<hash>",
      "artifact_sha256":"<hash>",
      "submitted_at":<current_UNIX_second>
    }

No remote Python, pickle, local shell commands, or untrusted ML model code is executed by the evaluator.

## Autonomous bounded agent

Generate a local identity using the existing CLI:

    python -m gradientmine.cli identity --out .local/researcher.json

Search public examples without submitting:

    python -m gradientmine.lab_worker --api http://127.0.0.1:8000 --benchmark YOUR_UUID --identity .local/researcher.json

Use --submit to register the best bounded, locally searched candidate. The agent does not see private holdout data; it may overfit the DEVELOPMENT split and is not a fully autonomous research scientist.

## Offline local LoRA proof

Optional PEFT training supports already cached and trusted causal/encoder-decoder Hugging Face model families with common q_proj/v_proj, q/v or c_attn attention modules. This is REAL local supervised LoRA training but remains a LOCAL artifact generation workflow, not a remotely registered LLM fine-tune bounty:

    pip install -e '.[llm]'
    python -m gradientmine.local_tuning --model-dir /trusted/cached-model --train-json public-supervised-examples.json --out .local/adapter-run --epochs 1 --rank 4

- Example file: JSON array of prompt and answer fields, at most 64.
- No automatic model downloads: trust_remote_code=False and local_files_only=True.
- Saves a safe-tensor adapter with a hashed manifest; no pickle or arbitrary training recipe execution.
- No holdout data is loaded by the worker.
- Requires appropriate local CPU RAM/GPU memory depending on the model.
- Does not upload multi-megabyte adapters to the current 256 KiB JSON API. That needs a separate streaming ingest protocol, artifact scanners, quotas, access control, evaluation workers and integrated tests.

To enable offline prompt-only evaluation, set GM_LOCAL_LLM_DIR to the trusted locally cached model directory on the API host. Without that setting, the server rejects creation of a benchmark of kind llm_prompt.

## Deployment and safety boundaries

A production Research Lab operator needs all of the following:
1. An HTTPS hostname with the API and browser sharing the exact GM_ORIGIN.
2. A private durable volume holding SQLite, validator identity, Fernet key and sealed benchmark data. Back up and restore these together; never expose them as static assets.
3. Only one API/evaluator process with SQLite. Scale independent workers, not the signed validator.
4. Explicit limits for storage/CPU/execution, private tenant audit and data retention before admitting outside companies.
5. Real wallet-extension QA, privacy/legal terms, enterprise identity/admin and billing integrations before customer use.
6. Solana Devnet program deployment plus a finalized, auditable escrow-funded competition and payout before claiming payments.
7. Independent review consensus requires independent evaluator execution and dispute handling; reviewer signatures alone do not achieve this.

Do not deposit mainnet assets. The new lab has zero monetary rewards, even when GM_MODE=devnet is configured for the separate Digits protocol.

## Tests

    python -m pytest -q tests/test_lab.py
    python -m pytest -q
    node --test tests/web/*.test.mjs
    npm run check
    python -m scripts.browser_qa --out evidence/browser

Offline LLM prompt evaluation is limited to 12 development examples, 16 held-out examples and two candidates. No strict CPU runtime limit, independent consensus or live payments are claimed.

The full verification workflow still compiles the original Rust/SBF program and runs it in local LiteSVM. It does NOT verify a real Devnet payout or a paid billing event.

## Remaining production roadmap

A complete AI improvement marketplace still needs (1) a secure large-artifact LoRA upload/evaluation protocol, (2) licensed private real-world RAG/safety/hallucination datasets and real reference model inference, (3) trusted remote worker isolation and cost metering, (4) multi-evaluator reruns and dispute resolution, (5) chosen billing provider with signed webhooks and production fee flow, (6) funded Devnet-to-recipient evidence, (7) legal/customer readiness, and (8) deployment credentials and permanent host capacity. These are NOT silently claimed as done.
