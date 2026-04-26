
from __future__ import annotations

import html
import pandas as pd


def _df_table(df: pd.DataFrame, pct_cols: list[str] | None = None) -> str:
    if df is None or df.empty:
        return "<p>无数据</p>"
    pct_cols = pct_cols or []
    rows = []
    for _, r in df.iterrows():
        cells = []
        for c in df.columns:
            v = r[c]
            if c in pct_cols and pd.notna(v):
                v = f"{float(v):.1%}"
            cells.append(f"<td>{html.escape(str(v))}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def generate_report_html(
    client_summary: dict,
    allocation_df: pd.DataFrame,
    recommendations: pd.DataFrame,
    industry_df: pd.DataFrame,
    compliance_notes: list[str],
    lookthrough_notes: list[str],
) -> str:
    style = """
    body{font-family:Arial,'Microsoft YaHei',sans-serif;margin:36px;color:#1d2433;line-height:1.65}
    h1{color:#173e75} h2{color:#173e75;border-bottom:1px solid #dfe6f3;padding-bottom:6px}
    table{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0}
    th,td{border:1px solid #dfe6f3;padding:8px;text-align:left;vertical-align:top}
    th{background:#f1f5fc;color:#173e75}
    .note{background:#fff8df;border:1px solid #ead28b;padding:10px 12px;border-radius:8px;margin:8px 0}
    .risk{background:#fff1f0;border:1px solid #f0c0bd;padding:10px 12px;border-radius:8px;margin:8px 0}
    .grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
    .metric{background:#f7faff;border:1px solid #dfe6f3;border-radius:10px;padding:10px}
    .metric b{display:block;font-size:18px;color:#173e75}
    """
    metrics = "".join(
        f"<div class='metric'><span>{html.escape(k)}</span><b>{html.escape(str(v))}</b></div>"
        for k, v in client_summary.items()
    )
    compliance = "".join(f"<div class='note'>{html.escape(x)}</div>" for x in compliance_notes)
    look = "".join(f"<div class='risk'>{html.escape(x)}</div>" for x in lookthrough_notes) or "<div class='note'>未触发明显穿透集中风险。</div>"

    rec_show = recommendations.copy()
    if not rec_show.empty:
        for col in ["目标比例", "近1年", "最大回撤"]:
            if col in rec_show.columns:
                rec_show[col] = rec_show[col].map(lambda x: "" if pd.isna(x) else f"{float(x):.1%}")
        if "配置金额" in rec_show.columns:
            rec_show["配置金额"] = rec_show["配置金额"].map(lambda x: f"{float(x):,.0f}")

    return f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'><title>客户基金配置建议书</title><style>{style}</style></head>
<body>
<h1>客户基金配置建议书</h1>
<p>本报告由基金配置分析系统生成，用于资产配置讨论，不构成具体金融产品买卖建议或收益承诺。</p>

<h2>一、客户画像</h2>
<div class='grid'>{metrics}</div>

<h2>二、目标资产配置</h2>
{_df_table(allocation_df)}

<h2>三、推荐基金组合</h2>
{_df_table(rec_show)}

<h2>四、行业穿透暴露</h2>
{_df_table(industry_df, pct_cols=["组合穿透占比"])}

<h2>五、适当性与合规提示</h2>
{compliance}

<h2>六、组合穿透风险</h2>
{look}

<h2>七、免责声明</h2>
<p>本报告中的数据、评分和组合建议依赖输入信息及数据源质量。正式交易前，应完成客户风险测评、产品风险等级匹配、合规披露和人工复核。</p>
</body></html>"""



def generate_rebalance_report_html(
    client_summary: dict,
    recommendations: pd.DataFrame,
    rebalance_plan: pd.DataFrame,
    execution_batches: pd.DataFrame,
    notes: list[str],
) -> str:
    style = """
    body{font-family:Arial,'Microsoft YaHei',sans-serif;margin:36px;color:#1d2433;line-height:1.65}
    h1{color:#173e75} h2{color:#173e75;border-bottom:1px solid #dfe6f3;padding-bottom:6px}
    table{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0}
    th,td{border:1px solid #dfe6f3;padding:8px;text-align:left;vertical-align:top}
    th{background:#f1f5fc;color:#173e75}
    .note{background:#fff8df;border:1px solid #ead28b;padding:10px 12px;border-radius:8px;margin:8px 0}
    .grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
    .metric{background:#f7faff;border:1px solid #dfe6f3;border-radius:10px;padding:10px}
    .metric b{display:block;font-size:18px;color:#173e75}
    """
    metrics = "".join(
        f"<div class='metric'><span>{html.escape(k)}</span><b>{html.escape(str(v))}</b></div>"
        for k, v in client_summary.items()
    )
    note_html = "".join(f"<div class='note'>{html.escape(x)}</div>" for x in notes)
    rb = rebalance_plan.copy() if rebalance_plan is not None else pd.DataFrame()
    if not rb.empty:
        for c in ["当前金额", "目标金额", "建议交易金额", "浮盈亏"]:
            if c in rb.columns:
                rb[c] = rb[c].map(lambda x: f"{float(x):,.0f}")
        for c in ["当前比例", "目标比例", "偏离比例", "浮盈亏比例"]:
            if c in rb.columns:
                rb[c] = rb[c].map(lambda x: f"{float(x):.1%}")

    batches = execution_batches.copy() if execution_batches is not None else pd.DataFrame()
    if not batches.empty and "本批金额" in batches.columns:
        batches["本批金额"] = batches["本批金额"].map(lambda x: f"{float(x):,.0f}")

    return f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'><title>组合调仓建议书</title><style>{style}</style></head>
<body>
<h1>组合调仓建议书</h1>
<p>本报告用于展示当前持仓与目标组合的偏离和分批执行建议，不构成交易指令。</p>

<h2>一、客户与组合摘要</h2>
<div class='grid'>{metrics}</div>

<h2>二、目标推荐组合</h2>
{_df_table(recommendations)}

<h2>三、调仓建议</h2>
{_df_table(rb)}

<h2>四、分批执行计划</h2>
{_df_table(batches)}

<h2>五、执行与合规提示</h2>
{note_html}

<h2>六、免责声明</h2>
<p>正式交易前，应结合客户风险测评、产品风险等级、交易成本、税费、赎回费、流动性和人工复核结果。</p>
</body></html>"""
