# Source and branch reconciliation — 2026-10-28

## Chosen source

- Remote `main` at inventory time: `442cb500d2cc24c394c7baf5a536dc2c0cd454d0`.
- Selected branch base: remote `feat/colosseum-judge-media-room-20261012` at `ec06f5033aad91963e892d8c7bd43bea6acbced5`.
- Relationship: selected branch is current `main` plus exactly one commit and one file, `web/review.html`. The page links the existing buyer studio, recorded evidence tour, signed-receipt inspector and public video links. It discloses local evidence, evaluator trust and absent funded Devnet payout.
- Proposal work branch: `proposal/gradientmine-local-bounty-journey-20261028`. It was created from the selected base after fetching only that exact existing remote ref. No existing branch was changed. The proposal branch name was absent from the remote at creation.

## Relevant branch comparison

| Existing remote ref | Exact tip | Difference from current `main` | Reconciliation |
|---|---|---|---|
| `feat/colosseum-judge-media-room-20261012` | `ec06f5033aad91963e892d8c7bd43bea6acbced5` | 0 main-only / 1 branch-only; adds `web/review.html` | Preserved as the proposal base; retain the standalone judge room. |
| `media/narrated-remaster-20261011` | `ba4a44ce9889b8f04e3adf64d971513b7d69e183` | 0 main-only / 5 branch-only; adds `.github/tools/publish_narrated_colosseum.py`, `.github/tools/remaster_assets.py`, `.github/workflows/colosseum-narrated-release-once.yml`, `.github/workflows/remaster-assets-once.yml`, and `submission/remaster-20261011/plan.json` | Preserve in backlog as the narration/remaster and release workflow family. Not copied or triggered: it is an existing worker branch and the current task forbids publication. Review output/license/dependency and workflow authority if later adopted. |
| `feat/colosseum-judge-studio-20261011` | `cc71eb40c285e4ce8a3f9a3679574599051ccf89` | Historical ancestor of `main`; no exclusive feature to port | Bounty Studio, its browser QA and supporting product page are already in current `main`. Their present semantics were inspected before adding a separate local simulation. |
| `feat/colosseum-one-click-evidence-audit-20261011` | `22e7960bec36604ef1512d2c45ee3d9004276b3d` | Historical ancestor of `main`; no exclusive feature to port | Public artifact hash/signature audit and explicit failed states are already in current `main`. |

Other inventoried refs were read but are not bases for this bounded change. No competing branch was reset, edited, merged or pushed.

## Ownership and unresolved reconciliation

Public Git refs and PR metadata do not establish whether a worker still owns `media/narrated-remaster-20261011` or any other unmerged branch. The branch was therefore left untouched. Mainline product work added here does not replace that work family; the feature ledger keeps it visible. If that worker later proposes a merge, compare its workflow publication behavior, source commit, generated assets, permissions and release claims before adoption.

## Competitor evidence and design decisions

Primary product documentation reviewed on 2026-10-28:

- Kaggle's official competition docs distinguish a public leaderboard from the final private leaderboard, with the public result based on a sample and final ranking based on the remaining test data: <https://www.kaggle.com/docs/competitions>.
- Kaggle's official setup guide says submissions are automatically scored using an evaluation metric and reflected on a live leaderboard: <https://www.kaggle.com/docs/competitions-setup>.
- HackerOne's report-state documentation distinguishes initial validation, pending program review and triaged reports: <https://docs.hackerone.com/en/articles/8475030-report-states>.
- HackerOne's award documentation describes awards attached to reports and recommends communicating reasons for awards or declines: <https://docs.hackerone.com/en/articles/8524543-awarding-bounties>.

These are workflow references only. The proposal uses generic patterns—freeze evaluation terms, distinguish pending/rejected/verified evidence, and expose settlement state—and original GradientMine styling. No competitor artwork, branding, user content or source code was copied. There is no independently reviewed app-specific review/forum sample for Kaggle or HackerOne in this task; the pain hypothesis and any competitor complaint remain **UNVERIFIED**. No complaint is inferred from the product documentation.

## Bounded implementation boundary

The Bounty Studio's added journey is a deterministic browser-only synthetic fixture. It is separate from (1) the real recorded Digits training and (2) the Research Lab task family. It does not upload models or data, call the live API, create a wallet intent, access chain RPC, lock funds, or pay. The demo key signs only a generated fixture. The synthetic 16-example set is public/reconstructible and cannot substantiate secret holdout security or model quality. The actual evaluation authority in any later funded service remains trusted.

The competing source uses no new external runtime, artwork or model service. The existing recorded artifact files and public evidence are unchanged by this implementation.

## Independent skeptical review disposition

An independent read-only reviewer identified four issues in the first patch. All were addressed before the verification run:

1. **Evaluator signature was self-anchored.** The receipt used to include a generated public key alongside its signature. The frozen policy now pins the synthetic evaluator public key and key hash, and receipt verification uses that key from the policy. The matching private half is visibly disclosed as bundled in public demo source; this only detects accidental edits and does not prove evaluator identity or create a trust boundary.
2. **Cancel could claim deletion after browser storage denied it.** Cancel now keeps the run and says deletion failed if `removeItem` throws. It only reports deletion after successful removal. Paused checkpoints keep a delete control; unreadable checkpoints have a separate discard control.
3. **Restore validation was incomplete.** Resume now validates checkpoint version/state, frozen policy/hash and schema, baseline, task family, budget, candidate shape/hash/signature/duplicates, receipt signature/lineage, and no-transaction recovery state before rendering resumed details. Corrupt JSON has a discard path.
4. **Duplicate `Path` import and assertion ordering.** Removed the duplicate import and updated tests for the additional submission-identity check.

Browser regression coverage now deliberately tampers with stored policy, blocks `removeItem`, retries successful deletion, and exercises malformed JSON. No real wallet or transaction path was found in the reviewed proposal.
