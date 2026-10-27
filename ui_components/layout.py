from __future__ import annotations

import html

import streamlit as st

from data_layer.models import Claim

DISCLAIMER = "研究辅助工具，不构成投资建议"

CSS = """
<style>
:root { --brand:#123B66; --ink:#17212B; --muted:#5B6773; --line:#D9E0E7; --bg:#F4F6F8; }
.stApp { background: var(--bg); color: var(--ink); }
.block-container { max-width: 1440px; padding-top: 1.2rem; padding-bottom: 2rem; }
h1 { font-size: 1.65rem !important; color: var(--ink); margin-bottom:.2rem !important; }
h2 { font-size: 1.15rem !important; border-bottom:1px solid var(--line); padding-bottom:.35rem; }
h3 { font-size: 1rem !important; }
[data-testid="stSidebar"] { background:#fff; border-right:1px solid var(--line); }
div[data-testid="stMetric"] { background:#fff; border:1px solid var(--line); border-radius:6px; padding:.65rem .8rem; }
.notice { border-left:4px solid var(--brand); background:#fff; padding:.62rem .8rem; margin:.45rem 0 .85rem; font-size:.85rem; }
.warning { border:1px solid #D8A6A6; border-left:4px solid #9B2C2C; background:#FFF9F9; padding:.75rem; border-radius:6px; }
.claim { background:#fff; border:1px solid var(--line); border-radius:6px; padding:.72rem .82rem; margin:.5rem 0; font-size:.86rem; }
.claim-id { color:var(--brand); font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-weight:650; }
.claim-meta { color:var(--muted); font-size:.78rem; margin-top:.35rem; }
.kicker { color:var(--brand); text-transform:uppercase; letter-spacing:.08em; font-size:.72rem; font-weight:700; }
.snapshot { color:var(--muted); font-size:.8rem; }
.badge { display:inline-block; border:1px solid var(--line); border-radius:4px; padding:.1rem .38rem; margin-right:.3rem; font-size:.72rem; background:#F8FAFC; }
[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:6px; }
</style>
"""


def setup_page() -> None:
    st.set_page_config(page_title="光伏供应链研究终端", page_icon="▦", layout="wide", initial_sidebar_state="expanded")
    st.markdown(CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str, snapshot_date: str) -> None:
    st.markdown('<div class="kicker">PV SUPPLY CHAIN INTELLIGENCE</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="snapshot">{html.escape(subtitle)} · 公开资料快照截止 {html.escape(snapshot_date)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="notice"><strong>{DISCLAIMER}</strong>｜结论需结合原始文件、实时市场与个体风险承受能力独立复核。</div>', unsafe_allow_html=True)


def claim_card(claim: Claim) -> None:
    metrics = ""
    if claim.metrics:
        metrics = " · ".join(f"{html.escape(str(k))}: {html.escape(str(v))}" for k, v in claim.metrics.items())
        metrics = f'<div class="claim-meta">{metrics}</div>'
    st.markdown(
        f'''<div class="claim">
        <div><span class="claim-id">{html.escape(claim.claim_id)}</span> <span class="badge">{html.escape(claim.evidence_type)}</span></div>
        <div><strong>{html.escape(claim.statement)}</strong></div>{metrics}
        <div class="claim-meta">{claim.stars} {html.escape(claim.source_label)} ｜ <a href="{html.escape(claim.source_url)}" target="_blank">{html.escape(claim.source_name)}</a> ｜ 报告期 {html.escape(claim.report_period)} ｜ as_of {html.escape(claim.as_of)} ｜ retrieved_at {html.escape(claim.retrieved_at)}</div>
        <div class="claim-meta"><strong>限制：</strong>{html.escape(claim.limitations)}</div>
        </div>''', unsafe_allow_html=True)


def render_claims(claims: list[Claim], label: str = "逐条证据") -> None:
    with st.expander(f"{label}（{len(claims)}）", expanded=False):
        for claim in claims:
            claim_card(claim)
