"""
洞察生成 Agent：聚合多篇文献，生成深度洞察
"""

import json
import re
from typing import Any, Dict, List
from openai import OpenAI
from src.utils.config import config


class InsightGeneratorAgent:
    SYSTEM_PROMPT_FLASH = """你是芯片技术规划专家。
基于以下技术文献，生成一份"技术快讯"（One-Pager）内容。

【强制要求】你必须且只能输出纯 JSON，不要任何 markdown 代码块标记，不要任何解释或分析文字。JSON 必须能被 Python json.loads 直接解析。

要求：
1. 技术名称：用一句话定义该技术方向
2. 关键创新：3-4 个核心进展 bullet
3. 成熟度评估：TRL 等级（1-9）及理由
4. 主要玩家：该方向的主要公司/机构
5. 一句话建议：对芯片设计团队的行动建议

输出 JSON 格式示例：
{"技术名称":"...","关键创新":["...","..."],"成熟度评估":{"等级":5,"理由":"..."},"主要玩家":["..."],"一句话建议":"..."}
"""

    SYSTEM_PROMPT_DEEP = """你是芯片技术战略专家。
基于以下多篇相关文献，生成一份"深度洞察报告"内容。

【强制要求】你必须且只能输出纯 JSON，不要任何 markdown 代码块标记，不要任何解释或分析文字。JSON 必须能被 Python json.loads 直接解析。

要求按以下章节组织：
1. 封面标题 + 核心结论前置（一句话总结该技术方向的战略价值）
2. 背景与动机：该技术试图解决什么行业痛点？（2-3 句）
3. 技术原理：用通俗语言解释核心机制（不超过 150 字）
4. 业界进展：时间线或关键里程碑（列表）
5. 竞争格局矩阵：主要玩家的技术路线对比（表格形式 JSON）
6. 优劣势分析：SWOT 式分析
7. 对芯片设计的启示：具体落地建议（3 条）
8. 行动建议：短期（3个月）/中期（1年）/长期（3年）

输出 JSON 格式，所有字符串值使用中文。"""

    def __init__(self) -> None:
        cfg = config.llm
        self.model = cfg.get("model", "gpt-4o-mini")
        self.temperature = 0.4
        self.max_tokens = 3000

        api_key = config.openai_api_key
        if api_key and api_key.startswith("sk-"):
            client_kwargs = {"api_key": api_key, "base_url": config.openai_base_url}
            if config.openai_default_headers:
                client_kwargs["default_headers"] = config.openai_default_headers
            self.client = OpenAI(**client_kwargs)
            self.use_mock = False
        else:
            self.client = None
            self.use_mock = True
            print(
                "[InsightGenerator] OPENAI_API_KEY not set, using MOCK mode for demo."
            )

    def generate_flash(self, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        if self.use_mock:
            return self._mock_flash(docs)

        context = self._build_context(docs)
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT_FLASH},
                {"role": "user", "content": context},
            ],
        )
        return self._parse_json_response(response.choices[0].message.content, "flash")

    def generate_deep_dive(self, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        if self.use_mock:
            return self._mock_deep_dive(docs)

        context = self._build_context(docs)
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT_DEEP},
                {"role": "user", "content": context},
            ],
        )
        return self._parse_json_response(
            response.choices[0].message.content, "deep_dive"
        )

    def _build_context(self, docs: List[Dict[str, Any]]) -> str:
        lines = [f"共 {len(docs)} 篇相关文献：\n"]
        for i, doc in enumerate(docs, 1):
            assessment = doc.get("assessment", {})
            summary = doc.get("structured_summary", {})
            lines.append(f"--- 文献 {i} ---")
            lines.append(f"标题：{doc.get('title', '')}")
            lines.append(f"摘要：{doc.get('abstract', '')[:500]}...")
            lines.append(f"关键创新：{', '.join(summary.get('innovations', [])[:2])}")
            lines.append(f"成熟度：TRL-{assessment.get('trl', 'N/A')}")
            lines.append("")
        return "\n".join(lines)

    def _parse_json_response(self, content: str, default_type: str) -> Dict[str, Any]:
        content = re.sub(r"```json\s*", "", content)
        content = re.sub(r"```\s*", "", content)
        try:
            return json.loads(content.strip())
        except (json.JSONDecodeError, ValueError):
            return {"raw": content, "type": default_type}

    def _mock_flash(self, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Mock 快讯生成"""
        assessment = docs[0].get("assessment", {})
        category = assessment.get("category", "芯片技术")
        keywords = assessment.get("keywords", [])

        return {
            "技术名称": f"{category} 方向：{', '.join(keywords[:2])}"
            if keywords
            else f"{category} 技术进展",
            "关键创新": [
                "文献聚类显示该方向近期有多项相关研究",
                f"涉及 {len(docs)} 篇最新论文/报道",
                "具体创新细节建议阅读原文获取",
            ],
            "成熟度评估": {
                "等级": assessment.get("trl", 4),
                "理由": "基于文献中提到的实验验证程度初步判断",
            },
            "主要玩家": assessment.get("key_players", []) or ["待进一步调研"],
            "一句话建议": f"建议持续关注 {category} 方向进展，评估与当前项目的关联性。",
        }

    def _mock_deep_dive(self, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Mock 深度洞察生成"""
        assessment = docs[0].get("assessment", {})
        category = assessment.get("category", "芯片技术")

        return {
            "封面标题": f"{category} 深度洞察报告",
            "核心结论": f"{category} 方向近期活跃度高，建议纳入技术雷达跟踪。",
            "背景与动机": f"随着芯片复杂度持续提升，{category} 方向的研究日益活跃。当前收集到 {len(docs)} 篇相关文献，显示学术界和业界正在积极探索。",
            "技术原理": "该技术方向的核心机制涉及新型架构设计、先进工艺或创新封装方法，旨在突破传统芯片设计的性能、功耗或面积瓶颈。",
            "业界进展": [
                "近期多篇文献集中发表",
                "实验验证与原型设计阶段并进",
                "产业化路径尚在探索中",
            ],
            "竞争格局矩阵": [
                {
                    "玩家": "学术界",
                    "技术路线": "前沿探索",
                    "成熟度": "TRL 3-5",
                    "优势": "创新性强",
                    "劣势": "产业化距离远",
                },
                {
                    "玩家": "头部企业",
                    "技术路线": "工程落地",
                    "成熟度": "TRL 6-8",
                    "优势": "资源整合",
                    "劣势": "披露信息有限",
                },
            ],
            "优劣势分析": {
                "优势": ["技术创新潜力大", "与现有流程兼容性较好"],
                "劣势": ["成熟度尚低", "工具链支持不完善"],
                "机会": ["AI 驱动需求爆发", "先进封装技术演进"],
                "威胁": ["技术路线不确定性", "投资回报周期长"],
            },
            "对芯片设计的启示": [
                "评估该技术对当前产品路线图的影响",
                "关注相关 EDA 工具和 IP 的可用性",
                "提前布局关键人才和合作资源",
            ],
            "行动建议": {
                "短期": "完成技术可行性初步评估，明确适用场景。",
                "中期": "建立原型验证环境，开展小规模实验。",
                "长期": "根据验证结果决定是否纳入产品路线图。",
            },
        }
