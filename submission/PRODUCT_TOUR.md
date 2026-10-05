# GradientMine product tour production brief

This is the production brief for short GradientMine launch/product-tour videos. It is intentionally evidence-first: every metric, transaction, address and UI state shown in a video must come from the current repository or a freshly verified run.

## Tooling decision

### /brag — production tool

Use [latent-spaces/brag](https://github.com/latent-spaces/brag) for the short launch cut.

License: MIT.

Codex install:

```bash
codex plugin marketplace add latent-spaces/brag
codex plugin add brag@brag
```

Alternative project-scoped install:

```bash
npx skills add https://github.com/latent-spaces/brag --skill brag
```

Required local tooling for the full workflow includes Node.js 22+, FFmpeg, and the Hyperframes CLI. Run `npx hyperframes doctor` before rendering.

Recommended invocation from the GradientMine repository:

```text
/brag --tone polished --format landscape --duration 22 --title "GradientMine"
```

For a social vertical variant:

```text
/brag --tone polished --format vertical --duration 20 --title "GradientMine"
```

Do not enable voice by default. The official hackathon pitch/demo narration should remain a separate controlled recording unless a generated voice is explicitly desired and allowed.

Expected output belongs in an ignored or explicitly reviewed video-output directory. Do not commit large rendered binaries unless there is a clear reason. Commit the plan, composition brief and share copy when useful.

### OneTake — continuity reference, not vendored runtime code

Reference: [feitangyuan/onetake](https://github.com/feitangyuan/onetake).

OneTake is licensed under PolyForm Noncommercial 1.0.0. Because GradientMine is presented as a startup/product, do **not** copy, vendor, modify or execute OneTake code for a commercial/promotional deliverable unless the intended use has been confirmed to comply with that license.

Its public design principles may be used as creative reference:

- one visual element carries across scene boundaries;
- transitions are transformations, not slide replacements;
- the camera follows the subject rather than sitting still;
- important actions show their cause, not only the result;
- vary rhythm, including deliberate holds;
- preserve one continuous visual grammar from hook to lockup.

If an explicitly noncommercial use is later confirmed, review the current OneTake license again before running its code.

## Product-tour concept

### Central visual idea: the evidence thread

One thin gradient line is the persistent subject of the whole film.

It begins as the underline beneath the bounty target, becomes the escrow path, becomes a training curve, resolves into the winning artifact hash, passes through the signed evaluation receipt, and finally becomes the line under the GradientMine wordmark.

Nothing resets to a fresh slide. The evidence thread visibly carries the viewer from promise to proof.

### Hook

On black:

**PAY FOR IMPROVEMENT.**

A small second line appears:

**Not compute hours.**

The underline extends and becomes the evidence thread.

Do not say "decentralized AI" or "trustless verification."

## 22-second /brag launch cut

### 0:00–0:02 — Hook

Text:
- PAY FOR IMPROVEMENT.
- Not compute hours.

The evidence thread grows from the text and leads the camera into the actual GradientMine bounty UI.

### 0:02–0:06 — Commit the target

Show the real bounty policy UI.

Highlight:
- parent model commitment
- metric
- minimum improvement
- cutoff
- validator

The policy SHA should be real if readable on screen.

The evidence thread exits the policy hash and becomes the outline of the escrow state.

### 0:06–0:10 — Workers actually train

Transition from the escrow outline into an actual worker terminal or product UI showing the worker lifecycle.

Use real GradientMine training output.

Short copy:

**REAL TRAINING.**
**SIGNED ARTIFACTS.**

Do not fake GPU telemetry, node counts or mining activity.

The thread becomes a model-improvement curve.

### 0:10–0:14 — Measure the result

The curve lands on the evaluation panel.

For the recorded verified local run, the only currently documented values are:

- baseline: 84.72%
- winning candidate: 95.28%
- improvement: +10.56 percentage points

Use those values only when showing that specific recorded run.

Add a small visible label:

**Recorded local verification**

Do not imply those numbers are Devnet payment evidence or a general benchmark claim.

### 0:14–0:18 — Evidence, not vibes

The winning score contracts into the winning artifact hash.

That hash transforms into the signed validator receipt.

Copy:

**HASHED.**
**SIGNED.**
**INSPECTABLE.**

Briefly show the receipt verification state from the real UI.

### 0:18–0:21 — Settlement state

Conditional branch:

**If a real Devnet end-to-end run exists:**
show the actual payout state and real Solana Explorer link/signature.

Copy:

**PAID ON DEVNET.**

**If real Devnet settlement is still not verified:**
do not fabricate a chain animation, signature or Explorer link.

Instead show:

**DEVNET SETTLEMENT PATH BUILT**
**LIVE EVIDENCE PENDING**

This distinction is mandatory.

### 0:21–0:22 — Lockup

The evidence thread becomes the underline beneath:

**GradientMine**

End line:

**Measure the work. Reward the improvement.**

## 45–60 second continuous product tour

This is the judge-friendly product tour. Use the same evidence-thread grammar, but allow enough time for comprehension.

### Beat 1 — Why this exists

Open on:

**A model team does not actually want GPU hours.**
**It wants a better model.**

The second sentence becomes the bounty target field.

### Beat 2 — Freeze the rules

Move through the actual bounty creation UI.

Show that the task owner commits:
- parent
- evaluation commitments
- metric
- threshold
- deadline
- validator
- reward when in Devnet mode

Explain visually that changing the rules after worker entry is not the product.

### Beat 3 — Escrow

If Devnet evidence exists, transform the bounty card into the real escrow account and show the actual funding transaction.

If not, show the implemented transaction-review state and label it as unverified internet-cluster settlement evidence.

Never substitute LiteSVM for Devnet.

### Beat 4 — Independent work

The escrow outline stretches into the worker CLI.

Show one real worker command and a short section of real training progress.

Then split/recombine the evidence thread to communicate multiple independent submissions without inventing independently operated physical nodes.

### Beat 5 — Held-out evaluation

Carry the worker artifact hash into the validator panel.

Show:
- baseline
- candidate
- delta
- eligibility
- receipt

State visually:

**One named validator. Explicitly trusted.**

Do not claim cryptographic proof of training.

### Beat 6 — Winner and evidence

The winning row expands into:
- artifact hash
- model lineage
- validator receipt
- signature verification

The UI should make it obvious that "eligible" and "paid" are different states.

### Beat 7 — Payout or honest boundary

If verified:
- show actual Devnet program ID;
- show actual bounty account;
- show actual funding signature;
- show actual registration signature;
- show actual settlement signature;
- open the real Explorer transaction.

If not verified:
show the honest local boundary and say that local training/evaluation is verified while public Devnet settlement remains unfinished.

### Beat 8 — Close

Pull the camera back until the evidence thread forms the GradientMine lockup.

End:

**GradientMine**
**Model-improvement bounties with inspectable evidence.**

## Visual direction

Use the existing GradientMine product UI as the source material. Do not invent a second fake interface merely to make the video prettier.

Tone:
- polished;
- technical;
- confident;
- restrained;
- no crypto casino aesthetic;
- no neon token coins;
- no fake server maps;
- no confetti;
- no fake "AI network" particles.

Prefer:
- dark neutral ground;
- sharp typography;
- real product panels;
- content-addressed hashes as visual texture;
- thin motion lines;
- subtle depth;
- deliberate camera pushes;
- occasional still holds.

The product's strongest visual object is evidence itself.

## Continuity rules

Borrowing the useful creative lesson from OneTake without copying its implementation:

1. Every major boundary needs a carrier.
2. The evidence thread is the default carrier.
3. A product panel may expand into the next scene rather than disappear.
4. A hash may physically become the receipt that references it.
5. The training curve may become the underline of the score.
6. The camera should arrive where the next object lands slightly before the object settles.
7. Use at least two real visual holds so the film does not feel like a template montage.
8. A hard cut is reserved for a deliberate emphasis hit, not ordinary navigation.

## Evidence guardrails

The video generator must read the current repository and latest verified evidence before scripting.

Never invent:
- program IDs;
- transaction signatures;
- Explorer URLs;
- customers;
- revenue;
- worker counts;
- independently owned nodes;
- GPU fleet claims;
- benchmark secrecy;
- deployed hosting URLs;
- videos;
- model results.

A signature is an authenticated statement, not proof of learning.

The public Digits task is reproducible and not a secret anti-cheating benchmark.

LiteSVM is local program execution, not Solana Devnet.

The Playwright wallet is a test wallet, not a Phantom-extension test.

## Codex execution prompt

After the product itself is complete and the current evidence has been re-verified, run:

```text
Install and use latent-spaces/brag from its official GitHub repository to create a polished GradientMine launch video.

Before rendering, read:
- README.md
- docs/BUILD_LEDGER.md
- docs/ARCHITECTURE.md
- docs/THREAT_MODEL.md
- submission/PRODUCT.md
- submission/DEMO.md
- submission/PRODUCT_TOUR.md

Use the "evidence thread" concept from PRODUCT_TOUR.md.

Create a 20–22 second landscape launch video and, if the tooling supports it cleanly, a vertical social variant.

Use only actual GradientMine UI and current verified evidence. Do not fabricate transactions, model metrics, users, nodes, deployment URLs or Devnet state.

Use OneTake's public continuity ideas only as creative reference: every beat must visibly grow out of the previous beat and one visual carrier must survive each major transition. Do not copy or vendor OneTake code because its repository is PolyForm Noncommercial unless the intended use is confirmed compliant.

Run /brag with a polished tone. Validate the composition before rendering. Keep the actual rendered video outside git if it is large, but commit the final plan, storyboard, composition brief and share copy.

If a real Devnet payout exists by then, include only its actual Explorer evidence. If not, show the honest boundary: local training/evaluation verified, live Devnet settlement pending.
```

## Deliverables

For the final product-tour pass produce:

- storyboard/plan;
- composition brief;
- 20–22 s landscape launch video;
- optional vertical launch video;
- poster frame;
- share copy;
- 45–60 s judge product-tour plan;
- exact list of evidence shown;
- provenance note listing the repository commit and CI run used;
- a statement of whether the displayed chain evidence is local, LiteSVM or real Devnet.

A rendered video is not considered verified until it has been watched end-to-end and its visible claims have been compared against the evidence bundle.
