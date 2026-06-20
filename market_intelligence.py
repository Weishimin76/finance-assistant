# -*- coding: utf-8 -*-
"""
竞品市场情报 - 竞品价格监控、政策变化评估、市场趋势分析
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random


class MarketIntelligence:
    """市场情报引擎"""

    def __init__(self, df: pd.DataFrame = None):
        self.df = df.copy() if df is not None else None
        self.competitor_data = self._load_competitor_data()
        self.policy_changes = self._load_policy_changes()

    def _load_competitor_data(self) -> Dict:
        """加载竞品数据（模拟）"""
        return {
            "Amazon": {
                "主要竞品": [
                    {"name": "竞品A", "price": 29.99, "rating": 4.5, "reviews": 1200},
                    {"name": "竞品B", "price": 34.99, "rating": 4.2, "reviews": 800},
                    {"name": "竞品C", "price": 24.99, "rating": 4.7, "reviews": 2000},
                ],
                "市场均价": 29.99,
                "价格区间": "24.99-34.99"
            },
            "TikTok Shop": {
                "主要竞品": [
                    {"name": "竞品D", "price": 19.99, "rating": 4.3, "reviews": 500},
                    {"name": "竞品E", "price": 22.99, "rating": 4.1, "reviews": 300},
                ],
                "市场均价": 21.49,
                "价格区间": "19.99-22.99"
            },
            "Shopee": {
                "主要竞品": [
                    {"name": "竞品F", "price": 15.99, "rating": 4.4, "reviews": 1500},
                    {"name": "竞品G", "price": 18.99, "rating": 4.0, "reviews": 600},
                ],
                "市场均价": 17.49,
                "价格区间": "15.99-18.99"
            }
        }

    def _load_policy_changes(self) -> List[Dict]:
        """加载平台政策变化（模拟）"""
        return [
            {
                "平台": "Amazon",
                "政策": "FBA费用上调",
                "生效日期": "2026-07-01",
                "影响": "物流成本增加约8%",
                "建议": "考虑使用第三方物流或调整定价"
            },
            {
                "平台": "TikTok Shop",
                "政策": "新卖家佣金减免",
                "生效日期": "2026-06-15",
                "影响": "前3个月佣金降至5%",
                "建议": "适合新入驻卖家，可降低初期成本"
            },
            {
                "平台": "Shopee",
                "政策": "免运活动门槛提高",
                "生效日期": "2026-08-01",
                "影响": "免运门槛从29提升至35",
                "建议": "考虑设置满减活动替代免运"
            }
        ]

    def competitor_price_analysis(self, platform: str = None, your_price: float = None) -> Dict:
        """竞品价格分析"""
        if platform and platform in self.competitor_data:
            data = self.competitor_data[platform]
        else:
            # 汇总所有平台
            data = {
                "主要竞品": [],
                "市场均价": 0,
                "价格区间": ""
            }
            all_prices = []
            for p, d in self.competitor_data.items():
                data["主要竞品"].extend(d["主要竞品"])
                all_prices.extend([c["price"] for c in d["主要竞品"]])

            if all_prices:
                data["市场均价"] = np.mean(all_prices)
                data["价格区间"] = f"{min(all_prices):.2f}-{max(all_prices):.2f}"

        competitors = data["主要竞品"]
        market_avg = data["市场均价"]

        # 排序：按价格从低到高
        competitors_sorted = sorted(competitors, key=lambda x: x["price"])

        analysis = {
            "平台": platform or "全平台",
            "市场均价": f"{market_avg:.2f}",
            "价格区间": data["价格区间"],
            "竞品数量": len(competitors),
            "竞品详情": competitors_sorted,
            "价格排名": None,
            "竞争力": None
        }

        # 如果你的价格已知，分析竞争力
        if your_price:
            if your_price < market_avg * 0.9:
                analysis["竞争力"] = "价格优势明显"
                analysis["建议"] = "价格有竞争力，可考虑适当提价提升利润"
            elif your_price > market_avg * 1.1:
                analysis["竞争力"] = "价格偏高"
                analysis["建议"] = "价格高于市场均价，需突出差异化价值"
            else:
                analysis["竞争力"] = "价格适中"
                analysis["建议"] = "价格合理，关注服务和品质提升"

            # 计算排名
            all_prices = [c["price"] for c in competitors] + [your_price]
            all_prices.sort()
            rank = all_prices.index(your_price) + 1
            analysis["价格排名"] = f"第{rank}名（共{len(all_prices)}个）"

        return analysis

    def pricing_recommendation(self, cost: float, target_margin: float = 30) -> Dict:
        """定价建议"""
        # 基于竞品数据给出建议
        all_competitors = []
        for p, d in self.competitor_data.items():
            all_competitors.extend(d["主要竞品"])

        if not all_competitors:
            return {"错误": "无竞品数据"}

        prices = [c["price"] for c in all_competitors]
        min_price = min(prices)
        max_price = max(prices)
        avg_price = np.mean(prices)

        # 计算建议售价
        min_profit_price = cost / (1 - target_margin / 100)

        recommendations = []

        # 渗透定价
        if min_profit_price <= min_price * 1.05:
            recommendations.append({
                "策略": "渗透定价",
                "建议售价": f"{min_price * 0.98:.2f}",
                "利润率": f"{(1 - cost / (min_price * 0.98)) * 100:.1f}%",
                "适用场景": "新品推广、抢占市场份额",
                "风险": "利润较低，需控制成本"
            })

        # 竞争定价
        competitive_price = avg_price * 0.95
        if competitive_price > min_profit_price:
            recommendations.append({
                "策略": "竞争定价",
                "建议售价": f"{competitive_price:.2f}",
                "利润率": f"{(1 - cost / competitive_price) * 100:.1f}%",
                "适用场景": "稳定期产品、保持竞争力",
                "风险": "中等利润，需持续优化"
            })

        # 溢价定价
        premium_price = avg_price * 1.1
        if premium_price > cost * 1.5:
            recommendations.append({
                "策略": "溢价定价",
                "建议售价": f"{premium_price:.2f}",
                "利润率": f"{(1 - cost / premium_price) * 100:.1f}%",
                "适用场景": "品牌产品、差异化明显",
                "风险": "销量可能受限，需强营销支持"
            })

        return {
            "成本": f"{cost:.2f}",
            "目标利润率": f"{target_margin}%",
            "市场最低": f"{min_price:.2f}",
            "市场最高": f"{max_price:.2f}",
            "市场平均": f"{avg_price:.2f}",
            "定价方案": recommendations,
            "综合建议": f"建议采用'{recommendations[0]['策略']}'，售价{recommendations[0]['建议售价']}，可获得{recommendations[0]['利润率']}利润率" if recommendations else "无法给出建议"
        }

    def policy_impact_assessment(self) -> Dict:
        """政策影响评估"""
        assessments = []

        for policy in self.policy_changes:
            # 计算财务影响
            impact_value = 0
            if "费用" in policy["影响"] or "成本" in policy["影响"]:
                # 提取百分比
                import re
                match = re.search(r'(\d+)%', policy["影响"])
                if match:
                    pct = int(match.group(1))
                    # 假设月销售额10000
                    impact_value = 10000 * pct / 100

            assessments.append({
                "平台": policy["平台"],
                "政策": policy["政策"],
                "生效日期": policy["生效日期"],
                "影响描述": policy["影响"],
                "预估月影响": f"{impact_value:.2f}",
                "影响方向": "负面" if impact_value > 0 else "正面",
                "建议": policy["建议"],
                "紧急程度": "高" if datetime.strptime(policy["生效日期"], "%Y-%m-%d") < datetime.now() + timedelta(days=30) else "中"
            })

        # 按紧急程度排序
        assessments.sort(key=lambda x: {"高": 0, "中": 1, "低": 2}.get(x["紧急程度"], 3))

        total_negative = sum([float(a["预估月影响"]) for a in assessments if a["影响方向"] == "负面"])
        total_positive = sum([float(a["预估月影响"]) for a in assessments if a["影响方向"] == "正面"])

        return {
            "政策数量": len(assessments),
            "紧急政策": sum(1 for a in assessments if a["紧急程度"] == "高"),
            "总负面影响": f"{total_negative:.2f}",
            "总正面影响": f"{total_positive:.2f}",
            "净影响": f"{total_positive - total_negative:+.2f}",
            "政策列表": assessments,
            "应对建议": [
                "关注即将生效的政策，提前调整运营策略",
                "评估政策影响，必要时调整定价或成本结构",
                "利用正面政策（如佣金减免）加速拓展"
            ]
        }

    def market_trend_analysis(self) -> Dict:
        """市场趋势分析"""
        # 模拟市场趋势数据
        trends = {
            "热门品类": [
                {"品类": "智能家居", "增长率": 35, "竞争度": "高"},
                {"品类": "户外用品", "增长率": 28, "竞争度": "中"},
                {"品类": "宠物用品", "增长率": 22, "竞争度": "低"},
                {"品类": "健康保健", "增长率": 18, "竞争度": "中"},
            ],
            " declining品类": [
                {"品类": "传统数码", "下降率": 15, "原因": "市场饱和"},
                {"品类": "快时尚", "下降率": 10, "原因": "环保意识提升"},
            ],
            "新兴机会": [
                {"机会": "AI智能产品", "潜力": "极高", "窗口期": "6-12个月"},
                {"机会": "可持续产品", "潜力": "高", "窗口期": "12-18个月"},
                {"机会": "个性化定制", "潜力": "中高", "窗口期": "6-12个月"},
            ]
        }

        return {
            "热门品类": trends["热门品类"],
            "衰退品类": trends["declining品类"],
            "新兴机会": trends["新兴机会"],
            "建议": [
                "考虑进入高增长低竞争品类，如宠物用品",
                "关注AI智能产品窗口期，提前布局",
                "传统品类需差异化定位，避免价格战"
            ]
        }

    def generate_competitive_report(self) -> Dict:
        """生成竞争情报报告"""
        return {
            "报告日期": datetime.now().strftime("%Y-%m-%d"),
            "竞品价格分析": self.competitor_price_analysis(),
            "政策影响评估": self.policy_impact_assessment(),
            "市场趋势": self.market_trend_analysis(),
            "行动建议": [
                "每周监控竞品价格变化，保持价格竞争力",
                "关注平台政策变化，提前调整运营策略",
                "把握新兴品类机会，提前布局高增长市场"
            ]
        }
