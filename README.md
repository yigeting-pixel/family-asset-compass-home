# 家庭资产小管家 Home v9

一个友好、私密、本地优先的家庭资产配置评估工具。

v9 新增了基金选择偏好模块：

- 题材偏好
- 不想配置的题材
- 基金公司品牌偏好
- 排除基金公司
- 银行推荐名单
- 只看银行推荐清单开关
- 家庭综合分：基础评分 + 偏好加分
- 银行推荐信息库

## 核心流程

```text
我的家庭
  ↓
安全体检
  ↓
三笔钱规划
  ↓
基金偏好：题材 / 品牌 / 银行推荐
  ↓
基金组合方向
  ↓
调整建议
  ↓
情景模拟
  ↓
我的记录
```

## 启动

Windows 解压后双击：

```text
START_HERE.bat
```

或手动运行：

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 银行推荐数据

维护文件：

```text
data/bank_recommendations.csv
```

字段：

```text
bank,channel,code,recommend_level,recommend_reason,suitable_for,bank_tag
```

注意：银行推荐只是信息来源，不等于最终适合本家庭。

## API

启动 API：

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

新增接口：

```text
POST /family/fund-preferences
```

## 隐私原则

- 不要求真实姓名
- 不要求手机号
- 默认本地运行
- 可导出/导入自己的评估记录
- 不承诺收益
- 不做销售话术


## Render 部署

本项目已经包含：

```text
render.yaml
Procfile
.python-version
.streamlit/config.toml
```

推荐用 Render Blueprint 部署。详细步骤见：

```text
RENDER_DEPLOY.md
```

## GitHub 发布

详细步骤见：

```text
GITHUB_PUBLISH.md
```
