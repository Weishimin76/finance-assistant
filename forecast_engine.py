# -*- coding: utf-8 -*-
"""
预测与模拟引擎 - 销量预测、利润模拟、汇率对冲建议
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import warnings
warnings.filterwarnings('ignore')


class ForecastEngine:
    """预测与模拟引擎"""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self._preprocess()

    def _preprocess(self):
        """数据预处理"""
        numeric_cols = ['订单金额', '佣金', '手续费', '运费', '实际到账', '数量']
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)

        if '日期' in self.df.columns:
            self.df['日期'] = pd.to_datetime(self.df['日期'], errors='coerce')

    def sales_forecast(self, days: int = 30) -> Dict:
        """销量预测"""
        if '日期' not in self.df.columns or '订单金额' not in self.df.columns:
            return {"错误": "缺少日期或订单金额数据"}

        # 按日期聚合
        daily_sales = self.df.groupby(self.df['日期'].dt.date).agg({
            '订单金额': 'sum',
            '数量': 'sum'
        }).reset_index()
        daily_sales['日期'] = pd.to_datetime(daily_sales['日期'])
        daily_sales = daily_sales.sort_values('日期')

        if len(daily_sales) < 7:
            return {"错误": "数据不足，至少需要7天数据"}

        # 创建特征
        daily_sales['天数'] = range(len(daily_sales))
        daily_sales['星期'] = daily_sales['日期'].dt.dayofweek
        daily_sales['月份'] = daily_sales['日期'].dt.month
        daily_sales['是否周末'] = (daily_sales['星期'] >= 5).astype(int)

        # 使用最近30天数据训练
        train_data = daily_sales.tail(min(30, len(daily_sales)))

        # 简单线性回归预测
        X = train_data[['天数', '是否周末']].values
        y_revenue = train_data['订单金额'].values
        y_quantity = train_data['数量'].values

        model_revenue = LinearRegression()
        model_quantity = LinearRegression()

        model_revenue.fit(X, y_revenue)
        model_quantity.fit(X, y_quantity)

        # 预测未来days天
        last_day = daily_sales['天数'].max()
        future_dates = []
        future_revenue = []
        future_quantity = []

        for i in range(1, days + 1):
            future_day = last_day + i
            future_date = daily_sales['日期'].max() + timedelta(days=i)
            is_weekend = 1 if future_date.weekday() >= 5 else 0

            X_future = np.array([[future_day, is_weekend]])
            pred_revenue = max(0, model_revenue.predict(X_future)[0])
            pred_quantity = max(0, model_quantity.predict(X_future)[0])

            future_dates.append(future_date.strftime("%m-%d"))
            future_revenue.append(pred_revenue)
            future_quantity.append(pred_quantity)

        # 计算趋势
        recent_avg = np.mean(daily_sales['订单金额'].tail(7))
        forecast_avg = np.mean(future_revenue[:7])
        trend = (forecast_avg - recent_avg) / recent_avg * 100 if recent_avg > 0 else 0

        return {
            "预测天数": days,
            "预测日期": future_dates,
            "预测销售额": [f"{r:.2f}" for r in future_revenue],
            "预测销量": [int(q) for q in future_quantity],
            "总预测销售额": f"{sum(future_revenue):.2f}",
            "总预测销量": int(sum(future_quantity)),
            "日均预测": f"{np.mean(future_revenue):.2f}",
            "趋势": "上升" if trend > 5 else "下降" if trend < -5 else "平稳",
            "趋势幅度": f"{trend:.1f}%",
            "置信度": "中" if len(train_data) > 14 else "低"
        }

    def profit_simulation(self, scenarios: List[Dict] = None) -> Dict:
        """利润模拟"""
        if scenarios is None:
            scenarios = [
                {"name": "当前情况", "price_change": 0, "cost_change": 0, "volume_change": 0},
                {"name": "提价10%", "price_change": 10, "cost_change": 0, "volume_change": -5},
                {"name": "降价10%", "price_change": -10, "cost_change": 0, "volume_change": 15},
                {"name": "优化成本", "price_change": 0, "cost_change": -10, "volume_change": 0},
            ]

        current_revenue = self.df['订单金额'].sum()
        current_profit = self.df['实际到账'].sum()
        current_orders = len(self.df)

        results = []
        for scenario in scenarios:
            price_mult = 1 + scenario["price_change"] / 100
            cost_mult = 1 + scenario["cost_change"] / 100
            volume_mult = 1 + scenario["volume_change"] / 100

            new_revenue = current_revenue * price_mult * volume_mult
            new_cost = (current_revenue - current_profit) * cost_mult * volume_mult
            new_profit = new_revenue - new_cost
            new_orders = int(current_orders * volume_mult)

            results.append({
                "场景": scenario["name"],
                "订单量": new_orders,
                "收入": f"{new_revenue:.2f}",
                "利润": f"{new_profit:.2f}",
                "利润率": f"{(new_profit/new_revenue*100):.1f}%" if new_revenue > 0 else "0%",
                "利润变化": f"{(new_profit - current_profit)/current_profit*100:+.1f}%" if current_profit > 0 else "0%",
                "vs当前": "🔥 最优" if new_profit == max([r["利润"] for r in results + [{"利润": new_profit}]]) else ""
            })

        # 找出最优方案
        best = max(results, key=lambda x: float(x["利润"]))

        return {
            "当前状态": {
                "订单量": current_orders,
                "收入": f"{current_revenue:.2f}",
                "利润": f"{current_profit:.2f}"
            },
            "模拟结果": results,
            "最优方案": best["场景"],
            "建议": f"建议采用'{best['场景']}'方案，预计利润提升{best['利润变化']}"
        }

    def exchange_rate_hedging(self, currency: str = "USD", amount: float = 10000) -> Dict:
        """汇率对冲建议"""
        # 模拟当前汇率和近期波动
        current_rates = {
            "USD": 7.25,
            "EUR": 7.85,
            "GBP": 9.15,
            "JPY": 0.049
        }

        if currency not in current_rates:
            return {"错误": f"不支持的货币: {currency}"}

        current_rate = current_rates[currency]

        # 模拟近期波动数据
        np.random.seed(42)
        recent_rates = current_rate + np.random.normal(0, current_rate * 0.01, 30)
        volatility = np.std(recent_rates) / np.mean(recent_rates) * 100

        # 计算不同对冲比例的效果
        hedging_scenarios = []
        for hedge_ratio in [0, 25, 50, 75, 100]:
            hedged_amount = amount * hedge_ratio / 100
            unhedged_amount = amount - hedged_amount

            # 假设汇率波动±2%
            best_case = unhedged_amount * (1 + 0.02) + hedged_amount
            worst_case = unhedged_amount * (1 - 0.02) + hedged_amount
            expected = (best_case + worst_case) / 2

            hedging_scenarios.append({
                "对冲比例": f"{hedge_ratio}%",
                "对冲金额": f"{hedged_amount:.2f}",
                "未对冲金额": f"{unhedged_amount:.2f}",
                "最佳情况": f"{best_case:.2f}",
                "最差情况": f"{worst_case:.2f}",
                "预期收益": f"{expected:.2f}",
                "风险等级": "高" if hedge_ratio < 25 else "中" if hedge_ratio < 75 else "低"
            })

        # 推荐对冲比例
        recommended = 50 if volatility > 3 else 25 if volatility > 1.5 else 0

        return {
            "货币": currency,
            "当前汇率": f"{current_rate:.4f}",
            "波动率": f"{volatility:.2f}%",
            "待对冲金额": amount,
            "对冲方案": hedging_scenarios,
            "推荐对冲比例": f"{recommended}%",
            "推荐理由": f"当前{currency}波动率{volatility:.1f}%，建议对冲{recommended}%降低风险" if recommended > 0 else "当前汇率稳定，暂不需要对冲",
            "操作建议": [
                "使用远期外汇合约锁定汇率" if recommended > 0 else "继续观察汇率走势",
                "分批结汇降低时点风险" if volatility > 2 else "按需结汇",
                "关注央行政策变化对汇率的影响"
            ]
        }

    def inventory_optimization(self) -> Dict:
        """库存优化建议"""
        if 'SKU' not in self.df.columns or '数量' not in self.df.columns:
            return {"错误": "缺少SKU或数量数据"}

        # 计算每个SKU的销售速度和库存周转
        sku_stats = self.df.groupby('SKU').agg({
            '数量': 'sum',
            '订单金额': 'sum'
        }).reset_index()

        sku_stats['日均销量'] = sku_stats['数量'] / 30  # 假设30天数据
        sku_stats['周转天数'] = 30  # 假设当前库存为30天销量

        # 分类
        fast_moving = sku_stats[sku_stats['日均销量'] > sku_stats['日均销量'].quantile(0.75)]
        slow_moving = sku_stats[sku_stats['日均销量'] < sku_stats['日均销量'].quantile(0.25)]

        recommendations = []

        # 畅销品建议
        for _, sku in fast_moving.head(5).iterrows():
            recommendations.append({
                "SKU": sku['SKU'],
                "类型": "畅销品",
                "日均销量": f"{sku['日均销量']:.1f}",
                "建议": "增加安全库存至45天",
                "补货量": f"{int(sku['日均销量'] * 45)}"
            })

        # 滞销品建议
        for _, sku in slow_moving.head(5).iterrows():
            recommendations.append({
                "SKU": sku['SKU'],
                "类型": "滞销品",
                "日均销量": f"{sku['日均销量']:.1f}",
                "建议": "减少库存至15天或促销清仓",
                "建议库存": f"{int(sku['日均销量'] * 15)}"
            })

        return {
            "SKU总数": len(sku_stats),
            "畅销品数": len(fast_moving),
            "滞销品数": len(slow_moving),
            "库存建议": recommendations,
            "总体建议": [
                f"畅销品({len(fast_moving)}个)增加安全库存，避免断货",
                f"滞销品({len(slow_moving)}个)考虑促销或下架",
                "定期review库存周转率，优化资金占用"
            ]
        }

    def seasonality_analysis(self) -> Dict:
        """季节性分析"""
        if '日期' not in self.df.columns or '订单金额' not in self.df.columns:
            return {"错误": "缺少日期或订单金额数据"}

        self.df['月份'] = self.df['日期'].dt.month
        self.df['星期'] = self.df['日期'].dt.dayofweek

        # 月度分析
        monthly = self.df.groupby('月份')['订单金额'].sum()
        peak_month = monthly.idxmax()
        low_month = monthly.idxmin()

        # 周内分析
        weekly = self.df.groupby('星期')['订单金额'].sum()
        peak_day = weekly.idxmax()
        low_day = weekly.idxmin()

        day_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

        return {
            "销售旺季": f"{peak_month}月",
            "销售淡季": f"{low_month}月",
            "周内高峰": day_names[peak_day],
            "周内低谷": day_names[low_day],
            "月度分布": {f"{m}月": f"{v:.2f}" for m, v in monthly.items()},
            "建议": [
                f"在{peak_month}月前提前备货，加大营销投入",
                f"{low_month}月可考虑清仓促销或开发新品",
                f"{day_names[peak_day]}是销售高峰，适合上新和促销",
                f"{day_names[low_day]}销售较低，可安排运营复盘"
            ]
        }
