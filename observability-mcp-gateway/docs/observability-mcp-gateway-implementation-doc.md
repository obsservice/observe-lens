# observability-mcp-gateway 服务详细实现文档

## 1. 背景与定位

observability-mcp-gateway 是 ObserveLens 体系中的统一观测数据访问网关，负责把外部观测系统能力以 **MCP Tool** 的形式对上层 Agent 暴露出来。它不是单纯的 API 转发层，而是一个面向 AI 调查场景的 **语义网关**：

- 将 Prometheus、Loki、Jaeger、Kubernetes、CMDB 等数据源统一抽象成可调用工具。
- 将原始查询能力封装为面向调查任务的高层接口，降低 Agent 的调用复杂度。
- 在网关层做鉴权、租户隔离、限流、超时、重试、参数校验、结果裁剪与结构化输出。
- 为 Agent 提供稳定、可扩展、可观测的工具目录。

它的核心目标不是“把所有系统都接进来”，而是把 **调查链路中最常用、最有价值、最适合模型调用** 的能力标准化。

## 2. 设计目标

### 2.1 目标

1. **统一入口**：Agent 只需要连接一个 MCP Gateway，即可访问多种观测系统。
2. **面向调查优化**：工具设计优先服务于排障、诊断、根因分析，而不是简单 CRUD。
3. **强隔离与安全**：支持多租户、权限控制、审计与敏感字段脱敏。
4. **低耦合扩展**：新增数据源时不影响已有工具协议，工具定义可插拔。
5. **高可观测性**：网关自身也要具备指标、日志、Trace、审计能力。
6. **AI 友好**：返回结果需适合 LLM 消化，避免超长文本、噪声字段、无结构数据。

### 2.2 非目标

- 不在网关内实现完整的可观测数据存储。
- 不重复建设 Prometheus/Loki/Jaeger 的原生查询能力。
- 不直接承担告警路由、事件编排、工单流转等业务职责。
- 不将复杂分析逻辑写死在网关里，复杂分析应交给上层 Agent 或专门的分析服务。

## 3. 总体架构

### 3.1 逻辑架构

```text
Agent / LLM
   |
   |  MCP over stdio / SSE / HTTP
   v
observability-mcp-gateway
   |-- AuthN/AuthZ / Tenant Context / Audit
   |-- Tool Registry / Parameter Validation
   |-- Source Adapters
   |     |-- Prometheus Adapter
   |     |-- Loki Adapter
   |     |-- Jaeger Adapter
   |     |-- Kubernetes Adapter
   |     |-- CMDB Adapter
   |     |-- Custom Adapter
   |-- Result Normalizer / Summarizer
   |-- Cache / Rate Limit / Retry / Circuit Breaker
   v
External Systems
   |-- Prometheus
   |-- Loki
   |-- Jaeger
   |-- Kubernetes API
   |-- CMDB / Internal Metadata Service
```

### 3.2 分层设计

建议将服务拆成 5 层：

1. **Transport 层**：处理 MCP 协议入口（stdio、SSE、HTTP 任选其一或多种）。
2. **Gateway Core 层**：负责会话、上下文、鉴权、审计、限流、统一错误码。
3. **Tool 层**：定义 MCP 工具、参数 schema、返回 schema、工具描述。
4. **Adapter 层**：屏蔽不同观测系统 API 差异。
5. **Normalization 层**：统一结果格式、裁剪、摘要、证据提取。

## 4. 推荐技术方案

### 4.1 语言与框架

建议使用 **Python + FastMCP** 作为主体实现：

- Python：便于快速集成多种观测系统 SDK 与 HTTP API。
- FastMCP：适合快速实现 MCP Server，并暴露标准化工具。
- Pydantic：用于参数 schema、结果模型、配置模型。
- httpx：异步调用外部系统。
- structlog / loguru：统一结构化日志。
- opentelemetry：Trace 与 Metrics。

### 4.2 为什么选 Python

