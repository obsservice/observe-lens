# ObserveLens Service

ObserveLens 的统一业务服务入口，提供会话管理、Agent 调用编排与 SSE 事件转发。

## Local development

```bash
make bootstrap
make run
```

服务默认监听 `http://localhost:3081`，API 前缀为 `/api/v1`。

开发质量检查：

```bash
make lint
make typecheck
make test
```

`make migrate` 必须在首次运行和每次数据库 Schema 升级后显式执行；应用启动不会自动修改数据库结构。
