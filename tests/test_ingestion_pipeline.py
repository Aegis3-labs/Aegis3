"""
Tests for Data Pipeline Ingestion & Extraction Suite
"""

import os
import sys
import tempfile

# Add data-pipeline and extractors to sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT_DIR, "data-pipeline"))
sys.path.append(os.path.join(ROOT_DIR, "data-pipeline", "extractors"))

from extractors.fingerprint_extractor import FingerprintExtractor
from extractors.etherscan_client import EtherscanClient


def test_fingerprint_extractor():
    extractor = FingerprintExtractor(min_dust_threshold=0.0005)
    wallet = "0xCandidateWallet"

    # Mock raw normal transactions from Etherscan
    mock_normal_txs = [
        # Chronologically earliest inbound transaction: Gas Funder
        {
            "from": "0xMasterFunder",
            "to": "0xCandidateWallet",
            "value": "15000000000000000",  # 0.015 ETH
            "timeStamp": "1600000000",
            "input": "0x"
        },
        # Interaction with Uniswap Router contract (has calldata input)
        {
            "from": "0xCandidateWallet",
            "to": "0xUniswapRouter",
            "value": "0",
            "timeStamp": "1600000500",
            "input": "0x38ed1739000000000000000000000000"  # swapExactTokensForTokens
        },
        # Outbound cash-out deposit to a centralized exchange personal deposit address
        {
            "from": "0xCandidateWallet",
            "to": "0xBinanceDepositAddress",
            "value": "1000000000000000000",  # 1.0 ETH
            "timeStamp": "1600001000",
            "input": "0x"
        }
    ]

    # Mock token transactions
    mock_token_txs = [
        {
            "from": "0xCandidateWallet",
            "to": "0xBinanceDepositAddress",
            "value": "500000000",
            "tokenSymbol": "USDC",
            "timeStamp": "1600001200"
        }
    ]

    fp = extractor.extract_fingerprint(wallet, mock_normal_txs, mock_token_txs)

    # 1. Verify Initial Funder
    assert fp.initial_funder == "0xmasterfunder"
    assert fp.initial_funding_value_eth == 0.015

    # 2. Verify Smart Contracts Called (Behavioral DNA)
    assert fp.contracts_called == ["0xuniswaprouter"]

    # 3. Verify Outbound Destinations (CEX Convergence)
    destinations = [dest for dest, _ in fp.outbound_destinations]
    assert "0xbinancedepositaddress" in destinations


def test_client_local_caching():
    with tempfile.TemporaryDirectory() as tmp_cache:
        client = EtherscanClient(chain="ethereum", cache_dir=tmp_cache)
        addr = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"
        dummy_data = [{"hash": "0x123", "value": "100"}]

        # Write to cache
        client._write_cache(addr, "txlist", dummy_data)

        # Read back from cache without making an HTTP network request
        cached = client.get_normal_transactions(addr)
        assert cached == dummy_data


if __name__ == "__main__":
    test_fingerprint_extractor()
    test_client_local_caching()
    print("All Ingestion Pipeline tests passed successfully!")
