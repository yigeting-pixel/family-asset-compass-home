from __future__ import annotations

import pandas as pd

from .models import ClientProfile
from .metrics import calc_nav_metrics, portfolio_nav, calc_nav_metrics as calc_metrics


TARGET_ALLOCATION = {
    "保守型": {"现金/短债": 0.25, "中短债/纯债": 0.45, "宽基指数": 0.08, "红利低波": 0.07, "黄金": 0.08, "海外资产": 0.04, "REITs/另类": 0.03},
    "稳健型": {"现金/短债": 0.15, "中短债/纯债": 0.35, "宽基指数": 0.18, "红利低波": 0.12, "主动权益": 0.08, "黄金": 0.07, "海外资产": 0.03, "REITs/另类": 0.02},
    "平衡型": {"现金/短债": 0.10, "中短债/纯债": 0.25, "宽基指数": 0.24, "红利低波": 0.12, "主动权益": 0.12, "黄金": 0.07, "海外资产": 0.07, "REITs/另类": 0.03},
    "成长型": {"现金/短债": 0.08, "中短债/纯债": 0.18, "宽基指数": 0.28, "红利低波": 0.10, "主动权益": 0.18, "行业主题": 0.05, "黄金": 0.05, "海外资产": 0.06, "REITs/另类": 0.02},
    "进取型": {"现金/短债": 0.05, "中短债/纯债": 0.12, "宽基指数": 0.30, "红利低波": 0.08, "主动权益": 0.22, "行业主题": 0.08, "黄金": 0.04, "海外资产": 0.08, "REITs/另类": 0.03},
}


def infer_risk(profile: ClientProfile) -> str:
    capacity = 0
    capacity += 2 if profile.emergency_months >= 6 else 0
    capacity += 2 if profile.liquidity_need_3y / max(profile.investable_assets, 1) < 0.25 else 0
    capacity += 2 if profile.horizon_years >= 5 else (1 if profile.horizon_years >= 3 else 0)
    capacity += {"稳定": 2, "一般": 1, "波动": 0, "经营性": 0}.get(profile.income_stability, 1)

    preference = 0
    preference += 3 if profile.max_drawdown_tolerance >= 0.25 else 2 if profile.max_drawdown_tolerance >= 0.15 else 1 if profile.max_drawdown_tolerance >= 0.08 else 0
    pref_map = {"保守型": 1, "稳健型": 2, "平衡型": 4, "成长型": 6, "进取型": 8}
    preference = min(preference + pref_map.get(profile.risk_preference, 2), 8)
    score = min(capacity, preference)

    if score <= 2:
        return "保守型"
    if score <= 4:
        return "稳健型"
    if score <= 5:
        return "平衡型"
    if score <= 6:
        return "成长型"
    return "进取型"


def adjusted_allocation(profile: ClientProfile) -> dict[str, float]:
    risk = infer_risk(profile)
    alloc = TARGET_ALLOCATION[risk].copy()

    # 短期流动性需求高，压低风险资产
    if profile.liquidity_need_3y / max(profile.investable_assets, 1) > 0.35 or profile.horizon_years < 3:
        shift = 0.08
        for k in ["主动权益", "行业主题", "海外资产"]:
            if k in alloc:
                cut = min(alloc[k], shift / 2)
                alloc[k] -= cut
                alloc["现金/短债"] = alloc.get("现金/短债", 0) + cut
        alloc["中短债/纯债"] = alloc.get("中短债/纯债", 0) + 0.04
        alloc["宽基指数"] = max(0, alloc.get("宽基指数", 0) - 0.04)

    if not profile.need_overseas:
        alloc["宽基指数"] = alloc.get("宽基指数", 0) + alloc.get("海外资产", 0)
        alloc["海外资产"] = 0

    if not profile.prefer_gold:
        alloc["中短债/纯债"] = alloc.get("中短债/纯债", 0) + alloc.get("黄金", 0)
        alloc["黄金"] = 0

    total = sum(alloc.values())
    return {k: v / total for k, v in alloc.items() if v > 0.001}


def build_fund_scores(master: pd.DataFrame, metrics: pd.DataFrame, managers: pd.DataFrame, ranks: pd.DataFrame, holdings: pd.DataFrame) -> pd.DataFrame:
    df = master.merge(metrics, on="code", how="left").merge(ranks, on="code", how="left").merge(managers, on=["manager", "company"], how="left")
    top_holding = holdings.groupby("code")["weight"].max().rename("top_holding_weight").reset_index()
    industry_count = holdings.groupby("code")["industry"].nunique().rename("industry_count").reset_index()
    df = df.merge(top_holding, on="code", how="left").merge(industry_count, on="code", how="left")

    def score(row):
        perf = max(0, min(25, 12 + row.get("annual_return", 0) * 60 + row.get("ret_1y", 0) * 15))
        risk = max(0, min(25, 25 + row.get("max_drawdown", 0) * 50 - row.get("volatility", 0) * 12 + row.get("sharpe", 0) * 3))
        manager = max(0, min(15, 5 + float(row.get("years", 0)) * 0.8 + (3 if row.get("style_stability") in ["高", "中高"] else 0)))
        rank = max(0, min(15, 15 - float(row.get("rank_percentile_3y", 50)) * 0.18))
        cost = max(0, min(10, 10 - float(row.get("fee", 1)) * 3))
        structure = max(0, min(10, 5 + float(row.get("industry_count", 1)) + (2 if float(row.get("top_holding_weight", 99)) < 8 else -2)))
        return round(perf + risk + manager + rank + cost + structure, 1)

    df["score"] = df.apply(score, axis=1)
    return df.sort_values("score", ascending=False)


