from __future__ import annotations
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fund_advisor.cloud_store import init_db
from fund_advisor.fund_data_refresh import refresh_fund_quotes
from fund_advisor.market_environment import refresh_environment_snapshot

def main():
    init_db(); fund_rows=refresh_fund_quotes(data_dir=ROOT/'data'); env=refresh_environment_snapshot(family_risk='稳健型')
    print(f'refreshed_funds={len(fund_rows)}')
    print(f"environment_level={env.get('level')} score={env.get('score')}")
if __name__=='__main__': main()
