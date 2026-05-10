"""
初筛 Agent：判断相关性、分类、价值
"""
import json
import re
import os
from datetime import datetime
from typing import Dict, Optional
from openai import OpenAI
from src.utils.config import config

class ScreenerAgent:
    SYSTEM_PROMPT = """你是资深芯片技术规划专家，拥有20年半导体行业经验。
请对以下论文/文章进行结构化评估。

评估维度：
1. relevance (0-10): 与芯片设计、EDA、先进工艺、封装、架构创新直接相关的程度
2. category: 技术分类，必须从以下选择：Architecture, EDA, Process, Packaging, Memory, AI Chip, Interconnect, Photonics, Base Station / RAN, Other
3. summary: 一句话摘要，用非技术高管也能听懂的话概括核心价值
4. trl (1-9): 技术成熟度等级（1=原理验证，9=大规模量产）
5. value_score (0-10): 对芯片设计工程师的参考价值和潜在影响
6. decision: 处理建议，必须从以下选择：
   - "Deep Dive": 突破性或高价值技术，需深度分析
   - "Flash Brief": 一般性更新或渐进改进，一页简报即可
   - "Ignore": 相关性低或重复内容，直接忽略
7. key_players: 该技术方向的主要公司/机构（列表，最多3个）
8. keywords: 关键技术关键词（列表，最多5个）

输出严格 JSON 格式，不要任何 markdown 代码块标记。"""

    def __init__(self):
        cfg = config.llm
        self.model = cfg.get("model", "gpt-4o-mini")
        self.temperature = cfg.get("temperature", 0.3)
        self.max_tokens = cfg.get("max_tokens", 2000)
        self.threshold = config.screening.get("relevance_threshold", 6.0)
        self.focus_areas = config.screening.get("focus_areas", [])
        
        # 初始化 LLM 客户端（若未配置 API Key 则使用 mock）
        api_key = config.openai_api_key
        if api_key and api_key.startswith("sk-"):
            self.client = OpenAI(api_key=api_key, base_url=config.openai_base_url)
            self.use_mock = False
        else:
            self.client = None
            self.use_mock = True
            print("[Screener] OPENAI_API_KEY not set, using MOCK mode for demo.")
    
    def screen(self, doc: Dict) -> Optional[Dict]:
        if self.use_mock:
            return self._mock_screen(doc)
        
        text = f"标题：{doc.get('title', '')}\n\n摘要：{doc.get('abstract', '')[:2000]}"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
            )
            
            content = response.choices[0].message.content
            content = re.sub(r"```json\s*", "", content)
            content = re.sub(r"```\s*", "", content)
            
            result = json.loads(content.strip())
            
            if result.get("relevance", 0) < self.threshold:
                return None
            
            return {
                **doc,
                "assessment": result,
                "screened_at": datetime.now().isoformat(),
            }
            
        except Exception as e:
            print(f"[Screener Error] {doc.get('title', '')[:40]}: {e}")
            return None
    
    def batch_screen(self, docs: list) -> list:
        results = []
        for doc in docs:
            screened = self.screen(doc)
            if screened:
                results.append(screened)
        return results
    
    def _mock_screen(self, doc: Dict) -> Optional[Dict]:
        """Mock 模式：基于关键词规则做初筛，用于无 API Key 演示"""
        title = doc.get("title", "").lower()
        abstract = doc.get("abstract", "").lower()
        text = title + " " + abstract
        
        # 芯片相关关键词 + 目标机构关键词
        # 芯片相关关键词 + 目标机构关键词
        chip_keywords = ["chip", "processor", "cpu", "gpu", "asic", "fpga", "soc", "memory",
                         "dram", "sram", "cache", "interconnect", "packaging", "eda", "verification",
                         "synthesis", "layout", "transistor", "cmos", "finfet", "gaa", "photonics",
                         "optical", "quantum", "risc-v", "riscv", "architecture", "microarchitecture",
                         "chiplet", "3d ic", "tsv", "interposer", "die", "wafer", "lithography",
                         "annealing", "anneal", "neuromorphic", "in-memory computing", "compute-in-memory",
                         "ai accelerator", "neural processing", "npu", "tpu", "hardware",
                         "circuit", "analog", "mixed-signal", "rf", "serdes", "pll",
                         # 芯片设计公司
                         "intel", "amd", "nvidia", "qualcomm", "broadcom", "marvell", "mediatek",
                         "apple silicon", "amazon graviton", "google tpu", "microsoft maia",
                         "samsung lsi", "arm ", "ibm research",
                         # 顶尖学术实验室
                         "eth zurich", "mit ", "massachusetts institute", "stanford", "uc berkeley",
                         "cmu ", "carnegie mellon", "uiuc", "university of illinois",
                         "ut austin", "university of washington", "princeton", "caltech",
                         "georgia tech", "university of toronto", "epfl", "cambridge",
                         "imperial college", "tsinghua", "peking university", "chinese academy of sciences",
                         # 通信/基站公司
                         "ericsson", "zte", "nokia", "bell labs", "huawei", "cisco",
                         "base station", "ran", "radio access", "enodeb", "gnodeb",
                         "基站", "射频", "通信", "5g", "6g", "wireless", "mmwave", "beamforming",
                         "massive mimo", "ofdm", "cfr", "dpd"]
        
        relevance = 0
        matched_keywords = []
        for kw in chip_keywords:
            if kw in text:
                relevance += 1.5
                matched_keywords.append(kw)
        
        relevance = min(relevance, 10)
        if relevance < self.threshold:
            return None
        
        # 简单分类 + 机构/场景细分
        category = "Other"
        if any(k in text for k in ["eda", "synthesis", "verification", "layout", "place", "route"]):
            category = "EDA"
        elif any(k in text for k in ["chiplet", "3d ic", "tsv", "interposer", "packaging", "advanced packaging"]):
            category = "Packaging"
        elif any(k in text for k in ["process", "lithography", "transistor", "cmos", "finfet", "gaa", "node", "nm "]):
            category = "Process"
        elif any(k in text for k in ["memory", "dram", "sram", "cache", "hbm", "storage"]):
            category = "Memory"
        elif any(k in text for k in ["ai accelerator", "neural", "npu", "tpu", "deep learning", "machine learning", "inference", "training"]):
            category = "AI Chip"
        elif any(k in text for k in ["architecture", "microarchitecture", "superscalar", "out-of-order", "pipeline", "branch prediction"]):
            category = "Architecture"
        elif any(k in text for k in ["interconnect", "network-on-chip", "noc", "bus", "mesh", "topology"]):
            category = "Interconnect"
        elif any(k in text for k in ["photonics", "optical", "silicon photonics", "optical interconnect"]):
            category = "Photonics"
        elif any(k in text for k in ["base station", "ran", "enodeb", "gnodeb", "基站", "射频", "beamforming", "mmwave", "5g", "6g"]):
            category = "Base Station / RAN"
        
        # TRL 简单估计
        trl = 3
        if "experimental" in text or "prototype" in text or "demonstration" in text:
            trl = 4
        if "fabricated" in text or "test chip" in text or "tape-out" in text or "silicon" in text:
            trl = 6
        if "production" in text or "commercial" in text or "product" in text:
            trl = 8
        
        # 机构加权：若来自目标机构，提升价值分
        tier1_orgs = ["intel", "amd", "nvidia", "eth zurich", "mit ", "stanford", "uc berkeley", "arm "]
        tier2_orgs = ["qualcomm", "broadcom", "samsung", "tsinghua", "peking university", "cmu ", "carnegie mellon", "google tpu"]
        org_bonus = 0
        matched_orgs = []
        for org in tier1_orgs:
            if org in text:
                org_bonus += 1.5
                matched_orgs.append(org.strip())
        for org in tier2_orgs:
            if org in text:
                org_bonus += 1.0
                matched_orgs.append(org.strip())
        
        # 价值分 = 基础相关性 + TRL加成 + 机构加成
        value_score = min(relevance + (1 if trl >= 6 else 0) + org_bonus, 10)
        
        decision = "Flash Brief"
        if value_score >= 8 or (trl in [4, 5, 6] and org_bonus > 0):
            decision = "Deep Dive"
        
        result = {
            "relevance": round(relevance, 1),
            "category": category,
            "summary": f"涉及 {', '.join(matched_keywords[:3])} 的芯片技术研究" if matched_keywords else "芯片相关技术研究",
            "trl": trl,
            "value_score": round(value_score, 1),
            "decision": decision,
            "key_players": matched_orgs[:3] if matched_orgs else [],
            "keywords": list(set(matched_keywords))[:5] if matched_keywords else ["chip"],
        }
        
        return {
            **doc,
            "assessment": result,
            "screened_at": datetime.now().isoformat(),
        }
