# observelens-service 数据库表设计

## 1. 设计约定

### 1.1 数据库

* 数据库：PostgreSQL
* 主键：`BIGINT`
* 主键由应用层生成，推荐使用 Snowflake ID
* 时间类型：`TIMESTAMPTZ`
* JSON 类型：`JSONB`
* 表名统一使用 `t_` 前缀
* 字段名统一使用 `snake_case`
* 所有时间均以 UTC 存储

### 1.2 多租户约定

所有租户级业务表必须包含：`tenant_id`。
任何查询、更新和删除操作都必须携带 `tenant_id` 条件，不允许仅根据资源 ID 查询租户数据。

### 1.3 通用审计字段

需要支持更新和软删除的业务表，统一使用：

| 字段            | 类型          | 说明               |
| ------------- | ----------- | ---------------- |
| `create_by`   | BIGINT      | 创建用户 ID，系统创建时可为空 |
| `update_by`   | BIGINT      | 最后更新用户 ID        |
| `create_time` | TIMESTAMPTZ | 创建时间             |
| `update_time` | TIMESTAMPTZ | 最后更新时间           |
| `delete_time` | TIMESTAMPTZ | 软删除时间，未删除时为空     |

只追加、不更新的数据表可仅保留 `create_time`。

---

## 数据库表设计

### t_tenants

租户表，一个租户对应一个企业、部门或组织单元。

| 字段            | 类型           | 必填 | 默认值                 | 说明                       |
| ------------- | ------------ | -: | ------------------- | ------------------------ |
| `id`          | BIGINT       |  是 | -                   | 租户主键                     |
| `code`        | VARCHAR(64)  |  是 | -                   | 租户唯一编码，用于接口、配置和资源隔离      |
| `name`        | VARCHAR(128) |  是 | -                   | 租户名称                     |
| `description` | VARCHAR(512) |  否 | NULL                | 租户描述                     |
| `status`      | VARCHAR(16)  |  是 | `ACTIVE`            | 租户状态：`ACTIVE`、`DISABLED` |
| `attributes`  | JSONB        |  是 | `{}`                | 租户级扩展属性                  |
| `create_by`   | BIGINT       |  否 | NULL                | 创建用户 ID                  |
| `update_by`   | BIGINT       |  否 | NULL                | 最后更新用户 ID                |
| `create_time` | TIMESTAMPTZ  |  是 | `CURRENT_TIMESTAMP` | 创建时间                     |
| `update_time` | TIMESTAMPTZ  |  是 | `CURRENT_TIMESTAMP` | 最后更新时间                   |
| `delete_time` | TIMESTAMPTZ  |  否 | NULL                | 软删除时间                    |

**约束与索引**

```text
PRIMARY KEY (id)
UNIQUE (code)
```

### t_users

用户表，保存 ObserveLens 平台内的用户基础信息。

| 字段                | 类型            | 必填 | 默认值                 | 说明                       |
| ----------------- | ------------- | -: | ------------------- | ------------------------ |
| `id`              | BIGINT        |  是 | -                   | 用户主键                     |
| `tenant_id`       | BIGINT        |  是 | -                   | 所属租户 ID                  |
| `external_id`     | VARCHAR(128)  |  否 | NULL                | 外部身份系统中的用户唯一 ID          |
| `username`        | VARCHAR(64)   |  是 | -                   | 用户登录名                    |
| `display_name`    | VARCHAR(128)  |  是 | -                   | 用户展示名称                   |
| `email`           | VARCHAR(256)  |  否 | NULL                | 用户邮箱                     |
| `role`            | VARCHAR(32)   |  是 | `MEMBER`            | 租户级角色：`ADMIN`、`MEMBER`   |
| `status`          | VARCHAR(16)   |  是 | `ACTIVE`            | 用户状态：`ACTIVE`、`DISABLED` |
| `create_by`       | BIGINT        |  否 | NULL                | 创建用户 ID                  |
| `update_by`       | BIGINT        |  否 | NULL                | 最后更新用户 ID                |
| `create_time`     | TIMESTAMPTZ   |  是 | `CURRENT_TIMESTAMP` | 创建时间                     |
| `update_time`     | TIMESTAMPTZ   |  是 | `CURRENT_TIMESTAMP` | 最后更新时间                   |
| `delete_time`     | TIMESTAMPTZ   |  否 | NULL                | 软删除时间                    |

