# ObserveLens Auth

## 设计目标

- 支持多租户：一个 user 可加入多个 tenant
- 登录后必须处于一个当前 tenant
- 所有业务数据按 tenant_id 隔离
- 权限由 tenant_member.role 决定
- 网关做统一入口，业务服务负责 JWT 校验和权限判断


## 核心模型

```
tenant
  id
  name
  display_name
  status
  created_at
  updated_at

user
  id
  name
  password_hash
  display_name
  email
  status
  created_at
  updated_at

role
  id
  name
  display_name
  permissions_json
  created_at
  updated_at

tenant_members
  id
  tenant_id
  user_id
  role_id
  status
  created_at
  updated_at

session_token
  id
  user_id
  tenant_id
  access_token_jti
  refresh_token_hash
  status
  ip_address
  created_at
  expires_at
  revoked_at

service_account
  id
  name
  description
  tenant_id
  role_id
  status
  token_hash
  token_prefix
  last_used_at
  expires_at
  revoked_at
  created_by_user_id
  created_at
  updated_at
```


## 角色定义

| 角色 | 定位 | 说明 |
|---|---|---|
| `admin` | 租户管理员 | 管理租户成员、系统配置、集成、知识库    |
| `editor` | 编辑者   | 查看数据、执行诊断、处理事件、维护知识库 |
| `viewer` | 只读用户 | 查看 Trace、指标、日志、拓扑、事件和知识库 |


## 权限集合

```
integration:read
integration:create
integration:update
integration:delete

incident:read
incident:create
incident:update
incident:delete

...
```


## 角色权限矩阵

| 权限 | admin | editor | viewer |
|---|---:|---:|---:|
| `integration:read` | Y | Y | Y |
| `integration:create` | Y | N | N |
| `integration:update` | Y | N | N |
| `integration:delete` | Y | N | N |
| `incident:read` | Y | Y | Y |
| `incident:create` | Y | Y | N |
| `incident:update` | Y | Y | N |
| `incident:delete` | Y | N | N |


## Token 设计

access_token 使用 JWT，短有效期；refresh_token 服务端保存 hash。

```
{
  "tenant_id": "tenant-001",
  "user_id": "user-001",
  "role": "admin",
  "permissions": [
    "incident:read",
  ],
  "jti": "access-token-id",
  "exp": 1893456000
}
```


## 认证 API

```
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me
POST /api/v1/auth/switch-tenant
POST /api/v1/auth/verify-token
```

登录：
POST /api/v1/auth/login
{
  "username": "admin",
  "password": "admin123"
}
返回：
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 1800,
  "current_tenant": {
    "id": "tenant-001",
    "name": "Default",
    "display_name": "default",
    "role": "admin"
  },
  "tenants": [
    {
      "id": "tenant-001",
      "name": "Default",
      "display_name": "default",
      "role": "admin"
    }
  ]
}

刷新 Token：
POST /api/v1/auth/refresh
{
  "refresh_token": "eyJ..."
}

登出：
POST /api/v1/auth/logout
Authorization: Bearer <access_token>

当前用户：
GET /api/v1/auth/me
Authorization: Bearer <access_token>
{
  "id": "user-10001",
  "name": "admin",
  "email": "admin@example.com",
  "display_name": "Admin",
  "current_tenant": {
    "id": "tenant-001",
    "name": "Default",
    "role": "admin",
    "permissions": ["trace:read", "metric:read"]
  },
  "tenants": [
    {
      "id": "tenant-001",
      "name": "Default",
      "role": "admin"
    }
  ]
}

切换租户：
POST /api/v1/auth/switch-tenant
Authorization: Bearer <access_token>
{
  "tenant_id": "tenant-002"
}
返回新的 access_token。

校验 Token：
POST /api/v1/auth/verify-token
Authorization: Bearer <access_token>
{
  "valid": true,
  "user_id": "user-10001",
  "tenant_id": "tenant-001",
  "role": "editor",
  "permissions": [
    "incident:update"
  ],
  "expires_at": 1893456000
}


## 用户/租户 API

```
GET   /api/v1/users
POST  /api/v1/users
GET   /api/v1/users/current

GET   /api/v1/tenants
POST  /api/v1/tenants
GET   /api/v1/tenants/current

GET    /api/v1/tenants/current/members
POST   /api/v1/tenants/current/members
PATCH  /api/v1/tenants/current/members/{member_id}
DELETE /api/v1/tenants/current/members/{member_id}
```


## 服务账号 API

```
POST /api/v1/service-accounts
GET /api/v1/service-accounts?page=1&page_size=20
PATCH /api/v1/service-accounts/{service_account_id}
```

创建 Service Account：
POST /api/v1/service-accounts
{
  "name": "ci-deploy",
  "description": "CI/CD deployment integration",
  "role_id": 1001,
  "expires_at": "2027-09-12T00:00:00Z"
}
返回：
{
  "id": 1890012345678901,
  "name": "ci-deploy",
  "description": "CI/CD deployment integration",
  "tenant_id": 1,
  "role_id": 1001,
  "status": "ACTIVE",
  "token": "olsa_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "token_prefix": "olsa_xxxxxxxx",
  "expires_at": "2027-09-12T00:00:00Z",
  "revoked_at": null,
  "created_by_user_id": 10001,
  "created_at": "2026-09-12T08:00:00Z",
  "updated_at": "2026-09-12T08:00:00Z"
}


## 鉴权规则

- 所有业务接口必须声明所需权限
- 从 JWT 读取 tenant_id，不从请求参数信任租户
- 查询业务数据时强制追加 tenant_id
- 禁用用户、移除成员、角色变化后，verify-token 应返回无效或最新权限
- 高风险接口建议调用 verify-token 做实时校验
