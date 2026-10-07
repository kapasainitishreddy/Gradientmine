# GradientMine: 60-second judge brief

## The idea

**GradientMine is a bug bounty marketplace for AI models.**

A company posts a measurable model failure. Independent engineers and AI agents compete to fix it. A held-out evaluator verifies which candidate actually improved the frozen parent. The best eligible fix can receive the locked reward through Solana.

## Why now

AI coding and research agents are making experimentation supply abundant. Model owners still have a procurement problem: they pay for engineering effort and compute rather than for a verified outcome.

GradientMine changes the unit being purchased from **work** to **measured improvement**.

## Why crypto

The poster and solver may be strangers or autonomous agents.

Solana provides escrow, registered recipients, evaluator-authorized settlement and timeout refunds.

The chain does not pretend to judge ML quality. Evaluation stays off-chain.

## What works today

A real local proof:

**84.72% → 95.28%**

**+10.56 percentage points**

**360 held-out examples**

Three actual worker processes trained bounded model updates. A negative control failed. The repository contains signed evidence, held-out evaluation, statistical eligibility, artifact admission controls, a Fix Passport and a native Solana escrow program exercised through compiled local VM integration.

## Initial wedge

Start with measurable tasks:

- classification
- retrieval
- small-model fine-tuning
- latency
- cost optimization with quality guardrails

## Business

Planned 10% success fee on successful bounties plus optional private/higher-assurance evaluation.

No custom token.

## The memorable line

**Compute markets sell compute. GradientMine pays for the verified improvement.**
