# GradientMine - Colosseum Crypto World's Fair 2026

Portal-ready draft prepared October 10, 2026. **Owner review required before submission.** Copy the answers, not the bracketed instructions. Field ceilings below follow community reporting of the live form and must be rechecked against the owner's logged-in portal.

## Public profile

**Project:** GradientMine

**Tagline:** Put a bounty on your AI's worst problem.

**Website:** https://gradientmine.pages.dev (read-only proof viewer)

**GitHub:** https://github.com/kapasainitishreddy/Gradientmine (public)

**Product category:** AI / developer infrastructure, choose closest exact portal option.

**Chain:** Solana only.

**Mobile-focused dApp:** No. Responsive browser interface.

**Primary team location:** Pennsylvania, United States (founder to confirm exact field response).

**Graphic (public JPEG):** https://github.com/kapasainitishreddy/Gradientmine/releases/download/colosseum-submission-2026/gradientmine-colosseum-graphic.jpg . Visually review in the portal.

**Pitch recording:** https://github.com/kapasainitishreddy/Gradientmine/releases/download/colosseum-submission-2026/gradientmine-pitch-colosseum-2026.mp4 . It is a newly recorded 120-second caption-led actual-UI video. Verify the version in the current public release after the final subtitle-QA run, anonymous playback, and portal support. Founder narration would strengthen it.

**Demo recording:** https://github.com/kapasainitishreddy/Gradientmine/releases/download/colosseum-submission-2026/gradientmine-demo-colosseum-2026.mp4 . Newly recorded 165-second actual-UI walkthrough; verify subtitle-QA, anonymous playback, and the form's accepted host. Static viewer is recorded local evidence, not live backend.

**X profile / Telegram contact:** Founder must provide real, current account/contact details. Do not invent.

## Answers with character ceilings

### Public brief description (384/500 characters)

GradientMine turns measurable AI model failures into bug bounties. Model owners freeze the target, metric, evaluator, deadline, and reward; engineers and AI agents compete to improve the model; a named evaluator verifies the best eligible fix against held-out data. A native Solana escrow program supports outcome-based settlement. Current proof is local, not a live paid marketplace.

### What are you building and for whom? (741/1000 characters)

GradientMine is an outcome-based model-improvement bounty platform for small AI teams, applied-ML developers, and eventually agent builders. Instead of paying for hours or GPU usage, a model owner specifies a measurable failure and precommits to a metric, minimum useful improvement, evaluation policy, deadline and reward. Independent workers submit bounded model updates. A named evaluator tests candidates against a withheld set, checks eligibility and identifies the best fix. Current implementation includes actual PyTorch worker training, signed artifacts and evaluator receipts, a Fix Passport, and a native Rust Solana escrow program exercised in local LiteSVM. The public website is a read-only recorded proof, not a production API.

### Why did you build this, and why now? (721/1000 characters)

Model owners often know exactly which metric must improve but cannot guarantee that a consultant, internal experiment or compute purchase will deliver it. At the same time, ML tooling and coding/research agents lower the cost of experimenting with competing fixes. Our hypothesis is that measurable model improvements can be purchased like bug-bounty outcomes, with clear rules before anyone starts and verifiable evidence afterward. We are starting with narrow, reproducible tasks because arbitrary LLM quality claims require much stronger evaluation. Solana provides programmable escrow and refunds for people who do not know one another, while a named off-chain evaluator remains accountable for judging model quality.

### How does your product use Solana? (360/500 characters)

A native Rust Solana program supports bounty escrow, worker registration, evaluator-authorized winner settlement and timeout refunds. The model and evaluation stay off-chain. Compiled Solana program execution and settlement logic have been verified locally with LiteSVM; we have not established an integrated funded Devnet payout or deployed production escrow.

### Did anyone outside the registered team do meaningful work? (333/600 characters)

AI coding assistance was used for research, implementation, tests, design, and draft writing under the project owner's direction. Open-source dependencies are attributed in THIRD_PARTY_NOTICES.md. The founder must confirm whether any unlisted human made a meaningful contribution and disclose their role accurately before submitting.

### Anything else judges should know? (416/500 characters)

Recorded local proof: a small Digits classifier improved from 84.72% to 95.28% on 360 held-out examples (+10.56 percentage points). Three worker processes ran on one host, one as a disclosed negative control. The evaluator is trusted; the public dataset is reconstructible; there is no live Devnet payout, external customer validation, or revenue claim. See the repository for signed evidence and honest limitations.

### How do you know people need it? (652/1000 characters)

