# observelens-service Coding Architecture

## Architecture Style

`observelens-service` 采用：

> **Lightweight Vertical Slice Architecture + Simple Layering**

代码优先按业务模块聚合，每个模块内部保持简单分层。

目标：

* 保持业务代码局部聚合。
* 降低跨目录跳转成本。
* 方便 AI 理解、生成和修改代码。
* 避免过度设计和不必要的抽象。
* 保证 API、业务逻辑、数据访问和外部调用之间的职责边界。

整体依赖关系：

```text
Router
  │
  ▼
Service
  ├── Repository
  │      │
  │      ▼
  │   PostgreSQL / Redis
  │
  └── Client
         │
         ▼
     External Services
```

---

## Project Structure

推荐项目目录：

```text
src/
└── observelens_service/
    ├── main.py
    ├── api.py
    │
    ├── modules/
    │   ├── conversations/
    │   │   ├── __init__.py
    │   │   ├── router.py
    │   │   ├── schemas.py
    │   │   ├── service.py
    │   │   ├── repository.py
    │   │   ├── models.py
    │   │   └── streaming.py
    │   │
    │   ├── runs/
    │   │   ├── router.py
    │   │   ├── schemas.py
    │   │   ├── service.py
    │   │   ├── repository.py
    │   │   └── models.py
    │   │
    │   ├── observations/
    │   ├── incidents/
    │   ├── inspections/
    │   ├── entities/
    │   ├── knowledge/
    │   ├── model_configs/
    │   ├── notifications/
    │   ├── auth/
    │   └── system/
    │
    ├── clients/
    │   ├── agent.py
    │   ├── catalog.py
    │   └── knowledge_base.py
    │
    ├── database/
    │   ├── base.py
    │   ├── session.py
    │   └── pagination.py
    │
    ├── config/
    │   ├── settings.py
    │   ├── database.py
    │   ├── agent.py
    │   ├── catalog.py
    │   └── knowledge.py
    │
    └── common/
        ├── exceptions.py
        ├── responses.py
        ├── dependencies.py
        ├── security.py
        └── context.py
```

测试目录按业务模块组织：

```text
tests/
├── conversations/
│   ├── test_router.py
│   ├── test_service.py
│   └── test_repository.py
├── runs/
├── incidents/
├── inspections/
└── conftest.py
```

---

## Module Organization

每个业务模块放在：

```text
app/modules/{module_name}/
```

一个标准模块包含：

```text
router.py
schemas.py
service.py
repository.py
models.py
```

根据实际需求按需创建文件。

最小模块可以只有：

```text
router.py
schemas.py
service.py
```

禁止为了目录形式统一而创建没有实际内容的空文件。

---

## Router (`modules/*/router.py`)

负责：

* REST API 路由。
* Path、Query、Header 和 Request Body 解析。
* 参数校验。
* Authentication 和 Authorization 依赖。
* 调用当前模块的 Service。
* 将业务结果转换为 HTTP Response。
* 建立 SSE 连接。

禁止：

* 编写业务逻辑。
* 直接访问数据库。
* 直接调用 Repository。
* 直接调用外部 Client。
* 在 Router 中实现事务。
* 在 Router 中拼装复杂业务流程。

推荐示例：

```python
router = APIRouter(
    prefix="/conversations",
    tags=["Conversation"],
)


@router.get("")
async def list_conversations(
    query: ConversationListQuery = Depends(),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationPage:
    return await service.list(query)
```

依赖关系：

```text
Router → Service
```

---

## Schemas (`modules/*/schemas.py`)

负责：

* Request Schema。
* Response Schema。
* Query Parameter Schema。
* DTO。
* Event Schema。
* 模块内部数据传输模型。

统一使用：

* Pydantic v2。
* 明确的字段类型。
* 明确的必填和可选字段。
* `ConfigDict(from_attributes=True)` 完成 ORM 转换。

推荐示例：

```python
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ConversationCreateRequest(BaseModel):
    title: str | None = None


class ConversationUpdateRequest(BaseModel):
    title: str


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
```

禁止：

