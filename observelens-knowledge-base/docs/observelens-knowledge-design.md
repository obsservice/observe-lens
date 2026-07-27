# ObserveLens Knowledge Base 服务设计文档

## 1. 文档概述

### 1.1 背景

ObserveLens 是面向 DEV/SRE 的 AI Native RCA 平台，能够围绕故障、告警、巡检和自然语言问题，主动调查生产环境并输出基于证据链的根因分析结果。

在故障调查过程中，Agent 除了需要查询实时指标、日志、调用链和资源拓扑，还需要使用企业内部积累的非结构化知识，例如：

* 运维 SOP 和 Runbook
* 系统架构及部署文档
* 历史故障复盘
* 产品和服务说明
* 配置手册
* 常见问题及处理经验
* 变更记录和排障案例

`observelens-knowledge-base` 用于统一管理这些文档，将原始文件加工为可检索的知识，并向 ObserveLens Agent 提供语义检索和知识问答能力。

---

## 2. 服务定位

### 2.1 核心定位

`observelens-knowledge-base` 是 ObserveLens 的非结构化知识管理与检索服务，负责：

1. 接收并管理知识文档。
2. 解析不同格式的文件。
3. 将文档切分为可检索的知识片段。
4. 生成并保存向量。
5. 提供混合检索和重排序能力。
6. 向 Agent 返回可引用的知识证据。
7. 管理文档版本、权限和索引状态。

该服务只负责“知识的加工与检索”，不直接负责 RCA 推理，也不负责与用户进行完整对话。

### 2.2 在 ObserveLens 中的位置

```text
                    ┌───────────────────────┐
                    │   observelens-web     │
                    │ Files / Search 页面   │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ observelens-service   │
                    │ 会话、权限、业务 API     │
                    └───────────┬───────────┘
                                │
               文档管理          │          Agent 检索
                                ▼
               ┌────────────────────────────────┐
               │ observelens-knowledge-base     │
               │                                │
               │ 文档解析 / Chunk / Embedding    │
               │ 混合检索 / Rerank / 引用         │
               └──────────┬───────────┬─────────┘
                          │           │
                          ▼           ▼
                 ┌─────────────┐ ┌──────────────┐
                 │ PostgreSQL  │ │ Object Store │
                 │ + pgvector  │ │ 原始文件      │
                 └─────────────┘ └──────────────┘
                          ▲
                          │
                    ┌─────┴──────────────┐
                    │ observelens-agent  │
                    │ RAG / RCA Workflow │
                    └────────────────────┘
```

---

## 3. 设计目标

### 3.1 功能目标

* 支持文档上传、更新、删除和查询。
* 支持 Markdown、TXT、PDF、DOCX、HTML 等常见格式。
* 支持文档异步解析和索引。
* 支持向量检索、关键词检索和混合检索。
* 支持按租户、知识库、文档类型、标签和实体过滤。
* 返回可追溯的文档来源和引用位置。
* 支持文档版本更新和索引重建。
* 支持面向 Agent 的稳定检索 API。
* 支持检索结果评估和反馈闭环。

### 3.2 非功能目标

* 多租户数据隔离。
* 文档与检索权限可控。
* 检索延迟可观测。
* 索引任务可重试、可恢复。
* Embedding 模型可替换。
* 避免知识库服务与具体 Agent 框架强绑定。
* 优先保持实现简单，适合 AI 辅助编码和长期维护。

### 3.3 暂不支持

MVP 阶段暂不承担以下能力：

* 通用企业搜索门户。
* 自动执行文档中的操作指令。
* 完整的知识图谱构建。
* 复杂文档协同编辑。
* 大规模互联网网页爬取。
* 基于知识库直接生成最终 RCA。
* 自动判断文档内容是否真实或正确。

---

## 4. 核心概念

### 4.1 Knowledge Base

知识库是文档的逻辑集合，用于隔离不同业务域或用途。

示例：

* Kafka 运维知识库
* Pulsar 运维知识库
* ObserveLens 产品文档
* 历史故障复盘
* SRE 通用 Runbook

### 4.2 Document

Document 表示一份用户可识别的原始文档。

一份 Document 包含：

* 文件名称
* 文件类型
* 来源
* 当前版本
* 标签
* 权限
* 索引状态
* 原始文件地址

### 4.3 Document Version

文档内容发生更新时创建新版本。

旧版本可保留用于审计，但默认只检索当前有效版本。

### 4.4 Chunk

Chunk 是文档经过解析和切分后形成的最小检索单元。

一个 Chunk 应当：

* 保留相对完整的语义。
* 能独立作为 Agent 的上下文。
* 包含可追溯的文档位置。
* 携带标题、章节、标签和实体等元数据。

### 4.5 Embedding

Embedding 是 Chunk 的向量表示，用于语义相似度检索。

Embedding 模型与业务逻辑解耦，允许通过配置切换不同模型。

### 4.6 Citation

Citation 表示检索结果对应的知识来源，包括：

