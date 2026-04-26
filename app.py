
from __future__ import annotations

import json
import pandas as pd
import streamlit as st

from fund_advisor.data_provider import LocalCSVFundDataProvider
from fund_advisor.models import ClientProfile
from fund_advisor.engine import recommend_portfolio
from fund_advisor.suitability import attach_suitability
from fund_advisor.lookthrough import industry_exposure, lookthrough_warnings, brand_exposure, manager_exposure, holding_overlap
from fund_advisor.rebalance import (
    normalize_current_holdings, recommendations_to_targets, build_rebalance_plan,
    summarize_rebalance, build_execution_batches
)
from fund_advisor.family_assessment import FamilyProfile, assess_family, family_risk_to_allocation, money_buckets
from fund_advisor.scenario import stress_test, goal_projection
from fund_advisor.explanation import explain_allocation, explain_rebalance, likely_client_questions
from fund_advisor.privacy import PRIVACY_STATEMENT
from fund_advisor.fund_preferences import (
    load_bank_recommendations, score_by_preferences, preference_summary, bank_recommendation_view
)


st.set_page_config(page_title="家庭资产小管家 v9", page_icon="🏡", layout="wide")

st.title("🏡 家庭资产小管家 v9")
st.caption("友好、私密、本地优先。新增题材偏好、基金公司品牌和银行推荐信息。")

st.info(PRIVACY_STATEMENT)

provider = LocalCSVFundDataProvider("data")
master = provider.fund_master()
holdings_df = provider.holdings()
companies = sorted(master["company"].unique().tolist())
themes = sorted(master["theme"].unique().tolist())
bank_recs = load_bank_recommendations("data")
banks = sorted(bank_recs["bank"].dropna().unique().tolist()) if not bank_recs.empty else []

if "family_profile" not in st.session_state:
    st.session_state.family_profile = FamilyProfile()
if "current_holdings" not in st.session_state:
    st.session_state.current_holdings = pd.read_csv("data/current_holdings_sample.csv")
if "fund_preferences" not in st.session_state:
    st.session_state.fund_preferences = {
        "theme_preferences": ["宽基", "红利", "债券", "黄金"],
        "brand_preferences": [],
        "bank_preferences": [],
        "must_be_bank_recommended": False,
        "exclude_themes": [],
        "exclude_brands": [],
    }

tabs = st.tabs([
    "我的家庭",
    "安全体检",
    "三笔钱规划",
    "基金偏好",
    "基金组合",
    "调整建议",
    "情景模拟",
    "我的记录",
    "小程序与发布",
])

