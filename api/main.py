
from __future__ import annotations

from typing import List, Optional
from pathlib import Path as _ApiPath

from fastapi import FastAPI
from pydantic import BaseModel

from fund_advisor.data_provider import LocalCSVFundDataProvider
from fund_advisor.models import ClientProfile
from fund_advisor.engine import recommend_portfolio
from fund_advisor.suitability import attach_suitability
from fund_advisor.lookthrough import industry_exposure, brand_exposure, manager_exposure, holding_overlap
from fund_advisor.scenario import stress_test


app = FastAPI(
    title="Family Asset Advisor Workbench API",
    version="0.6.0",
    description="家庭资产配置咨询工作台 API，供网页端和小程序端调用。",
)

provider = LocalCSVFundDataProvider(_ApiPath(__file__).resolve().parents[1] / "data")


class ClientProfileIn(BaseModel):
    investable_assets: float = 1000000
    emergency_months: float = 9
    income_stability: str = "一般"
    horizon_years: int = 5
    liquidity_need_3y: float = 200000
    max_drawdown_tolerance: float = 0.15
    risk_preference: str = "稳健型"
    prefer_active: bool = True
    prefer_index: bool = True
    prefer_gold: bool = True
    need_overseas: bool = True
    brand_whitelist: List[str] = []
    brand_blacklist: List[str] = []
    theme_preferences: List[str] = []
    excluded_themes: List[str] = []


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.6.0"}


@app.get("/funds")
def funds():
    master = provider.fund_master()
    return master.to_dict(orient="records")


@app.post("/consultation/recommend")
def recommend(profile_in: ClientProfileIn):
    profile = ClientProfile(**profile_in.model_dump())
    result = recommend_portfolio(provider, profile)
    recommendations = attach_suitability(result["recommendations"], provider.fund_master(), result["risk_level"])
    industry = industry_exposure(recommendations, provider.holdings())
    brand = brand_exposure(recommendations)
    manager = manager_exposure(recommendations)
    overlap = holding_overlap(recommendations, provider.holdings())
    stress = stress_test(result["allocation"])

    return {
        "risk_level": result["risk_level"],
        "allocation": result["allocation"],
        "recommendations": recommendations.to_dict(orient="records"),
        "industry_exposure": industry.to_dict(orient="records"),
        "brand_exposure": brand.to_dict(orient="records"),
        "manager_exposure": manager.to_dict(orient="records"),
        "holding_overlap": overlap.to_dict(orient="records"),
        "stress_test": stress.to_dict(orient="records"),
    }



# ----- v7 auth and approval endpoints -----
from fund_advisor.auth import create_demo_users, authenticate, list_users, permission_matrix
from fund_advisor.approval import submit_approval_request, list_approval_requests, update_approval_status
from fund_advisor.audit import log_event, list_audit_logs


class LoginIn(BaseModel):
    username: str
    password: str


class ApprovalIn(BaseModel):
    title: str = "家庭资产配置方案复核"
    client_id: Optional[int] = None
    consultation_id: Optional[int] = None
    submitter: str = ""
    proposal: dict = {}


class ApprovalDecisionIn(BaseModel):
    request_id: int
    status: str
    reviewer: str = ""
    review_comment: str = ""


@app.post("/auth/init-demo-users")
def api_init_demo_users():
    create_demo_users()
    return {"ok": True}


@app.post("/auth/login")
def api_login(payload: LoginIn):
    user = authenticate(payload.username, payload.password)
    if not user:
        return {"ok": False, "error": "invalid username or password"}
    log_event("auth.login", actor=payload.username, entity_type="user", entity_id=str(user["id"]))
    return {"ok": True, "user": user}


@app.get("/auth/users")
def api_users():
    return list_users()


@app.get("/auth/permissions")
def api_permissions():
    return permission_matrix()


@app.post("/approval/submit")
def api_submit_approval(payload: ApprovalIn):
    request_id = submit_approval_request(
        title=payload.title,
        proposal=payload.proposal,
        client_id=payload.client_id,
        consultation_id=payload.consultation_id,
        submitter=payload.submitter,
    )
    log_event("approval.submit", actor=payload.submitter, entity_type="approval_request", entity_id=str(request_id), payload=payload.proposal)
    return {"ok": True, "request_id": request_id}


@app.get("/approval/list")
def api_approval_list(status: Optional[str] = None):
    return list_approval_requests(status=status)


@app.post("/approval/decision")
def api_approval_decision(payload: ApprovalDecisionIn):
    update_approval_status(
        request_id=payload.request_id,
        status=payload.status,
        reviewer=payload.reviewer,
        review_comment=payload.review_comment,
    )
    log_event("approval.decision", actor=payload.reviewer, entity_type="approval_request", entity_id=str(payload.request_id), payload=payload.model_dump())
    return {"ok": True}


@app.get("/audit/logs")
def api_audit_logs(limit: int = 200):
    return list_audit_logs(limit=limit)



# ----- v8 family home endpoints -----
from fund_advisor.family_assessment import FamilyProfile, assess_family, family_risk_to_allocation, money_buckets


class FamilyProfileIn(BaseModel):
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


@app.post("/family/assess")
def family_assess(payload: FamilyProfileIn):
    profile = FamilyProfile(**payload.model_dump())
    assessment = assess_family(profile)
    allocation = family_risk_to_allocation(profile)
    buckets = money_buckets(profile, allocation)
    stress = stress_test(allocation)
    return {
        "assessment": assessment,
        "allocation": allocation,
        "buckets": buckets,
        "stress_test": stress.to_dict(orient="records"),
    }



# ----- v9 fund preference endpoint -----
from fund_advisor.fund_preferences import (
    load_bank_recommendations,
    score_by_preferences,
    bank_recommendation_view,
)


class FundPreferenceIn(BaseModel):
    theme_preferences: List[str] = []
    brand_preferences: List[str] = []
    bank_preferences: List[str] = []
    must_be_bank_recommended: bool = False
    exclude_themes: List[str] = []
    exclude_brands: List[str] = []


@app.post("/family/fund-preferences")
def family_fund_preferences(payload: FundPreferenceIn):
    profile = ClientProfile(
        investable_assets=1000000,
        emergency_months=9,
        income_stability="一般",
        horizon_years=5,
        liquidity_need_3y=200000,
        max_drawdown_tolerance=0.15,
        risk_preference="稳健型",
        prefer_active=True,
        prefer_index=True,
        prefer_gold=True,
        need_overseas=True,
        brand_whitelist=[],
        brand_blacklist=[],
        theme_preferences=payload.theme_preferences,
        excluded_themes=payload.exclude_themes,
    )
    result = recommend_portfolio(provider, profile)
    bank_recs = load_bank_recommendations(_ApiPath(__file__).resolve().parents[1] / "data")
    ranked = score_by_preferences(
        result["scored_funds"],
        theme_preferences=payload.theme_preferences,
        brand_preferences=payload.brand_preferences,
        bank_preferences=payload.bank_preferences,
        bank_recommendations=bank_recs,
        must_be_bank_recommended=payload.must_be_bank_recommended,
        exclude_themes=payload.exclude_themes,
        exclude_brands=payload.exclude_brands,
    )
    return {
        "ranked_funds": ranked.to_dict(orient="records"),
        "bank_recommendations": bank_recommendation_view(bank_recs, provider.fund_master()).to_dict(orient="records"),
    }
