# -*- coding: utf-8 -*-
"""
跨境电商财务智能体 - 实时数据更新模块
联网状态下自动获取最新汇率、税率、政策数据
支持离线缓存与自动更新调度
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import requests

# ---------------------------------------------------------------------------
# 日志
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
CACHE_DIR = os.path.join("data", "cache")
EXCHANGE_RATE_CACHE_FILE = os.path.join(CACHE_DIR, "exchange_rates.json")
POLICY_CACHE_FILE = os.path.join(CACHE_DIR, "policy_updates.json")

# 汇率 API 列表（按优先级排序）
EXCHANGE_RATE_APIS = [
    {
        "name": "open.er-api.com",
        "url": "https://open.er-api.com/v6/latest/USD",
        "timeout": 5,
    },
    {
        "name": "exchangerate.host",
        "url": "https://api.exchangerate.host/latest",
        "timeout": 5,
    },
]

# 支持 20+ 货币
SUPPORTED_CURRENCIES = [
    "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "SGD", "HKD",
    "KRW", "THB", "INR", "MYR", "PHP", "IDR", "VND", "RUB", "BRL",
    "MXN", "NZD",
]

# 缓存默认有效期（秒）
DEFAULT_CACHE_MAX_AGE = 30 * 60  # 30 分钟

# ---------------------------------------------------------------------------
# 各国 VAT 税率（2024-2025 年最新）
# ---------------------------------------------------------------------------
VAT_RATES = {
    "英国": {
        "standard_rate": 0.20,
        "reduced_rate": 0.05,
        "country_code": "GB",
        "effective_date": "2024-01-01",
    },
    "德国": {
        "standard_rate": 0.19,
        "reduced_rate": 0.07,
        "country_code": "DE",
        "effective_date": "2024-01-01",
    },
    "法国": {
        "standard_rate": 0.20,
        "reduced_rate": 0.055,
        "country_code": "FR",
        "effective_date": "2024-01-01",
    },
    "意大利": {
        "standard_rate": 0.22,
        "reduced_rate": 0.10,
        "country_code": "IT",
        "effective_date": "2024-01-01",
    },
    "西班牙": {
        "standard_rate": 0.21,
        "reduced_rate": 0.10,
        "country_code": "ES",
        "effective_date": "2024-01-01",
    },
    "荷兰": {
        "standard_rate": 0.21,
        "reduced_rate": 0.09,
        "country_code": "NL",
        "effective_date": "2024-01-01",
    },
    "波兰": {
        "standard_rate": 0.23,
        "reduced_rate": 0.08,
        "country_code": "PL",
        "effective_date": "2024-01-01",
    },
    "比利时": {
        "standard_rate": 0.21,
        "reduced_rate": 0.12,
        "country_code": "BE",
        "effective_date": "2024-01-01",
    },
    "瑞典": {
        "standard_rate": 0.25,
        "reduced_rate": 0.12,
        "country_code": "SE",
        "effective_date": "2024-01-01",
    },
    "奥地利": {
        "standard_rate": 0.20,
        "reduced_rate": 0.10,
        "country_code": "AT",
        "effective_date": "2024-01-01",
    },
    "日本": {
        "standard_rate": 0.10,
        "reduced_rate": 0.08,
        "country_code": "JP",
        "effective_date": "2024-01-01",
    },
    "澳大利亚": {
        "standard_rate": 0.10,
        "reduced_rate": 0.0,
        "country_code": "AU",
        "effective_date": "2024-01-01",
    },
    "加拿大": {
        "standard_rate": 0.05,
        "reduced_rate": 0.0,
        "country_code": "CA",
        "effective_date": "2024-01-01",
        "note": "GST 联邦税率，各省另有 PST",
    },
}

# ---------------------------------------------------------------------------
# 美国各州销售税（主要州）
# ---------------------------------------------------------------------------
US_SALES_TAX = {
    "Alabama": 0.04,
    "Alaska": 0.00,
    "Arizona": 0.056,
    "Arkansas": 0.065,
    "California": 0.0725,
    "Colorado": 0.029,
    "Connecticut": 0.0635,
    "Delaware": 0.00,
    "Florida": 0.06,
    "Georgia": 0.04,
    "Hawaii": 0.04,
    "Idaho": 0.06,
    "Illinois": 0.0625,
    "Indiana": 0.07,
    "Iowa": 0.06,
    "Kansas": 0.065,
    "Kentucky": 0.06,
    "Louisiana": 0.0445,
    "Maine": 0.055,
    "Maryland": 0.06,
    "Massachusetts": 0.0625,
    "Michigan": 0.06,
    "Minnesota": 0.06875,
    "Mississippi": 0.07,
    "Missouri": 0.04225,
    "Montana": 0.00,
    "Nebraska": 0.055,
    "Nevada": 0.0685,
    "New Hampshire": 0.00,
    "New Jersey": 0.06625,
    "New Mexico": 0.05125,
    "New York": 0.04,
    "North Carolina": 0.0475,
    "North Dakota": 0.05,
    "Ohio": 0.0575,
    "Oklahoma": 0.045,
    "Oregon": 0.00,
    "Pennsylvania": 0.06,
    "Rhode Island": 0.07,
    "South Carolina": 0.06,
    "South Dakota": 0.045,
    "Tennessee": 0.07,
    "Texas": 0.0625,
    "Utah": 0.047,
    "Vermont": 0.06,
    "Virginia": 0.053,
    "Washington": 0.065,
    "West Virginia": 0.06,
    "Wisconsin": 0.05,
    "Wyoming": 0.04,
    "District of Columbia": 0.06,
}

# ---------------------------------------------------------------------------
# 中国税率
# ---------------------------------------------------------------------------
CHINA_TAX_RATES = {
    "增值税": {
        "一般纳税人": {
            "标准税率": 0.13,
            "适用范围": "货物销售、进口货物、提供加工修理修配劳务",
        },
        "低税率": {
            "税率": 0.09,
            "适用范围": "交通运输、邮政、基础电信、建筑、不动产租赁、销售不动产、转让土地使用权",
        },
        "服务业税率": {
            "税率": 0.06,
            "适用范围": "现代服务（研发技术、信息技术、文化创意、物流辅助、鉴证咨询、广播影视、商务辅助）、金融服务、生活服务、增值电信服务",
        },
        "小规模纳税人": {
            "税率": 0.03,
            "适用范围": "年应征增值税销售额 500 万元以下",
            "note": "2024 年优惠政策：月销售额 10 万以下免征增值税",
        },
    },
    "企业所得税": {
        "标准税率": 0.25,
        "小型微利企业": 0.05,  # 2024 年优惠
        "高新技术企业": 0.15,
        "技术先进型服务企业": 0.15,
    },
    "个人所得税": {
        "综合所得": {
            "税率": "3%-45% 七级超额累进",
            "起征点": 5000,  # 元/月
        },
        "经营所得": {
            "税率": "5%-35% 五级超额累进",
        },
    },
    "关税": {
        "最惠国税率": "0%-65% 不等",
        "普通税率": "0%-270% 不等",
        "跨境电商": {
            "单次交易限值": "5000 元人民币",
            "年度交易限值": "26000 元人民币",
            "关税": "限值以内免征",
            "进口环节增值税": "按法定应纳税额 70% 征收",
            "消费税": "按法定应纳税额 70% 征收",
        },
    },
}


# ===========================================================================
# 数据缓存管理类
# ===========================================================================
class DataCache:
    """管理所有缓存数据"""

    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    # ---- 内部工具方法 ----
    def _cache_path(self, data_type: str) -> str:
        """根据 data_type 返回缓存文件路径"""
        return os.path.join(self.cache_dir, f"{data_type}.json")

    # ---- 公开接口 ----
    def save_cache(self, data_type: str, data: Any) -> None:
        """
        保存缓存

        Args:
            data_type: 数据类型标识（如 'exchange_rates', 'policy_updates'）
            data: 要缓存的数据（需可 JSON 序列化）
        """
        cache_entry = {
            "data": data,
            "updated_at": datetime.now().isoformat(),
            "timestamp": time.time(),
        }
        path = self._cache_path(data_type)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cache_entry, f, ensure_ascii=False, indent=2)
            logger.info(f"缓存已保存: {data_type} -> {path}")
        except Exception as e:
            logger.error(f"保存缓存失败 [{data_type}]: {e}")

    def load_cache(self, data_type: str) -> Optional[Any]:
        """
        加载缓存数据

        Args:
            data_type: 数据类型标识

        Returns:
            缓存的数据，如果不存在或损坏则返回 None
        """
        path = self._cache_path(data_type)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                entry = json.load(f)
            return entry.get("data")
        except Exception as e:
            logger.error(f"加载缓存失败 [{data_type}]: {e}")
            return None

    def load_cache_with_meta(self, data_type: str) -> Optional[Dict]:
        """
        加载缓存数据及其元信息

        Returns:
            包含 'data', 'updated_at', 'timestamp' 的字典，不存在则返回 None
        """
        path = self._cache_path(data_type)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载缓存（含元信息）失败 [{data_type}]: {e}")
            return None

    def is_cache_expired(self, data_type: str, max_age_seconds: float = DEFAULT_CACHE_MAX_AGE) -> bool:
        """
        检查缓存是否过期

        Args:
            data_type: 数据类型标识
            max_age_seconds: 最大有效期（秒）

        Returns:
            True 表示缓存已过期或不存在
        """
        entry = self.load_cache_with_meta(data_type)
        if entry is None:
            return True
        ts = entry.get("timestamp", 0)
        return (time.time() - ts) > max_age_seconds

    def get_cache_info(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有缓存的状态信息

        Returns:
            {data_type: {"exists": bool, "updated_at": str, "expired": bool, "age_seconds": float}}
        """
        result = {}
        known_types = ["exchange_rates", "policy_updates"]
        # 同时扫描缓存目录中所有 .json 文件
        if os.path.isdir(self.cache_dir):
            for fname in os.listdir(self.cache_dir):
                if fname.endswith(".json"):
                    dt = fname[:-5]
                    if dt not in known_types:
                        known_types.append(dt)
        for dt in known_types:
            entry = self.load_cache_with_meta(dt)
            if entry is None:
                result[dt] = {
                    "exists": False,
                    "updated_at": None,
                    "expired": True,
                    "age_seconds": None,
                }
            else:
                age = time.time() - entry.get("timestamp", 0)
                result[dt] = {
                    "exists": True,
                    "updated_at": entry.get("updated_at"),
                    "expired": age > DEFAULT_CACHE_MAX_AGE,
                    "age_seconds": round(age, 1),
                }
        return result


