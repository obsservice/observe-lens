# ObserveLens 编码规范

> 本文档用于指导 ObserveLens 项目的人工开发与 AI Coding。
> 所有新增代码默认遵循本文档约定，未经明确确认，不得擅自替换核心技术栈或引入重复能力组件。

---

# 1. 技术组件选型

## 1.1 基础开发语言

| 项目        | 选型                                  |
| --------- | ----------------------------------- |
| 前端语言      | TypeScript 5+                       |
| Python 服务 | Python 3.12+                        |
| Go 服务     | Go 1.24+                            |
| 数据库脚本     | SQL                                 |
| 配置文件      | YAML / TOML / Environment Variables |

---

## 1.2 observelens-web

| 分类              | 技术选型                           |
| --------------- | ------------------------------ |
| Web Framework   | Next.js                        |
| UI Framework    | React                          |
| 编程语言            | TypeScript                     |
| CSS Framework   | Tailwind CSS                   |
| UI Component    | shadcn/ui                      |
| Server State    | TanStack Query                 |
| Client State    | Zustand                        |
| Form            | React Hook Form                |
| Validation      | Zod                            |
| Markdown        | react-markdown                 |
| Code Highlight  | Shiki                          |
| Diagram         | Mermaid                        |
| Testing         | Vitest + React Testing Library |
| E2E Testing     | Playwright                     |
| Lint            | ESLint                         |
| Format          | Prettier                       |
| Package Manager | pnpm                           |

### 前端约束

* 仅使用 React Function Component。
* 开启 TypeScript Strict Mode。
* 不使用 Redux。
* 服务端数据统一使用 TanStack Query 管理。
* 本地轻量状态使用 Zustand。
* 表单统一使用 React Hook Form + Zod。
* UI 组件优先复用 shadcn/ui。
* 禁止在页面组件中直接编写底层 HTTP 请求。
* 流式输出默认使用 SSE。
* 禁止使用 `any`，特殊场景必须注明原因。
* 公共组件必须定义完整的 Props 类型。
* API 类型优先由 OpenAPI Schema 生成。

---

## 1.3 observelens-service

| 分类                    | 技术选型               |
| --------------------- | ------------------ |
| 编程语言                  | Python 3.12+       |
| Web Framework         | FastAPI            |
| Data Validation       | Pydantic v2        |
| ORM                   | SQLAlchemy 2.x     |
| Database Migration    | Alembic            |
| Database              | PostgreSQL         |
| Cache                 | Redis              |
| HTTP Client           | httpx              |
| Streaming             | Server-Sent Events |
| Logging               | structlog          |
| Testing               | pytest             |
| Async Testing         | pytest-asyncio     |
| Code Format           | Ruff Format        |
| Lint                  | Ruff               |
| Type Check            | mypy               |
| Dependency Management | uv                 |

### PostgreSQL 使用范围

* Conversation
* Message
* Run
* Plan
* Step
* Observation
* Artifact
* Model Configuration
* Prompt Configuration
* Notification Configuration
* User Preference
* Audit Log
* Task
* Incident

### Redis 使用范围

* Cache
* Session
* Rate Limit
* Distributed Lock
* Temporary Streaming State
* Idempotency Key
* Short-lived Runtime State

### 后端约束

* 所有网络 I/O 和数据库 I/O 优先使用异步实现。
* 使用 SQLAlchemy 2.x typed ORM。
* 禁止在 Router 中编写业务逻辑。
* Router 仅负责参数接收、鉴权、调用应用服务和响应转换。
* Pydantic Model 与 SQLAlchemy Model 必须分离。
* 数据库表结构变更必须通过 Alembic Migration。
* 禁止在业务代码中自动创建或修改表结构。
* 禁止使用 Redis 保存长期业务数据。
* 禁止在代码中拼接原生 SQL，复杂查询需集中管理并参数化。
* 所有外部请求必须配置连接超时和读取超时。
* 所有写接口必须考虑幂等性。
* 所有分页接口统一使用游标分页或明确的分页参数。
* API 默认挂载在 `/api/v1`。
* API 错误响应必须使用统一错误结构。
* 所有时间统一使用 UTC 存储。
* 数据库字段使用 `snake_case`。
* Python 枚举使用字符串枚举。
* 禁止使用可变对象作为函数默认参数。

