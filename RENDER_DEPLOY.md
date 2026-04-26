# Render 发布步骤

本项目已经包含 `render.yaml`，可以用 Render Blueprint 一次性创建两个服务：

- family-asset-compass-home：Streamlit 家庭版网页
- family-asset-compass-api：FastAPI 后端接口

## 方式一：Blueprint 部署

1. 先把项目发布到 GitHub
2. 打开 Render
3. New → Blueprint
4. 选择 GitHub 仓库：family-asset-compass-home
5. Render 会读取 `render.yaml`
6. 创建服务
7. 等待 Build 和 Deploy 完成

部署完成后，Render 会给你两个地址。实际域名以 Render 页面显示为准：

```text
https://family-asset-compass-home.onrender.com
https://family-asset-compass-api.onrender.com
```

## 方式二：只部署 Streamlit 网页

Render 新建 Web Service：

```text
Runtime: Python
Build Command: pip install -r requirements.txt
Start Command: streamlit run app.py --server.address 0.0.0.0 --server.port $PORT
```

环境变量：

```text
PYTHON_VERSION=3.11.9
```

## 方式三：只部署 FastAPI

Render 新建 Web Service：

```text
Runtime: Python
Build Command: pip install -r requirements.txt
Start Command: uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

环境变量：

```text
PYTHON_VERSION=3.11.9
```

API 文档地址：

```text
https://你的-api-服务地址/docs
```

## 注意

当前版本使用样例数据，适合演示和产品验证。正式公开发布前，需要补充：

- 隐私政策
- 用户协议
- 风险提示
- 数据来源说明
- 不构成投资建议声明
