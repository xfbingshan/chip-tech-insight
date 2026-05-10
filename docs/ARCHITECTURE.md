# 芯片技术洞察平台 — 架构设计文档

> 文档状态：后补（开发完成后追溯编写）  
> 版本：v1.0  
> 日期：2026-05-10

---

## 1. 设计目标

构建一个自动化技术情报系统，能够：
- 持续采集芯片设计、体系架构、通信基站领域的最新文献与新闻
- 通过 LLM 进行相关性筛选、摘要提取、价值评估
- 基于向量的语义去重
- 按技术方向和机构维度双维度聚合
- 自动生成 Markdown 洞察报告（技术快讯 + 深度洞察 + 机构动态）

---

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         外部数据源                                │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────────┐ │
│  │  arXiv  │  │  RSS    │  │  博客爬虫 │  │  后续扩展：专利/API  │ │
│  │  (Atom) │  │  (XML)  │  │  (HTML) │  │                     │ │
│  └────┬────┘  └────┬────┘  └────┬────┘  └─────────────────────┘ │
└───────┼────────────┼────────────┼─────────────────────────────────┘
        │            │            │
        └────────────┴────────────┘
                     │
        ┌────────────▼────────────┐
        │    采集层 Collectors     │
        │  - ArxivCollector        │
        │  - RSSCollector          │
        │  - BlogScraperCollector  │
        └────────────┬────────────┘
                     │ List[Dict]
        ┌────────────▼────────────┐
        │    认知层 Agents         │
        │  - ScreenerAgent         │
        │  - SummarizerAgent       │
        │  - InsightGeneratorAgent │
        └────────────┬────────────┘
                     │ List[Dict] (含 assessment)
        ┌────────────▼────────────┐
        │    存储层 Storage        │
        │  - VectorStore (TF-IDF)  │
        │  - MetadataStore (JSONL) │
        └────────────┬────────────┘
                     │ List[Dict]
        ┌────────────▼────────────┐
        │    聚合层 Scheduler      │
        │  - 技术方向聚类          │
        │  - 机构维度聚类          │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │    报告层 Reporting      │
        │  - Flash Brief (1页)     │
        │  - Deep Dive (多页)      │
        │  - Org Brief (机构动态)   │
        └─────────────────────────┘
```

---

## 3. 模块职责

| 模块 | 职责 | 关键类 |
|------|------|--------|
| `collectors` | 多源数据采集 | `ArxivCollector`, `RSSCollector`, `BlogScraperCollector` |
| `agents` | LLM 认知处理 | `ScreenerAgent`, `SummarizerAgent`, `InsightGeneratorAgent` |
| `storage` | 数据持久化与去重 | `VectorStore`, `MetadataStore` |
| `scheduler` | 工作流编排 | `InsightPipeline` |
| `reporting` | 报告生成 | `ReportGenerator` |
| `utils` | 配置与工具 | `Config` |

---

## 4. 关键技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| 向量存储 | 自研 TF-IDF + NumPy | 零外部依赖，适配受限环境 |
| 相似度算法 | 余弦相似度 | 简单有效，适合文本去重 |
| LLM 调用 | OpenAI API | 业界主流，prompt 可控 |
| 报告格式 | Markdown | 轻量、可转 PPT、易阅读 |
| 配置管理 | YAML + dotenv | 结构化配置 + 敏感信息隔离 |

---

## 5. 扩展性设计

- **采集器插件化**：新增数据源只需实现 `fetch() -> List[Dict]` 接口
- **Agent 可替换**：LLM  Provider 可从 OpenAI 切换为 Claude / 本地模型
- **报告模板可扩展**：新增报告类型只需在 `ReportGenerator` 中添加方法
- **双维度聚合**：技术维度与机构维度独立聚类，互不干扰