# ===========================================================================
# 全局缓存实例
# ===========================================================================
_cache = DataCache()


# ===========================================================================
# 网络状态检测
# ===========================================================================
def check_network() -> bool:
    """
    检测网络是否可用

    通过请求一个轻量级端点来判断网络连通性。

    Returns:
        True 表示网络可用
    """
    test_urls = [
        "https://www.google.com",
        "https://www.baidu.com",
        "https://1.1.1.1",
    ]
    for url in test_urls:
        try:
            resp = requests.get(url, timeout=3, allow_redirects=False)
            if resp.status_code < 500:
                return True
        except Exception:
            continue
    return False


# ===========================================================================
# 汇率实时获取
# ===========================================================================
def get_exchange_rates() -> Dict[str, Any]:
    """
    从多个免费 API 获取实时汇率

    优先使用 open.er-api.com，失败后回退到 exchangerate.host。
    如果所有 API 均不可用，使用上一次缓存的数据。

    Returns:
        {
            "rates": {currency: rate, ...},   # 以 USD 为基准
            "base": "USD",
            "updated_at": str,
            "source": str,                     # API 名称 或 "cache"
            "is_cached": bool,
        }
    """
    # 1) 尝试从 API 获取
    for api_info in EXCHANGE_RATE_APIS:
        try:
            resp = requests.get(
                api_info["url"],
                timeout=api_info["timeout"],
            )
            resp.raise_for_status()
            payload = resp.json()

            raw_rates = payload.get("rates", {})
            base = payload.get("base", "USD")

            # 只保留支持的货币
            rates = {c: raw_rates.get(c) for c in SUPPORTED_CURRENCIES if c in raw_rates}

            now = datetime.now().isoformat()
            result = {
                "rates": rates,
                "base": base,
                "updated_at": now,
                "source": api_info["name"],
                "is_cached": False,
            }

            # 写入缓存
            _cache.save_cache("exchange_rates", result)
            logger.info(f"汇率数据获取成功，来源: {api_info['name']}，共 {len(rates)} 种货币")
            return result

        except Exception as e:
            logger.warning(f"汇率 API [{api_info['name']}] 请求失败: {e}")
            continue

    # 2) 所有 API 失败，尝试加载缓存
    logger.warning("所有汇率 API 均不可用，尝试加载缓存数据")
    cached = _cache.load_cache("exchange_rates")
    if cached is not None:
        cached["is_cached"] = True
        cached["source"] = "cache"
        logger.info("已加载缓存汇率数据")
        return cached

    # 3) 缓存也没有，返回空结构
    logger.error("无可用汇率数据（API 与缓存均不可用）")
    return {
        "rates": {},
        "base": "USD",
        "updated_at": None,
        "source": "none",
        "is_cached": False,
    }