- 观测系统接口多数以 HTTP/JSON 为主，Python 适配成本低。
- 工具层需要快速迭代，Python 更适合频繁新增和调整 tool schema。
- Agent 周边生态（LLM、RAG、MCP）在 Python 侧集成更自然。

### 4.3 运行模式

建议支持两种运行模式：

- **本地模式**：stdio，适合开发、调试、桌面端集成。
- **服务模式**：SSE/HTTP，适合生产部署、集中鉴权、统一观测。

## 5. 目录结构建议

```text
observability-mcp-gateway/
├── src/observability_mcp_gateway/
│   ├── main.py
│   ├── config.py
│   ├── context.py
│   ├── auth/
│   │   └── session.py
│   ├── core/
│   │   ├── errors.py
│   │   ├── base_adapter.py
│   │   ├── cache.py
│   │   └── registry.py
│   ├── mcp/
│   │   ├── server.py
│   │   ├── tools/
│   │   │   ├── base.py
│   │   │   └── registration.py
│   │   └── schemas/
│   ├── adapters/
│   │   ├── prometheus.py
│   │   ├── loki.py
│   │   ├── jaeger.py
│   │   ├── kubernetes.py
│   │   └── cmdb.py
│   ├── services/
│   │   ├── query_service.py
│   │   └── normalize_service.py
│   ├── observability/
│   │   ├── logging.py
│   │   ├── metrics.py
│   │   ├── tracing.py
│   │   └── audit.py
│   └── utils/
├── tests/
├── docs/
├── pyproject.toml
└── Dockerfile
```

### 5.1 分层职责说明

| 目录 | 职责 | 说明 |
|------|------|------|
| `auth/` | 会话鉴权与租户上下文 | 从 JWT / 内部 token 解析身份信息，注入 `SessionContext`（§21.3） |
| `core/` | 核心基础设施 | 结构化错误码（`errors.py`）、Adapter ABC（`base_adapter.py`）、TTL 缓存（`cache.py`）、工具注册表（`registry.py`） |
| `mcp/` | MCP 协议层 | FastMCP server 创建与工具挂载（`server.py`）、工具注册编排（`tools/`）、输入输出 Schema 定义（`schemas/`） |
| `adapters/` | 外部系统适配层 | 屏蔽 Prometheus / Loki / Jaeger / Kubernetes / CMDB 各自 API 差异，统一暴露 `query` / `health_check` 接口 |
| `services/` | 工具执行业务层 | 查询编排与重试（`query_service.py`）、结果归一化（`normalize_service.py`）；不包含横切基础设施 |
| `observability/` | 网关自观测 | 结构化日志（`logging.py`）、指标（`metrics.py`）、链路追踪（`tracing.py`）、审计记录（`audit.py`） |
| `utils/` | 通用工具 | 时间解析（`timeutil.py`）、查询安全检查（`sanitize.py`） |

### 5.2 为什么 audit 和 cache 不在 services/ 下

`services/` 目录保留的是**工具执行业务编排**——`query_service` 编排 adapter 调用并驱动重试策略，`normalize_service` 将原始结果转换为 LLM 友好的统一输出。它们是工具调用链路的一部分，被 MCP tool handler 直接委托。

`cache_service` 和 `audit_service` 是**横切基础设施**，不参与工具业务逻辑本身：

- `cache.py` 移入 `core/`：缓存是核心基础设施能力，与 `registry`、`errors`、`base_adapter` 同属一层，由 `query_service` 按需调用。
- `audit.py` 移入 `observability/`：审计本质是网关自观测能力（§14），与 logging、metrics、tracing 同类——记录"谁调用了什么工具、耗时多少、是否出错"，属于可观测性范畴而非业务编排。

这样分层后，`services/` 的语义保持单一：只包含工具执行的业务逻辑，不混入基础设施组件。

## 6. 核心职责拆分

### 6.1 MCP Server

负责：

- 注册工具。
- 暴露 tool list / tool call 能力。
- 维护请求上下文。
- 将调用转给具体服务。

### 6.2 Tool Registry

负责：

