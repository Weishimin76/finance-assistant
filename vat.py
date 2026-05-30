# -*- coding: utf-8 -*-
"""
跨境电商财务智能体 - VAT 算税报税模块
按各国税率自动计算，生成税代格式，到期提醒
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from config import config


# 各国 VAT 申报截止日（每季度）
# 格式: (月份, 日) — 表示该季度申报截止日
VAT_DEADLINES = {
    "德国": [(1, 31), (4, 30), (7, 31), (10, 31)],
    "法国": [(1, 19), (4, 19), (7, 19), (10, 19)],
    "意大利": [(1, 16), (4, 16), (7, 16), (10, 16)],
    "西班牙": [(1, 20), (4, 20), (7, 20), (10, 20)],
    "英国": [(1, 31), (4, 30), (7, 31), (10, 31)],
    "荷兰": [(1, 31), (4, 30), (7, 31), (10, 31)],
    "波兰": [(1, 25), (4, 25), (7, 25), (10, 25)],
    "比利时": [(1, 20), (4, 20), (7, 20), (10, 20)],
    "瑞典": [(1, 26), (4, 26), (7, 26), (10, 26)],
    "捷克": [(1, 25), (4, 25), (7, 25), (10, 25)],
}

# 各国 VAT 注册号格式示例
VAT_NUMBER_FORMATS = {
    "德国": "DE#########",
    "法国": "FR## #########",
    "意大利": "IT#########",
    "西班牙": "ES#########",
    "英国": "GB#########",
    "荷兰": "NL##########",
    "波兰": "PL##########",
    "比利时": "BE#########",
    "瑞典": "SE##########",
    "捷克": "CZ##########",
}


class VATCalculator:
    """VAT 税务计算器"""

    def __init__(self):
        self.vat_rates = config.vat_rates
        self.deadlines = VAT_DEADLINES

    def calculate_vat(self, df: pd.DataFrame, country: str) -> pd.DataFrame:
        """
        计算指定国家的 VAT

        Args:
            df: 标准化订单数据（需包含该国家的销售数据）
            country: 国家名称

        Returns:
            VAT 计算明细 DataFrame
        """
        rate = self.vat_rates.get(country)
        if rate is None:
            raise ValueError(f"不支持的国家: {country}，支持的国家: {list(self.vat_rates.keys())}")

        if df.empty:
            return pd.DataFrame()

        result = pd.DataFrame()
        result["月份"] = pd.to_datetime(df["交易日期"], errors="coerce").dt.to_period("M").astype(str)
        result["订单数"] = df.groupby(result.index)["订单号"].transform("count")
        result["税前销售额"] = df["订单金额"]
        result["税率"] = rate
        result["应缴VAT"] = result["税前销售额"] * rate
        result["退款金额"] = df["退款金额"]
        result["退款VAT"] = result["退款金额"] * rate
        result["净VAT"] = result["应缴VAT"] - result["退款VAT"]
        result["币种"] = df["币种"]

        return result

    def generate_vat_report(self, df: pd.DataFrame, country: str, period: str = "") -> pd.DataFrame:
        """
        生成 VAT 申报报表（税代格式）

        Args:
            df: 标准化订单数据
            country: 国家
            period: 申报期间，如 "2025-Q1"，留空自动计算当前季度

        Returns:
            VAT 申报报表
        """
        rate = self.vat_rates.get(country, 0)

        if period:
            # 解析期间
            year, quarter = period.split("-Q")
            year, quarter = int(year), int(quarter)
            start_month = (quarter - 1) * 3 + 1
            end_month = start_month + 2
        else:
            today = datetime.now()
            year = today.year
            quarter = (today.month - 1) // 3 + 1
            start_month = (quarter - 1) * 3 + 1
            end_month = start_month + 2

        # 筛选期间数据
        df = df.copy()
        df["交易月份"] = pd.to_datetime(df["交易日期"], errors="coerce").dt.month
        df["交易年份"] = pd.to_datetime(df["交易日期"], errors="coerce").dt.year
        period_df = df[
            (df["交易年份"] == year) &
            (df["交易月份"] >= start_month) &
            (df["交易月份"] <= end_month)
        ]

        # 按月汇总
        monthly_data = []
        for m in range(start_month, end_month + 1):
            month_df = period_df[period_df["交易月份"] == m]
            sales = month_df["订单金额"].sum()
            refunds = month_df["退款金额"].sum()
            monthly_data.append({
                "月份": f"{year}-{m:02d}",
                "订单数": len(month_df),
                "税前销售额": round(sales, 2),
                "退款额": round(refunds, 2),
                "净销售额": round(sales - refunds, 2),
                "VAT税率": f"{rate:.0%}",
                "应缴VAT": round((sales - refunds) * rate, 2),
            })

        report_df = pd.DataFrame(monthly_data)

        # 添加合计行
        if not report_df.empty:
            total_net = report_df["净销售额"].sum()
            total_vat = report_df["应缴VAT"].sum()
            total_orders = report_df["订单数"].sum()
            total_row = pd.DataFrame([{
                "月份": "合计",
                "订单数": total_orders,
                "税前销售额": report_df["税前销售额"].sum(),
                "退款额": report_df["退款额"].sum(),
                "净销售额": round(total_net, 2),
                "VAT税率": f"{rate:.0%}",
                "应缴VAT": round(total_vat, 2),
            }])
            report_df = pd.concat([report_df, total_row], ignore_index=True)

        return report_df

    def get_upcoming_deadlines(self, days_ahead: int = 30) -> pd.DataFrame:
        """
        获取即将到来的 VAT 申报截止日

        Args:
            days_ahead: 提前多少天提醒

        Returns:
            截止日列表
        """
        today = datetime.now()
        deadlines = []

        for country, dl_list in self.deadlines.items():
            for month, day in dl_list:
                # 计算今年的截止日
                deadline = datetime(today.year, month, day)
                # 如果已过，检查下一个
                if deadline < today:
                    deadline = datetime(today.year + 1, month, day)

                days_left = (deadline - today).days
                if 0 <= days_left <= days_ahead:
                    # 确定季度
                    quarter = (month - 1) // 3
                    prev_quarter_end_month = quarter * 3

                    urgency = "🔴 紧急" if days_left <= 3 else ("🟡 注意" if days_left <= 7 else "🟢 正常")

                    deadlines.append({
                        "国家": country,
                        "VAT号格式": VAT_NUMBER_FORMATS.get(country, ""),
                        "申报期间": f"{deadline.year}-Q{quarter + 1}",
                        "截止日期": deadline.strftime("%Y-%m-%d"),
                        "剩余天数": days_left,
                        "紧急程度": urgency,
                        "税率": f"{self.vat_rates.get(country, 0):.0%}",
                    })

        df = pd.DataFrame(deadlines)
        if not df.empty:
            df = df.sort_values("剩余天数").reset_index(drop=True)
        return df

    def export_tax_agent_format(self, report_df: pd.DataFrame, country: str) -> str:
        """
        生成税代需要的格式（CSV 文本）

        Args:
            report_df: VAT 报表
            country: 国家

        Returns:
            CSV 格式文本
        """
        lines = []
        lines.append(f"VAT Return - {country}")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"VAT Registration: {VAT_NUMBER_FORMATS.get(country, 'N/A')}")
        lines.append("")

        # 表头
        cols = ["月份", "订单数", "税前销售额", "退款额", "净销售额", "VAT税率", "应缴VAT"]
        lines.append(",".join(cols))

        for _, row in report_df.iterrows():
            values = [str(row.get(c, "")) for c in cols]
            lines.append(",".join(values))

        lines.append("")
        lines.append("Declaration: 以上数据由跨境电商财务智能体自动生成，请核实后提交。")

        return "\n".join(lines)


def calculate_all_vat(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    计算所有国家的 VAT

    Returns:
        {国家: VAT明细}
    """
    calculator = VATCalculator()
    results = {}

    for country in config.vat_rates:
        country_df = df[df["平台"].str.lower().isin(["amazon", "shopify"])]  # 通常欧洲站销售
        if country_df.empty:
            continue
        try:
            vat_detail = calculator.calculate_vat(country_df, country)
            if not vat_detail.empty:
                results[country] = vat_detail
        except Exception:
            continue

    return results
