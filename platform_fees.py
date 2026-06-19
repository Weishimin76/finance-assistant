# -*- coding: utf-8 -*-
"""
平台费率知识库 - platform_fees.py
包含20+主流电商/支付平台的最新费率数据
文件编码: UTF-8
"""

import re
from datetime import datetime

# ============================================================
# 平台费率数据
# ============================================================
PLATFORM_FEES = {
    # --------------------------------------------------------
    # 1. Amazon
    # --------------------------------------------------------
    "amazon": {
        "name": "Amazon",
        "type": "跨境电商",
        "regions": ["美国", "英国", "德国", "日本", "法国", "意大利", "西班牙", "加拿大", "澳大利亚"],
        "fees": {
            "referral_fee": {
                "desc": "销售佣金",
                "rates": {
                    "美国": {"大部分品类": "15%", "电子产品": "8%", "服装": "17%", "珠宝": "20%"},
                    "英国": {"大部分品类": "15%", "电子产品": "8%"},
                    "德国": {"大部分品类": "15%"},
                    "日本": {"大部分品类": "10%", "电子产品": "8%"},
                    "加拿大": {"大部分品类": "12%", "电子产品": "8%"},
                },
            },
            "fba_fulfillment_fee": {
                "desc": "FBA配送费",
                "rates": {
                    "美国": {"小标准": "$3.22+", "大标准": "$5.44+", "大件": "$8.40+"},
                    "英国": {"小标准": "£2.55+", "大标准": "£3.83+"},
                    "德国": {"小标准": "€2.55+", "大标准": "€3.83+"},
                    "日本": {"小标准": "¥320+", "大标准": "¥500+"},
                },
            },
            "storage_fee": {
                "desc": "月度仓储费",
                "rates": {
                    "美国": {
                        "标准尺寸": "$0.87/立方英尺/月",
                        "大件": "$2.40/立方英尺/月",
                        "旺季(10-12月)": "标准尺寸$2.40/立方英尺/月",
                    },
                    "英国": {
                        "标准尺寸": "£0.75/立方英尺/月",
                        "大件": "£1.50/立方英尺/月",
                    },
                },
            },
            "closing_fee": {
                "desc": "成交费",
                "rates": {"媒体类": "$1.80/件"},
            },
        },
        "vat_thresholds": {"德国": "€10,000", "英国": "£10,000", "法国": "€10,000"},
        "updated": "2025-01",
        "source": "Amazon Seller Central 官方费率表",
    },

    # --------------------------------------------------------
    # 2. 淘宝/天猫
    # --------------------------------------------------------
    "taobao": {
        "name": "淘宝/天猫",
        "type": "国内电商",
        "fees": {
            "commission": {
                "desc": "佣金扣点",
                "rates": {"天猫": "0.5%-5%（按类目）", "淘宝": "0（免费）"},
            },
            "alimama": {
                "desc": "阿里妈妈推广费",
                "rates": {"CPC": "按点击付费", "CPS": "按成交付费，佣金率5%-50%"},
            },
            "service_fee": {
                "desc": "技术服务费",
                "rates": {"天猫": "3%-6%", "淘宝": "0"},
            },
        },
        "updated": "2025-01",
        "source": "淘宝/天猫商家中心",
    },

    # --------------------------------------------------------
    # 3. 京东
    # --------------------------------------------------------
    "jd": {
        "name": "京东",
        "type": "国内电商",
        "fees": {
            "pop_commission": {
                "desc": "POP店佣金",
                "rates": {"大部分品类": "5%-15%", "3C数码": "2%-8%", "服装": "5%-10%"},
            },
            "logistics_fee": {
                "desc": "京东物流费",
                "rates": {"中小件": "3-8元/单", "大件": "15-50元/单"},
            },
            "promotion_fee": {
                "desc": "促销活动费",
                "rates": {"618": "按活动报名", "双11": "按活动报名"},
            },
        },
        "updated": "2025-01",
        "source": "京东商家开放平台",
    },

    # --------------------------------------------------------
    # 4. 拼多多
    # --------------------------------------------------------
    "pdd": {
        "name": "拼多多",
        "type": "国内电商",
        "fees": {
            "commission": {
                "desc": "佣金",
                "rates": {"0佣金模式": "商家免费入驻，不收佣金"},
            },
            "ad_fee": {
                "desc": "推广费",
                "rates": {"搜索推广": "按CPC竞价", "场景推广": "按CPC/CPM"},
            },
            "deposit": {
                "desc": "保证金",
                "rates": {"标准": "1000元", "品牌": "根据类目"},
            },
        },
        "updated": "2025-01",
        "source": "拼多多商家后台",
    },

    # --------------------------------------------------------
    # 5. 速卖通
    # --------------------------------------------------------
    "aliexpress": {
        "name": "速卖通",
        "type": "跨境电商",
        "fees": {
            "commission": {
                "desc": "平台佣金",
                "rates": {"大部分品类": "5%-8%", "部分品类": "5%"},
            },
            "logistics": {
                "desc": "跨境物流费",
                "rates": {"标准物流": "$2-15/单", "无忧物流": "$3-20/单"},
            },
            "withdrawal": {
                "desc": "提现费",
                "rates": {"银行转账": "$15-30/笔", "Payoneer": "1%-2%"},
            },
        },
        "updated": "2025-01",
        "source": "速卖通卖家中心",
    },

    # --------------------------------------------------------
    # 6. Shopee
    # --------------------------------------------------------
    "shopee": {
        "name": "Shopee",
        "type": "跨境电商",
        "fees": {
            "commission": {
                "desc": "交易手续费",
                "rates": {"大部分站点": "2%-6%", "台湾站": "5%", "马来站": "2%-4%", "泰国站": "3%-5%", "菲律宾站": "2%"},
            },
            "payment_fee": {
                "desc": "支付手续费",
                "rates": {"各站点": "2%"},
            },
            "logistics": {
                "desc": "物流费",
                "rates": {"SLS标准": "按重量计费", "海外仓": "按仓库费率"},
            },
        },
        "updated": "2025-01",
        "source": "Shopee卖家学习中心",
    },

    # --------------------------------------------------------
    # 7. Temu
    # --------------------------------------------------------
    "temu": {
        "name": "Temu",
        "type": "跨境电商",
        "fees": {
            "commission": {
                "desc": "佣金",
                "rates": {"半托管": "0%-5%", "全托管": "平台定价"},
            },
            "settlement": {
                "desc": "结算周期",
                "rates": {"一般": "发货后7-15天"},
            },
            "logistics": {
                "desc": "物流费",
                "rates": {"半托管(卖家发货)": "卖家承担", "全托管": "平台承担"},
            },
        },
        "updated": "2025-01",
        "source": "Temu卖家中心",
    },

    # --------------------------------------------------------
    # 8. TikTok Shop
    # --------------------------------------------------------
    "tiktok_shop": {
        "name": "TikTok Shop",
        "type": "跨境电商",
        "fees": {
            "commission": {
                "desc": "平台佣金",
                "rates": {"大部分品类": "2%-8%", "东南亚": "1%-5%", "美国站": "5%-8%"},
            },
            "affiliate": {
                "desc": "达人带货佣金",
                "rates": {"一般": "5%-20%"},
            },
            "payment_fee": {
                "desc": "支付手续费",
                "rates": {"一般": "2%-3%"},
            },
        },
        "updated": "2025-01",
        "source": "TikTok Shop卖家中心",
    },

    # --------------------------------------------------------
    # 9. PayPal
    # --------------------------------------------------------
    "paypal": {
        "name": "PayPal",
        "type": "跨境支付",
        "fees": {
            "transaction_fee": {
                "desc": "交易手续费",
                "rates": {"跨境交易": "4.4%+固定费用", "国内交易": "2.9%+$0.30"},
            },
            "currency_conversion": {
                "desc": "货币转换费",
                "rates": {"加价": "3%-4%"},
            },
            "withdrawal": {
                "desc": "提现到国内银行",
                "rates": {"电汇": "$35/笔", "Payoneer": "1%"},
            },
        },
        "updated": "2025-01",
        "source": "PayPal官方费率页面",
    },

    # --------------------------------------------------------
    # 10. WorldFirst
    # --------------------------------------------------------
    "worldfirst": {
        "name": "WorldFirst",
        "type": "跨境支付",
        "fees": {
            "transfer_fee": {
                "desc": "转账手续费",
                "rates": {"一般": "0.5%-1%"},
            },
            "exchange_rate": {
                "desc": "汇率加价",
                "rates": {"一般": "0.3%-0.5%"},
            },
        },
        "updated": "2025-01",
        "source": "WorldFirst官方费率页面",
    },

    # --------------------------------------------------------
    # 11. PingPong
    # --------------------------------------------------------
    "pingpong": {
        "name": "PingPong",
        "type": "跨境支付",
        "fees": {
            "collection_fee": {
                "desc": "收款手续费",
                "rates": {"一般": "1%"},
            },
            "exchange_rate": {
                "desc": "汇率",
                "rates": {"实时汇率": "无加价"},
            },
        },
        "updated": "2025-01",
        "source": "PingPong官方费率页面",
    },

    # --------------------------------------------------------
    # 12. eBay
    # --------------------------------------------------------
    "ebay": {
        "name": "eBay",
        "type": "跨境电商",
        "regions": ["美国", "英国", "德国", "澳大利亚", "加拿大"],
        "fees": {
            "final_value_fee": {
                "desc": "成交费",
                "rates": {
                    "美国": {"大部分品类": "12.9%+$0.30", "电子产品": "12%+$0.30", "服装": "11%+$0.30"},
                    "英国": {"大部分品类": "12.8%+£0.30"},
                    "德国": {"大部分品类": "12%+€0.35"},
                },
            },
            "store_subscription": {
                "desc": "店铺订阅费",
                "rates": {"基础店": "$27.95/月", "高级店": "$74.95/月", "企业店": "$349.95/月"},
            },
            "listing_fee": {
                "desc": "刊登费",
                "rates": {"免费刊登": "每月250条", "超出": "$0.35/条"},
            },
            "managed_payments": {
                "desc": "支付处理费",
                "rates": {"美国": "2.9%+$0.30/笔"},
            },
        },
        "updated": "2025-01",
        "source": "eBay卖家中心费率表",
    },

    # --------------------------------------------------------
    # 13. Shopify
    # --------------------------------------------------------
    "shopify": {
        "name": "Shopify",
        "type": "独立站建站",
        "fees": {
            "subscription": {
                "desc": "订阅费",
                "rates": {"Basic": "$39/月", "Shopify": "$105/月", "Advanced": "$399/月"},
            },
            "payment_fee": {
                "desc": "支付手续费(Shopify Payments)",
                "rates": {"美国": "2.9%+$0.30", "英国": "2.5%+£0.20", "其他": "3.3%+特殊货币费"},
            },
            "third_party_payment_fee": {
                "desc": "第三方支付手续费",
                "rates": {"Basic": "2%", "Shopify": "1%", "Advanced": "0.5%"},
            },
            "transaction_fee": {
                "desc": "交易费(使用第三方支付时)",
                "rates": {"Basic": "2%", "Shopify": "1%", "Advanced": "0.5%"},
            },
        },
        "updated": "2025-01",
        "source": "Shopify官方定价页面",
    },

    # --------------------------------------------------------
    # 14. Walmart
    # --------------------------------------------------------
    "walmart": {
        "name": "Walmart Marketplace",
        "type": "跨境电商",
        "regions": ["美国", "加拿大"],
        "fees": {
            "referral_fee": {
                "desc": "销售佣金",
                "rates": {"大部分品类": "6%-15%", "电子产品": "8%", "服装": "8%-15%", "家居": "15%"},
            },
            "fulfillment_fee": {
                "desc": "WFS配送费",
                "rates": {"标准件": "$3.00+", "大件": "$6.00+"},
            },
            "storage_fee": {
                "desc": "仓储费",
                "rates": {"标准尺寸": "$0.75/立方英尺/月", "旺季(9-12月)": "$1.50/立方英尺/月"},
            },
        },
        "updated": "2025-01",
        "source": "Walmart Seller Center",
    },

    # --------------------------------------------------------
    # 15. Ozon
    # --------------------------------------------------------
    "ozon": {
        "name": "Ozon",
        "type": "跨境电商",
        "regions": ["俄罗斯"],
        "fees": {
            "commission": {
                "desc": "销售佣金",
                "rates": {"大部分品类": "5%-15%", "服装": "8%-12%", "电子产品": "5%-8%"},
            },
            "logistics": {
                "desc": "物流费",
                "rates": {"FBO仓发": "按重量体积计算", "FBS自发货": "按重量体积计算"},
            },
            "payment_fee": {
                "desc": "支付手续费",
                "rates": {"一般": "1.5%-3%"},
            },
        },
        "updated": "2025-01",
        "source": "Ozon卖家中心",
    },

    # --------------------------------------------------------
    # 16. Lazada
    # --------------------------------------------------------
    "lazada": {
        "name": "Lazada",
        "type": "跨境电商",
        "regions": ["东南亚(印尼/马来/菲律宾/新加坡/泰国/越南)"],
        "fees": {
            "commission": {
                "desc": "平台佣金",
                "rates": {"大部分站点": "1%-4%", "马来站": "1%-4%", "泰国站": "2%-4%"},
            },
            "payment_fee": {
                "desc": "支付手续费",
                "rates": {"各站点": "2%"},
            },
            "shipping_fee": {
                "desc": "物流费",
                "rates": {"LGS全球配送": "按重量计费", "海外仓": "按仓库费率"},
            },
        },
        "updated": "2025-01",
        "source": "Lazada卖家中心",
    },

    # --------------------------------------------------------
    # 17. Mercado Libre (美客多)
    # --------------------------------------------------------
    "mercado_libre": {
        "name": "Mercado Libre (美客多)",
        "type": "跨境电商",
        "regions": ["巴西", "墨西哥", "阿根廷", "智利", "哥伦比亚"],
        "fees": {
            "commission": {
                "desc": "销售佣金",
                "rates": {"巴西": "11%-16%", "墨西哥": "13%-16%", "阿根廷": "11%-13%"},
            },
            "listing_fee": {
                "desc": "刊登费",
                "rates": {"免费刊登": "每月50条", "超出": "按类目收费"},
            },
            "payment_fee": {
                "desc": "支付处理费",
                "rates": {"一般": "7.36%-13.99%"},
            },
        },
        "updated": "2025-01",
        "source": "Mercado Libre卖家中心",
    },

    # --------------------------------------------------------
    # 18. Wish
    # --------------------------------------------------------
    "wish": {
        "name": "Wish",
        "type": "跨境电商",
        "fees": {
            "commission": {
                "desc": "销售佣金",
                "rates": {"一般": "15%"},
            },
            "payment_processing": {
                "desc": "支付处理费",
                "rates": {"一般": "固定费用+2%"},
            },
            "logistics": {
                "desc": "物流费",
                "rates": {"Wish标准物流": "按重量计费", "Wish Express": "按重量计费"},
            },
        },
        "updated": "2025-01",
        "source": "Wish商户后台",
    },

    # --------------------------------------------------------
    # 19. Stripe
    # --------------------------------------------------------
    "stripe": {
        "name": "Stripe",
        "type": "跨境支付",
        "fees": {
            "transaction_fee": {
                "desc": "交易手续费",
                "rates": {"美国/加拿大/英国/澳洲": "2.9%+$0.30", "欧洲": "1.5%+€0.25", "国际卡": "3.5%+额外费用"},
            },
            "currency_conversion": {
                "desc": "货币转换费",
                "rates": {"加价": "1%"},
            },
            "payout": {
                "desc": "提现费",
                "rates": {"美国/英国/欧洲": "免费", "其他地区": "按银行费率"},
            },
        },
        "updated": "2025-01",
        "source": "Stripe官方定价页面",
    },

    # --------------------------------------------------------
    # 20. 连连支付 (LianLian Pay)
    # --------------------------------------------------------
    "lianlian": {
        "name": "连连支付",
        "type": "跨境支付",
        "fees": {
            "collection_fee": {
                "desc": "收款手续费",
                "rates": {"一般": "0.7%-1%"},
            },
            "exchange_rate": {
                "desc": "汇率加价",
                "rates": {"一般": "0.3%-0.5%"},
            },
            "withdrawal": {
                "desc": "提现费",
                "rates": {"国内银行": "免费或极低", "境外": "按银行费率"},
            },
        },
        "updated": "2025-01",
        "source": "连连支付官网",
    },

    # --------------------------------------------------------
    # 21. Coupang
    # --------------------------------------------------------
    "coupang": {
        "name": "Coupang",
        "type": "跨境电商",
        "regions": ["韩国"],
        "fees": {
            "commission": {
                "desc": "销售佣金",
                "rates": {"大部分品类": "7%-13%", "时尚类": "7%-10%", "电子产品": "7%-10%"},
            },
            "logistics": {
                "desc": "物流费",
                "rates": {"CGF/CGF LITE": "按重量体积计算", "海外仓": "按仓库费率"},
            },
            "payment_fee": {
                "desc": "支付手续费",
                "rates": {"一般": "2%-3%"},
            },
        },
        "updated": "2025-01",
        "source": "Coupang卖家中心",
    },

    # --------------------------------------------------------
    # 22. 独立站通用 (通用参考)
    # --------------------------------------------------------
    "independent_site": {
        "name": "独立站(通用)",
        "type": "独立站建站",
        "fees": {
            "payment_gateway": {
                "desc": "支付网关费",
                "rates": {"信用卡": "2%-3.5%+固定费用", "PayPal": "2.9%+$0.30", "本地支付": "1%-3%"},
            },
            "hosting": {
                "desc": "服务器/托管费",
                "rates": {"共享主机": "$5-30/月", "VPS": "$20-100/月", "云服务器": "$50-500/月"},
            },
            "ssl_certificate": {
                "desc": "SSL证书",
                "rates": {"免费(Let's Encrypt)": "$0", "付费证书": "$50-300/年"},
            },
        },
        "updated": "2025-01",
        "source": "行业通用数据",
    },
}


