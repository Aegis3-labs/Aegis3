# Aegis3 — Master GitHub Issues Backlog & Engineering Sprints

> **Pacing & Independent Work Philosophy:**
> Every issue below includes a **"Think First"** section outlining the underlying theory, algorithm tradeoffs, and architectural design choices. Deadlines are calibrated for student founders balancing coursework—allocating **8 to 15 focused hours spread over 7 to 10 calendar days** per issue so each person has time to deeply understand, experiment, and write clean production code independently.

---

## 📅 Sprint Schedule Overview

```
Sprint 1: COMPLETED (Data Ingestion, Anti-Framing, CEX Tracer, Temporal Burst Weighting, Evidence Hasher)
Sprint 2: Weeks 3–4 (Nov 8 – Nov 22, 2026) -> Graph Scaling, PDF Governance Artifacts & Benchmark Suite
Sprint 3: Weeks 5–6 (Nov 23 – Dec 7, 2026) -> Advanced Anti-Evasion (Entropy & Bounded Universe) & PyVis Visualizer
Sprint 4: Weeks 7–8 (Dec 8 – Dec 22, 2026) -> FastAPI Scoring Service & React Claim-Gate Component
```

---

# 🚀 SPRINT 2 (Weeks 3–4: Nov 8 – Nov 22, 2026)

---

### Issue #3: Weakly Connected Component (WCC) Pre-Filter
- **Assignee:** **Laukik Wani (CTO)**
- **Target Deadline:** **November 15, 2026** (7 days | ~10 hours focused effort)
- **Labels:** `core-engine`, `performance`, `graph-algorithms`

#### 🧠 Think First (Theory & Design Choices):
1. **The Performance Bottleneck:** Louvain community detection has a time complexity of roughly $\mathcal{O}(N \log N)$ to $\mathcal{O}(N^2)$ depending on graph density. If a protocol has 500,000 wallets, running Louvain on the whole graph in one go consumes immense RAM and runs single-threaded for hours.
2. **The Topological Insight:** In an airdrop candidate list, 60%–70% of addresses are **isolated singleton nodes** (degree 0) or simple 1-to-1 organic transfers that have no cycles or multi-hop clusters.
3. **The Solution:** Use `networkx.weakly_connected_components` to partition the graph into independent disconnected subgraphs (islands). Discard components with size $< \text{min\_cartel\_size}$ (e.g. $< 5$ nodes) immediately. Run Louvain **only** on the remaining candidate clusters. This reduces the problem space by up to 80% with zero loss of recall.

#### 🛠️ Implementation Plan:
- **Files to create/modify:** `core-engine/filters/pre_filter.py`, update `core-engine/graph_builder.py`.
- **Inputs:** Directed or Undirected NetworkX graph.
- **Outputs:** Filtered subgraph containing only candidate cartel components ($\ge 5$ nodes), plus a list of bypassed organic singleton addresses.

#### ✅ Definition of Done:
- [ ] `pre_filter.py` defines `ConnectedComponentPreFilter(min_component_size=5)`.
- [ ] Filters out singleton and small pairs before Louvain is called.
- [ ] Preserves bypassed wallets as `Tier 1: Authentic Human (Eligible)` with 0 risk score.
- [ ] Benchmark test confirms at least a $5\times$ speedup on graphs with $> 10,000$ nodes.
- [ ] Unit tests pass in `tests/test_pre_filter.py`.

---

### Issue #8: Executive PDF Launch Audit Report Exporter
- **Assignee:** **Chirag Janbandhu (CDO)**
- **Target Deadline:** **November 18, 2026** (10 days | ~14 hours focused effort)
- **Labels:** `report-generator`, `client-facing`, `governance`

