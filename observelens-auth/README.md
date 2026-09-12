# ObserveLens Auth

ObserveLens 的多租户认证授权服务。它使用 PostgreSQL 保存用户、租户、成员关系、会话刷新令牌与服务账号；业务服务通过 JWT 中的 `tenant_id`、角色与权限进行数据隔离和鉴权。

## 快速开始

```bash
cd observelens-auth
cp .env.example .env
docker compose up -d postgres
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn observelens_auth.main:app --reload --port 9081
```

默认启动账号为 `admin` / `observelens`，仅适用于本地开发。生产环境必须设置强随机的 `AUTH_JWT_SECRET` 并替换默认管理员密码。

如果数据库已按旧密码初始化，修改 `.env` 后执行 `make reset-admin-password` 以更新已有 `admin` 的密码；该命令不会删除任何数据。

服务启动时会幂等地创建默认角色、默认租户和启动管理员。Swagger UI 位于 `/docs`，ReDoc 位于 `/redoc`，OpenAPI JSON 位于 `/openapi.json`，健康检查位于 `/healthz`。

本地启动时，先执行 `make db-up` 启动 PostgreSQL；`.env.example` 连接到 Docker 暴露的 `localhost:5433`。使用 `docker compose up --build` 启动完整栈时，认证服务会通过 Compose 内部地址 `postgres:5432` 连接数据库。

## 配置

| 变量 | 说明 |
| --- | --- |
| `AUTH_DATABASE_URL` | SQLAlchemy 异步 PostgreSQL 连接串 |
| `AUTH_JWT_SECRET` | JWT HS256 签名密钥，至少 32 字符 |
| `AUTH_ACCESS_TOKEN_EXPIRE_MINUTES` | Access Token 有效分钟数，默认 30 |
| `AUTH_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token 有效天数，默认 14 |
| `AUTH_BOOTSTRAP_*` | 初始化默认租户和管理员的开发配置 |

## 认证约定

- JWT access token 放在 `Authorization: Bearer <token>` 中，包含 `tenant_id`、`user_id`、`role`、`permissions` 和 `jti`。
- Refresh token 仅在数据库中保存 SHA-256 哈希；刷新时会撤销旧会话并签发新的 token 对。
- 退出、禁用用户、禁用成员或变更角色后，`/api/v1/auth/verify-token` 会依据数据库实时状态拒绝旧 token 或返回最新权限。
- 服务账号令牌使用 `olsa_` 前缀且仅展示一次；请求中同样使用 Bearer 令牌。

## 数据库迁移

```bash
uv run alembic upgrade head
uv run alembic downgrade -1
```

## OpenAPI 文档

启动服务后访问 `http://localhost:9081/docs` 查看交互式 Swagger UI。提交静态 OpenAPI 文档前执行：

```bash
make openapi
```

该命令生成 `docs/openapi.json`，不会连接数据库或执行应用启动逻辑。
