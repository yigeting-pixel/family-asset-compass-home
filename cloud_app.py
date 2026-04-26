from __future__ import annotations
import pandas as pd
import streamlit as st
from fund_advisor.cloud_store import init_db, save_family_state, load_latest_family_state, latest_fund_snapshots, latest_environment_snapshot
from fund_advisor.fund_data_refresh import refresh_fund_quotes
from fund_advisor.market_environment import refresh_environment_snapshot, generate_environment_advice
from fund_advisor.family_assessment import FamilyProfile, assess_family

st.set_page_config(page_title='家庭资产小管家 Cloud v13', page_icon='☁️', layout='wide')
st.title('☁️ 家庭资产小管家 Cloud v13')
st.caption('云端同步、基金数据刷新、外部环境建议。生产环境请配置 DATABASE_URL。')
try:
    init_db(); st.success('数据库连接正常。未配置 DATABASE_URL 时使用本地 SQLite，仅适合开发演示。')
except Exception as e: st.error(f'数据库初始化失败：{e}')

tabs=st.tabs(['云端同步','基金数据刷新','外部环境建议','部署说明'])
with tabs[0]:
    st.subheader('家庭记录云端同步')
    family_key=st.text_input('家庭同步码', value='demo-family-key', type='password')
    family_label=st.text_input('家庭昵称', value='我的家庭')
    c1,c2=st.columns(2)
    with c1:
        income_wan=st.number_input('家庭年收入（万元）', min_value=0.0, value=60.0, step=1.0)
        expense_wan=st.number_input('家庭年支出（万元）', min_value=0.0, value=30.0, step=1.0)
        investable_wan=st.number_input('可投资资产（万元）', min_value=0.0, value=100.0, step=1.0)
    with c2:
        cash_wan=st.number_input('现金/活期/货币基金（万元）', min_value=0.0, value=15.0, step=1.0)
        need_3y_wan=st.number_input('未来3年要用的钱（万元）', min_value=0.0, value=20.0, step=1.0)
        risk=st.selectbox('风险偏好', ['保守型','稳健型','平衡型','成长型','进取型'], index=1)
    profile=FamilyProfile(family_name=family_label, annual_income=income_wan*10000, annual_expense=expense_wan*10000, investable_assets=investable_wan*10000, cash=cash_wan*10000, liquidity_need_3y=need_3y_wan*10000, risk_preference=risk)
    assessment=assess_family(profile)
    payload={'family_profile':profile.__dict__,'assessment':assessment,'unit':'yuan_internal_wan_ui'}
    m1,m2,m3=st.columns(3); m1.metric('家庭健康分',f"{assessment['total_score']}/100"); m2.metric('状态',assessment['health_level']); m3.metric('应急资金',f"{assessment['metrics']['应急资金月数']:.1f}个月")
    if st.button('保存到云端'):
        st.success(f"已保存云端记录：#{save_family_state(family_key,payload,family_label=family_label)}") if family_key.strip() else st.error('请输入家庭同步码。')
    if st.button('读取最新云端记录'):
        item=load_latest_family_state(family_key); st.json(item) if item else st.warning('没有找到记录。')
with tabs[1]:
    st.subheader('基金数据刷新')
    codes_text=st.text_input('基金代码，逗号分隔；留空表示刷新全部样例基金', value='')
    codes=[x.strip() for x in codes_text.split(',') if x.strip()]
    if st.button('手动刷新基金数据'):
        rows=refresh_fund_quotes(codes=codes,data_dir='data'); st.success(f'已刷新 {len(rows)} 条基金数据'); st.dataframe(pd.DataFrame(rows), use_container_width=True)
    latest=latest_fund_snapshots(limit=100); st.dataframe(pd.DataFrame(latest), use_container_width=True) if latest else st.info('暂无基金快照。')
with tabs[2]:
    st.subheader('外部环境建议')
    family_risk=st.selectbox('家庭风险偏好', ['保守型','稳健型','平衡型','成长型','进取型'], index=1, key='env_risk')
    if st.button('刷新外部环境'):
        payload=refresh_environment_snapshot(family_risk=family_risk); st.success('已刷新外部环境。'); st.json(payload)
    latest_env=latest_environment_snapshot()
    if latest_env:
        payload=latest_env['payload']; st.metric('环境等级', payload.get('level','')); st.metric('环境分数', payload.get('score',''))
        st.dataframe(pd.DataFrame(payload.get('indicators',[])), use_container_width=True)
        st.subheader('建议'); st.dataframe(pd.DataFrame(payload.get('advice', generate_environment_advice(payload,family_risk))), use_container_width=True)
    else: st.info('暂无环境快照。点击刷新生成。')
with tabs[3]:
    st.subheader('部署说明')
    st.markdown('''
1. 配置 `DATABASE_URL`，使用 Postgres/Supabase/Neon/Render Postgres。  
2. 使用 Render Cron Job 定时执行 `python jobs/refresh_data.py`。  
3. 基金数据供应商替换 `LicensedVendorFundQuoteProvider`。  
4. 小程序端调用 FastAPI，不直接访问数据库。  
5. 不要把真实姓名、手机号、身份证、银行卡作为同步码。  
''')
