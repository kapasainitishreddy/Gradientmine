# GradientMine

A working local model-improvement marketplace with real low-rank neural-network training, signed evidence, and a Solana Devnet escrow implementation. **Do not infer a deployment or payment from source code.** Current verification is recorded in `evidence/`.

## Run it

Use Python 3.11 or newer (3.12 recommended), Node 22, and an isolated environment.

```sh
python -m venv .venv
# Linux/macOS:
. .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e '.[chain,dev]'
gradientmine demo --out .local/demo
gradientmine serve
```

Open http://127.0.0.1:8000. The UI works with Wallet Standard Solana wallets. Local mode creates training bounties with zero reward and never simulates a blockchain payment. `gradientmine demo` starts its own API and three separate worker processes, including a deliberately shuffled-label negative control. The processes are on one machine, not three independently owned network nodes.

The task is an actual 64-48-10 neural classifier using UCI handwritten digit images. A frozen baseline is adapted with a trainable low-rank output update. This is not an LLM, not a claim of decentralized verification, and not a proof that training occurred just because an artifact is signed.

## Verify

```sh
python -m pytest -q
python -m ruff check gradientmine tests scripts
python -m compileall -q gradientmine scripts
npm test
npm run check
python scripts/browser_qa.py
cargo test --manifest-path program/Cargo.toml
cargo build-sbf --manifest-path program/Cargo.toml
```

Browser QA uses an explicitly test-only Wallet Standard signer against a real local API. A real wallet extension and Devnet settlement require their own evidence. No private key is ever requested by the UI or API. Local `.local/` identities must not be published.

## Scope and safety

The named evaluator controls withheld data and signs results. The public-source dataset is recoverable, so this benchmark is not safe for real-money competition. Confidence intervals use an approximate paired bootstrap with a predeclared eight-candidate correction; they are not a universal guarantee of improvement. Artifacts are bounded numeric JSON, never executable code or pickle. Model weights and evaluation data stay off-chain.

The escrow program restricts settlement to the named validator and a registered candidate, prevents duplicate settlement, and permits an owner refund after the committed window plus one hour. Application clients refuse networks whose genesis is not Devnet. That client-side network restriction is not an intrinsic property of the Rust bytecode.

A direct emergency refund, independent of the API, is available:

```sh
gradientmine refund-address --bounty PUBLIC_BOUNTY_ADDRESS --program PUBLIC_PROGRAM_ID --identity .local/creator.json
```

This signs locally and requires test SOL for the transaction fee. Keep the published program address and your public bounty address. Never send a secret key to support, a website, or an AI chat.

## Evidence and submission status

A recorded real local run is included under `web/assets/recorded-run.json`, with downloadable numeric model artifacts. The browser verifies the exact original signed bytes and hashes downloaded artifacts. Those signatures authenticate the signer, not the truth of the evaluator's methods.

**No Devnet program address, transaction signature, payout, public full-stack deployment, customer validation, or final video is asserted unless an evidence file explicitly records a verified result.** Full architecture, threat model, deployment runbook, research credits and submission materials are maintained in `docs/` and `submission/` as implementation progresses.

## License

Original source: MIT. UCI Optical Recognition of Handwritten Digits: Alpaydin and Kaynak (1998), DOI 10.24432/C50P49, CC BY 4.0. The shipped numeric artifacts were trained on that public dataset. See third-party notices for dependencies and research citations.
