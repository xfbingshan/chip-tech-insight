# 数据流与状态转换文档

## 1. 核心数据模型

### 1.1 原始文档 (Raw Document)
```python
{
    "id": str,           # 唯一标识
    "title": str,        # 标题
    "abstract": str,     # 摘要/正文
    "authors": List[str], # 作者列表
    "published": str,    # ISO 格式日期
    "pdf_url": str,      # 原文链接
    "source": str,       # 来源标识，如 "arxiv", "rss:Intel Newsroom"
    "category": str,     # 采集器预设分类
}
```

### 1.2 评估后文档 (Assessed Document)
在 Raw Document 基础上增加：
```python
{
    # ... Raw Document 字段
    "assessment": {
        "relevance": float,      # 0-10 相关性
        "category": str,         # 技术分类
        "summary": str,          # 一句话摘要
        "trl": int,              # 1-9 技术成熟度
        "value_score": float,    # 0-10 价值分
        "decision": str,         # Deep Dive / Flash Brief / Ignore
        "key_players": List[str],# 匹配的机构
        "keywords": List[str],   # 技术关键词
    },
    "structured_summary": {
        "innovations": List[str],
        "metrics": Dict[str, str],
        "limitations": List[str],
        "implications": List[str],
        "technical_depth": str,
    },
    "screened_at": str,  # ISO 时间戳
}
```

### 1.3 向量记录 (Vector Record)
```python
{
    "id": str,
    "vector": List[float],  # TF-IDF 向量
    "metadata": {
        "title": str,
        "source": str,
        "published": str,
        "category": str,
        "value_score": float,
    }
}
```

---

## 2. 数据流图

```
[外部源]
   │
   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Raw Docs   │───▶│  Screened   │───▶│  Summarized │
│  (采集层)    │    │  (初筛Agent) │    │  (摘要Agent) │
└─────────────┘    └─────────────┘    └──────┬──────┘
                                              │
                         ┌────────────────────┘
                         ▼
                  ┌─────────────┐
                  │ VectorStore │───▶ 去重判断
                  │  .add(doc)  │
                  └──────┬──────┘
                         │ 通过去重
                         ▼
                  ┌─────────────┐
                  │MetadataStore│───▶ 持久化 (JSONL)
                  │  .save(doc) │
                  └──────┬──────┘
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
┌─────────────────┐            ┌─────────────────┐
│ 技术方向聚类      │            │ 机构维度聚类      │
│ _cluster()      │            │ _cluster_by_org()│
└────────┬────────┘            └────────┬────────┘
         │                              │
         ▼                              ▼
┌─────────────────┐            ┌─────────────────┐
│ 技术报告生成      │            │ 机构动态报告      │
│ Deep/Flash Dive │            │ Org Brief       │
└─────────────────┘            └─────────────────┘
```

---

## 3. 状态转换表

| 阶段 | 输入状态 | 处理 | 输出状态 | 失败处理 |
|------|---------|------|---------|---------|
| 采集 | 无 | HTTP 请求 + 解析 | Raw Docs | 打印错误，跳过该源 |
| 初筛 | Raw Docs | LLM / 规则评估 | Screened Docs | 返回 None，丢弃 |
| 摘要 | Screened Docs | LLM / 规则提取 | Summarized Docs | 返回空摘要，保留文档 |
| 向量化 | Summarized Docs | TF-IDF 编码 | Vector + Metadata | 跳过，不入库 |
| 去重 | Vector | 余弦相似度比较 | 布尔 (is_new) | 标记 Duplicate，跳过 |
| 聚类 | 去重后 Docs | category / org 分组 | Clusters | 无 |
| 报告 | Clusters | Markdown 渲染 + PPT 生成 | Markdown + PPTX 文件 | Markdown 失败不影响 PPT，反之亦然 |
| 归档 | 报告文件路径列表 | 移动到日期子目录 + JSON 索引 | 归档记录 | 跳过，打印警告 |

---

## 4. 关键设计决策

### 决策 1：TF-IDF 替代 Embedding 模型
- **背景**：环境受限，无法安装 sentence-transformers
- **决策**：用 NumPy 实现轻量级 TF-IDF + 余弦相似度
- **影响**：去重精度略低于语义模型，但足够 MVP 使用

### 决策 2：Markdown + PPT 双格式输出
- **背景**：python-pptx 1.0.2 已可用
- **决策**：同时生成 Markdown（可读性）和 PPT（演示场景）
- **影响**：报告产出翻倍，但覆盖更多使用场景

### 决策 3：双维度并行聚类
- **背景**：用户既关心技术方向，也关心竞争对手动态
- **决策**：技术维度与机构维度独立聚类，分别生成报告
- **影响**：报告数量翻倍，但信息维度互补

### 决策 4：日期归档与自动清理
- **背景**：报告持续累积，需要历史管理
- **决策**：按运行日期归档，配置化保留天数，JSON 索引便于查询
- **影响**：磁盘空间可控，历史报告可回溯
