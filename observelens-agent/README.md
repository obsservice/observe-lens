# ObserveLens Agent

ObserveLens 的 Agent 执行服务，负责接收会话运行请求并流式返回 Agent 产出事件。

## Local development

```bash
make bootstrap
make run
```

服务默认监听 `http://localhost:3082`，API 前缀为 `/api/v1`。

开发质量检查：

```bash
make lint
make typecheck
make test
```
