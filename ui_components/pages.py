from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import streamlit as st

from analysis_engine import chain_summary, fetch_live_pv_data, graphviz_for
from data_layer import interface_statuses, load_claims, load_q1, load_q2, load_q3, resolve_claims, snapshot_metadata
from .layout import claim_card, page_header, render_claims


@st.cache_data(ttl=900, show_spinner=False)
def _live_data() -> dict:
    return fetch_live_pv_data()


def _render_live_data(live: dict) -> None:
    st.markdown("### 实时数据校验")
    fuyao = live.get("fuyao", {})
    if fuyao.get("adapter", {}).get("available"):
        rows = []
        for ticker_data in fuyao.get("data") or []:
            for item in ticker_data.get("items", []):
                rows.append({
                    "代码": ticker_data["ticker"],
                    "财年": item.get("fiscal_year"),
                    "营业收入(亿元)": round((item.get("operating_income") or 0) / 1e8, 2),
                    "净利润(亿元)": round((item.get("net_profit") or 0) / 1e8, 2),
                    "归母净利润(亿元)": round((item.get("parent_holder_net_profit") or 0) / 1e8, 2),
                    "EPS": item.get("basic_eps"),
                })
        st.success("扶摇 API 已连接：隆基绿能真实利润表已加载")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.warning("扶摇数据暂不可用：" + fuyao.get("adapter", {}).get("reason", "未知错误"))

    if live.get("ifind_longi"):
        st.success("iFinD MCP 已连接：隆基财务与光伏产业链指标已加载")
        st.markdown("**隆基绿能｜iFinD 财务指标**")
        st.markdown(live["ifind_longi"].get("answer", ""))
        st.markdown("**光伏产业链｜iFinD 行业指标**")
        st.markdown(live["ifind_chain"].get("answer", ""))
        descriptions = live["ifind_chain"].get("indicator_description", [])
        if descriptions:
            st.caption("指标口径与来源")
            st.dataframe(pd.DataFrame(descriptions), use_container_width=True, hide_index=True)
    else:
        reason = live.get("ifind_probe", {}).get("adapter", {}).get("reason", "未知错误")
        st.warning("iFinD 数据暂不可用：" + reason)

    for error in live.get("errors", []):
        st.caption(f"接口提示：{error}")


def render_home() -> None:
    meta = snapshot_metadata()
    page_header("光伏供应链研究终端", "证据优先 · 情景推演 · 跨市场可比", meta["snapshot_date"])
    stats = chain_summary()
    cols = st.columns(4)
    cols[0].metric("产业链公司", stats["公司数"])
    cols[1].metric("L1 收入证据", stats["L1收入证据"])
    cols[2].metric("固定情景", len(load_q2()))
    cols[3].metric("中外配对", len(load_q3()))
    st.subheader("三个研究问题")
    for title, text in [
        ("Q1｜公司真的属于这个环节吗？", "沿九段链条核验证据；仅有明确收入证据才进入L1。"),
        ("Q2｜外部冲击怎样进入财务报表？", "四个固定情景拆成0–3月、3–12月、1年以上，并保留成立与失效条件。"),
        ("Q3｜中外公司的表面数字能直接比吗？", "同时展示可比与不可比；拆解会计准则、币种、报告期、业务和政策差异。")]:
        st.markdown(f"**{title}**")
        st.caption(text)
    st.subheader("数据运行状态")
    statuses = interface_statuses()
    if all(item.available for item in statuses):
        st.success("扶摇 API 与 iFinD MCP 均已配置；关税情景页可直接查看真实公司财务和行业指标。")
    else:
        st.info("实时接口不可用时，产品会明确提示并回退到可审计的公开快照；不会生成或模拟数据。")


def render_q1() -> None:
    meta = snapshot_metadata()
    page_header("Q1 产业链证据", "从业务归属到收入证据的严格分层", meta["snapshot_date"])
    st.caption("Level口径：L1=有收入证据；L2=官方经营或扩张证据、尚缺独立收入；L3=战略布局；L4=传闻/推测。没有收入数字不得标L1。")
    rows = load_q1()
    stages = ["全部"] + list(dict.fromkeys(row["stage"] for row in rows))
    selected = st.selectbox("环节", stages)
    view = rows if selected == "全部" else [row for row in rows if row["stage"] == selected]
    st.dataframe(pd.DataFrame([{ "顺序":r["order"], "环节":r["stage"], "细分":r.get("substage","—"), "公司":r["company"], "代码":r["ticker"], "Level":r["level"], "归一理由":r["level_reason"], "claim_id":" / ".join(r["claim_ids"])} for r in view]), use_container_width=True, hide_index=True)
    for row in view:
        st.markdown(f"### {row['stage']} · {row['company']} `{row['level']}`")
        st.write(row["level_reason"])
        render_claims(resolve_claims(row["claim_ids"]))