with tabs[0]:
    st.subheader("我的家庭信息")
    st.write("这里不需要输入姓名、手机号等敏感信息。可以用“我家”“父母家”“教育金账户”等昵称。")

    p = st.session_state.family_profile
    col1, col2, col3 = st.columns(3)
    with col1:
        p.family_name = st.text_input("家庭昵称", value=p.family_name)
        p.adults = st.number_input("成年人数量", min_value=1, max_value=6, value=p.adults)
        p.children = st.number_input("子女数量", min_value=0, max_value=6, value=p.children)
        p.elders = st.number_input("需赡养老人数", min_value=0, max_value=8, value=p.elders)
        p.city = st.text_input("所在城市，可不填", value=p.city)
    with col2:
        p.annual_income = st.number_input("家庭年收入", min_value=0.0, value=float(p.annual_income), step=10000.0)
        p.annual_expense = st.number_input("家庭年支出", min_value=0.0, value=float(p.annual_expense), step=10000.0)
        p.investable_assets = st.number_input("可用于投资的钱", min_value=0.0, value=float(p.investable_assets), step=10000.0)
        p.cash = st.number_input("现金/活期/货币基金", min_value=0.0, value=float(p.cash), step=10000.0)
    with col3:
        p.debt = st.number_input("贷款余额", min_value=0.0, value=float(p.debt), step=10000.0)
        p.annual_debt_payment = st.number_input("年度还款额", min_value=0.0, value=float(p.annual_debt_payment), step=10000.0)
        p.liquidity_need_3y = st.number_input("未来3年要用的钱", min_value=0.0, value=float(p.liquidity_need_3y), step=10000.0)
        p.horizon_years = st.slider("长期资金可投资几年", 1, 20, int(p.horizon_years))

    st.subheader("风险和目标")
    col4, col5 = st.columns(2)
    with col4:
        p.risk_preference = st.selectbox("我家的投资风格", ["保守型", "稳健型", "平衡型", "成长型", "进取型"], index=["保守型", "稳健型", "平衡型", "成长型", "进取型"].index(p.risk_preference))
        p.max_drawdown_tolerance = st.slider("最大能接受账户下跌", 0, 50, int(p.max_drawdown_tolerance * 100)) / 100
        p.emergency_months = p.cash / max(p.annual_expense / 12, 1)
    with col5:
        p.goal_education = st.checkbox("子女教育", value=p.goal_education)
        p.goal_retirement = st.checkbox("养老储备", value=p.goal_retirement)
        p.goal_house = st.checkbox("买房/改善住房", value=p.goal_house)
        p.goal_healthcare = st.checkbox("医疗与保障", value=p.goal_healthcare)
        p.goal_travel = st.checkbox("旅行与生活品质", value=p.goal_travel)

    st.session_state.family_profile = p

    st.subheader("当前持有的基金，可选")
    input_mode = st.radio("持仓输入方式", ["使用样例", "手动编辑", "上传CSV"], horizontal=True)
    current_df = st.session_state.current_holdings
    if input_mode == "上传CSV":
        uploaded = st.file_uploader("CSV 字段：code,name,amount,cost_amount", type=["csv"])
        if uploaded is not None:
            current_df = pd.read_csv(uploaded)
    elif input_mode == "手动编辑":
        current_df = st.data_editor(current_df, num_rows="dynamic", use_container_width=True, key="family_holdings_editor")
    st.session_state.current_holdings = current_df
    st.dataframe(current_df, use_container_width=True, hide_index=True)


family_profile = st.session_state.family_profile
assessment = assess_family(family_profile)
allocation = family_risk_to_allocation(family_profile)

client_profile = ClientProfile(
    investable_assets=family_profile.investable_assets,
    emergency_months=assessment["metrics"]["应急资金月数"],
    income_stability="一般",
    horizon_years=family_profile.horizon_years,
    liquidity_need_3y=family_profile.liquidity_need_3y,
    max_drawdown_tolerance=family_profile.max_drawdown_tolerance,
    risk_preference=family_profile.risk_preference,
    prefer_active=True,
    prefer_index=True,
    prefer_gold=True,
    need_overseas=True,
    brand_whitelist=[],
    brand_blacklist=[],
    theme_preferences=st.session_state.fund_preferences.get("theme_preferences", ["宽基", "红利", "债券", "黄金"]),
    excluded_themes=st.session_state.fund_preferences.get("exclude_themes", []),
)

engine_result = recommend_portfolio(provider, client_profile)

prefs = st.session_state.fund_preferences
preference_ranked_funds = score_by_preferences(
    engine_result["scored_funds"],
    theme_preferences=prefs.get("theme_preferences", []),
    brand_preferences=prefs.get("brand_preferences", []),
    bank_preferences=prefs.get("bank_preferences", []),
    bank_recommendations=bank_recs,
    must_be_bank_recommended=prefs.get("must_be_bank_recommended", False),
    exclude_themes=prefs.get("exclude_themes", []),
    exclude_brands=prefs.get("exclude_brands", []),
)

recommendations = attach_suitability(engine_result["recommendations"], master, family_profile.risk_preference)

# Render/Pandas may read fund codes as integers in one table and strings in another.
# Normalize both sides before merging preference information to avoid dtype mismatch.
if not recommendations.empty and "基金代码" in recommendations.columns:
    recommendations["基金代码"] = recommendations["基金代码"].astype(str).str.replace(r"\\.0$", "", regex=True).str.zfill(6)

if not recommendations.empty and not preference_ranked_funds.empty:
    pref_cols = ["code", "家庭综合分", "偏好加分", "偏好匹配说明", "推荐银行", "银行推荐理由", "银行标签"]
    pref_cols = [c for c in pref_cols if c in preference_ranked_funds.columns]
    pref_map = preference_ranked_funds[pref_cols].copy()
    pref_map["code"] = pref_map["code"].astype(str).str.replace(r"\\.0$", "", regex=True).str.zfill(6)
    pref_map = pref_map.rename(columns={"code": "基金代码"})
    recommendations = recommendations.merge(pref_map, on="基金代码", how="left")

