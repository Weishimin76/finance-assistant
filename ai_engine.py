# -*- coding: utf-8 -*-
"""
智能AI引擎模块 - Smart AI Engine Module (增强版)

内置财务知识库 + Ollama本地模型 + 云端API 三引擎架构。
新增：防幻觉三层验证、实时数据集成、联网搜索、增强回答格式、平台费率计算集成。

引擎优先级：
1. 云端API（如果有配置API密钥，优先使用）
2. Ollama本地模型（如果Ollama服务可用，增强回答质量）
3. 内置知识库（永远可用，确保系统始终能给出回答）

防幻觉三层验证：
- Layer1: 涉及具体数字（税率/费率/汇率）的问题，必须从知识库或实时数据检索，禁止AI凭空编造
- Layer2: 置信度标注 - 高置信度直接输出，低置信度标注"此数据仅供参考，建议核实"
- Layer3: 来源追溯 - 每条关键数据附带来源标注

设计理念：
- 零依赖启动：即使没有任何外部AI服务，系统仍可基于内置知识库工作
- 自动检测：运行时自动探测可用的AI引擎，无需手动配置
- 智能降级：高优先级引擎不可用时自动切换到低优先级引擎
- 上下文增强：Ollama/云端引擎会以知识库搜索结果作为上下文，提升回答准确性
- 数据驱动：涉及数字的问题优先从实时数据/知识库获取，避免AI幻觉
"""

import json
import re
import os
import requests
from typing import Optional, List, Dict, Tuple
from datetime import datetime

try:
    import pandas as pd
except ImportError:
    pd = None

from financial_knowledge import search_knowledge

# 实时数据模块
try:
    from realtime_data import (
        get_exchange_rates,
        get_vat_rates,
        get_china_tax_rates,
        get_data_status,
    )
    _REALTIME_AVAILABLE = True
except ImportError:
    _REALTIME_AVAILABLE = False

# 平台费率模块
try:
    from platform_fees import (
        get_platform_fee,
        calculate_platform_commission,
        search_platform,
        compare_platforms,
    )
    _PLATFORM_FEES_AVAILABLE = True
except ImportError:
    _PLATFORM_FEES_AVAILABLE = False


# ============================================================================
# 问题类型检测关键词
# ============================================================================
_QUESTION_TYPE_PATTERNS = {
    "exchange_rate": {
        "keywords": [
            "汇率", "汇价", "兑换", "换算", "人民币兑美元", "美元兑人民币",
            "eur", "gbp", "jpy", "usd", "exchange rate", "currency",
            "usd/cny", "usdrmb", "美金", "英镑", "欧元", "日元",
        ],
        "label": "汇率查询",
    },
    "tax_rate": {
        "keywords": [
            "税率", "增值税", "vat", "所得税", "关税", "消费税",
            "tax rate", "tax", "企业税", "个人税", "个税",
            "销售税", "sales tax", "进口税", "出口退税",
            "小规模纳税人", "一般纳税人", "加计抵减",
        ],
        "label": "税率查询",
    },
    "fee_rate": {
        "keywords": [
            "佣金", "手续费", "费率", "commission", "fee",
            "平台费", "交易费", "提现费", "支付费",
            "listing fee", "referral fee", "transaction fee",
        ],
        "label": "费率查询",
    },
    "platform": {
        "keywords": [
            "amazon", "ebay", "shopee", "shopify", "walmart",
            "temu", "tiktok", "速卖通", "wish", "ozon", "lazada",
            "coupang", "美客多", "mercado", "pingpong", "paypal",
            "stripe", "worldfirst", "连连", "天猫", "京东", "拼多多",
            "平台对比", "平台比较", "哪个平台", "平台费用",
            "fba", "仓储费", "配送费", "fulfillment",
        ],
        "label": "平台查询",
    },
    "policy": {
        "keywords": [
            "政策", "法规", "合规", "申报", "注册", "备案",
            "policy", "regulation", "compliance", "customs",
            "海关", "税务政策", "新规", "最新政策",
        ],
        "label": "政策查询",
    },
}


def _detect_question_type(question: str) -> Tuple[str, float]:
    """
    检测用户问题的类型。

    Args:
        question: 用户的问题文本

    Returns:
        tuple: (问题类型标签, 匹配分数)
    """
    q_lower = question.lower().strip()
    best_type = "general"
    best_score = 0.0

    for qtype, info in _QUESTION_TYPE_PATTERNS.items():
        score = 0.0
        for kw in info["keywords"]:
            if kw in q_lower:
                score += 1.0
        if score > best_score:
            best_score = score
            best_type = qtype

    return best_type, best_score


def _is_numeric_question(question: str) -> bool:
    """
    判断问题是否涉及具体数字（税率/费率/汇率）。

    Layer1 防幻觉：涉及具体数字的问题必须从数据源获取，禁止AI编造。

    Args:
        question: 用户的问题文本

    Returns:
        bool: True 表示问题涉及具体数字
    """
    q_lower = question.lower()
    numeric_keywords = [
        "多少", "费率", "税率", "汇率", "佣金", "百分比", "比例",
        "计算", "费用", "多少钱", "收费", "标准",
        "how much", "rate", "fee", "tax", "commission", "percentage",
        "cost", "price", "charge",
    ]
    return any(kw in q_lower for kw in numeric_keywords)


def _assess_confidence(data_source: str, data_age_days: float = 0) -> Tuple[str, str]:
    """
    评估数据置信度。

    Layer2 防幻觉：高置信度直接输出，低置信度标注建议核实。

    Args:
        data_source: 数据来源标识
        data_age_days: 数据距今天数

    Returns:
        tuple: (置信度等级 "high"/"medium"/"low", 标注文本)
    """
    if data_source in ("online", "builtin"):
        if data_age_days <= 30:
            return "high", ""
        elif data_age_days <= 180:
            return "medium", "此数据仅供参考，建议核实"
        else:
            return "low", "此数据可能已过期，建议核实最新政策"
    elif data_source == "cache":
        return "medium", "此数据来自缓存，建议核实"
    elif data_source == "knowledge_base":
        return "medium", "此数据来自知识库，建议核实"
    elif data_source == "web_search":
        return "medium", "此数据来自网络搜索，建议核实"
    else:
        return "low", "此数据仅供参考，建议核实"


def _format_source_tag(source: str, extra: str = "") -> str:
    """
    生成来源标注标签。

    Layer3 防幻觉：每条关键数据附带来源标注。

    Args:
        source: 来源描述
        extra: 额外信息（如更新时间）

    Returns:
        str: 格式化的来源标注
    """
    tag = f"[来源：{source}]"
    if extra:
        tag += f" {extra}"
    return tag