def render_q2() -> None:
    meta = snapshot_metadata()
    page_header("Q2 冲击传导", "方向、敏感度与公式优先；不编造影响比例", meta["snapshot_date"])
    scenarios = load_q2()
    choice = st.selectbox("固定情景", [item["name"] for item in scenarios])
    scenario = next(item for item in scenarios if item["name"] == choice)
    st.markdown(f"**情景口径：** {scenario['assumption']}")
    st.graphviz_chart(graphviz_for(scenario), use_container_width=True)
    a, b = st.columns(2)
    a.markdown(f"**条件性受益：** {scenario['winners']}")
    b.markdown(f"**条件性受损：** {scenario['losers']}")
    st.markdown(f"**幅度/公式口径：** `{scenario['formula']}`")
    st.dataframe(pd.DataFrame([{ "期间":r["period"], "环节→公司→影响":r["impact"], "公司":r["companies"], "财务/经营指标":r["metrics"], "敏感度":r["sensitivity"], "推断类型":r["evidence_type"], "claim_id":" / ".join(r["claim_ids"])} for r in scenario["matrix"]]), use_container_width=True, hide_index=True)
    st.markdown(f"**失效条件：** {scenario['failure']}")
    if scenario["scenario_id"] == "US_TARIFF_25":
        st.subheader("美国关税端到端验收链")
        for index, step in enumerate(scenario["e2e_steps"], 1):
            st.markdown(f"{index}. **{step['step']}** — `{', '.join(step['claim_ids'])}`")
        with st.spinner("正在调用扶摇 API 与 iFinD MCP 拉取真实数据……"):
            live = _live_data()
        _render_live_data(live)
    render_claims(resolve_claims(scenario["claim_ids"]), "该情景全部证据")


def render_q3() -> None:
    meta = snapshot_metadata()
    page_header("Q3 中外可比", "比较业务，不机械比较表面毛利率", meta["snapshot_date"])
    pairs = load_q3()
    choice = st.selectbox("可比组", [item["title"] for item in pairs])
    pair = next(item for item in pairs if item["title"] == choice)
    if pair.get("continuity_break"):
        st.markdown('<div class="warning"><strong>主体断裂警示</strong><br>旧SunPower已于2024年进入Chapter 11；当前SunPower为原Complete Solaria收购部分资产后更名。禁止跨断点连续拼接收入、利润、资产或估值序列。</div>', unsafe_allow_html=True)
    cols = st.columns([1, 2])
    cols[0].metric("综合可比度", pair["comparability"])
    cols[1].markdown("**报告/会计差异**")
    cols[1].caption(pair["accounting"])
    st.markdown(f"**为何可比：** {pair['why_comparable']}")
    st.markdown(f"**为何不可比：** {pair['why_not']}")
    st.markdown("**推荐对标指标：** " + " · ".join(pair["metrics"]))
    for claim in resolve_claims(pair["claim_ids"]):
        claim_card(claim)


def render_sources() -> None:
    meta = snapshot_metadata()
    page_header("数据与来源", "统一Claim/Evidence账本与运行时接口状态", meta["snapshot_date"])
    st.subheader("运行时接口")
    for status in interface_statuses():
        st.markdown(f"**{status.name}** — `{status.status}`")
        st.caption(f"原因：{status.reason}")
        st.caption(f"回退：{status.fallback}")
    if st.button("刷新并加载真实数据", type="primary"):
        _live_data.clear()
        with st.spinner("正在调用扶摇 API 与 iFinD MCP……"):
            live = _live_data()
        _render_live_data(live)
    st.subheader("可信度规则")
    st.write("财报/公告=⭐⭐⭐⭐；扶摇/iFinD/行业权威=⭐⭐⭐；头部研报=⭐⭐；媒体=⭐。星级表示来源类型优先级，不代表结论无不确定性。")
    claims = list(load_claims().values())
    st.dataframe(pd.DataFrame([{ "claim_id":c.claim_id, "结论/数据":c.statement, "来源标签":c.source_label, "星级":c.stars, "source_name":c.source_name, "source_url":c.source_url, "as_of":c.as_of, "report_period":c.report_period, "retrieved_at":c.retrieved_at, "evidence_type":c.evidence_type, "限制":c.limitations} for c in claims]), use_container_width=True, hide_index=True, column_config={"source_url": st.column_config.LinkColumn("source_url")})


PAGES = {
    "研究主页": render_home,
    "Q1 产业链证据": render_q1,
    "Q2 冲击传导": render_q2,
    "Q3 中外可比": render_q3,
    "数据与来源": render_sources,
}