# ============================================================
# 辅助函数
# ============================================================

def _parse_percentage(rate_str):
    """将百分比字符串解析为小数。例如 '15%' -> 0.15"""
    if isinstance(rate_str, (int, float)):
        return float(rate_str) / 100.0 if rate_str > 1 else float(rate_str)
    if isinstance(rate_str, str):
        match = re.search(r"([\d.]+)\s*%", rate_str)
        if match:
            return float(match.group(1)) / 100.0
    return None


def _parse_range(rate_str):
    """解析范围费率字符串，返回 (min_rate, max_rate)。例如 '5%-15%' -> (0.05, 0.15)"""
    if isinstance(rate_str, str):
        parts = rate_str.split("-")
        if len(parts) == 2:
            low = _parse_percentage(parts[0])
            high = _parse_percentage(parts[1])
            if low is not None and high is not None:
                return (low, high)
    return None


def _get_data_expiry_notice(platform_data):
    """检查数据是否可能过期，返回提示信息"""
    updated = platform_data.get("updated", "")
    if updated:
        try:
            parts = updated.split("-")
            year = int(parts[0])
            month = int(parts[1])
            updated_date = datetime(year, month, 1)
            now = datetime.now()
            months_diff = (now.year - updated_date.year) * 12 + (now.month - updated_date.month)
            if months_diff > 6:
                return " [建议核实] 数据已超过6个月，费率可能已调整"
        except (ValueError, IndexError):
            pass
    return " [建议核实] 无法确认数据时效性"


