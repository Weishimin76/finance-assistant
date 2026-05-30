# -*- coding: utf-8 -*-
"""
跨境电商财务智能体 - 汇率波动监控模块
每日汇率获取 + 波动分析 + 换汇建议
"""
import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from config import config
import os
import csv


# 主要关注币种
MAJOR_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CNY", "SGD", "AUD", "CAD", "HKD"]

# 历史汇率存储文件
EXCHANGE_RATE_HISTORY_FILE = "data/exchange_rate_history.csv"

# 波动阈值
VOLATILITY_THRESHOLD = 0.02  # 2%


class ExchangeRateMonitor:
    """汇率监控器"""

    def __init__(self):
        self.base_currency = "CNY"  # 基准货币
        self.api_url = config.exchange_rate_api
        self.history_file = EXCHANGE_RATE_HISTORY_FILE
        self._ensure_history_file()

    def _ensure_history_file(self):
        """确保历史汇率文件存在"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.history_file):
            with open(self.history_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["日期", "币种", "汇率", "基准货币"])

    def fetch_current_rates(self, base: str = "CNY") -> Optional[Dict[str, float]]:
        """
        从 API 获取当前汇率

        Args:
            base: 基准货币

        Returns:
            {币种: 汇率} 字典
        """
        try:
            url = f"{self.api_url}/{base}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "rates" in data:
                return data["rates"]
            return None
        except Exception as e:
            print(f"获取汇率失败: {e}")
            return None

    def record_rates(self, rates: Dict[str, float], base: str = "CNY"):
        """
        记录当前汇率到历史文件

        Args:
            rates: 汇率字典
            base: 基准货币
        """
        today = datetime.now().strftime("%Y-%m-%d")
        with open(self.history_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for currency, rate in rates.items():
                if currency in MAJOR_CURRENCIES:
                    writer.writerow([today, currency, rate, base])

    def get_history(self, days: int = 30) -> pd.DataFrame:
        """
        获取历史汇率数据

        Args:
            days: 获取最近多少天的数据

        Returns:
            历史汇率 DataFrame
        """
        try:
            df = pd.read_csv(self.history_file, encoding="utf-8")
            df["日期"] = pd.to_datetime(df["日期"])
            cutoff = datetime.now() - timedelta(days=days)
            df = df[df["日期"] >= cutoff]
            return df
        except Exception:
            return pd.DataFrame(columns=["日期", "币种", "汇率", "基准货币"])

    def analyze_volatility(self, days: int = 7) -> pd.DataFrame:
        """
        分析汇率波动

        Args:
            days: 分析最近多少天

        Returns:
            波动分析 DataFrame
        """
        history = self.get_history(days + 1)
        if history.empty:
            return pd.DataFrame()

        results = []
        for currency in history["币种"].unique():
            currency_data = history[history["币种"] == currency].sort_values("日期")

            if len(currency_data) < 2:
                continue

            current_rate = currency_data.iloc[-1]["汇率"]
            previous_rate = currency_data.iloc[0]["汇率"]
            change_pct = (current_rate - previous_rate) / previous_rate if previous_rate != 0 else 0

            # 计算波动率（标准差 / 均值）
            rates = currency_data["汇率"].values
            volatility = np.std(rates) / np.mean(rates) if np.mean(rates) != 0 else 0

            # 最高最低
            max_rate = currency_data["汇率"].max()
            min_rate = currency_data["汇率"].min()

            # 趋势判断
            if change_pct > VOLATILITY_THRESHOLD:
                trend = "📈 大幅升值"
                alert = "🔴"
            elif change_pct < -VOLATILITY_THRESHOLD:
                trend = "📉 大幅贬值"
                alert = "🔴"
            elif change_pct > VOLATILITY_THRESHOLD / 2:
                trend = "↗️ 小幅升值"
                alert = "🟡"
            elif change_pct < -VOLATILITY_THRESHOLD / 2:
                trend = "↘️ 小幅贬值"
                alert = "🟡"
            else:
                trend = "➡️ 基本稳定"
                alert = "🟢"

            results.append({
                "币种": currency,
                "当前汇率": round(current_rate, 4),
                f"{days}天前汇率": round(previous_rate, 4),
                "变化幅度": f"{change_pct:+.2%}",
                "波动率": f"{volatility:.2%}",
                "期间最高": round(max_rate, 4),
                "期间最低": round(min_rate, 4),
                "趋势": trend,
                "提醒": alert,
            })

        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values("波动率", ascending=False).reset_index(drop=True)
        return df

    def get_exchange_suggestion(self, from_currency: str, to_currency: str, amount: float) -> str:
        """
        生成换汇建议

        Args:
            from_currency: 卖出币种
            to_currency: 买入币种
            amount: 金额

        Returns:
            换汇建议文本
        """
        rates = self.fetch_current_rates(base=from_currency)
        if not rates or to_currency not in rates:
            return f"⚠️ 无法获取 {from_currency}/{to_currency} 汇率"

        current_rate = rates[to_currency]
        converted = amount * current_rate

        # 分析趋势
        history = self.get_history(days=7)
        if not history.empty:
            pair_history = history[history["币种"] == to_currency]
            if len(pair_history) >= 2:
                old_rate = pair_history.iloc[0]["汇率"]
                change = (current_rate - old_rate) / old_rate

                if change > 0.01:
                    suggestion = (
                        f"💱 换汇建议\n\n"
                        f"**当前汇率**: 1 {from_currency} = {current_rate:.4f} {to_currency}\n"
                        f"**兑换金额**: {amount:,.2f} {from_currency} → {converted:,.2f} {to_currency}\n"
                        f"**7日趋势**: {change:+.2%} ({from_currency} 相对 {to_currency})\n\n"
                        f"📊 **建议**: {to_currency} 近期呈升值趋势，建议尽快换汇锁定汇率。"
                    )
                elif change < -0.01:
                    suggestion = (
                        f"💱 换汇建议\n\n"
                        f"**当前汇率**: 1 {from_currency} = {current_rate:.4f} {to_currency}\n"
                        f"**兑换金额**: {amount:,.2f} {from_currency} → {converted:,.2f} {to_currency}\n"
                        f"**7日趋势**: {change:+.2%} ({from_currency} 相对 {to_currency})\n\n"
                        f"📊 **建议**: {to_currency} 近期呈贬值趋势，建议观望，等待更有利汇率。"
                    )
                else:
                    suggestion = (
                        f"💱 换汇建议\n\n"
                        f"**当前汇率**: 1 {from_currency} = {current_rate:.4f} {to_currency}\n"
                        f"**兑换金额**: {amount:,.2f} {from_currency} → {converted:,.2f} {to_currency}\n"
                        f"**7日趋势**: {change:+.2%} (基本稳定)\n\n"
                        f"📊 **建议**: 汇率相对稳定，可按需换汇。"
                    )
                return suggestion

        return (
            f"💱 换汇参考\n\n"
            f"**当前汇率**: 1 {from_currency} = {current_rate:.4f} {to_currency}\n"
            f"**兑换金额**: {amount:,.2f} {from_currency} → {converted:,.2f} {to_currency}\n\n"
            f"⚠️ 历史数据不足，无法给出趋势建议。"
        )

    def get_alerts(self) -> List[Dict]:
        """
        获取汇率预警

        Returns:
            预警列表
        """
        volatility_df = self.analyze_volatility(days=7)
        alerts = []

        if volatility_df.empty:
            return alerts

        for _, row in volatility_df.iterrows():
            change_str = row["变化幅度"].replace("+", "").replace("%", "")
            try:
                change = float(change_str) / 100
            except ValueError:
                continue

            if abs(change) > VOLATILITY_THRESHOLD:
                alerts.append({
                    "币种": row["币种"],
                    "变化幅度": row["变化幅度"],
                    "当前汇率": row["当前汇率"],
                    "趋势": row["趋势"],
                    "级别": "🔴 高" if abs(change) > 0.03 else "🟡 中",
                })

        return alerts

    def update_and_analyze(self) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        更新汇率并分析（每日调用）

        Returns:
            (波动分析表, 预警列表)
        """
        rates = self.fetch_current_rates()
        if rates:
            self.record_rates(rates)

        volatility_df = self.analyze_volatility()
        alerts = self.get_alerts()

        return volatility_df, alerts


# 全局实例
exchange_monitor = ExchangeRateMonitor()