This is an unvalidated commercial hypothesis supported so far by engineering evidence, not by customer interviews or willingness-to-pay data. The underlying pain is identifiable: teams can pay for ML labor or compute without receiving a specified quality improvement. Before asserting demand, we plan to interview 3-5 model-owning design partners, collect real baseline/target/cost constraints, run one consented competition per partner, and compare total worker/evaluation spend with the team's existing alternative. We will report non-winners and failures, not just the best model. No pilots, signed letters, paying users, or revenue are claimed yet.

### How far along are you; do you have users? (644/1000 characters)

Working local prototype and public read-only evidence viewer; no external users or paying customers are claimed. A small PyTorch model improved from 84.72% to 95.28% on 360 held-out examples across three worker processes on one host. Candidates use bounded numeric artifacts, signed manifests, held-out evaluation, adjusted statistical eligibility, a downloadable Fix Passport and a native Rust Solana escrow program. The escrow path has passed compiled local LiteSVM tests, and the latest GitHub CI on October 8 passed. Missing: hosted Python/evaluation backend, real Devnet end-to-end payout, real-wallet E2E, outside pilots and live billing.

### Who competes, and what is your differentiation? (593/1000 characters)

The practical substitutes are in-house fine-tuning, ML contractors, compute marketplaces, model-evaluation suites and benchmark competitions. They each address part of the process: labor, compute, measurement or research contests. GradientMine's proposed wedge combines a precommitted buyer-defined improvement threshold, independent competing fixes, hidden final evaluation, bounded artifact admission, signed receipts, a model lineage passport and programmable reward settlement. This is not a claim that no other platform supports bounties, and our advantage is not commercially proven yet.

### Business model (247/500 characters)

Planned 10% success fee on successfully settled bounties, plus optional private evaluator hosting and higher-assurance audits. This fee is a hypothesis, not yet implemented or collected. No custom token, live billing, users or revenue are claimed.

### How long have you been working? (346/500 characters)

The visible repository history documents hackathon-period development and verification during October 2026. The founder must verify the actual start date, time commitment, any pre-September-14 work and reused source, and disclose pre-existing work truthfully. Do not treat Git commit dates alone as proof that all work began during the hackathon.

## Technical integrations

Python 3.11+ and PyTorch for bounded model training/evaluation; native Rust Solana SBF escrow program, Solana wallets/Ed25519 transaction signing and compiled LiteSVM local verification; SHA-256 content addressing, Ed25519 worker/evaluator receipts; browser JavaScript and HTML/CSS; Cloudflare Pages for static proof; Docker, Node, Playwright and automated CI. A separate local research-lab prototype is bounded and not a public production multi-model service. No Ethereum, Base or other chain claimed.

## Founder, team and accelerator declarations - DO NOT GUESS

- **Founder background draft:** Founder of Syrava, builds applied AI/software products, with graduate training in Data Science and an engineering background. Confirm exact credentials, current role, ownership and any relevant employer/IP restrictions before using first-person wording.
- **Registered team:** Use the names and backgrounds of actual registered members only. Solo participation is permitted.
- **Where the team works / relocation:** Confirm real city, collaboration format and willingness/eligibility for an in-person accelerator. Do not infer immigration or work permissions.
- **Start date, weekly hours and pre-existing work:** Must be verified by founder. Pre-September 14 source/idea/datasets are disclosed, not hidden.
- **Entity legally formed? Outside investment? Fundraising? Token?** Founder must answer each yes/no according to actual facts. There is no custom token in the current product.
- **AI/non-team human contributions:** Confirm before reusing the draft above.
- **Pitch / demo links:** Public MP4s are linked above. Replace with YouTube/Loom/Vimeo streams if required by logged-in portal; do not paste an untested link into the final form.
- **Final owner survey and member profiles:** Complete on Colosseum after reviewing the product fields.

## Verified versus unverified

- Verified in repo: October 8 latest GitHub CI success at commit dcd659be76e6ebc22cca487b25806b09e74b0a44; local model benchmark; compiled local escrow tests; published read-only web source.
- Site: Cloudflare API verified production deployed head `dcd659b` on October 8; independent signed-out desktop and 390px mobile browser checks returned HTTP 200 and showed the recorded model scores and no-payout disclosure on October 10.
- Verified: the latest product code matched production at the start of submission preparation and the new public release has MP4/JPEG/SRT assets. Unverified: live funded Devnet payout, Phantom real-extension flow, customer interviews, revenue, hosted backend, organizer acceptance of video hosts/caption-only pitch, completed portal survey and final product submission.

## Official sources

- https://colosseum.com/hackathon
- https://colosseum.com/worldsfair
- https://colosseum.com/legal/Crypto%20World%27s%20Fair%20Hackathon%20Rules.pdf
- Community form field-limit report: https://tr.superteam.fun/colosseum/the-form-itself (actual portal supersedes it)

**Deadline:** October 12, 2026, 11:59 p.m. Pacific, corresponding to October 13, 2026, 2:59 a.m. Eastern daylight time.
