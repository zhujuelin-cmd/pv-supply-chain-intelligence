from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import streamlit as st

from analysis_engine import chain_summary, fetch_live_pv_data, graphviz_for
from data_layer import interface_statuses, load_claims, load_industry_background, load_q1, load_q2, load_q3, resolve_claims, snapshot_metadata
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


def _source_links(source_ids: list[str], sources: dict) -> str:
    return " · ".join(f"[{sources[item]['name']}]({sources[item]['url']})" for item in source_ids)


def _industry_graphviz() -> str:
    return """digraph PV {
rankdir=LR; bgcolor=\"transparent\"; nodesep=0.35; ranksep=0.55;
node [shape=box, style=\"rounded,filled\", fillcolor=\"white\", color=\"#123B66\", fontname=\"Arial\", fontsize=10, margin=\"0.14,0.09\"];
edge [color=\"#6B7C8F\", arrowsize=0.7];
sand [label=\"硅砂\\n基础矿物原料\"];
poly [label=\"多晶硅\\n提纯与结晶\"];
wafer [label=\"硅片\\n拉晶与切片\"];
cell [label=\"电池片\\n光电转换\"];
module [label=\"组件\\n封装与可靠性\"];
epc [label=\"EPC\\n设计·采购·建设\"];
operator [label=\"电站运营商\\n发电与资产运营\"];
grid [label=\"电网\\n并网·调度·结算\"];
sand -> poly -> wafer -> cell -> module -> epc -> operator -> grid;
film [label=\"胶膜\\n封装保护\", fillcolor=\"#F5F8FB\"];
glass [label=\"光伏玻璃\\n透光与保护\", fillcolor=\"#F5F8FB\"];
frame [label=\"边框\\n结构保护\", fillcolor=\"#F5F8FB\"];
rack [label=\"支架\\n固定与跟踪\", fillcolor=\"#F5F8FB\"];
inverter [label=\"逆变器\\n直流转交流\", fillcolor=\"#F5F8FB\"];
film -> module; glass -> module; frame -> module; rack -> epc; inverter -> epc;
policy [label=\"政策\\n国内补贴·海外关税\", shape=note, color=\"#8C6A1F\", fillcolor=\"#FFF8E8\"];
commodity [label=\"大宗商品\\n工业硅·电力价格\", shape=note, color=\"#8C6A1F\", fillcolor=\"#FFF8E8\"];
policy -> module [style=dashed]; policy -> epc [style=dashed]; commodity -> poly [style=dashed];
}"""


def render_guide() -> None:
    meta = snapshot_metadata()
    page_header("📖 使用指南", "先按任务选入口，再看证据与限制", meta["snapshot_date"])
    st.subheader("从你的问题出发")
    scenarios = [
        ("① 行业新手", "我想快速了解光伏产业链是什么", "先看「🏭 行业背景」，建立从硅砂到并网发电的全景；再看「Q1 产业链证据」，理解公司为什么属于某个环节。"),
        ("② 事件研究", "我刚听到美国加征关税，想知道影响哪些公司", "直接进入「Q2 冲击传导」，在“固定情景”中选择「美国组件关税+25%」，顺着路径图、时间矩阵和证据卡片阅读。"),
        ("③ 中外对标", "我想判断中国公司和海外公司的估值是否可比", "进入「Q3 中外可比」，选择公司配对，先看业务、会计、币种和政策差异，再决定哪些指标可以放在一起。"),
    ]
    cols = st.columns(3)
    for col, (title, question, route) in zip(cols, scenarios):
        with col.container(border=True):
            st.markdown(f"### {title}")
            st.markdown(f"**{question}**")
            st.caption(route)

    st.subheader("可以调什么")
    q2_rows = [{"Q2情景": row["name"], "代表的假设": row["assumption"]} for row in load_q2()]
    st.dataframe(pd.DataFrame(q2_rows), use_container_width=True, hide_index=True)
    stages = list(dict.fromkeys(item["stage"] for item in load_q1()))
    st.markdown("**Q1 可筛选环节：** " + " · ".join(stages))
    st.caption("Q1 的下拉框支持查看全部环节或只看其中一个环节；筛选不会改变证据等级和来源。")

    st.subheader("结果在哪里看")
    outputs = [
        {"页面": "🏭 行业背景", "核心输出": "产业链全景图、环节说明、毛利率参考带、价格变量与行业阶段", "关键位置": "页面顶部全景图；中部业务说明与指标表"},
        {"页面": "Q1 产业链证据", "核心输出": "公司归属环节、L1–L4证据等级与归一理由", "关键位置": "环节筛选表下方的证据卡片"},
        {"页面": "Q2 冲击传导", "核心输出": "外部变化如何传到成本、价格、库存、毛利和公司", "关键位置": "页面顶部传导路径图；中部0–3月/3–12月/1年以上矩阵；底部证据卡片"},
        {"页面": "Q3 中外可比", "核心输出": "哪些指标可比、哪些不可比，以及差异来自哪里", "关键位置": "公司配对选择器下方的可比性分析与证据卡片"},
        {"页面": "数据与来源", "核心输出": "接口状态、可信度规则和完整Claim证据账本", "关键位置": "运行时接口区与完整来源表"},
    ]
    st.dataframe(pd.DataFrame(outputs), use_container_width=True, hide_index=True)

    st.subheader("数据说明")
    status_cols = st.columns(2)
    for col, status in zip(status_cols, interface_statuses()):
        with col.container(border=True):
            icon = "✅" if status.available else "⚠️"
            st.markdown(f"**{icon} {status.name}｜{status.status}**")
            st.caption(status.reason)
            st.caption(f"不可用时：{status.fallback}")
    st.markdown("公司事实优先使用**财报/公告**；行业价格与产业指标来自**扶摇、iFinD、CPIA、PV InfoLink、IEA PVPS 等来源**。每条关键证据都保留来源、报告期、检索日和局限性。")
    st.info("判断方法：看到绿色成功提示代表实时接口已返回；看到黄色提示代表接口暂不可用，页面正在使用公开资料快照。")
    st.warning("本产品只用于研究辅助，不提供买卖建议、目标价或收益承诺。")


