# Architecture and protocol v1

## System boundary

A single FastAPI coordinator and evaluator persists SQLite state, content-addressed numeric JSON artifacts and a private validator identity on one durable volume. Independent Python worker processes authenticate with locally stored Ed25519 identities, fetch hash-pinned public training inputs, train, sign a manifest, upload a bounded adapter and, in Devnet mode, register the adapter/manifest commitments on-chain. The responsive browser uses Wallet Standard and native WebCrypto. There is no hosted wallet, custom token, GPU-farm simulator or anonymous claim of decentralized consensus.

```
Wallet / Python CLI -> same-origin API -> SQLite + content-addressed JSON
       |                       |                   |
       |                  named evaluator <--------+
       |                       | signed receipts
       +-> Solana Devnet <-----+ verified winner settlement
              escrow / deadline / registrations / receipt hash / payout
```

The Rust program is native Solana, not Anchor. Its compiled SBF is exercised with LiteSVM. Local execution is not evidence of deployment. `gradientmine/chain.py` and `gradientmine/wire.py` are the versioned client and wire boundary. Exact account layouts are documented in those files and validated against the Rust implementation.

## Bounty state

Local: OPEN -> EVALUATED or NO_WINNER. A local result never becomes SETTLED and has no blockchain signatures.

Devnet: AWAITING_FUNDING -> OPEN -> EVALUATED -> SETTLING -> SETTLED. When no candidate qualifies, NO_WINNER waits for the creator refund timeout. Any still-open escrow becomes refundable at the immutable cutoff plus one hour. Funding, registration, settlement and refund are recorded only after finalized RPC evidence is checked against exact program, data, accounts, privileges and balance changes.

The validator commits the dataset hashes, parent model, cutoff, minimum improvement and statistical rule before workers enter. The program binds that policy hash to the escrow. ML files and the evaluation set stay off-chain. The chain does not execute ML or determine whether an evaluation is scientifically correct.

## Actual training

The CPU task uses 8x8 digit images, a 64-input / 48-hidden / 10-output neural classifier, and a low-rank update to the frozen classifier head: W_new = W_parent + B A. It is not a language model or distributed pretraining. The initial baseline uses 18 epochs on 240 examples, intentionally leaving room for improvement; this is disclosed, not presented as a strong benchmark.

Each worker independently optimizes its adapter. The coordinator evaluates complete merged candidates, never averages arbitrary adapters or invents scores. The three-worker local exercise runs separate OS processes on one machine; the third uses shuffled labels as an explicit negative control. This is not proof of three independently owned machines or a fraud detector.

## Evaluation and selection

At the cutoff, all registered candidates are evaluated on the same 360 held-out examples. Eligibility requires observed accuracy improvement at least the configured minimum and a strictly positive one-sided paired-bootstrap lower bound. There are 20,000 resamples, a precommitted seed and per-candidate alpha 0.05/8. Accuracy chooses the best eligible candidate; artifact hash ascending resolves ties. One submission per wallet, eight per job; wallets are not unique-human identities.

The signed receipt binds job, worker, policy, model, input artifact, manifest, held-out commitment and score. The parent of a new round must be the accepted local winner or the finalized Devnet winner of a completed round. There are no royalties in this release.

## Failure and recovery

The server stores signed settlement bytes before broadcast. Retries resend identical bytes. An explicit recovery operation only replaces an expired absent/failed transaction after finalized RPC shows that the bounty is still unpaid. Pending signatures and discarded attempts remain visible. The program independently rejects duplicate payout.

A creator can run `refund-address` directly from public bounty data without the coordinator. It checks the program owner, PDA derivation, creator, on-chain timeout, exact transaction and finalized balance change. Loss of every copy of the creator identity is not recoverable by this service.

## Deployment

One API process, one persistent volume, one named evaluator. No horizontal replicas over separate volumes. Frontend-only hosting can display a clearly labelled recorded run but cannot accept jobs or make payments. Read docs/DEPLOYMENT.md before exposing a live API. Source code, Docker configuration or an executable-looking public key alone never establishes a working deployment.
