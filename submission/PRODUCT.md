# Submission copy

## Name
GradientMine

## One line
Model-improvement bounties with actual training, inspectable evaluation evidence and Solana Devnet escrow.

## Product description
GradientMine turns a model-improvement target into a bounded competition with explicit terms. A task owner commits a parent model, evaluation rules, deadline and reward. Workers independently train low-rank candidates and submit content-addressed artifacts. A named evaluator compares candidates with the same parent on held-out examples, issues signed receipts and selects an eligible winner. The Solana program restricts escrow settlement to a registered worker and allows the creator to recover an unpaid reward after a timeout.

The included workload is a real CPU-trained neural digit classifier, not an LLM or generated scores. Local mode never simulates tokens. Devnet payments must have finalized, independently checked transaction evidence. The product makes its central evaluator and reconstructible public benchmark explicit rather than calling signatures decentralized verification.

## Blockchain and tools
Solana Devnet; native Rust Solana program; solders client; Wallet Standard; FastAPI; SQLite; PyTorch; scikit-learn digits; WebCrypto SHA-256 and Ed25519; vanilla JavaScript; reproducible tests and content-addressed numeric JSON.

## Why blockchain here?
A task owner can commit a reward and cutoff; registration and payout leave public evidence; the creator can invoke a timeout refund even if the coordinator is unavailable. The chain enforces those financial state transitions, not model quality. This is narrower than claiming blockchain solves the trust problem of ML evaluation.

## Initial customer hypothesis
Small model-owning teams seeking a narrowly measurable improvement are the proposed initial buyers. Independent ML developers are the proposed contributors. Begin with one task type and known participants rather than advertising a giant permissionless GPU network. A stronger baseline and genuinely controlled evaluation set are prerequisites for meaningful commercial testing.

## Go-to-market hypothesis
Recruit a small opt-in design-partner group through ML engineering communities and direct founder outreach. Help each team define a licensed task, baseline, utility metric and evaluation budget. Publish permissioned, reproducible case studies with total compute cost and failures, not only the winning gain. Grow through repeat task owners and contributor referrals only after measured usefulness is demonstrated.

## Business-model hypothesis
A possible future model is a disclosed service fee on successfully settled bounties plus separately priced private evaluation. A 5% example is a pricing hypothesis, not an implemented fee or validated willingness to pay. This release charges no protocol commission and has no token sale. Open competition may waste losing workers' compute; this must be measured against ordinary contracted fine-tuning.

## Honest traction
The project has internal engineering evidence: actual worker processes, measured model comparisons, signed artifacts and automated tests. External customer demand, repeat usage, willingness to pay and revenue have not been validated in this build. The latest exact commands and results are in docs/BUILD_LEDGER.md and evidence/. Do not count demo wallets or repeated CI runs as customers.

## Differentiation
A compact, inspectable outcome-bounty workflow with exact wallet-intent checks, explicit evaluator authority, measurable eligibility, evidence downloads and failure/refund handling. No claim of first-in-category novelty or replacement of decentralized training research. Important follow-up work is private-task validation and economic efficiency, not decorative miner counts.