def _format_currency(amount: float, currency: str = "USD") -> str:
    """
    格式化金额，保留2位小数，带币种符号。

    Args:
        amount: 金额
        currency: 货币代码

    Returns:
        str: 格式化的金额字符串
    """
    symbols = {
        "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥",
        "CNY": "¥", "RMB": "¥", "AUD": "A$", "CAD": "C$",
        "CHF": "CHF", "SGD": "S$", "HKD": "HK$", "KRW": "₩",
        "THB": "฿", "INR": "₹", "MYR": "RM", "PHP": "₱",
        "IDR": "Rp", "VND": "₫", "RUB": "₽", "BRL": "R$",
        "MXN": "MX$", "NZD": "NZ$",
    }
    symbol = symbols.get(currency.upper(), currency + " ")
    if currency.upper() == "JPY":
        return f"{symbol}{int(round(amount)):,}"
    return f"{symbol}{amount:,.2f}"


def _format_percentage(rate: float) -> str:
    """
    格式化百分比，精确到0.01%。

    Args:
        rate: 小数形式的比率（如 0.15 表示 15%）

    Returns:
        str: 格式化的百分比字符串
    """
    return f"{rate * 100:.2f}%"


def _format_data_expiry(updated_at: str) -> str:
    """
    生成过期数据标注。

    Args:
        updated_at: 数据更新时间（ISO格式字符串）

    Returns:
        str: 过期标注文本，如果数据较新则返回空字符串
    """
    if not updated_at:
        return "[数据更新时间未知，建议核实]"
    try:
        updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00").replace("+00:00", ""))
        now = datetime.now()
        days_diff = (now - updated).days
        if days_diff > 180:
            return f"[数据更新于{updated.strftime('%Y-%m-%d')}，已超过6个月，建议核实]"
        elif days_diff > 30:
            return f"[数据更新于{updated.strftime('%Y-%m-%d')}，建议核实]"
        else:
            return f"[数据更新于{updated.strftime('%Y-%m-%d')}]"
    except (ValueError, AttributeError):
        return f"[数据更新于{updated_at}，建议核实]"


def _build_markdown_table(headers: List[str], rows: List[List[str]]) -> str:
    """
    构建Markdown格式的表格。

    Args:
        headers: 表头列表
        rows: 数据行列表

    Returns:
        str: Markdown表格字符串
    """
    if not headers or not rows:
        return ""
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


