
from __future__ import annotations

import pandas as pd


MAX_FUND_RISK_BY_CLIENT_RISK = {
    "保守型": 2,
    "稳健型": 3,
    "平衡型": 4,
    "成长型": 5,
    "进取型": 5,
}


def attach_suitability(recommendations: pd.DataFrame, master: pd.DataFrame, client_risk_level: str) -> pd.DataFrame:
    if recommendations.empty:
        return recommendations

    max_allowed = MAX_FUND_RISK_BY_CLIENT_RISK.get(client_risk_level, 3)
    risk_map = master.set_index("code")["risk_level"].to_dict()

    df = recommendations.copy()
    df["产品风险等级"] = df["基金代码"].map(risk_map).fillna(3).astype(int)
    df["适当性状态"] = df["产品风险等级"].map(lambda x: "通过" if x <= max_allowed else "需人工复核")
    df["适当性说明"] = df.apply(
        lambda r: "风险等级匹配"
        if r["产品风险等级"] <= max_allowed
        else f"产品风险等级 R{r['产品风险等级']} 高于客户当前承受上限 R{max_allowed}",
        axis=1,
    )
    return df


def compliance_notes(recommendations: pd.DataFrame, client_risk_level: str) -> list[str]:
    notes = [
        f"客户当前风险等级为「{client_risk_level}」，推荐结果需要满足基金产品风险等级与客户风险承受能力匹配。",
        "本系统输出的是资产配置和基金池筛选建议，不等同于具体产品销售或收益承诺。",
    ]
    if recommendations.empty:
        notes.append("当前条件下未形成推荐组合，不能进行产品匹配。")
        return notes

    if "适当性状态" in recommendations.columns and (recommendations["适当性状态"] == "需人工复核").any():
        notes.append("存在产品风险等级高于客户承受上限的基金，正式交易前必须进行人工复核、风险揭示或替换。")
    if recommendations["目标比例"].max() > 0.2:
        notes.append("存在单只基金建议比例超过 20%，建议拆分工具或降低集中度。")
    if recommendations.groupby("资产类别")["目标比例"].sum().get("行业主题", 0) > 0.12:
        notes.append("行业主题基金建议比例偏高，应作为卫星仓位处理。")
    return notes
