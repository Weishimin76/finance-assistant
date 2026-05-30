# -*- coding: utf-8 -*-
import os
import shutil

base = r"C:\Users\Admin（无密码）\AppData\Roaming\TRAE SOLO CN\ModularData\ai-agent\work-mode-projects\6a1a40f7fe1065215841a76c"
release = os.path.join(base, "网页部署包")

# 创建发布目录
if os.path.exists(release):
    shutil.rmtree(release)
os.makedirs(release)

# 创建 .streamlit 目录
os.makedirs(os.path.join(release, ".streamlit"))

# 需要复制的文件
files = [
    ("app_secure.py", "app_secure.py"),
    ("config.py", "config.py"),
    ("parsers.py", "parsers.py"),
    ("reconciliation.py", "reconciliation.py"),
    ("reports.py", "reports.py"),
    ("finance_llm.py", "finance_llm.py"),
    ("vat.py", "vat.py"),
    ("expense_audit.py", "expense_audit.py"),
    ("exchange_rate.py", "exchange_rate.py"),
    ("tax_policy.py", "tax_policy.py"),
    ("archive.py", "archive.py"),
    ("requirements.txt", "requirements.txt"),
    ("Dockerfile", "Dockerfile"),
    (".streamlit/config.toml", ".streamlit/config.toml"),
]

for src_name, dst_name in files:
    src = os.path.join(base, src_name)
    dst = os.path.join(release, dst_name)
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        print(f"✅ {dst_name}")
    else:
        print(f"❌ 未找到: {src_name}")

# 复制部署指南
shutil.copy2(os.path.join(base, "部署指南.md"), os.path.join(release, "部署指南.md"))
print("✅ 部署指南.md")

print(f"\n✅ 网页部署包创建完成！\n位置: {release}")