#### 🧠 Think First (Theory & Design Choices):
1. **Why HTML is Not Enough:** Protocol foundations submitting launch fairness audits to centralized exchanges (Binance, Coinbase listing teams), VC boards, or DAO snapshot votes need an immutable, professionally formatted PDF with page breaks, corporate styling, and cryptographic verification seals.
2. **Library Choice Tradeoffs:**
   - *Option A (WeasyPrint / Playwright):* Converts HTML+CSS directly to PDF. Beautiful styling, but requires system dependencies (cairo/pango) which can be tricky on Windows.
   - *Option B (ReportLab):* Pure Python, rock-solid on all operating systems (Windows, Linux, macOS), zero external binaries. Requires manual programmatic layout (flowables, tables, styles).
   - *Option C (xhtml2pdf):* Lightweight pure Python HTML-to-PDF translator.
   - *Recommendation:* Prototype with `xhtml2pdf` or `ReportLab` so it runs seamlessly on Windows without requiring local Chrome headless binaries.

#### 🛠️ Implementation Plan:
- **Files to create:** `report-generator/pdf_exporter.py`, update `run_audit.py`.
- **Inputs:** `scored_df` (DataFrame), protocol metadata, SHA-256 root manifest hash.
- **Outputs:** `Docs/launch_audit_report.pdf` (Executive 3-page document).

#### ✅ Definition of Done:
- [ ] Page 1: Executive Cover Sheet (Protocol Name, Audit Timestamp, Total Wallets, Verified Organic %, Disqualified Bot %, SHA-256 Seal).
- [ ] Page 2: Detection Methodology & Threshold Breakdown (Louvain, Jaccard, CEX convergence weights).
- [ ] Page 3: Top Flagged Bot Cartels evidence table with truncated addresses and Etherscan links.
- [ ] Generates clean PDF with zero missing fonts or layout overflow.
- [ ] Unit test in `tests/test_pdf_exporter.py`.

---

### Issue #16: Ground-Truth Benchmarking Dataset Curator (5k/5k Split)
- **Assignee:** **Chirag Janbandhu (CDO)**
- **Target Deadline:** **November 20, 2026** (12 days | ~8 hours focused effort)
- **Labels:** `data-pipeline`, `datasets`, `benchmarking`

#### 🧠 Think First (Theory & Design Choices):
1. **The Need for Negative Controls:** In scientific testing and investor due diligence, testing *only* on known bots is meaningless—a filter that flags 100% of wallets will catch 100% of bots, but have a 100% false positive rate on humans.
2. **The Benchmark Dataset:** We need an authoritative 10,000-wallet evaluation dataset:
   - **5,000 Verified Bots:** Sampled from the LayerZero purge list (`layerzero_sybil_nodes.csv`).
   - **5,000 Organic Humans:** Sampled from long-term active Gitcoin donors, Ethereum name service (.ens) holders, or historical Uniswap v3 liquidity providers.
3. **Dataset Schema:** Canonical CSV with columns: `address`, `ground_truth_label` (`bot` vs `organic`), `source_event`, `notes`.

#### 🛠️ Implementation Plan:
- **Files to create:** `data-pipeline/curator.py`, save output to `data-pipeline/datasets/benchmark_ground_truth_10k.csv`.

#### ✅ Definition of Done:
- [ ] Script cleanly merges 5,000 known sybils with 5,000 active organic wallets.
- [ ] Validates all 10,000 addresses through `WalletListNormalizer`.
- [ ] Generates synthetic and real interaction logs for reproducible test suites.
- [ ] File committed or cached in `data-pipeline/datasets/`.

---

### Issue #9: Automated Precision, Recall & F1 Benchmark Suite
- **Assignee:** **Laukik Wani (CTO)**
- **Target Deadline:** **November 22, 2026** (14 days | ~12 hours focused effort)
- **Labels:** `tests`, `benchmarking`, `metrics`

#### 🧠 Think First (Theory & Design Choices):
1. **The Core Formulae:**
   - **Precision:** $\frac{TP}{TP + FP}$ (Of all wallets we banned, how many were actually bots? Must be $> 98\%$ to avoid Twitter drama).
   - **Recall:** $\frac{TP}{TP + FN}$ (Of all bots in the candidate list, what percentage did we catch? Target: $> 85\%$).
   - **False Positive Rate (FPR):** $\frac{FP}{FP + TN}$ (Target: $< 1.5\%$).
   - **F1 Score:** $2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$.
