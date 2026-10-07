# Final recording sheet: model bug bounty narrative

Use this for new Colosseum recordings after the model-bug-bounty UI is deployed.

## Presentation

Target: 2:35 to 2:50. Official range is 2 to 3 minutes.

### Shot 1 — 0:00 to 0:20

Screen: hero.

Narration:

"AI teams spend money on engineers and compute hoping a model gets better. But they do not actually want GPU hours. They want the model fixed. GradientMine is a bug bounty marketplace for AI models."

Hold on:

**Put a bounty on your AI's worst problem.**

### Shot 2 — 0:20 to 0:45

Screen: four-step flow.

Narration:

"A model owner freezes the failure, metric, minimum improvement, evaluator, deadline and reward. Independent engineers or AI agents compete on fixes. Public development feedback helps them iterate, but hidden verification decides who actually wins."

### Shot 3 — 0:45 to 1:15

Screen: recorded proof.

Narration:

"This repository includes a real CPU proof-of-function. A small classifier starts at 84.72%. Three worker processes submit actual low-rank model updates. The selected fix scores 95.28% on 360 held-out examples, a 10.56 percentage-point improvement."

Show the negative control.

### Shot 4 — 1:15 to 1:45

Screen: Bounty Rules and Fix Arena.

Narration:

"The rules are committed before evaluation. Workers cannot win on their own reported score. The named evaluator applies the same held-out test and predeclared statistical rule to every admitted candidate."

### Shot 5 — 1:45 to 2:10

Screen: Safe Submission Boundary and Fix Passport.

Narration:

"The current task format accepts bounded numeric adapters rather than arbitrary worker code. Hashes, signatures, architecture and shape are checked. The accepted result gets a machine-readable Fix Passport linking the parent, worker, evaluator, policy and measured improvement."

### Shot 6 — 2:10 to 2:35

Screen: lifecycle / Solana evidence / trust.

Narration:

"Solana handles the economic layer: escrow, registered recipients, evaluator-authorized settlement and timeout refunds. Model quality remains off-chain with the named evaluator. No custom token is needed."

### Shot 7 — 2:35 to 2:50

Screen: hero.

Narration:

"Compute markets sell GPU time. Freelance platforms sell labor. GradientMine is designed to sell the outcome: measurable AI improvement. Put a bounty on the model bug. Pay for the fix that actually works."

## Product demo

Target: 2:35 to 2:50. Maximum 3 minutes.

### 0:00 to 0:15

Show hero and four-step flow.

Say:

"Here is the whole product: post a measurable model bug, let workers compete, verify fixes on held-out evaluation, then settle the winner."

### 0:15 to 0:40

Open the recorded Digits bounty.

Say:

"This is recorded local evidence, not customer data and not a live payment. The baseline is deliberately budget-limited at 84.72%."

### 0:40 to 1:05

Show lifecycle and candidate table.

Say:

"Three actual worker processes on one host submitted low-rank numeric updates. This third worker is a disclosed shuffled-label negative control. Held-out results are unavailable to workers until cutoff."

### 1:05 to 1:35

Show Bounty Rules and Fix Arena.

Say:

"The primary metric, minimum delta, candidate budget, evaluator, assurance-set commitment and artifact policy are frozen. Public progress and hidden verification are separate."

### 1:35 to 2:00

Show winner and statistical evidence.

Say:

"The selected candidate reaches 95.28%, improving the parent by 10.56 percentage points across 360 held-out examples. It clears the minimum and has a positive adjusted lower bound."

### 2:00 to 2:20

Show Safe Submission Boundary.

Say:

"The validator does not execute arbitrary worker code in this task format. It verifies bounded model data, hashes, signatures, architecture and merged-weight shape."

### 2:20 to 2:38

Show Fix Passport.

Say:

"The result gets a downloadable passport linking the parent, accepted model, worker, evaluator, policy and measured delta."

### 2:38 to 2:50

Show settlement status and trust section.

Say:

"This run is local, so it correctly says no finalized payout. Solana settlement is a separate economic layer. GradientMine never turns missing evidence into a success claim."

## Capture rules

- 1920×1080, 30 fps
- readable browser zoom
- no notifications
- never expose private keys, seed phrases, auth headers or private identities
- use natural narration if possible
- keep the visible recorded/local/unpaid state readable
- no fake Devnet transaction or Explorer link
- do not use the illustrative support-routing use case as if it were the recorded demo
- test final video signed out after upload
