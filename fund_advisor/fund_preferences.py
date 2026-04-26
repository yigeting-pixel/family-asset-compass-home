
from __future__ import annotations

from pathlib import Path
import pandas as pd


def load_bank_recommendations(data_dir: str | Path = "data") -> pd.DataFrame:
    path = Path(data_dir) / "bank_recommendations.csv"
    if not path.exists():
        return pd.DataFrame(columns=[
            "bank", "channel", "code", "recommend_level", "recommend_reason", "suitable_for", "bank_tag"
        ])
    df = pd.read_csv(path)
    df["code"] = _normalize_code_for_merge(df["code"])
    return df


def _normalize_code_for_merge(series: pd.Series) -> pd.Series:
    """Normalize fund codes for joins in deployed environments."""
    return series.astype(str).str.replace(r"\\.0$", "", regex=True).str.zfill(6)


def score_by_preferences(
    scored_funds: pd.DataFrame,
    theme_preferences: list[str] | None = None,
    brand_preferences: list[str] | None = None,
    bank_preferences: list[str] | None = None,
    bank_recommendations: pd.DataFrame | None = None,
    must_be_bank_recommended: bool = False,
    exclude_themes: list[str] | None = None,
    exclude_brands: list[str] | None = None,
) -> pd.DataFrame:
    if scored_funds is None or scored_funds.empty:
        return pd.DataFrame()

    theme_preferences = theme_preferences or []
    brand_preferences = brand_preferences or []
    bank_preferences = bank_preferences or []
    exclude_themes = exclude_themes or []
    exclude_brands = exclude_brands or []

    df = scored_funds.copy()
    df["code"] = _normalize_code_for_merge(df["code"])

    bank_recommendations = bank_recommendations if bank_recommendations is not None else pd.DataFrame()
    if not bank_recommendations.empty:
        br = bank_recommendations.copy()
        br["code"] = _normalize_code_for_merge(br["code"])
        br_pref = br[br["bank"].isin(bank_preferences)].copy() if bank_preferences else br.copy()

        bank_level = br_pref.groupby("code")["recommend_level"].max().rename("银行推荐等级").reset_index()
        bank_names = br_pref.groupby("code")["bank"].apply(lambda x: "、".join(sorted(set(x)))).rename("推荐银行").reset_index()
        bank_reasons = br_pref.groupby("code")["recommend_reason"].apply(lambda x: "；".join(list(dict.fromkeys(x))[:3])).rename("银行推荐理由").reset_index()
        bank_tags = br_pref.groupby("code")["bank_tag"].apply(lambda x: "、".join(sorted(set(x)))).rename("银行标签").reset_index()

        df = df.merge(bank_level, on="code", how="left")
        df = df.merge(bank_names, on="code", how="left")
        df = df.merge(bank_reasons, on="code", how="left")
        df = df.merge(bank_tags, on="code", how="left")
    else:
        df["银行推荐等级"] = None
        df["推荐银行"] = ""
        df["银行推荐理由"] = ""
        df["银行标签"] = ""

    if must_be_bank_recommended:
        df = df[df["银行推荐等级"].notna()]
    if exclude_themes:
        df = df[~df["theme"].isin(exclude_themes)]
    if exclude_brands:
        df = df[~df["company"].isin(exclude_brands)]

    def pref_score(row):
        score = 0
        reasons = []

        theme = str(row.get("theme", ""))
        style = str(row.get("style", ""))
        asset_class = str(row.get("asset_class", ""))

        if theme_preferences and theme in theme_preferences:
            score += 18
            reasons.append(f"匹配题材偏好：{theme}")
        for t in theme_preferences:
            if t and (t in style or t in asset_class):
                score += 8
                reasons.append(f"风格/类别包含：{t}")
                break

        if brand_preferences and row.get("company") in brand_preferences:
            score += 18
            reasons.append(f"匹配基金公司品牌：{row.get('company')}")

        if pd.notna(row.get("银行推荐等级")):
            level = float(row.get("银行推荐等级"))
            score += min(20, level * 4)
            banks = row.get("推荐银行", "")
            if banks:
                reasons.append(f"在银行推荐名单：{banks}")

        if row.get("asset_class") == "行业主题":
            score -= 6
            reasons.append("行业主题仅建议小比例卫星配置")
        try:
            if float(row.get("risk_level", 3)) >= 5:
                score -= 8
                reasons.append("产品风险等级较高，需要控制比例")
        except Exception:
            pass

        return pd.Series({
            "偏好加分": round(score, 1),
            "偏好匹配说明": "；".join(dict.fromkeys(reasons)) or "未命中特定偏好，按基础评分排序",
        })

    pref = df.apply(pref_score, axis=1)
    df = pd.concat([df, pref], axis=1)
    df["家庭综合分"] = (df["score"].fillna(0) * 0.75 + df["偏好加分"].fillna(0) * 0.25).round(1)
    return df.sort_values(["家庭综合分", "score"], ascending=False)


def preference_summary(
    theme_preferences: list[str],
    brand_preferences: list[str],
    bank_preferences: list[str],
    must_be_bank_recommended: bool,
) -> list[dict[str, str]]:
    return [
        {
            "偏好类型": "题材偏好",
            "当前选择": "、".join(theme_preferences) if theme_preferences else "不限制",
            "解释": "题材偏好会提高相关基金的排序，但行业主题仍然只建议小比例配置。",
        },
        {
            "偏好类型": "基金公司品牌",
            "当前选择": "、".join(brand_preferences) if brand_preferences else "不限制",
            "解释": "品牌偏好会影响候选排序，但不会替代费率、回撤、经理和同类排名分析。",
        },
        {
            "偏好类型": "银行推荐",
            "当前选择": "、".join(bank_preferences) if bank_preferences else "全部银行推荐信息",
            "解释": "银行推荐仅作为信息来源之一，不等同于适合本家庭的最终配置。",
        },
        {
            "偏好类型": "只看银行推荐",
            "当前选择": "是" if must_be_bank_recommended else "否",
            "解释": "若开启，会过滤掉不在银行推荐清单中的基金，可能导致候选范围变窄。",
        },
    ]


def bank_recommendation_view(bank_recommendations: pd.DataFrame, fund_master: pd.DataFrame) -> pd.DataFrame:
    if bank_recommendations is None or bank_recommendations.empty:
        return pd.DataFrame()
    br = bank_recommendations.copy()
    br["code"] = _normalize_code_for_merge(br["code"])
    fm = fund_master.copy()
    fm["code"] = _normalize_code_for_merge(fm["code"])
    cols = ["code", "name", "company", "asset_class", "fund_type", "theme", "risk_level"]
    return br.merge(fm[cols], on="code", how="left")
