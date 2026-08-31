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

1. 快捷命令：`/get_info`、`/get_metric`、`/analysis_incident`。
2. 关键词正则：实体详情、指标、故障根因，以及现有 `mock/demo` 演示请求。
3. LLM 兜底：仅当前两层未命中且同时配置 `OBSERVELENS_AGENT_INTENT_LLM_BASE_URL` 与
   `OBSERVELENS_AGENT_INTENT_LLM_MODEL` 时，调用 OpenAI 兼容的
   `/chat/completions` 接口进行 JSON 意图分类。

识别结果会保存在图状态的 `intent`、`intent_source`、`intent_confidence` 与
`intent_reason` 字段中，方便后续规划与审计。未配置 LLM 或模型不可用时会安全降级为
`general` 意图。

### `get_info` 实体详情查询

当请求命中 `/get_info` 时，Agent 会从 Web 的 `@实体` 引用中提取 `entity_id`，并调用
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

开发质量检查：

```bash
make lint
make typecheck
make test
```