- 管理所有工具的名称、描述、输入 schema、输出 schema。
- 支持按模块加载工具。
- 支持按环境开关工具。
- 支持版本化。

### 6.3 Adapter

每个外部系统一个 adapter，统一对外呈现为类似接口：

- `query`
- `range_query`
- `get_resource`
- `list_resources`
- `search`

Adapter 内部只处理各自系统的协议细节。

### 6.4 Normalize Service

负责把不同系统返回结果转换成适合 LLM 的结构：

- 统一字段名。
- 截断长文本。
- 提取关键证据。
- 附加时间范围、来源、置信度、标签。
- 去除噪声字段。

### 6.5 Audit Service

负责记录：

- 谁调用了什么工具。
- 输入参数是什么。
- 返回大小与耗时。
- 是否命中缓存。
- 是否发生错误。

审计日志应支持脱敏。

## 7. 工具设计原则

### 7.1 工具设计要“少而强”

不要把原始系统 API 逐个搬到 MCP 工具里。推荐按调查任务抽象，例如：

- 查询某服务的错误日志。
- 查询某时间窗口的 P95 延迟。
- 查找某 trace_id 的调用链。
- 根据 workload 查集群状态。
- 根据标签/实体查相关指标。

### 7.2 工具返回要“短、准、可引用”

每个工具返回建议包含：

- `summary`：简短结论。
- `evidence`：关键证据列表。
- `data`：结构化数据。
- `source`：来源系统。
- `time_range`：查询时间范围。
- `next_actions`：建议下一步。

### 7.3 工具应具备幂等性

查询类工具必须可重复执行，不能改变外部系统状态。

## 8. 建议提供的核心工具

以下是推荐的最小可用工具集。

### 8.1 Prometheus 工具

#### 8.1.1 `prom_query`

用途：执行 instant query。

输入：
- `query`
- `timestamp`
- `tenant_id`
- `scope`（集群/命名空间/服务）

输出：
- 标量值、时间序列点、标签集合

#### 8.1.2 `prom_range_query`

用途：执行 range query。

输入：
- `query`
- `start`
- `end`
- `step`
- `tenant_id`

输出：
- 序列数据
- 统计摘要（min/max/avg/last）

#### 8.1.3 `prom_topk_metrics`

用途：查某时间窗口内 TopK 指标异常项。

适合排查：
- CPU 飙高
- QPS 激增
- 错误率异常
- 延迟上升

### 8.2 Loki 工具

#### 8.2.1 `loki_query_logs`

用途：按 query 语法查询日志。

输入：
- `query`
- `start`
- `end`
- `limit`
- `tenant_id`

输出：
- 日志行
- 时间戳
- labels
- 级别

#### 8.2.2 `loki_search_patterns`

用途：按关键词、错误码、异常名搜索。

适合：
- 找某个错误在日志中的分布
- 汇总相同异常的频次

### 8.3 Jaeger 工具

#### 8.3.1 `trace_get_by_id`

用途：根据 trace_id 获取完整 trace。

输出：
- spans
- parent/child 关系
- 耗时
- 错误 span
- 关键 tags

#### 8.3.2 `trace_search`

用途：按服务名、操作名、错误、耗时筛选 trace。

### 8.4 Kubernetes 工具

#### 8.4.1 `k8s_get_workload_status`

用途：查询 Deployment/StatefulSet/Pod 状态。

输出：
- 副本数
- 重启次数
- Ready 状态
- 节点分布
- 事件摘要

#### 8.4.2 `k8s_get_events`

用途：查询 Kubernetes Event。

#### 8.4.3 `k8s_get_resource_usage`

用途：查询 workload 资源使用。

### 8.5 CMDB / 实体工具

#### 8.5.1 `entity_resolve`

用途：把服务名、别名、IP、pod、namespace、topic 等映射成统一实体。

#### 8.5.2 `entity_topology`

用途：获取实体关系图。

#### 8.5.3 `entity_owners`

用途：获取负责人、团队、告警渠道、值班信息。

## 9. 请求处理流程

### 9.1 标准流程