**约束与索引**

```text
PRIMARY KEY (id)
UNIQUE (tenant_id, username)
```

### t_api_keys

API Key 表，用于系统集成、Webhook 或自动化调用。

| 字段               | 类型           | 必填 | 默认值                 | 说明                     |
| ---------------- | ------------ | -: | ------------------- | ---------------------- |
| `id`             | BIGINT       |  是 | -                   | API Key 主键             |
| `tenant_id`      | BIGINT       |  是 | -                   | 所属租户 ID                |
| `user_id`        | BIGINT       |  否 | NULL                | 创建或拥有该 API Key 的用户 ID  |
| `name`           | VARCHAR(128) |  是 | -                   | API Key 名称             |
| `key_hash`       | VARCHAR(256) |  是 | -                   | API Key 哈希值，不保存明文      |
| `scopes`         | JSONB        |  是 | `[]`                | 授权范围列表                 |
| `status`         | VARCHAR(16)  |  是 | `ACTIVE`            | 状态：`ACTIVE`、`REVOKED`  |
| `expires_time`   | TIMESTAMPTZ  |  否 | NULL                | 过期时间，为空表示不过期           |
| `create_by`      | BIGINT       |  否 | NULL                | 创建用户 ID                |
| `create_time`    | TIMESTAMPTZ  |  是 | `CURRENT_TIMESTAMP` | 创建时间                   |
| `delete_time`    | TIMESTAMPTZ  |  否 | NULL                | 删除或撤销时间                |

**约束与索引**

```text
PRIMARY KEY (id)
UNIQUE (tenant_id, name)
```

### t_conversations

会话主表，支持私有会话和公共会话。

| 字段                  | 类型           | 必填 | 默认值                 | 说明                                |
| ------------------- | ------------ | -: | ------------------- | --------------------------------- |
| `id`                | BIGINT       |  是 | -                   | 会话主键                              |
| `tenant_id`         | BIGINT       |  是 | -                   | 所属租户 ID                           |
| `title`             | VARCHAR(256) |  是 | -                   | 会话标题                              |
| `owner_id`          | BIGINT       |  是 | -                   | 会话创建者ID                          |
| `visibility`        | VARCHAR(32)  |  是 | `PRIVATE`           | 会话可见性：`PRIVATE`、`MEMBER`、`TENANT`   |
| `conversation_type` | VARCHAR(32)  |  是  | `CHAT`             | 会话类型：`CHAT`、`INCIDENT`           |
| `status`            | VARCHAR(16)  |  是 | `ACTIVE`            | 会话状态：`ACTIVE`、`ARCHIVED`、`CLOSED` |
| `summary`           | TEXT         |  否 | NULL                | 会话摘要，可由 AI 自动生成                   |
| `tags`              | JSONB        |  是 | `[]`                | 会话标签数组，例如 `["inspect","rca"]`  |
| `last_message_time` | TIMESTAMPTZ  |  否 | NULL                | 最后一条消息时间，用于会话列表排序         |
| `create_by`         | BIGINT       |  是 | -                   | 创建用户 ID                           |
| `update_by`         | BIGINT       |  否 | NULL                | 最后更新用户 ID                         |
| `create_time`       | TIMESTAMPTZ  |  是 | `CURRENT_TIMESTAMP` | 创建时间                              |
| `update_time`       | TIMESTAMPTZ  |  是 | `CURRENT_TIMESTAMP` | 最后更新时间                            |
| `delete_time`       | TIMESTAMPTZ  |  否 | NULL                | 软删除时间                             |

**访问规则**

* PRIVATE会话，只有创建者具有访问权限。（用户手工创建的会话为PRIVATE会话）
* TENANT会话，同一租户下的所有用户均可访问。（从故障事件创建的会话默认为TENANT会话）
* MEMBER会话，只有`t_conversations_members`表中的指定用户可访问。

**约束与索引**

