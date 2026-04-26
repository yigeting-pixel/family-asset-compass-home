# Deployment

## 本地顾问工作台

```bash
pip install -r requirements.txt
streamlit run app.py
```

## API 服务

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## 生产部署建议

- 后端：FastAPI + Gunicorn/Uvicorn
- 数据库：PostgreSQL
- 文件存储：对象存储
- 网关：Nginx
- HTTPS：必须
- 任务调度：每日基金数据同步
- 日志：推荐结果与用户操作留痕
