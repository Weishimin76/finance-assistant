# -*- coding: utf-8 -*-
"""
跨境电商财务智能体 - 税务政策监控模块
各国跨境电商政策变化追踪 + 翻译 + 影响分析
"""
import pandas as pd
import requests
from datetime import datetime
from typing import Dict, List, Optional
from config import config


# 主要监控国家和来源
MONITORED_COUNTRIES = {
    "欧盟": {
        "languages": ["en"],
        "keywords": ["VAT", "customs", "import", "e-commerce", "cross-border", "digital services tax"],
        "sources": [
            {"name": "European Commission - Taxation", "url": "https://ec.europa.eu/taxation_customs/"},
            {"name": "ECB", "url": "https://www.ecb.europa.eu/"},
        ],
    },
    "英国": {
        "languages": ["en"],
        "keywords": ["VAT", "customs", "import duty", "e-commerce", "HMRC"],
        "sources": [
            {"name": "Gov.uk - VAT", "url": "https://www.gov.uk/topic/business-tax/vat"},
        ],
    },
    "美国": {
        "languages": ["en"],
        "keywords": ["sales tax", "marketplace facilitator", "import duty", "FTZ", "de minimis"],
        "sources": [
            {"name": "IRS", "url": "https://www.irs.gov/"},
        ],
    },
    "日本": {
        "languages": ["en"],
        "keywords": ["consumption tax", "customs", "import", "JCT", "e-commerce"],
        "sources": [
            {"name": "Japan Customs", "url": "https://www.customs.go.jp/"},
        ],
    },
    "澳大利亚": {
        "languages": ["en"],
        "keywords": ["GST", "import", "e-commerce", "customs"],
        "sources": [
            {"name": "ATO", "url": "https://www.ato.gov.au/"},
        ],
    },
}

# 已知的重要政策变化（手动维护，定期更新）
KNOWN_POLICY_CHANGES = [
    {
        "日期": "2025-07-01",
        "国家/地区": "欧盟",
        "政策标题": "EU VAT in the Digital Age (ViDA) 第二阶段实施",
        "变化内容": "电商平台将全面承担VAT申报和缴纳义务，取消进口小额免税门槛",
        "影响分析": "所有在欧盟销售的跨境卖家需通过平台自动申报VAT，成本结构将发生变化",
        "建议操作": "关注平台通知，确认VAT注册号有效性，调整定价策略",
        "来源": "European Commission",
        "严重程度": "🔴 高",
    },
    {
        "日期": "2025-01-01",
        "国家/地区": "美国",
        "政策标题": "多州市场促进者法案更新",
        "变化内容": "更多州要求电商平台代收销售税，门槛进一步降低",
        "影响分析": "在美销售可能需要缴纳更多州的销售税",
        "建议操作": "检查各州销售税注册义务，更新税务合规流程",
        "来源": "State Tax Boards",
        "严重程度": "🟡 中",
    },
    {
        "日期": "2025-04-01",
        "国家/地区": "英国",
        "政策标题": "UK VAT Registration 门槛调整",
        "变化内容": "远程销售VAT注册门槛从£70,000降至£0",
        "影响分析": "所有向英国消费者销售的非英国卖家必须注册UK VAT",
        "建议操作": "确认是否需要注册UK VAT，联系税代处理",
        "来源": "HMRC",
        "严重程度": "🔴 高",
    },
    {
        "日期": "2025-10-01",
        "国家/地区": "日本",
        "政策标题": "JCT 合规发票制度更新",
        "变化内容": "跨境电商平台需在发票上显示JCT注册号",
        "影响分析": "未注册JCT的卖家可能影响消费者退税",
        "建议操作": "申请JCT注册号，更新平台发票信息",
        "来源": "Japan Tax Agency",
        "严重程度": "🟡 中",
    },
]


class TaxPolicyMonitor:
    """税务政策监控器"""

    def __init__(self):
        self.countries = MONITORED_COUNTRIES
        self.known_changes = KNOWN_POLICY_CHANGES

    def get_policy_changes(self) -> pd.DataFrame:
        """
        获取已知政策变化列表

        Returns:
            政策变化 DataFrame
        """
        if not self.known_changes:
            return pd.DataFrame()

        df = pd.DataFrame(self.known_changes)
        df["日期"] = pd.to_datetime(df["日期"])
        df = df.sort_values("日期", ascending=False).reset_index(drop=True)
        return df

    def get_upcoming_policies(self, days_ahead: int = 90) -> pd.DataFrame:
        """
        获取即将生效的政策

        Args:
            days_ahead: 未来多少天内

        Returns:
            即将生效的政策
        """
        df = self.get_policy_changes()
        if df.empty:
            return df

        today = datetime.now()
        future = today + pd.Timedelta(days=days_ahead)
        upcoming = df[(df["日期"] >= today) & (df["日期"] <= future)]
        return upcoming.reset_index(drop=True)

    def search_policy(self, keyword: str) -> pd.DataFrame:
        """
        搜索相关政策

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的政策列表
        """
        df = self.get_policy_changes()
        if df.empty:
            return df

        mask = (
            df["国家/地区"].str.contains(keyword, case=False, na=False) |
            df["政策标题"].str.contains(keyword, case=False, na=False) |
            df["变化内容"].str.contains(keyword, case=False, na=False) |
            df["影响分析"].str.contains(keyword, case=False, na=False)
        )
        return df[mask].reset_index(drop=True)

    def get_country_summary(self, country: str) -> pd.DataFrame:
        """
        获取某国政策摘要

        Args:
            country: 国家名称

        Returns:
            该国的政策变化
        """
        df = self.get_policy_changes()
        if df.empty:
            return df
        return df[df["国家/地区"] == country].reset_index(drop=True)

    def generate_impact_report(self, df: pd.DataFrame) -> str:
        """
        生成政策影响分析报告（文本格式）

        Args:
            df: 政策变化数据

        Returns:
            分析报告文本
        """
        if df.empty:
            return "暂无相关政策变化信息"

        lines = []
        lines.append(f"📋 跨境电商税务政策监控报告")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"共 {len(df)} 条政策变化")
        lines.append("")

        for _, row in df.iterrows():
            lines.append(f"{'='*50}")
            lines.append(f"📌 {row['政策标题']}")
            lines.append(f"   国家/地区: {row['国家/地区']}")
            lines.append(f"   生效日期: {row['日期'].strftime('%Y-%m-%d') if hasattr(row['日期'], 'strftime') else row['日期']}")
            lines.append(f"   严重程度: {row['严重程度']}")
            lines.append(f"")
            lines.append(f"   【变了什么】")
            lines.append(f"   {row['变化内容']}")
            lines.append(f"")
            lines.append(f"   【影响是什么】")
            lines.append(f"   {row['影响分析']}")
            lines.append(f"")
            lines.append(f"   【你要做什么】")
            lines.append(f"   {row['建议操作']}")
            lines.append(f"")
            lines.append(f"   来源: {row['来源']}")
            lines.append("")

        return "\n".join(lines)


# 全局实例
tax_policy_monitor = TaxPolicyMonitor()
