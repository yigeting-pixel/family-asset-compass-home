from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol
import pandas as pd
from .cloud_store import save_fund_snapshot

@dataclass
class FundQuote:
    code: str; name: str; nav: float; nav_date: str; source: str; extra: dict
class FundQuoteProvider(Protocol):
    def fetch_quotes(self, codes: list[str]) -> list[FundQuote]: ...

def normalize_code(value) -> str:
    return str(value).replace('.0','').zfill(6)

class LocalCsvFundQuoteProvider:
    def __init__(self, data_dir: str | Path = 'data'):
        self.data_dir=Path(data_dir)
    def fetch_quotes(self, codes: list[str]) -> list[FundQuote]:
        nav=pd.read_csv(self.data_dir/'nav.csv', dtype={'code':'string'})
        master=pd.read_csv(self.data_dir/'fund_master.csv', dtype={'code':'string'})
        nav['code']=nav['code'].map(normalize_code); master['code']=master['code'].map(normalize_code)
        latest=nav.sort_values('date').groupby('code', as_index=False).tail(1).merge(master[['code','name']], on='code', how='left')
        codes=[normalize_code(c) for c in codes] if codes else latest['code'].tolist()
        latest=latest[latest['code'].isin(codes)]
        return [FundQuote(str(r['code']), r.get('name',r['code']), float(r['nav']), str(r['date']), 'local_csv_demo', {'note':'样例净值；生产环境请替换为授权数据源'}) for _,r in latest.iterrows()]

class LicensedVendorFundQuoteProvider:
    def __init__(self, api_key: str = '', base_url: str = ''):
        self.api_key=api_key; self.base_url=base_url
    def fetch_quotes(self, codes: list[str]) -> list[FundQuote]:
        raise NotImplementedError('请接入正式授权数据源。开放式基金净值通常为日频更新；ETF 可接入盘中行情。')

def refresh_fund_quotes(codes: list[str] | None = None, data_dir: str | Path = 'data') -> list[dict]:
    provider=LocalCsvFundQuoteProvider(data_dir=data_dir)
    rows=[]
    for q in provider.fetch_quotes(codes or []):
        row={'code':q.code,'name':q.name,'nav':q.nav,'nav_date':q.nav_date,'source':q.source,'extra':q.extra,'refreshed_at':datetime.now().isoformat(timespec='seconds')}
        save_fund_snapshot(row); rows.append(row)
    return rows
