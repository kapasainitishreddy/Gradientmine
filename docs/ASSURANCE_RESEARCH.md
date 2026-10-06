# Assurance-market research synthesis

This note explains the research ideas behind GradientMine's current product direction and clearly separates implemented mechanisms from roadmap concepts. It is not a novelty claim or a literature-exhaustive academic survey.

## Current thesis

GradientMine treats model improvement as an adversarial procurement problem. A task owner wants a capability delta, but the worker's effort is hidden, public benchmarks can be gamed, evaluation is costly, artifacts can be unsafe to execute, and the evaluator remains an authority. The current release therefore prioritizes committed terms, held-out evaluation, explicit trust, bounded artifacts, statistical evidence and recoverable settlement.

## Research that directly shaped the shipped interface

### Strategic benchmark hacking
Xiaoyun Qiu, Yang Yu and Haifeng Xu, **On Benchmark Hacking in ML Contests: Modeling, Insights and Design** (2026), https://arxiv.org/abs/2604.22230 .

The paper models contestants allocating effort between genuine capability improvement and contest-specific benchmark optimization, and studies how reward structure changes equilibrium behavior. GradientMine does not implement the paper's optimal mechanism. It uses the result as motivation for visibly separating worker development scores from the evaluator's assurance score and for treating payout design as a mechanism-design problem rather than tokenomics decoration.

### Anytime-valid ranking
Runzhe Gu et al., **Anytime-Valid Inference for Online Ranking of Large Language Models (SERPANT)**, ICML 2026, https://proceedings.mlr.press/v306/gu26l.html .

SERPANT uses e-processes and adaptive comparisons to maintain anytime-valid family-wise error control in sequential model ranking. GradientMine v1 does not implement e-values or adaptive stopping. The current fixed paired-bootstrap gate remains approximate. SERPANT is a roadmap direction for repeated or adaptively monitored competitions.

### Adaptive evaluation
Peiyu Li et al., **Adaptive Testing for LLM Evaluation: A Psychometric Alternative to Static Benchmarks (ATLAS)**, ICML 2026, https://proceedings.mlr.press/v306/li26fx.html .

ATLAS uses Item Response Theory and Fisher-information-guided item selection, reporting large reductions in required evaluation items while retaining useful measurement precision. GradientMine does not implement IRT or ATLAS. It motivates the future concept of an evaluation budget that spends private test examples where candidate uncertainty is highest.

### Strategy auctions
Lisa Alazraki et al., **Scaling Small Agents Through Strategy Auctions**, ICML 2026, https://proceedings.mlr.press/v306/alazraki26a.html .

SALE lets agents bid strategic plans evaluated by a cost-value mechanism. GradientMine currently accepts completed worker artifacts, not pre-experiment research-plan bids. This motivates a longer-term move from an all-pay contest toward outcome-oriented R&D procurement where contributors can propose expected improvement and cost before compute is spent.

### AI/ML provenance
C2PA 2.3, **Guidance for Artificial Intelligence and Machine Learning**, https://spec.c2pa.org/specifications/specifications/2.3/ai-ml/ai_ml.html .

C2PA's guidance covers model provenance, training datasets, fine-tuning, LoRA-style adapters, versions and training-environment attestations. GradientMine's Model Passport is an original lightweight JSON evidence surface inspired by the broader provenance goal; it is not a C2PA credential and should not be described as standards-compliant.

## Important prior art already acknowledged

See [RESEARCH.md](RESEARCH.md) for LoRA, Proof-of-Learning, Gensyn Verde, Wallet Standard and dataset sources. Proof-of-improvement and decentralized ML are not claimed as new categories. GradientMine's product focus is the assurance workflow around customer-defined capability procurement.

## Implemented now

- explicit Assurance Contract view derived from the immutable bounty policy
- development score kept separate from held-out assurance score
- predeclared candidate limit and family-wise alpha
- approximate multiple-candidate-adjusted paired bootstrap lower bound
- no-winner state when no candidate meets current eligibility
- bounded numeric adapter submission rather than arbitrary worker code
- SHA-256 content addressing, worker signatures and validator receipts
- known-architecture and merged-weight validation
- Model Passport generated from actual accepted-result evidence
- explicit named-validator trust boundary
- Solana escrow/refund program, locally compiled and integration-tested

## Not implemented and not to be claimed in the hackathon entry

- anytime-valid e-value ranking / SERPANT
- ATLAS / Item Response Theory adaptive benchmark selection
- hidden commercial benchmark security
- peer-prediction or decentralized evaluator consensus
- TEEs or GPU remote attestation
- zkML / zero-knowledge evaluation
- proof that submitted training actually occurred
- backdoor-free model certification
- Shapley-style contribution royalties
- model-composition reward allocation
- autonomous research-agent miners
- strategy-auction procurement
- mainnet payments

## Research roadmap

1. Replace the public reconstructible demo benchmark with a properly licensed private assurance set.
2. Define multi-objective capability contracts with customer-specific non-regression requirements.
3. Study anytime-valid ranking for repeated/adaptive candidate evaluation.
4. Study adaptive evaluation to reduce private benchmark exposure and validator cost.
5. Add probabilistic replay audits for workloads that can be made reproducible.
6. Evaluate hardware attestation for private enterprise jobs.
7. Test procurement/prize mechanisms against total compute cost and benchmark-gaming incentives.
8. Measure whether complementary accepted artifacts can be safely composed before discarding losing experiments.

The product claim remains deliberately narrower than the roadmap: **compute is an input; GradientMine makes the evidence required to purchase a model improvement explicit.**
