# -*- coding: utf-8 -*-
"""
跨境电商财务智能体 - 多平台数据统一模块
将不同平台的订单/交易数据统一为标准格式
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, List
import re


# 统一标准字段
STANDARD_COLUMNS = [
    "平台", "订单号", "平台订单号", "交易日期", "交易时间",
    "商品名称", "SKU", "数量", "单价", "币种",
    "订单金额", "佣金", "手续费", "运费", "税费",
    "实际到账", "退款金额", "买家信息", "物流单号",
    "交易状态", "备注"
]

# 扩展列 - 解析器可能产生的额外列
EXTRA_COLUMNS = [
    "商品ID", "费用项", "商品描述", "资金渠道", "渠道账号",
    "店铺优惠", "平台补贴", "收货国家", "物流方式",
    "负责人", "支付方式", "供货价", "EANcode", "商品编码",
    "收货地址", "联系电话", "联系邮件", "邮编", "城市",
    "州省", "税号", "发货时间", "确认收货时间", "订单业务模式",
    "定制信息", "订单备注",
]


# ============================================================================
# 增强的列名映射 - 支持真实文件列名
# ============================================================================

# 文件1: 收支流水 - 列名映射
TRANSACTION_COLUMN_MAP = {
    # 标准列名 -> 可能的原始列名列表
    "交易日期": ["结算时间", "交易日期", "日期", "时间", "Date", "date", "Time", "time"],
    "收支类型": ["收支类型", "类型", "Type", "type"],
    "费用项": ["费用项", "费用类型", "Fee Type", "fee_type"],
    "商品描述": ["商品描述", "描述", "Description", "description"],
    "商品ID": ["商品ID", "商品 Id", "商品 id", "Product ID", "product_id"],
    "SKU": ["Sku ID", "Sku id", "sku id", "Sku编码", "sku编码", "SKU", "sku", "Sku"],
    "商品信息": ["商品信息", "商品名称", "Product Info", "product_info", "Product Name"],
    "订单金额": ["变动金额", "金额", "Amount", "amount", "收入", "支出"],
    "币种": ["币种", "货币", "Currency", "currency"],
    "平台订单号": ["订单号", "业务单号", "渠道流水单号", "平台流水单号", "Order No", "order_no", "Order ID", "order_id"],
    "资金渠道": ["资金渠道", "渠道", "Channel", "channel"],
    "渠道账号": ["渠道账号", "账号", "Account", "account"],
    "备注": ["备注", "说明", "Note", "note", "Remark", "remark"],
    "操作": ["操作", "Action", "action"],
}

# 文件2: 批量订单 - 列名映射
ORDER_COLUMN_MAP = {
    "平台订单号": ["订单号", "Order No", "order_no", "Order ID", "order_id"],
    "交易状态": ["订单状态", "状态", "Status", "status"],
    "负责人": ["负责人（业务员）", "负责人", "业务员", "Owner", "owner"],
    "买家信息": ["买家名称", "买家", "Buyer", "buyer", "Customer", "customer", "收件人名称"],
    "交易日期": ["下单时间", "付款时间", "Order Time", "order_time", "Date", "date", "Time", "time"],
    "支付方式": ["支付方式", "Payment", "payment"],
    "供货价": ["供货价", "成本价", "Cost Price", "cost_price"],
    "订单金额": ["订单金额", "产品总金额", "总金额", "Total Amount", "total_amount", "Total", "total"],
    "运费": ["物流费用", "运费", "Shipping Fee", "shipping_fee", "Shipping", "shipping"],
    "税费": ["预计增值税", "DDP关税", "增值税", "关税", "Tax", "tax"],
    "店铺优惠": ["店铺优惠", "优惠", "Discount", "discount"],
    "平台补贴": ["平台补贴", "补贴", "Subsidy", "subsidy"],
    "商品ID": ["商品 ID", "商品 Id", "商品 id", "Product ID", "product_id"],
    "商品名称": ["商品信息", "商品名称", "Product Info", "product_info", "Product Name", "product_name"],
    "商品编码": ["商品编码", "EANcode", "EAN", "ean", "Code", "code"],
    "订单备注": ["订单备注", "备注", "Note", "note"],
    "收货地址": ["完整收货地址", "地址", "Address", "address"],
    "联系电话": ["联系电话", "手机", "Phone", "phone", "Mobile", "mobile"],
    "联系邮件": ["联系邮件", "邮箱", "Email", "email"],
    "邮编": ["邮编", "Postal Code", "postal_code", "Zip", "zip"],
    "城市": ["城市", "扩展城市（德/意/波/墨为真实的城市）", "City", "city"],
    "州省": ["州/省", "省", "State", "state", "Province", "province"],
    "收货国家": ["收货国家", "国家", "Country", "country"],
    "税号": ["税号", "Tax ID", "tax_id", "VAT", "vat"],
    "物流方式": ["买家选择物流", "物流", "Shipping Method", "shipping_method"],
    "物流单号": ["实际发货单号", "发货单号", "Tracking No", "tracking_no", "Tracking", "tracking"],
    "发货时间": ["发货时间", "Ship Time", "ship_time"],
    "确认收货时间": ["确认收货时间", "Receipt Time", "receipt_time"],
    "订单业务模式": ["订单业务模式", "业务模式", "Business Model", "business_model"],
    "定制信息": ["定制信息", "Custom Info", "custom_info"],
}

# 合并所有列名映射（用于通用解析器）
UNIFIED_COLUMN_MAP = {}
for d in [TRANSACTION_COLUMN_MAP, ORDER_COLUMN_MAP]:
    for std_col, aliases in d.items():
        if std_col not in UNIFIED_COLUMN_MAP:
            UNIFIED_COLUMN_MAP[std_col] = []
        UNIFIED_COLUMN_MAP[std_col].extend(aliases)


# ============================================================================
# 平台特征模式 - 用于智能检测平台类型
# ============================================================================
PLATFORM_PATTERNS = {
    "amazon": {
        "filename_keywords": ["amazon", "fba", "seller central"],
        "column_keywords": ["referral fee", "fba fee", "order id", "asin", "sku", "quantity", "product sales"],
        "required_columns": ["order id", "sku"],
    },
    "ebay": {
        "filename_keywords": ["ebay", "paypal"],
        "column_keywords": ["final value fee", "paypal fee", "item id", "buyer username", "sale date"],
        "required_columns": ["item id", "sale date"],
    },
    "shopify": {
        "filename_keywords": ["shopify", "orders"],
        "column_keywords": ["shopify payments", "shop money", "lineitem", "order name", "financial status"],
        "required_columns": ["order name", "financial status"],
    },
    "shopee": {
        "filename_keywords": ["shopee"],
        "column_keywords": ["shopee", "order sn", "product name", "buyer username", "shipping fee"],
        "required_columns": ["order sn", "product name"],
    },
    "aliexpress": {
        "filename_keywords": ["aliexpress", "速卖通", "alibaba"],
        "column_keywords": ["订单号", "订单状态", "买家名称", "物流费用", "供货价", "商品信息", "收货国家"],
        "required_columns": ["订单号"],
    },
    "transaction": {
        "filename_keywords": ["收支", "流水", "transaction", "流水账", "结算"],
        "column_keywords": ["结算时间", "收支类型", "费用项", "变动金额", "资金渠道", "平台流水单号"],
        "required_columns": ["结算时间", "变动金额"],
    },
    "walmart": {
        "filename_keywords": ["walmart"],
        "column_keywords": ["purchase order", "partner name", "commission", "shipping"],
        "required_columns": ["purchase order"],
    },
    "temu": {
        "filename_keywords": ["temu"],
        "column_keywords": ["temu", "订单号", "商品名称", "结算金额"],
        "required_columns": ["订单号"],
    },
    "tiktok": {
        "filename_keywords": ["tiktok"],
        "column_keywords": ["tiktok", "order id", "product name", "settlement"],
        "required_columns": ["order id"],
    },
}


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
            return float(str(val).replace(",", "").replace("$", "").replace("€", "").replace("£", "").replace("US ", "").replace("CNY", "").replace("USD", "").strip())
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
                            "%b %d, %Y", "%d %b %Y",
                            "%m/%d/%Y %H:%M", "%Y-%m-%d %H:%M"]:
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
        for col in STANDARD_COLUMNS:
            if col in df.columns:
                result[col] = df[col].values
            else:
                result[col] = ""

        # 额外列也保留
        for col in EXTRA_COLUMNS:
            if col in df.columns:
                result[col] = df[col].values

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

        return result[STANDARD_COLUMNS + [c for c in EXTRA_COLUMNS if c in result.columns]]


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

        for col in STANDARD_COLUMNS:
            if col in df.columns:
                result[col] = df[col].values
            else:
                result[col] = ""

        # 额外列也保留
        for col in EXTRA_COLUMNS:
            if col in df.columns:
                result[col] = df[col].values

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

        return result[STANDARD_COLUMNS + [c for c in EXTRA_COLUMNS if c in result.columns]]


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

        for col in STANDARD_COLUMNS:
            if col in df.columns:
                result[col] = df[col].values
            else:
                result[col] = ""

        # 额外列也保留
        for col in EXTRA_COLUMNS:
            if col in df.columns:
                result[col] = df[col].values

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

        return result[STANDARD_COLUMNS + [c for c in EXTRA_COLUMNS if c in result.columns]]


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

        for col in STANDARD_COLUMNS:
            if col in df.columns:
                result[col] = df[col].values
            else:
                result[col] = ""

        # 额外列也保留
        for col in EXTRA_COLUMNS:
            if col in df.columns:
                result[col] = df[col].values

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

        return result[STANDARD_COLUMNS + [c for c in EXTRA_COLUMNS if c in result.columns]]


class AliExpressParser(PlatformParser):
    """速卖通(AliExpress) 订单数据解析器"""
    platform_name = "AliExpress"

    def parse(self, df: pd.DataFrame) -> pd.DataFrame:
        """解析速卖通批量订单导出文件"""
        col_map = {}
        mapped_targets = set()
        for col in df.columns:
            col_lower = str(col).lower().strip()
            col_str = str(col).strip()

            # 订单号相关
            if col_str in ["订单号"] and "平台订单号" not in mapped_targets:
                col_map[col] = "平台订单号"
                mapped_targets.add("平台订单号")
            # 日期相关 - 优先用付款时间
            elif col_str == "付款时间" and "交易日期" not in mapped_targets:
                col_map[col] = "交易日期"
                mapped_targets.add("交易日期")
            elif col_str == "下单时间" and "交易日期" not in mapped_targets:
                col_map[col] = "交易日期"
                mapped_targets.add("交易日期")
            # 商品信息
            elif col_str in ["商品信息", "商品名称"] and "商品名称" not in mapped_targets:
                col_map[col] = "商品名称"
                mapped_targets.add("商品名称")
            # 商品ID
            elif col_str in ["商品 ID", "商品 Id", "商品 id"] and "商品ID" not in mapped_targets:
                col_map[col] = "商品ID"
                mapped_targets.add("商品ID")
            # SKU
            elif "sku" in col_lower and "SKU" not in mapped_targets:
                col_map[col] = "SKU"
                mapped_targets.add("SKU")
            # 数量
            elif ("quantity" in col_lower or "qty" in col_lower or "数量" in col_str) and "数量" not in mapped_targets:
                col_map[col] = "数量"
                mapped_targets.add("数量")
            # 单价/供货价
            elif col_str in ["供货价"] and "单价" not in mapped_targets:
                col_map[col] = "单价"
                mapped_targets.add("单价")
            # 订单金额 - 优先用"产品总金额"（因为批量订单文件中有两个"订单金额"列，产品总金额更准确）
            elif col_str == "产品总金额" and "订单金额" not in mapped_targets:
                col_map[col] = "订单金额"
                mapped_targets.add("订单金额")
            elif col_str == "订单金额" and "订单金额" not in mapped_targets:
                col_map[col] = "订单金额"
                mapped_targets.add("订单金额")
            # 运费/物流费用
            elif col_str in ["物流费用", "运费"] and "运费" not in mapped_targets:
                col_map[col] = "运费"
                mapped_targets.add("运费")
            # 税费
            elif col_str in ["预计增值税", "DDP关税"] and "税费" not in mapped_targets:
                col_map[col] = "税费"
                mapped_targets.add("税费")
            # 优惠/折扣
            elif col_str in ["店铺优惠", "托管商家折扣"] and "店铺优惠" not in mapped_targets:
                col_map[col] = "店铺优惠"
                mapped_targets.add("店铺优惠")
            # 平台补贴
            elif col_str in ["平台补贴"] and "平台补贴" not in mapped_targets:
                col_map[col] = "平台补贴"
                mapped_targets.add("平台补贴")
            # 买家信息
            elif col_str in ["买家名称", "收件人名称"] and "买家信息" not in mapped_targets:
                col_map[col] = "买家信息"
                mapped_targets.add("买家信息")
            # 物流单号
            elif col_str in ["实际发货单号"] and "物流单号" not in mapped_targets:
                col_map[col] = "物流单号"
                mapped_targets.add("物流单号")
            # 交易状态
            elif col_str in ["订单状态"] and "交易状态" not in mapped_targets:
                col_map[col] = "交易状态"
                mapped_targets.add("交易状态")
            # 币种
            elif ("currency" in col_lower or "币种" in col_str) and "币种" not in mapped_targets:
                col_map[col] = "币种"
                mapped_targets.add("币种")
            # 备注
            elif col_str in ["订单备注"] and "备注" not in mapped_targets:
                col_map[col] = "备注"
                mapped_targets.add("备注")
            # 收货国家
            elif col_str in ["收货国家"] and "收货国家" not in mapped_targets:
                col_map[col] = "收货国家"
                mapped_targets.add("收货国家")
            # 物流方式
            elif col_str in ["买家选择物流"] and "物流方式" not in mapped_targets:
                col_map[col] = "物流方式"
                mapped_targets.add("物流方式")
            # 负责人
            elif col_str == "负责人（业务员）" and "负责人" not in mapped_targets:
                col_map[col] = "负责人"
                mapped_targets.add("负责人")
            # 支付方式
            elif col_str == "支付方式" and "支付方式" not in mapped_targets:
                col_map[col] = "支付方式"
                mapped_targets.add("支付方式")
            # EANcode
            elif col_str == "EANcode" and "EANcode" not in mapped_targets:
                col_map[col] = "EANcode"
                mapped_targets.add("EANcode")
            # 商品编码
            elif col_str == "商品编码" and "商品编码" not in mapped_targets:
                col_map[col] = "商品编码"
                mapped_targets.add("商品编码")
            # 收货地址
            elif col_str == "完整收货地址" and "收货地址" not in mapped_targets:
                col_map[col] = "收货地址"
                mapped_targets.add("收货地址")
            # 联系电话
            elif col_str == "联系电话" and "联系电话" not in mapped_targets:
                col_map[col] = "联系电话"
                mapped_targets.add("联系电话")
            # 联系邮件
            elif col_str == "联系邮件" and "联系邮件" not in mapped_targets:
                col_map[col] = "联系邮件"
                mapped_targets.add("联系邮件")
            # 邮编
            elif col_str == "邮编" and "邮编" not in mapped_targets:
                col_map[col] = "邮编"
                mapped_targets.add("邮编")
            # 城市 - 优先用"扩展城市"
            elif col_str == "扩展城市（德/意/波/墨为真实的城市）" and "城市" not in mapped_targets:
                col_map[col] = "城市"
                mapped_targets.add("城市")
            elif col_str == "城市" and "城市" not in mapped_targets:
                col_map[col] = "城市"
                mapped_targets.add("城市")
            # 州省
            elif col_str == "州/省" and "州省" not in mapped_targets:
                col_map[col] = "州省"
                mapped_targets.add("州省")
            # 税号
            elif col_str == "税号" and "税号" not in mapped_targets:
                col_map[col] = "税号"
                mapped_targets.add("税号")
            # 发货时间
            elif col_str == "发货时间" and "发货时间" not in mapped_targets:
                col_map[col] = "发货时间"
                mapped_targets.add("发货时间")
            # 确认收货时间
            elif col_str == "确认收货时间" and "确认收货时间" not in mapped_targets:
                col_map[col] = "确认收货时间"
                mapped_targets.add("确认收货时间")
            # 订单业务模式
            elif col_str == "订单业务模式" and "订单业务模式" not in mapped_targets:
                col_map[col] = "订单业务模式"
                mapped_targets.add("订单业务模式")
            # 定制信息
            elif col_str.strip() == "定制信息" and "定制信息" not in mapped_targets:
                col_map[col] = "定制信息"
                mapped_targets.add("定制信息")

        df = df.rename(columns=col_map)

        # 处理重复列名：如果有多个原始列映射到同一个目标列，保留第一个
        if len(df.columns) != len(set(df.columns)):
            seen = set()
            keep_idx = []
            for i, c in enumerate(df.columns):
                if c not in seen:
                    keep_idx.append(i)
                    seen.add(c)
            df = df.iloc[:, keep_idx]

        result = pd.DataFrame(columns=STANDARD_COLUMNS)

        for col in STANDARD_COLUMNS:
            if col in df.columns:
                result[col] = df[col].values
            else:
                result[col] = ""

        # 额外列也保留
        for col in EXTRA_COLUMNS:
            if col in df.columns:
                result[col] = df[col].values

        result["平台"] = [self.platform_name] * len(result)

        for col in ["数量"]:
            result[col] = result[col].apply(self._safe_int)
        for col in ["单价", "运费", "订单金额", "税费", "店铺优惠", "平台补贴"]:
            result[col] = result[col].apply(self._safe_float)

        # 速卖通佣金估算（约5-8%）
        result["佣金"] = result["订单金额"] * 0.06
        result["手续费"] = result["订单金额"] * 0.02  # 支付手续费估算
        result["实际到账"] = result["订单金额"] - result["佣金"] - result["手续费"] - result["运费"] - result["税费"] + result["平台补贴"]

        result["订单号"] = "AE-" + result["平台订单号"].astype(str)
        result["币种"] = result["币种"].replace("", "USD")
        result["交易日期"] = result["交易日期"].apply(self._safe_date)
        result["交易时间"] = ""

        return result[STANDARD_COLUMNS + [c for c in EXTRA_COLUMNS if c in result.columns]]


class TransactionParser(PlatformParser):
    """收支流水解析器 - 用于交易流水文件"""
    platform_name = "交易流水"

    def parse(self, df: pd.DataFrame) -> pd.DataFrame:
        """解析收支流水文件"""
        col_map = {}
        mapped_targets = set()
        for col in df.columns:
            col_str = str(col).strip()
            col_lower = col_str.lower()

            if (col_str == "结算时间") and "交易日期" not in mapped_targets:
                col_map[col] = "交易日期"
                mapped_targets.add("交易日期")
            elif col_str == "收支类型" and "收支类型" not in mapped_targets:
                col_map[col] = "收支类型"
                mapped_targets.add("收支类型")
            elif col_str == "费用项" and "费用项" not in mapped_targets:
                col_map[col] = "费用项"
                mapped_targets.add("费用项")
            elif col_str == "商品描述" and "商品描述" not in mapped_targets:
                col_map[col] = "商品描述"
                mapped_targets.add("商品描述")
            elif col_str in ["商品ID", "商品 Id"] and "商品ID" not in mapped_targets:
                col_map[col] = "商品ID"
                mapped_targets.add("商品ID")
            elif col_str in ["Sku ID", "Sku id", "Sku编码"] and "SKU" not in mapped_targets:
                col_map[col] = "SKU"
                mapped_targets.add("SKU")
            elif col_str == "商品信息" and "商品名称" not in mapped_targets:
                col_map[col] = "商品名称"
                mapped_targets.add("商品名称")
            elif col_str == "变动金额" and "订单金额" not in mapped_targets:
                col_map[col] = "订单金额"
                mapped_targets.add("订单金额")
            elif col_str == "币种" and "币种" not in mapped_targets:
                col_map[col] = "币种"
                mapped_targets.add("币种")
            elif col_str == "订单号" and "平台订单号" not in mapped_targets:
                col_map[col] = "平台订单号"
                mapped_targets.add("平台订单号")
            elif col_str == "资金渠道" and "资金渠道" not in mapped_targets:
                col_map[col] = "资金渠道"
                mapped_targets.add("资金渠道")
            elif col_str == "渠道账号" and "渠道账号" not in mapped_targets:
                col_map[col] = "渠道账号"
                mapped_targets.add("渠道账号")
            elif col_str == "备注" and "备注" not in mapped_targets:
                col_map[col] = "备注"
                mapped_targets.add("备注")

        df = df.rename(columns=col_map)

        # 处理重复列名：如果有多个原始列映射到同一个目标列，保留第一个
        if len(df.columns) != len(set(df.columns)):
            seen = set()
            keep_idx = []
            for i, c in enumerate(df.columns):
                if c not in seen:
                    keep_idx.append(i)
                    seen.add(c)
            df = df.iloc[:, keep_idx]

        result = pd.DataFrame(columns=STANDARD_COLUMNS)

        for col in STANDARD_COLUMNS:
            if col in df.columns:
                result[col] = df[col].values
            else:
                result[col] = ""

        # 额外列也保留
        for col in EXTRA_COLUMNS:
            if col in df.columns:
                result[col] = df[col].values

        result["平台"] = [self.platform_name] * len(result)

        # 处理变动金额（可能带负号表示支出）
        result["订单金额"] = result["订单金额"].apply(self._safe_float)

        # 收支类型判断
        if "收支类型" in df.columns:
            result["备注"] = result["备注"].astype(str) + " | 类型:" + df["收支类型"].astype(str)

        # 流水文件没有明确的佣金/手续费拆分，设为0
        result["佣金"] = 0.0
        result["手续费"] = 0.0
        result["运费"] = 0.0
        result["税费"] = 0.0
        result["退款金额"] = 0.0
        result["实际到账"] = result["订单金额"]
        result["数量"] = 1
        result["单价"] = result["订单金额"]
        result["订单号"] = "TXN-" + result["平台订单号"].astype(str).replace("nan", "")
        result["币种"] = result["币种"].replace("", "USD")
        result["交易日期"] = result["交易日期"].apply(self._safe_date)
        result["交易时间"] = ""
        result["买家信息"] = ""
        result["物流单号"] = ""
        result["交易状态"] = "完成"

        return result[STANDARD_COLUMNS + [c for c in EXTRA_COLUMNS if c in result.columns]]


class GenericParser(PlatformParser):
    """通用解析器 - 用于未知格式"""
    platform_name = "通用"

    def parse(self, df: pd.DataFrame) -> pd.DataFrame:
        """尝试智能匹配字段"""
        result = pd.DataFrame(columns=STANDARD_COLUMNS)

        # 使用统一的列名映射
        col_map = normalize_columns(df.columns)
        df = df.rename(columns=col_map)

        for col in STANDARD_COLUMNS:
            if col in df.columns:
                result[col] = df[col].values
            else:
                result[col] = ""

        # 额外列也保留
        for col in EXTRA_COLUMNS:
            if col in df.columns:
                result[col] = df[col].values

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

        return result[STANDARD_COLUMNS + [c for c in EXTRA_COLUMNS if c in result.columns]]


# ============================================================================
# 增强的列名标准化函数
# ============================================================================

def normalize_columns(columns) -> Dict[str, str]:
    """
    将各种列名统一映射到标准列名。

    Args:
        columns: 原始列名列表

    Returns:
        dict: {原始列名: 标准列名} 的映射字典
    """
    col_map = {}
    used_std = set()

    for col in columns:
        col_str = str(col).strip()
        col_lower = col_str.lower()
        matched = False

        for std_col, aliases in UNIFIED_COLUMN_MAP.items():
            if std_col in used_std:
                continue
            for alias in aliases:
                # 精确匹配或包含关系匹配
                if col_str == alias or col_lower == alias.lower():
                    col_map[col] = std_col
                    used_std.add(std_col)
                    matched = True
                    break
                # 模糊匹配：原始列名包含别名
                if alias.lower() in col_lower and len(alias) >= 3:
                    col_map[col] = std_col
                    used_std.add(std_col)
                    matched = True
                    break
            if matched:
                break

    return col_map


# ============================================================================
# 增强的平台检测函数
# ============================================================================

def detect_platform_enhanced(df: pd.DataFrame, filename: str = "") -> str:
    """
    更智能地检测平台类型。

    基于文件名关键词和列名特征进行多维度匹配，返回最可能的平台类型。

    Args:
        df: 数据DataFrame
        filename: 文件名

    Returns:
        str: 检测到的平台类型标识
    """
    filename_lower = filename.lower()
    cols_lower = [str(c).lower().strip() for c in df.columns]
    cols_str = " ".join(cols_lower)

    scores = {}

    for platform, pattern in PLATFORM_PATTERNS.items():
        score = 0

        # 文件名匹配
        for kw in pattern.get("filename_keywords", []):
            if kw.lower() in filename_lower:
                score += 3

        # 列名关键词匹配
        for kw in pattern.get("column_keywords", []):
            if kw.lower() in cols_str:
                score += 2

        # 必需列匹配
        required = pattern.get("required_columns", [])
        matched_required = sum(1 for r in required if any(r.lower() in c for c in cols_lower))
        if required:
            score += (matched_required / len(required)) * 5

        if score > 0:
            scores[platform] = score

    if scores:
        # 返回得分最高的平台
        best_platform = max(scores, key=scores.get)
        best_score = scores[best_platform]

        # 如果最高分与次高分差距太小，返回unknown
        if len(scores) > 1:
            second_best = sorted(scores.values(), reverse=True)[1]
            if best_score - second_best < 2:
                return "unknown"

        return best_platform

    return "unknown"


# 保留旧函数以兼容
def detect_platform(df: pd.DataFrame, filename: str = "") -> str:
    """根据文件名和列名自动检测平台（兼容旧版）"""
    return detect_platform_enhanced(df, filename)


# ============================================================================
# 解析器注册表
# ============================================================================
PARSERS = {
    "amazon": AmazonParser,
    "ebay": EbayParser,
    "walmart": AmazonParser,  # Walmart 格式类似 Amazon
    "shopify": ShopifyParser,
    "aliexpress": AliExpressParser,
    "shopee": ShopeeParser,
    "transaction": TransactionParser,
    "temu": GenericParser,
    "tiktok": GenericParser,
    "unknown": GenericParser,
}


# ============================================================================
# 增强的文件解析函数
# ============================================================================

def parse_file(file_path: str, platform: str = "auto") -> pd.DataFrame:
    """
    解析上传的文件，返回标准化数据（增强版）

    Args:
        file_path: 文件路径
        platform: 平台名称，"auto" 为自动检测

    Returns:
        标准化后的 DataFrame

    Raises:
        ValueError: 文件格式不支持或文件为空时抛出，附带明确的错误信息
    """
    # 读取文件
    ext = file_path.lower().split(".")[-1]
    if ext in ["csv"]:
        try:
            df = pd.read_csv(file_path, encoding="utf-8-sig", on_bad_lines="skip")
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(file_path, encoding="gbk", on_bad_lines="skip")
            except Exception:
                raise ValueError("CSV文件编码不支持，请使用UTF-8或GBK编码的CSV文件")
        except Exception as e:
            raise ValueError(f"CSV文件读取失败: {str(e)[:100]}，请检查文件格式")
    elif ext in ["xlsx", "xls"]:
        try:
            df = pd.read_excel(file_path, engine="openpyxl")
        except Exception as e:
            raise ValueError(f"Excel文件读取失败: {str(e)[:100]}，请确保文件未损坏且为有效Excel格式")
    else:
        raise ValueError(f"不支持的文件格式: .{ext}，请使用 CSV (.csv) 或 Excel (.xlsx/.xls) 格式")

    if df.empty:
        raise ValueError("文件为空，没有数据可解析。请检查文件内容是否包含数据行。")

    # 检查是否缺少必要列
    if len(df.columns) < 2:
        raise ValueError("文件列数过少，至少需要包含2列数据。请检查文件格式是否正确。")

    # 自动检测平台
    if platform == "auto":
        platform = detect_platform_enhanced(df, file_path)

    # 选择解析器
    parser_class = PARSERS.get(platform, GenericParser)
    parser = parser_class()

    # 解析
    try:
        result = parser.parse(df)
    except Exception as e:
        raise ValueError(f"数据解析失败: {str(e)[:100]}。可能是文件列名与预期不匹配，请检查文件格式。")

    # 如果检测为 unknown，更新平台名
    if platform == "unknown":
        result["平台"] = "未知平台"

    return result


def merge_multi_platform(dfs: list) -> pd.DataFrame:
    """合并多个平台的数据"""
    if not dfs:
        return pd.DataFrame(columns=STANDARD_COLUMNS)
    return pd.concat(dfs, ignore_index=True)
