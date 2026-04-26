
from __future__ import annotations

import pandas as pd


ASSET_BETA = {
    "现金/短债": 0.05,
    "中短债/纯债": 0.15,
    "宽基指数": 0.95,
    "红利低波": 0.70,
    "主动权益": 1.05,
    "行业主题": 1.30,
    "黄金": -0.10,
    "海外资产": 0.80,
    "REITs/另类": 0.45,
}


def stress_test(allocation: dict[str, float], market_shocks: dict[str, float] | None = None) -> pd.DataFrame:
    """Simple scenario stress test by asset beta.

    market_shocks means broad equity market drawdown assumptions.
    """
    scenarios = market_shocks or {
        "温和下跌：权益市场 -10%": -0.10,
        "明显下跌：权益市场 -20%": -0.20,
        "极端下跌：权益市场 -35%": -0.35,
        "权益上涨：权益市场 +15%": 0.15,
    }
    rows = []
    for name, shock in scenarios.items():
        total = 0.0
        details = []
        for asset, weight in allocation.items():
            beta = ASSET_BETA.get(asset, 0.5)
            asset_ret = beta * shock
            # defensive bond/gold adjustments
            if asset in ["现金/短债"]:
                asset_ret = 0.002
            elif asset == "中短债/纯债" and shock < 0:
                asset_ret = 0.005
            elif asset == "黄金" and shock < 0:
                asset_ret = min(0.08, abs(shock) * 0.25)
            total += weight * asset_ret
            details.append(f"{asset}:{asset_ret:.1%}")
        rows.append({
            "情景": name,
            "组合估算收益/回撤": total,
            "主要假设": "；".join(details),
        })
    return pd.DataFrame(rows)


def goal_projection(initial_amount: float, monthly_contribution: float, expected_return: float, years: int) -> pd.DataFrame:
    rows = []
    value = float(initial_amount)
    monthly_r = (1 + expected_return) ** (1 / 12) - 1
    for m in range(1, years * 12 + 1):
        value = value * (1 + monthly_r) + monthly_contribution
        if m % 12 == 0:
            rows.append({"年份": m // 12, "预计资产": value, "累计投入": initial_amount + monthly_contribution * m})
    return pd.DataFrame(rows)
