# 基金数据刷新设计

开放式基金净值通常是日频更新；ETF 和指数可接入盘中行情。
演示版从本地 CSV 刷新，生产版替换 LicensedVendorFundQuoteProvider。
定时刷新命令：python jobs/refresh_data.py
