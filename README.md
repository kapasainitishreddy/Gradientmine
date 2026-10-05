# GradientMine

**Model-improvement bounties, with inspectable evidence and an explicitly trusted validator.**

GradientMine runs actual PyTorch low-rank-adapter experiments, compares submitted models with a fixed baseline, signs evaluation receipts, and integrates a native Solana escrow program. It does not mine a blockchain, mint an investment token, or claim trustless verification.

## What is verified, and what is not

The local training/API loop and compiled Solana program have been exercised. The browser interface, wallet intent checks, receipt inspector, and recovery tools are implemented. Read [the build ledger](docs/BUILD_LEDGER.md) for commands and actual results. A simulated Solana VM is **not Devnet**. An interface implementation is **not a completed Phantom browser test**.

The included recorded run is real local CPU training by three independent processes on one machine. It is not a live decentralized network. Recorded runs never show a reward or Explorer link when no blockchain transaction occurred. The public Digits evaluation split can be reconstructed; it is not a secret anti-cheating benchmark.

**Never deposit mainnet assets. This release accepts local mode or Solana Devnet only.**

## Run locally

Python 3.11+ and Node 22 are supported; Python 3.12 is the CI target. No GPU or paid API is required.

```bash
git clone https://github.com/kapasainitishreddy/Gradientmine.git
cd Gradientmine
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip==26.2.1
python -m pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -e '.[chain,dev]'
python -m gradientmine.cli demo --out .local/my-first-run
python -m scripts.publish_demo --run .local/my-first-run/run.json
GM_MODE=local GM_ORIGIN=http://127.0.0.1:8000 python -m gradientmine.cli serve
```

Windows PowerShell: activate with `.venv\Scripts\Activate.ps1`, set `$env:GM_MODE='local'` and `$env:GM_ORIGIN='http://127.0.0.1:8000'`, then run `python -m gradientmine.cli serve`. Open `http://127.0.0.1:8000`. Local bounties use **zero monetary reward**.

The live API begins with no bounties: connect a Wallet Standard Solana wallet, authenticate by signing the exact origin-bound message, and create a local challenge. A static server over `web/` instead shows the exported recorded run read-only. It cannot create bounties or pay workers.

```bash
python -m gradientmine.cli identity --out .local/worker.json
python -m gradientmine.cli worker --api http://127.0.0.1:8000 \
  --identity .local/worker.json --job YOUR_LIVE_JOB_ID --out .local/my-worker
```

Wallet files stay on your machine. They are not needed by reviewers. Do not paste or upload private keys, seed phrases, `.local/`, or the validator's private database.

## Verified work boundary

1. A creator approves an immutable policy: model/data hashes, metric, cutoff, validator, reward and refund time.
2. In Devnet mode the browser constructs a funding intent, independently inspects it, requests a wallet signature and submits exact bytes. The API independently validates the same intent before broadcasting.
3. Workers run real head-LoRA training and publish a signed manifest plus strictly bounded numeric JSON weights. Devnet workers register commitments on-chain.
4. After the cutoff, a single named validator recomputes the baseline/candidate scores on held-out examples. Eligibility requires the declared minimum improvement and a positive approximate corrected paired-bootstrap lower bound.
5. The highest-scoring eligible candidate wins, with a deterministic artifact-hash tie break. The validator signs a receipt; the program enforces its authority and one-time escrow payout. This is **trusted evaluation**, not proof of training or decentralized consensus.
6. The UI shows exact artifacts, their hashes, receipt signature checks, lineage, and Explorer links **only for real Devnet transactions**.

Training: a small 64→48→10 Digits classifier; real rank-limited updates to its output head. No LLM fine-tuning, royalties, zkML or autonomous research agents are claimed.

## Test

```bash
python -m pytest -q
node --test tests/web/*.test.mjs
npm run check
python -m ruff check gradientmine scripts tests
python -m scripts.audit_dependencies --out .local/dependency-audit.json
python -m playwright install chromium
python -m scripts.browser_qa --out evidence/browser
```

Compiled-SBF tests additionally require `GM_SBF_PATH` pointing to the built `gradientmine_escrow.so`. Without it, VM tests are skipped, not counted as a passing deployment. CI compiles the Rust program, exercises the VM, runs real workers and browser checks, and retains public evidence.

## Deployment and submission

- [Deployment and emergency refunds](docs/DEPLOYMENT.md)
- [Architecture, assumptions and statistical limits](docs/ARCHITECTURE.md)
- [Threat model](docs/THREAT_MODEL.md)
- [Research and differentiation](docs/RESEARCH.md)
- [Licenses and acknowledgments](THIRD_PARTY_NOTICES.md)
- [Official submission checklist](submission/SUBMIT.md)
- [Product and honest go-to-market copy](submission/PRODUCT.md)
- [Pitch script](submission/PITCH.md) and [demo recording instructions](submission/DEMO.md)

A complete submission still requires the owner's registration/identity confirmation and uploaded videos. Do not describe scripts as finished videos or planned interviews as traction. The submission checklist distinguishes implementation from verified live operation.