* 在 Schema 中编写数据库操作。
* 在 Schema 中调用外部服务。
* 使用 Pydantic Model 代替 SQLAlchemy ORM Model。
* 在 Schema Validator 中放置复杂业务逻辑。

---

## Service (`modules/*/service.py`)

Service 是模块内唯一允许编排业务流程的组件。

负责：

* 业务规则。
* 业务流程编排。
* 调用 Repository。
* 调用外部 Client。
* 事务边界协调。
* 权限和资源归属校验。
* ORM Model 与 Response Schema 转换。
* 抛出业务异常。

依赖关系：

```text
Service
├── Repository
└── Client
```

推荐示例：

```python
class ConversationService:
    def __init__(
        self,
        repository: ConversationRepository,
    ) -> None:
        self.repository = repository

    async def create(
        self,
        owner_id: UUID,
        request: ConversationCreateRequest,
    ) -> ConversationResponse:
        conversation = Conversation(
            owner_id=owner_id,
            title=request.title or "New Conversation",
        )

        created = await self.repository.create(conversation)

        return ConversationResponse.model_validate(created)
```

禁止：

* 在 Service 中直接编写原始 SQL。
* 在 Service 中直接创建 HTTP Client。
* 在 Service 中读取环境变量。
* 在 Service 中处理 FastAPI Request 或 Response。
* 跨模块直接访问其他模块的 Repository。

---

## Repository (`modules/*/repository.py`)

Repository 仅在模块需要本地数据持久化时创建。

负责：

* PostgreSQL 数据访问。
* Redis 数据访问。
* CRUD。
* 查询构建。
* 分页查询。
* ORM Model 持久化。
* 数据库锁和数据库层操作。

依赖关系：

```text
Repository → Database
```

推荐示例：

```python
class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(
        self,
        conversation_id: UUID,
    ) -> Conversation | None:
        return await self.session.get(
            Conversation,
            conversation_id,
        )

    async def create(
        self,
        conversation: Conversation,
    ) -> Conversation:
        self.session.add(conversation)
        await self.session.flush()
        await self.session.refresh(conversation)
        return conversation
```

禁止：

* 编写业务规则。
* 调用外部 HTTP 服务。
* 调用其他模块的 Repository。
* 返回 API Response Schema。
* 处理 FastAPI 异常或 HTTP 状态码。
* 在 Repository 中做业务流程编排。

---

## Models (`modules/*/models.py`)

仅在模块需要本地数据库表时创建。

负责：

* SQLAlchemy ORM Model。
* 表名和字段定义。
* 数据库索引。
* 数据库约束。
* ORM Relationship。

统一使用：

* SQLAlchemy 2.x。
* `Mapped`。
* `mapped_column`。
* Async First。

推荐示例：

```python
class Conversation(Base):
    __tablename__ = "t_conversations"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    owner_id: Mapped[UUID] = mapped_column(
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
```

禁止：

* 定义 API Request 或 Response。
* 编写业务逻辑。
* 调用 Service。
* 调用外部 Client。
* 在 ORM Model 中实现复杂行为。

---

## Client (`clients`)

所有外部服务调用统一放在：

```text
app/clients/
```

当前主要 Client：

```text
agent.py
catalog.py
knowledge_base.py
```

负责：

* HTTP 请求。
* SSE 或流式响应接收。
* Timeout。
* Retry。
* Authentication Header。
* Trace ID 和 Request ID 透传。
* 外部异常转换。
* 外部请求和响应 DTO。

推荐示例：

```python
class CatalogClient:
    def __init__(
        self,
        http_client: httpx.AsyncClient,
        settings: CatalogSettings,
    ) -> None:
        self.http_client = http_client
        self.settings = settings

    async def search_entities(
        self,
        query: EntitySearchQuery,
    ) -> EntityPage:
        response = await self.http_client.get(
            f"{self.settings.base_url}/entities/search",
            params=query.model_dump(exclude_none=True),
        )
        response.raise_for_status()
        return EntityPage.model_validate(response.json())
```

禁止：

* 访问本地数据库。
* 编写业务决策。
* 调用 Repository。
* 直接返回 FastAPI Response。
* 在 Client 中维护业务状态。

---

## Database (`database`)

负责：

