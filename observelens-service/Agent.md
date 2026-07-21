## observelens-service Coding Architecture

采用 **Layered Architecture**，所有代码必须遵循以下分层，不得跨层访问。

```
API
 │
 ▼
Application
 ├── Repository
 └── Client
      │
      ▼
PostgreSQL / Redis / External Services
```

### API (`app/api`)

负责：

- REST API
- Request / Response
- Authentication
- Parameter Validation
- 调用 Application

禁止：

- 业务逻辑
- 数据库访问
- 外部 HTTP 调用

---

### Schemas (`app/schemas`)

负责：

- Request
- Response
- DTO
- Event Schema

统一使用 **Pydantic v2**。

---

### Application (`app/application`)

负责：

- 业务流程编排
- 事务控制
- 调用 Repository
- 调用 Client
- 返回业务结果

这是唯一允许编排业务流程的层。

---

### Repository (`app/repositories`)

负责：

- PostgreSQL 数据访问
- CRUD
- 查询

禁止：

- 业务逻辑
- HTTP 调用

---

### Client (`app/clients`)

负责：

- 调用 Agent
- 调用 Catalog
- 调用 Knowledge Base
- 调用其他外部服务

负责：

- HTTP
- Timeout
- Retry

禁止：

- 数据库访问
- 业务决策

---

### Models (`app/models`)

负责：

- SQLAlchemy ORM Model

禁止：

- API Schema
- Business Logic

---

### Infrastructure (`app/infrastructure`)

负责：

- PostgreSQL
- Redis
- Storage
- Logging
- Middleware

仅提供基础设施能力。

---

### Core (`app/core`)

负责：

- Exception
- Security
- Dependency Injection
- Request Context
- Common Utilities

---

### Config (`app/config`)

负责：

- Settings
- Environment
- Configuration

---

## Dependency Rules

允许：

```
API
    ↓
Application
    ↓
Repository
    ↓
Database

Application
    ↓
Client
    ↓
External Service
```

禁止：

- API → Repository
- API → Client
- Repository → HTTP
- Repository → Repository
- Client → Database
- 跨服务直接访问数据库

---

## General Rules

- Router 保持轻量，仅负责 HTTP 协议处理。
- 所有业务逻辑放在 Application。
- Repository 仅负责持久化。
- Client 仅负责外部服务调用。
- Service 之间通过 REST / SSE / MCP 通信，不共享数据库。
- 使用 Async First、Pydantic v2、SQLAlchemy 2.x。
- 数据库 Schema 统一通过 Alembic 管理。

