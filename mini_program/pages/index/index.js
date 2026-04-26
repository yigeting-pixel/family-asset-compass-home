Page({
  data: {
    apiBase: "https://your-domain.example.com",
    result: null
  },
  requestAssessment() {
    wx.request({
      url: this.data.apiBase + "/family/assess",
      method: "POST",
      data: {
        family_name: "我的家庭",
        annual_income: 600000,
        annual_expense: 300000,
        investable_assets: 1000000,
        cash: 150000,
        liquidity_need_3y: 200000,
        horizon_years: 5,
        max_drawdown_tolerance: 0.12,
        risk_preference: "稳健型",
        goal_education: true,
        goal_retirement: true
      },
      success: (res) => {
        this.setData({ result: res.data })
      }
    })
  }
})
