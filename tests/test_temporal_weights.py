"""
Tests for TemporalWeightCalculator & GraphBuilder Integration
"""

import os
import sys

# Add core-engine to sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT_DIR, "core-engine"))

from temporal_weights import TemporalWeightCalculator
from graph_builder import GraphBuilder


def test_pairwise_temporal_weight():
    calc = TemporalWeightCalculator(burst_window_seconds=1800, max_burst_multiplier=8.0)

    # 1. Transactions executed 60 seconds apart (Synchronized bot behavior)
    weight_burst = calc.calculate_pairwise_temporal_weight(
        base_weight=1.0, timestamp_a=1700000000, timestamp_b=1700000060
    )
    # Proximity is (1.0 - 60/1800) = ~0.966 -> multiplier ~7.7x
    assert weight_burst > 7.0

    # 2. Transactions executed 300 days apart (Stale organic behavior)
    weight_stale = calc.calculate_pairwise_temporal_weight(
        base_weight=1.0, timestamp_a=1700000000, timestamp_b=1700000000 + (300 * 86400)
    )
    # Decays down toward floor
    assert weight_stale <= 0.20


def test_batch_burst_detection():
    calc = TemporalWeightCalculator(burst_window_seconds=1800, max_burst_multiplier=8.0)

    # Simulated bot cartel: Master funds 5 wallets within 5 minutes (300s total duration)
    master = "0xMasterCartel"
    t_start = 1700000000
    bot_transfers = [
        (master, f"0xPuppet_{i}", 0.05, t_start + (i * 30))
        for i in range(5)
    ]

    weighted = calc.calculate_batch_burst_weights(bot_transfers)
    assert len(weighted) == 5

    # Each edge should have received a significant burst boost (> 0.05 base)
    for _, _, w in weighted:
        assert w > 0.15


def test_graph_builder_timestamp_integration():
    builder = GraphBuilder(enable_temporal_weighting=True)

    t_start = 1700000000
    timestamped_transfers = [
        ("0xMaster", "0xBot1", 0.05, t_start),
        ("0xMaster", "0xBot2", 0.05, t_start + 15),
    ]

    builder.add_transfers(timestamped_transfers)
    graph = builder.graph

    assert graph.number_of_nodes() == 3
    assert graph.number_of_edges() == 2

    edge_weight = graph["0xmaster"]["0xbot1"]["weight"]
    # Should be amplified by temporal calculator
    assert edge_weight > 0.05


if __name__ == "__main__":
    test_pairwise_temporal_weight()
    test_batch_burst_detection()
    test_graph_builder_timestamp_integration()
    print("All Temporal Weights tests passed successfully!")