* 文档 ID
* 文档名称
* 文档版本
* 章节标题
* 页码或段落位置
* 原始文件访问地址
* 内容片段

---

## 5. 总体架构

```text
┌──────────────────────────────────────────────────────┐
│                Knowledge Base API                    │
│                                                      │
│  KnowledgeBase API  Document API  Retrieval API      │
└──────────────────────────┬───────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────┐
│                   Application                       │
│                                                      │
│  Document Service     Retrieval Service              │
│  Indexing Service     Permission Service             │
│  Feedback Service     Citation Builder               │
└──────────────┬───────────────────────┬───────────────┘
               │                       │
┌──────────────▼────────────┐ ┌────────▼───────────────┐
│     Ingestion Pipeline    │ │   Retrieval Pipeline   │
│                           │ │                        │
│ Loader                    │ │ Query Rewrite          │
│ Parser                    │ │ Metadata Filter        │
│ Normalizer                │ │ Vector Search          │
│ Chunker                   │ │ Keyword Search         │
│ Metadata Extractor        │ │ Fusion                 │
│ Embedding                 │ │ Rerank                 │
│ Index Writer              │ │ Context Selection      │
└──────────────┬────────────┘ └────────┬───────────────┘
               │                       │
┌──────────────▼───────────────────────▼───────────────┐
│                   Infrastructure                     │
│                                                      │
│ PostgreSQL + pgvector                                │
│ Object Storage                                       │
│ Embedding Provider                                   │
│ Rerank Provider                                      │
│ Background Worker                                    │
└──────────────────────────────────────────────────────┘
```

---

## 6. 模块设计

为了提高代码局部聚合度，服务按业务能力组织，而不是按 Controller、Service、Repository 等技术分层拆散。

推荐目录如下：

```text
observelens-knowledge-base/
├── src/observelens_knowledge_base/
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   │
│   ├── knowledge_bases/
│   │   ├── api.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── repository.py
│   │   └── service.py
│   │
│   ├── documents/
│   │   ├── api.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── repository.py
│   │   ├── service.py
│   │   └── storage.py
│   │
│   ├── ingestion/
│   │   ├── pipeline.py
│   │   ├── loader.py
│   │   ├── parser.py
│   │   ├── normalizer.py
│   │   ├── chunker.py
│   │   ├── metadata.py
│   │   ├── embedding.py
│   │   └── indexer.py
│   │
│   ├── retrieval/
│   │   ├── api.py
│   │   ├── schemas.py
│   │   ├── service.py
│   │   ├── pipeline.py
│   │   ├── query_rewriter.py
│   │   ├── vector_search.py
│   │   ├── keyword_search.py
│   │   ├── fusion.py
│   │   ├── reranker.py
│   │   └── citation.py
│   │
│   ├── feedback/
│   │   ├── api.py
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── service.py
│   │
│   ├── providers/
│   │   ├── embedding/
│   │   ├── rerank/
│   │   └── object_storage/
│   │
│   ├── workers/
│   │   ├── tasks.py
│   │   └── runner.py
│   │
│   └── common/
│       ├── database.py
│       ├── exceptions.py
│       ├── pagination.py
│       ├── telemetry.py
│       └── security.py
│
├── migrations/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── scripts/
├── pyproject.toml
├── Dockerfile
└── README.md
```

---

## 7. 文档处理流程

### 7.1 整体流程

```text
上传文档
   ↓
保存原始文件
   ↓
创建文档版本
   ↓
提交索引任务
   ↓
加载文件
   ↓
解析正文
   ↓
内容清洗
   ↓
文档切分
   ↓
提取元数据
   ↓
生成 Embedding
   ↓
保存 Chunk 和向量
   ↓
激活新版本
   ↓
文档状态变为 READY
```

### 7.2 文档状态

```text
UPLOADED
   ↓
PENDING
   ↓
PROCESSING
   ↓
READY
```

异常状态：

```text
PROCESSING → FAILED
READY      → REINDEXING
REINDEXING → READY
REINDEXING → FAILED
```

建议枚举：

| 状态         | 说明          |
| ---------- | ----------- |
| UPLOADED   | 原始文件已经保存    |
| PENDING    | 等待执行索引      |
| PROCESSING | 正在解析和索引     |
| READY      | 当前版本可检索     |
| REINDEXING | 正在重建索引      |
| FAILED     | 处理失败        |
| ARCHIVED   | 文档已归档，不参与检索 |

### 7.3 文件解析

通过统一 Parser 接口适配不同文件格式：

```python
class DocumentParser(Protocol):
    async def parse(self, file: StoredFile) -> ParsedDocument:
        ...
```

解析后的统一结构：

```python
class ParsedDocument:
    title: str
    content: str
    sections: list[DocumentSection]
    metadata: dict[str, Any]
```

MVP 支持：

