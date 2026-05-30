# -*- coding: utf-8 -*-
"""
跨境电商财务智能体 - 配置管理
"""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    """全局配置"""
    # Ollama 配置
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:14b"  # 推荐使用中文能力强的模型

    # 数据目录
    data_dir: str = "data"
    upload_dir: str = "data/uploads"
    archive_dir: str = "data/archive"
    output_dir: str = "data/output"

    # 支持的平台
    supported_platforms: list = field(default_factory=lambda: [
        "amazon", "ebay", "walmart", "shopify", "aliexpress", "shopee"
    ])

    # VAT 税率（主要国家）
    vat_rates: dict = field(default_factory=lambda: {
        "德国": 0.19,
        "法国": 0.20,
        "意大利": 0.22,
        "西班牙": 0.21,
        "英国": 0.20,
        "荷兰": 0.21,
        "波兰": 0.23,
        "比利时": 0.21,
        "瑞典": 0.25,
        "捷克": 0.21,
    })

    # 佣金率参考（各平台典型范围）
    commission_rates: dict = field(default_factory=lambda: {
        "amazon": {"min": 0.08, "max": 0.45, "typical": 0.15},
        "ebay": {"min": 0.10, "max": 0.15, "typical": 0.13},
        "walmart": {"min": 0.06, "max": 0.20, "typical": 0.15},
        "shopify": {"min": 0.0, "max": 0.02, "typical": 0.01},  # 支付网关费
        "shopee": {"min": 0.02, "max": 0.12, "typical": 0.08},
        "aliexpress": {"min": 0.05, "max": 0.15, "typical": 0.08},
    })

    # 汇率 API
    exchange_rate_api: str = "https://api.exchangerate-api.com/v4/latest"

    # 安全设置
    strict_finance_only: bool = True  # 只回答财务相关问题
    max_upload_size_mb: int = 50

    def ensure_dirs(self):
        """确保所有必要目录存在"""
        for d in [self.data_dir, self.upload_dir, self.archive_dir, self.output_dir]:
            os.makedirs(d, exist_ok=True)


# 全局配置实例
config = Config()
config.ensure_dirs()