```text
PRIMARY KEY (id)
INDEX (tenant_id, last_message_time DESC)
```

### t_conversation_members

| 字段                | 类型          | 说明                                |
| ----------------- | ----------- | --------------------------------- |
| `id`              | BIGINT      | 主键                                |
| `tenant_id`       | BIGINT      | 所属租户                              |
| `conversation_id` | BIGINT      | 会话 ID                             |
| `user_id`         | BIGINT      | 成员用户 ID                           |
| `status`          | VARCHAR(16) | `ACTIVE`、`REMOVED`                  |
| `joined_time`     | TIMESTAMPTZ | 加入时间                              |
| `create_by`       | BIGINT      | 添加成员的用户                           |
| `create_time`     | TIMESTAMPTZ | 创建时间                              |
| `update_time`     | TIMESTAMPTZ | 更新时间                              |

**约束与索引**

```text
PRIMARY KEY (id)
INDEX (tenant_id, conversation_id, user_id)
```

### t_messages

会话消息表，保存用户消息、助手消息和系统消息。

| 字段                 | 类型          | 必填 | 默认值                 | 说明                                            |
| ------------------ | ----------- | -: | ------------------- | --------------------------------------------- |
| `id`               | BIGINT      |  是 | -                   | 消息主键                                          |
| `tenant_id`        | BIGINT      |  是 | -                   | 所属租户 ID                                       |
| `conversation_id`  | BIGINT      |  是 | -                   | 所属会话 ID                                       |
| `sequence_id`      | BIGINT      |  是 | -                   | 会话内消息顺序 ID                                  |
| `run_id`           | BIGINT      |  否 | NULL                | 关联的 Agent Run ID                              |
| `sender_role`      | VARCHAR(16) |  是 | -                   | 消息角色：`USER`、`ASSISTANT`、`SYSTEM`              |
| `sender_id`        | BIGINT NULL |  否 | -                   | 消息发送者用户ID；Assistant/System消息为空              |
| `content_format`   | VARCHAR(32) |  是 | `TEXT`              | 消息类型：`TEXT`、`MARKDOWN`                       |
| `content`          | TEXT        |  是 | ''                  | 消息正文                                          |
| `content_metadata` | JSONB       |  是 | `{}`                | 消息扩展信息，例如引用、实体、展示控制参数                 |
| `status`           | VARCHAR(16) |  是 | `COMPLETED`         | 状态：`PENDING`、`STREAMING`、`COMPLETED`、`FAILED`   |
| `create_time`      | TIMESTAMPTZ |  是 | `CURRENT_TIMESTAMP` | 消息创建时间                                        |
| `update_time`      | TIMESTAMPTZ |  是 | `CURRENT_TIMESTAMP` | 消息最后更新时间                                      |
| `delete_time`      | TIMESTAMPTZ |  否 | NULL                | 软删除时间                                         |

**约束与索引**

```text
PRIMARY KEY (id)
UNIQUE (tenant_id, conversation_id, sequence_id)
```

### t_message_attachments

消息附件表。文件正文存放在 S3 或 MinIO，本表仅保存元数据及引用。

| 字段                | 类型            | 必填 | 默认值                 | 说明                                        |
| ----------------- | ------------- | -: | ------------------- | ----------------------------------------- |
| `id`              | BIGINT        |  是 | -                   | 附件主键                                      |
| `tenant_id`       | BIGINT        |  是 | -                   | 所属租户 ID                                   |
| `conversation_id` | BIGINT        |  是 | -                   | 所属会话 ID                                   |
| `message_id`      | BIGINT        |  是 | -                   | 所属消息 ID                                   |
| `file_name`       | VARCHAR(256)  |  是 | -                   | 原始文件名                                     |
| `file_size`       | BIGINT        |  是 | -                   | 文件大小，单位为字节                                |
| `content_type`    | VARCHAR(128)  |  是 | -                   | MIME 类型                                   |
| `metadata`        | JSONB         |  是 | `{}`                | 文件页数、图片宽高、解析状态等扩展信息               |
| `checksum`        | VARCHAR(128)  |  否 | NULL                | 文件哈希，用于完整性校验和去重                     |
| `storage_bucket`  | VARCHAR(128)  |  是 | -                   | 对象存储 Bucket                               |
| `storage_key`     | VARCHAR(1024) |  是 | -                   | 对象存储中的对象 Key                              |
| `status`          | VARCHAR(16)   |  是 | `READY`             | 状态：`UPLOADING`、`READY`、`FAILED`、`DELETED` |
| `create_by`       | BIGINT        |  是 | -                   | 上传用户 ID                                   |
| `create_time`     | TIMESTAMPTZ   |  是 | `CURRENT_TIMESTAMP` | 创建时间                                      |
| `delete_time`     | TIMESTAMPTZ   |  否 | NULL                | 删除时间                                      |