---

## 1.4 observelens-agent

| 分类                    | 技术选型                  |
| --------------------- | --------------------- |
| 编程语言                  | Python 3.12+          |
| Agent Framework       | LangGraph             |
| LLM Protocol          | OpenAI Compatible API |
| Tool Client           | FastMCP Client        |
| Data Validation       | Pydantic v2           |
| HTTP Client           | httpx                 |
| Logging               | structlog             |
| Testing               | pytest                |
| Async Testing         | pytest-asyncio        |
| Code Format           | Ruff Format           |
| Lint                  | Ruff                  |
| Type Check            | mypy                  |
| Dependency Management | uv                    |

### LLM Provider 支持

* OpenAI
* Azure OpenAI
* Qwen
* DeepSeek
* Claude
* Gemini
* OpenAI API Compatible Model

### Agent 约束

* Agent 工作流统一使用 LangGraph。
* 不引入 CrewAI、AutoGen 或其他并行 Agent Framework。
* 每个 LangGraph Node 只完成一个明确步骤。
* Graph State 必须使用 TypedDict、Dataclass 或 Pydantic Model 明确定义。
* 禁止在 Node 之间传递无类型字典。
* 所有 Tool 输入和输出必须定义 Schema。
* Tool 返回结果必须结构化，禁止仅返回大段无约束字符串。
* Agent 不直接访问 Prometheus、Loki、Jaeger、Kubernetes、CMDB。
* Agent 不直接访问 Catalog、Knowledge Base 的数据库。
* 所有外部能力通过 API 或 MCP Tool 调用。
* Prompt 不得硬编码在业务函数中。
* Prompt 必须支持版本管理。
* 模型 Provider 与业务逻辑必须解耦。
* 禁止在业务代码中直接实例化特定模型客户端。
* 所有模型调用必须配置 Timeout、Retry 和最大 Token 限制。
* 重试不得无限执行。
* Tool Call 必须记录调用参数、耗时、状态和结果摘要。
* Checkpoint 不得保存大型原始指标、日志或 Trace 数据。
* 大型 Observation 应存储引用或摘要。
* 流式事件必须具有稳定的事件类型和数据结构。
* 禁止把完整 Chain of Thought 持久化或返回给前端。

---

## 1.5 observability-catalog

| 分类                  | 技术选型                    |
| ------------------- | ----------------------- |
| 编程语言                | Go 1.24+                |
| Web Framework       | Gin                     |
| Relational Database | MySQL                   |
| Analytical Database | ClickHouse              |
| Graph Database      | Neo4j                   |
| MySQL Driver        | go-sql-driver/mysql     |
| ClickHouse Driver   | clickhouse-go           |
| Neo4j Driver        | neo4j-go-driver         |
| SQL Access          | sqlc 或显式 Repository     |
| Database Migration  | golang-migrate          |
| Logging             | zap                     |
| Configuration       | Viper                   |
| Validation          | go-playground/validator |
| Metrics             | Prometheus Client       |
| Tracing             | OpenTelemetry           |
| Testing             | Go testing + Testify    |
| Mock                | mockery                 |
| Lint                | golangci-lint           |
| Format              | gofmt + goimports       |

### MySQL 使用范围

* Entity
* Relation
* Dataset
* DataSource
* Connector
* Metadata Schema
* Label Definition
* Sync Checkpoint
* Configuration

### ClickHouse 使用范围

* Entity Snapshot
* Relation Snapshot
* Historical Change
* Statistical Data
* Search Index
* Aggregation Result
* Time-based Metadata Record

### Neo4j 使用范围

* Entity Topology
* Dependency Graph
* Relationship Traversal
* Impact Analysis
* Upstream and Downstream Query

### Go 服务约束

