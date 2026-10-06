# Submission copy

## Name
GradientMine

## One line
GradientMine is an assurance market for AI improvement: define a measurable capability delta, let independent workers compete, and settle only against committed evaluation evidence.

## Product description
AI teams do not ultimately buy GPU-hours. They buy a model that performs better on a task they care about. GradientMine turns that outcome into an explicit assurance contract: a task owner commits a frozen parent model, metric, minimum improvement, evaluator, candidate budget, deadline and reward. Independent workers run real training and submit content-addressed numeric adapters plus signed manifests. After the cutoff, one named evaluator compares candidates on held-out examples, applies the predeclared threshold and adjusted paired-bootstrap rule, signs receipts, and selects an eligible winner.

The interface separates worker-reported development scores from held-out assurance scores, exposes the confidence lower bound, shows an Artifact Firewall describing the admission controls, and generates a downloadable Model Passport from the winning evidence. Solana is used for economic commitments and recovery: Devnet escrow, registered recipients, authorized settlement and a timeout refund. Model files and evaluation data stay off-chain.

The current public proof uses real CPU PyTorch training on a deliberately small digit-classification task. The recorded run improved held-out accuracy from 84.72% to 95.28%, a +10.56 percentage-point observed delta across 360 held-out examples, with a +6.11 pp adjusted lower bound. That is engineering evidence, not a claim of LLM-scale performance or generalization. The published viewer is read-only local evidence and shows no blockchain payout because no integrated Devnet payout has yet been finalized.

## Blockchain and tools
Solana Devnet; native Rust Solana escrow program; solders client; Wallet Standard; FastAPI; SQLite; PyTorch; scikit-learn digits; WebCrypto SHA-256 and Ed25519; vanilla JavaScript; Cloudflare Pages for the public read-only evidence viewer.

## Why blockchain here?
The chain does not decide whether a model is good. It commits the economic terms around the experiment. A creator escrows a test reward, candidate recipients can be registered, the named validator can authorize the selected payout, and the creator can recover an unpaid reward after the timeout even if the coordinator disappears. That financial state is independently inspectable. Models, training data and private evaluation data remain off-chain.

## Insight
Compute markets sell an input. Model owners care about an outcome. The difficult part is not only finding compute; it is deciding when an improvement claim is strong enough to pay for when workers, benchmarks, evaluators and submitted artifacts may all be strategic or unreliable. GradientMine makes that assurance policy visible instead of hiding it behind a leaderboard score.

## Differentiation
GradientMine is not presented as the first proof-of-improvement system and does not claim decentralized ML verification. Its current differentiation is the productized assurance workflow around a customer-defined model-improvement bounty:

- immutable policy and explicit evaluator authority
- development score separated from held-out assurance
- adjusted lower-bound evidence rather than point-estimate-only ranking
- content-addressed artifacts and signed worker/evaluator statements
- an Artifact Firewall that rejects arbitrary worker code in favor of bounded numeric adapters against a known architecture
- a machine-readable Model Passport for the accepted result
- exact browser-side wallet intent checking and recovery/refund paths
- no custom token and no fake local token activity

## Initial customer hypothesis
The initial buyer is a small model-owning team with a narrow, measurable problem: improve a classifier, reduce a failure rate, or beat a frozen baseline under explicit constraints. The initial contributor is an independent ML engineer or research agent operator willing to compete on a bounded task. A properly licensed private assurance set and a stronger parent are prerequisites for commercial testing.

## Go-to-market hypothesis
Start with a small, opt-in design-partner cohort recruited through ML engineering communities and founder outreach. Work with each task owner to define the baseline, metric, minimum useful delta, non-regression requirements, evaluation budget and artifact rights. Publish permissioned case studies that report total compute, evaluator cost, failed experiments and uncertainty, not only the winner. Expand only if task owners repeat and contributors accept the real risk/reward terms.

## Business-model hypothesis
A future business model could charge a disclosed fee on successfully settled bounties plus separately priced private evaluation or higher-assurance execution. A 5% service fee is only an example hypothesis. This release charges no protocol commission and has no token sale.

## Honest traction
Implemented and internally verified: real CPU worker processes, bounded adapters, signed manifests and receipts, held-out evaluation, statistical eligibility, exact wallet-intent checks, recovery paths, a native Rust escrow program exercised locally in LiteSVM, browser QA, dependency/security checks, and a public read-only evidence viewer at https://gradientmine.pages.dev .

Not yet validated: customer demand, willingness to pay, repeat usage, independent worker economics, a private benchmark, real Phantom-extension QA, or an integrated finalized Devnet training-to-payout run. Demo wallets and repeated CI runs are not customers.

## Research roadmap, not shipped claims
Research directions include anytime-valid sequential ranking, adaptive evaluation, richer non-regression contracts, probabilistic replay audits, hardware attestation, multiple independent evaluators, safe model-composition rounds and privacy-preserving evaluation. These are not presented as implemented features.
