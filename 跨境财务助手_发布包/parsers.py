# -*- coding: utf-8 -*-
"""
跨境电商财务智能体 - 多平台数据统一模块
将不同平台的订单/交易数据统一为标准格式
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional
import re


# 统一标准字段
STANDARD_COLUMNS = [
    "平台", "订单号", "平台订单号", "交易日期", "交易时间",
    "商品名称", "SKU", "数量", "单价", "币种",
    "订单金额", "佣金", "手续费", "运费", "税费",
    "实际到账", "退款金额", "买家信息", "物流单号",
    "交易状态", "备注"
]


class PlatformParser:
    """平台数据解析器基类"""

    platform_name = "unknown"
    # 各平台字段到标准字段的映射
    field_mapping = {}

    def parse(self, df: pd.DataFrame) -> pd.DataFrame:
        """将平台数据转换为标准格式"""
        raise NotImplementedError

    def _safe_float(self, val) -> float:
        """安全转换为浮点数"""
        try:
            if pd.isna(val) or val == "" or val is None:
                return 0.0
            return float(str(val).replace(",", "").replace("$", "").replace("€", "").replace("£", "").strip())
        except (ValueError, TypeError):
            return 0.0

    def _safe_int(self, val) -> int:
        """安全转换为整数"""
        try:
            return int(float(str(val).replace(",", "").strip()))
        except (ValueError, TypeError):
            return 0

    def _safe_date(self, val) -> str:
        """安全转换为日期字符串"""
        if pd.isna(val) or val == "":
            return ""
        try:
            if isinstance(val, str):
                # 尝试多种日期格式
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f",
                            "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y",
                            "%Y/%m/%d", "%m-%d-%Y", "%d-%b-%Y",
                            "%b %d, %Y", "%d %b %Y"]:
                    try:
                        return datetime.strptime(val.strip(), fmt).strftime("%Y-%m-%d")
                    except ValueError:
                        continue
            elif isinstance(val, (pd.Timestamp, datetime)):
                return val.strftime("%Y-%m-%d")
            return str(val)
        except Exception:
            return str(val)


class AmazonParser(PlatformParser):
    """Amazon 订单数据解析器"""
    platform_name = "Amazon"

    def parse(self, df: pd.DataFrame) -> pd.DataFrame:
        """解析 Amazon 订单报告（支持多种导出格式）"""
        # 标准化列名（Amazon 导出格式可能有多种）
        col_map = {}
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if "order" in col_lower and "id" in col_lower:
                col_map[col] = "平台订单号"
            elif "order" in col_lower and "date" in col_lower:
                col_map[col] = "交易日期"
            elif "sku" in col_lower:
                col_map[col] = "SKU"
            elif "product" in col_lower and "name" in col_lower:
                col_map[col] = "商品名称"
            elif "item" in col_lower and "price" in col_lower:
                col_map[col] = "单价"
            elif "quantity" in col_lower or "qty" in col_lower:
                col_map[col] = "数量"
            elif "ship" in col_lower and "charge" in col_lower:
                col_map[col] = "运费"
            elif "commission" in col_lower or "referral" in col_lower:
                col_map[col] = "佣金"
            elif "fee" in col_lower and "total" in col_lower:
                col_map[col] = "手续费"
            elif "total" in col_lower and "price" in col_lower:
                col_map[col] = "订单金额"
            elif "buyer" in col_lower or "name" in col_lower:
                col_map[col] = "买家信息"
            elif "track" in col_lower or "tracking" in col_lower:
                col_map[col] = "物流单号"
            elif "status" in col_lower:
                col_map[col] = "交易状态"
            elif "refund" in col_lower:
                col_map[col] = "退款金额"
            elif "currency" in col_lower:
                col_map[col] = "币种"

        df = df.rename(columns=col_map)

        # 确保标准字段存在
        result = pd.DataFrame(columns=STANDARD_COLUMNS)

        # 先赋值数据列
        for col in ["平台订单号", "交易日期", "商品名称", "SKU", "数量",
                     "单价", "运费", "佣金", "手续费", "订单金额",
                     "退款金额", "买家信息", "物流单号", "交易状态", "币种"]:
            if col in df.columns:
                result[col] = df[col].values
            else:
                result[col] = ""

        # 设置平台名（确保长度匹配）
        result["平台"] = [self.platform_name] * len(result)

        # 数值处理
        for col in ["数量"]:
            result[col] = result[col].apply(self._safe_int)
        for col in ["单价", "运费", "佣金", "手续费", "订单金额", "退款金额"]:
            result[col] = result[col].apply(self._safe_float)

        # 计算实际到账
        result["实际到账"] = result["订单金额"] - result["佣金"] - result["手续费"] - result["运费"] - result["退款金额"]

        # 生成统一订单号
        result["订单号"] = "AMZ-" + result["平台订单号"].astype(str)

        # 默认币种
        result["币种"] = result["币种"].replace("", "USD")

        # 日期处理
        result["交易日期"] = result["交易日期"].apply(self._safe_date)

        # 填充默认值
        result["交易时间"] = ""
        result["税费"] = 0.0
        result["备注"] = ""

        return result[STANDARD_COLUMNS]


class EbayParser(PlatformParser):
    """eBay 订单数据解析器"""
    platform_name = "eBay"

    def parse(self, df: pd.DataFrame) -> pd.DataFrame:
        col_map = {}
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if "order" in col_lower and ("id" in col_lower or "number" in col_lower):
                col_map[col] = "平台订单号"
            elif "sale" in col_lower and "date" in col_lower:
                col_map[col] = "交易日期"
            elif "item" in col_lower and ("title" in col_lower or "name" in col_lower):
                col_map[col] = "商品名称"
            elif "sku" in col_lower:
                col_map[col] = "SKU"
            elif "quantity" in col_lower or "qty" in col_lower:
                col_map[col] = "数量"
            elif "price" in col_lower and "sale" in col_lower:
                col_map[col] = "单价"
            elif "shipping" in col_lower:
                col_map[col] = "运费"
            elif "fee" in col_lower:
                col_map[col] = "手续费"
            elif "total" in col_lower and "price" in col_lower:
                col_map[col] = "订单金额"
            elif "buyer" in col_lower:
                col_map[col] = "买家信息"
            elif "tracking" in col_lower:
                col_map[col] = "物流单号"
            elif "status" in col_lower:
                col_map[col] = "交易状态"
            elif "refund" in col_lower:
                col_map[col] = "退款金额"
            elif "currency" in col_lower:
                col_map[col] = "币种"

        df = df.rename(columns=col_map)

        result = pd.DataFrame(columns=STANDARD_COLUMNS)

        for col in ["平台订单号", "交易日期", "商品名称", "SKU", "数量",
                     "单价", "运费", "手续费", "订单金额", "退款金额",
                     "买家信息", "物流单号", "交易状态", "币种"]:
            if col in df.columns:
                result[col] = df[col].values
            else:
                result[col] = ""

        result["平台"] = [self.platform_name] * len(result)

        for col in ["数量"]:
            result[col] = result[col].apply(self._safe_int)
        for col in ["单价", "运费", "手续费", "订单金额", "退款金额"]:
            result[col] = result[col].apply(self._safe_float)

        # eBay 佣金包含在手续费中
        result["佣金"] = result["手续费"] * 0.6  # 估算
        result["实际到账"] = result["订单金额"] - result["手续费"] - result["运费"] - result["退款金额"]

        result["订单号"] = "EBY-" + result["平台订单号"].astype(str)
        result["币种"] = result["币种"].replace("", "USD")
        result["交易日期"] = result["交易日期"].apply(self._safe_date)
        result["交易时间"] = ""
        result["税费"] = 0.0
        result["备注"] = ""

        return result[STANDARD_COLUMNS]


class ShopifyParser(PlatformParser):
    """Shopify 订单数据解析器"""
    platform_name = "Shopify"

    def parse(self, df: pd.DataFrame) -> pd.DataFrame:
        col_map = {}
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if "order" in col_lower and ("id" in col_lower or "name" in col_lower or "number" in col_lower):
                col_map[col] = "平台订单号"
            elif "created" in col_lower and "at" in col_lower:
                col_map[col] = "交易日期"
            elif "title" in col_lower or ("lineitem" in col_lower and "name" in col_lower):
                col_map[col] = "商品名称"
            elif "sku" in col_lower:
                col_map[col] = "SKU"
            elif "quantity" in col_lower:
                col_map[col] = "数量"
            elif "price" in col_lower:
                col_map[col] = "单价"
            elif "shipping" in col_lower:
                col_map[col] = "运费"
            elif "total" in col_lower and ("shop" in col_lower or "price" in col_lower):
                col_map[col] = "订单金额"
            elif "gateway" in col_lower and "fee" in col_lower:
                col_map[col] = "手续费"
            elif "customer" in col_lower:
                col_map[col] = "买家信息"
            elif "tracking" in col_lower:
                col_map[col] = "物流单号"
            elif "financial" in col_lower and "status" in col_lower:
                col_map[col] = "交易状态"
            elif "refund" in col_lower:
                col_map[col] = "退款金额"
            elif "currency" in col_lower:
                col_map[col] = "币种"

        df = df.rename(columns=col_map)

        result = pd.DataFrame(columns=STANDARD_COLUMNS)

        for col in ["平台订单号", "交易日期", "商品名称", "SKU", "数量",
                     "单价", "运费", "手续费", "订单金额", "退款金额",
                     "买家信息", "物流单号", "交易状态", "币种"]:
            if col in df.columns:
                result[col] = df[col].values
            else:
                result[col] = ""

        result["平台"] = [self.platform_name] * len(result)

        for col in ["数量"]:
            result[col] = result[col].apply(self._safe_int)
        for col in ["单价", "运费", "手续费", "订单金额", "退款金额"]:
            result[col] = result[col].apply(self._safe_float)

        result["佣金"] = 0.0  # Shopify 无平台佣金
        result["实际到账"] = result["订单金额"] - result["手续费"] - result["运费"] - result["退款金额"]

        result["订单号"] = "SHF-" + result["平台订单号"].astype(str)
        result["币种"] = result["币种"].replace("", "USD")
        result["交易日期"] = result["交易日期"].apply(self._safe_date)
        result["交易时间"] = ""
        result["税费"] = 0.0
        result["备注"] = ""

        return result[STANDARD_COLUMNS]


class ShopeeParser(PlatformParser):
    """Shopee 订单数据解析器"""
    platform_name = "Shopee"

    def parse(self, df: pd.DataFrame) -> pd.DataFrame:
        col_map = {}
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if "order" in col_lower and ("no" in col_lower or "id" in col_lower or "sn" in col_lower):
                col_map[col] = "平台订单号"
            elif "order" in col_lower and "time" in col_lower:
                col_map[col] = "交易日期"
            elif "product" in col_lower and "name" in col_lower:
                col_map[col] = "商品名称"
            elif "sku" in col_lower:
                col_map[col] = "SKU"
            elif "quantity" in col_lower or "qty" in col_lower:
                col_map[col] = "数量"
            elif "unit" in col_lower and "price" in col_lower:
                col_map[col] = "单价"
            elif "shipping" in col_lower and "fee" in col_lower:
                col_map[col] = "运费"
            elif "commission" in col_lower:
                col_map[col] = "佣金"
            elif "service" in col_lower and "fee" in col_lower:
                col_map[col] = "手续费"
            elif "total" in col_lower and "amount" in col_lower:
                col_map[col] = "订单金额"
            elif "refund" in col_lower:
                col_map[col] = "退款金额"
            elif "buyer" in col_lower:
                col_map[col] = "买家信息"
            elif "tracking" in col_lower:
                col_map[col] = "物流单号"
            elif "status" in col_lower:
                col_map[col] = "交易状态"
            elif "currency" in col_lower:
                col_map[col] = "币种"

        df = df.rename(columns=col_map)

        result = pd.DataFrame(columns=STANDARD_COLUMNS)

        for col in ["平台订单号", "交易日期", "商品名称", "SKU", "数量",
                     "单价", "运费", "佣金", "手续费", "订单金额", "退款金额",
                     "买家信息", "物流单号", "交易状态", "币种"]:
            if col in df.columns:
                result[col] = df[col].values
            else:
                result[col] = ""

        result["平台"] = [self.platform_name] * len(result)

        for col in ["数量"]:
            result[col] = result[col].apply(self._safe_int)
        for col in ["单价", "运费", "佣金", "手续费", "订单金额", "退款金额"]:
            result[col] = result[col].apply(self._safe_float)

        result["实际到账"] = result["订单金额"] - result["佣金"] - result["手续费"] - result["运费"] - result["退款金额"]

        result["订单号"] = "SHP-" + result["平台订单号"].astype(str)
        result["币种"] = result["币种"].replace("", "SGD")
        result["交易日期"] = result["交易日期"].apply(self._safe_date)
        result["交易时间"] = ""
        result["税费"] = 0.0
        result["备注"] = ""

        return result[STANDARD_COLUMNS]


class GenericParser(PlatformParser):
    """通用解析器 - 用于未知格式"""
    platform_name = "通用"

    def parse(self, df: pd.DataFrame) -> pd.DataFrame:
        """尝试智能匹配字段"""
        result = pd.DataFrame(columns=STANDARD_COLUMNS)

        # 尝试智能匹配
        col_map = {}
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if any(k in col_lower for k in ["order", "订单"]):
                if any(k in col_lower for k in ["id", "号", "no", "number"]):
                    col_map[col] = "平台订单号"
                elif any(k in col_lower for k in ["date", "日期", "time"]):
                    col_map[col] = "交易日期"
            elif any(k in col_lower for k in ["product", "商品", "item", "title"]):
                col_map[col] = "商品名称"
            elif "sku" in col_lower:
                col_map[col] = "SKU"
            elif any(k in col_lower for k in ["qty", "quantity", "数量"]):
                col_map[col] = "数量"
            elif any(k in col_lower for k in ["price", "价格", "金额"]):
                col_map[col] = "单价"
            elif any(k in col_lower for k in ["shipping", "运费", "邮费"]):
                col_map[col] = "运费"
            elif any(k in col_lower for k in ["commission", "佣金", "referral"]):
                col_map[col] = "佣金"
            elif any(k in col_lower for k in ["fee", "手续费", "费用"]):
                col_map[col] = "手续费"
            elif any(k in col_lower for k in ["total", "总计", "总额"]):
                col_map[col] = "订单金额"
            elif any(k in col_lower for k in ["refund", "退款"]):
                col_map[col] = "退款金额"
            elif any(k in col_lower for k in ["buyer", "买家", "customer"]):
                col_map[col] = "买家信息"
            elif any(k in col_lower for k in ["track", "物流", "运单"]):
                col_map[col] = "物流单号"
            elif any(k in col_lower for k in ["status", "状态"]):
                col_map[col] = "交易状态"
            elif any(k in col_lower for k in ["currency", "币种", "currency"]):
                col_map[col] = "币种"

        df = df.rename(columns=col_map)

        for col in ["平台订单号", "交易日期", "商品名称", "SKU", "数量",
                     "单价", "运费", "佣金", "手续费", "订单金额", "退款金额",
                     "买家信息", "物流单号", "交易状态", "币种"]:
            if col in df.columns:
                result[col] = df[col].values
            else:
                result[col] = ""

        result["平台"] = [self.platform_name] * len(result)

        for col in ["数量"]:
            result[col] = result[col].apply(self._safe_int)
        for col in ["单价", "运费", "佣金", "手续费", "订单金额", "退款金额"]:
            result[col] = result[col].apply(self._safe_float)

        result["实际到账"] = result["订单金额"] - result["佣金"] - result["手续费"] - result["运费"] - result["退款金额"]
        result["订单号"] = "GEN-" + result["平台订单号"].astype(str)
        result["币种"] = result["币种"].replace("", "USD")
        result["交易日期"] = result["交易日期"].apply(self._safe_date)
        result["交易时间"] = ""
        result["税费"] = 0.0
        result["备注"] = ""

        return result[STANDARD_COLUMNS]


# 解析器注册表
PARSERS = {
    "amazon": AmazonParser,
    "ebay": EbayParser,
    "walmart": AmazonParser,  # Walmart 格式类似 Amazon
    "shopify": ShopifyParser,
    "aliexpress": GenericParser,  # 速卖通暂用通用解析
    "shopee": ShopeeParser,
}


def detect_platform(df: pd.DataFrame, filename: str = "") -> str:
    """根据文件名和列名自动检测平台"""
    filename_lower = filename.lower()

    # 先按文件名判断
    if "amazon" in filename_lower:
        return "amazon"
    elif "ebay" in filename_lower:
        return "ebay"
    elif "walmart" in filename_lower:
        return "walmart"
    elif "shopify" in filename_lower:
        return "shopify"
    elif "shopee" in filename_lower:
        return "shopee"
    elif "aliexpress" in filename_lower or "速卖通" in filename_lower:
        return "aliexpress"

    # 按列名特征判断
    cols_str = " ".join(str(c).lower() for c in df.columns)
    if "referral fee" in cols_str or "fba fee" in cols_str:
        return "amazon"
    elif "final value fee" in cols_str:
        return "ebay"
    elif "shop money" in cols_str or "shopify payments" in cols_str:
        return "shopify"
    elif "shopee" in cols_str:
        return "shopee"

    return "unknown"


def parse_file(file_path: str, platform: str = "auto") -> pd.DataFrame:
    """
    解析上传的文件，返回标准化数据

    Args:
        file_path: 文件路径
        platform: 平台名称，"auto" 为自动检测

    Returns:
        标准化后的 DataFrame
    """
    # 读取文件
    ext = file_path.lower().split(".")[-1]
    if ext in ["csv"]:
        df = pd.read_csv(file_path, encoding="utf-8-sig", on_bad_lines="skip")
    elif ext in ["xlsx", "xls"]:
        df = pd.read_excel(file_path, engine="openpyxl")
    else:
        raise ValueError(f"不支持的文件格式: {ext}，请使用 CSV 或 Excel 格式")

    if df.empty:
        raise ValueError("文件为空，没有数据可解析")

    # 自动检测平台
    if platform == "auto":
        platform = detect_platform(df, file_path)

    # 选择解析器
    parser_class = PARSERS.get(platform, GenericParser)
    parser = parser_class()

    # 解析
    result = parser.parse(df)

    # 如果检测为 unknown，更新平台名
    if platform == "unknown":
        result["平台"] = "未知平台"

    return result


def merge_multi_platform(dfs: list) -> pd.DataFrame:
    """合并多个平台的数据"""
    if not dfs:
        return pd.DataFrame(columns=STANDARD_COLUMNS)
    return pd.concat(dfs, ignore_index=True)