* 默认使用 Gin，不同时引入 Fiber。
* Handler 不得直接访问数据库。
* 数据访问必须通过 Repository 接口。
* Repository 不得包含业务判断。
* Service 层不得依赖具体数据库驱动。
* 所有跨数据库写入必须明确一致性策略。
* 禁止假设 MySQL、ClickHouse 和 Neo4j 之间存在强事务。
* MySQL 作为核心元数据事实源。
* ClickHouse 和 Neo4j 作为派生存储时，必须支持重建。
* 数据同步操作必须幂等。
* 批量写入优先使用 Batch。
* 所有查询必须设置 Context Timeout。
* Goroutine 必须具备退出机制。
* 禁止启动无生命周期管理的后台 Goroutine。
* Channel 必须由发送方负责关闭。
* 错误必须使用 `%w` 包装。
* 禁止忽略返回的 Error。
* 对外接口不得直接暴露数据库 Model。
* 结构体 JSON 字段使用 `snake_case`。
* 所有接口参数必须进行 Validation。
* MySQL 表结构变更必须通过 Migration。
* Neo4j 写入优先使用 `MERGE` 保证幂等。
* ClickHouse 表设计优先考虑查询模式和分区策略。

---

## 1.6 observability-mcp-gateway

| 分类                    | 技术选型         |
| --------------------- | ------------ |
| 编程语言                  | Python 3.12+ |
| MCP Framework         | FastMCP      |
| HTTP Client           | httpx        |
| Data Validation       | Pydantic v2  |
| Logging               | structlog    |
| Retry                 | tenacity     |
| Testing               | pytest       |
| Code Format           | Ruff Format  |
| Lint                  | Ruff         |
| Type Check            | mypy         |
| Dependency Management | uv           |

### MCP Gateway 约束

* 一个 Tool 只负责一种明确能力。
* Tool 名称必须使用稳定的动词加名词形式。
* Tool 输入和输出必须定义 Pydantic Schema。
* 禁止直接返回底层平台原始响应。
* 返回值必须经过标准化。
* Tool 必须设置 Timeout。
* Retry 只用于可重试错误。
* 禁止对参数错误、权限错误进行无意义重试。
* 所有 Tool 必须限制最大返回数据量。
* 时序、日志、Trace 查询必须支持时间范围限制。
* 高基数查询必须提供保护机制。
* 禁止在 MCP Gateway 中编写 Agent 推理逻辑。
* 禁止在 MCP Gateway 中保存长期业务状态。
* 认证信息不得出现在日志中。
* Tool 执行日志必须记录 Tool Name、Duration、Status、Trace ID。
* 敏感参数必须脱敏。
* 外部系统适配器必须与 MCP Tool 定义分离。

---

## 1.7 observability-knowledge-base

| 分类                    | 技术选型           |
| --------------------- | -------------- |
| 编程语言                  | Python 3.12+   |
| Knowledge Framework   | LlamaIndex     |
| Relational Database   | PostgreSQL     |
| Vector Store          | pgvector       |
| Data Validation       | Pydantic v2    |
| ORM                   | SQLAlchemy 2.x |
| Database Migration    | Alembic        |
| HTTP Framework        | FastAPI        |
| HTTP Client           | httpx          |
| Logging               | structlog      |
| Testing               | pytest         |
| Code Format           | Ruff Format    |
| Lint                  | Ruff           |
| Type Check            | mypy           |
| Dependency Management | uv             |

### Embedding Provider

* OpenAI Embedding
* BGE-M3
* Qwen Embedding

### Reranker

* BGE Reranker
* Provider-compatible Reranker

### PostgreSQL 使用范围

* Knowledge Base
* Document
* Document Version
* Chunk
* Chunk Metadata
* Ingestion Task
* Source Configuration
* Index Configuration
* Citation Metadata
* Embedding Vector

### Knowledge Base 约束

