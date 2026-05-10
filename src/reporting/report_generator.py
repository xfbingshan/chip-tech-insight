"""
报告生成器 - 生成 Markdown 格式洞察报告
有 python-pptx 时可扩展为 PPT 输出
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from src.utils.config import config

class ReportGenerator:
    def __init__(self):
        self.output_dir = Path(config.reporting.get("output_dir", "./data/reports"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_flash_brief(self, content: Dict, docs: List[Dict]) -> str:
        """生成技术快讯（Markdown 单页）"""
        lines = []
        lines.append("# 技术快讯 | " + content.get("技术名称", "Unknown"))
        lines.append(f"\n**生成日期**: {datetime.now().strftime('%Y-%m-%d')}  ")
        lines.append(f"**情报来源**: {', '.join(set(d.get('source', '') for d in docs))}\n")
        lines.append("---\n")
        
        lines.append("## 一句话定义\n")
        lines.append(content.get("技术名称", "") + "\n")
        
        lines.append("## 关键创新\n")
        for item in content.get("关键创新", []):
            lines.append(f"- {item}")
        lines.append("")
        
        trl = content.get("成熟度评估", {})
        lines.append("## 成熟度评估\n")
        lines.append(f"**TRL-{trl.get('等级', 'N/A')}** | {trl.get('理由', '')}\n")
        
        lines.append("## 主要玩家\n")
        players = content.get("主要玩家", [])
        lines.append(", ".join(players) + "\n")
        
        lines.append("## 行动建议\n")
        lines.append(f"> 💡 **{content.get('一句话建议', '建议持续关注该技术方向')}**\n")
        
        lines.append("---\n")
        lines.append("### 参考来源\n")
        for d in docs[:5]:
            lines.append(f"- [{d.get('title', '')}]({d.get('pdf_url', '')}) ({d.get('source', '')})")
        
        md_text = "\n".join(lines)
        filename = f"FlashBrief_{datetime.now().strftime('%Y%m%d')}_{self._safe_name(content.get('技术名称', 'unknown'))}.md"
        filepath = Path(self.output_dir) / filename
        filepath.write_text(md_text, encoding="utf-8")
        return str(filepath)
    
    def generate_deep_dive(self, content: Dict, docs: List[Dict]) -> str:
        """生成深度洞察报告（Markdown 多页）"""
        lines = []
        lines.append("# 深度洞察 | " + content.get("封面标题", "Unknown"))
        lines.append(f"\n**生成日期**: {datetime.now().strftime('%Y年%m月%d日')}  ")
        lines.append(f"**核心结论**: {content.get('核心结论', '')}\n")
        lines.append("---\n")
        
        sections = [
            ("背景与动机", content.get("背景与动机", "")),
            ("技术原理", content.get("技术原理", "")),
        ]
        for title, text in sections:
            lines.append(f"## {title}\n")
            lines.append(text + "\n")
        
        milestones = content.get("业界进展", [])
        if milestones:
            lines.append("## 业界进展时间线\n")
            for m in milestones:
                lines.append(f"- {m}")
            lines.append("")
        
        matrix = content.get("竞争格局矩阵", [])
        if matrix:
            lines.append("## 竞争格局矩阵\n")
            headers = list(matrix[0].keys()) if matrix else []
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
            for row in matrix:
                lines.append("| " + " | ".join(str(row.get(h, "")) for h in headers) + " |")
            lines.append("")
        
        swot = content.get("优劣势分析", {})
        if swot:
            lines.append("## 优劣势与风险分析\n")
            for key in ["优势", "劣势", "机会", "威胁"]:
                vals = swot.get(key, [])
                if vals:
                    lines.append(f"### {key}\n")
                    for v in vals:
                        lines.append(f"- {v}")
                    lines.append("")
        
        implications = content.get("对芯片设计的启示", [])
        if implications:
            lines.append("## 对芯片设计的启示\n")
            for imp in implications:
                lines.append(f"- {imp}")
            lines.append("")
        
        actions = content.get("行动建议", {})
        if actions:
            lines.append("## 行动建议\n")
            for phase in [("短期（3个月）", "短期"), ("中期（1年）", "中期"), ("长期（3年）", "长期")]:
                label, key = phase
                val = actions.get(key, "")
                if val:
                    lines.append(f"### {label}\n")
                    lines.append(val + "\n")
        
        lines.append("---\n")
        lines.append("### 参考来源\n")
        for d in docs[:10]:
            lines.append(f"- [{d.get('title', '')}]({d.get('pdf_url', '')}) ({d.get('source', '')})")
        
        md_text = "\n".join(lines)
        filename = f"DeepDive_{datetime.now().strftime('%Y%m%d')}_{self._safe_name(content.get('封面标题', 'unknown'))}.md"
        filepath = Path(self.output_dir) / filename
        filepath.write_text(md_text, encoding="utf-8")
        return str(filepath)
    
    def generate_org_brief(self, org_name: str, docs: List[Dict]) -> str:
        """生成机构动态报告（按机构维度）"""
        lines = []
        lines.append(f"# 机构动态 | {org_name} 技术洞察")
        lines.append(f"\n**生成日期**: {datetime.now().strftime('%Y-%m-%d')}  ")
        lines.append(f"**文献数量**: {len(docs)} 篇  ")
        lines.append(f"**涉及方向**: {', '.join(sorted(set(d.get('assessment', {}).get('category', 'Other') for d in docs)))}\n")
        lines.append("---\n")
        
        lines.append("## 本周/近期核心动态\n")
        for i, doc in enumerate(docs, 1):
            assessment = doc.get("assessment", {})
            summary = doc.get("structured_summary", {})
            lines.append(f"### {i}. {doc.get('title', '')}")
            lines.append(f"- **技术分类**: {assessment.get('category', 'Other')}")
            lines.append(f"- **成熟度**: TRL-{assessment.get('trl', 'N/A')}")
            lines.append(f"- **价值分**: {assessment.get('value_score', 0)}/10")
            innovations = summary.get('innovations', [])
            if innovations:
                lines.append(f"- **关键创新**: {innovations[0]}")
            lines.append(f"- **来源**: [{doc.get('source', '')}]({doc.get('pdf_url', '')})")
            lines.append("")
        
        lines.append("---\n")
        lines.append("## 趋势判断\n")
        cats = [d.get('assessment', {}).get('category', 'Other') for d in docs]
        cat_counts = {}
        for c in cats:
            cat_counts[c] = cat_counts.get(c, 0) + 1
        top_cat = max(cat_counts, key=cat_counts.get) if cat_counts else "Unknown"
        lines.append(f"{org_name} 近期在 **{top_cat}** 方向布局最为密集，建议重点关注其技术路线与产品化节奏。\n")
        
        md_text = "\n".join(lines)
        filename = f"OrgBrief_{datetime.now().strftime('%Y%m%d')}_{self._safe_name(org_name)}.md"
        filepath = Path(self.output_dir) / filename
        filepath.write_text(md_text, encoding="utf-8")
        return str(filepath)
    
    def _safe_name(self, name: str) -> str:
        import re
        # 只保留 ASCII 字母数字和下划线，其余替换为空格后转下划线
        safe = re.sub(r"[^\x00-\x7F]+", " ", name)
        safe = re.sub(r"[^a-zA-Z0-9]+", "_", safe).strip("_")
        return safe[:50] if safe else "report"
