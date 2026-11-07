"""
Aegis3 Report Generator
Generates an institutional-grade, publishable HTML Audit Report
for protocol foundations and community governance.
"""

import os
import pandas as pd
from datetime import datetime

class AuditReportGenerator:
    def __init__(self, protocol_name: str = "Demo Protocol"):
        self.protocol_name = protocol_name

    def generate_html_report(self, scored_df: pd.DataFrame, output_path: str) -> str:
        total_wallets = len(scored_df)
        disqualified = len(scored_df[scored_df["recommended_verdict"] == "DISQUALIFY"])
        review = len(scored_df[scored_df["recommended_verdict"] == "MANUAL_REVIEW"])
        eligible = len(scored_df[scored_df["recommended_verdict"] == "ELIGIBLE"])

        disqualified_pct = (disqualified / total_wallets * 100) if total_wallets > 0 else 0
        eligible_pct = (eligible / total_wallets * 100) if total_wallets > 0 else 0

        # Extract top 25 high-risk records for the evidence table
        top_flagged = scored_df.head(25)

        table_rows = ""
        for _, row in top_flagged.iterrows():
            badge_color = "#e63946" if row["recommended_verdict"] == "DISQUALIFY" else "#f4a261" if row["recommended_verdict"] == "MANUAL_REVIEW" else "#2a9d8f"
            addr = row['wallet_address']
            short_addr = f"{addr[:6]}...{addr[-4:]}"
            cex_sig = row['cex_signal'] if 'cex_signal' in row else 0
            table_rows += f"""
            <tr>
                <td style="font-family: monospace; font-size: 13px;">
                    <a href="https://etherscan.io/address/{addr}" target="_blank" style="color: #4ea8de; text-decoration: none;">{short_addr}</a>
                </td>
                <td><strong style="color: {badge_color};">{row['sybil_risk_score']}/100</strong></td>
                <td><span style="background: {badge_color}22; color: {badge_color}; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{row['recommended_verdict']}</span></td>
                <td>{row['tier']}</td>
                <td style="color: #8d99ae;">Graph: {row['graph_signal']} | DNA: {row['jaccard_signal']} | CEX: {cex_sig}</td>
            </tr>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Aegis3 Launch Integrity Audit - {self.protocol_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            margin: 0;
            padding: 30px;
        }}
        .container {{
            max-width: 1050px;
            margin: 0 auto;
        }}
        .header {{
            border-bottom: 1px solid #30363d;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .logo {{
            color: #e63946;
            font-size: 26px;
            font-weight: 800;
            letter-spacing: -0.5px;
        }}
        .badge-verified {{
            background: #238636;
            color: #ffffff;
            font-size: 11px;
            font-weight: bold;
            padding: 4px 10px;
            border-radius: 20px;
            margin-left: 10px;
            vertical-align: middle;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 18px;
        }}
        .metric-value {{
            font-size: 28px;
            font-weight: 700;
            color: #f0f6fc;
            margin-top: 5px;
        }}
        .metric-label {{
            font-size: 12px;
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .table-container {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            overflow: hidden;
            margin-top: 25px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        th {{
            background: #21262d;
            color: #8b949e;
            font-size: 12px;
            font-weight: 600;
            padding: 12px 16px;
            border-bottom: 1px solid #30363d;
        }}
        td {{
            padding: 12px 16px;
            border-bottom: 1px solid #21262d;
            font-size: 13px;
        }}
        tr:hover {{
            background: #1c2128;
        }}
        .footer {{
            margin-top: 40px;
            text-align: center;
            font-size: 12px;
            color: #484f58;
            border-top: 1px solid #21262d;
            padding-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="logo">🛡️ AEGIS3</span>
            <span class="badge-verified">OFFICIAL LAUNCH AUDIT</span>
            <h1 style="color: #f0f6fc; margin: 15px 0 5px 0; font-size: 22px;">Token Distribution Integrity & Sybil Audit Report</h1>
            <p style="color: #8b949e; margin: 0; font-size: 13px;">Target Protocol: <strong>{self.protocol_name}</strong> | Generated: {datetime.now().strftime("%Y-%m-%d %H:%M UTC")} | Engine: Aegis3 Deterministic Graph Heuristics v0.1</p>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Audited Wallets</div>
                <div class="metric-value">{total_wallets:,}</div>
            </div>
            <div class="metric-card" style="border-top: 3px solid #2a9d8f;">
                <div class="metric-label">Verified Organic Users</div>
                <div class="metric-value" style="color: #2a9d8f;">{eligible:,} <span style="font-size: 14px; color: #8b949e;">({eligible_pct:.1f}%)</span></div>
            </div>
            <div class="metric-card" style="border-top: 3px solid #e63946;">
                <div class="metric-label">Disqualified Sybil Bots</div>
                <div class="metric-value" style="color: #e63946;">{disqualified:,} <span style="font-size: 14px; color: #8b949e;">({disqualified_pct:.1f}%)</span></div>
            </div>
            <div class="metric-card" style="border-top: 3px solid #f4a261;">
                <div class="metric-label">Flagged For Review</div>
                <div class="metric-value" style="color: #f4a261;">{review:,}</div>
            </div>
        </div>

        <h3 style="color: #f0f6fc; margin-bottom: 10px;">Top Flagged Sybil Coordinates (Sample Audit Trail)</h3>
        <p style="color: #8b949e; font-size: 13px; margin-top: 0;">Transparent, auditable proofs generated using Hub-Pruned Louvain Partitioning, Behavioral Jaccard DNA, and CEX Deposit Convergence.</p>

        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Wallet Address</th>
                        <th>Risk Score</th>
                        <th>Verdict</th>
                        <th>Classification Tier</th>
                        <th>Signal Breakdown</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>

        <div class="footer">
            Aegis3 Enterprise Security Suite &copy; 2026. Certified Launch Integrity Infrastructure for Web3 Protocols.
        </div>
    </div>
</body>
</html>
"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"[ReportGenerator] Successfully generated official launch audit report: {output_path}")
        return output_path
