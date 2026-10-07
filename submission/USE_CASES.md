# GradientMine use-case ladder

The product should lead with one category: **model bug bounties**.

Do not present every future use case as equally production-ready. Start with objectives that can be measured reproducibly.

## Tier 1: strongest near-term bounties

### Classification regression

Example: "Improve refund-intent routing from 84% to at least 92% without dropping any protected category by more than 1 percentage point."

### Retrieval quality

Example: "Increase retrieval recall@10 from 0.76 to at least 0.86 on the hidden query set without increasing average retrieved context above the declared budget."

### Small-model fine-tuning

Example: "Improve this 1-3B task model by 5 points on the private task suite under the same inference budget."

### Cost / latency optimization

Example: "Reduce p95 latency by 25% while preserving at least 99% of baseline task score."

## Tier 2: attractive after stronger evaluator infrastructure

### Hallucination reduction

Requires robust judge design, disagreement handling and benchmark governance.

### Agent reliability

Requires sandboxed tool environments, deterministic replay and side-effect controls.

### Safety / jailbreak robustness

Requires governed red-team data, multiple metrics, adaptive-attacker evaluation and release-risk review.

## Tier 3: long-term market

Any measurable AI improvement that can be represented by a frozen parent state, admissible artifact format, evaluation function, hidden evaluation set/environment, minimum useful improvement, non-regression constraints, named or distributed evaluator and payout rule.

## Design-partner interview question

Do not ask, "Would you use GradientMine?"

Ask:

"What is one model metric your team has spent engineering time trying to move in the last 90 days?"

Then:

"What would that improvement be worth if you only paid after an independent evaluation verified it?"

The first external proof we want is not compliments. It is one model owner willing to define a real bounty.
