"""
摘要 Agent：生成结构化技术摘要
"""
import json
import re
from typing import Dict
from openai import OpenAI
from src.utils.config import config

class SummarizerAgent:
    SYSTEM_PROMPT = """你是芯片技术领域的资深技术编辑。
请将以下论文/技术文章转化为结构化的技术情报卡片。

要求：
1. 提取核心创新点（最多4条，每条不超过30字）
2. 提取关键技术指标（如性能提升%、功耗降低%、面积缩减%，若有）
3. 判断技术局限性或待解决问题（最多2条）
4. 提炼对芯片设计实践的直接启示（最多2条）

输出 JSON 格式：
{
  "innovations": ["...", "..."],
  "metrics": {"performance": "", "power": "", "area": ""},
  "limitations": ["..."],
  "implications": ["..."],
  "technical_depth": "Brief|Moderate|Deep"
}"""

    def __init__(self):
        cfg = config.llm
        self.model = cfg.get("model", "gpt-4o-mini")
        self.temperature = cfg.get("temperature", 0.3)
        self.max_tokens = cfg.get("max_tokens", 2000)
        
        api_key = config.openai_api_key
        if api_key and api_key.startswith("sk-"):
            self.client = OpenAI(api_key=api_key, base_url=config.openai_base_url)
            self.use_mock = False
        else:
            self.client = None
            self.use_mock = True
            print("[Summarizer] OPENAI_API_KEY not set, using MOCK mode for demo.")
    
    def summarize(self, doc: Dict) -> Dict:
        if self.use_mock:
            return self._mock_summarize(doc)
        
        text = f"标题：{doc.get('title', '')}\n\n摘要：{doc.get('abstract', '')[:3000]}"
        
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
            
            summary = json.loads(content.strip())
            doc["structured_summary"] = summary
            return doc
            
        except Exception as e:
            print(f"[Summarizer Error] {doc.get('title', '')[:40]}: {e}")
            doc["structured_summary"] = {
                "innovations": [],
                "metrics": {},
                "limitations": [],
                "implications": [],
                "technical_depth": "Brief"
            }
            return doc
    
    def _mock_summarize(self, doc: Dict) -> Dict:
        """Mock 摘要：提取前几句作为创新点"""
        abstract = doc.get("abstract", "")
        sentences = [s.strip() for s in abstract.split(".") if len(s.strip()) > 20]
        
        innovations = sentences[:3] if sentences else ["暂无详细摘要"]
        
        # 简单指标提取
        metrics = {}
        import re
        perf_match = re.search(r'(\d+\.?\d*)\s*%\s*(?:improvement|better|faster|speedup|gain)', abstract, re.I)
        if perf_match:
            metrics["performance"] = f"{perf_match.group(1)}% improvement"
        power_match = re.search(r'(\d+\.?\d*)\s*%\s*(?:power reduction|lower power|energy reduction)', abstract, re.I)
        if power_match:
            metrics["power"] = f"{power_match.group(1)}% reduction"
        area_match = re.search(r'(\d+\.?\d*)\s*%\s*(?:area reduction|smaller area|area saving)', abstract, re.I)
        if area_match:
            metrics["area"] = f"{area_match.group(1)}% reduction"
        
        doc["structured_summary"] = {
            "innovations": innovations,
            "metrics": metrics,
            "limitations": ["需进一步验证实际量产可行性"],
            "implications": ["建议关注该技术在目标产品中的适用性"],
            "technical_depth": "Moderate",
        }
        return doc
