# -*- coding: utf-8 -*-
"""
创建完整发布包
"""
import os
import shutil

base = r"C:\Users\Admin（无密码）\AppData\Roaming\TRAE SOLO CN\ModularData\ai-agent\work-mode-projects\6a1a40f7fe1065215841a76c"
release = os.path.join(base, "跨境财务助手_发布包")

# 创建发布目录
if os.path.exists(release):
    shutil.rmtree(release)
os.makedirs(release)

# 需要复制的文件
files = [
    "app_secure.py", "config.py", "parsers.py", "reconciliation.py",
    "reports.py", "finance_llm.py", "vat.py", "expense_audit.py",
    "exchange_rate.py", "tax_policy.py", "archive.py", "启动助手.bat"
]

for f in files:
    src = os.path.join(base, f)
    dst = os.path.join(release, f)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"✅ {f}")
    else:
        print(f"❌ 未找到: {f}")

# 复制data目录
data_src = os.path.join(base, "data")
data_dst = os.path.join(release, "data")
if os.path.exists(data_src):
    shutil.copytree(data_src, data_dst)
    print("✅ data目录")

# 创建使用说明
readme = """# 跨境财务助手 Pro v5.0

## 使用方法

1. 确保已安装 Python 3.10+
2. 安装依赖: pip install streamlit pandas numpy plotly ollama openpyxl
3. 双击 "启动助手.bat" 运行

## 功能
- 多平台对账 (Amazon/eBay/Shopify/Shopee/AliExpress)
- 自动异常检测
- 智能报表生成
- VAT计算 (10国)
- 报销审核
- 汇率监控

## 技术支持
如有问题请联系开发者
"""
with open(os.path.join(release, "README.txt"), "w", encoding="utf-8") as f:
    f.write(readme)

print(f"\n✅ 发布包创建完成！\n位置: {release}")