# ============================================================
# 核心函数
# ============================================================

def get_platform_fee(platform, fee_type):
    """
    获取指定平台的指定费率

    参数:
        platform (str): 平台标识（如 'amazon', 'taobao'）
        fee_type (str): 费率类型（如 'referral_fee', 'commission'）

    返回:
        dict: 包含费率描述、具体费率和时效性提示
    """
    platform = platform.lower().strip()
    fee_type = fee_type.lower().strip()

    platform_data = PLATFORM_FEES.get(platform)
    if not platform_data:
        return {
            "error": f"未找到平台 '{platform}'",
            "available_platforms": list(PLATFORM_FEES.keys()),
        }

    fees = platform_data.get("fees", {})
    fee_data = fees.get(fee_type)
    if not fee_data:
        return {
            "error": f"未找到费率类型 '{fee_type}'",
            "available_fee_types": list(fees.keys()),
            "platform": platform_data["name"],
        }

    notice = _get_data_expiry_notice(platform_data)

    return {
        "platform": platform_data["name"],
        "platform_key": platform,
        "fee_type": fee_type,
        "desc": fee_data["desc"],
        "rates": fee_data["rates"],
        "updated": platform_data.get("updated", "未知"),
        "source": platform_data.get("source", "未知"),
        "notice": notice if "建议核实" in notice else "",
    }


