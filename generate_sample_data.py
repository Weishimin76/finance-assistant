# -*- coding: utf-8 -*-
"""
生成示例数据 - 用于测试和演示
"""
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def generate_sample_data():
    """生成多平台示例订单数据"""

    np.random.seed(42)

    # Amazon 示例数据
    amazon_data = {
        "Order ID": [f"AMZ-{1000+i}" for i in range(50)],
        "Order Date": [(datetime.now() - timedelta(days=np.random.randint(0, 90))).strftime("%Y-%m-%d") for _ in range(50)],
        "SKU": [f"SKU-A{np.random.randint(100,999)}" for _ in range(50)],
        "Product Name": [np.random.choice(["无线蓝牙耳机", "手机壳", "充电线", "手机支架", "屏幕保护膜"]) for _ in range(50)],
        "Quantity": np.random.randint(1, 10, 50),
        "Item Price": np.round(np.random.uniform(5, 80, 50), 2),
        "Shipping Charge": np.round(np.random.uniform(3, 15, 50), 2),
        "Referral Fee": np.round(np.random.uniform(0.75, 12, 50), 2),  # 佣金
        "Total Price": None,
        "Buyer Name": [f"Buyer_{i}" for i in range(50)],
        "Tracking Number": [f"TRK{np.random.randint(100000,999999)}" for _ in range(50)],
        "Status": np.random.choice(["Shipped", "Delivered", "Pending", "Refunded"], 50, p=[0.4, 0.3, 0.2, 0.1]),
        "Currency": "USD",
    }
    amazon_df = pd.DataFrame(amazon_data)
    amazon_df["Total Price"] = amazon_df["Item Price"] * amazon_df["Quantity"] + amazon_df["Shipping Charge"]

    # 添加一些异常数据
    # 重复订单
    amazon_df.loc[0, "Order ID"] = "AMZ-1001"
    amazon_df.loc[1, "Order ID"] = "AMZ-1001"
    # 高佣金
    amazon_df.loc[5, "Referral Fee"] = 50.0
    # 退款但状态未更新
    amazon_df.loc[10, "Status"] = "Delivered"
    amazon_df.loc[10, "Referral Fee"] = -20.0

    # eBay 示例数据
    ebay_data = {
        "Order Number": [f"EBY-{2000+i}" for i in range(30)],
        "Sale Date": [(datetime.now() - timedelta(days=np.random.randint(0, 90))).strftime("%Y-%m-%d") for _ in range(30)],
        "Item Title": [np.random.choice(["LED灯带", "数据线", "收纳盒", "厨房用品", "宠物用品"]) for _ in range(30)],
        "SKU": [f"SKU-E{np.random.randint(100,999)}" for _ in range(30)],
        "Quantity Sold": np.random.randint(1, 5, 30),
        "Sale Price": np.round(np.random.uniform(3, 50, 30), 2),
        "Shipping Fee": np.round(np.random.uniform(2, 10, 30), 2),
        "Final Value Fee": np.round(np.random.uniform(0.5, 7, 30), 2),
        "Total Price": None,
        "Buyer Username": [f"eBuyer_{j}" for j in range(30)],
        "Tracking": [f"ETRK{np.random.randint(100000,999999)}" for _ in range(30)],
        "Order Status": np.random.choice(["Shipped", "Completed", "Cancelled"], 30, p=[0.3, 0.5, 0.2]),
        "Currency": "USD",
    }
    ebay_df = pd.DataFrame(ebay_data)
    ebay_df["Total Price"] = ebay_df["Sale Price"] * ebay_df["Quantity Sold"] + ebay_df["Shipping Fee"]

    # Shopify 示例数据
    shopify_data = {
        "Order Name": [f"#SHF-{3000+i}" for i in range(20)],
        "Created at": [(datetime.now() - timedelta(days=np.random.randint(0, 90))).strftime("%Y-%m-%d %H:%M:%S") for _ in range(20)],
        "Lineitem name": [np.random.choice(["定制T恤", "帆布包", "马克杯", "钥匙扣", "手机壳"]) for _ in range(20)],
        "Lineitem sku": [f"SKU-S{np.random.randint(100,999)}" for _ in range(20)],
        "Lineitem quantity": np.random.randint(1, 5, 20),
        "Total Price": np.round(np.random.uniform(10, 100, 20), 2),
        "Shipping": np.round(np.random.uniform(5, 20, 20), 2),
        "Gateway Fee": np.round(np.random.uniform(0.3, 3, 20), 2),
        "Email": [f"customer{i}@example.com" for i in range(20)],
        "Financial Status": np.random.choice(["Paid", "Refunded", "Partially Refunded", "Pending"], 20, p=[0.5, 0.15, 0.1, 0.25]),
        "Currency": "USD",
    }

    shopify_df = pd.DataFrame(shopify_data)

    # Shopee 示例数据
    shopee_data = {
        "Order No": [f"SHP-{4000+i}" for i in range(25)],
        "Order Time": [(datetime.now() - timedelta(days=np.random.randint(0, 90))).strftime("%Y-%m-%d %H:%M:%S") for _ in range(25)],
        "Product Name": [np.random.choice(["手机支架", "数据线", "耳机套", "充电宝", "蓝牙音箱"]) for _ in range(25)],
        "SKU": [f"SKU-SP{np.random.randint(100,999)}" for _ in range(25)],
        "Quantity": np.random.randint(1, 8, 25),
        "Unit Price": np.round(np.random.uniform(2, 40, 25), 2),
        "Shipping Fee": np.round(np.random.uniform(1, 8, 25), 2),
        "Commission": np.round(np.random.uniform(0.2, 5, 25), 2),
        "Service Fee": np.round(np.random.uniform(0.1, 2, 25), 2),
        "Total Amount": None,
        "Buyer": [f"Shopper_{k}" for k in range(25)],
        "Tracking Number": [f"STRK{np.random.randint(100000,999999)}" for _ in range(25)],
        "Status": np.random.choice(["Shipped", "Completed", "Cancelled", "Returned"], 25, p=[0.3, 0.4, 0.15, 0.15]),
        "Currency": "SGD",
    }
    shopee_df = pd.DataFrame(shopee_data)
    shopee_df["Total Amount"] = shopee_df["Unit Price"] * shopee_df["Quantity"] + shopee_df["Shipping Fee"]

    # 保存文件
    os.makedirs("data/sample_data", exist_ok=True)
    amazon_df.to_csv("data/sample_data/amazon_orders.csv", index=False, encoding="utf-8-sig")
    ebay_df.to_csv("data/sample_data/ebay_orders.csv", index=False, encoding="utf-8-sig")
    shopify_df.to_csv("data/sample_data/shopify_orders.csv", index=False, encoding="utf-8-sig")
    shopee_df.to_csv("data/sample_data/shopee_orders.csv", index=False, encoding="utf-8-sig")

    print("✅ 示例数据已生成到 data/sample_data/ 目录")
    print(f"   - Amazon: {len(amazon_df)} 条")
    print(f"   - eBay: {len(ebay_df)} 条")
    print(f"   - Shopify: {len(shopify_df)} 条")
    print(f"   - Shopee: {len(shopee_df)} 条")


if __name__ == "__main__":
    generate_sample_data()