* RAG 能力统一使用 LlamaIndex。
* LangGraph 不负责文档加载、切片和向量索引。
* 文档、版本、Chunk 和 Embedding 必须具有稳定 ID。
* 文档更新必须生成新版本或显式更新版本号。
* Chunk 不得仅依赖数组下标作为唯一标识。
* Chunk 必须保留来源、标题、章节、页码或路径等元数据。
* Embedding Model 必须记录模型名称和向量维度。
* 更换 Embedding Model 时必须重新构建对应索引。
* 禁止在同一向量列中混用不同维度的 Embedding。
* 检索默认支持 Metadata Filter。
* 混合检索优先采用关键词检索加向量检索。
* Rerank 必须配置候选数量上限。
* 检索结果必须返回 Citation 信息。
* 禁止将超大文档完整写入 Prompt。
* 文档解析失败必须记录失败原因和处理状态。
* 原始文件建议存储在 S3 或 MinIO，PostgreSQL 保存元数据和引用。
* 向量索引类型必须根据数据规模评估后选择。
* 数据量较小时优先保证召回准确性，不盲目增加复杂索引。

---

## 1.8 数据库与中间件

| 组件         | 用途                           |
| ---------- | ---------------------------- |
| PostgreSQL | ObserveLens 应用数据、知识库元数据、向量数据 |
| pgvector   | Knowledge Base 向量检索          |
| Redis      | 缓存、会话、锁、限流、短期运行状态            |
| MySQL      | Catalog 核心元数据                |
| ClickHouse | Catalog 快照、历史和统计分析           |
| Neo4j      | Catalog 拓扑和依赖关系              |
| MinIO / S3 | 文档、附件、报告和大型 Artifact         |

### 存储约束

* 不跨服务共享数据库表。
* 不允许一个服务直接访问另一个服务的数据库。
* 服务之间通过 API、Event 或 MCP 交互。
* PostgreSQL 与 MySQL 不承担原始 Metrics、Logs、Traces 存储。
* 原始可观测数据仍保存在对应可观测平台。
* Redis 不作为最终事实源。
* ClickHouse 和 Neo4j 中的派生数据必须可重建。
* 所有存储连接池必须配置最大连接数、空闲连接数和连接生命周期。
* 所有数据库查询必须具备超时控制。
* 所有数据库 Schema 变更必须提交 Migration。
* 禁止在生产环境启动时自动修改 Schema。

---

## 1.9 API 与通信协议

| 场景                | 技术选型              |
| ----------------- | ----------------- |
| Web 与 Service     | REST + SSE        |
| Service 与 Agent   | REST / SSE        |
| Agent 与 Tool      | MCP               |
| 内部普通服务调用          | REST              |
| API Schema        | OpenAPI 3.x       |
| Serialization     | JSON              |
| Time Format       | RFC 3339          |
| Trace Propagation | W3C Trace Context |

### API 规范

* API 统一使用 `/api/v1` 前缀。
* URL 使用复数名词。
* URL 不使用动词表达资源操作。
* HTTP Method 必须符合语义。
* 所有接口定义明确的请求和响应 Schema。
* 不直接返回 ORM Model。
* 错误响应使用统一结构：

```json
{
  "code": "RESOURCE_NOT_FOUND",
  "message": "Resource not found",
  "request_id": "req_xxx",
  "details": {}
}
```

* 列表接口必须限制最大分页大小。
* 批量接口必须限制最大批量数量。
* 所有写操作必须考虑幂等性。
* 所有接口必须透传或生成 Request ID。
* 时间字段统一使用带时区的 RFC 3339 格式。
* 接口废弃必须经过版本迁移，不直接破坏现有协议。

---

# 2. 通用编码规范

## 2.1 模块边界

* 禁止跨服务直接访问数据库。
* 禁止通过复制代码绕过已有公共组件。
* 禁止形成循环依赖。
* Domain 层不得依赖 Web Framework。
* 业务逻辑不得依赖具体数据库实现。
* 基础设施实现必须通过接口注入。
* 禁止创建无明确用途的 `common`、`utils` 大杂烩模块。
* 通用能力应按业务语义命名。

---

## 2.2 命名规范

### Python