2. **Scientific Credibility:** This script is what gets Aegis3 funded in grant applications (Arbitrum, Starknet) and incubator interviews (KGP Forge). It provides indisputable mathematical proof that the engine works.

#### 🛠️ Implementation Plan:
- **Files to create:** `tests/benchmark_suite.py`.
- **Inputs:** `data-pipeline/datasets/benchmark_ground_truth_10k.csv`.
- **Outputs:** Console summary + Markdown metrics card (`Docs/BENCHMARK_RESULTS.md`) with confusion matrix.

#### ✅ Definition of Done:
- [ ] Runs all 10,000 benchmark wallets through the full pipeline.
- [ ] Computes and prints True Positives, False Positives, True Negatives, False Negatives.
- [ ] Asserts that Precision $\ge 95\%$ and Recall $\ge 80\%$.
- [ ] Automated execution via `python tests/benchmark_suite.py`.

---

### Issue #20: Protocol Founder Discovery Calls & Problem Validation
- **Assignee:** **Vinit (CPO)**
- **Target Deadline:** **November 22, 2026** (14 days | ~10 hours focused effort)
- **Labels:** `product`, `customer-discovery`, `growth`

#### 🧠 Think First (Customer Discovery Principles):
1. **Do Not Pitch — Listen:** When speaking with protocol founders, do not try to sell them software on call #1. Ask about their past launches or upcoming TGEs:
   - *"How did you handle bot farming in your previous campaign?"*
   - *"What was the biggest headache when reviewing candidate wallet lists?"*
   - *"How much did community complaints/appeals on Discord cost you in time and morale?"*
2. **Target Audience:** Emerging protocols on testnets or point seasons (Mode ecosystem, Scroll dApps, Berachain testnet protocols, HyperEVM dApps).
3. **The Deliverable:** A structured discovery document summarizing 5 calls with founders, noting their biggest fears and willingness-to-pay.

#### ✅ Definition of Done:
- [ ] Conduct at least 5 structured discovery calls with Web3 protocol leads or foundation members.
- [ ] Document raw notes and insights in `Docs/CUSTOMER_DISCOVERY_NOTES.md`.
- [ ] Validate whether the ₹15L–28L pricing is perceived as cheap, fair, or expensive relative to their security budgets.

---

# 🛡️ SPRINT 3 (Weeks 5–6: Nov 23 – Dec 7, 2026)

---

### Issue #12: Population Interval Entropy & Diurnal Activity Clock
- **Assignee:** **Laukik Wani (CTO)**
- **Target Deadline:** **December 1, 2026** (8 days | ~15 hours focused effort)
- **Labels:** `core-engine`, `heuristics`, `anti-evasion`

#### 🧠 Think First (Theory & Design Choices):
1. **The Attacker Evasion:** Sophisticated bot operators know that uniform timers (`sleep(60)`) get caught. To evade detection, they use `sleep(random.uniform(30, 300))`.
2. **The Flaw in Bot RNG:** A pseudo-random uniform distribution is **non-human**. Human activity follows a **heavy-tailed, bursty Poisson process** with natural diurnal (circadian) sleep rhythms:
   - Humans sleep for 6–8 hours daily (a distinct daily lull in activity).
   - Humans do 3–5 rapid transactions while using a dApp, then disappear for 3 days.
   - Bots transact 24 hours a day, 7 days a week, evenly distributed across the clock.
3. **The Math:** Calculate the **Shannon Entropy** of inter-arrival times $\Delta t$:
   $$H(X) = -\sum P(x) \log_2 P(x)$$
   Combine this with a **Diurnal Activity Score** (measuring variance across 24 hourly bins in UTC). A wallet with uniform 24-hour activity and abnormal timing entropy is flagged as an automated daemon.

