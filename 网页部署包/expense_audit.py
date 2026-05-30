# -*- coding: utf-8 -*-
"""
跨境电商财务智能体 - 报销/付款审核模块
图片上传识别 + 自动加总 + 对比公司标准 + 标红超标
"""
import pandas as pd
import numpy as np
import os
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class ExpenseItem:
    """报销项"""
    description: str = ""
    amount: float = 0.0
    currency: str = "CNY"
    category: str = ""
    date: str = ""
    receipt_type: str = ""  # 发票/收据/无
    vendor: str = ""
    is_anomaly: bool = False
    anomaly_reason: str = ""


@dataclass
class AuditRule:
    """审核规则"""
    name: str
    category: str
    max_amount: float = 0.0  # 0 = 无限制
    need_receipt: bool = True  # 是否需要发票
    need_approval: bool = False  # 是否需要审批
    description: str = ""


# 默认审核规则
DEFAULT_AUDIT_RULES = [
    AuditRule("餐饮报销", "餐饮", max_amount=500, need_receipt=True, description="单次餐饮不超过500元"),
    AuditRule("交通报销", "交通", max_amount=200, need_receipt=False, description="单次交通不超过200元"),
    AuditRule("住宿报销", "住宿", max_amount=800, need_receipt=True, description="单晚住宿不超过800元"),
    AuditRule("办公用品", "办公用品", max_amount=2000, need_receipt=True, description="单次办公用品不超过2000元"),
    AuditRule("物流运费", "物流运费", max_amount=0, need_receipt=True, description="物流运费需有发票"),
    AuditRule("广告推广", "广告推广", max_amount=50000, need_receipt=True, need_approval=True, description="广告推广超5万需审批"),
    AuditRule("样品费", "样品费", max_amount=1000, need_receipt=True, description="单次样品费不超过1000元"),
    AuditRule("平台费用", "平台费用", max_amount=0, need_receipt=True, description="平台费用需有发票"),
    AuditRule("包装材料", "包装材料", max_amount=5000, need_receipt=True, description="单次包装材料不超过5000元"),
    AuditRule("其他费用", "其他", max_amount=0, need_receipt=False, description="其他费用"),
]