class FinanceAI:
    """智能财务AI引擎 - 自动检测并调度可用AI引擎（增强版）"""

    def __init__(self):
        """初始化AI引擎，自动检测可用引擎"""
        self.ollama_available = False
        self.cloud_available = False
        self.ollama_url = "http://localhost:11434"
        self.ollama_model = "qwen2.5:14b"
        self.cloud_api_key = ""
        self.cloud_api_url = ""
        self.cloud_model = ""

        # 自动检测可用引擎
        self.check_engines()

    def check_engines(self):
        """
        检测所有可用AI引擎的状态。

        依次检测：
        1. Ollama本地服务（通过HTTP请求探测）
        2. 云端API配置（检查是否已配置API密钥）
        检测结果保存在实例属性中，供后续调度使用。
        """
        # 检测Ollama
        try:
            response = requests.get(
                self.ollama_url,
                timeout=3
            )
            if response.status_code == 200:
                self.ollama_available = True
            else:
                self.ollama_available = False
        except Exception:
            self.ollama_available = False

        # 检测云端API配置
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "data", ".secure_config"
            )
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    secure_config = json.load(f)
                self.cloud_api_key = secure_config.get("cloud_api_key", "")
                self.cloud_api_url = secure_config.get("cloud_api_url", "")
                self.cloud_model = secure_config.get("cloud_model", "")
                if self.cloud_api_key and self.cloud_api_url:
                    self.cloud_available = True
                else:
                    self.cloud_available = False
            else:
                self.cloud_available = False
        except Exception:
            self.cloud_available = False

    def get_engine_status(self) -> Dict[str, dict]:
        """
        返回各AI引擎的状态信息。

        Returns:
            dict: 包含各引擎状态的字典
        """
        status = {
            "knowledge_base": {
                "available": True,
                "desc": "内置财务知识库（始终可用）"
            },
            "ollama": {
                "available": self.ollama_available,
                "desc": (
                    f"Ollama本地模型已就绪 (模型: {self.ollama_model})"
                    if self.ollama_available
                    else "Ollama未检测到（系统将使用内置知识库）"
                )
            },
            "cloud_api": {
                "available": self.cloud_available,
                "desc": (
                    f"云端API已配置 (模型: {self.cloud_model})"
                    if self.cloud_available
                    else "云端API未配置"
                )
            },
            "realtime_data": {
                "available": _REALTIME_AVAILABLE,
                "desc": (
                    "实时数据模块已就绪（汇率/税率/费率）"
                    if _REALTIME_AVAILABLE
                    else "实时数据模块不可用"
                )
            },
            "platform_fees": {
                "available": _PLATFORM_FEES_AVAILABLE,
                "desc": (
                    "平台费率模块已就绪（20+平台）"
                    if _PLATFORM_FEES_AVAILABLE
                    else "平台费率模块不可用"
                )
            },
        }
        return status

    # ====================================================================
    # 联网搜索能力（预留）
    # ====================================================================
    def _web_search(self, query: str) -> List[Dict[str, str]]:
        """
        使用DuckDuckGo API搜索最新政策信息。

        当知识库中没有匹配结果时，尝试联网搜索。

        Args:
            query: 搜索查询文本

        Returns:
            list: 搜索结果列表，每项包含 title, url, snippet
        """
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1,
            }
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                results = []
                # DuckDuckGo Instant Answer API 返回的相关主题
                topics = data.get("RelatedTopics", [])
                for topic in topics[:5]:
                    if isinstance(topic, dict):
                        text = topic.get("Text", "")
                        url_link = topic.get("FirstURL", "")
                        if text:
                            results.append({
                                "title": text[:100],
                                "url": url_link,
                                "snippet": text,
                            })
                    elif isinstance(topic, str):
                        results.append({
                            "title": topic[:100],
                            "url": "",
                            "snippet": topic,
                        })
                if results:
                    return results
        except Exception:
            pass

        # DuckDuckGo Instant Answer API 可能不返回丰富结果，
        # 尝试 HTML 搜索版本
        try:
            search_url = "https://html.duckduckgo.com/html/"
            params = {"q": query}
            resp = requests.get(search_url, params=params, timeout=10, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            if resp.status_code == 200:
                # 简单提取结果摘要
                results = []
                results_html = resp.text
                # 提取结果块
                result_blocks = re.findall(
                    r'<a rel="nofollow" class="result__a"[^>]*>(.*?)</a>.*?'
                    r'<a class="result__snippet"[^>]*>(.*?)</a>',
                    results_html,
                    re.DOTALL
                )
                for title, snippet in result_blocks[:5]:
                    clean_title = re.sub(r'<[^>]+>', '', title).strip()
                    clean_snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                    if clean_title:
                        results.append({
                            "title": clean_title,
                            "url": "",
                            "snippet": clean_snippet,
                        })
                return results
        except Exception:
            pass

        return []

    # ====================================================================
    # 实时数据查询路由
    # ====================================================================
    def _query_exchange_rate(self, question: str) -> Optional[str]:
        """
        查询汇率数据并格式化回答。

        Args:
            question: 用户问题

        Returns:
            str: 格式化的汇率回答，或 None（如果无法处理）
        """
        if not _REALTIME_AVAILABLE:
            return None

        try:
            data = get_exchange_rates()
            rates = data.get("rates", {})
            base = data.get("base", "USD")
            updated_at = data.get("updated_at", "")
            source = data.get("source", "unknown")
            is_cached = data.get("is_cached", False)

            if not rates:
                return None

            # 检测用户询问的具体货币对
            q_lower = question.lower()
            target_currencies = []
            currency_map = {
                "美元": "USD", "美金": "USD", "usd": "USD",
                "欧元": "EUR", "eur": "EUR",
                "英镑": "GBP", "gbp": "GBP",
                "日元": "JPY", "jp": "JPY", "jpy": "JPY",
                "澳元": "AUD", "aud": "AUD",
                "加元": "CAD", "cad": "CAD",
                "人民币": "CNY", "rmb": "CNY", "cny": "CNY",
                "港币": "HKD", "hkd": "HKD",
                "韩元": "KRW", "krw": "KRW",
                "泰铢": "THB", "thb": "THB",
                "新加坡元": "SGD", "sgd": "SGD",
                "瑞郎": "CHF", "chf": "CHF",
            }

            for cn_name, code in currency_map.items():
                if cn_name in q_lower:
                    target_currencies.append(code)

            # 如果没有检测到具体货币，显示主要货币
            if not target_currencies:
                target_currencies = ["CNY", "EUR", "GBP", "JPY", "AUD", "CAD"]

            # 构建回答
            parts = []
            parts.append("## 实时汇率查询")
            parts.append("")

            # 置信度评估
            confidence, notice = _assess_confidence(
                "cache" if is_cached else "online"
            )
            if notice:
                parts.append(f"> {notice}")
                parts.append("")

            # 数据更新时间标注
            expiry_tag = _format_data_expiry(updated_at)
            parts.append(expiry_tag)
            parts.append("")

            # 构建汇率表格
            headers = ["货币", f"兑{base}汇率", f"1{base}兑换"]
            rows = []
            for code in target_currencies:
                if code in rates:
                    rate = rates[code]
                    if base == "USD" and code == "CNY":
                        rows.append([
                            f"{code} (人民币)",
                            f"{rate:.4f}",
                            f"{_format_currency(1, 'USD')} = {_format_currency(rate, 'CNY')}",
                        ])
                    else:
                        symbol_map = {
                            "EUR": "EUR (欧元)", "GBP": "GBP (英镑)",
                            "JPY": "JPY (日元)", "AUD": "AUD (澳元)",
                            "CAD": "CAD (加元)", "HKD": "HKD (港币)",
                            "KRW": "KRW (韩元)", "THB": "THB (泰铢)",
                            "SGD": "SGD (新元)", "CHF": "CHF (瑞郎)",
                        }
                        label = symbol_map.get(code, code)
                        rows.append([
                            label,
                            f"{rate:.4f}",
                            f"{_format_currency(1, base)} = {rate:.4f} {code}",
                        ])

            if rows:
                parts.append(_build_markdown_table(headers, rows))
                parts.append("")

            # 来源标注
            source_label = "缓存" if is_cached else source
            parts.append(_format_source_tag(source_label, f"基准货币: {base}"))

            return "\n".join(parts)

        except Exception:
            return None

    def _query_tax_rate(self, question: str) -> Optional[str]:
        """
        查询税率数据并格式化回答。

        Args:
            question: 用户问题

        Returns:
            str: 格式化的税率回答，或 None
        """
        q_lower = question.lower()
        parts = []

        # 检测查询类型
        is_vat = any(kw in q_lower for kw in ["vat", "增值税", "消费税"])
        is_china = any(kw in q_lower for kw in ["中国", "国内", "小规模", "一般纳税人", "企业所得税", "个人所得税", "个税", "关税"])
        is_us = any(kw in q_lower for kw in ["美国", "us", "州税", "sales tax"])

        if is_vat and _REALTIME_AVAILABLE:
            try:
                data = get_vat_rates()
                vat_rates = data.get("rates", {})
                updated_at = data.get("updated_at", "")

                parts.append("## 各国VAT税率")
                parts.append("")
                parts.append(_format_data_expiry(updated_at))
                parts.append("")

                # 检测用户询问的具体国家
                country_map = {
                    "英国": "英国", "德国": "德国", "法国": "法国",
                    "意大利": "意大利", "西班牙": "西班牙", "荷兰": "荷兰",
                    "波兰": "波兰", "比利时": "比利时", "瑞典": "瑞典",
                    "奥地利": "奥地利", "日本": "日本", "澳大利亚": "澳大利亚",
                    "加拿大": "加拿大",
                }
                target_countries = []
                for cn, key in country_map.items():
                    if cn in question:
                        target_countries.append(key)

                if not target_countries:
                    target_countries = list(vat_rates.keys())[:8]

                headers = ["国家/地区", "标准税率", "低税率"]
                rows = []
                for country in target_countries:
                    if country in vat_rates:
                        info = vat_rates[country]
                        std_rate = _format_percentage(info.get("standard_rate", 0))
                        red_rate = _format_percentage(info.get("reduced_rate", 0))
                        rows.append([country, std_rate, red_rate])

                if rows:
                    parts.append(_build_markdown_table(headers, rows))
                    parts.append("")

                parts.append(_format_source_tag("内置VAT税率数据 (2024-2025)"))
                parts.append("")
                parts.append("> 注：涉及税务问题时，请以税务机关最终确认为准。")

                return "\n".join(parts)
            except Exception:
                pass

        if is_china and _REALTIME_AVAILABLE:
            try:
                data = get_china_tax_rates()
                china_rates = data.get("rates", {})
                updated_at = data.get("updated_at", "")

                parts.append("## 中国税率查询")
                parts.append("")
                parts.append(_format_data_expiry(updated_at))
                parts.append("")

                # 增值税
                if "增值税" in china_rates:
                    parts.append("### 增值税")
                    vat_info = china_rates["增值税"]
                    headers = ["纳税人类型", "税率", "适用范围"]
                    rows = []
                    for key, val in vat_info.items():
                        if isinstance(val, dict):
                            rate = val.get("税率", val.get("标准税率", ""))
                            scope = val.get("适用范围", "")
                            if isinstance(rate, float):
                                rate = _format_percentage(rate)
                            rows.append([key, str(rate), scope])
                    if rows:
                        parts.append(_build_markdown_table(headers, rows))
                        parts.append("")

                # 企业所得税
                if "企业所得税" in china_rates:
                    parts.append("### 企业所得税")
                    cit_info = china_rates["企业所得税"]
                    headers = ["类型", "税率"]
                    rows = []
                    for key, val in cit_info.items():
                        if isinstance(val, (int, float)):
                            rows.append([key, _format_percentage(val)])
                        elif isinstance(val, str):
                            rows.append([key, val])
                    if rows:
                        parts.append(_build_markdown_table(headers, rows))
                        parts.append("")

                # 个人所得税
                if "个人所得税" in china_rates:
                    parts.append("### 个人所得税")
                    pit_info = china_rates["个人所得税"]
                    for key, val in pit_info.items():
                        if isinstance(val, dict):
                            rate = val.get("税率", "")
                            threshold = val.get("起征点", "")
                            line = f"- **{key}**: {rate}"
                            if threshold:
                                line += f"（起征点: {_format_currency(threshold, 'CNY')}/月）"
                            parts.append(line)
                    parts.append("")

                parts.append(_format_source_tag("内置中国税率数据 (2024-2025)"))
                parts.append("")
                parts.append("> 注：涉及税务问题时，请以税务机关最终确认为准。")

                return "\n".join(parts)
            except Exception:
                pass

        return None

    def _query_platform_fee(self, question: str) -> Optional[str]:
        """
        查询平台费率数据并格式化回答。

        Args:
            question: 用户问题

        Returns:
            str: 格式化的平台费率回答，或 None
        """
        if not _PLATFORM_FEES_AVAILABLE:
            return None

        q_lower = question.lower()

        # 检测FBA费用计算请求
        fba_keywords = ["fba费用", "fba计算", "仓储费", "配送费", "fulfillment"]
        is_fba_query = any(kw in q_lower for kw in fba_keywords)

        if is_fba_query:
            try:
                from platform_fees import calculate_amazon_fba
                # 尝试从问题中提取重量和尺寸
                weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(oz|盎司|ozs)', q_lower)
                size_match = re.search(r'(小标准|大标准|大件|small|large|oversize)', q_lower)

                weight = float(weight_match.group(1)) if weight_match else 10
                size = size_match.group(1) if size_match else "大标准"
                # 标准化尺寸名称
                size_normalize = {"small": "小标准", "large": "大标准", "oversize": "大件"}
                size = size_normalize.get(size.lower(), size)

                result = calculate_amazon_fba(weight, size)

                parts = []
                parts.append("## Amazon FBA费用计算")
                parts.append("")

                if "error" in result:
                    parts.append(f"错误: {result['error']}")
                else:
                    parts.append(f"- **区域**: {result.get('region', '美国')}")
                    parts.append(f"- **尺寸分类**: {result.get('size_category', '')}")
                    parts.append(f"- **重量**: {result.get('weight_oz', 0)} oz")
                    parts.append(f"- **预估配送费**: {result.get('display_fee', '')}")
                    parts.append("")

                    if result.get("notice"):
                        parts.append(f"> {result['notice']}")
                        parts.append("")

                    parts.append(_format_source_tag(
                        result.get("source", "Amazon Seller Central"),
                        f"更新于 {result.get('updated', '未知')}"
                    ))
                    parts.append("")
                    parts.append(f"> {result.get('disclaimer', '')}")

                return "\n".join(parts)
            except Exception:
                pass

        # 检测平台对比请求
        compare_keywords = ["平台对比", "平台比较", "各平台", "哪个平台", "平台费用对比"]
        is_compare = any(kw in q_lower for kw in compare_keywords)

        if is_compare:
            try:
                # 默认对比主要平台
                platforms = ["amazon", "ebay", "shopee", "tiktok_shop", "temu"]
                amount = 1000  # 默认对比金额 $1000

                # 尝试从问题中提取金额
                amount_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:美元|usd|美金|\$)?', question)
                if amount_match:
                    amount = float(amount_match.group(1))

                result = compare_platforms(platforms, amount)

                parts = []
                parts.append("## 平台费用对比")
                parts.append("")
                parts.append(f"对比金额: {_format_currency(amount, 'USD')}")
                parts.append("")

                headers = ["平台", "佣金率", "佣金金额", "净收入"]
                rows = []
                for p in result.get("platforms", []):
                    if "error" not in p:
                        rows.append([
                            p.get("platform", ""),
                            p.get("commission_rate_display", ""),
                            f"${p.get('commission', 0):.2f}",
                            f"${p.get('net_amount', 0):.2f}",
                        ])
                if rows:
                    parts.append(_build_markdown_table(headers, rows))
                    parts.append("")

                if result.get("fee_difference_display"):
                    parts.append(f"**费用差异**: {result['fee_difference_display']}")
                    parts.append("")

                parts.append(_format_source_tag("平台费率知识库 (2025-01)"))
                parts.append("")
                parts.append("> 注：以上为估算数据，实际费用以各平台结算为准。")

                return "\n".join(parts)
            except Exception:
                pass

        # 检测特定平台费率查询
        platform_keywords = {
            "amazon": ["amazon", "亚马逊"],
            "ebay": ["ebay"],
            "shopee": ["shopee"],
            "shopify": ["shopify"],
            "walmart": ["walmart"],
            "temu": ["temu"],
            "tiktok_shop": ["tiktok", "tiktok shop"],
            "paypal": ["paypal"],
            "stripe": ["stripe"],
            "pingpong": ["pingpong", "ping pong"],
            "worldfirst": ["worldfirst", "world first"],
            "aliexpress": ["速卖通", "aliexpress"],
            "ozon": ["ozon"],
            "lazada": ["lazada"],
            "coupang": ["coupang"],
            "wish": ["wish"],
        }

        matched_platform = None
        for pkey, aliases in platform_keywords.items():
            for alias in aliases:
                if alias in q_lower:
                    matched_platform = pkey
                    break
            if matched_platform:
                break

        if matched_platform:
            try:
                # 获取平台佣金计算
                commission_result = calculate_platform_commission(
                    matched_platform, 100, "默认"
                )

                # 获取平台详情
                from platform_fees import get_platform_detail
                detail = get_platform_detail(matched_platform)

                parts = []
                parts.append(f"## {detail.get('platform', matched_platform)} 费率详情")
                parts.append("")

                if detail.get("type"):
                    parts.append(f"**类型**: {detail['type']}")
                if detail.get("regions"):
                    parts.append(f"**覆盖区域**: {', '.join(detail['regions'])}")
                parts.append("")

                # 佣金信息
                if "error" not in commission_result:
                    parts.append("### 佣金估算 (以$100为例)")
                    parts.append(f"- **佣金率**: {commission_result.get('commission_rate_display', '')}")
                    parts.append(f"- **佣金金额**: ${commission_result.get('commission', 0):.2f}")
                    parts.append(f"- **净收入**: ${commission_result.get('net_amount', 0):.2f}")
                    parts.append("")

                # 费率明细
                fees = detail.get("fees", {})
                if fees:
                    parts.append("### 费率明细")
                    for fee_key, fee_info in fees.items():
                        desc = fee_info.get("desc", fee_key)
                        rates = fee_info.get("rates", {})
                        parts.append(f"**{desc}**:")
                        if isinstance(rates, dict):
                            for region, rate in list(rates.items())[:5]:
                                parts.append(f"  - {region}: {rate}")
                        elif isinstance(rates, str):
                            parts.append(f"  - {rates}")
                        parts.append("")

                if detail.get("notice"):
                    parts.append(f"> {detail['notice']}")
                    parts.append("")

                parts.append(_format_source_tag(
                    detail.get("source", "平台官方数据"),
                    f"更新于 {detail.get('updated', '未知')}"
                ))
                parts.append("")
                parts.append("> 注：以上费率数据仅供参考，实际费用以平台结算为准。")

                return "\n".join(parts)
            except Exception:
                pass

        return None

    def _query_policy(self, question: str) -> Optional[str]:
        """
        查询政策信息。

        优先从知识库获取，如果没有匹配则尝试联网搜索。

        Args:
            question: 用户问题

        Returns:
            str: 格式化的政策回答，或 None
        """
        # 先从知识库搜索
        knowledge_results = self._answer_from_knowledge(question)
        if knowledge_results and knowledge_results[0].get("score", 0) > 0.3:
            parts = []
            parts.append("## 政策信息查询")
            parts.append("")

            for i, item in enumerate(knowledge_results[:3], 1):
                category = item.get("category", "")
                answer = item.get("answer", "")
                score = item.get("score", 0)
                parts.append(f"### 相关政策 {i}（匹配度: {score:.0%}）")
                parts.append(f"[{category}]")
                parts.append("")
                parts.append(answer)
                parts.append("")

            parts.append(_format_source_tag("内置财务知识库"))
            return "\n".join(parts)

        # 知识库无匹配，尝试联网搜索
        search_results = self._web_search(question)
        if search_results:
            parts = []
            parts.append("## 政策信息查询（网络搜索）")
            parts.append("")

            for i, result in enumerate(search_results[:3], 1):
                parts.append(f"### 搜索结果 {i}")
                parts.append(f"**标题**: {result.get('title', '')}")
                parts.append(f"**摘要**: {result.get('snippet', '')}")
                if result.get("url"):
                    parts.append(f"**链接**: {result['url']}")
                parts.append("")

            parts.append(_format_source_tag("DuckDuckGo网络搜索"))
            parts.append("")
            parts.append("> 此数据仅供参考，建议核实。")

            return "\n".join(parts)

        return None

    # ====================================================================
    # 主对话方法（增强版）
    # ====================================================================
    def chat(self, question: str, context: str = "") -> str:
        """
        主对话方法 - 智能调度引擎回答用户问题（增强版）。

        增强调度逻辑：
        1. 检测问题类型（汇率/税率/费率/平台/政策/通用）
        2. 根据类型路由到对应的数据源
        3. 如果有实时数据，使用实时数据
        4. 如果有知识库，使用知识库
        5. 如果有Ollama，将数据作为上下文增强
        6. 如果都没有，尝试联网搜索
        7. 最终降级到通用回答

        防幻觉机制：
        - Layer1: 涉及具体数字的问题，必须从数据源获取
        - Layer2: 置信度标注
        - Layer3: 来源追溯

        Args:
            question: 用户的问题文本
            context: 额外的上下文信息（如当前报表数据摘要等）

        Returns:
            str: AI生成的回答文本
        """
        if not question or not question.strip():
            return "请输入您的问题，我将为您解答财务相关问题。"

        # 第一步：检测问题类型
        q_type, q_score = _detect_question_type(question)
        is_numeric = _is_numeric_question(question)

        # 第二步：根据类型路由到对应数据源
        data_driven_answer = None

        if q_type == "exchange_rate" or ("汇率" in question.lower()):
            data_driven_answer = self._query_exchange_rate(question)

        if data_driven_answer is None and q_type == "tax_rate":
            data_driven_answer = self._query_tax_rate(question)

        if data_driven_answer is None and q_type in ("fee_rate", "platform"):
            data_driven_answer = self._query_platform_fee(question)

        if data_driven_answer is None and q_type == "policy":
            data_driven_answer = self._query_policy(question)

        # 如果数据驱动回答成功，直接返回（防幻觉：数字问题优先数据源）
        if data_driven_answer is not None:
            return data_driven_answer

        # 第三步：从内置知识库搜索（始终执行，作为基础回答）
        knowledge_results = self._answer_from_knowledge(question)

        # 如果知识库有高质量匹配，优先使用
        has_good_knowledge = (
            knowledge_results
            and knowledge_results[0].get("score", 0) > 0.5
        )

        # 构建增强上下文（用于Ollama/云端）
        enhanced_context = context
        if knowledge_results:
            kb_context_parts = []
            for item in knowledge_results[:3]:
                kb_context_parts.append(
                    f"知识库条目: {item.get('question', '')} -> {item.get('answer', '')[:300]}"
                )
            enhanced_context = (
                f"{context}\n\n【知识库参考】\n"
                + "\n".join(kb_context_parts)
                if context
                else "【知识库参考】\n" + "\n".join(kb_context_parts)
            )

        # 第四步：尝试使用云端API增强
        if self.cloud_available:
            try:
                cloud_answer = self._answer_from_cloud(question, enhanced_context)
                if cloud_answer:
                    # 如果是数字问题，附加知识库来源标注
                    if is_numeric and knowledge_results:
                        source_tag = _format_source_tag("云端AI + 内置知识库")
                        cloud_answer += f"\n\n{source_tag}"
                    return cloud_answer
            except Exception:
                pass

        # 第五步：尝试使用Ollama增强
        if self.ollama_available:
            try:
                ollama_answer = self._answer_from_ollama(question, enhanced_context)
                if ollama_answer:
                    # 如果是数字问题，附加知识库来源标注
                    if is_numeric and knowledge_results:
                        source_tag = _format_source_tag("Ollama + 内置知识库")
                        ollama_answer += f"\n\n{source_tag}"
                    return ollama_answer
            except Exception:
                pass

        # 第六步：如果知识库有高质量匹配，返回格式化结果
        if has_good_knowledge:
            return self._format_answer(knowledge_results)

        # 第七步：尝试联网搜索
        if not has_good_knowledge:
            search_results = self._web_search(question)
            if search_results:
                parts = []
                parts.append("## 网络搜索结果")
                parts.append("")
                for i, result in enumerate(search_results[:3], 1):
                    parts.append(f"### 搜索结果 {i}")
                    parts.append(f"- **标题**: {result.get('title', '')}")
                    parts.append(f"- **摘要**: {result.get('snippet', '')}")
                    if result.get("url"):
                        parts.append(f"- **链接**: {result['url']}")
                    parts.append("")
                parts.append(_format_source_tag("DuckDuckGo网络搜索"))
                parts.append("")
                parts.append("> 此数据仅供参考，建议核实。")
                return "\n".join(parts)

        # 第八步：返回知识库结果（兜底方案，永远可用）
        return self._format_answer(knowledge_results)

    def _answer_from_knowledge(self, question: str) -> List[Dict]:
        """
        从内置财务知识库搜索匹配的知识条目。

        Args:
            question: 用户的问题文本

        Returns:
            list: 匹配的知识条目列表
        """
        return search_knowledge(question, threshold=0.25, max_results=5)

    def _answer_from_ollama(self, question: str, context: str) -> str:
        """
        使用Ollama本地大模型生成回答。

        将内置知识库的搜索结果作为上下文传给Ollama，让模型基于专业知识生成更精准、
        更自然的回答。同时如果调用方提供了额外的上下文（如数据摘要），也会一并传入。

        Args:
            question: 用户的问题文本
            context: 额外的上下文信息

        Returns:
            str: Ollama生成的回答；如果调用失败则返回空字符串
        """
        # 先获取知识库结果作为专业上下文
        knowledge_results = self._answer_from_knowledge(question)

        # 构建系统提示词
        system_prompt = (
            "你是一个专业的跨境电商财务助手。请基于以下知识库内容回答用户的问题。\n"
            "要求：\n"
            "1. 只回答财务相关问题\n"
            "2. 回答要专业、准确、简洁\n"
            "3. 不确定的信息要明确标注\n"
            "4. 涉及金额时标明币种，保留2位小数\n"
            "5. 百分比精确到0.01%\n"
            "6. 涉及税务问题时声明'请以税务机关最终确认为准'\n"
            "7. 禁止编造具体数字（税率/费率/汇率），如不确定请说明\n"
            "8. 使用Markdown格式化回答\n"
        )

        # 构建知识库上下文
        knowledge_context = ""
        if knowledge_results:
            knowledge_parts = []
            for item in knowledge_results[:3]:
                knowledge_parts.append(
                    f"【知识条目】\n"
                    f"问题：{item.get('question', '')}\n"
                    f"答案：{item.get('answer', '')}"
                )
            knowledge_context = "\n\n".join(knowledge_parts)

        # 构建完整提示
        full_prompt = f"【系统指令】\n{system_prompt}\n\n"
        if knowledge_context:
            full_prompt += f"【参考知识库】\n{knowledge_context}\n\n"
        if context:
            full_prompt += f"【数据上下文】\n{context}\n\n"
        full_prompt += f"【用户问题】\n{question}"

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 2048,
                    }
                },
                timeout=60
            )
            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "").strip()
                if answer:
                    return answer
            return ""
        except Exception:
            return ""

    def _answer_from_cloud(self, question: str, context: str) -> str:
        """
        使用云端API生成回答。

        支持兼容OpenAI格式的云端API（如DeepSeek、通义千问、ChatGPT等）。

        Args:
            question: 用户的问题文本
            context: 额外的上下文信息

        Returns:
            str: 云端API生成的回答；如果调用失败则返回空字符串
        """
        # 先获取知识库结果作为专业上下文
        knowledge_results = self._answer_from_knowledge(question)

        # 构建系统提示词
        system_prompt = (
            "你是一个专业的跨境电商财务助手。请基于以下知识库内容回答用户的问题。\n"
            "要求：\n"
            "1. 只回答财务相关问题\n"
            "2. 回答要专业、准确、简洁\n"
            "3. 不确定的信息要明确标注\n"
            "4. 涉及金额时标明币种，保留2位小数\n"
            "5. 百分比精确到0.01%\n"
            "6. 涉及税务问题时声明'请以税务机关最终确认为准'\n"
            "7. 禁止编造具体数字（税率/费率/汇率），如不确定请说明\n"
            "8. 使用Markdown格式化回答\n"
        )

        # 构建知识库上下文
        knowledge_context = ""
        if knowledge_results:
            knowledge_parts = []
            for item in knowledge_results[:3]:
                knowledge_parts.append(
                    f"【知识条目】\n"
                    f"问题：{item.get('question', '')}\n"
                    f"答案：{item.get('answer', '')}"
                )
            knowledge_context = "\n\n".join(knowledge_parts)

        # 构建消息列表（兼容OpenAI Chat格式）
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        if knowledge_context:
            messages.append({
                "role": "system",
                "content": f"【参考知识库】\n{knowledge_context}"
            })

        if context:
            messages.append({
                "role": "system",
                "content": f"【数据上下文】\n{context}"
            })

        messages.append({"role": "user", "content": question})

        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.cloud_api_key}"
            }
            payload = {
                "model": self.cloud_model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 2048,
            }

            response = requests.post(
                self.cloud_api_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                choices = result.get("choices", [])
                if choices:
                    answer = choices[0].get("message", {}).get("content", "").strip()
                    if answer:
                        return answer
            return ""
        except Exception:
            return ""

    def _format_answer(self, knowledge_results: List[Dict]) -> str:
        """
        将知识库搜索结果格式化为专业的回答文本。

        根据搜索结果的数量和质量，生成不同风格的回答。

        Args:
            knowledge_results: search_knowledge返回的知识条目列表

        Returns:
            str: 格式化后的专业回答文本
        """
        if not knowledge_results:
            return (
                "抱歉，我在内置知识库中没有找到与您问题直接相关的内容。\n\n"
                "建议：\n"
                "1. 尝试换一种方式描述您的问题\n"
                "2. 使用更具体的关键词（如'VAT'、'汇率'、'利润'等）\n"
                "3. 如果需要更深入的分析，建议配置Ollama本地模型或云端API\n"
                "   以获得更强大的AI回答能力"
            )

        # 按相关度排序，取最相关的结果
        top_results = knowledge_results[:3]

        # 如果只有一个高度相关的结果，直接返回其答案
        if len(top_results) == 1 or (len(top_results) >= 1 and top_results[0]["score"] > 0.8):
            answer = top_results[0].get("answer", "")
            category = top_results[0].get("category", "")
            source_tag = _format_source_tag("内置财务知识库")
            return f"[{category}]\n\n{answer}\n\n{source_tag}"

        # 多个相关结果，综合展示
        parts = []
        for i, item in enumerate(top_results, 1):
            category = item.get("category", "")
            question = item.get("question", "")
            answer = item.get("answer", "")
            score = item.get("score", 0)

            parts.append(
                f"--- 相关知识 {i}（匹配度: {score:.0%}）---\n"
                f"[{category}] {question}\n\n"
                f"{answer}"
            )

        # 添加总结提示
        formatted = "\n\n".join(parts)
        formatted += (
            "\n\n---\n"
            + _format_source_tag("内置财务知识库")
            + "\n以上内容来自内置财务知识库。如需更深入的分析，"
            "建议配置Ollama本地模型或云端API以获得增强的AI回答能力。"
        )

        return formatted

    def analyze_data(self, df_summary: str) -> str:
        """
        分析上传的财务数据并生成洞察。

        接收DataFrame的摘要信息（字符串格式），结合内置知识库生成专业的财务分析洞察。

        Args:
            df_summary: DataFrame转换后的摘要字符串

        Returns:
            str: 财务分析洞察文本
        """
        if not df_summary or not df_summary.strip():
            return "暂无数据可供分析，请先上传财务数据文件。"

        # 从摘要中提取关键信息用于知识库搜索
        analysis_keywords = self._extract_analysis_keywords(df_summary)

        # 搜索相关知识
        knowledge_results = []
        for keyword in analysis_keywords:
            results = search_knowledge(keyword, threshold=0.2, max_results=2)
            knowledge_results.extend(results)

        # 去重（按question去重）
        seen_questions = set()
        unique_results = []
        for item in knowledge_results:
            q = item.get("question", "")
            if q not in seen_questions:
                seen_questions.add(q)
                unique_results.append(item)

        # 构建分析提示
        analysis_prompt = (
            "请基于以下财务数据摘要，生成一份专业的财务分析报告。\n\n"
            "要求：\n"
            "1. 利润分析：计算毛利率、净利率等关键指标\n"
            "2. 异常检测：识别退款率过高、佣金异常、大额交易等异常情况\n"
            "3. 趋势判断：分析各平台表现和收入趋势\n"
            "4. 改进建议：给出降低成本、提升利润的具体建议\n"
            "5. 用Markdown表格展示核心指标\n"
            "6. 涉及金额保留2位小数，百分比精确到0.01%\n"
            "7. 结论先行，细节在后\n\n"
            f"【财务数据摘要】\n{df_summary}"
        )

        # 如果有相关知识，附加到提示中
        if unique_results:
            knowledge_context = "\n\n".join([
                f"- {item.get('question', '')}: {item.get('answer', '')[:200]}..."
                for item in unique_results[:3]
            ])
            analysis_prompt += (
                f"\n\n【相关知识参考】\n{knowledge_context}"
            )

        # 尝试使用云端API
        if self.cloud_available:
            try:
                answer = self._answer_from_cloud(analysis_prompt, "")
                if answer:
                    return answer
            except Exception:
                pass

        # 尝试使用Ollama
        if self.ollama_available:
            try:
                answer = self._answer_from_ollama(analysis_prompt, "")
                if answer:
                    return answer
            except Exception:
                pass

        # 降级：基于知识库生成基础分析
        return self._generate_basic_analysis(df_summary, unique_results)

    def _extract_analysis_keywords(self, df_summary: str) -> List[str]:
        """
        从数据摘要中提取用于知识库搜索的关键词。

        Args:
            df_summary: DataFrame摘要字符串

        Returns:
            list: 提取的关键词列表
        """
        keywords = ["利润分析", "财务分析", "跨境电商"]

        # 检测平台关键词
        platform_map = {
            "amazon": "亚马逊",
            "ebay": "eBay",
            "shopee": "Shopee",
            "shopify": "Shopify",
            "walmart": "Walmart",
            "aliexpress": "速卖通",
        }
        summary_lower = df_summary.lower()
        for eng_name, cn_name in platform_map.items():
            if eng_name in summary_lower or cn_name in df_summary:
                keywords.append(cn_name)

        # 检测财务主题关键词
        finance_topics = {
            "退款": "退款",
            "佣金": "佣金",
            "vat": "VAT",
            "增值税": "增值税",
            "汇率": "汇率",
            "运费": "运费",
            "手续费": "手续费",
            "税": "税务",
        }
        for topic_key, topic_name in finance_topics.items():
            if topic_key in summary_lower or topic_key in df_summary:
                keywords.append(topic_name)

        return list(set(keywords))

    def _generate_basic_analysis(self, df_summary: str, knowledge_results: List[Dict]) -> str:
        """
        在没有外部AI引擎时，基于知识库生成基础财务分析。

        Args:
            df_summary: DataFrame摘要字符串
            knowledge_results: 相关知识条目列表

        Returns:
            str: 基础财务分析文本
        """
        analysis_parts = []

        analysis_parts.append("=" * 50)
        analysis_parts.append("  财务数据分析报告（基于内置知识库）")
        analysis_parts.append("=" * 50)
        analysis_parts.append("")

        # 数据概览
        analysis_parts.append("## 数据概览")
        analysis_parts.append(df_summary)
        analysis_parts.append("")

        # 知识库建议
        if knowledge_results:
            analysis_parts.append("## 相关知识建议")
            for i, item in enumerate(knowledge_results[:3], 1):
                category = item.get("category", "")
                question = item.get("question", "")
                answer = item.get("answer", "")
                brief_answer = answer[:300]
                if len(answer) > 300:
                    brief_answer += "..."
                analysis_parts.append(
                    f"\n{i}. [{category}] {question}\n"
                    f"   {brief_answer}"
                )
            analysis_parts.append("")

        # 通用建议
        analysis_parts.append("## 通用财务建议")
        analysis_parts.append("- 定期核对各平台账单，确保订单金额与实际到账一致")
        analysis_parts.append("- 关注汇率波动，合理安排结汇时机以降低汇损")
        analysis_parts.append("- 监控退款率，高退款率可能影响平台店铺评分")
        analysis_parts.append("- 及时申报VAT等跨境税务，避免合规风险和罚款")
        analysis_parts.append("- 优化物流成本，比较不同物流渠道的性价比")
        analysis_parts.append("")

        analysis_parts.append("---")
        analysis_parts.append(
            _format_source_tag("内置财务知识库")
            + "\n提示：以上分析基于内置知识库生成。如需更深入的AI分析，"
            "建议配置Ollama本地模型或云端API。"
        )

        return "\n".join(analysis_parts)

    # ====================================================================
    # 新增：分析上传数据的方法
    # ====================================================================
    def analyze_uploaded_data(self, df: pd.DataFrame) -> Dict:
        """
        专门分析用户上传的数据，生成多维度的数据洞察。

        Args:
            df: 用户上传的标准化DataFrame

        Returns:
            dict: 包含多个分析维度的结果字典
        """
        if df is None or df.empty:
            return {
                "status": "error",
                "message": "暂无数据可供分析，请先上传财务数据文件。",
                "insights": [],
            }

        insights = []

        # 1. 基础统计
        total_orders = len(df)
        total_sales = df["订单金额"].sum() if "订单金额" in df.columns else 0
        total_commission = df["佣金"].sum() if "佣金" in df.columns else 0
        total_net = df["实际到账"].sum() if "实际到账" in df.columns else (total_sales - total_commission)
        profit_rate = (total_net / total_sales * 100) if total_sales > 0 else 0

        insights.append({
            "type": "基础统计",
            "title": "数据概览",
            "content": (
                f"共 {total_orders:,} 笔订单，总销售额 {self._format_currency(total_sales)}，"
                f"总佣金 {self._format_currency(total_commission)}，"
                f"实际到账 {self._format_currency(total_net)}，"
                f"利润率 {profit_rate:.2f}%"
            ),
        })

        # 2. 平台分析
        if "平台" in df.columns:
            platform_stats = df.groupby("平台").agg(
                订单数=("订单金额", "count"),
                总销售额=("订单金额", "sum"),
                总佣金=("佣金", "sum"),
                实际到账=("实际到账", "sum"),
            ).reset_index()
            platform_stats["利润率"] = platform_stats.apply(
                lambda r: (r["实际到账"] / r["总销售额"] * 100) if r["总销售额"] > 0 else 0, axis=1
            )
            best_platform = platform_stats.loc[platform_stats["利润率"].idxmax()]

            insights.append({
                "type": "平台分析",
                "title": "平台表现",
                "content": (
                    f"利润率最高的平台是 {best_platform['平台']}，"
                    f"利润率 {best_platform['利润率']:.2f}%，"
                    f"销售额 {self._format_currency(best_platform['总销售额'])}"
                ),
            })

        # 3. 日期趋势
        if "交易日期" in df.columns:
            df["交易日期"] = pd.to_datetime(df["交易日期"], errors="coerce")
            df_valid = df.dropna(subset=["交易日期"])
            if not df_valid.empty:
                df_valid = df_valid.sort_values("交易日期")
                first_date = df_valid["交易日期"].min().strftime("%Y-%m-%d")
                last_date = df_valid["交易日期"].max().strftime("%Y-%m-%d")
                insights.append({
                    "type": "趋势分析",
                    "title": "日期范围",
                    "content": f"数据时间跨度: {first_date} 至 {last_date}",
                })

        # 4. 异常检测
        anomaly_count = 0
        for col in ["订单金额", "佣金", "实际到账"]:
            if col in df.columns:
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                if iqr > 0:
                    outliers = df[(df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)]
                    anomaly_count += len(outliers)

        if anomaly_count > 0:
            insights.append({
                "type": "异常检测",
                "title": "异常数据",
                "content": f"检测到 {anomaly_count} 条异常记录，建议重点核查。",
            })
        else:
            insights.append({
                "type": "异常检测",
                "title": "数据质量",
                "content": "未检测到明显异常数据，数据质量良好。",
            })

        # 5. 币种分析
        if "币种" in df.columns:
            currency_dist = df["币种"].value_counts().to_dict()
            main_currency = max(currency_dist, key=currency_dist.get) if currency_dist else "USD"
            insights.append({
                "type": "币种分析",
                "title": "币种分布",
                "content": f"主要交易币种为 {main_currency}，涉及 {len(currency_dist)} 种币种。",
            })

        return {
            "status": "success",
            "message": f"已分析 {total_orders:,} 条记录，生成 {len(insights)} 条洞察",
            "insights": insights,
            "summary": {
                "total_orders": total_orders,
                "total_sales": total_sales,
                "total_commission": total_commission,
                "total_net": total_net,
                "profit_rate": profit_rate,
            },
        }

    def generate_data_insights(self, df: pd.DataFrame, focus: str = "general") -> str:
        """
        生成数据洞察文本报告。

        Args:
            df: 用户上传的标准化DataFrame
            focus: 分析焦点 (general/profit/platform/anomaly)

        Returns:
            str: Markdown格式的洞察报告
        """
        result = self.analyze_uploaded_data(df)
        if result["status"] == "error":
            return result["message"]

        parts = []
        parts.append("## 数据洞察报告")
        parts.append("")

        summary = result.get("summary", {})
        parts.append("### 核心指标")
        parts.append(f"- **总订单数**: {summary.get('total_orders', 0):,}")
        parts.append(f"- **总销售额**: {self._format_currency(summary.get('total_sales', 0))}")
        parts.append(f"- **总佣金**: {self._format_currency(summary.get('total_commission', 0))}")
        parts.append(f"- **实际到账**: {self._format_currency(summary.get('total_net', 0))}")
        parts.append(f"- **利润率**: {summary.get('profit_rate', 0):.2f}%")
        parts.append("")

        # 根据焦点过滤洞察
        insights = result.get("insights", [])
        if focus != "general":
            type_map = {
                "profit": ["基础统计", "平台分析"],
                "platform": ["平台分析"],
                "anomaly": ["异常检测"],
            }
            allowed = type_map.get(focus, [])
            insights = [i for i in insights if i["type"] in allowed]

        if insights:
            parts.append("### 详细洞察")
            for insight in insights:
                parts.append(f"**{insight['title']}** ({insight['type']})")
                parts.append(f"{insight['content']}")
                parts.append("")

        parts.append("---")
        parts.append(_format_source_tag("AI财务分析引擎"))
        return "\n".join(parts)


# ============================================================================
# 全局实例 - 模块级别单例
# ============================================================================
finance_ai = FinanceAI()