**约束与索引**

```text
PRIMARY KEY (id)
UNIQUE (tenant_id, storage_key)
INDEX (tenant_id, message_id)
```

### t_runs

| 字段                  | 类型                | 说明                                                   |
| ------------------- | ----------------- | ---------------------------------------------------- |
| `id`                | BIGINT            | Service Run 主键                                       |
| `tenant_id`         | BIGINT            | 所属租户                                                 |
| `conversation_id`   | BIGINT NULL       | Chat/Incident 会话；Task 可为空                            |
| `input_message_id`  | BIGINT NULL       | Chat 输入消息 ID                                         |
| `output_message_id` | BIGINT NULL       | Chat 输出消息 ID                                         |
| `agent_run_id`      | VARCHAR(128) NULL | Agent Runtime 的运行 ID                                 |
| `status`            | VARCHAR(16)       | `PENDING`、`RUNNING`、`COMPLETED`、`FAILED`、`CANCELLED` |
| `error_code`        | VARCHAR(64) NULL  | 错误码                                                  |
| `error_message`     | TEXT NULL         | 错误摘要                                                 |
| `started_time`      | TIMESTAMPTZ NULL  | 开始时间                                                 |
| `completed_time`    | TIMESTAMPTZ NULL  | 结束时间                                                 |
| `duration_ms`       | BIGINT NULL       | 耗时                                                   |
| `trigger_user_id`   | BIGINT NULL       | 发起用户                                                 |
| `create_time`       | TIMESTAMPTZ       | 创建时间                                                 |
| `update_time`       | TIMESTAMPTZ       | 更新时间                                                 |

**约束与索引**

```text
PRIMARY KEY (id)
```

### t_incidents

故障主表，一个故障绑定一个协作会话，成员通过该会话统一管理。

| 字段                | 类型           | 必填 | 默认值                 | 说明                                                        |
| ----------------- | ------------ | -: | ------------------- | --------------------------------------------------------- |
| `id`              | BIGINT       |  是 | -                   | 故障主键                                                      |
| `tenant_id`       | BIGINT       |  是 | -                   | 所属租户 ID                                                   |
| `incident_id`     | VARCHAR(64)  |  是 | -                   | 租户内可读故障编号                                                 |
| `title`           | VARCHAR(256) |  是 | -                   | 故障标题                                                      |
| `description`     | TEXT         |  否 | NULL                | 故障描述                                                      |
| `severity`        | VARCHAR(16)  |  是 | `MEDIUM`            | 严重等级：`CRITICAL`、`HIGH`、`MEDIUM`、`LOW`                     |
| `status`          | VARCHAR(32)  |  是 | `OPEN`              | 状态：`OPEN`、`INVESTIGATING`、`MITIGATED`、`RESOLVED`、`CLOSED` |
| `source`          | VARCHAR(64)  |  否 | NULL                | 故障来源，例如 `ALERTMANAGER`、`GRAFANA`、`MANUAL`                 |
| `external_metadata`| JSONB       |  是 | `{}`                | 外部告警ID、原始链接等扩展信息                                          |
| `entity_type`     | VARCHAR(64)  |  否 | NULL                | 主要故障实体类型                                                  |
| `entity_id`       | VARCHAR(256) |  否 | NULL                | 主要故障实体 ID                                                 |
| `impact_scope`    | JSONB        |  否 | NULL                | 故障影响范围                                                    |
| `assignee_id`     | BIGINT       |  否 | NULL                | 故障指派处理用户 ID                                              |
| `conversation_id` | BIGINT       |  否 | NULL                | 故障对应的协作会话 ID                                              |
| `started_time`    | TIMESTAMPTZ  |  否 | NULL                | 故障发生时间                                                    |
| `detected_time`   | TIMESTAMPTZ  |  否 | NULL                | 故障发现时间                                                    |
| `resolved_time`   | TIMESTAMPTZ  |  否 | NULL                | 故障恢复时间                                                    |
| `closed_time`     | TIMESTAMPTZ  |  否 | NULL                | 故障关闭时间                                                    |
| `root_cause`      | TEXT         |  否 | NULL                | 最终根因结论                                                    |
| `resolution`      | TEXT         |  否 | NULL                | 处置或恢复方案                                                   |
| `create_by`       | BIGINT       |  否 | NULL                | 创建用户 ID，自动创建时可为空                                          |
| `update_by`       | BIGINT       |  否 | NULL                | 最后更新用户 ID                                                 |
| `create_time`     | TIMESTAMPTZ  |  是 | `CURRENT_TIMESTAMP` | 创建时间                                                      |
| `update_time`     | TIMESTAMPTZ  |  是 | `CURRENT_TIMESTAMP` | 更新时间                                                      |
| `delete_time`     | TIMESTAMPTZ  |  否 | NULL                | 软删除时间                                                     |