def render_industry_background() -> None:
    meta = snapshot_metadata()
    data = load_industry_background()
    sources = data["sources"]
    page_header("🏭 行业背景", "从硅砂到并网发电，先建立产业链地图", meta["snapshot_date"])

    st.subheader("光伏产业链全景图")
    st.graphviz_chart(_industry_graphviz(), use_container_width=True)
    st.caption("结构来源：" + _source_links(["nrel", "cpia"], sources))
    st.info("读图方法：主链是“硅砂→多晶硅→硅片→电池片→组件→EPC→运营→电网”；胶膜、玻璃、边框、支架和逆变器从侧面进入主链；政策和大宗商品会跨环节传导。")

    st.subheader("各环节在做什么")
    groups = ["上游", "中游制造", "辅材", "下游"]
    tabs = st.tabs(groups)
    for tab, group in zip(tabs, groups):
        with tab:
            for row in [item for item in data["stages"] if item["group"] == group]:
                with st.expander(f"{row['stage']}｜代表公司：{row['companies']}", expanded=group == "上游"):
                    st.markdown(f"**主要功能：** {row['function']}")
                    st.markdown(f"**竞争关键：** {row['competition']}")
                    st.caption("来源：" + _source_links(row["source_ids"], sources))

    st.subheader("产业链关键指标")
    st.markdown("#### 代表企业综合毛利率参考带")
    st.warning("下表不是统一行业毛利率：它用各环节代表上市公司的2025年报综合毛利率构成参考带。公司可能跨多个环节，且资产运营与制造业口径不同，不能直接用于估值比较。")
    margin_rows = []
    for row in data["margin_reference"]:
        margin_rows.append({**row, "来源": sources["ifind"]["name"], "来源链接": sources["ifind"]["url"]})
    st.dataframe(
        pd.DataFrame(margin_rows).rename(columns={"stage": "环节", "margin": "毛利率参考带", "value_position": "价值链位置", "basis": "代表企业口径"}),
        use_container_width=True,
        hide_index=True,
        column_config={"来源链接": st.column_config.LinkColumn("来源链接")},
    )
    profit_cols = st.columns(3)
    for col, title, text in [
        (profit_cols[0], "制造主链", "硅料、硅片、电池、组件当前处于价格竞争与产能出清阶段，利润对价格和利用率高度敏感。"),
        (profit_cols[1], "技术与渠道", "逆变器、跟踪支架等环节更依赖技术、认证和全球服务，利润韧性相对更强。"),
        (profit_cols[2], "资产运营", "电站运营综合毛利率较高，但还需看融资成本、折旧、利用小时和资本开支。"),
    ]:
        with col.container(border=True):
            st.markdown(f"**{title}**")
            st.caption(text)
    st.caption("利润位置判断来源：" + _source_links(["ifind"], sources))

    st.markdown("#### 四个需要持续跟踪的价格变量")
    price_cols = st.columns(4)
    for col, row in zip(price_cols, data["price_variables"]):
        with col.container(border=True):
            st.markdown(f"**{row['name']}**")
            st.caption(row["meaning"])
            st.markdown(f"[查看公开价格源]({sources[row['source_id']]['url']})")

    st.subheader("行业发展阶段")
    st.markdown(f"**当前判断：{data['development']['stage']}**")
    for item in data["development"]["changes"]:
        st.markdown(f"- {item}")
    st.caption("行业阶段与技术路线来源：" + _source_links(["cpia", "iea"], sources))

    market_tabs = st.tabs(["美国", "欧洲", "新兴市场"])
    for tab, text in zip(market_tabs, data["development"]["markets"]):
        with tab:
            st.write(text)
    st.caption("海外政策来源：" + _source_links(["us_45x", "eu", "iea"], sources))

    st.subheader("如何阅读本产品")
    cols = st.columns(3)
    for col, title, text in [
        (cols[0], "① 证据分层", "先用 Q1 判断公司是否真的属于某个环节。只有明确收入证据才进入 L1，布局或传闻不能替代收入。"),
        (cols[1], "② 传导路径", "再用 Q2 把外部变化拆成成本、价格、库存、毛利和长期产能影响，并区分0–3月、3–12月和1年以上。"),
        (cols[2], "③ 中外可比", "最后用 Q3 检查业务、会计、币种、报告期和政策差异，避免把表面相同的指标直接比较。"),
    ]:
        with col.container(border=True):
            st.markdown(f"**{title}**")
            st.caption(text)
    st.info("为什么做：产业链研究能把原材料、技术、政策和终端需求连接到具体公司，帮助研究者避免只看单一财务数字。")
    st.warning("局限性：本产品不预测未来价格、不提供投资建议；传导路径是带成立条件和失效条件的逻辑推演，必须结合最新数据复核。")


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
    "📖 使用指南": render_guide,
    "🏭 行业背景": render_industry_background,
    "Q1 产业链证据": render_q1,
    "Q2 冲击传导": render_q2,
    "Q3 中外可比": render_q3,
    "数据与来源": render_sources,
}