1. Agent 发起 MCP 工具调用。
2. Gateway 解析请求并提取上下文。
3. 鉴权模块校验租户、权限、工具白名单。
4. 参数校验模块检查 schema。
5. 路由到对应 adapter。
6. Adapter 调用外部系统。
7. Normalize Service 处理返回结果。
8. 记录审计日志、指标、Trace。
9. 返回标准化结果给 Agent。

### 9.2 失败处理

当外部系统失败时，网关应返回清晰的结构化错误：

- `TIMEOUT`
- `AUTH_FAILED`
- `RATE_LIMITED`
- `INVALID_QUERY`
- `UPSTREAM_UNAVAILABLE`
- `PARTIAL_RESULT`
- `INTERNAL_ERROR`

错误体应包含：

- 错误码
- 错误摘要
- 哪个 upstream 出错
- 是否可重试
- 建议下一步

## 10. 参数与结果模型

### 10.1 统一输入约束

所有工具建议统一支持：

- `tenant_id`
- `request_id`
- `scope`
- `time_range`
- `limit`
- `debug`（仅内部或受控环境开放）

### 10.2 统一输出模型

推荐输出如下结构：

```json
{
  "summary": "...",
  "source": "prometheus",
  "time_range": {
    "start": "...",
    "end": "..."
  },
  "evidence": [
    {
      "title": "...",
      "value": "...",
      "tags": {
        "service": "...",
        "cluster": "..."
      }
    }
  ],
  "data": {},
  "next_actions": ["..."]
}
```

### 10.3 裁剪策略

为了避免上下文爆炸，建议：

- 日志默认只返回前 N 条 + 聚合摘要。
- Trace 默认只返回关键 spans。
- 指标默认返回统计摘要和异常点。
- 原始大字段自动截断。

## 11. 配置设计

### 11.1 配置来源

支持：

- 环境变量
- 配置文件
- Secret 管理系统
- 动态配置中心（可选）

### 11.2 配置项示例

```yaml
server:
  mode: sse
  host: 0.0.0.0
  port: 3084

auth:
  enabled: true
  jwt_issuer: xxx
  jwt_audience: xxx

tenancy:
  default_tenant: default
  enforce_tenant_header: true

upstreams:
  prometheus:
    base_url: http://prometheus.monitoring.svc:9090
    timeout_ms: 5000
  loki:
    base_url: http://loki.monitoring.svc:3100
    timeout_ms: 5000
  jaeger:
    base_url: http://jaeger-query.observability.svc:16686
    timeout_ms: 5000

limits:
  max_tool_output_chars: 20000
  max_log_lines: 200
  max_trace_spans: 100
  request_timeout_ms: 10000
```

## 12. 鉴权与权限控制

### 12.1 鉴权方式

可采用：

- JWT
- 内部网关签发 token
- mTLS
- API key（开发环境）

### 12.2 权限模型

建议按三层控制：

1. **租户级**：只能访问自己的 tenant。
2. **工具级**：某些工具仅对特定角色开放。
3. **资源级**：某些命名空间、集群、环境受限。

### 12.3 脱敏策略

对以下内容进行脱敏或裁剪：

- token
- password
- access key
- cookie
- 内部 IP/域名（按策略）
- 用户隐私字段

## 13. 缓存、限流与熔断

### 13.1 缓存

适合缓存的内容：

- CMDB 实体映射
- 资源拓扑
- 相对稳定的元数据
- 高频重复查询结果（短 TTL）

不建议长时间缓存：

- 实时指标
- 故障日志
- Trace 结果

### 13.2 限流

限制维度建议包括：

- 租户
- 用户
- 工具名
- 上游系统

### 13.3 熔断

当 upstream 长时间失败时：

- 快速失败
- 返回降级结果
- 标记 upstream 健康状态
- 避免拖垮整个 Agent 请求链路

## 14. 可观测性设计

网关本身必须可观测。

### 14.1 Metrics

建议至少提供：

