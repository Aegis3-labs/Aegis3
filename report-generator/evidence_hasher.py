"""
Aegis3 Report Generator - Cryptographic Evidence Hasher & Audit Manifest
Generates immutable, content-addressed SHA-256 manifests across every audit artifact.
Enables instant detection of insider tampering, modified rows, or falsified reports.
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional


class EvidenceHasher:
    """
    Computes cryptographic SHA-256 hashes of raw inputs, graph representations,
    scored allocation databases, and client audit reports to ensure tamper-evident governance.
    """

    @staticmethod
    def hash_file(file_path: str, block_size: int = 65536) -> str:
        """
        Computes the SHA-256 hash of a file streaming in chunks.
        Safely handles multi-gigabyte CSVs without memory exhaustion.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Artifact not found on disk: {file_path}")

        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                data = f.read(block_size)
                if not data:
                    break
                sha256.update(data)
        return sha256.hexdigest()

    @staticmethod
    def hash_string(content: str) -> str:
        """Computes SHA-256 of an in-memory string."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def generate_audit_manifest(
        self,
        artifacts: Dict[str, str],
        output_manifest_path: str,
        protocol_name: str = "Aegis3 Protocol Audit",
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Generates an auditable cryptographic manifest binding all artifacts together.

        :param artifacts: Dict mapping label -> file_path (e.g. {"scored_csv": "path/to/csv"})
        :param output_manifest_path: File path to save audit_manifest.json
        :param protocol_name: Name of the protocol audited.
        :param metadata: Optional extra audit metadata (e.g., wallet count, engine version).
        :return: Dict representation of the generated manifest.
        """
        manifest_entries = {}
        cumulative_hash = hashlib.sha256()

        for label, path in artifacts.items():
            if not os.path.exists(path):
                raise FileNotFoundError(f"Cannot generate manifest; missing artifact: {path}")

            file_hash = self.hash_file(path)
            file_size = os.path.getsize(path)

            manifest_entries[label] = {
                "file_name": os.path.basename(path),
                "relative_path": os.path.relpath(path, os.path.dirname(output_manifest_path)),
                "sha256": file_hash,
                "size_bytes": file_size,
            }
            # Fold each file hash into root integrity hash
            cumulative_hash.update(file_hash.encode("utf-8"))

        root_hash = cumulative_hash.hexdigest()

        manifest = {
            "aegis3_manifest_version": "1.0.0",
            "protocol_name": protocol_name,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "root_integrity_hash": root_hash,
            "metadata": metadata or {},
            "artifacts": manifest_entries,
        }

        os.makedirs(os.path.dirname(output_manifest_path), exist_ok=True)
        with open(output_manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        print(
            f"[EvidenceHasher] Generated tamper-evident audit manifest: {output_manifest_path}\n"
            f"                  Root SHA-256: {root_hash[:16]}...{root_hash[-8:]}"
        )
        return manifest

    def verify_manifest(self, manifest_path: str) -> Tuple[bool, List[str]]:
        """
        Verifies that every artifact listed in the manifest exists and has not been tampered with.

        :param manifest_path: Path to audit_manifest.json
        :return: (is_valid: bool, errors: List[str])
        """
        if not os.path.exists(manifest_path):
            return False, [f"Manifest file not found: {manifest_path}"]

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        base_dir = os.path.dirname(manifest_path)
        errors = []
        cumulative_hash = hashlib.sha256()

        for label, item in manifest.get("artifacts", {}).items():
            rel_path = item.get("relative_path", item.get("file_name"))
            full_path = os.path.normpath(os.path.join(base_dir, rel_path))

            if not os.path.exists(full_path):
                errors.append(f"MISSING_ARTIFACT: '{label}' not found at {full_path}")
                continue

            current_hash = self.hash_file(full_path)
            expected_hash = item.get("sha256")

            if current_hash != expected_hash:
                errors.append(
                    f"TAMPER_DETECTED in '{label}' ({item['file_name']})!\n"
                    f"  Expected: {expected_hash}\n"
                    f"  Found:    {current_hash}"
                )

            cumulative_hash.update(current_hash.encode("utf-8"))

        expected_root = manifest.get("root_integrity_hash")
        computed_root = cumulative_hash.hexdigest()

        if expected_root and computed_root != expected_root:
            errors.append(
                f"ROOT_HASH_MISMATCH: Audit root integrity check failed!\n"
                f"  Expected Root: {expected_root}\n"
                f"  Computed Root: {computed_root}"
            )

        is_valid = len(errors) == 0
        if is_valid:
            print("[EvidenceHasher] VERIFICATION PASSED: All artifacts match cryptographic manifest.")
        else:
            print(f"[EvidenceHasher] [!] VERIFICATION FAILED: {len(errors)} integrity violation(s) detected.")

        return is_valid, errors
