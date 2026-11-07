# Aegis3

Enterprise token launch integrity and Sybil defense for Web3 protocol foundations.

Aegis3 helps protocol teams run fair, defensible token distributions by detecting coordinated bot cartels in candidate wallet lists and producing auditable, explainable evidence that can be published to the community without PR backlash.

---

## What This Repository Contains

```
Aegis3/
├── core-engine/                 The detection brain
│   ├── graph_builder.py         Ingests wallets and transfer edges into a directed NetworkX graph
│   ├── temporal_weights.py      [Active] Exponential decay and synchronized batch burst weighting
│   ├── filters/
│   │   ├── louvain_cluster.py   Community partitioning (groups tightly linked wallets)
│   │   ├── jaccard_dna.py       Behavioral sequence similarity (catches scripted contract calls)
│   │   ├── cex_tracer.py        [Active] CEX deposit address convergence tracer (100% deterministic)
│   │   ├── pre_filter.py        [Sprint 2] Weakly connected component graph pre-filter
│   │   ├── entropy_clock.py     [Sprint 3] Population interval entropy and diurnal rhythm analysis
│   │   └── universe_sandbox.py  [Sprint 3] Bounded-universe ecosystem leakage filter
│   └── scorer.py                Aggregates signals into 0-100 risk scores with tiered verdicts
│
├── data-pipeline/               Data sourcing, validation, and extraction
│   ├── normalizer.py            [Active] Strict EIP-55 address sanitizer & anti-framing dust shield
│   ├── candidate_cli.py         [Active] End-to-end candidate ingestion & trace payload CLI
│   ├── extractors/
│   │   ├── etherscan_client.py  [Active] Multi-chain explorer client (ETH, Arb, Polygon, Base, OP) with cache
│   │   └── fingerprint_extractor.py [Active] Behavioral fingerprint, gas funder & contract set parser
│   ├── sql/                     Dune Analytics queries for historical airdrop data
│   ├── datasets/                Ground-truth CSVs (LayerZero verified Sybils)
│   └── curator.py               [Sprint 2] 5k bot vs 5k human benchmarking dataset curator
│
├── report-generator/            Client-facing governance deliverables
│   ├── generate_report.py       Produces branded HTML audit reports with signal breakdowns
│   ├── evidence_hasher.py       [Active] Cryptographic SHA-256 evidence integrity hasher & manifest verifier
│   └── pdf_exporter.py          [Sprint 2] Executive PDF export utility with cryptographic seal
│
├── claim-sdk/                   [Sprint 4] Embeddable React claim verification widget
├── api/                         [Sprint 4] FastAPI REST scoring service for live claims
├── Extension/                   Chrome MV3 transaction interceptor prototype
├── notebooks/                   Research notebooks (EDA, benchmarks, visualizations)
├── tests/                       Automated regression & heuristic test suite
│   ├── test_normalizer.py       Validates EIP-55 sanitization and dust-framing defense
│   ├── test_cex_tracer.py       Validates CEX deposit convergence clustering & router pruning
│   ├── test_evidence_hasher.py  Validates SHA-256 manifest generation & tamper detection
│   ├── test_ingestion_pipeline.py Validates explorer scraping, caching & fingerprinting
│   ├── test_temporal_weights.py Validates exponential decay & synchronized batch bursts
│   └── test_benchmark.py        [Sprint 2] Full precision/recall regression benchmark
│
├── Docs/                        Architecture blueprints, grant guides, pitch materials
│   ├── PROJECT_CONTEXT.md       Master engineering blueprint & commercial thesis
│   ├── SECURITY_ISSUES.md       Production security issue specifications (Issues #14 & #15)
│   └── GITHUB_ISSUES_BACKLOG.md Comprehensive task backlog with realistic thinking & coding timelines
│
└── run_audit.py                 Master CLI: runs the full multi-signal pipeline end-to-end
```

---

## System Architecture

The pipeline operates across five distinct phases, moving from raw on-chain data to final cryptographic governance deliverables.

