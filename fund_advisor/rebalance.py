
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import pandas as pd


def _normalize_code(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)


def _pick_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def normalize_current_holdings(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize current holdings.

    Supported input formats:
    - code,name,amount,cost_amount
    - 基金代码,基金名称,持仓金额（万元）,当前盈亏（万元）
    - code,name,amount_wan,profit_wan
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["code", "name", "amount", "cost_amount", "profit_amount"])

    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]

    code_col = _pick_column(out, ["code", "基金代码", "基金编号", "基金代码/编号"])
    name_col = _pick_column(out, ["name", "基金名称"])
    amount_col = _pick_column(out, ["amount", "持仓金额", "当前金额"])
    amount_wan_col = _pick_column(out, ["amount_wan", "持仓金额（万元）", "当前金额（万元）", "持仓金额(万元)", "当前金额(万元)"])
    cost_col = _pick_column(out, ["cost_amount", "成本金额"])
    cost_wan_col = _pick_column(out, ["cost_amount_wan", "成本金额（万元）", "成本金额(万元)"])
    profit_col = _pick_column(out, ["profit_amount", "当前盈亏", "浮盈亏"])
    profit_wan_col = _pick_column(out, ["profit_wan", "当前盈亏（万元）", "浮盈亏（万元）", "当前盈利（万元）", "当前盈利情况（万元）", "当前盈亏(万元)", "浮盈亏(万元)"])

    if code_col is None:
        raise ValueError("当前持仓必须包含基金代码 / code")
    if amount_col is None and amount_wan_col is None:
        raise ValueError("当前持仓必须包含持仓金额（万元）或 amount")

    normalized = pd.DataFrame()
    normalized["code"] = _normalize_code(out[code_col])
    normalized["name"] = out[name_col].astype(str) if name_col else normalized["code"]

    if amount_wan_col:
        normalized["amount"] = pd.to_numeric(out[amount_wan_col], errors="coerce").fillna(0.0) * 10000
    else:
        normalized["amount"] = pd.to_numeric(out[amount_col], errors="coerce").fillna(0.0)

    if profit_wan_col:
        normalized["profit_amount"] = pd.to_numeric(out[profit_wan_col], errors="coerce").fillna(0.0) * 10000
        normalized["cost_amount"] = normalized["amount"] - normalized["profit_amount"]
    elif profit_col:
        normalized["profit_amount"] = pd.to_numeric(out[profit_col], errors="coerce").fillna(0.0)
        normalized["cost_amount"] = normalized["amount"] - normalized["profit_amount"]
    elif cost_wan_col:
        normalized["cost_amount"] = pd.to_numeric(out[cost_wan_col], errors="coerce").fillna(0.0) * 10000
        normalized["profit_amount"] = normalized["amount"] - normalized["cost_amount"]
    elif cost_col:
        normalized["cost_amount"] = pd.to_numeric(out[cost_col], errors="coerce").fillna(normalized["amount"])
        normalized["profit_amount"] = normalized["amount"] - normalized["cost_amount"]
    else:
        normalized["cost_amount"] = normalized["amount"]
        normalized["profit_amount"] = 0.0

    normalized["cost_amount"] = normalized["cost_amount"].clip(lower=0.0)
    normalized = normalized[normalized["amount"] > 0].copy()
    return normalized[["code", "name", "amount", "cost_amount", "profit_amount"]]


def recommendations_to_targets(recommendations: pd.DataFrame, investable_assets: float) -> pd.DataFrame:
    if recommendations is None or recommendations.empty:
        return pd.DataFrame(columns=["code", "name", "target_weight", "target_amount", "asset_class"])

    df = recommendations.copy()
    return pd.DataFrame({
        "code": _normalize_code(df["基金代码"]),
        "name": df["基金名称"],
        "target_weight": df["目标比例"].astype(float),
        "target_amount": df["目标比例"].astype(float) * float(investable_assets),
        "asset_class": df["资产类别"],
    })


