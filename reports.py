# -*- coding: utf-8 -*-
"""
跨境电商财务智能体 - 报表自动生成模块
原始数据 → 公司固定格式报表 + 同比环比分析
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional


class ReportGenerator:
    """报表生成器"""

    def __init__(self):
        self.currency_map = {
            "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥",
            "CNY": "¥", "SGD": "S$", "AUD": "A$", "CAD": "C$",
        }

    def generate_summary_report(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成收支汇总报表

        Args:
            df: 标准化订单数据

        Returns:
            汇总报表 DataFrame
        """
        if df.empty:
            return pd.DataFrame()

        # 按平台汇总
        platform_summary = df.groupby("平台").agg(
            订单数=("订单号", "count"),
            总销售额=("订单金额", "sum"),
            总佣金=("佣金", "sum"),
            总手续费=("手续费", "sum"),
            总运费=("运费", "sum"),
            总退款=("退款金额", "sum"),
            实际到账=("实际到账", "sum"),
        ).reset_index()

        platform_summary["净收入"] = platform_summary["实际到账"]
        platform_summary["退款率"] = (
            platform_summary["总退款"] / platform_summary["总销售额"]
        ).fillna(0).apply(lambda x: f"{x:.1%}")
        platform_summary["佣金率"] = (
            platform_summary["总佣金"] / platform_summary["总销售额"]
        ).fillna(0).apply(lambda x: f"{x:.1%}")

        # 合计行
        total_row = pd.DataFrame({
            "平台": ["合计"],
            "订单数": [platform_summary["订单数"].sum()],
            "总销售额": [platform_summary["总销售额"].sum()],
            "总佣金": [platform_summary["总佣金"].sum()],
            "总手续费": [platform_summary["总手续费"].sum()],
            "总运费": [platform_summary["总运费"].sum()],
            "总退款": [platform_summary["总退款"].sum()],
            "实际到账": [platform_summary["实际到账"].sum()],
            "净收入": [platform_summary["净收入"].sum()],
            "退款率": [f"{platform_summary['总退款'].sum() / platform_summary['总销售额'].sum():.1%}" if platform_summary['总销售额'].sum() > 0 else "0%"],
            "佣金率": [f"{platform_summary['总佣金'].sum() / platform_summary['总销售额'].sum():.1%}" if platform_summary['总销售额'].sum() > 0 else "0%"],
        })

        return pd.concat([platform_summary, total_row], ignore_index=True)

    def generate_monthly_report(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成月度报表

        Args:
            df: 标准化订单数据

        Returns:
            月度报表 DataFrame
        """
        if df.empty:
            return pd.DataFrame()

        df = df.copy()
        df["月份"] = pd.to_datetime(df["交易日期"], errors="coerce").dt.to_period("M").astype(str)

        monthly = df.groupby("月份").agg(
            订单数=("订单号", "count"),
            总销售额=("订单金额", "sum"),
            总成本=("佣金", lambda x: x.sum() + df.loc[x.index, "手续费"].sum()),
            总退款=("退款金额", "sum"),
            净收入=("实际到账", "sum"),
        ).reset_index()

        # 同比分析（需要至少2年数据）
        monthly["年份"] = monthly["月份"].str[:4]
        monthly["月"] = monthly["月份"].str[5:]

        # 环比分析
        monthly["销售额环比"] = monthly["总销售额"].pct_change().fillna(0).apply(lambda x: f"{x:+.1%}")
        monthly["净收入环比"] = monthly["净收入"].pct_change().fillna(0).apply(lambda x: f"{x:+.1%}")

        # 同比分析（与去年同期对比）
        monthly["去年同期销售额"] = 0.0
        monthly["销售额同比"] = "N/A"

        for i, row in monthly.iterrows():
            year = row["年份"]
            month = row["月"]
            last_year_month = f"{int(year) - 1}-{month}"
            last_year_row = monthly[monthly["月份"] == last_year_month]
            if not last_year_row.empty:
                last_year_sales = last_year_row["总销售额"].values[0]
                monthly.loc[i, "去年同期销售额"] = last_year_sales
                if last_year_sales > 0:
                    yoy = (row["总销售额"] - last_year_sales) / last_year_sales
                    monthly.loc[i, "销售额同比"] = f"{yoy:+.1%}"

        return monthly

    def generate_platform_report(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成各平台对比报表

        Args:
            df: 标准化订单数据

        Returns:
            平台对比 DataFrame
        """
        if df.empty:
            return pd.DataFrame()

        df = df.copy()
        df["月份"] = pd.to_datetime(df["交易日期"], errors="coerce").dt.to_period("M").astype(str)

        # 按平台+月份汇总
        pivot = df.pivot_table(
            values="订单金额",
            index="月份",
            columns="平台",
            aggfunc="sum",
            fill_value=0
        ).reset_index()

        # 添加合计列
        numeric_cols = pivot.select_dtypes(include=[np.number]).columns
        pivot["合计"] = pivot[numeric_cols].sum(axis=1)

        return pivot

    def generate_currency_report(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成币种分布报表

        Args:
            df: 标准化订单数据

        Returns:
            币种汇总 DataFrame
        """
        if df.empty:
            return pd.DataFrame()

        currency_summary = df.groupby("币种").agg(
            订单数=("订单号", "count"),
            总金额=("订单金额", "sum"),
            平均订单额=("订单金额", "mean"),
            总到账=("实际到账", "sum"),
        ).reset_index()

        currency_summary["占比"] = (
            currency_summary["总金额"] / currency_summary["总金额"].sum()
        ).apply(lambda x: f"{x:.1%}")

        return currency_summary

    def generate_sku_report(self, df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
        """
        生成 SKU 销售排行

        Args:
            df: 标准化订单数据
            top_n: 显示前N个

        Returns:
            SKU 排行 DataFrame
        """
        if df.empty:
            return pd.DataFrame()

        sku_report = df.groupby(["SKU", "商品名称"]).agg(
            销售数量=("数量", "sum"),
            销售额=("订单金额", "sum"),
            退款次数=("退款金额", lambda x: (x > 0).sum()),
            退款金额=("退款金额", "sum"),
            订单数=("订单号", "count"),
        ).reset_index()

        sku_report["平均单价"] = sku_report["销售额"] / sku_report["销售数量"].replace(0, np.nan)
        sku_report["退款率"] = (sku_report["退款次数"] / sku_report["订单数"]).fillna(0).apply(lambda x: f"{x:.1%}")

        sku_report = sku_report.sort_values("销售额", ascending=False).head(top_n)

        return sku_report.reset_index(drop=True)


def generate_all_reports(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    生成所有报表

    Returns:
        报表字典: {报表名: DataFrame}
    """
    generator = ReportGenerator()
    reports = {
        "收支汇总": generator.generate_summary_report(df),
        "月度报表": generator.generate_monthly_report(df),
        "平台对比": generator.generate_platform_report(df),
        "币种分布": generator.generate_currency_report(df),
        "SKU排行TOP20": generator.generate_sku_report(df),
    }
    return reports
