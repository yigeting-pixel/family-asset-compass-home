
from __future__ import annotations

import pandas as pd


def explain_allocation(client_summary: dict, allocation: dict[str, float]) -> list[dict[str, str]]:
    cards = []
    liquidity_ratio = float(client_summary.get("liquidity_need_3y_ratio", 0))
    final_risk = client_summary.get("final_risk", "稳健型")

    for asset, weight in allocation.items():
        reason = []
        if asset in ["现金/短债", "中短债/纯债"]:
            reason.append("用于覆盖短期资金需求、降低组合波动")
            if liquidity_ratio > 0.25:
                reason.append("客户未来三年资金需求占比较高，因此提高低波动资产权重")
        elif asset in ["宽基指数", "红利低波"]:
            reason.append("作为长期权益核心仓，提供市场平均收益和相对稳定的风格暴露")
        elif asset == "主动权益":
            reason.append("用于获取基金经理主动管理能力带来的超额收益，但需要控制单只和经理集中度")
        elif asset == "行业主题":
            reason.append("作为卫星仓位，参与特定行业机会，不应成为核心仓")
        elif asset == "黄金":
            reason.append("用于分散权益和债券风险，对冲极端情境")
        elif asset == "海外资产":
            reason.append("用于币种和市场分散，降低单一市场风险")
        elif asset == "REITs/另类":
            reason.append("用于增加现金流型或低相关资产暴露")

        cards.append({
            "解释主题": f"为什么配置 {asset}",
            "建议比例": f"{weight:.1%}",
            "顾问解释": "；".join(reason) or "根据客户风险等级和目标期限配置。",
            "客户版话术": f"这部分资金的目标不是追求短期高收益，而是在「{final_risk}」风险边界内承担相应角色。",
        })
    return cards


def explain_rebalance(plan: pd.DataFrame) -> list[dict[str, str]]:
    if plan is None or plan.empty:
        return []

    cards = []
    for _, r in plan.iterrows():
        action = r.get("交易方向", "")
        if action not in ["买入", "卖出", "观察"]:
            continue
        if action == "买入":
            why = f"当前金额低于目标金额，偏离约 {float(r.get('偏离比例', 0)):.1%}，需要用新增资金或调出资金补足。"
            client = "这不是一次性追涨，而是把组合补回目标比例，建议分批执行。"
        elif action == "卖出":
            why = f"当前金额高于目标金额或不在目标组合内，建议逐步降低仓位。"
            client = "卖出的目的不是判断短期涨跌，而是降低组合集中度和不匹配风险。"
        else:
            why = str(r.get("原因", "需要人工复核。"))
            client = "该基金暂不机械处理，先观察和复核，避免在不合适的位置做错误决策。"

        cards.append({
            "基金代码": r.get("基金代码", ""),
            "基金名称": r.get("基金名称", ""),
            "建议动作": action,
            "顾问解释": why,
            "客户版话术": client,
            "需要确认的问题": "是否有赎回费、锁定期、税费、客户心理预期和替代产品确认。",
        })
    return cards


def likely_client_questions(final_risk: str) -> list[dict[str, str]]:
    return [
        {
            "客户问题": "为什么不是全部买收益最高的基金？",
            "建议回答": "历史收益高通常伴随更高波动和回撤。家庭资产配置先看资金用途、期限和承受力，再决定基金工具。我们要避免在市场下跌时被迫卖出。",
        },
        {
            "客户问题": "为什么要卖掉我亏损的基金？",
            "建议回答": "亏损本身不是卖出理由。真正的判断依据是：它是否仍符合你的风险等级、目标组合、行业暴露和基金基本面。浮亏较大的品种会先进入观察或分批处理。",
        },
        {
            "客户问题": "为什么配置债券或现金，收益是不是太低？",
            "建议回答": "低波动资产负责流动性和防守。它们让组合在市场波动时有缓冲，也能避免短期资金被迫从权益基金中赎回。",
        },
        {
            "客户问题": "这个组合能保证收益吗？",
            "建议回答": "不能保证收益。这个方案的作用是把风险控制在与你的风险等级相匹配的范围内，并通过分散配置提高长期达成目标的概率。",
        },
        {
            "客户问题": f"我是{final_risk}，为什么还要限制高风险基金？",
            "建议回答": "风险等级不是只看主观偏好，还要看家庭现金流、未来支出、投资期限和应急资金。系统采用更保守的适当性等级，是为了避免错配。",
        },
    ]
