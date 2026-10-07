# Research, data and dependency notices

Original application code, Rust escrow, browser adapter, scripts and geometric logo are MIT-licensed under LICENSE. No competitor implementation was copied. Calling dependency APIs is not a claim that we authored those libraries. Source packages retain their own notices; distribute those notices when redistributing dependency binaries.

## Dataset attribution

E. Alpaydin and C. Kaynak (1998), **Optical Recognition of Handwritten Digits**, UCI Machine Learning Repository, DOI [10.24432/C50P49](https://doi.org/10.24432/C50P49). Official dataset record: https://archive.ics.uci.edu/dataset/80/optical+recognition+of+handwritten+digits . The official dataset record was retrieved with HTTP 200 and TLS verification on October 5, 2026 and identifies **Creative Commons Attribution 4.0 International (CC BY 4.0)**, https://creativecommons.org/licenses/by/4.0/ . The page permits sharing and adaptation for any purpose with appropriate credit. No endorsement is implied.

The packaged scikit-learn digits subset is used. GradientMine normalizes pixel values by 16, performs deterministic stratified train/validation/test splitting, and trains numeric model weights. Public artifacts are outputs of this training, not the original authors' weights. This is a public and reconstructible dataset, unsuitable as a secret real-money evaluation set.

## Libraries

Direct versions are pinned in pyproject.toml / program/Cargo.lock. On October 5, 2026, versions and license metadata/files were inspected in the installed distributions after activating the managed environment. The table records those artifacts, not assumptions from mutable upstream main branches. Runtime transitive dependencies and bundled components retain their individual licenses; this is not a complete software bill of materials. In particular, keep the complete PyTorch wheel licenses directory (and any included NOTICE files) and the complete NumPy wheel license (including bundled numerical libraries) when redistributing binaries.

| Dependency | Version used | License / primary project |
|---|---|---|
| PyTorch | 2.14.1+cpu | Installed SPDX expression: Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND MIT; preserve all bundled licenses; https://github.com/pytorch/pytorch/blob/main/LICENSE |
| scikit-learn | 1.8.0 | BSD-3-Clause; https://github.com/scikit-learn/scikit-learn/blob/main/COPYING |
| NumPy | 2.3.5 | BSD-3-Clause with bundled notices; https://numpy.org/doc/stable/license.html |
| FastAPI | 0.142.2 | MIT; https://github.com/fastapi/fastapi/blob/master/LICENSE |
| Pydantic | 2.13.5 | MIT; https://github.com/pydantic/pydantic/blob/main/LICENSE |
| HTTPX | 0.28.1 | BSD-3-Clause; https://github.com/encode/httpx/blob/master/LICENSE.md |
| Uvicorn | 0.48.0 | BSD-3-Clause; https://github.com/encode/uvicorn/blob/main/LICENSE.md |
| cryptography | 50.0.2 | Apache-2.0 OR BSD-3-Clause; https://github.com/pyca/cryptography/blob/main/LICENSE |
| solders | 0.29.0 | Apache-2.0, confirmed from installed LICENSE; https://github.com/kevinheavey/solders/blob/main/LICENSE |
| solana-program | 2.3.0, with transitives locked in program/Cargo.lock | Apache-2.0, confirmed from installed Cargo.toml; individual transitive crate licenses also apply; https://github.com/anza-xyz/solana-sdk |
| Ruff | 0.14.10, development only | MIT; https://github.com/astral-sh/ruff/blob/main/LICENSE |
| Motion | 13.5.0, browser progressive enhancement via pinned jsDelivr ESM import | MIT; https://github.com/motiondivision/motion/blob/main/LICENSE |
| Playwright | 1.57.0, development only | Apache-2.0; https://github.com/microsoft/playwright/blob/main/LICENSE |
| pytest | 9.0.3, development only | MIT; installed licenses/LICENSE |
| pip-audit | 2.10.0, development only | Apache-2.0; installed licenses/LICENSE |
| setuptools | 83.0.0, build/development | MIT plus separately licensed vendored packages; installed licenses/LICENSE |

Wallet Standard discovery and signing interfaces were checked on October 5, 2026 through official native-Git source reads at the revisions recorded in docs/RESEARCH.md; both source repositories are Apache-2.0. They are reference interfaces, not bundled npm dependencies: https://github.com/wallet-standard/wallet-standard and https://github.com/anza-xyz/wallet-standard . The browser adapter is original, deliberately restricted to legacy single-instruction transactions. No wallet or sponsor logo is bundled. No external font files are bundled.

Node has no third-party npm runtime dependencies declared in package.json. The browser optionally imports the pinned Motion ESM build directly from jsDelivr at runtime; it is not an npm dependency of the repository. Tests import LiteSVM from the installed `solders.litesvm` module, supplied by solders 0.29.0; this environment does not have a separate Python `litesvm` distribution. The solders binary includes third-party Rust components whose notices remain applicable. CI install commands are in .github/workflows/verify.yml. Their distributed notices must accompany any redistributed tool binaries.

For research credits, source-verification evidence and precisely limited claims, read docs/RESEARCH.md. The paper licenses are not used as licenses for any third-party implementation. New tasks/models must separately document model and dataset licenses before use.


## Video-production references

- **latent-spaces/brag** — https://github.com/latent-spaces/brag — MIT. Used as an optional development-time agent skill for planning/rendering a short launch video. It is not a GradientMine runtime dependency.
- **feitangyuan/onetake** — https://github.com/feitangyuan/onetake — PolyForm Noncommercial 1.0.0. GradientMine documentation uses its publicly described continuity/carry ideas only as creative reference. Do not copy, vendor, modify, or execute OneTake code for a commercial/promotional deliverable unless the intended use is confirmed to comply with its license.

No OneTake source code or assets are vendored into GradientMine.

## UI design references

- **Motion** — https://motion.dev — MIT. GradientMine uses the pinned open-source Motion 13.5.0 browser ESM build for optional entrance, winner and theme-change animation. The application remains functional when the module cannot load and disables the enhancement for `prefers-reduced-motion`.
- **Radix Colors / Radix Themes** — https://github.com/radix-ui/colors and https://github.com/radix-ui/themes — MIT. Consulted as open-source references for accessible contrast scales and theme-system ergonomics. GradientMine's Void, Aurora and Paper palettes, CSS, layout and components are original; Radix packages or component source are not bundled.


## Colosseum motion-design references

- **yihui-dev/awesome-opus5-5-videos** — https://github.com/yihui-dev/awesome-opus5-5-videos — MIT. Used as a reference collection of publicly shared motion-design prompts and implementation techniques. GradientMine's cinematic proof stage is an original Canvas implementation; no source code, media assets, branded artwork, or prompt text from the collection is vendored.
- The cinematic redesign draws high-level motion-direction inspiration from the collection's professional SaaS-launch/showreel prompts, including **@moritzkremb** (professional SaaS launch-video grammar), **@ajith_io** (go-all-out showreel pacing), **@ezshine** (feature-led product introduction), and **@0xfemyn** (short dynamic motion-graphics intensity). GradientMine translates those ideas into an original interactive site using its own Canvas, CSS and Motion code. Prompt wording, source code, branded assets and media from the collection are not copied into the product.
