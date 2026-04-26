from __future__ import annotations

import numpy as np
import pandas as pd


def max_drawdown(nav: pd.Series) -> float:
    if len(nav) == 0:
        return 0.0
    peak = nav.cummax()
    dd = nav / peak - 1
    return float(dd.min())


def calc_nav_metrics(nav_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for code, g in nav_df.groupby("code"):
        g = g.sort_values("date")
        nav = g["nav"].astype(float).reset_index(drop=True)
        if len(nav) < 30:
            continue

        ret = nav.pct_change().dropna()
        total_ret = nav.iloc[-1] / nav.iloc[0] - 1
        years = max(len(ret) / 252, 1 / 252)
        ann_ret = (nav.iloc[-1] / nav.iloc[0]) ** (1 / years) - 1
        vol = ret.std() * np.sqrt(252)
        sharpe = (ann_ret - 0.02) / vol if vol and vol > 0 else 0
        mdd = max_drawdown(nav)
        calmar = ann_ret / abs(mdd) if mdd < 0 else 0

        def p_ret(days: int) -> float:
            if len(nav) <= days:
                return np.nan
            return nav.iloc[-1] / nav.iloc[-1 - days] - 1

        rows.append({
            "code": code,
            "latest_nav": nav.iloc[-1],
            "total_return": total_ret,
            "annual_return": ann_ret,
            "volatility": vol,
            "max_drawdown": mdd,
            "sharpe": sharpe,
            "calmar": calmar,
            "ret_1m": p_ret(21),
            "ret_3m": p_ret(63),
            "ret_6m": p_ret(126),
            "ret_1y": p_ret(252),
            "ret_3y": p_ret(756),
            "positive_day_ratio": float((ret > 0).mean()),
        })
    return pd.DataFrame(rows)


def portfolio_nav(nav_df: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    wide = nav_df.pivot(index="date", columns="code", values="nav").sort_index().ffill().dropna()
    codes = [c for c in weights if c in wide.columns]
    if not codes:
        return pd.DataFrame(columns=["date", "nav"])
    sub = wide[codes]
    norm = sub / sub.iloc[0]
    w = np.array([weights[c] for c in codes], dtype=float)
    w = w / w.sum()
    pnav = norm.values @ w
    return pd.DataFrame({"date": norm.index, "nav": pnav})


def correlation_matrix(nav_df: pd.DataFrame, codes: list[str]) -> pd.DataFrame:
    wide = nav_df[nav_df["code"].isin(codes)].pivot(index="date", columns="code", values="nav").sort_index().ffill().dropna()
    ret = wide.pct_change().dropna()
    return ret.corr()