| 类型       | 处理方式         |
| -------- | ------------ |
| Markdown | 保留标题层级和代码块   |
| TXT      | 按段落解析        |
| HTML     | 去除菜单、脚本和无关标签 |
| DOCX     | 提取标题、段落和表格   |
| PDF      | 提取正文、页码和标题信息 |

扫描版 PDF 暂不默认开启 OCR，可作为后续扩展能力。

---

## 8. Chunk 切分策略

### 8.1 切分原则

Chunk 不是单纯按固定字符数截断，应尽量保留文档结构和语义边界。

优先级如下：

1. 标题章节。
2. Markdown 段落。
3. 列表或表格。
4. 空行。
5. 句子边界。
6. Token 数量。

### 8.2 推荐参数

MVP 默认配置：

```yaml
chunk:
  target_tokens: 600
  max_tokens: 900
  overlap_tokens: 100
  preserve_code_block: true
  preserve_table: true
```

对于 SOP 和 Runbook，可适当扩大 Chunk，避免将一个完整操作步骤拆散。

对于历史故障复盘，可按以下结构优先切分：

* 故障现象
* 影响范围
* 时间线
* 调查过程
* 根因
* 解决方案
* 改进措施

### 8.3 Chunk 元数据

每个 Chunk 至少保存：

```json
{
  "knowledge_base_id": "kb_001",
  "document_id": "doc_001",
  "document_version_id": "ver_001",
  "title": "Pulsar Broker Direct Memory OOM",
  "section_path": [
    "故障排查",
    "内存问题",
    "Direct Memory"
  ],
  "page_number": 12,
  "chunk_index": 8,
  "document_type": "POSTMORTEM",
  "tags": [
    "pulsar",
    "broker",
    "direct-memory"
  ],
  "entities": [
    {
      "type": "SERVICE",
      "name": "pulsar-broker"
    }
  ]
}
```

---

## 9. 检索设计

### 9.1 检索流程

```text
用户问题
   ↓
Query 标准化
   ↓
可选 Query Rewrite
   ↓
权限与元数据过滤
   ↓
向量检索 ──────┐
              ├─→ 融合排序 → Rerank → 去重 → 上下文选择
关键词检索 ────┘
   ↓
构建 Citation
   ↓
返回 Agent
```

### 9.2 混合检索

仅依赖向量检索会对服务名、错误码、配置项和类名等精确文本表现较弱。

因此默认采用：

* Vector Search：检索语义相近内容。
* Full-Text Search：检索错误码、类名、配置项和关键词。
* Metadata Filter：限定租户、知识库、标签、实体和文档类型。
* Rerank：对候选结果进行二次排序。

建议检索参数：

```yaml
retrieval:
  vector_top_k: 30
  keyword_top_k: 30
  fusion_top_k: 20
  rerank_top_k: 10
  final_top_k: 6
```

### 9.3 融合算法

MVP 推荐使用 Reciprocal Rank Fusion，避免对不同检索方式的分数进行复杂归一化。

```text
score(document) =
    Σ 1 / (k + rank)
```

其中 `k` 可设置为 60。

### 9.4 Query Rewrite

Query Rewrite 不应默认对所有请求调用大模型。

建议仅在以下情况下启用：

* 用户问题过长。
* 用户问题包含多个子问题。
* 需要提取错误码、组件名或配置项。
* 需要结合实体上下文补全检索条件。

示例：

原始问题：

```text
为什么这个 Topic 在流量增加后开始大量从 Bookie 读取？
```

结合上下文改写为：

```text
Pulsar KoP 实时消费场景下，Broker managed ledger cache
命中率下降并从 Bookie 读取数据的原因和排查方法
```

### 9.5 检索请求

```json
{
  "query": "Pulsar Broker Direct Memory OOM 如何排查？",
  "knowledge_base_ids": [
    "kb_pulsar"
  ],
  "filters": {
    "document_types": [
      "SOP",
      "POSTMORTEM"
    ],
    "tags": [
      "pulsar"
    ],
    "entities": [
      {
        "type": "SERVICE",
        "name": "pulsar-broker"
      }
    ]
  },
  "top_k": 6,
  "rerank": true
}
```

### 9.6 检索结果

```json
{
  "query": "Pulsar Broker Direct Memory OOM 如何排查？",
  "results": [
    {
      "chunk_id": "chunk_001",
      "score": 0.92,
      "content": "当 Broker 出现 OutOfDirectMemoryError 时，应首先……",
      "citation": {
        "document_id": "doc_001",
        "document_name": "Pulsar Broker 内存故障处理手册",
        "document_version": 3,
        "section": "Direct Memory 排查",
        "page_number": 12,
        "source_url": "/api/v1/documents/doc_001/content"
      },
      "metadata": {
        "document_type": "SOP",
        "tags": [
          "pulsar",
          "direct-memory"
        ]
      }
    }
  ],
  "trace": {
    "vector_candidates": 30,
    "keyword_candidates": 18,
    "reranked_candidates": 10,
    "latency_ms": 186
  }
}
```

---

## 10. 数据模型