#### 🛠️ Implementation Plan:
- **Files to create:** `core-engine/filters/entropy_clock.py`.
- **Inputs:** Array of transaction timestamps for a wallet.
- **Outputs:** `entropy_score` (0–100) and `diurnal_score` (0–100).

#### ✅ Definition of Done:
- [ ] Correctly identifies 24-hour bot scripts vs organic human day-night sleep cycles.
- [ ] Integrates as an optional corroborating signal into `scorer.py`.
- [ ] Unit tests pass in `tests/test_entropy_clock.py`.

---

### Issue #17: Interactive PyVis Graph Topology Visualizer
- **Assignee:** **Chirag Janbandhu (CDO)**
- **Target Deadline:** **December 4, 2026** (11 days | ~10 hours focused effort)
- **Labels:** `report-generator`, `visualization`, `frontend`

#### 🧠 Think First (Theory & Design Choices):
1. **Why Graph Visuals Sell:** Protocols and community members struggle to understand mathematical modularity numbers. When they can physically see an interactive, drag-and-drop star graph showing 42 red bot nodes revolving around 1 yellow master hub, the evidence is indisputable.
2. **Library:** Use `pyvis.network.Network` to generate an embeddable, standalone HTML/JS canvas widget with physics simulation (ForceAtlas2 or Barnes-Hut).

#### 🛠️ Implementation Plan:
- **Files to create:** `report-generator/visualizer.py`.
- **Inputs:** NetworkX graph and cartel cluster dictionary.
- **Outputs:** Standalone interactive HTML file + embeddable iframe in `launch_audit_report.html`.

#### ✅ Definition of Done:
- [ ] Generates interactive WebGL/Canvas network visualization of detected bot cartels.
- [ ] Colors nodes by verdict (Red = Disqualified Cartel, Green = Organic, Yellow = Master Hub).
- [ ] Hover tooltips show wallet address, risk score, and transaction volume.
- [ ] Embedded seamlessly into the official audit report.

---

### Issue #13: Bounded-Universe Sandbox Filter (Ecosystem Leakage)
- **Assignee:** **Laukik Wani (CTO)**
- **Target Deadline:** **December 7, 2026** (14 days | ~12 hours focused effort)
- **Labels:** `core-engine`, `heuristics`, `behavioral`

#### 🧠 Think First (Theory & Design Choices):
1. **The Concept of Ecosystem Leakage:** Real crypto users live on the blockchain—they trade meme coins on Uniswap, mint free NFTs, register ENS names, and claim small gaming tokens.
2. **The Bot Cartel Profile:** Automated farming wallets are strictly optimized for gas efficiency. Their entire transaction history is confined to the **exact 2 or 3 contracts** required to qualify for the target airdrop.
3. **The Heuristic:** Measures the ratio of non-airdrop contract interactions vs qualification task interactions:
   $$\text{Leakage Ratio} = \frac{|\text{General Ecosystem Contracts}|}{|\text{Target Protocol Contracts}|}$$
   A leakage ratio of $0.0$ across 50 wallets indicates a single-purpose automated farming syndicate.

#### 🛠️ Implementation Plan:
- **Files to create:** `core-engine/filters/universe_sandbox.py`.
- **Inputs:** Wallet contract interaction sets.
- **Outputs:** `leakage_ratio` and confidence flag.

#### ✅ Definition of Done:
- [ ] Flags wallets with zero background ecosystem activity.
- [ ] Protects real power users with diverse on-chain histories.
- [ ] Unit tests pass in `tests/test_universe_sandbox.py`.

---

### Issue #19: Competitive Matrix & Launch Pricing Test
- **Assignee:** **Vinit (CPO)**
- **Target Deadline:** **December 7, 2026** (14 days | ~8 hours focused effort)
- **Labels:** `product`, `market-intelligence`, `commercial`

