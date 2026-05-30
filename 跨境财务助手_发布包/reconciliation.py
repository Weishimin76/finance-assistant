# -*- coding: utf-8 -*-
"""
跨境电商财务智能体 - 智能对账引擎
自动检测异常交易：重复订单、漏记退款、多扣佣金等
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from config import config


class AnomalyType:
    """异常类型常量"""
    DUPLICATE_ORDER = "重复订单"
    MISSING_REFUND = "漏记退款"
    OVER_COMMISSION = "多扣佣金"
    PRICE_ANOMALY = "价格异常"
    NEGATIVE_AMOUNT = "负数异常"
    MISSING_DATA = "数据缺失"
    DATE_ANOMALY = "日期异常"
    COMMISSION_ANOMALY = "佣金率异常"


class ReconciliationEngine:
    """智能对账引擎"""

    def __init__(self):
        self.anomalies = []
        self.commission_rates = config.commission_rates

    def reconcile(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        执行对账检查

        Args:
            df: 标准化后的订单数据

        Returns:
            (正常数据, 异常数据) 两个 DataFrame
        """
        self.anomalies = []
        df = df.copy()

        # 依次执行各项检查
        self._check_duplicates(df)
        self._check_commissions(df)
        self._check_price_anomalies(df)
        self._check_negative_amounts(df)
        self._check_missing_data(df)
        self._check_date_anomalies(df)

        # 标记异常行
        anomaly_indices = set()
        for a in self.anomalies:
            anomaly_indices.add(a["行号"])

        # 创建异常标记列
        df["异常标记"] = ""
        df["异常原因"] = ""

        for a in self.anomalies:
            idx = a["行号"]
            if df.loc[idx, "异常标记"]:
                df.loc[idx, "异常标记"] += " | "
                df.loc[idx, "异常原因"] += " | "
            df.loc[idx, "异常标记"] = "🔴"
            df.loc[idx, "异常原因"] += f"[{a['类型']}] {a['详情']}"

        # 分离正常和异常数据
        normal_df = df[~df.index.isin(anomaly_indices)].copy()
        anomaly_df = df[df.index.isin(anomaly_indices)].copy()

        return normal_df, anomaly_df

    def _check_duplicates(self, df: pd.DataFrame):
        """检查重复订单"""
        # 同平台同订单号出现多次
        for platform in df["平台"].unique():
            platform_df = df[df["平台"] == platform]
            dup_mask = platform_df.duplicated(subset=["平台订单号"], keep=False)
            for idx in platform_df[dup_mask].index:
                order_id = platform_df.loc[idx, "平台订单号"]
                count = len(platform_df[platform_df["平台订单号"] == order_id])
                self.anomalies.append({
                    "行号": idx,
                    "类型": AnomalyType.DUPLICATE_ORDER,
                    "详情": f"订单 {order_id} 在 {platform} 出现 {count} 次",
                    "严重程度": "高"
                })

    def _check_commissions(self, df: pd.DataFrame):
        """检查佣金是否异常偏高"""
        for platform, rates in self.commission_rates.items():
            platform_df = df[df["平台"].str.lower() == platform]
            if platform_df.empty:
                continue

            for idx, row in platform_df.iterrows():
                order_amount = row["订单金额"]
                commission = row["佣金"]

                if order_amount <= 0:
                    continue

                # 计算实际佣金率
                actual_rate = commission / order_amount

                # 如果佣金率超过最大值的1.5倍，标记异常
                max_rate = rates["max"] * 1.5
                if actual_rate > max_rate and commission > 0:
                    self.anomalies.append({
                        "行号": idx,
                        "类型": AnomalyType.OVER_COMMISSION,
                        "详情": f"佣金率 {actual_rate:.1%}，超出 {platform} 正常范围 "
                               f"({rates['min']:.0%}-{rates['max']:.0%})，"
                               f"佣金 ¥{commission:.2f}，订单金额 ¥{order_amount:.2f}",
                        "严重程度": "高"
                    })

    def _check_price_anomalies(self, df: pd.DataFrame):
        """检查价格异常（同SKU价格波动过大）"""
        sku_groups = df.groupby("SKU")
        for sku, group in sku_groups:
            if len(group) < 3 or sku == "":
                continue
            prices = group["单价"].values
            if np.std(prices) > 0 and np.mean(prices) > 0:
                cv = np.std(prices) / np.mean(prices)  # 变异系数
                if cv > 0.5:  # 变异系数超过50%
                    for idx in group.index:
                        price = group.loc[idx, "单价"]
                        avg_price = np.mean(prices)
                        deviation = abs(price - avg_price) / avg_price
                        if deviation > 0.5:
                            self.anomalies.append({
                                "行号": idx,
                                "类型": AnomalyType.PRICE_ANOMALY,
                                "详情": f"SKU {sku} 单价 ¥{price:.2f}，"
                                       f"均价 ¥{avg_price:.2f}，"
                                       f"偏差 {deviation:.0%}",
                                "严重程度": "中"
                            })

    def _check_negative_amounts(self, df: pd.DataFrame):
        """检查负数异常"""
        for idx, row in df.iterrows():
            if row["订单金额"] < 0 and row["退款金额"] == 0:
                self.anomalies.append({
                    "行号": idx,
                    "类型": AnomalyType.NEGATIVE_AMOUNT,
                    "详情": f"订单金额为负数 ¥{row['订单金额']:.2f}，但无退款记录",
                    "严重程度": "高"
                })

    def _check_missing_data(self, df: pd.DataFrame):
        """检查关键字段缺失"""
        critical_fields = ["平台订单号", "交易日期", "订单金额"]
        for idx, row in df.iterrows():
            missing = []
            for field in critical_fields:
                if pd.isna(row[field]) or str(row[field]).strip() == "":
                    missing.append(field)
            if missing:
                self.anomalies.append({
                    "行号": idx,
                    "类型": AnomalyType.MISSING_DATA,
                    "详情": f"缺少关键字段: {', '.join(missing)}",
                    "严重程度": "中"
                })

    def _check_date_anomalies(self, df: pd.DataFrame):
        """检查日期异常"""
        today = datetime.now()
        for idx, row in df.iterrows():
            date_str = str(row["交易日期"])
            if date_str == "" or date_str == "nan":
                continue
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
                # 未来日期
                if date > today + timedelta(days=1):
                    self.anomalies.append({
                        "行号": idx,
                        "类型": AnomalyType.DATE_ANOMALY,
                        "详情": f"交易日期 {date_str} 为未来日期",
                        "严重程度": "中"
                    })
                # 超过2年前的日期
                elif date < today - timedelta(days=730):
                    self.anomalies.append({
                        "行号": idx,
                        "类型": AnomalyType.DATE_ANOMALY,
                        "详情": f"交易日期 {date_str} 超过2年前",
                        "严重程度": "低"
                    })
            except ValueError:
                self.anomalies.append({
                    "行号": idx,
                    "类型": AnomalyType.DATE_ANOMALY,
                    "详情": f"日期格式异常: {date_str}",
                    "严重程度": "中"
                })

    def get_summary(self) -> pd.DataFrame:
        """获取异常汇总"""
        if not self.anomalies:
            return pd.DataFrame(columns=["类型", "数量", "严重程度"])

        summary = {}
        for a in self.anomalies:
            key = (a["类型"], a["严重程度"])
            summary[key] = summary.get(key, 0) + 1

        rows = []
        for (atype, severity), count in sorted(summary.items(), key=lambda x: -x[1]):
            rows.append({"类型": atype, "数量": count, "严重程度": severity})

        return pd.DataFrame(rows)


def reconcile_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    对账主入口函数

    Returns:
        (正常数据, 异常数据, 异常汇总)
    """
    engine = ReconciliationEngine()
    normal_df, anomaly_df = engine.reconcile(df)
    summary_df = engine.get_summary()
    return normal_df, anomaly_df, summary_df
