"""
主工作流编排：从采集到报告的完整 Pipeline
"""
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from collections import defaultdict

from src.collectors import ArxivCollector, RSSCollector, BlogScraperCollector
from src.agents import ScreenerAgent, SummarizerAgent, InsightGeneratorAgent
from src.storage import VectorStore, MetadataStore
from src.reporting import ReportGenerator
from src.utils.config import config

class InsightPipeline:
    def __init__(self):
        print("[Pipeline] Initializing...")
        self.arxiv_collector = ArxivCollector()
        self.rss_collector = RSSCollector()
        self.blog_collector = BlogScraperCollector()
        self.screener = ScreenerAgent()
        self.summarizer = SummarizerAgent()
        self.insight_generator = InsightGeneratorAgent()
        self.vector_store = VectorStore()
        self.metadata_store = MetadataStore()
        self.report_generator = ReportGenerator()
        
        self.one_pager_threshold = config.reporting.get("one_pager_threshold", 7.5)
        print("[Pipeline] Ready.")
    
    def run(self, dry_run: bool = False):
        """
        执行完整工作流
        dry_run: 如果为 True，不保存到数据库，仅打印结果
        """
        print("\n" + "="*60)
        print(f"[Pipeline] Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # Stage 1: 采集
        print("\n[Stage 1] Collecting sources...")
        raw_docs = self._collect()
        print(f"[Stage 1] Total raw documents: {len(raw_docs)}")
        
        if not raw_docs:
            print("[Pipeline] No new documents found. Exiting.")
            return
        
        # Stage 2: 初筛
        print("\n[Stage 2] Screening documents...")
        screened = self.screener.batch_screen(raw_docs)
        print(f"[Stage 2] Passed screening: {len(screened)} / {len(raw_docs)}")
        
        if not screened:
            print("[Pipeline] No documents passed screening. Exiting.")
            return
        
        # Stage 3: 摘要与向量化
        print("\n[Stage 3] Summarizing and indexing...")
        processed = []
        for doc in screened:
            summarized = self.summarizer.summarize(doc)
            
            if not dry_run:
                is_new = self.vector_store.add(summarized)
                if is_new:
                    self.metadata_store.save(summarized)
                    processed.append(summarized)
            else:
                processed.append(summarized)
        
        print(f"[Stage 3] New unique documents: {len(processed)}")
        
        if not processed:
            print("[Pipeline] No new unique documents. Exiting.")
            return
        
        # Stage 4: 按技术方向聚类
        print("\n[Stage 4] Clustering by technology direction...")
        clusters = self._cluster(processed)
        print(f"[Stage 4] Formed {len(clusters)} clusters")
        
        # Stage 4b: 机构维度聚类
        print("\n[Stage 4b] Clustering by organization...")
        org_clusters = self._cluster_by_org(processed)
        print(f"[Stage 4b] Formed {len(org_clusters)} organization clusters")
        
        # Stage 5: 生成技术方向报告
        print("\n[Stage 5] Generating technology reports...")
        reports = []
        for cluster_name, docs in clusters.items():
            avg_score = sum(d.get("assessment", {}).get("value_score", 0) for d in docs) / len(docs)
            
            if avg_score >= self.one_pager_threshold and len(docs) >= 2:
                print(f"  [Deep Dive] {cluster_name} ({len(docs)} docs, avg_score={avg_score:.1f})")
                content = self.insight_generator.generate_deep_dive(docs)
                if not dry_run:
                    path = self.report_generator.generate_deep_dive(content, docs)
                    reports.append({"type": "deep_dive", "topic": cluster_name, "path": path})
            else:
                print(f"  [Flash Brief] {cluster_name} ({len(docs)} docs, avg_score={avg_score:.1f})")
                content = self.insight_generator.generate_flash(docs)
                if not dry_run:
                    path = self.report_generator.generate_flash_brief(content, docs)
                    reports.append({"type": "flash_brief", "topic": cluster_name, "path": path})
        
        # Stage 5b: 生成机构动态报告
        print("\n[Stage 5b] Generating organization briefs...")
        for org_name, docs in org_clusters.items():
            print(f"  [Org Brief] {org_name} ({len(docs)} docs)")
            if not dry_run:
                path = self.report_generator.generate_org_brief(org_name, docs)
                reports.append({"type": "org_brief", "topic": org_name, "path": path})
        
        # Stage 6: 汇总
        print("\n" + "="*60)
        print("[Pipeline] Summary")
        print("="*60)
        print(f"Raw documents collected: {len(raw_docs)}")
        print(f"Passed screening: {len(screened)}")
        print(f"New unique documents: {len(processed)}")
        print(f"Reports generated: {len(reports)}")
        for r in reports:
            print(f"  - [{r['type']}] {r['topic']}")
            print(f"    -> {r['path']}")
        
        return reports
    
    def _collect(self) -> List[Dict]:
        """采集所有数据源"""
        docs = []
        try:
            arxiv_docs = self.arxiv_collector.fetch()
            print(f"  arXiv: {len(arxiv_docs)} papers")
            docs.extend(arxiv_docs)
        except Exception as e:
            print(f"[Collector Error] arXiv: {e}")
        
        try:
            rss_docs = self.rss_collector.fetch()
            print(f"  RSS: {len(rss_docs)} articles")
            docs.extend(rss_docs)
        except Exception as e:
            print(f"[Collector Error] RSS: {e}")
        
        try:
            blog_docs = self.blog_collector.fetch()
            print(f"  Blogs: {len(blog_docs)} articles")
            docs.extend(blog_docs)
        except Exception as e:
            print(f"[Collector Error] Blogs: {e}")
        
        return docs
    
    def _cluster(self, docs: List[Dict]) -> Dict[str, List[Dict]]:
        """
        按技术分类聚类
        同一技术方向（category）的文档聚合在一起，避免过于分散
        """
        clusters = defaultdict(list)
        for doc in docs:
            assessment = doc.get("assessment", {})
            category = assessment.get("category", "Other")
            clusters[category].append(doc)
        
        return dict(clusters)
    
    def _cluster_by_org(self, docs: List[Dict]) -> Dict[str, List[Dict]]:
        """
        按机构维度聚类
        一篇文献可能涉及多个机构，会被归入多个机构簇
        """
        # 机构名称标准化映射
        NAME_MAP = {
            "Amd": "AMD",
            "Mit": "MIT",
            "Arm": "ARM",
            "Nvidia": "NVIDIA",
            "Cmu": "CMU",
            "Uc Berkeley": "UC Berkeley",
            "Eth Zurich": "ETH Zurich",
            "Google Tpu": "Google TPU",
            "Apple Silicon": "Apple Silicon",
            "Amazon Graviton": "Amazon Graviton",
            "Microsoft Maia": "Microsoft Maia",
        }
        
        clusters = defaultdict(list)
        for doc in docs:
            assessment = doc.get("assessment", {})
            orgs = assessment.get("key_players", [])
            for org in orgs:
                org_clean = org.strip().title()
                org_clean = NAME_MAP.get(org_clean, org_clean)
                if org_clean and len(org_clean) > 1:
                    clusters[org_clean].append(doc)
        
        # 只保留有 >=1 篇文献的机构
        return {k: v for k, v in clusters.items() if len(v) >= 1}
