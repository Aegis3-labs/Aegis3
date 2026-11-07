"""
Aegis3 Data Pipeline - Candidate List Ingestion & Trace Extraction CLI
Takes a raw CSV/text file of candidate addresses, applies strict EIP-55 sanitization,
extracts behavioral fingerprints, and outputs clean pipeline payloads.
"""

import os
import sys
import csv
import json
import argparse
from typing import List, Dict

# Add data-pipeline and root to sys.path
PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PIPELINE_DIR)
sys.path.append(os.path.join(PIPELINE_DIR, "extractors"))

from normalizer import WalletListNormalizer
from extractors.etherscan_client import EtherscanClient, EXPLORER_APIS
from extractors.fingerprint_extractor import FingerprintExtractor


def ingest_and_process_candidates(
    input_file: str,
    output_file: str,
    chain: str = "ethereum",
    fetch_traces: bool = False,
    api_key: str = "",
    limit: int = 500
):
    print("=" * 65)
    print("[AEGIS3] DATA INGESTION & TRACE NORMALIZER CLI")
    print("=" * 65)

    if not os.path.exists(input_file):
        print(f"[!] Error: Input file not found: {input_file}")
        return

    # 1. Read Raw Candidate List
    print(f"\n[1/3] Reading raw candidate list from {os.path.basename(input_file)}...")
    raw_addresses = []
    if input_file.endswith(".csv"):
        with open(input_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            col_idx = 0
            if header:
                # Find matching column
                for idx, h in enumerate(header):
                    if h.lower().strip() in ["sybil_address", "address", "wallet", "wallet_address"]:
                        col_idx = idx
                        break
            for row in reader:
                if row and len(row) > col_idx:
                    val = row[col_idx].strip()
                    if val:
                        raw_addresses.append(val)
    else:
        with open(input_file, "r", encoding="utf-8") as f:
            raw_addresses = [line.strip() for line in f if line.strip()]

    print(f"      Parsed {len(raw_addresses):,} raw input rows.")

    # 2. Sanitize and Validate via Normalizer
    print("\n[2/3] Sanitizing inputs and applying EIP-55 anti-framing shield...")
    normalizer = WalletListNormalizer()
    report = normalizer.sanitize_wallets(raw_addresses)

    clean_wallets = report.valid_wallets[:limit]
    print(f"      Targeting top {len(clean_wallets):,} clean unique addresses for extraction.")

    # 3. Optional Trace Extraction via Etherscan / RPC
    transfers = []
    interactions_map = {}
    outbound_map = {}

    if fetch_traces:
        print(f"\n[3/3] Fetching on-chain traces for {len(clean_wallets)} addresses on {chain}...")
        client = EtherscanClient(api_key=api_key, chain=chain)
        extractor = FingerprintExtractor()

        for idx, wallet in enumerate(clean_wallets):
            if idx % 10 == 0 and idx > 0:
                print(f"      Processed {idx}/{len(clean_wallets)} wallets...")

            normal_txs = client.get_normal_transactions(wallet, limit=50)
            token_txs = client.get_token_transactions(wallet, limit=50)

            fp = extractor.extract_fingerprint(wallet, normal_txs, token_txs)

            if fp.initial_funder:
                transfers.append((fp.initial_funder, wallet, fp.initial_funding_value_eth))

            interactions_map[wallet] = fp.contracts_called
            outbound_map[wallet] = fp.outbound_destinations
    else:
        print("\n[3/3] Trace extraction skipped (flag --fetch-traces not set).")

    # 4. Save Structured Payload
    payload = {
        "chain": chain,
        "total_valid_wallets": len(clean_wallets),
        "wallets": clean_wallets,
        "funding_transfers": transfers,
        "contract_interactions": interactions_map,
        "outbound_destinations": outbound_map,
        "sanitization_report": {
            "total_ingested": report.total_ingested,
            "valid_count": report.valid_count,
            "duplicate_count": report.duplicate_count,
            "rejected_count": report.rejected_count,
        }
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print("\n" + "=" * 65)
    print(f"[+] Ingestion complete! Saved pipeline payload to:")
    print(f"   {output_file}")
    print("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aegis3 Candidate Ingestion CLI")
    parser.add_argument("--input", required=True, help="Path to raw candidate CSV or TXT file")
    parser.add_argument("--output", default="data-pipeline/output/sanitized_candidates.json", help="Path to output JSON")
    parser.add_argument("--chain", default="ethereum", choices=list(EXPLORER_APIS.keys()), help="Target blockchain")
    parser.add_argument("--fetch-traces", action="store_true", help="Fetch live on-chain traces via explorer API")
    parser.add_argument("--api-key", default="", help="Explorer API Key")
    parser.add_argument("--limit", type=int, default=1000, help="Maximum addresses to process")

    args = parser.parse_args()
    ingest_and_process_candidates(
        input_file=args.input,
        output_file=args.output,
        chain=args.chain,
        fetch_traces=args.fetch_traces,
        api_key=args.api_key,
        limit=args.limit
    )