* SQLAlchemy Engine。
* AsyncSession。
* Declarative Base。
* 数据库连接池。
* 分页基础能力。
* 数据库生命周期管理。

推荐目录：

```text
database/
├── base.py
├── session.py
└── pagination.py
```

禁止：

* 放置业务 ORM Model。
* 编写业务查询。
* 调用外部服务。
* 依赖具体业务模块。

业务 ORM Model 必须放在对应模块中：

```text
modules/conversations/models.py
modules/incidents/models.py
```

---

## Config (`config`)

负责：

* 应用配置加载。
* 环境变量。
* 数据库配置。
* 外部服务地址。
* Timeout。
* 安全配置。
* 日志配置参数。

统一使用：

* `pydantic-settings`。
* 类型化配置。
* `.env` 仅用于本地开发。

推荐目录：

```text
config/
├── settings.py
├── database.py
├── agent.py
├── catalog.py
└── knowledge.py
```

禁止：

* 在业务代码中直接调用 `os.getenv()`。
* 在配置文件中编写业务逻辑。
* 在配置对象中建立数据库或 HTTP 连接。
* 在多个模块中重复读取同一个环境变量。

业务代码通过依赖注入获取配置。

---

## Common (`common`)

负责真正跨模块复用的公共能力。

推荐内容：

```text
common/
├── exceptions.py
├── responses.py
├── dependencies.py
├── security.py
└── context.py
```

适合放置：

* 全局异常。
* 公共响应模型。
* FastAPI 公共依赖。
* 身份认证辅助能力。
* Request Context。
* Tenant Context。
* Request ID。
* Trace Context。

禁止：

* 放置具体业务逻辑。
* 放置特定模块的 Schema。
* 放置特定模块的数据访问。
* 将 `common` 演变为万能工具目录。

只有至少两个模块实际复用的代码，才允许放入 `common`。

---

## External Proxy Modules

部分模块主要代理内部服务，不需要本地持久化。

例如：

```text
modules/entities/
├── router.py
├── schemas.py
└── service.py
```

其调用关系：

```text
Entity Router
    ↓
Entity Service
    ↓
Catalog Client
```

同理：

```text
modules/knowledge/
├── router.py
├── schemas.py
└── service.py
```

调用关系：

```text
Knowledge Router
    ↓
Knowledge Service
    ↓
Knowledge Base Client
```

代理模块不应为了保持结构一致而创建：

```text
models.py
repository.py
```

---

## Conversation Module

Conversation、Message、Run 和 Observation 存在较强关联。

当前阶段推荐：

```text
modules/
├── conversations/
│   ├── router.py
│   ├── message_router.py
│   ├── schemas.py
│   ├── models.py
│   ├── repository.py
│   ├── service.py
│   └── streaming.py
│
├── runs/
│   ├── router.py
│   ├── schemas.py
│   ├── models.py
│   ├── repository.py
│   └── service.py
│
└── observations/
    ├── router.py
    ├── schemas.py
    └── service.py
```

约束：

* Conversation 和 Message 放在同一业务模块中。
* Run 具有独立生命周期，单独作为模块。
* Observation 当前只有详情查询时，可以保持轻量模块。
* 不提前为 Observation 引入复杂 Repository 或领域抽象。
* 业务复杂度增加后再进一步拆分。

---

## Dependency Rules

允许：

```text
Router → Service

Service → Repository

Service → Client

Repository → Database

Client → External Service
```

禁止：

```text
Router → Repository

Router → Client

Repository → Client

Repository → Repository

Client → Repository

Client → Database

Database → Business Module

Business Module → Config Environment Directly
```

跨模块调用原则：

```text
Module A Service
        ↓
Module B Service
```

不允许：

```text
Module A Service
        ↓
Module B Repository
```

如跨模块调用开始变得复杂，应优先评估是否需要：

* 合并模块。
* 抽取清晰的 Service 接口。
* 将流程放入上层业务模块。

不要默认增加新的架构层。

---

## Transaction Rules

事务由 Service 层控制。

推荐：

```python
async with session.begin():
    ...
```

Repository：

* 负责 `add`、`flush`、查询。
* 默认不主动 `commit`。
* 不独立控制跨 Repository 事务。

