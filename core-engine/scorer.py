"""
Aegis3 Core Engine - Risk Scorer
Aggregates graph topology metrics, Louvain clustering, Jaccard sequence similarity,
and CEX deposit convergence to produce a deterministic 0-100 Risk Score and Tiered Allocation classification.
"""

from typing import Dict, List, Optional
import pandas as pd

class SybilRiskScorer:
    def __init__(self):
        # Weights for multi-signal aggregation
        self.W_GRAPH = 0.40     # Weight for Louvain cluster density / star-funder links
        self.W_JACCARD = 0.30   # Weight for behavioral sequence duplication
        self.W_CEX = 0.30       # Weight for CEX deposit convergence (hard proof)

    def score_wallets(self, 
                      wallets: List[str], 
                      cartel_clusters: List[Dict], 
                      jaccard_clusters: List[Dict],
                      cex_clusters: Optional[List[Dict]] = None) -> pd.DataFrame:
        """
        Calculates a deterministic 0-100 Sybil Risk Score for every candidate wallet.
        """
        results = []
        cex_clusters = cex_clusters or []

        # Index memberships for O(1) lookups
        cartel_membership = {}
        for c in cartel_clusters:
            for w in c.get("members", []):
                cartel_membership[str(w).lower().strip()] = c

        jaccard_membership = {}
        for j in jaccard_clusters:
            for w in j.get("wallets", []):
                jaccard_membership[str(w).lower().strip()] = j

        cex_membership = {}
        for x in cex_clusters:
            for w in x.get("wallets", []):
                cex_membership[str(w).lower().strip()] = x

        for w in wallets:
            w_lower = str(w).lower().strip()
            
            # 1. Graph signal (0 - 100)
            graph_score = 0
            if w_lower in cartel_membership:
                cluster_size = cartel_membership[w_lower].get("size", 0)
                # Larger cluster = higher confidence of industrial coordination
                graph_score = min(100, 40 + (cluster_size * 2))

            # 2. Jaccard behavioral DNA signal (0 - 100)
            jaccard_score = 0
            if w_lower in jaccard_membership:
                j_size = jaccard_membership[w_lower].get("cluster_size", 0)
                jaccard_score = min(100, 50 + (j_size * 3))

            # 3. CEX Deposit convergence signal (0 - 100)
            cex_score = 0
            if w_lower in cex_membership:
                cex_info = cex_membership[w_lower]
                cex_score = cex_info.get("confidence_score", 85)

            # Combined Weighted Score
            total_score = int(round(
                (graph_score * self.W_GRAPH) + 
                (jaccard_score * self.W_JACCARD) + 
                (cex_score * self.W_CEX)
            ))

            # CEX convergence is a hard deterministic proof: ensure it crosses into Tier 3
            if cex_score >= 85 and total_score < 70:
                total_score = max(total_score, 75)

            # Classification Tier:
            if total_score >= 70:
                tier = "Tier 3: Sybil Bot Cartel (Disqualified)"
                verdict = "DISQUALIFY"
            elif total_score >= 35:
                tier = "Tier 2: Suspicious Activity (Under Review)"
                verdict = "MANUAL_REVIEW"
            else:
                tier = "Tier 1: Authentic Human (Eligible)"
                verdict = "ELIGIBLE"

            results.append({
                "wallet_address": w,
                "sybil_risk_score": total_score,
                "tier": tier,
                "recommended_verdict": verdict,
                "graph_signal": graph_score,
                "jaccard_signal": jaccard_score,
                "cex_signal": cex_score
            })

        df = pd.DataFrame(results)
        df.sort_values(by="sybil_risk_score", ascending=False, inplace=True)
        return df
