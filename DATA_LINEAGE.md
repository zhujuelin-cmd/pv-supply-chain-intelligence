# DATA LINEAGE｜数据血缘与可信度

## 1. 快照原则

- 快照截止：**2026-10-27**；每条证据保留自身 `as_of` 与 `report_period`。
- 产品运行仅读取 `data/public/*.json`；不读取工作区研究材料，不读取任何Excel。
- 研究材料只用于一次性结构化，最终展示必须关联公开来源URL。

## 2. 统一 Claim/Evidence 字段

`claim_id`、`statement`、`source_label`、`stars`、`source_name`、`source_url`、`as_of`、`report_period`、`retrieved_at`、`evidence_type`、`limitations`、可选 `metrics`。仓库加载时执行字段、URL与星级映射校验。

## 3. 可信度规则

| 来源标签 | 星级 | 用途 |
|---|---:|---|
| 财报/公告 | ⭐⭐⭐⭐ | 财报、交易所公告、SEC/监管文件、政府正式政策文本、公司正式公告 |
| 扶摇/iFinD/行业权威 | ⭐⭐⭐ | 扶摇/iFinD接口或IEA、NREL、OPIS等行业权威 |
| 头部研报 | ⭐⭐ | 头部券商/研究机构二次分析 |
| 媒体 | ⭐ | 新闻与媒体补充 |

星级是来源类型规则，不替代对口径、期间和限制的判断。

## 4. Q1 血缘

- 通威、隆基、爱旭、晶科、福斯特、福莱特、中信博、阳光电源、中国能建、中节能太阳能：分别来自上交所/深交所年报、审计报告或正式公告。
- Q1结构表仅保存环节、公司、严格Level和 `claim_id`；数字在账本中维护。
- 收入字段可直接证明L1；销量、出货、合同额、产能或业务归属不可替代收入。

## 5. Q2 血缘

- 硅料情景：OPIS耗硅口径 + 隆基历史财报证据。
- 美国关税：美国商务部政策基线、晶科/隆基财报、USITC调查范围、First Solar 45X公告。25%为压力测试假设，不是现行统一税率。
- 欧洲目标：欧盟委员会正式目标 + IEA系统整合分析。
- 钙钛矿：NREL商业化约束 + 隆基第三方认证公告。
- 每个矩阵行显式标注事实/计算/历史数据支撑/分析师共识/逻辑推演。

## 6. Q3 血缘

- 中国公司：交易所半年报或公司正式中期披露。
- Wacker：IFRS半年报告；First Solar：SEC 10-Q；Enphase：官方季度业绩。
- SunPower：旧主体Chapter 11 SEC文件、当前主体SEC业绩附件。两者之间设置不可跨越的时间序列断点。
- 币种不换算，以避免引入未注明汇率；报告期不强行对齐。

## 7. 运行时接口

`FuyaoAdapter` 检查 `FUYAO_API_KEY/API_KEY`，`IFindAdapter` 检查 `IFIND_API_KEY/IFIND_MCP_TOKEN`。即使发现环境变量，若无可调用客户端，仍返回 `unavailable`；`data=None`，回退到官方公开资料快照。当前环境四项凭据均缺失且无活动MCP，故公开快照是唯一展示数据。