Service：

* 决定事务开始和结束。
* 负责跨多个 Repository 操作的一致性。
* 负责失败后的异常转换。

对于单次简单 CRUD，可以通过统一 Session Dependency 管理事务，但必须保持行为一致。

---

## Exception Rules

模块业务异常定义在模块内部：

```text
modules/conversations/exceptions.py
modules/incidents/exceptions.py
```

真正通用的异常定义在：

```text
common/exceptions.py
```

推荐异常：

```python
class ConversationNotFoundError(Exception):
    pass


class ConversationAccessDeniedError(Exception):
    pass
```

Service 抛出业务异常。

Router 不捕获具体业务异常。

统一由全局 Exception Handler 转换成 HTTP 响应。

禁止在 Repository 中抛出 FastAPI `HTTPException`。

---

## Async Rules

项目统一采用 Async First。

必须使用：

* FastAPI Async Route。
* SQLAlchemy AsyncSession。
* `httpx.AsyncClient`。
* 异步 SSE。
* 异步外部服务调用。

禁止在异步请求链路中直接执行：

* 同步 HTTP 请求。
* 同步数据库请求。
* 长时间阻塞任务。
* CPU 密集型计算。

阻塞任务应放入：

* 线程池。
* 任务队列。
* 独立 Worker。
* 外部 Agent Runtime。

---

## AI Coding Rules

为了提高 AI 编码质量，必须遵守以下约定。

### Fixed File Names

模块内使用固定命名：

```text
router.py
schemas.py
service.py
repository.py
models.py
exceptions.py
streaming.py
```

不要同时使用多个等价命名：

```text
service.py
manager.py
handler.py
use_case.py
application.py
```

简单业务统一使用 `service.py`。

---

### Locality First

修改某个业务功能时，优先将相关代码放在同一个模块中。

例如 Incident 功能应主要位于：

```text
modules/incidents/
```

不要将 Incident 代码分散到：

```text
api/
schemas/
repositories/
models/
application/
```

---

### Avoid Premature Abstraction

禁止在没有明确复用需求时引入：

* BaseRepository。
* GenericService。
* UnitOfWork。
* Command Bus。
* Query Bus。
* Event Bus。
* Domain Event Framework。
* Port / Adapter 抽象。
* Factory 层。
* Manager 层。
* Handler 层。
* UseCase 层。
* CQRS。

只有当重复逻辑真实出现并且至少被多个模块使用时，才允许抽取公共能力。

---

### Keep Files Small

建议：

* 单个文件尽量控制在 300 行以内。
* 单个 Service 类尽量控制在 200 行以内。
* 单个函数尽量控制在 50 行以内。

当文件持续增长时，优先按具体能力拆分：

```text
service.py
integration_service.py
streaming.py
```

不要建立无明确职责的：

```text
helpers.py
utils.py
misc.py
```

---

## General Rules

* Router 保持轻量。
* 业务逻辑统一放在 Service。
* Repository 只负责持久化。
* Client 只负责外部服务调用。
* Schema 与 ORM Model 严格分离。
* 配置统一放在 `config`。
* 数据库基础设施统一放在 `database`。
* 业务代码优先按模块聚合。
* 不为了形式统一创建无用文件。
* 不跨服务直接访问数据库。
* 服务之间通过 REST、SSE 或 MCP 通信。
* 使用 Pydantic v2。
* 使用 SQLAlchemy 2.x。
* 数据库 Schema 统一通过 Alembic 管理。
* 所有公共抽象必须有真实复用场景。
* 简单实现优先于复杂架构。

---

## Final Architecture Principle

`observelens-service` 的核心编码原则是：

> **按业务模块聚合代码，在模块内部保持 Router → Service → Repository / Client 的简单依赖关系。**

推荐最小模块：

```text
modules/{module_name}/
├── router.py
├── schemas.py
└── service.py
```

存在本地持久化时增加：

```text
repository.py
models.py
```

存在流式能力时增加：

```text
streaming.py
```

这种架构在保持职责清晰的同时，具有较高的代码局部性，适合当前业务复杂度，也更利于 AI 编码、代码审查、测试和长期维护。