### 10.1 t_knowledge_bases

| 字段              | 类型        | 说明              |
| --------------- | --------- | --------------- |
| id              | UUID      | 主键              |
| tenant_id       | UUID      | 租户 ID           |
| name            | VARCHAR   | 知识库名称           |
| description     | TEXT      | 描述              |
| status          | VARCHAR   | ACTIVE、DISABLED |
| embedding_model | VARCHAR   | Embedding 模型    |
| created_by      | UUID      | 创建人             |
| created_at      | TIMESTAMP | 创建时间            |
| updated_at      | TIMESTAMP | 更新时间            |

唯一约束：

```text
tenant_id + name
```

### 10.2 t_documents

| 字段                 | 类型        | 说明             |
| ------------------ | --------- | -------------- |
| id                 | UUID      | 文档 ID          |
| tenant_id          | UUID      | 租户 ID          |
| knowledge_base_id  | UUID      | 所属知识库          |
| name               | VARCHAR   | 文档名称           |
| document_type      | VARCHAR   | 文档类型           |
| source_type        | VARCHAR   | UPLOAD、URL、API |
| current_version_id | UUID      | 当前有效版本         |
| status             | VARCHAR   | 文档状态           |
| tags               | JSONB     | 标签             |
| metadata           | JSONB     | 扩展元数据          |
| created_by         | UUID      | 创建人            |
| created_at         | TIMESTAMP | 创建时间           |
| updated_at         | TIMESTAMP | 更新时间           |
| archived_at        | TIMESTAMP | 归档时间           |

建议文档类型精简为：

| 类型        | 说明              |
| --------- | --------------- |
| GUIDE     | 架构说明、使用手册和技术文档  |
| SOP       | 标准操作流程和 Runbook |
| CASE      | 故障案例和复盘         |
| REFERENCE | API、配置项及参考资料    |
| OTHER     | 其他文档            |

### 10.3 t_document_versions

| 字段              | 类型        | 说明      |
| --------------- | --------- | ------- |
| id              | UUID      | 版本 ID   |
| tenant_id       | UUID      | 租户 ID   |
| document_id     | UUID      | 文档 ID   |
| version         | INTEGER   | 版本号     |
| file_name       | VARCHAR   | 原始文件名   |
| mime_type       | VARCHAR   | MIME 类型 |
| file_size       | BIGINT    | 文件大小    |
| content_hash    | VARCHAR   | 内容摘要    |
| storage_uri     | TEXT      | 原始文件地址  |
| parser_version  | VARCHAR   | 解析器版本   |
| chunk_config    | JSONB     | 切分配置    |
| embedding_model | VARCHAR   | 向量模型    |
| status          | VARCHAR   | 索引状态    |
| error_message   | TEXT      | 失败原因    |
| created_at      | TIMESTAMP | 创建时间    |
| indexed_at      | TIMESTAMP | 索引完成时间  |

### 10.4 t_document_chunks

| 字段                  | 类型        | 说明       |
| ------------------- | --------- | -------- |
| id                  | UUID      | Chunk ID |
| tenant_id           | UUID      | 租户 ID    |
| knowledge_base_id   | UUID      | 知识库 ID   |
| document_id         | UUID      | 文档 ID    |
| document_version_id | UUID      | 文档版本 ID  |
| chunk_index         | INTEGER   | Chunk 顺序 |
| content             | TEXT      | Chunk 内容 |
| content_tsv         | TSVECTOR  | 全文检索字段   |
| token_count         | INTEGER   | Token 数  |
| title               | VARCHAR   | Chunk 标题 |
| section_path        | JSONB     | 章节路径     |
| page_number         | INTEGER   | 页码       |
| metadata            | JSONB     | 元数据      |
| embedding           | VECTOR    | 向量       |
| created_at          | TIMESTAMP | 创建时间     |

核心索引：

```sql
CREATE INDEX idx_chunks_tenant_kb
ON t_document_chunks(tenant_id, knowledge_base_id);

CREATE INDEX idx_chunks_document_version
ON t_document_chunks(document_version_id);

CREATE INDEX idx_chunks_fts
ON t_document_chunks USING GIN(content_tsv);

CREATE INDEX idx_chunks_embedding
ON t_document_chunks
USING hnsw (embedding vector_cosine_ops);
```

### 10.5 t_index_tasks

| 字段                  | 类型        | 说明                               |
| ------------------- | --------- | -------------------------------- |
| id                  | UUID      | 任务 ID                            |
| tenant_id           | UUID      | 租户 ID                            |
| document_id         | UUID      | 文档 ID                            |
| document_version_id | UUID      | 文档版本 ID                          |
| task_type           | VARCHAR   | INDEX、REINDEX、DELETE             |
| status              | VARCHAR   | PENDING、RUNNING、SUCCEEDED、FAILED |
| retry_count         | INTEGER   | 重试次数                             |
| error_message       | TEXT      | 错误信息                             |
| started_at          | TIMESTAMP | 开始时间                             |
| finished_at         | TIMESTAMP | 完成时间                             |
| created_at          | TIMESTAMP | 创建时间                             |

