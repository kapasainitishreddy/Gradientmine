# Colosseum pitch script

Target: 2 to 3 minutes.

## 0:00-0:20 — Hook

"AI teams spend money on engineers and compute hoping a model gets better. But they do not actually want GPU hours. They want the model fixed.

GradientMine is a bug bounty marketplace for AI models. A company posts a measurable model failure, engineers and AI agents compete to fix it, and the best verified improvement gets paid."

On screen: **Put a bounty on your AI's worst problem.**

## 0:20-0:45 — Concrete use case

"Imagine your support-routing model is stuck at 84% accuracy. You need at least 92%.

Instead of hiring one consultant and paying for the attempt, you post the model, metric, minimum improvement, deadline and reward. Those rules are frozen before anyone competes."

On screen: Bounty Rules.

"This generalizes to retrieval quality, small-model fine-tuning, latency, cost and other measurable model failures."

## 0:45-1:15 — Competition

"Workers can be independent ML engineers or autonomous research agents. They train a fix and submit a bounded model artifact.

They can see development feedback, but not the held-out result that decides the bounty."

On screen: Fix Arena.

"That separation matters because a worker-reported score is not evidence that the model generalizes."

## 1:15-1:45 — Real proof

"This is a recorded real run from the repository, not a mockup.

The parent classifier scored 84.72%. Three independent worker processes submitted actual low-rank updates. The selected candidate scored 95.28% on 360 held-out examples, a 10.56 percentage-point improvement, with a positive adjusted lower bound."

On screen: recorded proof and candidate table.

"The third worker is intentionally trained on shuffled labels and correctly fails."

## 1:45-2:10 — Why Solana

"Model quality stays off-chain with a named evaluator. Solana handles the part a blockchain is good at: escrow, registered payout recipients, authorized settlement and timeout refunds.

That lets a company and an unknown engineer or agent coordinate globally without inventing a token."

On screen: Bounty → Escrow → Submitted → Evaluated → Winner → Paid.

## 2:10-2:35 — Safety and evidence

"Untrusted workers do not hand the evaluator arbitrary executable code in the current task format. GradientMine admits bounded numeric adapters, checks hashes, signatures, architecture and shape, then creates a machine-readable Fix Passport for the accepted result."

On screen: Safe Submission Boundary and Fix Passport.

## 2:35-2:55 — Business

"Our initial wedge is small AI teams with narrow measurable model failures. The planned business model is a success fee on settled bounties plus private higher-assurance evaluation.

Compute markets sell compute. Freelance platforms sell time.

GradientMine sells the outcome: measurable AI improvement."

## Final line

"Put a bounty on the model bug. Pay for the fix that actually works."

## Claims to avoid

Do not say decentralized model verification, proof of training, trustless ML evaluation, live customer marketplace, live Devnet payout unless finalized evidence exists, three independent machines, production anti-cheating benchmark, existing revenue, or willingness to pay.
