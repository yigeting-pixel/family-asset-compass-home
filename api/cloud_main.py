from __future__ import annotations
from typing import Any
from fastapi import FastAPI
from pydantic import BaseModel
from fund_advisor.cloud_store import init_db, save_family_state, load_latest_family_state, latest_fund_snapshots, latest_environment_snapshot
from fund_advisor.fund_data_refresh import refresh_fund_quotes
from fund_advisor.market_environment import refresh_environment_snapshot
app=FastAPI(title='Family Asset Compass Cloud API', version='0.13.0')
class FamilySyncIn(BaseModel): family_key: str; family_label: str=''; payload: dict[str,Any]
class FundRefreshIn(BaseModel): codes: list[str]=[]
class EnvironmentRefreshIn(BaseModel): family_risk: str='稳健型'
@app.on_event('startup')
def startup(): init_db()
@app.get('/cloud/health')
def health(): return {'ok':True,'service':'family-asset-compass-cloud','version':'0.13.0'}
@app.post('/cloud/family/save')
def save_family(payload: FamilySyncIn): return {'ok':True,'id':save_family_state(payload.family_key,payload.payload,family_label=payload.family_label)}
@app.get('/cloud/family/latest')
def load_family(family_key: str):
    item=load_latest_family_state(family_key); return {'ok':bool(item),'data':item}
@app.post('/cloud/funds/refresh')
def refresh_funds(payload: FundRefreshIn):
    rows=refresh_fund_quotes(codes=payload.codes,data_dir='data'); return {'ok':True,'count':len(rows),'rows':rows}
@app.get('/cloud/funds/latest')
def latest_funds(limit: int=100): return {'ok':True,'rows':latest_fund_snapshots(limit=limit)}
@app.post('/cloud/environment/refresh')
def refresh_environment(payload: EnvironmentRefreshIn): return {'ok':True,'environment':refresh_environment_snapshot(family_risk=payload.family_risk)}
@app.get('/cloud/environment/latest')
def latest_environment(): return {'ok':True,'environment':latest_environment_snapshot()}
