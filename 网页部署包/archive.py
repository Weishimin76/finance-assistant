# -*- coding: utf-8 -*-
"""
跨境电商财务智能体 - 单据归档系统
财务文件自动分类归档 + 全文搜索
"""
import os
import shutil
import json
import csv
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
import pandas as pd
import re


# 归档目录结构
ARCHIVE_ROOT = "data/archive"

# 文件分类规则
CATEGORY_RULES = {
    "发票": ["invoice", "发票", "fapiao", "vat_invoice"],
    "报关单": ["customs", "报关", "declaration", "hs_code"],
    "银行流水": ["bank", "银行", "statement", "流水", "对账单"],
    "平台账单": ["settlement", "结算", "平台账单", "amazon_settlement", "payout"],
    "税务文件": ["tax", "税务", "vat_return", "vat_certificate", "报税"],
    "物流单据": ["shipping", "物流", "运单", "tracking", "waybill", "快递"],
    "合同协议": ["contract", "合同", "agreement", "协议", "service_agreement"],
    "报销凭证": ["receipt", "报销", "收据", "expense"],
    "财务报表": ["report", "报表", "financial_statement", "p&l", "balance_sheet"],
    "其他": [],
}

# 索引文件
INDEX_FILE = "data/archive_index.csv"


@dataclass
class ArchiveEntry:
    """归档条目"""
    id: str = ""
    filename: str = ""
    original_name: str = ""
    category: str = "其他"
    platform: str = ""
    country: str = ""
    date: str = ""
    amount: float = 0.0
    currency: str = ""
    tags: List[str] = field(default_factory=list)
    description: str = ""
    archive_path: str = ""
    archived_at: str = ""
    file_size: int = 0