- `mcp_requests_total`
- `mcp_request_duration_seconds`
- `mcp_tool_calls_total`
- `mcp_tool_failures_total`
- `upstream_latency_seconds`
- `upstream_timeout_total`
- `cache_hit_ratio`
- `audit_events_total`

### 14.2 Logs

日志建议结构化输出：

- request_id
- tenant_id
- user_id
- tool_name
- upstream
- duration_ms
- result_size
- error_code

### 14.3 Tracing

建议每次 MCP 调用生成一条 Trace：

- root span：tool call
- child span：auth / validate / adapter / normalize / audit
- 子 span：upstream HTTP 请求

## 15. 代码实现建议

### 15.1 主入口

`main.py` 只做：

- 读取配置
- 初始化 logger / metrics / tracer
- 创建 MCP server
- 注册工具
- 启动服务

### 15.2 Adapter 模式

每个数据源 adapter 统一实现：

```python
class BaseAdapter(ABC):
    async def health_check(self) -> bool:
        ...

    async def query(self, request: QueryRequest) -> QueryResult:
        ...
```

### 15.3 Service 模式

将复杂逻辑放入 service 层，避免 tool handler 过胖：

- handler 只负责接入 MCP
- service 负责业务编排
- adapter 负责外部调用

### 15.4 Schema 驱动

建议所有工具输入输出都用 Pydantic schema 明确描述，避免隐式字段散落。

## 16. 扩展新数据源的方式

新增一个数据源时，遵循以下步骤：

1. 增加 adapter。
2. 定义数据源健康检查。
3. 定义一个或多个调查工具。
4. 补充输出归一化逻辑。
5. 增加集成测试。
6. 注册到 tool registry。
7. 更新文档与示例。

## 17. 测试策略

### 17.1 单元测试

覆盖：

- 参数校验
- schema 序列化
- 结果裁剪
- 脱敏逻辑
- 错误映射

### 17.2 集成测试

覆盖：

- Prometheus 查询结果
- Loki 查询结果
- Jaeger 查询结果
- K8s API 结果
- CMDB 解析结果

### 17.3 契约测试

保证：

- tool name 不随意变更
- schema 兼容性稳定
- 错误码稳定
- 返回结构稳定

## 18. 部署与运行

### 18.1 部署形态

建议容器化部署，运行在 Kubernetes 中。

### 18.2 Helm / Manifest 要点

- 配置通过 ConfigMap / Secret 注入。
- upstream 地址支持环境区分。
- 资源限制要合理，避免网关成为瓶颈。
- 应暴露 readiness / liveness probe。

### 18.3 水平扩展

网关是无状态服务，支持水平扩展：

- 共享配置中心或环境变量
- 缓存使用 Redis 或本地短缓存
- 审计日志落外部存储

## 19. API 与 MCP 协议边界

建议明确区分：

- **MCP Tool**：给 Agent 调用。
- **HTTP Admin API**：给运维、测试、健康检查使用。
- **Metrics Endpoint**：给监控系统采集。

Admin API 可用于：

- 查看 tool 列表
- 查看 upstream 健康状态
- 查看版本信息
- 执行诊断

## 20. 一个典型调查场景

以“服务延迟升高”为例，Agent 通过 observability-mcp-gateway 的典型调用顺序可能是：

1. `entity_resolve`：把服务名解析成具体 workload 与集群。
2. `prom_range_query`：查看 5 分钟内 P95/P99 延迟。
3. `prom_range_query`：查看错误率、QPS、CPU、内存。
4. `loki_query_logs`：查询对应时间窗口的错误日志。
5. `trace_search` / `trace_get_by_id`：查看慢请求链路。
6. `k8s_get_workload_status`：确认是否发生重启、滚动发布或资源不足。
7. 由上层 Agent 汇总证据，输出 RCA。

这个流程里，网关的价值在于：**把"找数据"变成"调用标准工具"**，让 Agent 能稳定地组织调查步骤。

## 21. Agent 侧 Tool Client 协议契约

本章节定义 observelens-agent（FastMCP Client）与 observability-mcp-gateway（FastMCP Server）之间的交互契约，明确工具发现、上下文注入、调用编排、错误处理与结果消费的边界。

