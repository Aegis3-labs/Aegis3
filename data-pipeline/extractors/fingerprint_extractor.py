"""
Aegis3 Data Pipeline - Wallet Behavioral Fingerprint Extractor
Transforms raw transaction lists into structured graph edges,
smart contract call sets (DNA), and cash-out destination addresses.
"""

from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class WalletFingerprint:
    """Structured behavioral and topological profile of a candidate wallet."""
    wallet_address: str
    initial_funder: Optional[str] = None
    initial_funding_value_eth: float = 0.0
    initial_funding_timestamp: int = 0
    contracts_called: List[str] = field(default_factory=list)
    outbound_destinations: List[Tuple[str, float]] = field(default_factory=list)
    all_transfers: List[Tuple[str, str, float]] = field(default_factory=list)
    total_tx_count: int = 0
    first_seen_timestamp: int = 0
    last_seen_timestamp: int = 0


class FingerprintExtractor:
    """
    Parses on-chain transaction logs and produces behavioral footprints
    ready for GraphBuilder, Louvain clustering, Jaccard DNA, and CEX deposit tracing.
    """

    def __init__(self, min_dust_threshold: float = 0.0005):
        self.min_dust_threshold = min_dust_threshold

    def extract_fingerprint(
        self,
        wallet_address: str,
        normal_txs: List[Dict],
        token_txs: Optional[List[Dict]] = None
    ) -> WalletFingerprint:
        """
        Extracts topological and behavioral signals from transaction arrays.

        :param wallet_address: The candidate address being analyzed.
        :param normal_txs: External native transactions (Etherscan txlist).
        :param token_txs: ERC-20 token transactions (Etherscan tokentx).
        :return: Populated WalletFingerprint.
        """
        w = wallet_address.lower().strip()
        fingerprint = WalletFingerprint(wallet_address=w)

        if not normal_txs and not token_txs:
            return fingerprint

        # Sort transactions chronologically
        sorted_txs = sorted(
            normal_txs or [],
            key=lambda x: int(x.get("timeStamp", 0))
        )

        contracts_seen: Set[str] = set()
        outbound_destinations = []
        all_transfers = []

        initial_funder_found = False

        for tx in sorted_txs:
            sender = str(tx.get("from", "")).lower().strip()
            recipient = str(tx.get("to", "")).lower().strip()
            input_data = str(tx.get("input", "0x")).lower()
            timestamp = int(tx.get("timeStamp", 0))

            # Convert wei to ETH
            try:
                val_wei = int(tx.get("value", 0))
                val_eth = val_wei / 1e18
            except (ValueError, TypeError):
                val_eth = 0.0

            # 1. Identify the Initial Gas Funder (Chronologically earliest inbound transfer)
            if recipient == w and sender != w and not initial_funder_found:
                if val_eth >= self.min_dust_threshold:
                    fingerprint.initial_funder = sender
                    fingerprint.initial_funding_value_eth = round(val_eth, 6)
                    fingerprint.initial_funding_timestamp = timestamp
                    initial_funder_found = True
                    all_transfers.append((sender, w, val_eth))

            # 2. Identify Smart Contract Interactions (input != '0x' or contract creation)
            if sender == w and recipient:
                # If there is call data (input != '0x'), the recipient is a smart contract
                if input_data != "0x" and len(input_data) > 2:
                    contracts_seen.add(recipient)

            # 3. Identify Outbound Transfers & Consolidations (potential CEX or parent sweeps)
            if sender == w and recipient and recipient != w:
                if val_eth >= self.min_dust_threshold:
                    outbound_destinations.append((recipient, val_eth))
                    all_transfers.append((w, recipient, val_eth))

        # Ingest ERC-20 Token Transactions for downstream cash-out detection
        for ttx in (token_txs or []):
            sender = str(ttx.get("from", "")).lower().strip()
            recipient = str(ttx.get("to", "")).lower().strip()

            if sender == w and recipient and recipient != w:
                # Store token transfer edge with mock normalization
                outbound_destinations.append((recipient, 1.0))
                all_transfers.append((w, recipient, 1.0))

        fingerprint.contracts_called = sorted(list(contracts_seen))
        fingerprint.outbound_destinations = outbound_destinations
        fingerprint.all_transfers = all_transfers
        fingerprint.total_tx_count = len(sorted_txs)

        if sorted_txs:
            fingerprint.first_seen_timestamp = int(sorted_txs[0].get("timeStamp", 0))
            fingerprint.last_seen_timestamp = int(sorted_txs[-1].get("timeStamp", 0))

        return fingerprint
