
from __future__ import annotations

import pandas as pd


def find_alternatives(
    scored_funds: pd.DataFrame,
    selected_code: str,
    same_asset_class: bool = True,
    exclude_companies: list[str] | None = None,
    top_n: int = 5,
) -> pd.DataFrame:
    if scored_funds is None or scored_funds.empty:
        return pd.DataFrame()

    df = scored_funds.copy()
    selected_code = str(selected_code).zfill(6)
    if selected_code not in df["code"].astype(str).str.zfill(6).values:
        return pd.DataFrame()

    df["code"] = df["code"].astype(str).str.zfill(6)
    selected = df[df["code"] == selected_code].iloc[0]

    pool = df[df["code"] != selected_code].copy()
    if same_asset_class:
        pool = pool[pool["asset_class"] == selected["asset_class"]]
    if exclude_companies:
        pool = pool[~pool["company"].isin(exclude_companies)]

    pool["替代匹配理由"] = pool.apply(
        lambda r: build_reason(r, selected),
        axis=1,
    )
    cols = [
        "code", "name", "company", "asset_class", "fund_type", "manager",
        "score", "annual_return", "max_drawdown", "sharpe", "rank_percentile_3y",
        "替代匹配理由",
    ]
    cols = [c for c in cols if c in pool.columns]
    return pool.sort_values("score", ascending=False)[cols].head(top_n)


def build_reason(row, selected) -> str:
    reasons = []
    if row.get("asset_class") == selected.get("asset_class"):
        reasons.append("同资产类别")
    if row.get("score", 0) >= selected.get("score", 0):
        reasons.append("评分不低于原基金")
    if row.get("rank_percentile_3y", 100) <= selected.get("rank_percentile_3y", 100):
        reasons.append("同类3年排名更靠前")
    if row.get("fee", 9) < selected.get("fee", 9):
        reasons.append("费率更低")
    if row.get("max_drawdown", -1) > selected.get("max_drawdown", -1):
        reasons.append("历史回撤更小")
    return "、".join(reasons) or "同类候选基金"