```
                          AEGIS3 DETECTION PIPELINE
                          -------------------------

  [1] INGEST              [2] BUILD              [3] DETECT (Multi-Signal)
  Candidate wallet     -> Directed graph      -> • Louvain Partitioning (Topology)
  list (CSV/JSON)         with temporal edges    • Jaccard DNA (Contract Overlap)
  + live traces from      pruned of exchange     • CEX Deposit Convergence (Cash-out)
  Etherscan/RPC           mega-hubs              • Population Entropy (Timing RNG)
                                                 • Bounded Universe (Activity Leakage)

       |                       |                               |
       v                       v                               v

  normalizer.py          graph_builder.py              louvain_cluster.py
  etherscan_client.py    temporal_weights.py           jaccard_dna.py
  fingerprint_extractor.py                             cex_tracer.py
  candidate_cli.py                                     entropy_clock.py
                                                       universe_sandbox.py

                                                               |
                                                               v

                        [4] SCORE                      [5] REPORT
                        Aggregate signals           -> Generate HTML/PDF
                        into 0-100 risk                audit report with
                        scores and assign              SHA-256 evidence
                        tiered verdicts                integrity manifests

                             |                              |
                             v                              v

                         scorer.py                    generate_report.py
                                                      pdf_exporter.py
                                                      evidence_hasher.py
```

---

## How Detection Works (No Machine Learning)

We do not use neural networks, deep learning, or LLMs to detect Sybils. The reasons are practical, not ideological:

1. **No Ground-Truth Supervised Training:** The pseudonymous nature of blockchains means no universal, clean dataset of "human vs bot" exists. Supervised models trained on noisy labels will produce noisy predictions.
2. **Explainability Requirement:** Protocols need to publicly justify every disqualification. A model that says "87.4% probability of being a bot" based on latent embeddings will get torn apart on Twitter. Deterministic graph evidence (*"these 42 wallets were funded by the same address within 3 minutes and cashed out to Binance deposit 0x123..."*) cannot be argued with.
3. **Computational Efficiency:** Mathematical graph algorithms and set theory run in linear or near-linear time without requiring expensive GPU inference clusters.

### The Multi-Signal Defense Suite:
- **Hub-Pruned Louvain Community Detection:** Identifies dense subgraphs of wallets that transact heavily with each other but rarely with the rest of the network. Prunes public exchange hot wallets and DEX routers to prevent false topological bridges.
- **Jaccard Behavioral DNA:** Compares the set of smart contracts each wallet has interacted with. Wallets that share $\ge 85\%$ of their contract interaction history are running identical automated scripts.
- **CEX Deposit Address Convergence:** Traces downstream cash-out transactions to personal centralized exchange deposit addresses. Multiple wallets depositing into the exact same exchange deposit address share identical legal/individual ownership (100% precision, zero false positives).
- **Temporal Burst & Decay Weighting:** Applies exponential decay kernels to transaction edges. Distributions executed within a 15-minute automated loop receive a $3\times$ to $8\times$ weight boost; ancient historical transfers decay toward a floor.
- **Population Interval Entropy & Diurnal Rhythm:** Evaluates whether transaction inter-arrival times follow natural human bursty Poisson processes and human sleep-wake cycles, catching attackers who attempt to randomize timers.
- **Bounded-Universe Sandbox Detection:** Measures ecosystem leakage. Real users interact with diverse protocols across the chain (meme coins, gaming, governance), whereas automated cartels confine activity strictly within token qualification tasks.

---

## Sprint Roadmap & Issue Assignment

> **Pacing Principle:** Deadlines are structured with realistic engineering buffers (8–15 focused hours per issue spread across 7–10 days). Each issue includes dedicated "Think First" architecture time before writing code.

```
SPRINT 1 (COMPLETED): DATA FOUNDATION & CORE HEURISTICS
-------------------------------------------------------
[#14 Input Normalizer & Anti-Framing Shield] (Chirag)        --> [COMPLETED]
[#4 Etherscan Multi-Chain Client] (Chirag)                   --> [COMPLETED]
[#5 Behavioral Fingerprint Extractor] (Chirag)               --> [COMPLETED]
[#6 Candidate Ingestion CLI] (Chirag)                        --> [COMPLETED]
[#1 CEX Deposit Address Convergence Tracer] (Laukik)         --> [COMPLETED]
[#2 Temporal Decay & Synchronized Burst Weights] (Laukik)    --> [COMPLETED]
[#7 SHA-256 Cryptographic Evidence Hasher] (Chirag/Laukik)   --> [COMPLETED]


SPRINT 2 (WEEKS 3-4: NOV 8 - NOV 22, 2026): PERFORMANCE & GOVERNANCE ARTIFACTS
-------------------------------------------------------------------------------
[#3 Connected Component Pre-Filter] (Laukik)        Target: Nov 15, 2026 (~10h)
       |
[#8 Executive PDF Audit Report Export] (Chirag)     Target: Nov 18, 2026 (~14h)
       |
[#16 Ground-Truth Dataset Curator (5k/5k)] (Chirag) Target: Nov 20, 2026 (~8h)
       |
[#9 Automated Precision/Recall Benchmark] (Laukik)  Target: Nov 22, 2026 (~12h)
       |
[#20 Protocol Founder Discovery Calls] (Vinit)      Target: Nov 22, 2026 (5 calls)


SPRINT 3 (WEEKS 5-6: NOV 23 - DEC 7, 2026): ADVANCED ANTI-EVASION & VISUALIZATION
---------------------------------------------------------------------------------
[#12 Population Entropy & Diurnal Clock] (Laukik)   Target: Dec 1, 2026  (~15h)
       |
[#17 Interactive PyVis Topology Visualizer] (Chirag)Target: Dec 4, 2026  (~10h)
       |
[#13 Bounded-Universe Sandbox Filter] (Laukik)      Target: Dec 7, 2026  (~12h)
       |
[#19 Competitive Intelligence & Pricing Test] (Vinit)Target: Dec 7, 2026 (10 reviews)


SPRINT 4 (WEEKS 7-8: DEC 8 - DEC 22, 2026): CLAIM-GATE & COMMERCIAL DEPLOYMENT
-------------------------------------------------------------------------------
[#10 FastAPI REST Scoring Endpoint] (Laukik)        Target: Dec 16, 2026 (~14h)
       |
[#11 React Verified Claim-Gate Component] (Chirag)  Target: Dec 20, 2026 (~16h)
       |
[#18 Protocol Launch Operations Playbook] (Vinit)   Target: Dec 22, 2026 (~12h)
```

