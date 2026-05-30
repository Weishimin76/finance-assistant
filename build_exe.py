# -*- coding: utf-8 -*-
"""
打包跨境财务助手为EXE可执行文件
修复版：添加Streamlit元数据支持
"""
import PyInstaller.__main__
import os
import shutil

# 清理旧构建
for folder in ['build', 'dist']:
    if os.path.exists(folder):
        shutil.rmtree(folder)

# 打包配置
PyInstaller.__main__.run([
    'app_secure.py',                    # 主程序
    '--name=跨境财务助手Pro',            # 应用名称
    '--onefile',                         # 打包成单个EXE
    '--windowed',                        # 无控制台窗口
    
    # 包含源代码文件
    '--add-data=config.py;.',
    '--add-data=parsers.py;.',
    '--add-data=reconciliation.py;.',
    '--add-data=reports.py;.',
    '--add-data=finance_llm.py;.',
    '--add-data=vat.py;.',
    '--add-data=expense_audit.py;.',
    '--add-data=exchange_rate.py;.',
    '--add-data=tax_policy.py;.',
    '--add-data=archive.py;.',
    '--add-data=data;data',
    
    # 关键修复：收集Streamlit的所有文件（包括元数据）
    '--collect-all=streamlit',
    
    # 隐藏导入
    '--hidden-import=pandas',
    '--hidden-import=numpy',
    '--hidden-import=plotly',
    '--hidden-import=streamlit',
    '--hidden-import=streamlit.web.cli',
    '--hidden-import=streamlit.runtime.scriptrunner',
    '--hidden-import=streamlit.web',
    '--hidden-import=streamlit.runtime',
    '--hidden-import=ollama',
])

print("✅ 打包完成！EXE文件在 dist/ 目录")
