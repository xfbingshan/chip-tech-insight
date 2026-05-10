# 芯片技术洞察平台 (Chip Tech Insight)

[![CI](https://github.com/xfbingshan/chip-tech-insight/actions/workflows/ci.yml/badge.svg)](https://github.com/xfbingshan/chip-tech-insight/actions/workflows/ci.yml)
[![Lint](https://github.com/xfbingshan/chip-tech-insight/actions/workflows/lint.yml/badge.svg)](https://github.com/xfbingshan/chip-tech-insight/actions/workflows/lint.yml)

自动追踪业界与学术界芯片技术进展，生成结构化 PPT 洞察报告。

## 核心能力

- **多源采集**：arXiv、IEEE、技术博客 RSS、专利
- **智能初筛**：LLM 评估相关性、技术成熟度（TRL）、价值分
- **语义去重**：基于向量的相似度检测
- **自动聚类**：按技术方向聚合多篇文献
- **PPT 自动生成**：
  - **技术快讯（One-Pager）**：一般技术一页讲清
  - **深度洞察（Deep Dive）**：高价值技术 5-8 页详细分析

## 项目结构

```
chip-tech-insight/
├── config/
│   └── settings.yaml          # 采集源、阈值、模型配置
├── src/
│   ├── collectors/            # 数据采集器
│   ├── agents/                # LLM Agent（初筛/摘要/洞察）
│   ├── storage/               # 向量库 + 元数据存储
│   ├── reporting/             # PPT 报告生成
│   ├── scheduler/             # 工作流编排
│   └── utils/                 # 工具函数
├── templates/                 # PPT 模板（预留）
├── data/                      # 数据存储
│   ├── chroma_db/             # 向量数据库
│   ├── documents/             # 元数据索引
│   └── reports/               # 生成的 PPT 报告
├── main.py                    # 主入口
└── requirements.txt
```

## 持续集成

- **测试矩阵**：Python 3.10 / 3.11 / 3.12 × Ubuntu / Windows
- **代码质量**：Ruff linter + formatter
- 详见 [`.github/workflows/ci.yml`](.github/workflows/ci.yml) 与 [`.github/workflows/lint.yml`](.github/workflows/lint.yml)

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入你的 OPENAI_API_KEY
```

> **安全提示**：`.env` 已加入 `.gitignore`，不会误提交到 GitHub。请确保不要手动将真实 API Key 写入任何代码文件或配置文件中。
>
> 如果未配置 API Key，系统会自动降级为 **MOCK 模式**，使用基于关键词的启发式规则完成初筛和摘要（适合测试和演示，但分析质量低于 LLM 模式）。

### 3. 运行一次（测试模式）

```bash
python main.py --dry-run
```

### 4. 正式运行（保存数据并生成 PPT）

```bash
python main.py
```

### 5. 定时调度模式

```bash
# 每60分钟自动执行一次
python main.py --serve --interval 60
```

## 报告样例

### 技术快讯（One-Pager）
- 技术名称与一句话定义
- 关键创新（3-4 bullet）
- TRL 成熟度评估
- 主要玩家
- 一句话行动建议

### 深度洞察（Deep Dive）
1. 封面 + 核心结论前置
2. 背景与动机
3. 技术原理
4. 业界进展时间线
5. 竞争格局矩阵
6. 优劣势 SWOT 分析
7. 对芯片设计的启示
8. 短/中/长期行动建议

## 配置说明

编辑 `config/settings.yaml`：

- `collection.arxiv.categories`: 要追踪的 arXiv 分类
- `collection.rss.sources`: RSS 订阅源
- `screening.relevance_threshold`: 相关性阈值（0-10）
- `screening.focus_areas`: 重点关注的芯片技术方向
- `reporting.one_pager_threshold`: 深度报告触发阈值

## 设计文档

> 注：以下文档为开发完成后追溯补充，用于规范后续迭代。

| 文档 | 内容 |
|------|------|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | 系统架构、模块职责、技术选型 |
| [`docs/DATA_FLOW.md`](docs/DATA_FLOW.md) | 数据模型、状态转换、关键设计决策 |
| [`docs/API.md`](docs/API.md) | 模块接口契约、输入输出定义 |
| [`docs/DEVELOPMENT_LOG.md`](docs/DEVELOPMENT_LOG.md) | 开发过程追溯、问题清单、改进措施 |

## 后续扩展

- [ ] 接入 IEEE Xplore / ACM 官方 API
- [ ] 专利采集（USPTO/WIPO）
- [ ] 竞争格局可视化（网络图）
- [ ] 技术雷达图生成
- [ ] 飞书/邮件自动推送
- [ ] Streamlit 审核看板
