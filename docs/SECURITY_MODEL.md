# Security Model

## Roles

- advisor: 客户建档、咨询、提交方案
- supervisor: 顾问权限 + 方案复核
- risk: 风控复核、风险检查
- admin: 全部权限

## Demo Users

- advisor / advisor123
- supervisor / supervisor123
- risk / risk123
- admin / admin123

## Production Requirements

- Replace demo login with real authentication
- Use HTTPS only
- Store password hashes with strong algorithms such as bcrypt or Argon2
- Add session expiration
- Add rate limiting
- Add audit logging for all sensitive actions
- Add row-level tenant isolation if SaaS