def calculate_amazon_fba(weight_oz, size_category, region="美国"):
    """
    计算Amazon FBA配送费用（估算值）

    参数:
        weight_oz (float): 商品重量（盎司）
        size_category (str): 尺寸分类 ('小标准', '大标准', '大件')
        region (str): 区域（默认'美国'）

    返回:
        dict: 包含费用明细和时效性提示
    """
    platform_data = PLATFORM_FEES.get("amazon", {})
    notice = _get_data_expiry_notice(platform_data)

    # FBA基础费率表（美元，美国站）
    fba_base_rates = {
        "美国": {
            "小标准": {"base": 3.22, "per_oz": 0.0, "max_weight": 16},
            "大标准": {"base": 3.86, "per_oz": 0.40, "max_weight": 112},
            "大件": {"base": 8.40, "per_oz": 0.83, "max_weight": 240},
        },
        "英国": {
            "小标准": {"base": 2.55, "per_oz": 0.0, "max_weight": 16},
            "大标准": {"base": 3.83, "per_oz": 0.30, "max_weight": 112},
            "大件": {"base": 6.50, "per_oz": 0.60, "max_weight": 240},
        },
        "德国": {
            "小标准": {"base": 2.55, "per_oz": 0.0, "max_weight": 16},
            "大标准": {"base": 3.83, "per_oz": 0.30, "max_weight": 112},
            "大件": {"base": 6.50, "per_oz": 0.60, "max_weight": 240},
        },
        "日本": {
            "小标准": {"base": 320, "per_oz": 0.0, "max_weight": 16, "currency": "JPY"},
            "大标准": {"base": 500, "per_oz": 40, "max_weight": 112, "currency": "JPY"},
            "大件": {"base": 900, "per_oz": 80, "max_weight": 240, "currency": "JPY"},
        },
    }

    region_data = fba_base_rates.get(region)
    if not region_data:
        return {
            "error": f"暂不支持区域 '{region}'",
            "supported_regions": list(fba_base_rates.keys()),
        }

    size_data = region_data.get(size_category)
    if not size_data:
        return {
            "error": f"无效尺寸分类 '{size_category}'",
            "valid_categories": list(region_data.keys()),
        }

    currency = size_data.get("currency", "USD")
    currency_symbol = {"USD": "$", "GBP": "£", "EUR": "€", "JPY": "¥"}.get(currency, "$")

    if weight_oz <= size_data["max_weight"]:
        extra_weight = max(0, weight_oz - 16) if size_category != "小标准" else 0
        fee = size_data["base"] + extra_weight * size_data["per_oz"]
    else:
        fee = size_data["base"] + (size_data["max_weight"] - 16) * size_data["per_oz"]

    return {
        "platform": "Amazon FBA",
        "region": region,
        "size_category": size_category,
        "weight_oz": weight_oz,
        "estimated_fee": round(fee, 2),
        "currency": currency,
        "display_fee": f"{currency_symbol}{fee:.2f}",
        "updated": platform_data.get("updated", "未知"),
        "source": platform_data.get("source", "未知"),
        "notice": notice if "建议核实" in notice else "",
        "disclaimer": "此为估算费用，实际费用以Amazon Seller Central为准",
    }