industry_df = industry_exposure(recommendations, holdings_df)
look_notes = lookthrough_warnings(
    industry_df,
    brand_exposure(recommendations),
    manager_exposure(recommendations),
    holding_overlap(recommendations, holdings_df),
)

with tabs[1]:
    st.subheader("家庭安全体检")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("家庭健康分", f"{assessment['total_score']}/100")
    c2.metric("状态", assessment["health_level"])
    c3.metric("应急资金", f"{assessment['metrics']['应急资金月数']:.1f}个月")
    c4.metric("储蓄率", f"{assessment['metrics']['储蓄率']:.1%}")
    st.write(assessment["summary"])

    score_df = pd.DataFrame([{"项目": k, "得分": v} for k, v in assessment["score_parts"].items()])
    st.bar_chart(score_df.set_index("项目"))

    st.subheader("需要优先关注的地方")
    if assessment["risks"]:
        for r in assessment["risks"]:
            st.warning(r)
    else:
        st.success("没有发现明显的安全垫问题。可以进入长期资产配置。")

    st.subheader("家庭目标提示")
    st.dataframe(pd.DataFrame(assessment["goals"]), use_container_width=True, hide_index=True)


with tabs[2]:
    st.subheader("三笔钱规划")
    bucket_df = pd.DataFrame(money_buckets(family_profile, allocation))
    bucket_show = bucket_df.copy()
    bucket_show["建议金额"] = bucket_show["建议金额"].map(lambda x: f"{x:,.0f}")
    st.dataframe(bucket_show, use_container_width=True, hide_index=True)

    st.subheader("建议大类配置")
    alloc_df = pd.DataFrame([
        {"资产类别": k, "建议比例": v, "建议金额": v * family_profile.investable_assets}
        for k, v in allocation.items()
    ])
    show_alloc = alloc_df.copy()
    show_alloc["建议比例"] = show_alloc["建议比例"].map(lambda x: f"{x:.1%}")
    show_alloc["建议金额"] = show_alloc["建议金额"].map(lambda x: f"{x:,.0f}")
    st.dataframe(show_alloc, use_container_width=True, hide_index=True)

    st.subheader("每一类资产的作用")
    cards = explain_allocation(
        {
            "final_risk": family_profile.risk_preference,
            "liquidity_need_3y_ratio": family_profile.liquidity_need_3y / max(family_profile.investable_assets, 1),
        },
        allocation,
    )
    st.dataframe(pd.DataFrame(cards), use_container_width=True, hide_index=True)


with tabs[3]:
    st.subheader("基金偏好")
    st.write("可以告诉系统：家里更关心哪些题材、偏好哪些基金公司、是否参考某些银行推荐名单。")

    prefs = st.session_state.fund_preferences
    col1, col2 = st.columns(2)
    with col1:
        prefs["theme_preferences"] = st.multiselect("题材 / 资产主题偏好", themes, default=prefs.get("theme_preferences", []))
        prefs["exclude_themes"] = st.multiselect("不想配置的题材", themes, default=prefs.get("exclude_themes", []))
        prefs["brand_preferences"] = st.multiselect("偏好的基金公司品牌", companies, default=prefs.get("brand_preferences", []))
        prefs["exclude_brands"] = st.multiselect("不想选择的基金公司", companies, default=prefs.get("exclude_brands", []))
    with col2:
        prefs["bank_preferences"] = st.multiselect("参考哪些银行的推荐名单", banks, default=prefs.get("bank_preferences", []))
        prefs["must_be_bank_recommended"] = st.checkbox("只看银行推荐清单里的基金", value=prefs.get("must_be_bank_recommended", False))

    st.session_state.fund_preferences = prefs

    st.subheader("当前偏好如何影响选择")
    st.dataframe(pd.DataFrame(preference_summary(
        prefs["theme_preferences"],
        prefs["brand_preferences"],
        prefs["bank_preferences"],
        prefs["must_be_bank_recommended"],
    )), use_container_width=True, hide_index=True)

    st.subheader("银行推荐信息库")
    bank_view = bank_recommendation_view(bank_recs, master)
    if not bank_view.empty:
        st.dataframe(bank_view, use_container_width=True, hide_index=True)
    else:
        st.info("暂无银行推荐信息。可以在 data/bank_recommendations.csv 中维护。")


