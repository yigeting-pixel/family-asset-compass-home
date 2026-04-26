# Render 云端版部署

使用 render.cloud.yaml 创建：
1. cloud_app.py 网页服务
2. api.cloud_main API 服务
3. jobs/refresh_data.py 定时刷新任务

三个服务都要配置同一个 DATABASE_URL。