---

## Current State (What Works Today)

- **Input Normalizer & Anti-Framing Shield:** Validates EIP-55 address formatting, deduplicates case-insensitively, and strips $<0.0005$ ETH dust transfers defending against Sybil framing attacks.
- **Multi-Chain Explorer Scraper:** Fetches normal and ERC-20 transaction logs from Ethereum, Arbitrum, Base, Optimism, and Polygon with disk caching and rate-limiting.
- **Behavioral Fingerprint Extractor:** Parses on-chain traces into gas funder edges, smart contract call sets (DNA), and cash-out destinations.
- **Candidate Ingestion CLI:** `candidate_cli.py` ingests any raw protocol CSV/TXT list and outputs clean pipeline payloads.
- **CEX Deposit Tracer:** Identifies shared personal exchange deposit addresses (100% deterministic cash-out cartel detection) and prunes public DEX pools/routers.
- **Temporal Burst Weighting:** Applies exponential decay kernels and batch burst multipliers ($3\times$ to $8\times$) to synchronized automated funding loops.
- **Louvain Community Partitioning:** Isolates dense bot cartels after hub pruning (validated with 100% precision on LayerZero data).
- **Jaccard Behavioral DNA:** Detects scripted clones sharing $\ge 85\%$ contract call history.
- **Multi-Signal Scorer:** Aggregates graph topology (40%), Jaccard DNA (30%), and CEX convergence (30%) into 0–100 risk scores with tiered verdicts.
- **Cryptographic Hasher:** Computes SHA-256 content-addressed `audit_manifest.json` sealing raw inputs and final reports against insider tampering.
- **Institutional HTML Report:** Generates branded, dark-mode governance audit reports with evidence tables.
- **Master Pipeline CLI:** `run_audit.py` ties the full multi-signal pipeline together.
- **Automated Test Suite:** 5 passing test suites covering all core modules (`tests/`).

---

## Local Development Setup

```powershell
git clone https://github.com/coder-hub-l/Aegis3.git
cd Aegis3
python -m venv .venv

# Windows PowerShell:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

# Linux/Mac:
# source .venv/bin/activate

pip install --upgrade pip
pip install networkx python-louvain pandas matplotlib scikit-learn ipykernel

# Run the test suite:
python tests/test_normalizer.py
python tests/test_cex_tracer.py
python tests/test_evidence_hasher.py
python tests/test_ingestion_pipeline.py
python tests/test_temporal_weights.py

# Run the full audit pipeline:
python run_audit.py
```

Output is written to `Docs/launch_audit_report.html` and `Docs/scored_allocations.csv`.

---

## Team & Leadership

| Person | Role | Core Ownership |
| :--- | :--- | :--- |
| **Laukik Wani** | CTO, Systems and Security | Core detection engine (`core-engine/`), graph algorithms, temporal & entropy heuristics, API architecture (`api/`), benchmarking (`tests/`) |
| **Chirag Janbandhu** | CDO, Data Operations | On-chain data sourcing (`data-pipeline/`), explorer clients, normalizers, report generator & PDF exporter (`report-generator/`), claim SDK frontend (`claim-sdk/`) |
| **Vinit** | CPO, Product Management | Protocol discovery interviews, partner outreach, pricing validation, competitive intelligence, launch operations playbook |
