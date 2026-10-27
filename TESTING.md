# 测试说明

## 执行命令

```bash
pytest -q
python scripts/e2e_validate.py
streamlit run app.py --server.headless true
```

## 覆盖范围

| 测试 | 目标 |
|---|---|
| `test_claims.py` | 每条claim有HTTP(S) URL、正确星级、as_of/report_period/retrieved_at、证据类型与限制 |
| `test_q1.py` | 九段链条展示口径完整；无收入数字不能L1 |
| `test_q2.py` | 四固定情景、三时间段、图与证据完整；美国关税五步链通过 |
| `test_q3.py` | SunPower主体断点及证据存在 |
| `test_adapters.py` | 无凭据时返回unavailable、data=None并回退公开快照 |
| `test_compliance.py` | 检出买卖/收益承诺措辞，产品数据无违规措辞 |
| `test_streamlit.py` | Streamlit首页装配无异常 |

## E2E判定

`scripts/e2e_validate.py` 逐步验证：
1. 组件出口与税率口径；
2. 晶科/隆基暴露；
3. 海外收入/毛利/库存指标；
4. First Solar美国本土制造与调查范围差异；
5. 45X与关税保护独立归因。

每步必须有存在于账本的证据ID才PASS。

## 实际用户路径验证（2026-10-27）

已通过本地浏览器访问部署后的公开 URL，按分析师路径完成一次真实交互：

1. 在 Q1 筛选“组件”，定位晶科能源组件归属及 `Q1-MODULE-JINKO-2025` 收入证据；
2. 在 Q2 切换“美国组件关税+25%”，查看进口组件→晶科/隆基→美国销量、毛利率、库存→First Solar 的流程图与三时间段矩阵；
3. 核验晶科、隆基受损节点及 `Q2-TARIFF-JINKO`、`Q2-TARIFF-LONGI` 证据；
4. 在 Q3 切换“隆基绿能 — First Solar”，核验晶硅/CdTe、美国本土制造、45X 与关税保护差异；
5. 检查结论卡片均显示 claim_id、原始链接、星级、报告期、检索日、证据类型与限制。

结果：五步均通过；浏览器未发现阻断性页面错误。Graphviz 运行时出现一条“未启用 Web Worker”的非阻断警告，不影响流程图渲染和交互。