def build_rebalance_plan(
    current_holdings: pd.DataFrame,
    target_holdings: pd.DataFrame,
    total_assets: float,
    min_trade_amount: float = 5000,
    drift_threshold: float = 0.02,
    sell_loss_control: bool = True,
) -> pd.DataFrame:
    cur = normalize_current_holdings(current_holdings)
    tgt = target_holdings.copy() if target_holdings is not None else pd.DataFrame()
    if not tgt.empty and "code" in tgt.columns:
        tgt["code"] = _normalize_code(tgt["code"])

    cur_map = cur.set_index("code").to_dict("index") if not cur.empty else {}
    tgt_map = tgt.set_index("code").to_dict("index") if not tgt.empty else {}

    codes = sorted(set(cur_map) | set(tgt_map))
    rows = []
    for code in codes:
        c = cur_map.get(code, {})
        t = tgt_map.get(code, {})
        current_amount = float(c.get("amount", 0.0))
        cost_amount = float(c.get("cost_amount", current_amount))
        target_amount = float(t.get("target_amount", 0.0))
        current_weight = current_amount / total_assets if total_assets else 0
        target_weight = float(t.get("target_weight", 0.0))
        diff = target_amount - current_amount
        drift = target_weight - current_weight
        pnl = current_amount - cost_amount
        pnl_ratio = pnl / cost_amount if cost_amount else 0

        if abs(diff) < min_trade_amount and abs(drift) < drift_threshold:
            action = "保留"; trade_amount = 0.0; reason = "当前持仓接近目标比例"; priority = "低"
        elif diff > 0:
            action = "买入"; trade_amount = diff; reason = "当前配置低于目标比例"; priority = "高" if abs(drift) >= 0.05 else "中"
        else:
            action = "卖出"; trade_amount = abs(diff); reason = "当前配置高于目标比例"; priority = "高" if abs(drift) >= 0.05 else "中"

        if action == "卖出" and sell_loss_control and pnl_ratio < -0.15:
            action = "观察"; trade_amount = 0.0; reason = "当前浮亏较大，建议先观察；可结合新增资金、基金基本面和家庭承受力再决定是否分批调出"; priority = "中"

        if current_amount > 0 and target_amount == 0:
            if pnl_ratio < -0.15 and sell_loss_control:
                action = "观察"; trade_amount = 0.0; reason = "不在目标组合内，但浮亏较大，建议先观察并判断退出节奏"; priority = "中"
            else:
                action = "卖出"; trade_amount = current_amount; reason = "不在目标组合内，建议逐步调出"; priority = "高"

        if current_amount == 0 and target_amount > 0:
            action = "买入"; trade_amount = target_amount; reason = "目标组合新增基金"; priority = "高"

        rows.append({
            "基金代码": code, "基金名称": t.get("name") or c.get("name") or code,
            "资产类别": t.get("asset_class", "非目标持仓"),
            "当前金额": current_amount, "目标金额": target_amount,
            "当前比例": current_weight, "目标比例": target_weight, "偏离比例": drift,
            "交易方向": action, "建议交易金额": trade_amount, "优先级": priority,
            "浮盈亏": pnl, "浮盈亏比例": pnl_ratio, "原因": reason,
        })

    return pd.DataFrame(rows).sort_values(["优先级", "交易方向"], ascending=[True, True])


def summarize_rebalance(plan: pd.DataFrame) -> dict:
    if plan is None or plan.empty:
        return {"buy_total": 0.0, "sell_total": 0.0, "watch_count": 0, "hold_count": 0, "trade_count": 0, "cash_gap": 0.0}
    buy_total = plan.loc[plan["交易方向"] == "买入", "建议交易金额"].sum()
    sell_total = plan.loc[plan["交易方向"] == "卖出", "建议交易金额"].sum()
    return {
        "buy_total": float(buy_total), "sell_total": float(sell_total),
        "watch_count": int((plan["交易方向"] == "观察").sum()),
        "hold_count": int((plan["交易方向"] == "保留").sum()),
        "trade_count": int(plan["交易方向"].isin(["买入", "卖出"]).sum()),
        "cash_gap": float(buy_total - sell_total),
    }


def build_execution_batches(plan: pd.DataFrame, batch_count: int = 4) -> pd.DataFrame:
    if plan is None or plan.empty:
        return pd.DataFrame(columns=["批次", "基金代码", "基金名称", "交易方向", "本批金额", "执行条件"])

    rows = []
    trades = plan[plan["交易方向"].isin(["买入", "卖出"]) & (plan["建议交易金额"] > 0)].copy()
    for _, r in trades.iterrows():
        for b in range(1, batch_count + 1):
            condition = "按周/月定投执行；若市场快速上涨，不追高加速" if r["交易方向"] == "买入" else "按批调出；若持仓波动较大，优先卖出偏离度最高部分"
            rows.append({"批次": f"第{b}批", "基金代码": r["基金代码"], "基金名称": r["基金名称"], "交易方向": r["交易方向"], "本批金额": float(r["建议交易金额"]) / batch_count, "执行条件": condition})
    return pd.DataFrame(rows)


def save_version_snapshot(output_dir: str | Path, client_summary: dict, allocation: dict, recommendations: pd.DataFrame, rebalance_plan: pd.DataFrame, notes: list[str] | None = None) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"recommendation_snapshot_{ts}.json"
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "client_summary": client_summary, "allocation": allocation,
        "recommendations": recommendations.to_dict(orient="records") if recommendations is not None else [],
        "rebalance_plan": rebalance_plan.to_dict(orient="records") if rebalance_plan is not None else [],
        "notes": notes or [],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def list_snapshots(output_dir: str | Path) -> list[Path]:
    output_dir = Path(output_dir)
    if not output_dir.exists():
        return []
    return sorted(output_dir.glob("recommendation_snapshot_*.json"), reverse=True)


def load_snapshot(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
