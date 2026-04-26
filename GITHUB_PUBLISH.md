# GitHub 发布步骤

建议仓库名：

```text
family-asset-compass-home
```

## 方法一：命令行发布

进入解压后的项目目录，执行：

```bash
git init
git add .
git commit -m "Initial release: family asset compass home"
git branch -M main
git remote add origin https://github.com/yigeting-pixel/family-asset-compass-home.git
git push -u origin main
```

如果远程仓库已经存在，直接执行：

```bash
git remote add origin https://github.com/yigeting-pixel/family-asset-compass-home.git
git push -u origin main
```

如果提示 remote 已存在：

```bash
git remote set-url origin https://github.com/yigeting-pixel/family-asset-compass-home.git
git push -u origin main
```

## 方法二：GitHub 网页上传

1. 在 GitHub 创建新仓库：family-asset-compass-home
2. 选择 Public 或 Private
3. 不要勾选自动生成 README
4. 点击 upload files
5. 上传本项目全部文件
6. Commit changes

## 建议仓库描述

```text
A friendly, private-first family asset allocation assessment tool with household safety check, money buckets, fund preferences, bank recommendations, and Streamlit/FastAPI deployment support.
```

## 建议 Topics

```text
asset-allocation
family-finance
streamlit
fastapi
fund-analysis
portfolio
wealth-management
render
mini-program
```