def calculate_platform_commission(platform, amount, category="默认"):
    """
    计算平台佣金（估算值）

    参数:
        platform (str): 平台标识
        amount (float): 销售金额
        category (str): 商品类目（默认"默认"）

    返回:
        dict: 包含佣金计算结果
    """
    platform = platform.lower().strip()
    platform_data = PLATFORM_FEES.get(platform)
    if not platform_data:
        return {
            "error": f"未找到平台 '{platform}'",
            "available_platforms": list(PLATFORM_FEES.keys()),
        }

    notice = _get_data_expiry_notice(platform_data)

    # 佣金费率映射表
    commission_rate_map = {
        "amazon": {
            "默认": 0.15,
            "电子产品": 0.08,
            "服装": 0.17,
            "珠宝": 0.20,
        },
        "taobao": {
            "默认": 0.03,
            "天猫": 0.03,
            "淘宝": 0.0,
        },
        "jd": {
            "默认": 0.10,
            "3C数码": 0.05,
            "服装": 0.075,
        },
        "pdd": {
            "默认": 0.0,
        },
        "aliexpress": {
            "默认": 0.065,
        },
        "shopee": {
            "默认": 0.04,
            "台湾站": 0.05,
            "马来站": 0.03,
        },
        "temu": {
            "默认": 0.025,
            "半托管": 0.025,
            "全托管": 0.0,
        },
        "tiktok_shop": {
            "默认": 0.05,
            "东南亚": 0.03,
            "美国站": 0.065,
        },
        "ebay": {
            "默认": 0.129,
            "电子产品": 0.12,
            "服装": 0.11,
        },
        "shopify": {
            "默认": 0.029,
        },
        "walmart": {
            "默认": 0.10,
            "电子产品": 0.08,
            "服装": 0.115,
        },
        "ozon": {
            "默认": 0.10,
        },
        "lazada": {
            "默认": 0.025,
        },
        "mercado_libre": {
            "默认": 0.14,
            "巴西": 0.135,
            "墨西哥": 0.145,
        },
        "wish": {
            "默认": 0.15,
        },
        "coupang": {
            "默认": 0.10,
        },
    }

    rate = commission_rate_map.get(platform, {}).get(category, commission_rate_map.get(platform, {}).get("默认", None))

    if rate is None:
        return {
            "platform": platform_data["name"],
            "error": f"无法计算佣金，平台 '{platform}' 暂无默认费率数据",
            "amount": amount,
            "category": category,
        }

    commission = amount * rate

    return {
        "platform": platform_data["name"],
        "platform_key": platform,
        "amount": amount,
        "category": category,
        "commission_rate": rate,
        "commission_rate_display": f"{rate * 100:.1f}%",
        "commission": round(commission, 2),
        "net_amount": round(amount - commission, 2),
        "updated": platform_data.get("updated", "未知"),
        "source": platform_data.get("source", "未知"),
        "notice": notice if "建议核实" in notice else "",
        "disclaimer": "此为估算佣金，实际费用以平台结算为准",
    }


