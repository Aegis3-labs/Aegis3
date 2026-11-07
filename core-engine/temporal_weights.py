"""
Aegis3 Core Engine - Temporal Decay & Synchronized Burst Weighting
Calculates dynamic edge weights based on transaction inter-arrival times and burst clustering.
Synchronized bot farm distributions get exponential weight boosts; stale transfers decay.
"""

import math
from typing import List, Tuple, Dict, Optional
from collections import defaultdict


class TemporalWeightCalculator:
    """
    Applies exponential decay kernels and batch burst detection to transaction edges.
    """

    def __init__(
        self,
        burst_window_seconds: int = 1800,       # 30 minutes: maximum window for rapid bot batching
        stale_threshold_seconds: int = 15552000, # 180 days: transactions older than this decay
        max_burst_multiplier: float = 8.0,      # Max weight boost for near-simultaneous batch bursts
        min_decay_floor: float = 0.15           # Minimum weight floor for very old historical transfers
    ):
        self.burst_window = burst_window_seconds
        self.stale_threshold = stale_threshold_seconds
        self.max_multiplier = max_burst_multiplier
        self.decay_floor = min_decay_floor

    def calculate_pairwise_temporal_weight(
        self,
        base_weight: float,
        timestamp_a: int,
        timestamp_b: int
    ) -> float:
        """
        Calculates the weight between two related transactions based on time difference.
        delta_t near 0 -> high weight multiplier.
        delta_t very large -> decayed weight.
        """
        delta_t = abs(timestamp_a - timestamp_b)

        if delta_t <= self.burst_window:
            # Synchronized execution: scale from 1.0 up to max_multiplier as delta_t approaches 0
            proximity = 1.0 - (delta_t / self.burst_window)
            multiplier = 1.0 + ((self.max_multiplier - 1.0) * proximity)
            return round(base_weight * multiplier, 6)

        # Gradual exponential decay for older transactions
        decay_constant = self.stale_threshold / 2.0
        decay = math.exp(-delta_t / decay_constant)
        effective_decay = max(self.decay_floor, decay)

        return round(base_weight * effective_decay, 6)

    def calculate_batch_burst_weights(
        self,
        timestamped_transfers: List[Tuple[str, str, float, int]]
    ) -> List[Tuple[str, str, float]]:
        """
        Ingests timestamped transfers: (sender, receiver, value_eth, timestamp).
        Identifies master wallets that execute rapid-fire batch distributions to multiple recipients,
        and applies synchronized burst multipliers to all child edges in that batch.

        :return: List of weighted transfers: (sender, receiver, weighted_value)
        """
        if not timestamped_transfers:
            return []

        # Group outbound transfers by sender to detect master distribution bursts
        sender_batches = defaultdict(list)
        for sender, receiver, val, ts in timestamped_transfers:
            sender_batches[str(sender).lower().strip()].append((str(receiver).lower().strip(), float(val), int(ts)))

        weighted_transfers = []

        for sender, transfers in sender_batches.items():
            if len(transfers) < 2:
                # Single transfer: no batch clustering possible, preserve base value
                for r, v, _ in transfers:
                    weighted_transfers.append((sender, r, round(v, 6)))
                continue

            # Sort transfers chronologically by timestamp
            transfers.sort(key=lambda x: x[2])
            timestamps = [t[2] for t in transfers]
            batch_duration = timestamps[-1] - timestamps[0]

            # Calculate average interval between consecutive transactions
            intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            avg_interval = sum(intervals) / len(intervals) if intervals else 0

            # If the entire distribution batch was completed within burst_window
            # or the average inter-arrival time is under 120 seconds (automated loop)
            if batch_duration <= self.burst_window or avg_interval <= 120:
                # Bot cartel detected: calculate burst intensity
                # Shorter duration & more recipients = higher intensity
                intensity = min(1.0, self.burst_window / max(1, batch_duration))
                size_factor = min(2.0, 1.0 + (len(transfers) / 50.0))
                burst_boost = min(self.max_multiplier, 1.0 + (self.max_multiplier - 1.0) * intensity * size_factor)

                for r, v, _ in transfers:
                    weighted_val = round(v * burst_boost, 6)
                    weighted_transfers.append((sender, r, weighted_val))
            else:
                # Human / Organic pacing: apply standard pairwise decay
                for r, v, ts in transfers:
                    weighted_transfers.append((sender, r, round(v, 6)))

        return weighted_transfers
