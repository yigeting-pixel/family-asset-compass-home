from __future__ import annotations
from datetime import datetime
from typing import Any
from .cloud_store import save_environment_snapshot

def sample_environment_payload() -> dict[str, Any]:
    indicators=[
        {'name':'权益估值温度','value':42,'unit':'0-100','direction':'neutral','explain':'估值处于中性偏低区域，长期资金可分批配置。'},
        {'name':'市场波动温度','value':58,'unit':'0-100','direction':'risk','explain':'波动略高，避免一次性重仓权益。'},
        {'name':'债券环境','value':55,'unit':'0-100','direction':'neutral','explain':'债券可作为三年目标桶和防守资产。'},
        {'name':'黄金分散价值','value':63,'unit':'0-100','direction':'positive','explain':'黄金仍可作为组合小比例分散工具。'},
        {'name':'海外资产分散价值','value':52,'unit':'0-100','direction':'neutral','explain':'海外资产适合长期分散，但需关注汇率波动。'},
    ]
    score=round(sum(i['value'] for i in indicators)/len(indicators),1)
    level='谨慎' if score<35 else '中性偏谨慎' if score<55 else '中性' if score<70 else '相对积极'
    return {'source':'sample_environment','updated_at':datetime.now().isoformat(timespec='seconds'),'score':score,'level':level,'indicators':indicators}

def generate_environment_advice(payload: dict[str, Any], family_risk: str='稳健型') -> list[dict[str,str]]:
    level=payload.get('level','中性'); score=float(payload.get('score',50)); advice=[]
    if score<45: advice.append({'建议主题':'总体仓位','建议':'保持防守，优先保证安心生活桶和三年目标桶，不建议提高权益仓位。','原因':f'当前外部环境为「{level}」。'})
    elif score<60: advice.append({'建议主题':'总体仓位','建议':'按目标配置分批执行，不追涨，不因短期波动大幅偏离计划。','原因':f'当前外部环境为「{level}」。'})
    else: advice.append({'建议主题':'总体仓位','建议':'长期资金可按计划分批配置权益和红利低波，但仍需控制行业主题比例。','原因':f'当前外部环境为「{level}」。'})
    if family_risk in ['保守型','稳健型']:
        advice.append({'建议主题':'家庭风险边界','建议':'权益和行业主题只取目标区间下沿，新增资金优先用定投或分批买入。','原因':f'家庭风险偏好为「{family_risk}」，不应被市场情绪带偏。'})
    else:
        advice.append({'建议主题':'家庭风险边界','建议':'可以保留成长资产配置，但行业主题和单只基金仍要设置上限。','原因':f'家庭风险偏好为「{family_risk}」，但家庭资产仍需分层管理。'})
    advice += [
        {'建议主题':'债券/现金','建议':'未来三年要用的钱仍以现金、短债和中短债为主。','原因':'短期目标不能承担权益市场回撤风险。'},
        {'建议主题':'黄金','建议':'黄金适合作为 3%-8% 的分散工具，不建议用作核心收益来源。','原因':'黄金主要承担分散和对冲功能。'},
        {'建议主题':'银行推荐信息','建议':'银行推荐名单只作为外部参考，最终仍按家庭目标、风险承受力和组合比例决定。','原因':'推荐名单不等同于适合每个家庭。'},
    ]
    return advice

def refresh_environment_snapshot(family_risk: str='稳健型') -> dict[str, Any]:
    payload=sample_environment_payload(); payload['advice']=generate_environment_advice(payload,family_risk)
    save_environment_snapshot(payload); return payload
