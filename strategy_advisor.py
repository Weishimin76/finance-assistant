# -*- coding: utf-8 -*-
"""
AI策略顾问 - 利润提升方案、平台选择模拟、定价策略
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from config import PLATFORM_CONFIG


class StrategyAdvisor:
    """AI策略顾问引擎"""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self._preprocess()

    def _preprocess(self):
        """数据预处理"""
        numeric_cols = ['订单金额', '佣金', '手续费', '运费', '实际到账', '数量', '成本']
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)

    def profit_boost_strategies(self, target_increase: float = 20.0) -> Dict:
        """生成利润提升策略"""
        strategies = []
        current_profit = self.df['实际到账'].sum()
        target_profit = current_profit * (1 + target_increase / 100)
        gap = target_profit - current_profit

        # 策略1：提高定价
        if '订单金额' in self.df.columns and len(self.df) > 0:
            avg_order = self.df['订单金额'].mean()
            price_increase_needed = (gap / len(self.df)) / avg_order * 100 if avg_order > 0 else 0

            if price_increase_needed < 30:  # 合理的提价范围
                strategies.append({
                    "策略名称": "优化定价策略",
                    "策略描述": f"将平均订单金额提升{price_increase_needed:.1f}%",
                    "具体操作": [
                        "分析竞品定价，找到提价空间",
                        "对高需求SKU进行5-10%提价测试",
                        "推出捆绑销售套餐提升客单价"
                    ],
                    "预期效果": f"月利润提升{target_increase:.0f}%",
                    "实施难度": "低",
                    "风险等级": "低",
                    "预估收益": f"{gap:.2f}"
                })

        # 策略2：降低费用
        if '佣金' in self.df.columns and '手续费' in self.df.columns:
            total_fees = self.df['佣金'].sum() + self.df['手续费'].sum()
            if total_fees > 0:
                fee_reduction_potential = total_fees * 0.15  # 假设可降低15%
                if fee_reduction_potential > gap * 0.3:
                    strategies.append({
                        "策略名称": "优化费用结构",
                        "策略描述": "通过谈判和优化降低平台费用",
                        "具体操作": [
                            "与平台谈判降低佣金率",
                            "优化物流方案降低运费",
                            "使用平台促销活动减少手续费"
                        ],
                        "预期效果": f"月费用降低15%，利润增加{fee_reduction_potential:.2f}",
                        "实施难度": "中",
                        "风险等级": "低",
                        "预估收益": f"{fee_reduction_potential:.2f}"
                    })

        # 策略3：拓展高利润平台
        if '平台' in self.df.columns:
            platform_profit = self.df.groupby('平台')['实际到账'].sum()
            if len(platform_profit) > 1:
                best_platform = platform_profit.idxmax()
                worst_platform = platform_profit.idxmin()
                profit_gap = platform_profit.max() - platform_profit.min()

                strategies.append({
                    "策略名称": "平台资源再分配",
                    "策略描述": f"将资源从{worst_platform}转向{best_platform}",
                    "具体操作": [
                        f"逐步减少{worst_platform}的广告投入",
                        f"增加{best_platform}的SKU上架数量",
                        "测试新平台的利润空间"
                    ],
                    "预期效果": f"优化后月利润可提升{profit_gap * 0.3:.2f}",
                    "实施难度": "中",
                    "风险等级": "中",
                    "预估收益": f"{profit_gap * 0.3:.2f}"
                })

        # 策略4：SKU优化
        if 'SKU' in self.df.columns:
            sku_stats = self.df.groupby('SKU').agg({
                '实际到账': 'sum',
                '订单金额': 'sum',
                '数量': 'sum'
            }).reset_index()
            sku_stats['利润率'] = sku_stats['实际到账'] / sku_stats['订单金额'].clip(lower=0.01)

            low_profit_skus = sku_stats[sku_stats['利润率'] < 0.1]
            if len(low_profit_skus) > 0:
                potential_gain = low_profit_skus['订单金额'].sum() * 0.05
                strategies.append({
                    "策略名称": "SKU结构优化",
                    "策略描述": f"优化{len(low_profit_skus)}个低利润SKU",
                    "具体操作": [
                        "下架或替换利润率低于10%的SKU",
                        "集中资源推广高利润SKU",
                        "开发新品替代亏损SKU"
                    ],
                    "预期效果": f"SKU利润率提升，月利润增加{potential_gain:.2f}",
                    "实施难度": "中",
                    "风险等级": "中",
                    "预估收益": f"{potential_gain:.2f}"
                })

        # 策略5：提升转化率（如果有流量数据）
        if '访客数' in self.df.columns and '订单金额' in self.df.columns:
            conversion_rate = len(self.df) / self.df['访客数'].sum() * 100
            if conversion_rate < 3:  # 行业平均约2-3%
                potential_orders = self.df['访客数'].sum() * 0.005  # 提升0.5%
                avg_order_value = self.df['订单金额'].mean()
                potential_revenue = potential_orders * avg_order_value
                strategies.append({
                    "策略名称": "提升转化率",
                    "策略描述": f"当前转化率{conversion_rate:.1f}%，目标提升至{conversion_rate+0.5:.1f}%",
                    "具体操作": [
                        "优化产品详情页和主图",
                        "设置限时促销活动",
                        "改善客户评价和问答"
                    ],
                    "预期效果": f"月订单增加{potential_orders:.0f}单，利润增加{potential_revenue*0.15:.2f}",
                    "实施难度": "低",
                    "风险等级": "低",
                    "预估收益": f"{potential_revenue*0.15:.2f}"
                })

        return {
            "当前月利润": f"{current_profit:.2f}",
            "目标月利润": f"{target_profit:.2f}",
            "利润缺口": f"{gap:.2f}",
            "策略列表": strategies,
            "最优策略": strategies[0] if strategies else None
        }

    def platform_comparison_simulation(self, platforms: List[str] = None) -> Dict:
        """平台选择模拟对比"""
        if platforms is None:
            platforms = list(PLATFORM_CONFIG.keys())[:5]

        simulation_results = []

        # 假设测试订单金额
        test_amount = 1000

        for platform in platforms:
            if platform not in PLATFORM_CONFIG:
                continue

            config = PLATFORM_CONFIG[platform]
            commission_rate = config.get("commission", 0.15)
            logistics_rate = config.get("logistics_rate", 0.1)
            payment_rate = config.get("payment_rate", 0.02)
            vat_rate = config.get("vat_rate", 0.2)

            # 计算各项费用
            commission = test_amount * commission_rate
            logistics = test_amount * logistics_rate
            payment = test_amount * payment_rate
            vat = (test_amount - commission) * vat_rate / (1 + vat_rate) if vat_rate > 0 else 0

            total_fees = commission + logistics + payment + vat
            net_profit = test_amount - total_fees
            profit_rate = (net_profit / test_amount) * 100

            simulation_results.append({
                "平台": platform,
                "测试金额": test_amount,
                "佣金": f"{commission:.2f} ({commission_rate*100:.0f}%)",
                "物流费": f"{logistics:.2f} ({logistics_rate*100:.0f}%)",
                "支付费": f"{payment:.2f} ({payment_rate*100:.1f}%)",
                "VAT": f"{vat:.2f}",
                "总费用": f"{total_fees:.2f}",
                "净利润": f"{net_profit:.2f}",
                "利润率": f"{profit_rate:.1f}%",
                "综合评分": self._calculate_platform_score(profit_rate, commission_rate, logistics_rate)
            })

        # 排序：按利润率从高到低
        simulation_results.sort(key=lambda x: float(x["利润率"].replace("%", "")), reverse=True)

        return {
            "模拟结果": simulation_results,
            "推荐平台": simulation_results[0]["平台"] if simulation_results else None,
            "最差平台": simulation_results[-1]["平台"] if simulation_results else None
        }

    def _calculate_platform_score(self, profit_rate: float, commission: float, logistics: float) -> str:
        """计算平台综合评分"""
        score = profit_rate * 0.5 + (1 - commission) * 30 + (1 - logistics) * 20
        if score >= 80:
            return "A级（推荐）"
        elif score >= 60:
            return "B级（可考虑）"
        else:
            return "C级（谨慎）"

    def pricing_strategy(self, sku: str = None) -> Dict:
        """定价策略建议"""
        if sku and 'SKU' in self.df.columns:
            sku_df = self.df[self.df['SKU'] == sku]
            if len(sku_df) == 0:
                return {"错误": f"SKU {sku} 不存在"}
        else:
            sku_df = self.df

        if '订单金额' not in sku_df.columns or '实际到账' not in sku_df.columns:
            return {"错误": "缺少必要的数据列"}

        avg_price = sku_df['订单金额'].mean()
        avg_profit = sku_df['实际到账'].mean()
        profit_margin = (avg_profit / avg_price * 100) if avg_price > 0 else 0

        # 建议定价区间
        suggestions = []

        # 基于利润率的建议
        if profit_margin < 10:
            suggestions.append({
                "类型": "提价建议",
                "当前利润率": f"{profit_margin:.1f}%",
                "建议定价": f"{avg_price * 1.15:.2f}",
                "理由": "利润率过低，建议提价15%测试市场反应",
                "风险": "可能降低转化率，建议小批量测试"
            })
        elif profit_margin > 30:
            suggestions.append({
                "类型": "竞争优势",
                "当前利润率": f"{profit_margin:.1f}%",
                "建议": "利润率健康，可考虑降价5-10%抢占市场份额",
                "理由": "有降价空间，提升竞争力"
            })

        # 基于历史数据的建议
        if '日期' in sku_df.columns and len(sku_df) > 30:
            sku_df = sku_df.sort_values('日期')
            recent_avg = sku_df.tail(10)['订单金额'].mean()
            old_avg = sku_df.head(10)['订单金额'].mean()

            if recent_avg > old_avg * 1.1:
                suggestions.append({
                    "类型": "趋势分析",
                    "发现": "近期定价呈上升趋势",
                    "建议": "市场需求旺盛，可继续提价5%",
                    "数据支持": f"近期均价{recent_avg:.2f} vs 早期均价{old_avg:.2f}"
                })
            elif recent_avg < old_avg * 0.9:
                suggestions.append({
                    "类型": "趋势分析",
                    "发现": "近期定价呈下降趋势",
                    "建议": "市场竞争加剧，建议优化成本或差异化定位",
                    "数据支持": f"近期均价{recent_avg:.2f} vs 早期均价{old_avg:.2f}"
                })

        return {
            "当前均价": f"{avg_price:.2f}",
            "当前利润率": f"{profit_margin:.1f}%",
            "建议列表": suggestions,
            "定价区间": {
                "保守": f"{avg_price * 0.95:.2f}",
                "当前": f"{avg_price:.2f}",
                "激进": f"{avg_price * 1.15:.2f}"
            }
        }

    def scenario_simulation(self, scenario_type: str, params: Dict) -> Dict:
        """场景模拟"""
        if scenario_type == "price_change":
            return self._simulate_price_change(params)
        elif scenario_type == "platform_switch":
            return self._simulate_platform_switch(params)
        elif scenario_type == "cost_reduction":
            return self._simulate_cost_reduction(params)
        else:
            return {"错误": "未知的模拟类型"}

    def _simulate_price_change(self, params: Dict) -> Dict:
        """模拟价格变动影响"""
        price_change = params.get("price_change", 10)  # 默认提价10%
        elasticity = params.get("elasticity", -1.5)  # 价格弹性，默认-1.5

        current_revenue = self.df['订单金额'].sum()
        current_orders = len(self.df)
        current_profit = self.df['实际到账'].sum()

        # 计算新订单量（价格弹性）
        new_orders = int(current_orders * (1 + elasticity * price_change / 100))
        new_orders = max(new_orders, int(current_orders * 0.5))  # 最低保留50%

        # 计算新收入和利润
        avg_price = current_revenue / current_orders if current_orders > 0 else 0
        new_avg_price = avg_price * (1 + price_change / 100)
        new_revenue = new_orders * new_avg_price

        # 假设利润率不变
        profit_margin = current_profit / current_revenue if current_revenue > 0 else 0
        new_profit = new_revenue * profit_margin

        return {
            "模拟场景": f"价格变动{price_change:+.0f}%",
            "当前状态": {
                "订单量": current_orders,
                "收入": f"{current_revenue:.2f}",
                "利润": f"{current_profit:.2f}"
            },
            "模拟结果": {
                "订单量": new_orders,
                "收入": f"{new_revenue:.2f}",
                "利润": f"{new_profit:.2f}"
            },
            "变化": {
                "订单量": f"{(new_orders - current_orders) / current_orders * 100:+.1f}%",
                "收入": f"{(new_revenue - current_revenue) / current_revenue * 100:+.1f}%",
                "利润": f"{(new_profit - current_profit) / current_profit * 100:+.1f}%"
            },
            "建议": "提价有利可图" if new_profit > current_profit else "提价会减少利润，建议维持或降价"
        }

    def _simulate_platform_switch(self, params: Dict) -> Dict:
        """模拟平台切换影响"""
        from_platform = params.get("from_platform", "Amazon")
        to_platform = params.get("to_platform", "TikTok Shop")
        order_amount = params.get("order_amount", 10000)

        if from_platform not in PLATFORM_CONFIG or to_platform not in PLATFORM_CONFIG:
            return {"错误": "平台配置不存在"}

        from_config = PLATFORM_CONFIG[from_platform]
        to_config = PLATFORM_CONFIG[to_platform]

        # 计算原平台利润
        from_fees = order_amount * (from_config.get("commission", 0.15) +
                                     from_config.get("logistics_rate", 0.1) +
                                     from_config.get("payment_rate", 0.02))
        from_profit = order_amount - from_fees

        # 计算新平台利润
        to_fees = order_amount * (to_config.get("commission", 0.15) +
                                   to_config.get("logistics_rate", 0.1) +
                                   to_config.get("payment_rate", 0.02))
        to_profit = order_amount - to_fees

        return {
            "模拟场景": f"从{from_platform}切换到{to_platform}",
            "测试金额": order_amount,
            f"{from_platform}利润": f"{from_profit:.2f}",
            f"{to_platform}利润": f"{to_profit:.2f}",
            "利润差异": f"{to_profit - from_profit:+.2f}",
            "差异比例": f"{(to_profit - from_profit) / from_profit * 100:+.1f}%",
            "建议": f"切换到{to_platform}更有利" if to_profit > from_profit else f"继续留在{from_platform}"
        }

    def _simulate_cost_reduction(self, params: Dict) -> Dict:
        """模拟成本降低影响"""
        cost_reduction = params.get("cost_reduction", 10)  # 成本降低10%

        current_cost = self.df['成本'].sum() if '成本' in self.df.columns else self.df['订单金额'].sum() * 0.6
        current_profit = self.df['实际到账'].sum()

        new_cost = current_cost * (1 - cost_reduction / 100)
        cost_saving = current_cost - new_cost
        new_profit = current_profit + cost_saving

        return {
            "模拟场景": f"成本降低{cost_reduction:.0f}%",
            "当前成本": f"{current_cost:.2f}",
            "新成本": f"{new_cost:.2f}",
            "节省金额": f"{cost_saving:.2f}",
            "当前利润": f"{current_profit:.2f}",
            "新利润": f"{new_profit:.2f}",
            "利润提升": f"{(new_profit - current_profit) / current_profit * 100:+.1f}%",
            "实施建议": [
                "与供应商谈判降低采购成本",
                "优化物流方案减少运费",
                "提高运营效率降低人力成本"
            ]
        }
