
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class FamilyProfile:
    family_name: str = "我的家庭"
    adults: int = 2
    children: int = 1
    elders: int = 0
    city: str = ""
    annual_income: float = 600000
    annual_expense: float = 300000
    investable_assets: float = 1000000
    cash: float = 150000
    debt: float = 0
    annual_debt_payment: float = 0
    emergency_months: float = 6
    horizon_years: int = 5
    liquidity_need_3y: float = 200000
    max_drawdown_tolerance: float = 0.12
    risk_preference: str = "稳健型"
    goal_education: bool = True
    goal_retirement: bool = True
    goal_house: bool = False
    goal_healthcare: bool = True
    goal_travel: bool = False


def safe_div(a: float, b: float) -> float:
    return 0.0 if not b else a / b


def assess_family(profile: FamilyProfile) -> dict[str, Any]:
    monthly_expense = profile.annual_expense / 12 if profile.annual_expense else 0
    emergency_months_calc = safe_div(profile.cash, monthly_expense)
    savings_rate = safe_div(profile.annual_income - profile.annual_expense, profile.annual_income)
    debt_ratio = safe_div(profile.debt, profile.investable_assets + profile.cash)
    debt_service_ratio = safe_div(profile.annual_debt_payment, profile.annual_income)
    short_need_ratio = safe_div(profile.liquidity_need_3y, profile.investable_assets)

    score_parts = {}
    score_parts["现金流余量"] = max(0, min(20, savings_rate / 0.35 * 20))
    score_parts["应急资金"] = 20 if emergency_months_calc >= 6 else max(0, emergency_months_calc / 6 * 20)
    score_parts["负债压力"] = max(0, 20 * (1 - debt_ratio / 0.7))
    score_parts["偿债压力"] = max(0, 15 * (1 - debt_service_ratio / 0.4))
    score_parts["短期目标匹配"] = max(0, 15 * (1 - short_need_ratio / 0.5))
    score_parts["长期投资空间"] = 10 if profile.horizon_years >= 5 else 6 if profile.horizon_years >= 3 else 3

    total = round(sum(score_parts.values()), 1)

    if total >= 80:
        level = "较健康"
        tone = "家庭财务安全垫较好，可以在控制风险的前提下做长期配置。"
    elif total >= 65:
        level = "基本健康"
        tone = "整体可控，但需要关注现金流、短期资金和组合波动。"
    elif total >= 50:
        level = "需要优化"
        tone = "建议先补足安全垫，再逐步做基金和长期资产配置。"
    else:
        level = "需要优先修复"
        tone = "当前不适合激进投资，应先处理现金流、负债或应急资金。"

    risks = []
    if emergency_months_calc < 6:
        risks.append("应急资金不足 6 个月，建议先补足家庭安全垫。")
    if debt_ratio > 0.5:
        risks.append("负债占比较高，投资前需要确认还款压力。")
    if debt_service_ratio > 0.35:
        risks.append("年度还款压力偏高，建议避免新增高波动投资。")
    if short_need_ratio > 0.35:
        risks.append("未来三年用钱需求较高，短期资金不应放入权益基金。")
    if profile.max_drawdown_tolerance < 0.08:
        risks.append("对亏损较敏感，基金组合应以稳健和低波动为主。")

    goals = []
    if profile.goal_education:
        goals.append({"目标": "子女教育", "建议": "教育金建议用稳健资产和长期定投组合分层准备。"})
    if profile.goal_retirement:
        goals.append({"目标": "养老储备", "建议": "养老资金期限长，可用宽基、红利、债券和黄金做长期组合。"})
    if profile.goal_house:
        goals.append({"目标": "购房/改善住房", "建议": "3 年内要用的钱应放在现金、短债或存款类工具。"})
    if profile.goal_healthcare:
        goals.append({"目标": "医疗与保障", "建议": "投资前先确认家庭保障和大额医疗支出准备。"})
    if profile.goal_travel:
        goals.append({"目标": "旅行与生活品质", "建议": "这类目标可设为短中期资金桶，避免和长期投资混在一起。"})

    return {
        "profile": asdict(profile),
        "metrics": {
            "月支出": monthly_expense,
            "应急资金月数": emergency_months_calc,
            "储蓄率": savings_rate,
            "负债率": debt_ratio,
            "偿债收入比": debt_service_ratio,
            "三年资金需求占比": short_need_ratio,
        },
        "score_parts": {k: round(v, 1) for k, v in score_parts.items()},
        "total_score": total,
        "health_level": level,
        "summary": tone,
        "risks": risks,
        "goals": goals,
    }


def family_risk_to_allocation(profile: FamilyProfile) -> dict[str, float]:
    # 家庭版采用更保守的口径：先保证安全垫，再考虑成长资产
    base = {
        "保守型": {"现金/短债": 0.30, "中短债/纯债": 0.45, "宽基指数": 0.08, "红利低波": 0.07, "黄金": 0.07, "海外资产": 0.03},
        "稳健型": {"现金/短债": 0.18, "中短债/纯债": 0.36, "宽基指数": 0.18, "红利低波": 0.12, "主动权益": 0.06, "黄金": 0.07, "海外资产": 0.03},
        "平衡型": {"现金/短债": 0.12, "中短债/纯债": 0.28, "宽基指数": 0.24, "红利低波": 0.12, "主动权益": 0.10, "黄金": 0.07, "海外资产": 0.07},
        "成长型": {"现金/短债": 0.10, "中短债/纯债": 0.22, "宽基指数": 0.28, "红利低波": 0.10, "主动权益": 0.14, "行业主题": 0.04, "黄金": 0.05, "海外资产": 0.07},
        "进取型": {"现金/短债": 0.08, "中短债/纯债": 0.16, "宽基指数": 0.32, "红利低波": 0.08, "主动权益": 0.18, "行业主题": 0.06, "黄金": 0.04, "海外资产": 0.08},
    }
    alloc = base.get(profile.risk_preference, base["稳健型"]).copy()

    if profile.emergency_months < 6 or profile.liquidity_need_3y / max(profile.investable_assets, 1) > 0.35:
        # 提高安全资金，降低高波动资产
        add = 0.08
        alloc["现金/短债"] = alloc.get("现金/短债", 0) + add
        for k in ["主动权益", "行业主题", "海外资产", "宽基指数"]:
            if k in alloc and add > 0:
                cut = min(alloc[k] * 0.25, add)
                alloc[k] -= cut
                add -= cut

    total = sum(alloc.values())
    return {k: v / total for k, v in alloc.items() if v > 0.001}


def money_buckets(profile: FamilyProfile, allocation: dict[str, float]) -> list[dict[str, Any]]:
    short_amount = max(profile.liquidity_need_3y, profile.annual_expense * 0.5)
    emergency_amount = max(profile.cash, profile.annual_expense / 12 * 6)
    long_amount = max(0, profile.investable_assets - short_amount)
    return [
        {
            "资金桶": "安心生活桶",
            "用途": "应急金、日常备用、1年内确定要用的钱",
            "建议金额": emergency_amount,
            "适合工具": "现金、货币基金、短债、存款",
        },
        {
            "资金桶": "三年目标桶",
            "用途": "教育、购房、装修、家庭计划等三年内目标",
            "建议金额": short_amount,
            "适合工具": "短债、中短债、低波动固收、存款",
        },
        {
            "资金桶": "长期成长桶",
            "用途": "养老、长期增值、子女长期教育金",
            "建议金额": long_amount,
            "适合工具": "宽基指数、红利低波、少量主动权益、黄金、海外资产",
        },
    ]
