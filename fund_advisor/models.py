from dataclasses import dataclass
from typing import List

@dataclass
class ClientProfile:
    investable_assets: float
    emergency_months: float
    income_stability: str
    horizon_years: int
    liquidity_need_3y: float
    max_drawdown_tolerance: float
    risk_preference: str
    prefer_active: bool
    prefer_index: bool
    prefer_gold: bool
    need_overseas: bool
    brand_whitelist: List[str]
    brand_blacklist: List[str]
    theme_preferences: List[str]
    excluded_themes: List[str]