def apply_client_filters(scored: pd.DataFrame, profile: ClientProfile) -> pd.DataFrame:
    df = scored.copy()
    if profile.brand_whitelist:
        df = df[df["company"].isin(profile.brand_whitelist)]
    if profile.brand_blacklist:
        df = df[~df["company"].isin(profile.brand_blacklist)]
    if profile.excluded_themes:
        df = df[~df["theme"].isin(profile.excluded_themes)]
    if not profile.prefer_active:
        df = df[df["fund_type"].isin(["指数型", "指数增强", "债券型", "商品型", "QDII", "REITs"])]
    if not profile.prefer_index:
        df = df[~df["fund_type"].isin(["指数型", "指数增强"])]
    return df


def recommend_portfolio(provider, profile: ClientProfile) -> dict:
    master = provider.fund_master()
    nav = provider.nav()
    holdings = provider.holdings()
    managers = provider.managers()
    ranks = provider.peer_rank()

    metrics = calc_nav_metrics(nav)
    scored = build_fund_scores(master, metrics, managers, ranks, holdings)
    filtered = apply_client_filters(scored, profile)
    allocation = adjusted_allocation(profile)

    recs = []
    for asset_class, weight in allocation.items():
        bucket = filtered[filtered["asset_class"] == asset_class].copy()
        if bucket.empty:
            # 允许相近类别兜底
            bucket = filtered[filtered["asset_class"].str.contains(asset_class.split("/")[0], na=False)].copy()
        if bucket.empty:
            continue
        bucket = bucket.sort_values("score", ascending=False).head(2)
        # 核心资产取 1-2 只，主题资产只取 1 只
        n = 1 if asset_class in ["行业主题", "黄金", "海外资产", "REITs/另类"] else min(2, len(bucket))
        bucket = bucket.head(n)
        for _, row in bucket.iterrows():
            recs.append({
                "资产类别": asset_class,
                "目标比例": weight / n,
                "配置金额": profile.investable_assets * weight / n,
                "基金代码": row["code"],
                "基金名称": row["name"],
                "基金公司": row["company"],
                "基金经理": row["manager"],
                "基金类型": row["fund_type"],
                "主题": row["theme"],
                "评分": row["score"],
                "近1年": row.get("ret_1y"),
                "最大回撤": row.get("max_drawdown"),
                "夏普": row.get("sharpe"),
                "同类3年排名百分位": row.get("rank_percentile_3y"),
                "选择理由": reason_text(row, asset_class),
            })

    rec_df = pd.DataFrame(recs)
    weights = {}
    if not rec_df.empty:
        weights = {r["基金代码"]: r["目标比例"] for _, r in rec_df.iterrows()}
        pnav = portfolio_nav(nav, weights)
        pm = calc_nav_metrics(pnav.assign(code="portfolio"))
    else:
        pnav = pd.DataFrame()
        pm = pd.DataFrame()

    warnings = build_warnings(profile, rec_df)
    return {
        "risk_level": infer_risk(profile),
        "allocation": allocation,
        "scored_funds": scored,
        "filtered_funds": filtered,
        "recommendations": rec_df,
        "portfolio_nav": pnav,
        "portfolio_metrics": pm,
        "warnings": warnings,
    }


def reason_text(row, asset_class: str) -> str:
    parts = []
    if row.get("score", 0) >= 70:
        parts.append("综合评分靠前")
    if row.get("rank_percentile_3y", 100) <= 30:
        parts.append("同类3年排名靠前")
    if row.get("sharpe", 0) > 0.5:
        parts.append("风险调整后收益较好")
    if row.get("fee", 9) <= 0.6:
        parts.append("费率较低")
    if row.get("style_stability") in ["高", "中高"]:
        parts.append("经理/团队风格较稳定")
    if not parts:
        parts.append("作为该类别候选工具")
    return "、".join(parts)


def build_warnings(profile: ClientProfile, rec_df: pd.DataFrame) -> list[str]:
    warnings = []
    if profile.emergency_months < 6:
        warnings.append("应急资金不足，建议先保留 6-12 个月家庭支出，不要全部进入基金组合。")
    if profile.liquidity_need_3y / max(profile.investable_assets, 1) > 0.35:
        warnings.append("未来 3 年资金需求较高，权益和行业主题仓位应取下沿。")
    if not rec_df.empty:
        by_asset = rec_df.groupby("资产类别")["目标比例"].sum()
        if by_asset.get("行业主题", 0) > 0.12:
            warnings.append("行业主题基金超过 12%，建议控制为卫星仓位。")
        for _, r in rec_df.iterrows():
            if r["目标比例"] > 0.20:
                warnings.append(f"{r['基金名称']} 单只建议比例超过 20%，应拆分或降低集中度。")
    return warnings