with tabs[4]:
    st.subheader("基金组合建议")
    st.write("银行推荐、题材偏好和品牌偏好只是筛选参考，最终仍要服从家庭安全垫、三笔钱规划和风险承受力。")

    st.subheader("按家庭偏好排序的候选基金池")
    if preference_ranked_funds.empty:
        st.warning("当前偏好条件下没有候选基金。可以放宽银行推荐或品牌限制。")
    else:
        pref_show = preference_ranked_funds.copy()
        keep_cols = [
            "code", "name", "company", "asset_class", "fund_type", "theme", "style",
            "score", "偏好加分", "家庭综合分", "推荐银行", "银行标签", "偏好匹配说明"
        ]
        keep_cols = [c for c in keep_cols if c in pref_show.columns]
        st.dataframe(pref_show[keep_cols].head(20), use_container_width=True, hide_index=True)

    st.subheader("建议组合")
    if recommendations.empty:
        st.warning("当前条件下没有生成基金候选。")
    else:
        show_rec = recommendations.copy()
        show_rec["目标比例"] = show_rec["目标比例"].map(lambda x: f"{x:.1%}")
        show_rec["配置金额"] = show_rec["配置金额"].map(lambda x: f"{x:,.0f}")
        for col in ["近1年", "最大回撤"]:
            if col in show_rec:
                show_rec[col] = show_rec[col].map(lambda x: "" if pd.isna(x) else f"{x:.1%}")
        if "夏普" in show_rec:
            show_rec["夏普"] = show_rec["夏普"].map(lambda x: "" if pd.isna(x) else f"{x:.2f}")
        st.dataframe(show_rec, use_container_width=True, hide_index=True)

    st.subheader("组合穿透提醒")
    if not industry_df.empty:
        idf = industry_df.copy()
        idf["组合穿透占比"] = idf["组合穿透占比"].map(lambda x: f"{x:.1%}")
        st.dataframe(idf, use_container_width=True, hide_index=True)
    if look_notes:
        for n in look_notes:
            st.warning(n)
    else:
        st.success("组合穿透后未发现明显集中风险。")


with tabs[5]:
    st.subheader("调整建议")
    try:
        current_df = normalize_current_holdings(st.session_state.current_holdings)
    except Exception as e:
        st.error(str(e))
        current_df = pd.DataFrame(columns=["code", "name", "amount", "cost_amount"])

    target_df = recommendations_to_targets(recommendations, family_profile.investable_assets)
    plan = build_rebalance_plan(
        current_holdings=current_df,
        target_holdings=target_df,
        total_assets=family_profile.investable_assets,
        min_trade_amount=5000,
        drift_threshold=0.02,
        sell_loss_control=True,
    )
    summary = summarize_rebalance(plan)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("建议买入", f"{summary['buy_total']:,.0f}")
    c2.metric("建议卖出", f"{summary['sell_total']:,.0f}")
    c3.metric("资金缺口", f"{summary['cash_gap']:,.0f}")
    c4.metric("观察项", summary["watch_count"])

    display_plan = plan.copy()
    for col in ["当前金额", "目标金额", "建议交易金额", "浮盈亏"]:
        if col in display_plan:
            display_plan[col] = display_plan[col].map(lambda x: f"{x:,.0f}")
    for col in ["当前比例", "目标比例", "偏离比例", "浮盈亏比例"]:
        if col in display_plan:
            display_plan[col] = display_plan[col].map(lambda x: f"{x:.1%}")
    st.dataframe(display_plan, use_container_width=True, hide_index=True)

    st.subheader("为什么这么调整")
    rebalance_cards = explain_rebalance(plan)
    if rebalance_cards:
        st.dataframe(pd.DataFrame(rebalance_cards), use_container_width=True, hide_index=True)

    st.subheader("分批执行建议")
    batches = build_execution_batches(plan, batch_count=4)
    if not batches.empty:
        display_batches = batches.copy()
        display_batches["本批金额"] = display_batches["本批金额"].map(lambda x: f"{x:,.0f}")
        st.dataframe(display_batches, use_container_width=True, hide_index=True)


