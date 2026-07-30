# Observability MCP Gateway

ObserveLens 的可观测数据 MCP 网关，将 Prometheus、Loki、Jaeger、Kubernetes、CMDB 等数据源统一封装为标准 MCP Tool 接口，为 Agent 提供面向调查场景的工具能力。

## Local development

```bash
make bootstrap
make run
```

服务默认监听 `http://localhost:3084`，运行模式为 SSE。

开发质量检查：

```bash
make lint
make typecheck
make test
```
