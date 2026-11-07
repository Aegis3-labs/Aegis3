"""
Tests for WalletListNormalizer & Anti-Framing Shield
"""

import os
import sys

# Add data-pipeline to sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT_DIR, "data-pipeline"))

from normalizer import WalletListNormalizer


def test_valid_address_detection():
    normalizer = WalletListNormalizer()
    valid_addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    assert normalizer.is_valid_evm_address(valid_addr) is True
    assert normalizer.is_valid_evm_address("0x0000000000000000000000000000000000000000") is True


def test_invalid_address_rejection():
    normalizer = WalletListNormalizer()
    assert normalizer.is_valid_evm_address("not_an_address") is False
    assert normalizer.is_valid_evm_address("0x123") is False
    assert normalizer.is_valid_evm_address("0x" + "Z" * 40) is False  # Non-hex characters
    assert normalizer.is_valid_evm_address(None) is False
    assert normalizer.is_valid_evm_address(12345) is False


def test_case_insensitive_deduplication():
    normalizer = WalletListNormalizer()
    raw = [
        "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        "0xD8DA6BF26964AF9D7EED9E03E53415D37AA96045",  # Uppercase
        "0xd8da6bf26964af9d7eed9e03e53415d37aa96045",  # Lowercase
    ]
    report = normalizer.sanitize_wallets(raw)

    assert report.total_ingested == 3
    assert report.valid_count == 1
    assert report.duplicate_count == 2
    assert report.valid_wallets == ["0xd8da6bf26964af9d7eed9e03e53415d37aa96045"]


def test_sybil_framing_dust_filter():
    normalizer = WalletListNormalizer(min_transfer_eth=0.0005)
    valid_master = "0x1111111111111111111111111111111111111111"
    valid_victim = "0x2222222222222222222222222222222222222222"

    transfers = [
        # Normal economic transfer (should pass)
        (valid_master, valid_victim, 0.5),
        # Sybil framing dust transfer (0.0001 ETH < 0.0005 threshold, should be pruned)
        (valid_master, valid_victim, 0.0001),
        # Zero value approval/taint ping
        (valid_master, valid_victim, 0.0),
    ]

    clean, dust = normalizer.filter_dust_transfers(transfers)

    assert len(clean) == 1
    assert clean[0][2] == 0.5
    assert len(dust) == 2
    assert dust[0][2] == 0.0001
    assert dust[1][2] == 0.0


if __name__ == "__main__":
    test_valid_address_detection()
    test_invalid_address_rejection()
    test_case_insensitive_deduplication()
    test_sybil_framing_dust_filter()
    print("All WalletListNormalizer tests passed successfully!")
