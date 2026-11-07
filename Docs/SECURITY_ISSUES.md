# Aegis3 — Security Pipeline GitHub Issues

Copy and paste these directly into [GitHub Issues](https://github.com/Aegis3-labs/Aegis3/issues/new).

---

## 📌 Issue #14: `feat(pipeline): Input Sanitizer, EIP-55 Checksummer & Anti-Framing Shield`

**Title:** `[Security] Secure Candidate List Normalizer, EIP-55 Checksum & Anti-Poisoning Filter`

**Labels:** `security`, `pipeline`, `high-priority`

### Description:
Raw candidate wallet lists submitted by protocols contain malformed strings, duplicate addresses, casing inconsistencies, and potential poison-pill inputs. Furthermore, malicious bot syndicates can attempt **"Sybil Framing" attacks**—sending 0.0001 ETH to innocent community power users to falsely link them to a cartel. 

We need a production-grade input normalizer and sanitization pipeline that runs before any graph construction.

### Threat Model Defended:
1. **Malicious / Corrupt Input Injection:** Invalid hex strings, null bytes, non-EVM addresses, or CSV injection payloads that could crash downstream NetworkX or ClickHouse pipelines.
2. **Sybil Framing Attacks:** Attackers sending microscopic dust amounts to taint legitimate protocol contributors.
3. **Double-Allocation Multi-Accounting:** Case-sensitivity bypasses (e.g. `0xABC...` vs `0xabc...`) extracting duplicate allocations.

### Acceptance Criteria:
- [ ] Validates 40-character hex EVM addresses and supports EIP-55 checksum verification.
- [ ] Canonicalizes all addresses to lowercase for consistent graph node hashing.
- [ ] Discards dust taint transactions below configurable threshold (default: `< 0.0005 ETH`).
- [ ] Deduplicates address inputs while preserving first-seen ingestion order and metadata.
- [ ] Produces a structured sanitization report: total ingested, valid addresses, dropped malformed rows, and deduplicated duplicates.
- [ ] Exports clean sanitized CSV and rejected entries log for protocol transparency.

---

## 📌 Issue #15: `feat(security): Cryptographic Evidence Hasher & Tamper-Proof Manifest`

**Title:** `[Security] SHA-256 Content-Addressed Hash Manifest & Evidence Integrity Verifier`

**Labels:** `security`, `cryptography`, `governance`

### Description:
A major failure mode in high-stakes token airdrops is **insider tampering and post-audit dispute**. If an insider alters a single row in an audit CSV to whitelist a bot, or if a disqualified farmer claims the protocol faked the audit results, the team has no cryptographic way to prove the audit hasn't been modified.

We need an automated cryptographic evidence hasher that generates an immutable, content-addressed SHA-256 manifest across every pipeline stage.

### Threat Model Defended:
1. **Insider Bribery / Tampering:** Silently modifying scores or verdicts in the output database.
2. **Post-TGE Legal & PR Disputes:** Community claims that disqualified addresses were selectively targeted.
3. **Transit Corruption:** Mismatched files between local audit generation and protocol foundation handoff.

### Acceptance Criteria:
- [ ] Generates SHA-256 digest of raw input candidate list.
- [ ] Generates SHA-256 digest of constructed graph edges.
- [ ] Generates SHA-256 digest of final `scored_allocations.csv`.
- [ ] Generates SHA-256 digest of published `launch_audit_report.html`.
- [ ] Compiles a signed/structured `audit_manifest.json` binding all artifacts with timestamp, engine version, and root integrity hash.
- [ ] Provides a CLI verification command `verify_manifest()` that verifies artifact integrity in <1 second.
