# -*- coding: utf-8 -*-
"""
智能诊断中心 - 自动发现财务异常、利润黑洞、现金流风险
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional


class SmartDiagnosis:
    """智能诊断引擎"""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.diagnosis_results = {}
        self._preprocess_data()

    def _preprocess_data(self):
        """数据预处理"""
        # 确保数值列正确
        numeric_cols = ['订单金额', '佣金', '手续费', '运费', '实际到账', '退款金额', '数量']
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)

        # 日期处理
        if '日期' in self.df.columns:
            self.df['日期'] = pd.to_datetime(self.df['日期'], errors='coerce')

    def run_full_diagnosis(self) -> Dict:
        """运行完整诊断"""
        return {
            "异常订单检测": self.detect_anomaly_orders(),
            "利润黑洞分析": self.analyze_profit_blackholes(),
            "现金流风险": self.analyze_cashflow_risk(),
            "平台健康度": self.analyze_platform_health(),
            "SKU表现分析": self.analyze_sku_performance(),
            "综合评分": self.calculate_overall_score(),
            "行动建议": self.generate_action_items(),
        }

    def detect_anomaly_orders(self) -> Dict:
        """检测异常订单"""
        anomalies = []

        # 1. 高退款率订单
        if '退款金额' in self.df.columns and '订单金额' in self.df.columns:
            refund_mask = self.df['退款金额'] > 0
            high_refund = self.df[refund_mask & (self.df['退款金额'] / self.df['订单金额'].clip(lower=0.01) > 0.5)]
            if len(high_refund) > 0:
                anomalies.append({
                    "类型": "高退款订单",
                    "数量": len(high_refund),
                    "涉及金额": f"{high_refund['订单金额'].sum():.2f}",
                    "详情": f"{len(high_refund)}笔订单退款超过50%",
                    "风险等级": "高" if len(high_refund) > 10 else "中"
                })

        # 2. 佣金异常（佣金率过高）
        if '佣金' in self.df.columns and '订单金额' in self.df.columns:
            self.df['佣金率'] = self.df['佣金'] / self.df['订单金额'].clip(lower=0.01)
            high_commission = self.df[self.df['佣金率'] > 0.3]
            if len(high_commission) > 0:
                anomalies.append({
                    "类型": "佣金异常",
                    "数量": len(high_commission),
                    "涉及金额": f"{high_commission['佣金'].sum():.2f}",
                    "详情": f"{len(high_commission)}笔订单佣金率超过30%",
                    "风险等级": "高"
                })

        # 3. 零利润/负利润订单
        if '实际到账' in self.df.columns and '订单金额' in self.df.columns:
            negative_profit = self.df[self.df['实际到账'] <= 0]
            if len(negative_profit) > 0:
                anomalies.append({
                    "类型": "亏损订单",
                    "数量": len(negative_profit),
                    "涉及金额": f"{negative_profit['订单金额'].sum():.2f}",
                    "详情": f"{len(negative_profit)}笔订单实际到账≤0",
                    "风险等级": "高"
                })

        # 4. 重复订单号
        if '订单号' in self.df.columns:
            duplicates = self.df[self.df.duplicated(subset=['订单号'], keep=False)]
            if len(duplicates) > 0:
                anomalies.append({
                    "类型": "重复订单",
                    "数量": len(duplicates),
                    "涉及金额": f"{duplicates['订单金额'].sum():.2f}",
                    "详情": f"发现{len(duplicates)}条重复订单记录",
                    "风险等级": "中"
                })

        return {
            "异常总数": len(anomalies),
            "异常列表": anomalies,
            "健康度": max(0, 100 - len(anomalies) * 15)
        }

    def analyze_profit_blackholes(self) -> Dict:
        """分析利润黑洞"""
        blackholes = []

        # 按平台分析利润率
        if '平台' in self.df.columns and '实际到账' in self.df.columns and '订单金额' in self.df.columns:
            platform_stats = self.df.groupby('平台').agg({
                '订单金额': 'sum',
                '实际到账': 'sum',
                '佣金': 'sum',
                '手续费': 'sum',
                '运费': 'sum'
            }).reset_index()

            platform_stats['利润率'] = (platform_stats['实际到账'] / platform_stats['订单金额'].clip(lower=0.01)) * 100
            platform_stats = platform_stats.sort_values('利润率')

            # 利润率最低的平台
            worst_platform = platform_stats.iloc[0]
            if worst_platform['利润率'] < 10:
                blackholes.append({
                    "类型": "低利润平台",
                    "平台": worst_platform['平台'],
                    "利润率": f"{worst_platform['利润率']:.1f}%",
                    "损失估算": f"{(worst_platform['订单金额'] * 0.15 - worst_platform['实际到账']):.2f}",
                    "建议": f"考虑减少{worst_platform['平台']}投入或提高定价"
                })

        # 按SKU分析亏损
        if 'SKU' in self.df.columns:
            sku_stats = self.df.groupby('SKU').agg({
                '订单金额': 'sum',
                '实际到账': 'sum',
                '数量': 'sum'
            }).reset_index()
            sku_stats['利润率'] = (sku_stats['实际到账'] / sku_stats['订单金额'].clip(lower=0.01)) * 100

            losing_skus = sku_stats[sku_stats['利润率'] < 5].head(5)
            if len(losing_skus) > 0:
                for _, sku in losing_skus.iterrows():
                    blackholes.append({
                        "类型": "亏损SKU",
                        "SKU": sku['SKU'],
                        "利润率": f"{sku['利润率']:.1f}%",
                        "销量": int(sku['数量']),
                        "建议": "检查成本结构或考虑下架"
                    })

        # 费用占比分析
        if '佣金' in self.df.columns and '手续费' in self.df.columns and '运费' in self.df.columns:
            total_revenue = self.df['订单金额'].sum()
            total_fees = self.df['佣金'].sum() + self.df['手续费'].sum() + self.df['运费'].sum()
            fee_ratio = (total_fees / total_revenue) * 100 if total_revenue > 0 else 0

            if fee_ratio > 40:
                blackholes.append({
                    "类型": "费用过高",
                    "费用占比": f"{fee_ratio:.1f}%",
                    "损失估算": f"{total_fees * 0.1:.2f}",
                    "建议": "费用占比超过40%，建议优化物流或谈判平台费率"
                })

        return {
            "黑洞数量": len(blackholes),
            "黑洞列表": blackholes,
            "预估月损失": sum([float(b.get("损失估算", 0)) for b in blackholes if "损失估算" in b])
        }

    def analyze_cashflow_risk(self) -> Dict:
        """分析现金流风险"""
        risks = []

        # 应收账款分析
        if '交易状态' in self.df.columns and '实际到账' in self.df.columns:
            pending = self.df[self.df['交易状态'].isin(['待结算', '处理中', 'pending'])]
            if len(pending) > 0:
                risks.append({
                    "类型": "应收账款",
                    "金额": f"{pending['实际到账'].sum():.2f}",
                    "笔数": len(pending),
                    "风险": "资金被平台占用，影响现金流"
                })

        # 库存资金占用（如果有库存数据）
        if '库存' in self.df.columns and '成本' in self.df.columns:
            inventory_value = (self.df['库存'] * self.df['成本']).sum()
            if inventory_value > self.df['订单金额'].sum() * 0.5:
                risks.append({
                    "类型": "库存积压",
                    "金额": f"{inventory_value:.2f}",
                    "风险": "库存资金占用过高，建议促销清仓"
                })

        # 日均现金流
        if '日期' in self.df.columns and '实际到账' in self.df.columns:
            daily_cash = self.df.groupby(self.df['日期'].dt.date)['实际到账'].sum()
            if len(daily_cash) > 7:
                recent_avg = daily_cash.tail(7).mean()
                previous_avg = daily_cash.tail(14).head(7).mean()
                if previous_avg > 0 and recent_avg / previous_avg < 0.8:
                    risks.append({
                        "类型": "现金流下滑",
                        "下降幅度": f"{(1 - recent_avg/previous_avg)*100:.1f}%",
                        "风险": "近7天现金流较上周下降超过20%"
                    })

        return {
            "风险数量": len(risks),
            "风险列表": risks,
            "风险等级": "高" if len(risks) >= 3 else "中" if len(risks) >= 1 else "低"
        }

    def analyze_platform_health(self) -> Dict:
        """分析平台健康度"""
        if '平台' not in self.df.columns:
            return {"平台列表": []}

        platform_health = []
        for platform in self.df['平台'].unique():
            if pd.isna(platform):
                continue
            platform_df = self.df[self.df['平台'] == platform]

            health = {
                "平台": platform,
                "订单数": len(platform_df),
                "总销售额": f"{platform_df['订单金额'].sum():.2f}",
                "实际到账": f"{platform_df['实际到账'].sum():.2f}",
            }

            if '佣金' in platform_df.columns:
                health["佣金率"] = f"{(platform_df['佣金'].sum() / platform_df['订单金额'].sum() * 100):.1f}%"

            if '退款金额' in platform_df.columns:
                refund_rate = platform_df['退款金额'].sum() / platform_df['订单金额'].sum() * 100
                health["退款率"] = f"{refund_rate:.1f}%"
                health["健康度"] = "优" if refund_rate < 5 else "良" if refund_rate < 10 else "差"
            else:
                health["健康度"] = "良"

            platform_health.append(health)

        return {"平台列表": platform_health}

    def analyze_sku_performance(self) -> Dict:
        """分析SKU表现"""
        if 'SKU' not in self.df.columns:
            return {"SKU列表": []}

        sku_stats = self.df.groupby('SKU').agg({
            '订单金额': 'sum',
            '实际到账': 'sum',
            '数量': 'sum'
        }).reset_index()

        sku_stats['利润率'] = (sku_stats['实际到账'] / sku_stats['订单金额'].clip(lower=0.01)) * 100
        sku_stats = sku_stats.sort_values('实际到账', ascending=False)

        top_skus = sku_stats.head(10).to_dict('records')
        bottom_skus = sku_stats.tail(5).to_dict('records')

        return {
            "明星SKU": top_skus,
            "滞销SKU": bottom_skus,
            "SKU总数": len(sku_stats)
        }

    def calculate_overall_score(self) -> Dict:
        """计算综合健康评分"""
        scores = {
            "订单健康度": 100,
            "利润健康度": 100,
            "现金流健康度": 100,
            "平台健康度": 100,
        }

        # 根据异常数量扣分
        anomaly = self.detect_anomaly_orders()
        scores["订单健康度"] = anomaly.get("健康度", 100)

        # 利润黑洞扣分
        blackholes = self.analyze_profit_blackholes()
        scores["利润健康度"] = max(0, 100 - blackholes.get("黑洞数量", 0) * 20)

        # 现金流风险扣分
        cashflow = self.analyze_cashflow_risk()
        risk_level = cashflow.get("风险等级", "低")
        scores["现金流健康度"] = {"低": 100, "中": 70, "高": 40}.get(risk_level, 100)

        # 综合评分
        overall = sum(scores.values()) / len(scores)

        return {
            "综合评分": f"{overall:.0f}",
            "评分等级": "优秀" if overall >= 90 else "良好" if overall >= 75 else "一般" if overall >= 60 else "需改进",
            "分项评分": scores
        }

    def generate_action_items(self) -> List[Dict]:
        """生成行动建议"""
        actions = []

        # 基于异常订单
        anomaly = self.detect_anomaly_orders()
        if anomaly.get("异常总数", 0) > 0:
            actions.append({
                "优先级": "紧急",
                "行动": f"处理{anomaly['异常总数']}笔异常订单",
                "预期收益": "减少损失，提升数据准确性"
            })

        # 基于利润黑洞
        blackholes = self.analyze_profit_blackholes()
        for hole in blackholes.get("黑洞列表", []):
            actions.append({
                "优先级": "高",
                "行动": hole.get("建议", "优化成本结构"),
                "涉及": hole.get("平台", hole.get("SKU", "未知"))
            })

        # 基于现金流
        cashflow = self.analyze_cashflow_risk()
        for risk in cashflow.get("风险列表", []):
            actions.append({
                "优先级": "中",
                "行动": f"关注{risk['类型']}风险，金额{risk.get('金额', '未知')}",
                "预期收益": "保障现金流安全"
            })

        # 通用建议
        if '平台' in self.df.columns:
            platform_count = self.df['平台'].nunique()
            if platform_count < 3:
                actions.append({
                    "优先级": "低",
                    "行动": "考虑拓展更多销售渠道，分散平台风险",
                    "预期收益": "降低单一平台依赖"
                })

        return actions[:10]  # 最多返回10条
