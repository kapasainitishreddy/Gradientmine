# Presentation script

Target: 2 minutes 30 seconds. The current Colosseum FAQ asks for a two-to-three-minute presentation. This is the startup pitch, not the technical demo.

## 0:00–0:25 | Problem

“AI teams do not ultimately want another invoice for GPU time. They want a model that performs better on a task they care about.

But outcome-based AI work creates a harder question: when an outside worker claims an improvement, what evidence is strong enough to pay for?”

## 0:25–0:52 | Insight and product

“GradientMine is an assurance market for AI improvement.

A task owner defines a capability contract: the frozen parent model, objective metric, minimum useful improvement, evaluator, candidate budget, deadline and reward. Independent workers compete by training real model updates.

We keep the trust boundary explicit. Solana commits the economic terms. A named evaluator judges model quality.”

## 0:52–1:22 | Real evidence

“Our reproducible proof-of-function runs three independent worker processes on one machine using actual PyTorch training.

The parent scores 84.72 percent on the held-out set. The best candidate reaches 95.28 percent, an observed improvement of 10.56 percentage points across 360 held-out examples. The adjusted paired-bootstrap lower bound is positive at 6.11 percentage points.

The Arena deliberately separates each worker's development score from the held-out assurance score.”

## 1:22–1:48 | Security and provenance

“Winning is more than a leaderboard row.

GradientMine uses content-addressed artifacts, signed worker manifests and signed evaluator receipts. The Artifact Firewall accepts bounded numeric adapters against a known architecture rather than executing arbitrary worker-supplied code. The accepted result receives a downloadable Model Passport linking its parent, artifact, policy, evaluator and measured delta.

Those controls improve inspectability; they do not prove that a model is backdoor-free or that training happened exactly as claimed.”

## 1:48–2:08 | Why Solana

“The chain handles the part it is good at: escrow and settlement rules.

A creator can commit a test reward, recipients can be registered, the selected winner can be paid by the program, and an unpaid bounty has an on-chain timeout refund. Models and private evaluation data stay off-chain.”

## 2:08–2:30 | Business and vision

“Our first customer hypothesis is a small model-owning team with a narrow, measurable failure and properly licensed data. We plan to test outcome-priced competitions against ordinary contracted fine-tuning, including the cost of losing experiments and evaluation.

Today we have engineering evidence, not customer traction.

Compute markets sell GPU time. GradientMine buys assured capability improvement.”

## Recording notes

Use https://gradientmine.pages.dev for the public evidence surface, plus terminal/source footage where useful. Keep the public mode banner visible when discussing recorded evidence. If a real Devnet payout has not been finalized before recording, say so clearly and do not show a synthetic Explorer transaction. Natural narration is preferred over a silent caption-only pitch.