| 类型   | 规范                 |
| ---- | ------------------ |
| 文件   | `snake_case.py`    |
| 变量   | `snake_case`       |
| 函数   | `snake_case`       |
| 类    | `PascalCase`       |
| 常量   | `UPPER_SNAKE_CASE` |
| 私有成员 | `_name`            |

### Go

| 类型      | 规范                       |
| ------- | ------------------------ |
| Package | 小写单词                     |
| 文件      | `snake_case.go`          |
| 导出类型    | `PascalCase`             |
| 非导出类型   | `camelCase`              |
| 接口      | 按行为命名                    |
| 缩写      | 保持统一，如 `ID`、`HTTP`、`URL` |

### TypeScript

| 类型               | 规范                                 |
| ---------------- | ---------------------------------- |
| 文件               | `kebab-case.ts` / `kebab-case.tsx` |
| 变量               | `camelCase`                        |
| 函数               | `camelCase`                        |
| Component        | `PascalCase`                       |
| Type / Interface | `PascalCase`                       |
| 常量               | `UPPER_SNAKE_CASE`                 |
| Hook             | `useXxx`                           |

---

## 2.3 类型规范

* 所有公共函数必须声明输入和返回类型。
* 禁止使用无约束字典传递核心业务数据。
* Python 优先使用明确类型、TypedDict、Dataclass 或 Pydantic Model。
* TypeScript 禁止使用 `any`。
* Go 禁止使用 `map[string]any` 作为稳定业务接口。
* Optional 或 Nullable 字段必须具有明确语义。
* DTO、Domain Model、Persistence Model 必须按需要分离。
* 外部输入必须完成 Runtime Validation。
* 不信任来自前端、第三方 API 或 Tool 的任何输入。

---

## 2.4 错误处理

* 禁止吞掉异常。
* 禁止空 `except`。
* 禁止只记录错误但继续返回成功。
* 错误必须包含可定位上下文。
* 不得在错误信息中泄露 Token、密码或连接串。
* 可重试错误与不可重试错误必须区分。
* 业务错误必须使用稳定错误码。
* 底层错误不得原样暴露给用户。
* HTTP 错误必须映射为统一 API Error。
* Tool 错误必须返回结构化失败结果。
* 异步任务失败必须可查询和可追踪。

---

## 2.5 日志规范

### Python

使用：

```text
structlog
```

### Go

使用：

```text
zap
```

### 日志字段

所有关键日志尽可能包含：

* `trace_id`
* `request_id`
* `conversation_id`
* `run_id`
* `step_id`
* `tool_call_id`
* `user_id`
* `component`
* `duration_ms`
* `status`

### 日志约束

* 使用结构化 JSON 日志。
* 禁止使用 `print`。
* 禁止记录密码、Token、Cookie 和密钥。
* Prompt 和 Tool 参数按敏感级别脱敏。
* 大型响应只记录摘要、大小和引用。
* 异常日志必须包含 Stack Trace。
* 同一错误不得在多个层级重复记录完整堆栈。
* 高频路径避免逐条输出 INFO 日志。
* DEBUG 日志不得作为关键业务逻辑依赖。

---

## 2.6 配置规范

* 配置统一通过环境变量或配置文件注入。
* Python 使用 Pydantic Settings。
* Go 使用 Viper。
* 前端环境变量按 Next.js 规范管理。
* 禁止在代码中硬编码域名、密码、Token 和数据库地址。
* 配置项必须提供类型和默认值说明。
* 敏感配置通过 Secret 管理。
* 配置文件不得提交真实凭证。
* 启动时必须校验必要配置。
* 配置命名统一使用大写下划线环境变量格式。

---

## 2.7 并发与异步规范

### Python

* 网络和数据库操作优先使用 `async`。
* 禁止在 Async 函数中调用阻塞 I/O。
* CPU 密集型任务不得直接阻塞 Event Loop。
* 后台任务必须具有生命周期和错误处理。
* 所有异步调用必须设置 Timeout。
* 并发调用必须限制并发度。

### Go

