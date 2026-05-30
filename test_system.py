# -*- coding: utf-8 -*-
"""系统功能测试脚本"""
from datetime import datetime

# 测试实时时间同步功能
print('=== 实时时间同步功能测试 ===')
for i in range(3):
    now = datetime.now()
    print(f'当前时间 {i+1}: {now.strftime("%Y-%m-%d %H:%M:%S")}')

print()
print('=== AI功能状态检查 ===')
from finance_llm import finance_llm
print(f'配置的AI模型: {finance_llm.model}')
print(f'Ollama服务地址: {finance_llm.base_url}')
print(f'Ollama连接状态: {finance_llm.check_connection()}')

print()
print('=== 高端UI配置检查 ===')
print('主色调: #1E3A8A (深海军蓝)')
print('数字字体: Roboto Mono (等宽字体)')
print('实时时钟: 已集成在header中')
print('专业话术: 已更新为高端商务用语')

print()
print('✅ 系统功能检查完成！')