**约束与索引**

```text
PRIMARY KEY (id)
UNIQUE (tenant_id, incident_id)
INDEX (tenant_id, title)
UNIQUE (tenant_id, conversation_id) WHERE conversation_id IS NOT NULL
```

### t_tasks

巡检任务定义表。

| 字段                | 类型           | 必填 | 默认值                 | 说明                           |
| ----------------- | ------------ | -: | ------------------- | ---------------------------- |
| `id`              | BIGINT       |  是 | -                   | 任务主键                         |
| `tenant_id`       | BIGINT       |  是 | -                   | 所属租户 ID                      |
| `name`            | VARCHAR(128) |  是 | -                   | 任务名称                         |
| `description`     | TEXT         |  否 | NULL                | 任务描述                         |
| `input_template`  | TEXT         |  是 | -                   | 任务输入模板                      |
| `variable_schema` | JSONB        |  是 | -                   | 输入模板变量定义及校验规则          |
| `enabled`         | BOOLEAN      |  是 | -                   | 是否启用                         |
| `create_by`       | BIGINT       |  是 | -                   | 创建用户 ID                      |
| `update_by`       | BIGINT       |  否 | NULL                | 最后更新用户 ID                   |
| `create_time`     | TIMESTAMPTZ  |  是 | `CURRENT_TIMESTAMP` | 创建时间                         |
| `update_time`     | TIMESTAMPTZ  |  是 | `CURRENT_TIMESTAMP` | 更新时间                         |
| `delete_time`     | TIMESTAMPTZ  |  否 | NULL                | 软删除时间                        |

**约束与索引**

```text
PRIMARY KEY (id)
UNIQUE (tenant_id, name)
```

### t_task_schedules

巡检任务调度配置表。

| 字段                  | 类型           | 必填 | 默认值                 | 说明                       |
| ------------------- | ------------ | -: | ------------------- | ------------------------ |
| `id`                | BIGINT       |  是 | -                   | 调度主键                     |
| `tenant_id`         | BIGINT       |  是 | -                   | 所属租户 ID                  |
| `task_id`           | BIGINT       |  是 | -                   | 任务 ID                    |
| `name`              | VARCHAR(128) |  是 | -                   | 任务实例名称                 |
| `template_variables`| JSONB        |  是 | `{}`                | 消息模板变量                   |
| `schedule_type`     | VARCHAR(16)  |  是 | -                   | 调度方式：`CRON`、`INTERVAL` |
| `interval_seconds`  | INT          |  否 | -                   | 间隔执行的秒数                |
| `cron_expression`   | VARCHAR(128) |  否 | -                   | Cron 表达式                 |
| `timezone`          | VARCHAR(64)  |  是 | `UTC`               | 调度时区，例如 `Asia/Singapore` |
| `enabled`           | BOOLEAN      |  是 | -                   | 是否启用                       |
| `create_by`         | BIGINT       |  是 | -                   | 创建用户 ID                  |
| `update_by`         | BIGINT       |  否 | NULL                | 最后更新用户 ID                |
| `create_time`       | TIMESTAMPTZ  |  是 | `CURRENT_TIMESTAMP` | 创建时间                     |
| `update_time`       | TIMESTAMPTZ  |  是 | `CURRENT_TIMESTAMP` | 更新时间                     |