# ===========================================================================
# 税率数据获取
# ===========================================================================
def get_vat_rates() -> Dict[str, Any]:
    """
    获取各国最新 VAT 税率

    当前使用内置数据（2024-2025），未来可扩展为在线获取。

    Returns:
        {
            "rates": {国家: {standard_rate, reduced_rate, ...}, ...},
            "updated_at": str,
            "source": "builtin",
            "is_cached": False,
        }
    """
    now = datetime.now().isoformat()
    return {
        "rates": VAT_RATES,
        "updated_at": now,
        "source": "builtin",
        "is_cached": False,
    }


def get_china_tax_rates() -> Dict[str, Any]:
    """
    获取中国最新税率

    当前使用内置数据（2024-2025），未来可扩展为在线获取。

    Returns:
        {
            "rates": CHINA_TAX_RATES,
            "updated_at": str,
            "source": "builtin",
            "is_cached": False,
        }
    """
    now = datetime.now().isoformat()
    return {
        "rates": CHINA_TAX_RATES,
        "updated_at": now,
        "source": "builtin",
        "is_cached": False,
    }


def get_us_sales_tax() -> Dict[str, Any]:
    """
    获取美国各州销售税

    当前使用内置数据，未来可扩展为在线获取。

    Returns:
        {
            "rates": {州名: 税率, ...},
            "updated_at": str,
            "source": "builtin",
            "is_cached": False,
        }
    """
    now = datetime.now().isoformat()
    return {
        "rates": US_SALES_TAX,
        "updated_at": now,
        "source": "builtin",
        "is_cached": False,
    }


