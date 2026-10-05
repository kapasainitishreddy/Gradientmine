# Presentation script

Target: about 2 minutes 30 seconds with natural pauses. Prior repository guidance reports a 2–3 minute allowed length; current official recheck is blocked, as recorded in SUBMIT.md. **This file is a script, not a completed video.** Use the timed action/caption plan in [RECORDING.md](RECORDING.md). Read the latest ledger first; do not add payment, customer or hosting claims without evidence.

## 0:00–0:25 | Problem and proposition

“An AI team does not ultimately want another invoice for compute. It wants a model that performs better on a task it cares about. GradientMine explores a different contract: define the improvement, commit the reward, and inspect the evidence before settlement.

We are building model-improvement bounties, not a new cryptocurrency or a general-purpose GPU cloud.”

## 0:25–0:55 | Product

“A task owner selects a frozen parent model and commits the evaluation rules, deadline and reward. Workers independently train candidate updates. A named evaluator tests those candidates against the same held-out examples and records signed, content-addressed receipts.

The Solana escrow program binds the bounty terms, records candidate commitments and restricts settlement to a registered winner. A creator has an on-chain timeout refund rather than a promise from an unavailable server.”

## 0:55–1:25 | Evidence

“The included task is intentionally small enough to reproduce: a real neural digit classifier with a low-rank update trained on a CPU. We run separate worker processes, compare actual before-and-after results, inspect artifact hashes and verify the expected evaluator's signature.

The interface separates an eligible result from a paid result. Local runs never show pretend token transfers. A Devnet payment needs finalized transaction evidence, not a green animation.”

## 1:25–1:55 | Trust and differentiation

“The difficult part is trust. We do not claim that a signature proves training, or that one server is decentralized verification. The public digits benchmark is reconstructible and unsuitable for real-money competition.

Our initial contribution is a coherent, inspectable workflow: explicit terms, exact wallet transaction checks, independent experiments, evidence downloads and documented recovery. We are building on established low-rank adaptation and learning from verification research rather than claiming to have invented them.”

## 1:55–2:30 | Market and next test

“Our first customer hypothesis is small model-owning teams with a narrow, measurable task and properly licensed data. We plan to test the workflow with consenting design partners and compare total cost, including losing experiments, against ordinary contracted fine-tuning.

A future fee on successful bounties is a business-model hypothesis. We have internal engineering evidence, not validated customer traction yet.

GradientMine: measure the work, make the trust visible, and reward the improvement.”

## Recording

Use the actual UI, original logo and repository evidence. A screen recording with your natural narration is sufficient; a face camera is optional. Export 1920x1080 H.264 MP4, keep the total between 120 and 180 seconds, upload to an accessible host and check it signed out. Do not voice-clone anyone, imply affiliation with Colosseum or use unlicensed background music.
