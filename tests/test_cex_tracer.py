"""
Tests for CEXDepositTracer
"""

import os
import sys

# Add core-engine to sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT_DIR, "core-engine"))

from filters.cex_tracer import CEXDepositTracer


def test_basic_convergence_detection():
    tracer = CEXDepositTracer(min_convergence_wallets=2)

    # 4 distinct wallets depositing into the exact same Binance personal deposit address
    transfers = [
        ("0xWalletA", "0xBinanceDeposit_1", 1.5),
        ("0xWalletB", "0xBinanceDeposit_1", 2.0),
        ("0xWalletC", "0xBinanceDeposit_1", 0.8),
        ("0xWalletD", "0xBinanceDeposit_1", 3.2),
        # Unrelated organic transfer to another address
        ("0xWalletE", "0xRandomMerchant", 0.1),
    ]

    clusters = tracer.find_converging_clusters(transfers)
    assert len(clusters) == 1

    cluster = clusters[0]
    assert cluster["deposit_address"] == "0xbinancedeposit_1"
    assert cluster["cluster_size"] == 4
    assert cluster["confidence_score"] == 100
    assert cluster["total_volume"] == 7.5
    assert set(cluster["wallets"]) == {"0xwalleta", "0xwalletb", "0xwalletc", "0xwalletd"}


def test_public_router_degree_pruning():
    tracer = CEXDepositTracer(min_convergence_wallets=2, max_deposit_degree=5)

    # 6 wallets send to Uniswap Router (exceeds max_deposit_degree=5)
    transfers = [(f"0xWallet_{i}", "0xUniswapRouter", 1.0) for i in range(6)]
    # 2 wallets send to a private CEX address
    transfers.extend([
        ("0xBot1", "0xPrivateCEX", 5.0),
        ("0xBot2", "0xPrivateCEX", 5.0),
    ])

    clusters = tracer.find_converging_clusters(transfers)
    # The router should be pruned; only 0xPrivateCEX should remain
    assert len(clusters) == 1
    assert clusters[0]["deposit_address"] == "0xprivatecex"
    assert clusters[0]["cluster_size"] == 2


def test_known_public_address_exclusion():
    known = {"0xBridgeContract"}
    tracer = CEXDepositTracer(min_convergence_wallets=2, known_public_addresses=known)

    transfers = [
        ("0xWallet1", "0xBridgeContract", 10.0),
        ("0xWallet2", "0xBridgeContract", 10.0),
    ]

    clusters = tracer.find_converging_clusters(transfers)
    assert len(clusters) == 0


def test_wallet_convergence_map():
    tracer = CEXDepositTracer(min_convergence_wallets=2)
    transfers = [
        ("0xWalletA", "0xCEX_1", 1.0),
        ("0xWalletB", "0xCEX_1", 2.0),
    ]
    clusters = tracer.find_converging_clusters(transfers)
    w_map = tracer.get_wallet_convergence_map(clusters)

    assert "0xwalleta" in w_map
    assert "0xwalletb" in w_map
    assert w_map["0xwalleta"]["deposit_address"] == "0xcex_1"


if __name__ == "__main__":
    test_basic_convergence_detection()
    test_public_router_degree_pruning()
    test_known_public_address_exclusion()
    test_wallet_convergence_map()
    print("All CEXDepositTracer tests passed successfully!")