### 10.6 t_retrieval_logs

| 字段               | 类型        | 说明     |
| ---------------- | --------- | ------ |
| id               | UUID      | 检索 ID  |
| tenant_id        | UUID      | 租户 ID  |
| query            | TEXT      | 原始问题   |
| rewritten_query  | TEXT      | 改写后的问题 |
| filters          | JSONB     | 检索过滤条件 |
| result_chunk_ids | JSONB     | 返回结果   |
| latency_ms       | INTEGER   | 检索延迟   |
| trace_id         | VARCHAR   | 链路 ID  |
| created_at       | TIMESTAMP | 创建时间   |

### 10.7 t_retrieval_feedback

| 字段               | 类型        | 说明                           |
| ---------------- | --------- | ---------------------------- |
| id               | UUID      | 反馈 ID                        |
| tenant_id        | UUID      | 租户 ID                        |
| retrieval_log_id | UUID      | 检索记录                         |
| chunk_id         | UUID      | Chunk ID                     |
| rating           | INTEGER   | 相关性评分                        |
| feedback_type    | VARCHAR   | RELEVANT、IRRELEVANT、OUTDATED |
| comment          | TEXT      | 反馈说明                         |
| created_by       | UUID      | 反馈人                          |
| created_at       | TIMESTAMP | 创建时间                         |

---

## 11. API 设计

基础路径：

```text
/api/v1
```

### 11.1 知识库管理

```text
POST   /knowledge-bases
GET    /knowledge-bases
GET    /knowledge-bases/{knowledge_base_id}
PATCH  /knowledge-bases/{knowledge_base_id}
DELETE /knowledge-bases/{knowledge_base_id}
```

### 11.2 文档管理

```text
POST   /knowledge-bases/{knowledge_base_id}/documents
GET    /knowledge-bases/{knowledge_base_id}/documents
GET    /documents/{document_id}
PATCH  /documents/{document_id}
DELETE /documents/{document_id}
POST   /documents/{document_id}/versions
GET    /documents/{document_id}/versions
GET    /documents/{document_id}/content
POST   /documents/{document_id}/reindex
```

上传接口使用：

```text
multipart/form-data
```

示例：

```text
POST /api/v1/knowledge-bases/{id}/documents
```

字段：

```text
file
name
document_type
tags
metadata
```

### 11.3 检索 API

```text
POST /retrieval/search
POST /retrieval/feedback
```

内部 Agent 可使用更稳定的语义化接口：

```text
POST /internal/v1/context/retrieve
```

该接口返回经过筛选和重排序的上下文，不暴露过多底层检索实现。

### 11.4 索引任务

```text
GET  /index-tasks/{task_id}
POST /index-tasks/{task_id}/retry
```

---

## 12. 与 Agent 的集成

### 12.1 Agent Tool 定义

Knowledge Base 可以作为 Agent 的一个工具：

```python
async def search_knowledge(
    query: str,
    knowledge_base_ids: list[str] | None = None,
    entity_type: str | None = None,
    entity_name: str | None = None,
    document_types: list[str] | None = None,
    top_k: int = 6,
) -> KnowledgeSearchResult:
    ...
```

### 12.2 使用场景

Agent 在以下阶段调用知识库：

1. 理解问题时查询系统背景。
2. 生成调查计划时查询 Runbook。
3. 工具执行失败时查询已知问题。
4. 发现异常现象后查询历史案例。
5. 输出 RCA 前查询对应的处置建议。
6. 输出结果时引用原始知识来源。

### 12.3 Observation 表达

知识检索结果作为 Observation 写入 AESP：

```json
{
  "id": "obs_001",
  "type": "observation.completed",
  "conversation_id": "conv_001",
  "run_id": "run_001",
  "data": {
    "observation_type": "knowledge",
    "tool_call_id": "tool_001",
    "summary": "找到 3 条与 Pulsar Direct Memory OOM 相关的内部知识",
    "result_ref": {
      "retrieval_id": "ret_001"
    },
    "items": [
      {
        "document_name": "Pulsar Broker 内存故障处理手册",
        "section": "Direct Memory 排查",
        "score": 0.92
      }
    ]
  }
}
```

知识库只提供证据，是否采信及如何用于 RCA，由 Agent 决定。

---

## 13. 权限与多租户

### 13.1 租户隔离

所有核心数据表必须包含 `tenant_id`。

任何检索请求都必须隐式注入当前租户条件：

```sql
WHERE tenant_id = :current_tenant_id
```

客户端不允许自行指定其他租户 ID。

### 13.2 权限模型

MVP 可采用知识库级权限：

| 权限     | 能力           |
| ------ | ------------ |
| READER | 浏览文档、执行检索    |
| EDITOR | 上传、更新和重新索引文档 |
| ADMIN  | 管理知识库和成员权限   |

后续可扩展：