def get_all_platforms():
    """
    获取所有平台列表

    返回:
        list[dict]: 平台列表，每个元素包含平台标识、名称、类型和更新日期
    """
    platforms = []
    for key, data in PLATFORM_FEES.items():
        platforms.append({
            "key": key,
            "name": data["name"],
            "type": data["type"],
            "updated": data.get("updated", "未知"),
            "source": data.get("source", "未知"),
        })
    return platforms


def get_platform_detail(platform):
    """
    获取平台完整费率详情

    参数:
        platform (str): 平台标识

    返回:
        dict: 平台完整费率信息
    """
    platform = platform.lower().strip()
    platform_data = PLATFORM_FEES.get(platform)
    if not platform_data:
        return {
            "error": f"未找到平台 '{platform}'",
            "available_platforms": list(PLATFORM_FEES.keys()),
        }

    notice = _get_data_expiry_notice(platform_data)

    result = {
        "platform": platform_data["name"],
        "platform_key": platform,
        "type": platform_data["type"],
        "fees": {},
        "updated": platform_data.get("updated", "未知"),
        "source": platform_data.get("source", "未知"),
    }

    if "regions" in platform_data:
        result["regions"] = platform_data["regions"]

    if "vat_thresholds" in platform_data:
        result["vat_thresholds"] = platform_data["vat_thresholds"]

    for fee_key, fee_data in platform_data.get("fees", {}).items():
        result["fees"][fee_key] = {
            "desc": fee_data["desc"],
            "rates": fee_data["rates"],
        }

    if "建议核实" in notice:
        result["notice"] = notice

    return result


