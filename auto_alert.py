# -*- coding: utf-8 -*-
"""
自动化预警系统 - 汇率波动、利润下滑、税务到期提醒
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os


class AutoAlertSystem:
    """自动化预警引擎"""

    def __init__(self, user_id: int = None):
        self.user_id = user_id
        self.alert_history = []
        self.alert_config = self._load_config()

    def _load_config(self) -> Dict:
        """加载预警配置"""
        default_config = {
            "汇率预警": {
                "enabled": True,
                "threshold": 2.0,  # 汇率波动超过2%预警
                "currencies": ["USD", "EUR", "GBP", "JPY"]
            },
            "利润预警": {
                "enabled": True,
                "threshold": -10.0,  # 利润下降超过10%预警
                "period": 7  # 对比7天数据
            },
            "税务预警": {
                "enabled": True,
                "vat_deadline": 15,  # VAT申报截止日（每月15日）
                "advance_days": 3  # 提前3天提醒
            },
            "异常订单预警": {
                "enabled": True,
                "threshold": 5  # 单日异常订单超过5笔预警
            },
            "库存预警": {
                "enabled": True,
                "low_stock_threshold": 10  # 库存低于10预警
            }
        }
        return default_config

    def check_all_alerts(self, df: pd.DataFrame = None, exchange_rates: Dict = None) -> List[Dict]:
        """检查所有预警"""
        alerts = []

        # 1. 汇率波动预警
        if self.alert_config["汇率预警"]["enabled"] and exchange_rates:
            rate_alerts = self._check_exchange_rate_alerts(exchange_rates)
            alerts.extend(rate_alerts)

        # 2. 利润下滑预警
        if self.alert_config["利润预警"]["enabled"] and df is not None and len(df) > 0:
            profit_alerts = self._check_profit_decline(df)
            alerts.extend(profit_alerts)

        # 3. 税务到期预警
        if self.alert_config["税务预警"]["enabled"]:
            tax_alerts = self._check_tax_deadlines()
            alerts.extend(tax_alerts)

        # 4. 异常订单预警
        if self.alert_config["异常订单预警"]["enabled"] and df is not None:
            anomaly_alerts = self._check_anomaly_orders(df)
            alerts.extend(anomaly_alerts)

        # 5. 库存预警
        if self.alert_config["库存预警"]["enabled"] and df is not None:
            stock_alerts = self._check_low_stock(df)
            alerts.extend(stock_alerts)

        # 保存预警历史
        self.alert_history.extend(alerts)

        return sorted(alerts, key=lambda x: {"紧急": 0, "高": 1, "中": 2, "低": 3}.get(x["级别"], 4))

    def _check_exchange_rate_alerts(self, current_rates: Dict) -> List[Dict]:
        """检查汇率波动"""
        alerts = []
        threshold = self.alert_config["汇率预警"]["threshold"]

        # 模拟历史汇率（实际应从数据库或API获取）
        # 这里使用简单的基准汇率进行比较
        base_rates = {
            "USD": 7.2,
            "EUR": 7.8,
            "GBP": 9.1,
            "JPY": 0.048
        }

        for currency, rate in current_rates.items():
            if currency in base_rates:
                base_rate = base_rates[currency]
                change_pct = abs((rate - base_rate) / base_rate) * 100

                if change_pct > threshold:
                    direction = "升值" if rate > base_rate else "贬值"
                    alerts.append({
                        "类型": "汇率波动",
                        "级别": "高" if change_pct > 5 else "中",
                        "货币": currency,
                        "当前汇率": f"{rate:.4f}",
                        "基准汇率": f"{base_rate:.4f}",
                        "波动幅度": f"{change_pct:.2f}%",
                        "方向": direction,
                        "建议": f"{currency}{direction}{change_pct:.1f}%，建议{'尽快结汇' if direction == '升值' else '暂缓结汇'}",
                        "时间": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })

        return alerts

    def _check_profit_decline(self, df: pd.DataFrame) -> List[Dict]:
        """检查利润下滑"""
        alerts = []
        threshold = self.alert_config["利润预警"]["threshold"]
        period = self.alert_config["利润预警"]["period"]

        if '日期' not in df.columns or '实际到账' not in df.columns:
            return alerts

        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        df = df.dropna(subset=['日期'])

        if len(df) < period * 2:
            return alerts

        # 按日期分组计算日利润
        daily_profit = df.groupby(df['日期'].dt.date)['实际到账'].sum().sort_index()

        if len(daily_profit) < period * 2:
            return alerts

        # 对比最近period天和前period天
        recent_profit = daily_profit.tail(period).sum()
        previous_profit = daily_profit.tail(period * 2).head(period).sum()

        if previous_profit > 0:
            decline_pct = (recent_profit - previous_profit) / previous_profit * 100

            if decline_pct < threshold:
                alerts.append({
                    "类型": "利润下滑",
                    "级别": "紧急" if decline_pct < -20 else "高",
                    "最近利润": f"{recent_profit:.2f}",
                    "上期利润": f"{previous_profit:.2f}",
                    "下滑幅度": f"{decline_pct:.1f}%",
                    "对比周期": f"最近{period}天 vs 前{period}天",
                    "建议": "立即分析利润下滑原因，检查费用结构和定价策略",
                    "时间": datetime.now().strftime("%Y-%m-%d %H:%M")
                })

        return alerts

    def _check_tax_deadlines(self) -> List[Dict]:
        """检查税务到期"""
        alerts = []
        config = self.alert_config["税务预警"]
        vat_deadline = config["vat_deadline"]
        advance_days = config["advance_days"]

        today = datetime.now()

        # VAT申报提醒
        next_vat_date = datetime(today.year, today.month, vat_deadline)
        if today.day > vat_deadline:
            # 本月已过，计算下月
            if today.month == 12:
                next_vat_date = datetime(today.year + 1, 1, vat_deadline)
            else:
                next_vat_date = datetime(today.year, today.month + 1, vat_deadline)

        days_until_vat = (next_vat_date - today).days

        if days_until_vat <= advance_days:
            alerts.append({
                "类型": "税务到期",
                "级别": "高" if days_until_vat <= 1 else "中",
                "税种": "VAT增值税",
                "截止日期": next_vat_date.strftime("%Y-%m-%d"),
                "剩余天数": days_until_vat,
                "建议": f"VAT申报即将到期，请准备相关材料，剩余{days_until_vat}天",
                "时间": today.strftime("%Y-%m-%d %H:%M")
            })

        # 季度税务提醒
        if today.month in [1, 4, 7, 10] and today.day <= 15:
            alerts.append({
                "类型": "税务到期",
                "级别": "中",
                "税种": "季度所得税",
                "截止日期": datetime(today.year, today.month, 15).strftime("%Y-%m-%d"),
                "剩余天数": 15 - today.day,
                "建议": "季度所得税申报期，请准备财务报表",
                "时间": today.strftime("%Y-%m-%d %H:%M")
            })

        return alerts

    def _check_anomaly_orders(self, df: pd.DataFrame) -> List[Dict]:
        """检查异常订单"""
        alerts = []
        threshold = self.alert_config["异常订单预警"]["threshold"]

        if '日期' not in df.columns:
            return alerts

        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        today = datetime.now().date()
        today_orders = df[df['日期'].dt.date == today]

        # 检查高退款订单
        if '退款金额' in today_orders.columns and '订单金额' in today_orders.columns:
            high_refund = today_orders[today_orders['退款金额'] / today_orders['订单金额'].clip(lower=0.01) > 0.5]
            if len(high_refund) > threshold:
                alerts.append({
                    "类型": "异常订单",
                    "级别": "高",
                    "异常类型": "高退款率",
                    "今日异常数": len(high_refund),
                    "涉及金额": f"{high_refund['订单金额'].sum():.2f}",
                    "建议": "今日高退款订单异常增多，请检查产品质量或物流问题",
                    "时间": datetime.now().strftime("%Y-%m-%d %H:%M")
                })

        # 检查负利润订单
        if '实际到账' in today_orders.columns:
            negative_profit = today_orders[today_orders['实际到账'] < 0]
            if len(negative_profit) > threshold:
                alerts.append({
                    "类型": "异常订单",
                    "级别": "紧急",
                    "异常类型": "亏损订单",
                    "今日异常数": len(negative_profit),
                    "涉及金额": f"{negative_profit['订单金额'].sum():.2f}",
                    "建议": "今日出现多笔亏损订单，请立即检查定价和成本结构",
                    "时间": datetime.now().strftime("%Y-%m-%d %H:%M")
                })

        return alerts

    def _check_low_stock(self, df: pd.DataFrame) -> List[Dict]:
        """检查低库存"""
        alerts = []
        threshold = self.alert_config["库存预警"]["low_stock_threshold"]

        if '库存' not in df.columns or 'SKU' not in df.columns:
            return alerts

        # 获取最新库存数据
        latest_stock = df.groupby('SKU')['库存'].last().reset_index()
        low_stock = latest_stock[latest_stock['库存'] <= threshold]

        for _, item in low_stock.iterrows():
            alerts.append({
                "类型": "库存预警",
                "级别": "中" if item['库存'] > 0 else "高",
                "SKU": item['SKU'],
                "当前库存": int(item['库存']),
                "建议": f"{'库存告急，请立即补货' if item['库存'] <= 0 else '库存偏低，建议安排补货'}",
                "时间": datetime.now().strftime("%Y-%m-%d %H:%M")
            })

        return alerts

    def get_alert_summary(self) -> Dict:
        """获取预警摘要"""
        if not self.alert_history:
            return {
                "状态": "正常",
                "待处理预警": 0,
                "最近预警": None
            }

        recent_alerts = [a for a in self.alert_history
                        if datetime.strptime(a["时间"], "%Y-%m-%d %H:%M") > datetime.now() - timedelta(days=7)]

        urgent_count = sum(1 for a in recent_alerts if a["级别"] in ["紧急", "高"])

        return {
            "状态": "有预警" if urgent_count > 0 else "正常",
            "待处理预警": len(recent_alerts),
            "紧急预警": urgent_count,
            "最近预警": recent_alerts[-1] if recent_alerts else None,
            "预警类型分布": self._get_alert_type_distribution(recent_alerts)
        }

    def _get_alert_type_distribution(self, alerts: List[Dict]) -> Dict:
        """获取预警类型分布"""
        distribution = {}
        for alert in alerts:
            alert_type = alert.get("类型", "其他")
            distribution[alert_type] = distribution.get(alert_type, 0) + 1
        return distribution

    def update_config(self, alert_type: str, config: Dict):
        """更新预警配置"""
        if alert_type in self.alert_config:
            self.alert_config[alert_type].update(config)
            return True
        return False

    def export_alerts(self, format: str = "json") -> str:
        """导出预警记录"""
        if format == "json":
            return json.dumps(self.alert_history, ensure_ascii=False, indent=2)
        elif format == "csv":
            if not self.alert_history:
                return "类型,级别,时间,建议\n"
            df = pd.DataFrame(self.alert_history)
            return df.to_csv(index=False)
        else:
            return "不支持的格式"