* 文档级权限。
* 部门或用户组权限。
* 私有知识库。
* 跨租户共享知识库。

### 13.3 Agent 权限

Agent 发起检索时应携带：

```text
tenant_id
user_id
roles
conversation_id
run_id
```

Knowledge Base 根据调用用户权限过滤可检索内容，不能因为调用方是 Agent 就绕过权限控制。

---

## 14. 异步任务设计

### 14.1 为什么需要异步处理

PDF 或大型 DOCX 的解析、切分和 Embedding 可能耗时较长，不适合在上传请求内同步完成。

上传接口只负责：

1. 保存文件。
2. 创建 Document 和 DocumentVersion。
3. 创建索引任务。
4. 返回任务 ID。

### 14.2 MVP 实现

MVP 可直接使用 PostgreSQL 任务表加 Worker 轮询，避免过早引入复杂消息队列。

```text
API
 ↓
t_index_tasks
 ↓
Worker SELECT ... FOR UPDATE SKIP LOCKED
 ↓
执行 Pipeline
 ↓
更新任务状态
```

任务领取示例：

```sql
SELECT id
FROM t_index_tasks
WHERE status = 'PENDING'
ORDER BY created_at
FOR UPDATE SKIP LOCKED
LIMIT 1;
```

生产规模扩大后，可迁移到：

* Redis Queue
* Celery
* Temporal
* Kafka 或 Pulsar

索引 Pipeline 的业务接口保持不变。

### 14.3 幂等性

索引任务应以 `document_version_id` 为幂等边界。

执行索引前：

1. 清理该版本未完成的 Chunk。
2. 重新解析文件。
3. 在事务中写入新 Chunk。
4. 完成后切换 `current_version_id`。
5. 旧版本 Chunk 异步清理或保留。

不能在新版本索引未完成时覆盖当前可用版本。

---

## 15. Embedding 与 Rerank Provider

### 15.1 Provider 接口

```python
class EmbeddingProvider(Protocol):
    async def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        ...

    async def embed_query(
        self,
        text: str,
    ) -> list[float]:
        ...
```

```python
class RerankProvider(Protocol):
    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int,
    ) -> list[RerankResult]:
        ...
```

### 15.2 配置示例

```yaml
embedding:
  provider: openai_compatible
  model: text-embedding-model
  dimensions: 1024
  batch_size: 32
  timeout_seconds: 30

rerank:
  enabled: true
  provider: openai_compatible
  model: rerank-model
  timeout_seconds: 10
```

### 15.3 模型切换约束

同一知识库中的 Chunk 应使用相同维度的 Embedding。

切换 Embedding 模型时，需要：

1. 更新知识库模型配置。
2. 创建全量重建任务。
3. 生成新向量。
4. 完成后切换索引版本。

不能直接使用不同维度的向量覆盖原字段。

---

## 16. 可观测性设计

### 16.1 核心指标

文档处理：

```text
knowledge_document_upload_total
knowledge_index_task_total
knowledge_index_task_duration_seconds
knowledge_index_task_failed_total
knowledge_document_chunk_count
knowledge_embedding_request_total
knowledge_embedding_request_duration_seconds
knowledge_embedding_token_total
```

检索：

```text
knowledge_retrieval_total
knowledge_retrieval_duration_seconds
knowledge_vector_search_duration_seconds
knowledge_keyword_search_duration_seconds
knowledge_rerank_duration_seconds
knowledge_retrieval_result_count
knowledge_retrieval_empty_total
```

资源：

```text
knowledge_worker_active_tasks
knowledge_worker_pending_tasks
knowledge_database_connections
knowledge_object_storage_request_total
```

### 16.2 日志字段

统一输出：

```json
{
  "trace_id": "trace_001",
  "tenant_id": "tenant_001",
  "knowledge_base_id": "kb_001",
  "document_id": "doc_001",
  "document_version_id": "ver_001",
  "index_task_id": "task_001",
  "retrieval_id": "ret_001",
  "operation": "document_index",
  "duration_ms": 1260,
  "status": "success"
}
```

日志中不得输出：

* 完整文档内容。
* 完整用户问题上下文。
* Embedding 向量。
* 密钥和认证 Token。

---

## 17. 异常处理

统一错误结构：

```json
{
  "error": {
    "code": "DOCUMENT_PARSE_FAILED",
    "message": "Failed to parse document",
    "details": {
      "document_id": "doc_001"
    },
    "trace_id": "trace_001"
  }
}
```

主要错误码：

| 错误码                       | 说明             |
| ------------------------- | -------------- |
| KNOWLEDGE_BASE_NOT_FOUND  | 知识库不存在         |
| DOCUMENT_NOT_FOUND        | 文档不存在          |
| DOCUMENT_TYPE_UNSUPPORTED | 文件类型不支持        |
| DOCUMENT_TOO_LARGE        | 文件超过大小限制       |
| DOCUMENT_PARSE_FAILED     | 文档解析失败         |
| DOCUMENT_INDEX_FAILED     | 文档索引失败         |
| EMBEDDING_REQUEST_FAILED  | Embedding 调用失败 |
| RETRIEVAL_FAILED          | 检索执行失败         |
| RERANK_FAILED             | 重排序失败          |
| PERMISSION_DENIED         | 无访问权限          |
| INDEX_VERSION_CONFLICT    | 索引版本冲突         |