with tabs[6]:
    st.subheader("情景模拟")
    stress = stress_test(allocation)
    show_stress = stress.copy()
    show_stress["组合估算收益/回撤"] = show_stress["组合估算收益/回撤"].map(lambda x: f"{x:.1%}")
    st.dataframe(show_stress, use_container_width=True, hide_index=True)

    st.subheader("长期目标模拟")
    col1, col2, col3 = st.columns(3)
    with col1:
        initial = st.number_input("初始投入", min_value=0.0, value=family_profile.investable_assets, step=10000.0)
    with col2:
        monthly = st.number_input("每月追加", min_value=0.0, value=5000.0, step=1000.0)
    with col3:
        expected = st.slider("假设年化收益", -5, 12, 4) / 100

    projection = goal_projection(initial, monthly, expected, family_profile.horizon_years)
    if not projection.empty:
        st.line_chart(projection.set_index("年份")["预计资产"])
        show_proj = projection.copy()
        show_proj["预计资产"] = show_proj["预计资产"].map(lambda x: f"{x:,.0f}")
        show_proj["累计投入"] = show_proj["累计投入"].map(lambda x: f"{x:,.0f}")
        st.dataframe(show_proj, use_container_width=True, hide_index=True)

    st.subheader("家人可能会问")
    st.dataframe(pd.DataFrame(likely_client_questions(family_profile.risk_preference)), use_container_width=True, hide_index=True)


with tabs[7]:
    st.subheader("我的记录")
    snapshot = {
        "family_profile": family_profile.__dict__,
        "assessment": assessment,
        "allocation": allocation,
        "fund_preferences": st.session_state.fund_preferences,
        "recommendations": recommendations.to_dict(orient="records"),
        "industry_exposure": industry_df.to_dict(orient="records"),
    }

    st.download_button(
        "下载我的家庭评估记录 JSON",
        data=json.dumps(snapshot, ensure_ascii=False, indent=2, default=str).encode("utf-8"),
        file_name="family_asset_assessment.json",
        mime="application/json",
    )

    uploaded_snapshot = st.file_uploader("导入之前保存的 JSON", type=["json"])
    if uploaded_snapshot is not None:
        try:
            data = json.loads(uploaded_snapshot.read().decode("utf-8"))
            profile_data = data.get("family_profile", {})
            st.session_state.family_profile = FamilyProfile(**{k: v for k, v in profile_data.items() if k in FamilyProfile.__dataclass_fields__})
            if "fund_preferences" in data:
                st.session_state.fund_preferences = data["fund_preferences"]
            st.success("已导入家庭评估记录。请刷新页面或切换标签查看。")
        except Exception as e:
            st.error(f"导入失败：{e}")

    st.subheader("家庭版产品原则")
    st.markdown("""
    - 不要求真实姓名和手机号  
    - 默认本地运行  
    - 不做销售话术  
    - 不承诺收益  
    - 银行推荐只是参考，不等于最终适合  
    - 先看安全垫，再看投资组合  
    - 先解释风险，再给调整建议  
    """)


with tabs[8]:
    st.subheader("小程序与发布方向")
    st.code("""
家庭版小程序建议页面：
1. 首页：家庭资产小管家
2. 我的家庭：收入、支出、可投资产、未来用钱
3. 安全体检：应急金、储蓄率、负债压力
4. 三笔钱：安心生活桶、三年目标桶、长期成长桶
5. 基金偏好：题材、品牌、银行推荐
6. 基金组合：大类配置和候选基金
7. 调整建议：保留、买入、卖出、观察
8. 我的记录：本地保存/云端同步可选
    """, language="text")

    st.subheader("家庭版基金选择逻辑")
    st.table(pd.DataFrame([
        {"层级": "第一层", "内容": "家庭安全垫", "说明": "应急金、负债、短期用钱优先"},
        {"层级": "第二层", "内容": "三笔钱规划", "说明": "安心生活、三年目标、长期成长"},
        {"层级": "第三层", "内容": "大类资产配置", "说明": "先定现金、债券、权益、黄金、海外比例"},
        {"层级": "第四层", "内容": "基金偏好", "说明": "题材、品牌、银行推荐只影响候选排序"},
        {"层级": "第五层", "内容": "基金组合", "说明": "结合评分、风险、穿透和偏好生成"},
    ]))