class ExpenseAuditor:
    """报销审核器"""

    def __init__(self, rules: List[AuditRule] = None):
        self.rules = rules or DEFAULT_AUDIT_RULES
        self.expenses: List[ExpenseItem] = []

    def add_expense(self, item: ExpenseItem):
        """添加报销项"""
        self.expenses.append(item)

    def parse_text_expense(self, text: str) -> List[ExpenseItem]:
        """
        从文本中解析报销信息（简易OCR结果或手动输入）

        Args:
            text: 包含报销信息的文本

        Returns:
            解析出的报销项列表
        """
        items = []
        lines = text.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            item = ExpenseItem()

            # 提取金额（支持多种格式）
            amount_patterns = [
                r'[\$￥¥€£]?\s*([\d,]+\.?\d*)\s*(?:元|CNY|USD|EUR|GBP)?',
                r'(?:金额|合计|总计|总额)[：:]\s*([\d,]+\.?\d*)',
                r'(\d+\.?\d*)\s*(?:元|块)',
            ]

            amount_found = False
            for pattern in amount_patterns:
                match = re.search(pattern, line)
                if match:
                    item.amount = float(match.group(1).replace(",", ""))
                    amount_found = True
                    break

            if not amount_found:
                continue

            # 提取日期
            date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', line)
            if date_match:
                item.date = date_match.group(1).replace("/", "-")

            # 提取币种
            if "$" in line or "USD" in line:
                item.currency = "USD"
            elif "€" in line or "EUR" in line:
                item.currency = "EUR"
            elif "£" in line or "GBP" in line:
                item.currency = "GBP"
            else:
                item.currency = "CNY"

            # 提取描述（去掉金额部分）
            desc = re.sub(r'[\d,]+\.?\d*\s*(?:元|CNY|USD|EUR|GBP)?', '', line).strip()
            desc = re.sub(r'[￥¥$€£]', '', desc).strip()
            desc = re.sub(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', '', desc).strip()
            if desc:
                item.description = desc

            # 自动分类
            item.category = self._auto_classify(item.description)

            # 检测发票
            if "发票" in line or "invoice" in line.lower():
                item.receipt_type = "发票"
            elif "收据" in line or "receipt" in line.lower():
                item.receipt_type = "收据"
            else:
                item.receipt_type = "无"

            items.append(item)

        return items

    def _auto_classify(self, text: str) -> str:
        """根据描述自动分类"""
        text_lower = text.lower()
        category_keywords = {
            "餐饮": ["餐", "饭", "食", "外卖", "咖啡", "茶", "饮料", "restaurant", "food", "meal"],
            "交通": ["车", "机票", "火车", "地铁", "出租", "加油", "停车", "taxi", "uber", "transport"],
            "住宿": ["酒店", "宾馆", "住宿", "hotel", "hostel", "airbnb"],
            "办公用品": ["办公", "文具", "打印", "纸", "笔", "office"],
            "物流运费": ["运费", "物流", "快递", "shipping", "freight", "dhl", "fedex", "ups"],
            "广告推广": ["广告", "推广", "投放", "ad", "marketing", "promotion"],
            "样品费": ["样品", "sample"],
            "平台费用": ["平台费", "月租", "仓储费", "storage", "platform"],
            "包装材料": ["包装", "胶带", "纸箱", "标签", "packaging", "box", "label"],
        }

        for category, keywords in category_keywords.items():
            for kw in keywords:
                if kw in text_lower:
                    return category

        return "其他"

    def audit(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        执行审核

        Returns:
            (正常项, 异常项) 两个 DataFrame
        """
        normal_items = []
        anomaly_items = []

        for item in self.expenses:
            is_anomaly = False
            reasons = []

            # 查找匹配的规则
            matched_rule = None
            for rule in self.rules:
                if rule.category == item.category:
                    matched_rule = rule
                    break

            if matched_rule is None:
                matched_rule = AuditRule("默认", "其他")

            # 检查金额上限
            if matched_rule.max_amount > 0 and item.amount > matched_rule.max_amount:
                is_anomaly = True
                reasons.append(f"超出{matched_rule.name}限额 {matched_rule.max_amount}元")

            # 检查发票
            if matched_rule.need_receipt and item.receipt_type == "无":
                is_anomaly = True
                reasons.append(f"{matched_rule.name}需要发票")

            # 检查是否需要审批
            if matched_rule.need_approval and item.amount > matched_rule.max_amount:
                is_anomaly = True
                reasons.append(f"超限额需主管审批")

            item.is_anomaly = is_anomaly
            item.anomaly_reason = " | ".join(reasons)

            if is_anomaly:
                anomaly_items.append(item)
            else:
                normal_items.append(item)

        # 转换为 DataFrame
        def items_to_df(items):
            if not items:
                return pd.DataFrame()
            return pd.DataFrame([{
                "描述": it.description,
                "金额": it.amount,
                "币种": it.currency,
                "分类": it.category,
                "日期": it.date,
                "票据类型": it.receipt_type,
                "异常原因": it.anomaly_reason,
                "状态": "🔴 异常" if it.is_anomaly else "✅ 正常",
            } for it in items])

        normal_df = items_to_df(normal_items)
        anomaly_df = items_to_df(anomaly_items)

        return normal_df, anomaly_df

    def get_summary(self) -> pd.DataFrame:
        """获取审核汇总"""
        if not self.expenses:
            return pd.DataFrame()

        # 按分类汇总
        categories = {}
        for item in self.expenses:
            if item.category not in categories:
                categories[item.category] = {"count": 0, "total": 0, "anomaly": 0}
            categories[item.category]["count"] += 1
            categories[item.category]["total"] += item.amount
            if item.is_anomaly:
                categories[item.category]["anomaly"] += 1

        rows = []
        for cat, data in categories.items():
            rows.append({
                "分类": cat,
                "笔数": data["count"],
                "总金额": round(data["total"], 2),
                "异常笔数": data["anomaly"],
                "状态": "🔴 有异常" if data["anomaly"] > 0 else "✅ 正常",
            })

        # 合计行
        total_amount = sum(data["total"] for data in categories.values())
        total_count = sum(data["count"] for data in categories.values())
        total_anomaly = sum(data["anomaly"] for data in categories.values())
        rows.append({
            "分类": "合计",
            "笔数": total_count,
            "总金额": round(total_amount, 2),
            "异常笔数": total_anomaly,
            "状态": "🔴 有异常" if total_anomaly > 0 else "✅ 正常",
        })

        return pd.DataFrame(rows)

    def reset(self):
        """清空报销项"""
        self.expenses = []


def parse_expense_from_image(image_path: str) -> List[ExpenseItem]:
    """
    从图片中解析报销信息

    注意：完整 OCR 需要安装额外依赖（如 pytesseract 或 PaddleOCR）
    这里提供基础实现，建议安装 PaddleOCR 获得更好的中文识别效果

    Args:
        image_path: 图片路径

    Returns:
        解析出的报销项
    """
    text = ""

    # 尝试 PaddleOCR（推荐）
    try:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
        result = ocr.ocr(image_path, cls=True)
        if result and result[0]:
            text = "\n".join([line[1][0] for line in result[0]])
    except ImportError:
        pass

    # 尝试 pytesseract
    if not text:
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang="chi_sim+eng")
        except ImportError:
            text = "[需要安装 OCR 引擎] 请安装 PaddleOCR: pip install paddleocr"

    if not text:
        return []

    auditor = ExpenseAuditor()
    return auditor.parse_text_expense(text)