Rerank 失败时可降级为融合排序结果，不应直接导致整个检索失败。

Embedding 查询失败时无法执行向量检索，但可根据配置降级为关键词检索。

---

## 18. 配置设计

```yaml
server:
  host: 0.0.0.0
  port: 8080

database:
  url: postgresql+asyncpg://user:password@postgres/knowledge
  pool_size: 20
  max_overflow: 10

storage:
  provider: s3
  bucket: observelens-knowledge
  endpoint: http://minio:9000

document:
  max_file_size_mb: 100
  supported_types:
    - text/plain
    - text/markdown
    - text/html
    - application/pdf
    - application/vnd.openxmlformats-officedocument.wordprocessingml.document

chunk:
  target_tokens: 600
  max_tokens: 900
  overlap_tokens: 100

retrieval:
  vector_top_k: 30
  keyword_top_k: 30
  fusion_top_k: 20
  rerank_top_k: 10
  final_top_k: 6

worker:
  concurrency: 4
  poll_interval_seconds: 2
  max_retries: 3

embedding:
  provider: openai_compatible
  model: embedding-model
  dimensions: 1024
  batch_size: 32

rerank:
  enabled: true
  provider: openai_compatible
  model: rerank-model
```

敏感配置通过环境变量或 Secret 管理，不写入配置文件。

---

## 19. 部署设计

### 19.1 部署原则

`observelens-knowledge-base` 是一个业务服务，内部包含两类运行能力：

* **API Runtime**：负责文档管理、知识检索和任务查询。
* **Indexing Worker**：负责文档解析、Chunk 切分、Embedding 和索引写入。

两者共用同一套代码、镜像、数据库和配置，不属于两个独立微服务。

```text
observelens-knowledge-base
├── API Runtime
└── Indexing Worker
```

### 19.2 MVP 部署方式

MVP 阶段采用单 Deployment、单实例混合运行：

```text
┌─────────────────────────────────┐
│ observelens-knowledge-base      │
│                                 │
│  HTTP API                       │
│  Internal Indexing Worker       │
└───────────────┬─────────────────┘
                │
       ┌────────┴─────────┐
       ▼                  ▼
PostgreSQL + pgvector   S3 / MinIO
```

服务启动时，同时启动 API 和后台 Worker：

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
```

推荐初始配置：

```yaml
replicas: 1

worker:
  enabled: true
  concurrency: 1
```

该方式部署简单，适合初期文档数量和索引负载较低的场景。

### 19.3 任务调度

索引任务保存在 PostgreSQL 的 `t_index_tasks` 表中。

Worker 使用数据库锁领取任务：

```sql
SELECT id
FROM t_index_tasks
WHERE status = 'PENDING'
ORDER BY created_at
FOR UPDATE SKIP LOCKED
LIMIT 1;
```

该机制支持多个实例安全并发执行，无需额外引入消息队列或分布式锁。

索引任务以 `document_version_id` 作为幂等边界，避免同一文档版本被重复索引。

### 19.4 健康检查

服务提供：

```text
GET /health/live
GET /health/ready
```

其中：

* `live`：检查服务进程是否存活。
* `ready`：检查 PostgreSQL、pgvector 和对象存储是否可用。

远程 Embedding 服务短暂异常时，不建议直接将整个 API 标记为不可用，可降级为关键词检索。

---

## 20. 安全设计

* 上传文件需要校验 MIME 类型和文件扩展名。
* 设置单文件大小限制。
* 文件名不能直接作为对象存储路径。
* HTML 解析时移除脚本和危险标签。
* 原始文件访问必须经过权限校验。
* 防止 Prompt Injection 文档直接控制 Agent。
* 检索结果必须标记为“外部知识证据”，不能作为系统指令执行。
* 文档中的命令、脚本和操作步骤只作为文本返回。
* 敏感文档可配置禁止返回大段原文。
* 对文件下载和检索接口执行审计记录。

Agent 使用知识内容时，应明确区分：

```text
System Instruction
User Input
Tool Observation
Retrieved Knowledge
```

不能将 Retrieved Knowledge 拼接到 System Prompt 的高优先级区域。

---

## 21. 测试设计

### 21.1 单元测试

* 不同文档格式解析。
* Chunk 边界与 overlap。
* 元数据提取。
* RRF 融合算法。
* Citation 构建。
* 权限过滤。
* Provider 异常降级。

### 21.2 集成测试

* PostgreSQL + pgvector 写入和检索。
* 文档上传到完成索引。
* 版本更新与原子切换。
* 全文检索和向量检索融合。
* Worker 并发领取任务。
* 索引失败重试。

### 21.3 E2E 测试

```text
上传 Pulsar 故障文档
   ↓