**约束与索引**

```text
PRIMARY KEY (id)
INDEX (tenant_id, task_id)
```

### `t_task_runs`

巡检任务运行记录表。

| 字段                  | 类型            | 必填 | 默认值                 | 说明                                                      |
| ------------------- | ------------- | -: | ------------------- | ------------------------------------------------------- |
| `id`                | BIGINT        |  是 | -                   | 任务运行主键                                                  |
| `tenant_id`         | BIGINT        |  是 | -                   | 所属租户 ID                                                 |
| `task_id`           | BIGINT        |  是 | -                   | 任务 ID                                                   |
| `schedule_id`       | BIGINT        |  否 | -                   | 调度规则 ID                                               |
| `trigger_type`      | VARCHAR(16)   |  是 | -                   | 触发类型：`MANUAL`、`SCHEDULED`                            |
| `status`            | VARCHAR(16)   |  是 | `PENDING`           | 状态：`PENDING`、`RUNNING`、`COMPLETED`、`FAILED`、`CANCELLED` |
| `template_variables`| JSONB         |  是 | -                  | 本次执行使用的任务输入快照                                          |
| `input_message`     | JSONB         |  否 | NULL                | 本次执行的输入Message                                       |
| `output_message`    | JSONB         |  否 | NULL                | 本次执行的输出Message                                       |
| `error_code`        | INT           |  否 | NULL                | 错误码                                                     |
| `error_message`     | TEXT          |  否 | NULL                | 错误摘要                                                    |
| `started_time`      | TIMESTAMPTZ   |  否 | NULL                | 开始时间                                                    |
| `completed_time`    | TIMESTAMPTZ   |  否 | NULL                | 完成时间                                                    |
| `duration_ms`       | BIGINT        |  否 | NULL                | 执行耗时                                                    |
| `create_time`       | TIMESTAMPTZ   |  是 | `CURRENT_TIMESTAMP` | 创建时间                                                    |
| `update_time`       | TIMESTAMPTZ   |  是 | `CURRENT_TIMESTAMP` | 更新时间                                                    |

**约束与索引**

```text
PRIMARY KEY (id)
INDEX (tenant_id, schedule_id, create_time DESC)
```

### `t_llm_models`

大模型配置表。

| 字段               | 类型            | 必填 | 默认值                 | 说明                                         |
| ---------------- | ------------- | -: | ------------------- | ------------------------------------------ |
| `id`             | BIGINT        |  是 | -                   | 模型配置主键                                     |
| `tenant_id`      | BIGINT        |  是 | -                   | 所属租户 ID                                    |
| `name`           | VARCHAR(128)  |  是 | -                   | 配置显示名称                                     |
| `provider`       | VARCHAR(64)   |  是 | -                   | Provider，例如 `OPENAI`、`AZURE_OPENAI`、`QWEN` |
| `model_name`     | VARCHAR(128)  |  是 | -                   | Provider 侧模型名称                             |
| `endpoint`       | VARCHAR(1024) |  否 | NULL                | API Endpoint                               |
| `credential`     | VARCHAR(256)  |  否 | NULL                | 密钥管理系统中的凭证                               |
| `api_version`    | VARCHAR(64)   |  否 | NULL                | API 版本                                     |
| `parameters`     | JSONB         |  是 | `{}`                | Temperature、max_tokens 等默认参数               |
| `priority`       | INTEGER       |  是 | `100`               | 模型路由优先级，数值越小优先级越高                          |
| `level`          | VARCHAR(32)   |  否 | NULL                | 模型等级，例如 `LIGHT`、`STANDARD`、`ADVANCED`      |
| `capabilities`   | JSONB         |  是 | `[]`                | 能力列表，例如 `CHAT`、`TOOL_CALLING`、`VISION`     |
| `status`         | VARCHAR(16)   |  是 | `ACTIVE`            | 状态：`ACTIVE`、`DISABLED`                     |
| `is_default`     | BOOLEAN       |  是 | `FALSE`             | 是否为租户默认模型                                  |
| `create_by`      | BIGINT        |  是 | -                   | 创建用户 ID                                    |
| `update_by`      | BIGINT        |  否 | NULL                | 更新用户 ID                                    |
| `create_time`    | TIMESTAMPTZ   |  是 | `CURRENT_TIMESTAMP` | 创建时间                                       |
| `update_time`    | TIMESTAMPTZ   |  是 | `CURRENT_TIMESTAMP` | 更新时间                                       |
| `delete_time`    | TIMESTAMPTZ   |  否 | NULL                | 软删除时间                                      |

