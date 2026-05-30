# -*- coding: utf-8 -*-
"""
核心模块测试脚本
"""
import sys
import os

# 确保项目目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_parsers():
    """测试数据解析模块"""
    print("=" * 50)
    print("测试1: 多平台数据解析")
    print("=" * 50)

    from parsers import parse_file, merge_multi_platform

    # 测试 Amazon
    try:
        amz_df = parse_file("data/sample_data/amazon_orders.csv", platform="amazon")
        print(f"✅ Amazon 解析成功: {len(amz_df)} 条记录")
        print(f"   字段: {list(amz_df.columns)}")
    except Exception as e:
        print(f"❌ Amazon 解析失败: {e}")

    # 测试 eBay
    try:
        eby_df = parse_file("data/sample_data/ebay_orders.csv", platform="ebay")
        print(f"✅ eBay 解析成功: {len(eby_df)} 条记录")
    except Exception as e:
        print(f"❌ eBay 解析失败: {e}")

    # 测试 Shopify
    try:
        shf_df = parse_file("data/sample_data/shopify_orders.csv", platform="shopify")
        print(f"✅ Shopify 解析成功: {len(shf_df)} 条记录")
    except Exception as e:
        print(f"❌ Shopify 解析失败: {e}")

    # 测试 Shopee
    try:
        shp_df = parse_file("data/sample_data/shopee_orders.csv", platform="shopee")
        print(f"✅ Shopee 解析成功: {len(shp_df)} 条记录")
    except Exception as e:
        print(f"❌ Shopee 解析失败: {e}")

    # 合并
    merged = merge_multi_platform([amz_df, eby_df, shf_df, shp_df])
    print(f"✅ 多平台合并成功: {len(merged)} 条记录")
    print(f"   平台分布: {dict(merged['平台'].value_counts())}")

    return merged


def test_reconciliation(df):
    """测试对账引擎"""
    print("\n" + "=" * 50)
    print("测试2: 智能对账引擎")
    print("=" * 50)

    from reconciliation import reconcile_data

    normal, anomaly, summary = reconcile_data(df)

    print(f"✅ 对账完成")
    print(f"   正常记录: {len(normal)} 条")
    print(f"   异常记录: {len(anomaly)} 条")

    if not summary.empty:
        print(f"\n   异常汇总:")
        for _, row in summary.iterrows():
            print(f"   - {row['类型']}: {row['数量']} 条 ({row['严重程度']})")

    if not anomaly.empty:
        print(f"\n   异常明细（前5条）:")
        for _, row in anomaly.head(5).iterrows():
            print(f"   - {row['订单号']} | {row['异常原因']}")

    return normal, anomaly, summary


def test_reports(df):
    """测试报表生成"""
    print("\n" + "=" * 50)
    print("测试3: 报表自动生成")
    print("=" * 50)

    from reports import generate_all_reports

    reports = generate_all_reports(df)

    for name, report_df in reports.items():
        if not report_df.empty:
            print(f"✅ {name}: {len(report_df)} 行 x {len(report_df.columns)} 列")
        else:
            print(f"⚠️ {name}: 无数据")

    return reports


def test_llm():
    """测试 LLM 连接"""
    print("\n" + "=" * 50)
    print("测试4: LLM 连接状态")
    print("=" * 50)

    try:
        from finance_llm import finance_llm
        connected = finance_llm.check_connection()
        if connected:
            models = finance_llm.list_models()
            print(f"✅ Ollama 已连接")
            print(f"   可用模型: {models}")
        else:
            print(f"⚠️ Ollama 未运行（不影响其他功能）")
            print(f"   请运行: ollama serve")
    except Exception as e:
        print(f"⚠️ Ollama 未安装（不影响其他功能）")
        print(f"   下载地址: https://ollama.com")


if __name__ == "__main__":
    print("\n🧪 跨境电商财务智能体 - 模块测试\n")

    # 测试解析
    merged_df = test_parsers()

    # 测试对账
    normal, anomaly, summary = test_reconciliation(merged_df)

    # 测试报表
    reports = test_reports(merged_df)

    # 测试 LLM
    test_llm()

    print("\n" + "=" * 50)
    print("✅ 所有核心模块测试完成！")
    print("=" * 50)
    print("\n启动 Web 应用: python app.py")
    print("或直接运行: start.bat")