### 21.1 连接与传输

Agent 通过 FastMCP Client 连接 Gateway，支持两种传输模式：

- **本地模式（stdio）**：开发与调试场景，Agent 进程直接以子进程方式拉起 Gateway，通过 stdin/stdout 通信。
- **服务模式（SSE / HTTP）**：生产部署场景，Agent 通过网络连接 Gateway 的 SSE 或 HTTP 端点。

连接配置示例：

```python
# stdio 模式（开发环境）
client = Client(
    transport=StdioTransport(
        command="python",
        args=["-m", "observability_mcp_gateway.main"],
        env=gateway_env,
    )
)

# SSE 模式（生产环境）
client = Client(
    transport=SSETransport(
        url="http://mcp-gateway.observability.svc:3084/sse",
        headers={"Authorization": f"Bearer {session_token}"},
    )
)
```

连接建立时，Gateway 会完成一次握手鉴权（参见 §12），鉴权通过后生成会话上下文，后续所有工具调用均在此上下文内执行。

### 21.2 工具发现机制

工具发现采用 **启动时拉取 + 运行时缓存** 策略：

1. **启动时拉取**：Agent 初始化时调用 MCP `tools/list` 方法，获取 Gateway 当前注册的全部工具及其 input schema。
2. **缓存与刷新**：Agent 将工具列表缓存到本地。当 Gateway 版本更新或工具集变更时，Agent 可通过 Admin API（§19）收到通知或主动重新拉取。
3. **动态开关**：Gateway 支持按环境、租户、角色动态控制工具可见性。Agent 拉取到的工具列表已经过权限过滤，不存在 Agent 调用未授权工具的情况。

Agent 侧不建议硬编码工具清单，应依赖运行时发现结果驱动 LangGraph 的工具绑定。

```python
# Agent 侧工具发现伪代码
async def load_tools(client: Client) -> list[Tool]:
    tools_response = await client.list_tools()
    return [
        Tool(
            name=t.name,
            description=t.description,
            input_schema=t.inputSchema,
        )
        for t in tools_response.tools
    ]
```

### 21.3 上下文注入与租户隔离

**关键原则：`tenant_id`、`user_id` 等身份信息由 Gateway 会话上下文注入，不由 Agent 作为工具参数传入。**

这确保了：
- LLM 无法伪造或篡改租户身份。
- Agent 工具调用参数中不包含敏感身份字段，降低 prompt 注入风险。
- 权限校验在 Gateway 侧完成，Agent 侧无需维护鉴权逻辑。

上下文注入流程：

1. Agent 连接 Gateway 时，在握手阶段传递 JWT 或内部 token。
2. Gateway 从 token 中解析 `tenant_id`、`user_id`、`roles`，写入会话上下文。
3. 后续每次工具调用，Gateway Core 层自动从会话上下文注入身份信息，Adapter 层和 Tool 层无需关心。
4. 工具的 input schema 中 **不包含** `tenant_id`、`user_id` 字段。

```
┌─────────┐    handshake(JWT)     ┌──────────┐
│  Agent  │ ───────────────────> │ Gateway  │
│ (Client)│                      │ (Server) │
│         │ <── session ctx ──── │          │
│         │                      │          │
│         │  tool_call(prom_query)           │
│         │ ───────────────────> │          │
│         │                      │ inject tenant_id from session ctx
│         │                      │ → adapter → prometheus
│         │ <── result ───────── │          │
└─────────┘                      └──────────┘
```

### 21.4 调用模式

#### 21.4.1 单工具调用

Agent 按调查步骤逐个调用工具。每次调用包含：

- `name`：工具名称（如 `prom_range_query`）。
- `arguments`：工具输入参数（JSON，符合 input schema）。

Gateway 返回标准化结果（§10.2），Agent 将结果写入 LangGraph State 供后续节点使用。

#### 21.4.2 并发调用

