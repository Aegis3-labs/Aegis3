"""
Aegis3 Core Engine - Centralized Exchange (CEX) Deposit Address Convergence Tracer
Detects downstream cash-out and funding convergence to shared personal deposit addresses.
Personal CEX deposit addresses provide deterministic proof of unified wallet ownership.
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict


class CEXDepositTracer:
    """
    Identifies bot cartels by tracing transactions from candidate wallets to shared
    downstream deposit addresses (e.g., Binance, OKX, Bybit personal deposit addresses).
    """

    def __init__(
        self,
        min_convergence_wallets: int = 2,
        max_deposit_degree: int = 150,
        known_public_addresses: Optional[Set[str]] = None,
    ):
        """
        :param min_convergence_wallets: Minimum number of unique candidate wallets sending to the
                                        same deposit address to flag as a shared cash-out cartel.
        :param max_deposit_degree: Maximum incoming transactions before an address is deemed a
                                   public router, bridge, or pool rather than a personal deposit address.
        :param known_public_addresses: Set of known contract addresses (Uniswap router, bridges) to ignore.
        """
        self.min_convergence = min_convergence_wallets
        self.max_deposit_degree = max_deposit_degree
        self.known_public_addresses = {
            addr.lower().strip() for addr in (known_public_addresses or set())
        }

    def find_converging_clusters(
        self, transfers: List[Tuple[str, str, float]]
    ) -> List[Dict]:
        """
        Analyzes a list of transfers and identifies converging deposit addresses.

        :param transfers: List of (sender_wallet, destination_address, value_eth/tokens)
        :return: List of detected convergence cartel clusters with metadata.
        """
        # Map: destination_address -> set of unique senders & transfer details
        destination_senders = defaultdict(set)
        destination_volume = defaultdict(float)
        destination_tx_count = defaultdict(int)

        for sender, destination, value in transfers:
            s = str(sender).lower().strip()
            d = str(destination).lower().strip()
            val = float(value) if value is not None else 0.0

            destination_senders[d].add(s)
            destination_volume[d] += val
            destination_tx_count[d] += 1

        clusters = []
        for dest, senders in destination_senders.items():
            # 1. Skip known public infrastructure (routers, AMMs)
            if dest in self.known_public_addresses:
                continue

            # 2. Skip mega-destinations exceeding degree threshold (likely liquidity pools/bridges)
            total_txs = destination_tx_count[dest]
            if total_txs > self.max_deposit_degree:
                continue

            # 3. Check if multiple candidate wallets converged on this address
            unique_wallet_count = len(senders)
            if unique_wallet_count >= self.min_convergence:
                # 2 wallets = 85% confidence, 3+ wallets = 100% deterministic certainty
                confidence = 100 if unique_wallet_count >= 3 else 85

                clusters.append(
                    {
                        "deposit_address": dest,
                        "cluster_size": unique_wallet_count,
                        "wallets": sorted(list(senders)),
                        "total_volume": round(destination_volume[dest], 4),
                        "transaction_count": total_txs,
                        "confidence_score": confidence,
                    }
                )

        # Sort clusters by size (largest cartels first)
        clusters.sort(key=lambda x: (x["cluster_size"], x["total_volume"]), reverse=True)
        print(
            f"[CEXDepositTracer] Identified {len(clusters)} shared deposit convergence clusters "
            f"(>= {self.min_convergence} converging wallets)."
        )
        return clusters

    @staticmethod
    def get_wallet_convergence_map(clusters: List[Dict]) -> Dict[str, Dict]:
        """
        Creates an O(1) lookup dictionary mapping wallet_address -> cluster metadata.
        """
        wallet_map = {}
        for cluster in clusters:
            for wallet in cluster["wallets"]:
                # If wallet appears in multiple, preserve the highest confidence cluster
                if wallet not in wallet_map or cluster["confidence_score"] > wallet_map[wallet]["confidence_score"]:
                    wallet_map[wallet] = cluster
        return wallet_map
