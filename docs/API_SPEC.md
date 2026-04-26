# API Spec

## Health

GET /health

## Fund List

GET /funds

## Consultation Recommend

POST /consultation/recommend

Request:

```json
{
  "investable_assets": 1000000,
  "emergency_months": 9,
  "income_stability": "一般",
  "horizon_years": 5,
  "liquidity_need_3y": 200000,
  "max_drawdown_tolerance": 0.15,
  "risk_preference": "稳健型",
  "prefer_active": true,
  "prefer_index": true,
  "prefer_gold": true,
  "need_overseas": true,
  "brand_whitelist": [],
  "brand_blacklist": [],
  "theme_preferences": ["宽基", "红利"],
  "excluded_themes": []
}
```

Response includes:

- risk_level
- allocation
- recommendations
- industry_exposure
- brand_exposure
- manager_exposure
- holding_overlap
- stress_test