当调查步骤中存在多个 **无依赖关系** 的工具调用时，Agent 应通过 `asyncio.gather` 并发执行，缩短调查耗时。

典型场景：同时查询 P95 延迟、错误率、CPU 使用率——三者互相独立，可并发。

```python
# Agent 侧并发调用伪代码
async def investigate_latency(client: Client, service: str, time_range: TimeRange):
    results = await asyncio.gather(
        client.call_tool("prom_range_query", {
            "query": f'histogram_quantile(0.95, ...{service}...)',
            "start": time_range.start,
            "end": time_range.end,
            "step": "30s",
        }),
        client.call_tool("prom_range_query", {
            "query": f'rate(http_errors_total{{service="{service}"}}[5m])',
            "start": time_range.start,
            "end": time_range.end,
            "step": "30s",
        }),
        client.call_tool("prom_range_query", {
            "query": f'rate(container_cpu_usage_seconds_total{{pod=~"{service}.*"}}[5m])',
            "start": time_range.start,
            "end": time_range.end,
            "step": "30s",
        }),
    )
    return results
```
并发控制约束：

- Agent 侧应限制最大并发数（建议默认 5），避免对 Gateway 造成突发压力。
- Gateway 侧的限流（§13.2）作为兜底保护，即使 Agent 侧并发失控也不会拖垮上游系统。

#### 21.4.3 串行调查链路

当后续工具依赖前置工具的返回结果时（如先 `entity_resolve` 得到 workload，再 `k8s_get_workload_status` 查状态），Agent 必须串行执行。

工具返回的 `next_actions` 字段（§7.2）为 Agent 提供调查链路建议，但 **是否采纳由 Agent 的 LangGraph 编排逻辑决定**，Gateway 不强制执行顺序。

### 21.5 next_actions 的语义与消费规则

`next_actions` 是 Gateway 基于 **规则化模板** 生成的调查建议，不是 LLM 推理结果，也不包含任何 Agent 编排逻辑。

生成规则示例：

| 当前工具 | 结果特征 | next_actions 建议 |
|---------|---------|------------------|
| `prom_range_query` | 检测到延迟突增 | `["loki_query_logs: 查询对应时间窗口的错误日志", "trace_search: 搜索该时间段的慢请求 trace"]` |
| `loki_query_logs` | 检测到 error 级别日志 | `["trace_get_by_id: 根据 log 中的 trace_id 获取完整链路"]` |
| `k8s_get_workload_status` | 检测到重启 | `["k8s_get_events: 查询相关 Event", "prom_range_query: 查看重启前后的资源使用"]` |
| `trace_get_by_id` | 检测到错误 span | `["loki_query_logs: 查询错误 span 对应服务的日志"]` |

Agent 消费规则：

- `next_actions` 是 **建议性** 的，不是强制执行列表。
- Agent 的 LangGraph 编排节点根据调查上下文、已有证据和调查目标，自主决定是否采纳建议。
- Agent 可以忽略 `next_actions`，按自己的推理选择其他工具。
- Agent 不应将 `next_actions` 原样透传给 LLM 作为强制指令，应作为参考信息纳入上下文。

### 21.6 错误处理契约

当工具调用失败时，Gateway 返回结构化错误（§9.2），Agent 侧按以下策略处理：

| 错误码 | Agent 处理策略 |
|-------|--------------|
| `TIMEOUT` | 可重试。Agent 最多重试 1 次，重试时缩小时间范围或降低精度。 |
| `RATE_LIMITED` | 不可重试（立即）。Agent 应退避等待后重试，或切换到其他调查路径。 |
| `AUTH_FAILED` | 不可重试。Agent 应终止调查并向上层报告权限不足。 |
| `INVALID_QUERY` | 不可重试。Agent 应修正查询参数后重新调用。 |
| `UPSTREAM_UNAVAILABLE` | 可重试。Agent 最多重试 1 次，重试失败后跳过该数据源，继续其他调查步骤。 |
| `PARTIAL_RESULT` | 不视为错误。Agent 正常消费返回的部分结果，注意在 summary 中标注数据不完整。 |
| `INTERNAL_ERROR` | 不可重试。Agent 应记录错误并跳过该步骤。 |