等待文档状态 READY
   ↓
检索 Direct Memory OOM
   ↓
验证返回目标章节
   ↓
验证 Citation 可访问
   ↓
更新文档
   ↓
验证只检索最新版本
```

### 21.4 检索评估集

建议维护固定评估集：

```json
{
  "question": "Pulsar Broker Direct Memory OOM 如何排查？",
  "expected_documents": [
    "Pulsar Broker 内存故障处理手册"
  ],
  "expected_keywords": [
    "MaxDirectMemorySize",
    "Netty",
    "memory.stat"
  ]
}
```

评估指标：

* Recall@K
* Precision@K
* MRR
* NDCG
* 空结果率
* 人工相关性评分

---

## 22. MVP 范围

第一阶段优先实现：

1. 知识库 CRUD。
2. Markdown、TXT、PDF、DOCX 上传。
3. 文档异步索引。
4. PostgreSQL + pgvector 存储。
5. 基于章节的 Chunk 切分。
6. 向量检索与 PostgreSQL 全文检索。
7. RRF 混合排序。
8. 可选 Rerank。
9. 租户级隔离。
10. Citation 返回。
11. Agent 检索 Tool。
12. 基础指标和任务状态查询。

第一阶段不引入：

* Elasticsearch。
* 独立向量数据库。
* Kafka 或 Pulsar 任务队列。
* 复杂知识图谱。
* 多级文档审批流。
* 自动网页爬虫。
* 复杂 Agentic RAG。
* 多轮自主检索。

---

## 23. 后续演进

### 阶段一：基础 RAG

```text
文件上传
→ 文档解析
→ Chunk
→ Embedding
→ 混合检索
→ Citation
```

### 阶段二：检索质量提升

```text
Query Rewrite
→ Metadata 自动提取
→ Rerank
→ 检索评估集
→ 用户反馈
```

### 阶段三：面向 RCA 的知识增强

```text
实体关联
→ 故障类型识别
→ Runbook 定向检索
→ 历史案例相似度
→ 根因和解决方案结构化提取
```

### 阶段四：知识治理

```text
文档过期检测
→ 重复内容识别
→ 低质量知识检测
→ 负责人和有效期
→ 使用频率和命中率分析
```

后续可以将文档中的结构化关系同步到 Observability Catalog，例如：

```text
Runbook → applies_to → Service
Postmortem → caused_by → Change
SOP → operates_on → Cluster
Document → owned_by → Team
```

但知识原文、Chunk 和向量仍由 Knowledge Base 管理。

---

## 24. 关键设计决策

### 24.1 使用 PostgreSQL + pgvector

原因：

* ObserveLens 已使用 PostgreSQL。
* MVP 数据规模可控。
* 同时支持关系数据、JSON、全文检索和向量检索。
* 降低部署与运维复杂度。
* 支持事务化切换文档版本。
* 后续可在检索规模扩大后替换专用引擎。

### 24.2 原始文件与索引数据分离

* 原始文件保存在对象存储。
* 文档元数据、Chunk 和向量保存在 PostgreSQL。
* 数据库不保存完整二进制文件。
* 删除文档时分别清理数据库和对象存储。

### 24.3 索引采用异步 Pipeline

文档处理耗时且可能失败，异步 Pipeline 可以：

* 避免阻塞 API。
* 支持任务重试。
* 支持进度和状态展示。
* 支持后续独立扩容 Worker。

### 24.4 默认使用混合检索

运维知识中包含大量：

* 错误码
* Java 类名
* 配置名称
* 服务名
* Topic 名
* 日志原文

这些内容仅依赖向量检索容易丢失，因此默认采用向量检索与关键词检索融合。

### 24.5 Knowledge Base 不负责最终回答

Knowledge Base 只返回：

* 相关内容。
* 检索分数。
* 元数据。
* 引用来源。

Agent 负责：

* 判断知识是否与当前问题相关。
* 将知识与实时观测证据结合。
* 生成调查结论。
* 输出最终 RCA。

---

## 25. 总结

`observelens-knowledge-base` 的本质不是一个通用文件管理系统，而是 ObserveLens Agent 的知识证据服务。

其核心链路是：

```text
文档
→ 解析
→ Chunk
→ Embedding
→ 混合检索
→ Rerank
→ Citation
→ Agent 调查与 RCA
```

MVP 阶段应优先确保：

* 文档可以稳定索引。
* 检索结果与当前问题相关。
* 每条知识都可以追溯到原始文档。
* 不同租户和用户只能访问有权限的知识。
* 检索链路简单、可观测、可评估。
* Knowledge Base 与 Agent 推理解耦。

通过该服务，ObserveLens 可以将实时可观测数据与企业历史知识结合起来，使 Agent 不仅能够“看到当前发生了什么”，还能够理解“过去如何处理过类似问题”。