# ===========================================================================
# 政策新闻获取
# ===========================================================================
def get_policy_updates(keywords: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    获取最新财税政策

    预留接口：未来可接入搜索引擎或新闻 API。
    当前返回缓存数据或空列表。

    Args:
        keywords: 搜索关键词列表（可选）

    Returns:
        {
            "updates": [{title, source, date, summary, url}, ...],
            "updated_at": str,
            "source": str,
            "is_cached": bool,
        }
    """
    # 1) 如果网络可用，尝试在线搜索（预留）
    if check_network():
        try:
            online_result = _fetch_policy_online(keywords)
            if online_result is not None:
                _cache.save_cache("policy_updates", online_result)
                return online_result
        except Exception as e:
            logger.warning(f"在线获取政策更新失败: {e}")

    # 2) 回退到缓存
    cached = _cache.load_cache("policy_updates")
    if cached is not None:
        cached["is_cached"] = True
        cached["source"] = "cache"
        return cached

    # 3) 无缓存，返回空
    return {
        "updates": [],
        "updated_at": datetime.now().isoformat(),
        "source": "none",
        "is_cached": False,
    }


def _fetch_policy_online(keywords: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """
    在线获取政策更新（预留实现）

    可扩展接入搜索引擎 API、RSS 订阅等。

    Args:
        keywords: 搜索关键词

    Returns:
        政策更新字典，或 None
    """
    # ---- 预留：可在此处接入外部 API ----
    # 示例结构：
    # if keywords:
    #     query = " ".join(keywords)
    #     resp = requests.get("https://api.example.com/search", params={"q": query}, timeout=5)
    #     ...
    #     return {"updates": [...], "updated_at": ..., "source": "online", "is_cached": False}

    logger.info("在线政策获取接口已预留，暂未接入外部数据源")
    return None


# ===========================================================================
# 数据状态总览
# ===========================================================================
def get_data_status() -> Dict[str, Dict[str, Any]]:
    """
    返回各数据源的状态

    Returns:
        {
            "network": bool,
            "exchange_rates": {"status": "online"|"offline"|"cache", ...},
            "vat_rates": {"status": "builtin", ...},
            "china_tax": {"status": "builtin", ...},
            "us_sales_tax": {"status": "builtin", ...},
            "policy_updates": {"status": "online"|"offline"|"cache", ...},
            "cache_info": {...},
        }
    """
    network_ok = check_network()
    cache_info = _cache.get_cache_info()

    # 汇率状态
    er_expired = cache_info.get("exchange_rates", {}).get("expired", True)
    if network_ok:
        er_status = "online"
    elif not er_expired:
        er_status = "cache"
    else:
        er_status = "offline"

    # 政策状态
    pu_expired = cache_info.get("policy_updates", {}).get("expired", True)
    if network_ok:
        pu_status = "online"
    elif not pu_expired:
        pu_status = "cache"
    else:
        pu_status = "offline"

    return {
        "network": network_ok,
        "exchange_rates": {
            "status": er_status,
            "cache_expired": er_expired,
            "cache_updated_at": cache_info.get("exchange_rates", {}).get("updated_at"),
        },
        "vat_rates": {
            "status": "builtin",
            "cache_expired": False,
        },
        "china_tax": {
            "status": "builtin",
            "cache_expired": False,
        },
        "us_sales_tax": {
            "status": "builtin",
            "cache_expired": False,
        },
        "policy_updates": {
            "status": pu_status,
            "cache_expired": pu_expired,
            "cache_updated_at": cache_info.get("policy_updates", {}).get("updated_at"),
        },
        "cache_info": cache_info,
    }


# ===========================================================================
# 自动更新调度
# ===========================================================================
_last_auto_update_time: float = 0.0


def auto_update(interval_seconds: float = DEFAULT_CACHE_MAX_AGE) -> Dict[str, Any]:
    """
    自动检查并更新所有数据

    仅在距上次更新超过 interval_seconds 时才执行实际更新。
    适合在 Streamlit 中每隔一定时间调用。

    Args:
        interval_seconds: 更新间隔（秒），默认 30 分钟

    Returns:
        {
            "executed": bool,           # 是否执行了更新
            "exchange_rates": {...},
            "policy_updates": {...},
            "timestamp": str,
        }
    """
    global _last_auto_update_time

    now = time.time()
    if (now - _last_auto_update_time) < interval_seconds:
        return {
            "executed": False,
            "reason": f"距上次更新仅 {round(now - _last_auto_update_time, 1)} 秒，"
                      f"未达到 {interval_seconds} 秒间隔",
            "timestamp": datetime.now().isoformat(),
        }

    _last_auto_update_time = now
    logger.info("开始自动更新数据...")

    # 更新汇率
    exchange_data = get_exchange_rates()

    # 更新政策
    policy_data = get_policy_updates()

    result = {
        "executed": True,
        "exchange_rates": {
            "source": exchange_data.get("source"),
            "is_cached": exchange_data.get("is_cached", False),
            "currency_count": len(exchange_data.get("rates", {})),
        },
        "policy_updates": {
            "source": policy_data.get("source"),
            "is_cached": policy_data.get("is_cached", False),
            "update_count": len(policy_data.get("updates", [])),
        },
        "timestamp": datetime.now().isoformat(),
    }

    logger.info(f"自动更新完成: 汇率来源={exchange_data.get('source')}, "
                f"政策来源={policy_data.get('source')}")
    return result


# ===========================================================================
# 便捷函数：获取汇率换算值
# ===========================================================================
def convert_currency(amount: float, from_currency: str, to_currency: str) -> Optional[float]:
    """
    使用实时汇率进行货币换算

    Args:
        amount: 金额
        from_currency: 源货币代码
        to_currency: 目标货币代码

    Returns:
        换算后的金额，如果汇率不可用则返回 None
    """
    data = get_exchange_rates()
    rates = data.get("rates", {})
    base = data.get("base", "USD")

    if from_currency == to_currency:
        return amount

    # 先转为基准货币
    if from_currency == base:
        base_amount = amount
    elif from_currency in rates:
        base_amount = amount / rates[from_currency]
    else:
        logger.warning(f"不支持的源货币: {from_currency}")
        return None

    # 再转为目标货币
    if to_currency == base:
        return base_amount
    elif to_currency in rates:
        return round(base_amount * rates[to_currency], 6)
    else:
        logger.warning(f"不支持的目标货币: {to_currency}")
        return None


# ===========================================================================
# 初始化：确保缓存目录存在
# ===========================================================================
os.makedirs(CACHE_DIR, exist_ok=True)