**约束与索引**

```text
PRIMARY KEY (id)
UNIQUE (tenant_id, name)
```

### `t_prompt_templates`

Prompt 模板及版本表。

| 字段            | 类型            | 必填 | 默认值                 | 说明                                      |
| ------------- | ------------- | -: | ------------------- | --------------------------------------- |
| `id`          | BIGINT        |  是 | -                   | Prompt 模板版本主键                           |
| `tenant_id`   | BIGINT        |  是 | -                   | 所属租户 ID                                 |
| `prompt_type` | VARCHAR(32)   |  是 | -                   | 类型：`SYSTEM`、`PLANNER`、`RCA`、`SUMMARY` 等 |
| `prompt_key`  | VARCHAR(128)  |  是 | -                   | 稳定的 Prompt 业务标识                         |
| `name`        | VARCHAR(128)  |  是 | -                   | Prompt 显示名称                             |
| `description` | VARCHAR(1024) |  否 | NULL                | Prompt 用途说明                             |
| `version`     | INTEGER       |  是 | `1`                 | Prompt 版本号                              |
| `content`     | TEXT          |  是 | -                   | Prompt 模板正文                             |
| `variables`   | JSONB         |  是 | `[]`                | 模板变量定义                                  |
| `status`      | VARCHAR(16)   |  是 | `DRAFT`             | 状态：`DRAFT`、`ACTIVE`、`ARCHIVED`          |
| `is_default`  | BOOLEAN       |  是 | `FALSE`             | 是否为该 Prompt Key 的默认版本                   |
| `create_by`   | BIGINT        |  是 | -                   | 创建用户 ID                                 |
| `create_time` | TIMESTAMPTZ   |  是 | `CURRENT_TIMESTAMP` | 创建时间                                    |
| `update_time` | TIMESTAMPTZ   |  是 | `CURRENT_TIMESTAMP` | 更新时间                                    |

**约束与索引**

```text
PRIMARY KEY (id)
UNIQUE (tenant_id, prompt_key, version)
```

### `t_notification_channels`

通知渠道配置表。

| 字段                   | 类型            | 必填 | 默认值                 | 说明                                     |
| -------------------- | ------------- | -: | ------------------- | -------------------------------------- |
| `id`                 | BIGINT        |  是 | -                   | 通知渠道主键                                 |
| `tenant_id`          | BIGINT        |  是 | -                   | 所属租户 ID                                |
| `name`               | VARCHAR(128)  |  是 | -                   | 渠道名称                                   |
| `channel_type`       | VARCHAR(32)   |  是 | -                   | 渠道类型：`WEBHOOK`                         |
| `config`             | JSONB         |  是 | `{}`                | 渠道非敏感配置                                |
| `credential`         | VARCHAR(256)  |  否 | NULL                | 敏感凭证                                 |
| `status`             | VARCHAR(16)   |  是 | `ACTIVE`            | 状态：`ACTIVE`、`DISABLED`                 |
| `create_by`          | BIGINT        |  是 | -                   | 创建用户 ID                                |
| `update_by`          | BIGINT        |  否 | NULL                | 更新用户 ID                                |
| `create_time`        | TIMESTAMPTZ   |  是 | `CURRENT_TIMESTAMP` | 创建时间                                   |
| `update_time`        | TIMESTAMPTZ   |  是 | `CURRENT_TIMESTAMP` | 更新时间                                   |
| `delete_time`        | TIMESTAMPTZ   |  否 | NULL                | 软删除时间                                  |

