"""
Tests for EvidenceHasher & Tamper Detection
"""

import os
import sys
import tempfile
import shutil

# Add report-generator to sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT_DIR, "report-generator"))

from evidence_hasher import EvidenceHasher


def test_hash_string_and_file():
    hasher = EvidenceHasher()
    # SHA-256 of empty string is e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
    assert hasher.hash_string("") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_manifest_generation_and_tamper_detection():
    hasher = EvidenceHasher()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy artifacts
        file_a = os.path.join(tmpdir, "scored_allocations.csv")
        file_b = os.path.join(tmpdir, "launch_audit_report.html")

        with open(file_a, "w") as f:
            f.write("wallet,score\n0x111,100\n0x222,0\n")

        with open(file_b, "w") as f:
            f.write("<html><body>Report</body></html>")

        manifest_path = os.path.join(tmpdir, "audit_manifest.json")
        artifacts = {
            "scored_csv": file_a,
            "html_report": file_b,
        }

        # 1. Generate Manifest
        manifest = hasher.generate_audit_manifest(artifacts, manifest_path, protocol_name="TestProtocol")
        assert "root_integrity_hash" in manifest
        assert len(manifest["artifacts"]) == 2

        # 2. Verify Manifest (should PASS)
        is_valid, errors = hasher.verify_manifest(manifest_path)
        assert is_valid is True
        assert len(errors) == 0

        # 3. Simulate Insider Tampering: modifying a single byte in the CSV
        with open(file_a, "a") as f:
            f.write("0xInsiderBot,0\n")  # Insider altered the CSV to whitelist a bot

        # 4. Verify Manifest (should FAIL and catch the exact file)
        is_valid_tampered, tamper_errors = hasher.verify_manifest(manifest_path)
        assert is_valid_tampered is False
        assert len(tamper_errors) > 0
        assert any("TAMPER_DETECTED" in err for err in tamper_errors)


if __name__ == "__main__":
    test_hash_string_and_file()
    test_manifest_generation_and_tamper_detection()
    print("All EvidenceHasher tests passed successfully!")