class DocumentArchive:
    """单据归档系统"""

    def __init__(self):
        self.archive_root = ARCHIVE_ROOT
        self.index_file = INDEX_FILE
        self._ensure_dirs()
        self._entries: List[ArchiveEntry] = []
        self._load_index()

    def _ensure_dirs(self):
        """确保目录结构"""
        os.makedirs(self.archive_root, exist_ok=True)
        for category in CATEGORY_RULES:
            os.makedirs(os.path.join(self.archive_root, category), exist_ok=True)
        os.makedirs("data", exist_ok=True)

    def _load_index(self):
        """加载索引"""
        if os.path.exists(self.index_file):
            try:
                df = pd.read_csv(self.index_file, encoding="utf-8-sig")
                for _, row in df.iterrows():
                    entry = ArchiveEntry(
                        id=str(row.get("id", "")),
                        filename=str(row.get("filename", "")),
                        original_name=str(row.get("original_name", "")),
                        category=str(row.get("category", "其他")),
                        platform=str(row.get("platform", "")),
                        country=str(row.get("country", "")),
                        date=str(row.get("date", "")),
                        amount=float(row.get("amount", 0)),
                        currency=str(row.get("currency", "")),
                        tags=str(row.get("tags", "[]")),
                        description=str(row.get("description", "")),
                        archive_path=str(row.get("archive_path", "")),
                        archived_at=str(row.get("archived_at", "")),
                        file_size=int(row.get("file_size", 0)),
                    )
                    # 解析 tags
                    try:
                        entry.tags = json.loads(entry.tags.replace("'", '"'))
                    except Exception:
                        entry.tags = []
                    self._entries.append(entry)
            except Exception:
                self._entries = []

    def _save_index(self):
        """保存索引"""
        if not self._entries:
            return
        rows = []
        for entry in self._entries:
            d = asdict(entry)
            d["tags"] = json.dumps(entry.tags, ensure_ascii=False)
            rows.append(d)
        df = pd.DataFrame(rows)
        df.to_csv(self.index_file, index=False, encoding="utf-8-sig")

    def _auto_classify(self, filename: str) -> str:
        """根据文件名自动分类"""
        filename_lower = filename.lower()
        for category, keywords in CATEGORY_RULES.items():
            if category == "其他":
                continue
            for kw in keywords:
                if kw in filename_lower:
                    return category
        return "其他"

    def _extract_metadata(self, filename: str) -> Dict:
        """从文件名提取元数据"""
        metadata = {
            "platform": "",
            "country": "",
            "date": "",
            "amount": 0.0,
            "currency": "",
        }

        filename_lower = filename.lower()

        # 提取平台
        platform_keywords = {
            "amazon": "Amazon", "ebay": "eBay", "walmart": "Walmart",
            "shopify": "Shopify", "shopee": "Shopee", "aliexpress": "速卖通",
        }
        for kw, name in platform_keywords.items():
            if kw in filename_lower:
                metadata["platform"] = name
                break

        # 提取国家
        country_keywords = {
            "de": "德国", "fr": "法国", "uk": "英国", "gb": "英国",
            "it": "意大利", "es": "西班牙", "nl": "荷兰", "us": "美国",
            "jp": "日本", "au": "澳大利亚", "sg": "新加坡",
        }
        for kw, name in country_keywords.items():
            if kw in filename_lower:
                metadata["country"] = name
                break

        # 提取日期
        date_patterns = [
            r'(\d{4})[-_]?(\d{2})[-_]?(\d{2})',
            r'(\d{4})(\d{2})(\d{2})',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                metadata["date"] = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                break

        # 提取金额
        amount_match = re.search(r'([\d,]+\.?\d*)', filename)
        if amount_match:
            try:
                metadata["amount"] = float(amount_match.group(1).replace(",", ""))
            except ValueError:
                pass

        # 提取币种
        if "usd" in filename_lower or "$" in filename:
            metadata["currency"] = "USD"
        elif "eur" in filename_lower or "€" in filename:
            metadata["currency"] = "EUR"
        elif "gbp" in filename_lower or "£" in filename:
            metadata["currency"] = "GBP"
        elif "cny" in filename_lower or "rmb" in filename_lower:
            metadata["currency"] = "CNY"

        return metadata

    def archive_file(self, file_path: str, category: str = "auto",
                     tags: List[str] = None, description: str = "") -> ArchiveEntry:
        """
        归档文件

        Args:
            file_path: 原始文件路径
            category: 分类，"auto" 为自动检测
            tags: 标签列表
            description: 描述

        Returns:
            归档条目
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        original_name = os.path.basename(file_path)
        ext = os.path.splitext(original_name)[1]

        # 自动分类
        if category == "auto":
            category = self._auto_classify(original_name)

        # 提取元数据
        metadata = self._extract_metadata(original_name)

        # 生成归档文件名
        entry_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self._entries):04d}"
        archive_name = f"{entry_id}{ext}"
        archive_path = os.path.join(self.archive_root, category, archive_name)

        # 复制文件
        shutil.copy2(file_path, archive_path)

        # 创建归档条目
        entry = ArchiveEntry(
            id=entry_id,
            filename=archive_name,
            original_name=original_name,
            category=category,
            platform=metadata["platform"],
            country=metadata["country"],
            date=metadata["date"],
            amount=metadata["amount"],
            currency=metadata["currency"],
            tags=tags or [],
            description=description,
            archive_path=archive_path,
            archived_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            file_size=os.path.getsize(archive_path),
        )

        self._entries.append(entry)
        self._save_index()

        return entry

    def search(self, query: str, category: str = "", date_from: str = "",
              date_to: str = "", platform: str = "") -> pd.DataFrame:
        """
        全文搜索归档文件

        Args:
            query: 搜索关键词
            category: 分类筛选
            date_from: 起始日期
            date_to: 结束日期
            platform: 平台筛选

        Returns:
            搜索结果 DataFrame
        """
        if not self._entries:
            return pd.DataFrame()

        results = []
        query_lower = query.lower() if query else ""

        for entry in self._entries:
            # 分类筛选
            if category and entry.category != category:
                continue

            # 日期筛选
            if date_from and entry.date and entry.date < date_from:
                continue
            if date_to and entry.date and entry.date > date_to:
                continue

            # 平台筛选
            if platform and entry.platform != platform:
                continue

            # 关键词搜索
            if query_lower:
                searchable = " ".join([
                    entry.original_name.lower(),
                    entry.description.lower(),
                    entry.category.lower(),
                    entry.platform.lower(),
                    entry.country.lower(),
                    " ".join(entry.tags).lower(),
                ])
                if query_lower not in searchable:
                    continue

            results.append({
                "ID": entry.id,
                "文件名": entry.original_name,
                "分类": entry.category,
                "平台": entry.platform,
                "国家": entry.country,
                "日期": entry.date,
                "金额": entry.amount,
                "币种": entry.currency,
                "标签": ", ".join(entry.tags),
                "描述": entry.description,
                "归档时间": entry.archived_at,
                "文件大小": f"{entry.file_size / 1024:.1f}KB",
            })

        return pd.DataFrame(results)

    def get_statistics(self) -> pd.DataFrame:
        """获取归档统计"""
        if not self._entries:
            return pd.DataFrame()

        categories = {}
        for entry in self._entries:
            if entry.category not in categories:
                categories[entry.category] = {"count": 0, "size": 0}
            categories[entry.category]["count"] += 1
            categories[entry.category]["size"] += entry.file_size

        rows = []
        for cat, data in categories.items():
            rows.append({
                "分类": cat,
                "文件数": data["count"],
                "总大小": f"{data['size'] / 1024 / 1024:.1f}MB",
            })

        return pd.DataFrame(rows)

    def get_all_entries(self) -> pd.DataFrame:
        """获取所有归档条目"""
        if not self._entries:
            return pd.DataFrame()

        rows = []
        for entry in sorted(self._entries, key=lambda x: x.archived_at, reverse=True):
            rows.append({
                "ID": entry.id,
                "文件名": entry.original_name,
                "分类": entry.category,
                "平台": entry.platform,
                "国家": entry.country,
                "日期": entry.date,
                "金额": entry.amount,
                "标签": ", ".join(entry.tags),
                "归档时间": entry.archived_at,
            })

        return pd.DataFrame(rows)

    def delete_entry(self, entry_id: str) -> bool:
        """删除归档条目"""
        for i, entry in enumerate(self._entries):
            if entry.id == entry_id:
                # 删除文件
                if os.path.exists(entry.archive_path):
                    os.remove(entry.archive_path)
                self._entries.pop(i)
                self._save_index()
                return True
        return False


# 全局实例
document_archive = DocumentArchive()