#### 🧠 Think First:
1. Maintain active competitive tracking on Trusta Labs (TrustScan), Chaos Labs, Nansen, and Gitcoin Passport.
2. Formulate the "Aegis3 Battlecard": When a protocol asks *"Why should we use Aegis3 instead of Trusta Labs?"*, what are our 3 clear, unarguable advantages? (e.g. 100% explainable graph math vs black-box AI; cryptographic SHA-256 evidence seals; B2B tailored war room vs generic API).

#### ✅ Definition of Done:
- [ ] Complete `Docs/COMPETITIVE_BATTLECARD.md`.
- [ ] Test standard vs enterprise launch package pricing with 3 protocol decision-makers.

---

# 🌐 SPRINT 4 (Weeks 7–8: Dec 8 – Dec 22, 2026)

---

### Issue #10: FastAPI REST Scoring & Verification Endpoint
- **Assignee:** **Laukik Wani (CTO)**
- **Target Deadline:** **December 16, 2026** (8 days | ~14 hours focused effort)
- **Labels:** `api`, `backend`, `infrastructure`

#### 🧠 Think First:
- During a token launch, `claim.protocol.xyz` can experience tens of thousands of requests per second. The scoring endpoint must not run the full graph algorithm on every request!
- Pre-compute all scored allocations and Merkle proofs during the audit phase, store them in Redis or a fast SQLite/PostgreSQL key-value cache, and serve individual wallet queries in $< 15\text{ms}$.

#### 🛠️ Implementation Plan:
- **Files to create:** `api/server.py`, `api/schemas.py`, `api/config.py`.
- **Endpoints:**
  - `GET /health` -> Service health check.
  - `GET /api/v1/score/{wallet_address}` -> Returns 0–100 score, tier, and evidence trail.
  - `GET /api/v1/merkle-proof/{wallet_address}` -> Returns cryptographic proof for claim contract.

#### ✅ Definition of Done:
- [ ] FastAPI service with sub-20ms response time on cached lookups.
- [ ] OpenAPI docs generated automatically at `/docs`.
- [ ] Unit and load tests pass in `tests/test_api.py`.

---

### Issue #11: React Verified Claim-Gate Component (SDK)
- **Assignee:** **Chirag Janbandhu (CDO)**
- **Target Deadline:** **December 20, 2026** (12 days | ~16 hours focused effort)
- **Labels:** `claim-sdk`, `frontend`, `react`, `web3`

#### 🧠 Think First:
- Protocols embed this component into their React/Next.js claim portal (`claim.protocol.xyz`).
- Must support standard EVM wallet connection (Wagmi / viem / ethers.js).
- If the connected wallet is flagged, it renders an unarguable **Evidence Drawer** showing the exact transaction hash, cartel ID, and CEX deposit link so users know why they were disqualified and cannot spam Discord.

#### 🛠️ Implementation Plan:
- **Files to create:** `claim-sdk/src/ClaimGate.tsx`, `claim-sdk/src/EvidenceCard.tsx`, `claim-sdk/package.json`.

#### ✅ Definition of Done:
- [ ] Lightweight React component with Tailwind / CSS modules styling.
- [ ] Integrates with `api/server.py` to query eligibility and Merkle proof.
- [ ] Verified in a demo Next.js application.

---

### Issue #18: Protocol Launch Operations & Appeal Playbook
- **Assignee:** **Vinit (CPO)**
- **Target Deadline:** **December 22, 2026** (14 days | ~12 hours focused effort)
- **Labels:** `product`, `operations`, `governance`

#### 🧠 Think First:
- Even with deterministic proof, 1%–2% of disqualified users will appeal. Having a transparent, published 72-hour appeal window (like LayerZero did) gives the protocol foundation absolute moral and PR high ground.

#### ✅ Definition of Done:
- [ ] Write `Docs/LAUNCH_OPERATIONS_PLAYBOOK.md` detailing:
  1. Timeline: T-30 days data snapshot to T-0 launch day.
  2. The 72-hour community appeal and bounty hunter workflow.
  3. Foundation communication templates for Twitter/X announcements.
