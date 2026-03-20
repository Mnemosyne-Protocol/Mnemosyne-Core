
#!/usr/bin/env python3
"""
Mnemosyne Audit Report Generator v5
Creates a clean HTML audit report suitable for investor/studio Data Room review.

Usage:
    python3 generate_audit_report.py
    python3 generate_audit_report.py ./vault
    python3 generate_audit_report.py ./vault ./vault/keys/mnemosyne_ed25519_public.pem
    python3 generate_audit_report.py ./vault ./vault/keys/mnemosyne_ed25519_public.pem ./audit_report.html

Dependencies:
    python3 -m pip install cryptography

What it does:
- Independently verifies the Mnemosyne ledger:
  * Ed25519 signatures
  * record hashes
  * previous-record chain links
  * chain_state.json consistency
  * merkle_roots.json consistency
- Produces a polished HTML report for Data Room sharing

Exit codes:
- 0 = report generated and chain intact
- 1 = report generated but chain compromised
- 2 = usage or environment error
"""

import sys
import json
import html
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature


APP_NAME = "Mnemosyne Audit Report Generator"
APP_VERSION = "5.0.0"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(payload: Dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_public_key(path: Path) -> Ed25519PublicKey:
    data = path.read_bytes()
    return serialization.load_pem_public_key(data)


def public_key_fingerprint(pub: Ed25519PublicKey) -> str:
    raw = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return sha256_bytes(raw)


def merkle_parent(a_hex: str, b_hex: str) -> str:
    return sha256_bytes(bytes.fromhex(a_hex) + bytes.fromhex(b_hex))


def compute_merkle_root(leaves: List[str]) -> Optional[str]:
    if not leaves:
        return None
    level = list(leaves)
    while len(level) > 1:
        next_level = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else level[i]
            next_level.append(merkle_parent(left, right))
        level = next_level
    return level[0]


def verify_record_signature(record: Dict[str, Any], public_key: Ed25519PublicKey) -> List[str]:
    errors = []
    signature_block = record.get("signature")
    if not isinstance(signature_block, dict):
        return ["missing_signature_block"]

    sig_hex = signature_block.get("signature_hex")
    declared_signed_sha = signature_block.get("signed_fields_canonical_json_sha256")
    if not sig_hex or not declared_signed_sha:
        return ["incomplete_signature_block"]

    unsigned_record = dict(record)
    unsigned_record.pop("signature", None)
    signing_bytes = canonical_json_bytes(unsigned_record)
    calculated_signed_sha = sha256_bytes(signing_bytes)

    if calculated_signed_sha != declared_signed_sha:
        errors.append(
            f"signed_payload_hash_mismatch: declared={declared_signed_sha} calculated={calculated_signed_sha}"
        )

    try:
        public_key.verify(bytes.fromhex(sig_hex), signing_bytes)
    except InvalidSignature:
        errors.append("invalid_ed25519_signature")
    except Exception as e:
        errors.append(f"signature_verification_error:{e}")

    return errors


def verify_record_hash(record: Dict[str, Any]) -> List[str]:
    errors = []
    ledger = record.get("ledger", {})
    declared_record_hash = ledger.get("record_hash")
    if not declared_record_hash:
        return ["missing_ledger_record_hash"]

    calculated_record_hash = sha256_bytes(canonical_json_bytes(record))
    if calculated_record_hash != declared_record_hash:
        errors.append(
            f"record_hash_mismatch: declared={declared_record_hash} calculated={calculated_record_hash}"
        )
    return errors


def safe(s: Any) -> str:
    if s is None:
        return "—"
    return html.escape(str(s))


def short_hash(value: Optional[str], size: int = 14) -> str:
    if not value:
        return "—"
    if len(value) <= size * 2:
        return value
    return f"{value[:size]}…{value[-size:]}"


def verify_ledger(vault_dir: Path, public_key_path: Path) -> Dict[str, Any]:
    records_dir = vault_dir / "ledger" / "records"
    chain_state_path = vault_dir / "ledger" / "state" / "chain_state.json"
    merkle_roots_path = vault_dir / "ledger" / "state" / "merkle_roots.json"

    if not vault_dir.exists():
        raise FileNotFoundError(f"vault dir not found: {vault_dir}")
    if not records_dir.exists():
        raise FileNotFoundError(f"ledger records dir not found: {records_dir}")
    if not public_key_path.exists():
        raise FileNotFoundError(f"public key not found: {public_key_path}")

    public_key = load_public_key(public_key_path)
    expected_pub_fpr = public_key_fingerprint(public_key)

    record_files = sorted(records_dir.glob("*.json"))
    if not record_files:
        raise FileNotFoundError("no ledger record files found")

    results = {
        "generated_at_utc": utc_now_iso(),
        "vault_dir": str(vault_dir.resolve()),
        "public_key_path": str(public_key_path.resolve()),
        "public_key_fingerprint": expected_pub_fpr,
        "records_total": len(record_files),
        "records_ok": 0,
        "records_failed": 0,
        "chain_compromised": False,
        "record_results": [],
        "chain_checks": [],
        "calculated_merkle_root": None,
        "stored_merkle_root": None,
        "stored_record_hashes_match": None,
        "chain_state": {},
        "summary": {},
    }

    all_record_hashes = []
    previous_record_hash = None
    previous_record_file = None
    expected_index = 1

    for record_path in record_files:
        entry = {
            "file": record_path.name,
            "path": str(record_path.resolve()),
            "status": "ok",
            "errors": [],
            "record_index": None,
            "record_type": None,
            "asset_id": None,
            "declared_record_hash": None,
            "previous_record_hash": None,
            "previous_record_file": None,
            "signature_key_fingerprint": None,
            "timestamp_utc": None,
        }

        try:
            record = read_json(record_path)
        except Exception as e:
            entry["status"] = "fail"
            entry["errors"].append(f"unreadable_json:{e}")
            results["chain_compromised"] = True
            results["records_failed"] += 1
            results["record_results"].append(entry)
            continue

        entry["record_type"] = record.get("record_type") or record.get("status")
        entry["asset_id"] = record.get("asset_id")
        entry["timestamp_utc"] = record.get("timestamp_utc")

        signature_block = record.get("signature", {})
        record_pub_fpr = signature_block.get("public_key_fingerprint_sha256")
        entry["signature_key_fingerprint"] = record_pub_fpr

        if record_pub_fpr != expected_pub_fpr:
            entry["errors"].append(
                f"public_key_fingerprint_mismatch: record={record_pub_fpr} expected={expected_pub_fpr}"
            )

        entry["errors"].extend(verify_record_signature(record, public_key))
        entry["errors"].extend(verify_record_hash(record))

        ledger = record.get("ledger", {})
        record_index = ledger.get("record_index")
        prev_hash_declared = ledger.get("previous_record_hash")
        prev_file_declared = ledger.get("previous_record_file")
        declared_record_hash = ledger.get("record_hash")

        entry["record_index"] = record_index
        entry["declared_record_hash"] = declared_record_hash
        entry["previous_record_hash"] = prev_hash_declared
        entry["previous_record_file"] = prev_file_declared

        if record_index != expected_index:
            entry["errors"].append(
                f"record_index_gap_or_reorder: declared={record_index} expected={expected_index}"
            )

        if prev_hash_declared != previous_record_hash:
            entry["errors"].append(
                f"previous_record_hash_mismatch: declared={prev_hash_declared} expected={previous_record_hash}"
            )

        if prev_file_declared != previous_record_file:
            entry["errors"].append(
                f"previous_record_file_mismatch: declared={prev_file_declared} expected={previous_record_file}"
            )

        if entry["errors"]:
            entry["status"] = "fail"
            results["chain_compromised"] = True
            results["records_failed"] += 1
        else:
            results["records_ok"] += 1

        results["record_results"].append(entry)

        all_record_hashes.append(declared_record_hash)
        previous_record_hash = declared_record_hash
        previous_record_file = record_path.name
        expected_index += 1

    results["calculated_merkle_root"] = compute_merkle_root(all_record_hashes)

    try:
        chain_state = read_json(chain_state_path)
        results["chain_state"] = chain_state
    except Exception as e:
        results["chain_compromised"] = True
        results["chain_checks"].append({"name": "chain_state.json", "status": "fail", "detail": f"unreadable:{e}"})
        chain_state = None

    if chain_state:
        expected_count = len(record_files)
        checks = [
            ("chain_state.record_count", chain_state.get("record_count"), expected_count),
            ("chain_state.last_record_hash", chain_state.get("last_record_hash"), previous_record_hash),
            ("chain_state.last_record_file", chain_state.get("last_record_file"), previous_record_file),
        ]
        for name, stored, expected in checks:
            passed = stored == expected
            results["chain_checks"].append({
                "name": name,
                "status": "ok" if passed else "fail",
                "detail": f"stored={stored} expected={expected}",
            })
            if not passed:
                results["chain_compromised"] = True

    try:
        merkle_state = read_json(merkle_roots_path)
    except Exception as e:
        results["chain_compromised"] = True
        results["chain_checks"].append({"name": "merkle_roots.json", "status": "fail", "detail": f"unreadable:{e}"})
        merkle_state = None

    if merkle_state:
        stored_hashes = merkle_state.get("record_hashes", [])
        stored_root = merkle_state.get("merkle_root")
        results["stored_merkle_root"] = stored_root
        record_hashes_match = stored_hashes == all_record_hashes
        merkle_root_match = stored_root == results["calculated_merkle_root"]
        results["stored_record_hashes_match"] = record_hashes_match

        checks = [
            ("merkle_roots.record_hashes", record_hashes_match, f"stored_count={len(stored_hashes)} calculated_count={len(all_record_hashes)}"),
            ("merkle_root", merkle_root_match, f"stored={stored_root} calculated={results['calculated_merkle_root']}"),
        ]
        for name, passed, detail in checks:
            results["chain_checks"].append({
                "name": name,
                "status": "ok" if passed else "fail",
                "detail": detail,
            })
            if not passed:
                results["chain_compromised"] = True

    results["summary"] = {
        "final_status": "CHAIN COMPROMISED" if results["chain_compromised"] else "CHAIN INTACT",
        "records_total": results["records_total"],
        "records_ok": results["records_ok"],
        "records_failed": results["records_failed"],
        "calculated_merkle_root": results["calculated_merkle_root"],
        "stored_merkle_root": results["stored_merkle_root"],
    }
    return results


def render_html_report(results: Dict[str, Any]) -> str:
    final_ok = not results["chain_compromised"]
    badge_class = "badge-ok" if final_ok else "badge-fail"
    status_text = "LEDGER VERIFIED — CHAIN INTACT" if final_ok else "ZİNCİR KIRILDI — CHAIN COMPROMISED"

    record_rows = []
    for r in results["record_results"]:
        row_class = "ok-row" if r["status"] == "ok" else "fail-row"
        errors = "<br>".join(html.escape(e) for e in r["errors"]) if r["errors"] else "—"
        record_rows.append(f"""
        <tr class="{row_class}">
          <td>{safe(r["record_index"])}</td>
          <td>{safe(r["record_type"])}</td>
          <td>{safe(r["asset_id"])}</td>
          <td title="{safe(r["declared_record_hash"])}">{safe(short_hash(r["declared_record_hash"]))}</td>
          <td>{safe(r["timestamp_utc"])}</td>
          <td><span class="mini {'mini-ok' if r['status']=='ok' else 'mini-fail'}">{safe(r["status"].upper())}</span></td>
          <td>{errors}</td>
        </tr>
        """)

    chain_rows = []
    for c in results["chain_checks"]:
        chain_rows.append(f"""
        <tr class="{'ok-row' if c['status']=='ok' else 'fail-row'}">
          <td>{safe(c["name"])}</td>
          <td><span class="mini {'mini-ok' if c['status']=='ok' else 'mini-fail'}">{safe(c["status"].upper())}</span></td>
          <td>{safe(c["detail"])}</td>
        </tr>
        """)

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mnemosyne Audit Report</title>
<style>
  :root {{
    --bg: #0b1020;
    --panel: #111831;
    --panel-2: #162041;
    --text: #e8edf8;
    --muted: #a9b5d1;
    --line: #2a3766;
    --ok: #1fbf75;
    --fail: #e14d5a;
    --accent: #5aa6ff;
    --warn: #f0b429;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: linear-gradient(180deg, #0a0f1c 0%, #111831 100%);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Arial, sans-serif;
    line-height: 1.45;
  }}
  .wrap {{
    max-width: 1260px;
    margin: 0 auto;
    padding: 36px 24px 64px;
  }}
  .header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 20px;
    margin-bottom: 28px;
  }}
  h1 {{
    margin: 0 0 10px;
    font-size: 32px;
    letter-spacing: 0.2px;
  }}
  .sub {{
    color: var(--muted);
    font-size: 15px;
  }}
  .badge {{
    display: inline-block;
    padding: 10px 14px;
    border-radius: 999px;
    font-weight: 700;
    letter-spacing: 0.3px;
    border: 1px solid transparent;
    white-space: nowrap;
  }}
  .badge-ok {{
    background: rgba(31,191,117,.12);
    color: #87efb7;
    border-color: rgba(31,191,117,.35);
  }}
  .badge-fail {{
    background: rgba(225,77,90,.12);
    color: #ff9ca5;
    border-color: rgba(225,77,90,.35);
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }}
  .card {{
    background: rgba(17,24,49,.88);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 18px;
    backdrop-filter: blur(8px);
    box-shadow: 0 8px 28px rgba(0,0,0,.2);
  }}
  .label {{
    color: var(--muted);
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: .5px;
    margin-bottom: 8px;
  }}
  .value {{
    font-size: 20px;
    font-weight: 700;
    word-break: break-word;
  }}
  .small {{
    font-size: 13px;
    color: var(--muted);
  }}
  .section {{
    margin-top: 18px;
    margin-bottom: 14px;
    font-size: 20px;
    font-weight: 700;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    background: rgba(17,24,49,.88);
    border: 1px solid var(--line);
    border-radius: 18px;
    overflow: hidden;
  }}
  th, td {{
    padding: 12px 14px;
    text-align: left;
    vertical-align: top;
    border-bottom: 1px solid rgba(42,55,102,.55);
    font-size: 14px;
  }}
  th {{
    background: rgba(22,32,65,.92);
    color: #dbe5fa;
    font-weight: 700;
    position: sticky;
    top: 0;
  }}
  tr:last-child td {{
    border-bottom: none;
  }}
  .ok-row td:first-child,
  .fail-row td:first-child {{
    border-left: 4px solid transparent;
  }}
  .ok-row td:first-child {{ border-left-color: var(--ok); }}
  .fail-row td:first-child {{ border-left-color: var(--fail); }}
  .mini {{
    display: inline-block;
    padding: 4px 9px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: .3px;
  }}
  .mini-ok {{
    background: rgba(31,191,117,.14);
    color: #87efb7;
  }}
  .mini-fail {{
    background: rgba(225,77,90,.14);
    color: #ff9ca5;
  }}
  .meta-grid {{
    display: grid;
    grid-template-columns: 1.2fr 1fr;
    gap: 16px;
    margin-bottom: 22px;
  }}
  .kv {{
    display: grid;
    grid-template-columns: 220px 1fr;
    gap: 8px 12px;
    font-size: 14px;
  }}
  .kv div:nth-child(odd) {{
    color: var(--muted);
  }}
  .footer {{
    margin-top: 28px;
    color: var(--muted);
    font-size: 13px;
  }}
  @media (max-width: 980px) {{
    .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    .meta-grid {{ grid-template-columns: 1fr; }}
    .header {{ flex-direction: column; }}
  }}
  @media (max-width: 680px) {{
    .grid {{ grid-template-columns: 1fr; }}
    .kv {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <div>
        <h1>Mnemosyne Audit Report</h1>
        <div class="sub">Independent ledger verification report for investor and studio Data Room review.</div>
      </div>
      <div class="badge {badge_class}">{html.escape(status_text)}</div>
    </div>

    <div class="grid">
      <div class="card">
        <div class="label">Generated At</div>
        <div class="value">{safe(results["generated_at_utc"])}</div>
      </div>
      <div class="card">
        <div class="label">Records Verified</div>
        <div class="value">{safe(results["records_ok"])} / {safe(results["records_total"])}</div>
      </div>
      <div class="card">
        <div class="label">Calculated Merkle Root</div>
        <div class="value" style="font-size:15px">{safe(results["calculated_merkle_root"])}</div>
      </div>
      <div class="card">
        <div class="label">Stored Merkle Root</div>
        <div class="value" style="font-size:15px">{safe(results["stored_merkle_root"])}</div>
      </div>
    </div>

    <div class="meta-grid">
      <div class="card">
        <div class="section" style="margin-top:0">Verification Scope</div>
        <div class="kv">
          <div>Vault Directory</div><div>{safe(results["vault_dir"])}</div>
          <div>Public Key Path</div><div>{safe(results["public_key_path"])}</div>
          <div>Public Key Fingerprint</div><div>{safe(results["public_key_fingerprint"])}</div>
          <div>Generator</div><div>{APP_NAME} v{APP_VERSION}</div>
          <div>Final Status</div><div>{safe(results["summary"]["final_status"])}</div>
        </div>
      </div>
      <div class="card">
        <div class="section" style="margin-top:0">Executive Summary</div>
        <div class="kv">
          <div>Total Records</div><div>{safe(results["summary"]["records_total"])}</div>
          <div>Records Passed</div><div>{safe(results["summary"]["records_ok"])}</div>
          <div>Records Failed</div><div>{safe(results["summary"]["records_failed"])}</div>
          <div>Hash List Integrity</div><div>{safe(results["stored_record_hashes_match"])}</div>
          <div>Chain Outcome</div><div>{safe(status_text)}</div>
        </div>
      </div>
    </div>

    <div class="section">Chain State & Merkle Verification</div>
    <table>
      <thead>
        <tr>
          <th>Check</th>
          <th>Status</th>
          <th>Detail</th>
        </tr>
      </thead>
      <tbody>
        {''.join(chain_rows) if chain_rows else '<tr><td colspan="3">No chain checks available.</td></tr>'}
      </tbody>
    </table>

    <div class="section">Ledger Record Verification</div>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Type</th>
          <th>Asset ID</th>
          <th>Record Hash</th>
          <th>Timestamp (UTC)</th>
          <th>Status</th>
          <th>Verification Notes</th>
        </tr>
      </thead>
      <tbody>
        {''.join(record_rows)}
      </tbody>
    </table>

    <div class="footer">
      This report is designed for Data Room use. It summarizes Ed25519 signature validation, previous-record chaining, ledger state consistency, and Merkle root integrity for the Mnemosyne cryptographic asset ledger.
    </div>
  </div>
</body>
</html>"""
    return html_doc


def main() -> int:
    if len(sys.argv) > 4:
        print("Usage: python3 generate_audit_report.py [vault_dir] [public_key_path] [output_html]")
        return 2

    vault_dir = Path(sys.argv[1]) if len(sys.argv) >= 2 else Path("./vault")
    public_key_path = (
        Path(sys.argv[2])
        if len(sys.argv) >= 3
        else vault_dir / "keys" / "mnemosyne_ed25519_public.pem"
    )
    output_path = Path(sys.argv[3]) if len(sys.argv) == 4 else Path("./mnemosyne_audit_report.html")

    try:
        results = verify_ledger(vault_dir, public_key_path)
        html_report = render_html_report(results)
        output_path.write_text(html_report, encoding="utf-8")
        print(f"Audit report written: {output_path.resolve()}")
        print(f"Final status: {results['summary']['final_status']}")
        return 1 if results["chain_compromised"] else 0
    except Exception as e:
        print(f"ERROR: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
