"""
Aegis3 Data Pipeline - Secure Input Normalizer & Anti-Poisoning Shield
Validates, deduplicates, and sanitizes candidate wallet lists.
Filters out dust transactions used in Sybil Framing attacks.
"""

import re
import os
import sys
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass, field


# Strict 42-character EVM address regex (0x + 40 hex digits)
EVM_ADDRESS_REGEX = re.compile(r"^0x[0-9a-fA-F]{40}$")


@dataclass
class SanitizationReport:
    """Summary of the sanitization and validation run."""
    total_ingested: int = 0
    valid_count: int = 0
    rejected_count: int = 0
    duplicate_count: int = 0
    valid_wallets: List[str] = field(default_factory=list)
    rejected_entries: List[Dict[str, str]] = field(default_factory=list)

    @property
    def valid_percentage(self) -> float:
        return (self.valid_count / self.total_ingested * 100) if self.total_ingested > 0 else 0.0


class WalletListNormalizer:
    """
    Production-grade input sanitization and anti-framing shield for EVM candidate lists.
    """

    def __init__(self, min_transfer_eth: float = 0.0005):
        """
        :param min_transfer_eth: Threshold below which transfers are classified as
                                 malicious dust/framing noise and excluded from the graph.
        """
        self.min_transfer_eth = min_transfer_eth

    @staticmethod
    def is_valid_evm_address(address: Any) -> bool:
        """
        Checks if the provided input is a valid 42-character EVM hexadecimal address.
        """
        if not address or not isinstance(address, str):
            return False
        cleaned = address.strip()
        return bool(EVM_ADDRESS_REGEX.match(cleaned))

    def sanitize_wallets(self, raw_wallets: List[Any]) -> SanitizationReport:
        """
        Validates, canonicalizes, and deduplicates a raw list of wallet addresses.

        :param raw_wallets: List of candidate wallet strings.
        :return: SanitizationReport containing clean unique addresses and rejected logs.
        """
        report = SanitizationReport(total_ingested=len(raw_wallets))
        seen_wallets: Set[str] = set()

        for idx, item in enumerate(raw_wallets):
            if item is None:
                report.rejected_entries.append({
                    "index": idx,
                    "raw_value": "None",
                    "reason": "NULL_VALUE"
                })
                report.rejected_count += 1
                continue

            addr_str = str(item).strip()

            # 1. Format & Hex Character Check
            if not self.is_valid_evm_address(addr_str):
                report.rejected_entries.append({
                    "index": idx,
                    "raw_value": addr_str[:20] + "..." if len(addr_str) > 20 else addr_str,
                    "reason": "INVALID_EVM_FORMAT"
                })
                report.rejected_count += 1
                continue

            # 2. Canonicalization to lowercase
            canonical = addr_str.lower()

            # 3. Deduplication Check
            if canonical in seen_wallets:
                report.duplicate_count += 1
                report.rejected_entries.append({
                    "index": idx,
                    "raw_value": addr_str,
                    "reason": "DUPLICATE_ENTRY"
                })
                continue

            seen_wallets.add(canonical)
            report.valid_wallets.append(canonical)
            report.valid_count += 1

        print(
            f"[Normalizer] Ingested {report.total_ingested:,} raw inputs -> "
            f"{report.valid_count:,} valid unique wallets "
            f"({report.duplicate_count:,} duplicates, {report.rejected_count:,} rejected)."
        )
        return report

    def filter_dust_transfers(
        self, transfers: List[Tuple[str, str, float]]
    ) -> Tuple[List[Tuple[str, str, float]], List[Tuple[str, str, float]]]:
        """
        Filters out dust transfers to protect against Sybil Framing attacks.
        Bot cartels send micro-amounts (0.0001 ETH) to legitimate users to falsely
        entangle them in the cartel's transfer graph.

        :param transfers: List of (sender, receiver, value_eth)
        :return: (clean_transfers, pruned_dust_transfers)
        """
        clean = []
        dust = []

        for sender, receiver, value in transfers:
            val = float(value) if value is not None else 0.0
            s_clean = str(sender).strip().lower()
            r_clean = str(receiver).strip().lower()

            # Must be valid addresses
            if not self.is_valid_evm_address(s_clean) or not self.is_valid_evm_address(r_clean):
                continue

            # Check dust framing threshold
            if val < self.min_transfer_eth:
                dust.append((s_clean, r_clean, val))
            else:
                clean.append((s_clean, r_clean, val))

        if dust:
            print(
                f"[Normalizer] Shielded graph against {len(dust):,} dust framing transfer(s) "
                f"(< {self.min_transfer_eth} ETH)."
            )
        return clean, dust


if __name__ == "__main__":
    # Standalone verification demo
    normalizer = WalletListNormalizer()
    sample_inputs = [
        "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Valid vitalik.eth
        "0xd8da6bf26964af9d7eed9e03e53415d37aa96045",  # Duplicate (different case)
        "0xinvalidAddressWithBadLength123",            # Invalid
        "not_an_address",                               # Invalid
        "0x0000000000000000000000000000000000000000",  # Valid burn address
    ]
    res = normalizer.sanitize_wallets(sample_inputs)
    print("Sanitized list:", res.valid_wallets)