**约束与索引**

```text
PRIMARY KEY (id)
UNIQUE (tenant_id, name)
```

### `t_system_settings`

系统配置表，支持租户级 Key-Value 配置。

| 字段              | 类型            | 必填 | 默认值                 | 说明                                     |
| --------------- | ------------- | -: | ------------------- | -------------------------------------- |
| `id`            | BIGINT        |  是 | -                   | 配置主键                                   |
| `tenant_id`     | BIGINT        |  是 | -                   | 所属租户 ID                                |
| `category`      | VARCHAR(64)   |  是 | -                   | 配置分类，例如 `GENERAL`、`AGENT`、`SECURITY`   |
| `description`   | VARCHAR(1024) |  否 | NULL                | 配置说明                                   |
| `setting_key`   | VARCHAR(128)  |  是 | -                   | 配置键                                    |
| `setting_value` | JSONB         |  是 | -                   | 配置值                                    |
| `is_sensitive`  | BOOLEAN       |  是 | `FALSE`             | 是否包含敏感信息                               |
| `create_by`     | BIGINT        |  是 | -                   | 创建用户 ID                                |
| `update_by`     | BIGINT        |  否 | NULL                | 更新用户 ID                                |
| `create_time`   | TIMESTAMPTZ   |  是 | `CURRENT_TIMESTAMP` | 创建时间                                   |
| `update_time`   | TIMESTAMPTZ   |  是 | `CURRENT_TIMESTAMP` | 更新时间                                   |

**约束与索引**

```text
PRIMARY KEY (id)
UNIQUE (tenant_id, category, setting_key)
```

### `t_audit_logs`

平台操作审计日志。该表采用追加写入，不支持业务更新和软删除。

| 字段              | 类型            | 必填 | 默认值                 | 说明                                       |
| --------------- | ------------- | -: | ------------------- | ---------------------------------------- |
| `id`            | BIGINT        |  是 | -                   | 审计日志主键                                   |
| `tenant_id`     | BIGINT        |  是 | -                   | 所属租户 ID                                  |
| `action`        | VARCHAR(64)   |  是 | -                   | 操作类型，例如 `CREATE_INCIDENT`、`UPDATE_MODEL` |
| `detail`        | JSONB         |  是 | `{}`                | 操作详情，必须过滤敏感信息                            |
| `result`        | VARCHAR(16)   |  是 | -                   | 操作结果：`SUCCESS`、`FAILED`                  |
| `resource_type` | VARCHAR(64)   |  是 | -                   | 资源类型                                     |
| `resource_id`   | VARCHAR(128)  |  否 | NULL                | 资源 ID                                    |
| `user_type`    | VARCHAR(16)   |  是 | `USER`              | 操作者类型：`USER`、`SYSTEM`、`API_KEY`          |
| `user_id`       | BIGINT        |  否 | NULL                | 操作用户 ID，系统操作时可为空                         |
| `request_id`    | VARCHAR(128)  |  否 | NULL                | 请求 ID                                    |
| `trace_id`      | VARCHAR(64)   |  否 | NULL                | 分布式追踪 ID                                 |
| `http_method`   | VARCHAR(16)   |  否 | NULL                | HTTP Method                              |
| `request_path`  | VARCHAR(1024) |  否 | NULL                | 请求路径                                     |
| `client_ip`     | VARCHAR(64)   |  否 | NULL                | 客户端 IP                                   |
| `error_code`    | VARCHAR(64)   |  否 | NULL                | 失败错误码                                    |
| `create_time`   | TIMESTAMPTZ   |  是 | `CURRENT_TIMESTAMP` | 操作发生时间                                   |

**约束与索引**

```text
PRIMARY KEY (id)
INDEX (tenant_id, create_time DESC)
```