def search_platform(query):
    """
    搜索平台（支持中英文模糊搜索）

    参数:
        query (str): 搜索关键词（中英文均可）

    返回:
        list[dict]: 匹配的平台列表
    """
    query = query.lower().strip()
    results = []

    for key, data in PLATFORM_FEES.items():
        name = data["name"].lower()
        ptype = data["type"].lower()

        # 精确匹配平台标识
        if query == key:
            results.append({
                "key": key,
                "name": data["name"],
                "type": data["type"],
                "match_type": "精确匹配",
                "updated": data.get("updated", "未知"),
            })
            continue

        # 名称匹配
        if query in name or name in query:
            results.append({
                "key": key,
                "name": data["name"],
                "type": data["type"],
                "match_type": "名称匹配",
                "updated": data.get("updated", "未知"),
            })
            continue

        # 类型匹配
        if query in ptype:
            results.append({
                "key": key,
                "name": data["name"],
                "type": data["type"],
                "match_type": "类型匹配",
                "updated": data.get("updated", "未知"),
            })
            continue

        # 区域匹配
        regions = data.get("regions", [])
        for region in regions:
            if query in region.lower() or region.lower() in query:
                results.append({
                    "key": key,
                    "name": data["name"],
                    "type": data["type"],
                    "match_type": "区域匹配",
                    "matched_region": region,
                    "updated": data.get("updated", "未知"),
                })
                break

        # 费率关键词匹配
        fees = data.get("fees", {})
        for fee_key, fee_data in fees.items():
            desc = fee_data.get("desc", "").lower()
            if query in desc:
                results.append({
                    "key": key,
                    "name": data["name"],
                    "type": data["type"],
                    "match_type": "费率匹配",
                    "matched_fee": fee_data.get("desc", fee_key),
                    "updated": data.get("updated", "未知"),
                })
                break

    return results


