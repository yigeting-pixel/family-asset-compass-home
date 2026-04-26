from __future__ import annotations

import pandas as pd


def _normalize_code(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)


def industry_exposure(recommendations: pd.DataFrame, holdings: pd.DataFrame) -> pd.DataFrame:
    if recommendations is None or recommendations.empty:
        return pd.DataFrame(columns=["industry", "组合穿透占比"])

    rec = recommendations[["基金代码", "目标比例"]].rename(columns={"基金代码": "code"}).copy()
    rec["code"] = _normalize_code(rec["code"])

    h = holdings.copy()
    if "code" not in h.columns:
        return pd.DataFrame(columns=["industry", "组合穿透占比"])
    h["code"] = _normalize_code(h["code"])

    h = h.merge(rec, on="code", how="inner")
    if h.empty:
        return pd.DataFrame(columns=["industry", "组合穿透占比"])

    h["组合穿透占比"] = h["weight"] / 100 * h["目标比例"]
    return (
        h.groupby("industry", as_index=False)["组合穿透占比"]
        .sum()
        .sort_values("组合穿透占比", ascending=False)
    )


def brand_exposure(recommendations: pd.DataFrame) -> pd.DataFrame:
    if recommendations is None or recommendations.empty:
        return pd.DataFrame(columns=["基金公司", "目标比例"])
    return (
        recommendations.groupby("基金公司", as_index=False)["目标比例"]
        .sum()
        .sort_values("目标比例", ascending=False)
    )


def manager_exposure(recommendations: pd.DataFrame) -> pd.DataFrame:
    if recommendations is None or recommendations.empty:
        return pd.DataFrame(columns=["基金经理", "目标比例"])
    return (
        recommendations.groupby("基金经理", as_index=False)["目标比例"]
        .sum()
        .sort_values("目标比例", ascending=False)
    )


def holding_overlap(recommendations: pd.DataFrame, holdings: pd.DataFrame) -> pd.DataFrame:
    if recommendations is None or recommendations.empty:
        return pd.DataFrame(columns=["基金A", "基金B", "重合持仓数", "重合权重估算"])

    rec = recommendations.copy()
    rec["基金代码"] = _normalize_code(rec["基金代码"])

    h = holdings.copy()
    if "code" not in h.columns:
        return pd.DataFrame(columns=["基金A", "基金B", "重合持仓数", "重合权重估算", "重合持仓"])
    h["code"] = _normalize_code(h["code"])

    codes = rec["基金代码"].tolist()
    rows = []
    hmap = {}
    for code in codes:
        g = h[h["code"] == code]
        hmap[code] = {r["holding"]: float(r["weight"]) for _, r in g.iterrows()}

    for i, a in enumerate(codes):
        for b in codes[i + 1:]:
            common = set(hmap.get(a, {})) & set(hmap.get(b, {}))
            overlap_weight = sum(min(hmap[a][x], hmap[b][x]) for x in common) / 100
            if common:
                rows.append({
                    "基金A": a,
                    "基金B": b,
                    "重合持仓数": len(common),
                    "重合权重估算": overlap_weight,
                    "重合持仓": "、".join(sorted(common)),
                })
    return pd.DataFrame(rows).sort_values("重合权重估算", ascending=False) if rows else pd.DataFrame(columns=["基金A", "基金B", "重合持仓数", "重合权重估算", "重合持仓"])


def lookthrough_warnings(industry_df: pd.DataFrame, brand_df: pd.DataFrame, manager_df: pd.DataFrame, overlap_df: pd.DataFrame) -> list[str]:
    warnings = []
    if industry_df is not None and not industry_df.empty:
        top = industry_df.iloc[0]
        if top["组合穿透占比"] > 0.35:
            warnings.append(f"组合穿透后对「{top['industry']}」暴露达到 {top['组合穿透占比']:.1%}，存在行业/主题集中风险。")
    if brand_df is not None and not brand_df.empty:
        top = brand_df.iloc[0]
        if top["目标比例"] > 0.45:
            warnings.append(f"组合中「{top['基金公司']}」占比达到 {top['目标比例']:.1%}，品牌集中度较高。")
    if manager_df is not None and not manager_df.empty:
        top = manager_df.iloc[0]
        if top["目标比例"] > 0.30 and top["基金经理"] not in ["-", "固收团队", "量化团队"]:
            warnings.append(f"组合中基金经理「{top['基金经理']}」管理产品占比较高，存在管理人集中风险。")
    if overlap_df is not None and not overlap_df.empty and overlap_df["重合权重估算"].max() > 0.08:
        r = overlap_df.iloc[0]
        warnings.append(f"{r['基金A']} 与 {r['基金B']} 的重合持仓权重较高，可能削弱组合分散效果。")
    return warnings
