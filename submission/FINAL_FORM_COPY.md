# Final Colosseum form copy

This sheet is designed to paste into the signed-in submission portal. Fit to actual field limits if the portal differs. Owner-only identity/team declarations still require founder review.

## Product name
GradientMine

## One-line description
An assurance market where teams post measurable AI-improvement bounties, independent workers compete with real model updates, and rewards settle against committed evaluation evidence.

## Short description
GradientMine turns a model-improvement target into an explicit assurance contract. A task owner freezes the parent model, metric, minimum useful delta, evaluator, deadline and reward. Workers run real training and submit content-addressed numeric adapters. After cutoff, a named evaluator recomputes held-out results, applies the predeclared statistical rule, signs receipts and selects an eligible winner. The UI separates development scores from assurance scores, exposes artifact admission controls and produces a Model Passport. Solana Devnet handles escrow, registered recipients, authorized settlement and timeout refunds; model files and evaluation data stay off-chain.

## Problem
GPU and DePIN markets sell compute, but an AI team usually cares about the outcome: did the model actually get better on the task that matters? Outsourcing that outcome creates a trust problem because worker-reported scores can overfit benchmarks, artifacts can be malformed or unsafe to execute, evaluators remain a point of authority, and payment rules can change after work has been done.

## Insight
Treat model improvement as a procurement contract with an explicit assurance policy, not as raw compute rental. Separate development feedback from held-out assurance, bind the evaluation and economic terms before settlement, and make the resulting evidence inspectable.

## What we built
- actual CPU PyTorch low-rank model updates from independent worker processes
- content-addressed adapters and signed worker manifests
- held-out evaluator scoring after cutoff
- predeclared minimum delta and adjusted paired-bootstrap eligibility
- deterministic winner selection
- Assurance Contract UI
- Arena comparing development vs held-out assurance
- Artifact Firewall showing enforced admission constraints
- downloadable Model Passport
- exact wallet authentication and transaction-intent checking
- native Rust Solana escrow program with registration, settlement and timeout refund paths
- local compiled-program integration through LiteSVM
- public read-only evidence viewer

## Current measured result
Recorded proof-of-function:
- parent held-out accuracy: 84.72%
- accepted candidate: 95.28%
- observed delta: +10.56 percentage points
- adjusted lower bound: +6.11 pp
- held-out examples: 360
- three actual worker processes on one host
- third worker is a disclosed shuffled-label negative control
- local evidence only; no integrated Devnet payout is claimed

## Why Solana
Solana commits and exposes the financial state of the competition. The task creator can fund escrow, candidates can be registered, the named evaluator can authorize payment to the selected worker, and the creator can recover an unpaid bounty after the immutable timeout. The model-quality decision remains off-chain because model files and evaluation data do not belong in consensus.

## Blockchains and tools
Solana Devnet; native Rust Solana program; Wallet Standard; solders; FastAPI; SQLite; PyTorch; scikit-learn; WebCrypto SHA-256 and Ed25519; vanilla JavaScript; Cloudflare Pages.

## Public links
Repository: https://github.com/kapasainitishreddy/Gradientmine

Public evidence viewer: https://gradientmine.pages.dev

The viewer is intentionally read-only recorded evidence, not the live validator/API and not proof of a Devnet payout.

## Differentiation
GradientMine does not claim to have invented proof-of-improvement or decentralized ML. The product differentiation is the assurance workflow around customer-defined model-improvement procurement: explicit evaluator authority, development-vs-assurance separation, statistical eligibility, safe bounded artifact admission, provenance/passport evidence, wallet-intent verification, and recoverable on-chain settlement without a custom token.

## Initial market
Start with small model-owning teams that have a narrow measurable task and can provide properly licensed training/evaluation data. Initial contributors are independent ML engineers or research-agent operators. A private assurance set and stronger production baseline are required before real-money testing.

## Go-to-market
Recruit a small opt-in design-partner cohort through ML engineering communities and direct founder outreach. Co-design one narrow contract per team, run a controlled competition, and publish permissioned case studies with total compute, evaluation cost, failed experiments and uncertainty. Expand through repeat task owners and contributor referrals only after the workflow demonstrates acceptable economics.

## Demand validation
No external customer demand or willingness-to-pay claim is made yet. Current evidence is product/engineering validation: real training processes, measured before/after results, signed artifacts/receipts, browser and protocol tests, compiled Solana program tests, and a public evidence surface. Planned interviews or demo wallets are not counted as traction.

## Business model
Future hypothesis: a transparent service fee on successfully settled bounties plus optional private/higher-assurance evaluation. No fee is implemented today, no willingness-to-pay result is claimed, and there is no custom token sale.

## Trust disclosure
One named evaluator remains trusted. Hashes and signatures authenticate content and statements; they do not prove that training happened or guarantee generalization. The public Digits benchmark is reconstructible and therefore is not suitable as a secure commercial assurance set. The Artifact Firewall prevents arbitrary submitted code in the current task format but does not prove a model is free of behavioral backdoors or poisoned training. Integrated Devnet payment should be claimed only after finalized matching transaction evidence exists.

## Research roadmap, not shipped
Anytime-valid sequential ranking, adaptive assurance-set sampling, richer multi-objective/non-regression contracts, probabilistic replay audits, hardware attestation, multiple independent evaluators, safe model composition, and privacy-preserving evaluation.

## Founder/team
Use submission/TEAM.md only after confirming the actual registered founder/team, location, background, funding, prior work, IP rights and eligibility declarations.

## Prior work / AI assistance
Use submission/DISCLOSURE.md and disclose all relevant pre-event work. AI assistance was used for research, programming, debugging, tests, design and draft submission materials under owner direction.