* Goroutine 必须受 Context 控制。
* 所有长期运行任务必须支持 Graceful Shutdown。
* 禁止无限制创建 Goroutine。
* Channel 使用必须明确发送方和接收方责任。
* 共享状态必须明确同步策略。
* 优先使用不可变数据和消息传递。

### Frontend

* 必须处理请求取消。
* 页面卸载后不得继续更新状态。
* SSE 重连必须设置退避策略。
* 禁止因组件重复渲染产生重复请求。

---

## 2.8 测试规范

### 测试层级

* Unit Test
* Integration Test
* Contract Test
* End-to-End Test

### 基本要求

* 核心业务逻辑必须有单元测试。
* Repository 必须有集成测试。
* API 必须覆盖成功、参数错误、权限错误和异常场景。
* MCP Tool 必须覆盖超时、限流和底层错误。
* Agent Node 必须可独立测试。
* Prompt 测试与代码测试分离。
* 禁止仅测试 Happy Path。
* 测试不得依赖不稳定的公共外部服务。
* 外部系统通过 Fake、Mock 或 Test Container 替代。
* 修复 Bug 时必须补充回归测试。
* 测试数据必须可重复执行。

---

## 2.9 安全规范

* 所有外部输入必须校验。
* 所有数据库查询必须参数化。
* 上传文件必须校验类型、大小和文件名。
* 防止路径穿越。
* 防止 SSRF。
* MCP Tool 必须限制可访问目标。
* PromQL、LogQL、SQL 和 Cypher 输入必须进行安全检查。
* 不允许 LLM 自由生成并直接执行高风险命令。
* 高风险操作必须经过审批或策略检查。
* 用户权限检查必须在服务端执行。
* 禁止信任前端传入的角色和权限字段。
* Secret 统一通过密钥管理系统注入。
* 日志和追踪数据必须进行脱敏。

---

## 2.10 可观测性规范

统一使用 OpenTelemetry。

必须采集：

* Metrics
* Logs
* Traces

核心指标包括：

* 请求量
* 错误率
* 请求延迟
* 数据库连接池状态
* 外部依赖延迟
* Tool 调用次数与耗时
* LLM 调用次数、耗时和 Token
* Agent Run 成功率
* Agent Step 耗时
* SSE 活跃连接
* 检索召回数量
* Embedding 处理耗时
* Catalog 同步延迟

所有跨服务请求必须传递 Trace Context。

---

# 3. AI Coding 约束

AI 生成或修改代码时必须遵循以下规则：

1. 不得擅自更换本文档确定的核心技术栈。
2. 不得同时引入功能重复的 Framework。
3. 不得跨服务访问数据库。
4. 不得在 Router、Handler 或 Controller 中堆积业务逻辑。
5. 不得绕过 MCP Gateway 直接访问可观测数据源。
6. 不得让 LangGraph 承担 Knowledge Base 索引构建职责。
7. 不得让 LlamaIndex 承担 Agent Workflow 编排职责。
8. 不得使用 Redis 保存长期业务数据。
9. 不得在代码中硬编码凭证和环境地址。
10. 新增依赖前必须说明必要性和替代方案。
11. 修改数据库结构时必须同时生成 Migration。
12. 新增 API 时必须提供请求、响应和错误 Schema。
13. 新增 Tool 时必须提供输入、输出、超时和错误定义。
14. 新增业务逻辑时必须提供对应测试。
15. 新增外部请求时必须设置 Timeout。
16. 新增重试逻辑时必须设置最大次数和退避策略。
17. 新增后台任务时必须支持停止、失败处理和状态查询。
18. 不得持久化或返回模型内部完整推理过程。
19. 代码必须通过项目既有的 Format、Lint、Type Check 和 Test。
20. 不确定现有接口或目录结构时，应先检查现有代码，不得自行假设。
21. 优先修改现有实现，避免无必要地创建重复模块。
22. 不得为了抽象而抽象，优先保持代码局部性和可读性。
23. 未达到复用条件时，不提前设计复杂插件或注册机制。
24. 固定流程优先使用明确 Pipeline，不使用动态注册框架。
25. 所有生成代码必须可运行，不得只输出不可执行的伪代码。
