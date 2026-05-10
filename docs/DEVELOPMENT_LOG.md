# 开发过程记录（后补）

> 本文档用于追溯开发过程中的关键决策与迭代路径，暴露流程问题并指导改进。

---

## 时间线

### Phase 1：基础框架搭建（~30 min）
- 直接创建目录结构（`src/collectors`, `src/agents`, ...）
- 编写 `requirements.txt`，假设所有依赖可用
- **问题**：未先验证环境依赖可用性，导致后续大量返工

### Phase 2：核心模块编码（~60 min）
- 编写 ArxivCollector、RSSCollector
- 编写 ScreenerAgent、SummarizerAgent、InsightGeneratorAgent
- 编写 VectorStore（ChromaDB）、MetadataStore
- **问题**：未写接口契约，模块间数据格式在编码中逐步确定

### Phase 3：首次运行与严重阻塞（~20 min）
- 发现 pip 无法联网安装依赖
- 发现 hermes-agent venv 中只有部分包
- **返工**：重写 VectorStore（ChromaDB → NumPy TF-IDF）
- **返工**：重写 ReportGenerator（PPT → Markdown）
- **返工**：重写 Collectors（去掉 feedparser、arxiv 库）

### Phase 4：适配与调通（~40 min）
- 适配可用依赖（requests, openai, yaml, numpy）
- 添加 MOCK 模式（无 API Key 可运行）
- 修复 RSS 时间解析错误
- 修复中文文件名乱码
- 修复向量存储路径不一致

### Phase 5：需求扩展（~40 min）
- 用户要求增加 Intel/AMD/ETH/MIT/通信公司追踪
- 添加 RSS 源、更新 screener 关键词
- 实现 BlogScraperCollector
- 实现机构加权机制

### Phase 6：双维度报告（~20 min）
- 实现机构维度聚类 `_cluster_by_org()`
- 实现 `generate_org_brief()` 报告模板
- 修复机构名称大小写标准化

---

## 流程问题清单

| # | 问题 | 严重程度 | 影响 |
|---|------|---------|------|
| 1 | **无前期设计文档** | 🔴 高 | 架构在编码中漂移，模块职责边界模糊 |
| 2 | **未先验证环境约束** | 🔴 高 | 假设依赖可用，导致大量返工 |
| 3 | **接口契约后补** | 🟡 中 | 数据格式在模块间传递时反复调整 |
| 4 | **无单元测试** | 🟡 中 | 只能靠端到端运行验证，调试效率低 |
| 5 | **commit 粒度失控** | 🟡 中 | 所有改动一次性写入，无版本回溯点 |
| 6 | **需求在开发中膨胀** | 🟡 中 | 从"技术方向报告"扩展到"机构动态报告"，架构未预留扩展点 |

---

## 应该遵循的正确流程

```
1. 需求澄清与范围定义（10%）
   └─ 输出：《需求规格说明书》

2. 架构设计（20%）
   └─ 输出：《架构设计文档》《接口契约》《数据模型》
   └─ 评审：模块边界、扩展性、技术选型

3. 环境验证与原型验证（10%）
   └─ 输出：《环境可行性报告》
   └─ 验证：依赖可用性、网络连通性、LLM API 可用性

4. 迭代开发（50%）
   └─ 每模块：编码 → 单元测试 → 提交
   └─ 输出：可运行的增量版本

5. 集成测试与调优（10%）
   └─ 输出：《测试报告》《性能基线》
```

---

## 改进措施（已执行）

- [x] 补充架构设计文档 `docs/ARCHITECTURE.md`
- [x] 补充数据流文档 `docs/DATA_FLOW.md`
- [x] 补充接口契约 `docs/API.md`
- [x] 补充开发日志 `docs/DEVELOPMENT_LOG.md`
- [ ] 补充单元测试（待执行）
- [ ] 补充 CI/CD 流水线（待执行）
