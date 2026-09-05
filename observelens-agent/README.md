# ObserveLens Agent

ObserveLens 的 Agent 执行服务，负责接收会话运行请求并流式返回 Agent 产出事件。

## Local development

```bash
make bootstrap
make run
```

服务默认监听 `http://localhost:3082`，API 前缀为 `/api/v1`。

## Intent recognition

每个会话请求会按以下优先级识别意图：

1. CMD：`/get_entity_info`、`/get_metric`、`/get_log`、`/get_tarce`、`/get_event`、
   `/generate_incident_report` 等快捷命令与常用可观测数据查看请求。
2. RCA：故障、告警、根因等根因分析请求。
3. QA：文档咨询及其它通用问答请求。
4. LLM 兜底：当前规则未命中时，调用已注入的 OpenAI 兼容客户端；仅当
   `OBSERVELENS_AGENT_INTENT_LLM_BASE_URL` 与 `OBSERVELENS_AGENT_INTENT_LLM_MODEL` 均已配置时才会请求
   `/chat/completions` 接口进行 JSON 意图分类。

识别结果会保存在图状态的 `intent_type`、`short_cmd`、`entity`、`intent_source`、`intent_confidence` 与
`intent_reason` 字段中，方便后续规划与审计。`intent_type` 只会是 `cmd`、`rca` 或 `qa`，主图直接使用该值
选择对应子图。未配置 LLM 或模型不可用时会安全降级为 `qa`。

Graph 运行参数统一存放在 `AgentState.default_config`。该配置包含指标查询窗口、采样间隔、查询数量、
RCA 日志查询上限及意图 LLM 参数；其内置默认值，并在创建状态时由 `OBSERVELENS_AGENT_*` 配置覆盖。

### `get_entity_info` 实体详情查询

当请求命中 `/get_entity_info` 时，Agent 会从 Web 的 `@实体` 引用中提取 `entity_id`，并调用
`GET {OBSERVELENS_AGENT_CATALOG_BASE_URL}/api/v1/workspaces/{workspace_id}/entities/{entity_id}`
获取资源详情。其中 `workspace_id` 由 `OBSERVELENS_AGENT_CATALOG_WORKSPACE_ID` 配置，默认
`ws000003`。未引用实体、Catalog 不可用或实体不存在时，Agent 会返回可读的错误提示而不中断
会话流。

### `get_metric` 时序查询

当请求命中 `/get_metric` 时，Agent 会查询实体关联的 Dataset，并仅解析其中
`document.kind=MetricSet` 的具体数据集实例。随后按输入语义选择最相关的 `spec.metrics` 项，从其
`generator` 读取 PromQL，并仅覆盖原始 PromQL selector 中已有的 MetricSet 标签，避免把实体字段
错误地当作 Prometheus 标签追加。随后 Agent
通过 FastMCP SSE 调用 `prom_range_query` 获取时序数据。配置
`OBSERVELENS_AGENT_MCP_GATEWAY_SSE_URL` 指向 Gateway 的 `/sse` 端点；默认查询窗口由
`OBSERVELENS_AGENT_METRIC_QUERY_DEFAULT_WINDOW_MINUTES` 控制，也支持“最近 30 分钟”“last 2h”等
时间范围，采样间隔由 `OBSERVELENS_AGENT_METRIC_QUERY_STEP` 控制。

### `analysis_incident` 故障调查

`/analysis_incident` 会以 AESP 自定义 SSE 事件流逐步展示调查过程：识别故障实体、检索 RAG 架构
上下文、读取 Catalog 的 Dataset 与拓扑、制定指标和日志查询计划、通过 MCP Gateway 获取真实遥测数据、
识别异常、推理根因并生成报告。前端可直接消费 `plan.generated`、`step.*`、
`observation.generated`、`finding.generated` 与 `output.progress` 事件。

知识库检索默认请求 `OBSERVELENS_AGENT_KNOWLEDGE_BASE_URL` 的
`/api/v1/knowledge/retrieval/search`，并使用配置的租户与用户请求头。Catalog 当前只提供查询语义和拓扑；
真实指标与日志分别通过 MCP 的 `prom_range_query` 和 `loki_query_logs` 获取。

开发质量检查：

```bash
make lint
make typecheck
make test
```