Agent 侧不应将原始错误体直接返回给用户，应将其转换为用户可理解的调查状态描述。

### 21.7 结果消费与 State 写入

Agent 收到工具返回后，将结果写入 LangGraph State。写入策略遵循 `Agent.md` 中的约束：

- **不存原始大字段**：工具返回的 `data` 字段可能较大，Agent 只将 `summary` 和 `evidence` 写入 State，`data` 的完整内容存储引用或摘要。
- **证据累积**：每次工具返回的 `evidence` 追加到 State 的证据列表，供后续 RCA 节点使用。
- **Checkpoint 友好**：State 中的数据量必须可控，避免 Checkpoint 序列化时包含大量原始指标、日志或 Trace 数据。

```python
# Agent 侧结果消费伪代码
def consume_tool_result(state: AgentState, result: ToolResult) -> AgentState:
    # 写入摘要与证据
    state.observations.append(Observation(
        summary=result.summary,
        source=result.source,
        time_range=result.time_range,
        evidence=result.evidence,
        next_actions=result.next_actions,
    ))
    # 大数据仅保留引用
    if result.data_size > MAX_STATE_DATA_SIZE:
        state.data_refs.append(DataRef(
            tool=result.source,
            ref_id=result.request_id,
            size=result.data_size,
        ))
    else:
        state.data_snapshot = result.data
    return state
```

### 21.8 调用日志与审计对齐

Agent 侧和 Gateway 侧的日志通过 `request_id` 和 `trace_id` 关联，形成完整调用链：

- **Agent 侧日志**：记录 `tool_name`、`arguments`（脱敏）、`request_id`、`trace_id`、`duration_ms`、`status`、`result_summary`。
- **Gateway 侧日志**：记录 `request_id`、`trace_id`、`tenant_id`、`user_id`、`tool_name`、`upstream`、`duration_ms`、`result_size`、`error_code`、`cache_hit`。

两侧通过 W3C Trace Context 传递 `traceparent`，确保跨服务调用链可串联。

### 21.9 版本兼容性契约

- **工具名称稳定**：已发布的工具名称不随意变更，废弃工具经过一个版本的 deprecation 期。
- **Schema 向后兼容**：工具 input schema 新增字段必须可选，不破坏已有调用方。output schema 新增字段不影响 Agent 消费。
- **错误码稳定**：已定义的错误码含义不变，新增错误码通过 Admin API 公告。
- **Agent 侧适配**：Agent 依赖工具发现机制（§21.2）获取最新 schema，不硬编码工具参数结构，确保 Gateway 升级时 Agent 无需同步发版。

## 22. 版本演进建议

### v0.1

- 支持 MCP Server。
- 支持 Prometheus、Loki、Jaeger 三类工具。
- 完成基础鉴权、审计、日志、错误处理。

### v0.2

- 增加 Kubernetes 与 CMDB。
- 增加缓存与限流。
- 增加 trace 与 metrics。

### v1.0

- 支持多租户完整隔离。
- 支持工具版本化与灰度发布。
- 支持策略化权限控制。
- 支持更完整的调查上下文联动。

## 23. 实现要点总结

observability-mcp-gateway 的关键不是“接了多少系统”，而是是否真的把观测数据能力封装成了 **适合 Agent 调查的标准接口**。实现时应重点抓住四件事：

1. **统一入口**：MCP 协议标准化。
2. **统一语义**：工具按调查场景建模。
3. **统一治理**：鉴权、限流、审计、脱敏、熔断。
4. **统一观测**：网关本身也要可观测。

这样，observability-mcp-gateway 才能成为 ObserveLens 中"连接 Agent 与观测世界"的核心中间层。

---

如果后续要继续落地，建议下一步直接补两份内容：

1. **MCP Tool 清单与 schema 定义**
2. **Python + FastMCP 的最小可运行代码骨架**
3. **Agent 侧 Tool Client 交互示例与集成测试方案**