def compare_platforms(platforms, amount, category="默认"):
    """
    对比多个平台费用

    参数:
        platforms (list): 平台标识列表
        amount (float): 销售金额
        category (str): 商品类目（默认"默认"）

    返回:
        dict: 各平台费用对比结果
    """
    if not isinstance(platforms, (list, tuple)):
        platforms = [platforms]

    comparison = {
        "amount": amount,
        "category": category,
        "platforms": [],
        "lowest_fee": None,
        "highest_fee": None,
    }

    for platform in platforms:
        platform = platform.lower().strip()
        result = calculate_platform_commission(platform, amount, category)

        if "error" in result:
            comparison["platforms"].append(result)
            continue

        comparison["platforms"].append(result)

        commission = result.get("commission", 0)
        if comparison["lowest_fee"] is None or commission < comparison["lowest_fee"]["commission"]:
            comparison["lowest_fee"] = result
        if comparison["highest_fee"] is None or commission > comparison["highest_fee"]["commission"]:
            comparison["highest_fee"] = result

    # 计算费用差异
    if comparison["lowest_fee"] and comparison["highest_fee"]:
        diff = comparison["highest_fee"]["commission"] - comparison["lowest_fee"]["commission"]
        comparison["fee_difference"] = round(diff, 2)
        comparison["fee_difference_display"] = (
            f"{comparison['lowest_fee']['platform']} vs {comparison['highest_fee']['platform']}: "
            f"差额 {diff:.2f}"
        )

    return comparison


# ============================================================
# 模块测试入口
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("平台费率知识库 - 测试")
    print("=" * 60)

    # 1. 获取所有平台
    print("\n[1] 所有平台列表:")
    all_platforms = get_all_platforms()
    for p in all_platforms:
        print(f"  {p['key']:20s} | {p['name']:25s} | {p['type']:10s} | 更新: {p['updated']}")

    # 2. 获取指定费率
    print("\n[2] Amazon销售佣金:")
    fee = get_platform_fee("amazon", "referral_fee")
    for k, v in fee.items():
        print(f"  {k}: {v}")

    # 3. 计算FBA费用
    print("\n[3] Amazon FBA费用计算 (10oz, 大标准, 美国):")
    fba = calculate_amazon_fba(10, "大标准", "美国")
    for k, v in fba.items():
        print(f"  {k}: {v}")

    # 4. 计算佣金
    print("\n[4] 平台佣金计算 ($100, 默认类目):")
    for p in ["amazon", "shopee", "ebay"]:
        result = calculate_platform_commission(p, 100)
        print(f"  {result['platform']}: 佣金 {result.get('commission', 'N/A')}")

    # 5. 搜索平台
    print("\n[5] 搜索'跨境':")
    results = search_platform("跨境")
    for r in results:
        print(f"  {r['name']:25s} | 匹配: {r['match_type']}")

    # 6. 平台对比
    print("\n[6] 平台费用对比 ($1000, 默认类目):")
    comparison = compare_platforms(["amazon", "ebay", "shopee", "tiktok_shop"], 1000)
    for p in comparison["platforms"]:
        print(f"  {p['platform']:25s} | 佣金率: {p.get('commission_rate_display', 'N/A'):8s} | 佣金: ${p.get('commission', 0):.2f}")
    if comparison.get("fee_difference_display"):
        print(f"  费用差异: {comparison['fee_difference_display']}")

    # 7. 平台详情
    print("\n[7] PayPal平台详情:")
    detail = get_platform_detail("paypal")
    for k, v in detail.items():
        print(f"  {k}: {v}")

    print("\n" + "=" * 60)
    print(f"共收录 {len(PLATFORM_FEES)} 个平台")
    print("=" * 60)
