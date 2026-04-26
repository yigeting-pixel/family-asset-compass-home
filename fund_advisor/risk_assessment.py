
from __future__ import annotations

from dataclasses import dataclass


QUESTIONS = [
    {
        "key": "loss_reaction",
        "title": "如果组合短期下跌 10%，你的反应更接近？",
        "options": [
            ("立即赎回，先保住本金", 0),
            ("部分赎回，降低波动", 1),
            ("继续观察，不急于处理", 2),
            ("有闲钱会考虑分批加仓", 3),
        ],
    },
    {
        "key": "experience",
        "title": "你的基金/股票投资经验？",
        "options": [
            ("少于 1 年", 0),
            ("1-3 年", 1),
            ("3-5 年", 2),
            ("5 年以上，经历过完整牛熊", 3),
        ],
    },
    {
        "key": "income",
        "title": "家庭收入稳定性？",
        "options": [
            ("波动较大或经营收入为主", 0),
            ("一般稳定", 1),
            ("较稳定", 2),
            ("非常稳定且收入来源多元", 3),
        ],
    },
    {
        "key": "liquidity",
        "title": "未来 3 年是否有大额支出？",
        "options": [
            ("有，且金额较大", 0),
            ("有，但可控", 1),
            ("不确定", 2),
            ("基本没有", 3),
        ],
    },
    {
        "key": "horizon",
        "title": "这笔资金最长可投资多久？",
        "options": [
            ("1 年以内", 0),
            ("1-3 年", 1),
            ("3-5 年", 2),
            ("5 年以上", 3),
        ],
    },
    {
        "key": "knowledge",
        "title": "你对基金净值波动、回撤、夏普、风格漂移的理解？",
        "options": [
            ("基本不了解", 0),
            ("了解一些，但不系统", 1),
            ("能看懂主要指标", 2),
            ("能独立判断基金风格与风险", 3),
        ],
    },
]


def evaluate_risk_answers(answer_scores: dict[str, int]) -> dict:
    total = sum(answer_scores.values())
    max_score = len(QUESTIONS) * 3
    ratio = total / max_score if max_score else 0

    if ratio <= 0.25:
        risk = "保守型"
        max_fund_risk = 2
    elif ratio <= 0.45:
        risk = "稳健型"
        max_fund_risk = 3
    elif ratio <= 0.65:
        risk = "平衡型"
        max_fund_risk = 4
    elif ratio <= 0.82:
        risk = "成长型"
        max_fund_risk = 5
    else:
        risk = "进取型"
        max_fund_risk = 5

    return {
        "questionnaire_score": total,
        "questionnaire_max": max_score,
        "questionnaire_ratio": ratio,
        "questionnaire_risk_level": risk,
        "max_fund_risk": max_fund_risk,
    }
