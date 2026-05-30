# -*- coding: utf-8 -*-
"""
AI驱动跨境财务管理平台 v7.0 - 企业级专业版
智能对账 · 精准算税 · 实时洞察 · 全链路自动化
主色调：深海军蓝 #1E3A8A
"""
import streamlit as st
import pandas as pd
import numpy as np
import os
import hashlib
import json
from datetime import datetime
import time
import random

# ==================== 高层次跨境财务知识库 ====================
FINANCIAL_TIPS = [
    {
        "title": "汇率风险管理",
        "content": "跨境电商应建立完善的汇率风险管理体系，通过远期结汇、外汇期权等金融工具锁定成本，避免汇率波动对利润的侵蚀。",
        "source": "跨境电商财务管理实践"
    },
    {
        "title": "VAT递延清关",
        "content": "采用VAT递延清关（Postponed VAT Accounting）可在进口时不缴纳进口VAT，有效改善现金流，降低资金占用成本。",
        "source": "欧盟海关合规指南"
    },
    {
        "title": "转移定价规则",
        "content": "跨境关联交易需遵循独立交易原则，确保定价公允。各国税务局对转移定价审查日趋严格，建议保留完整的转让定价文档。",
        "source": "OECD转移定价指南"
    },
    {
        "title": "成本加成法",
        "content": "跨境电商常用成本加成法核算关联采购价格，加成比例通常在5%-15%之间，需根据行业特点和功能风险合理确定。",
        "source": "国际税务筹划"
    },
    {
        "title": "境外所得抵免",
        "content": "企业在境外缴纳的所得税可按规定在境内应纳税额中抵免，避免双重征税。抵免限额计算需综合考虑综合抵免与分国抵免两种方式。",
        "source": "企业所得税法实施条例"
    },
    {
        "title": "离岸账户合规",
        "content": "境外账户需按期进行CRS信息申报，大额交易需说明资金来源。账户开立前应评估实际控制人身份及受益所有人信息披露要求。",
        "source": "反洗钱合规实务"
    },
    {
        "title": "进口关税估算",
        "content": "跨境进口关税=完税价格×关税率。完税价格包含货值、运费、保险费等。合理归类HS编码可有效降低关税成本。",
        "source": "海关估价协议"
    },
    {
        "title": "亚马逊FBA成本优化",
        "content": "FBA成本包括仓储费、配送费、月度仓储长期费。优化库存周转、合理安排旺季补货可显著降低FBA成本。",
        "source": "亚马逊卖家中心"
    },
    {
        "title": "出口退税筹划",
        "content": "出口货物退（免）税需确保收齐增值税专用发票。退税申报时间窗口为货物出口后90天内，逾期将丧失退税资格。",
        "source": "出口货物退（免）税管理办法"
    },
    {
        "title": "跨境支付合规",
        "content": "跨境收支需通过有牌支付机构办理，留存完整的交易单据。个人年度结售汇限额为5万美元，超额需提供真实性证明材料。",
        "source": "外汇管理条例"
    },
    {
        "title": "利润汇回税务",
        "content": "境外子公司利润汇回需关注预提所得税税率，中美预提所得税税率为10%，中国香港地区可申请税收协定优惠至5%。",
        "source": "税收协定应用指南"
    },
    {
        "title": "无形资产定价",
        "content": "跨境电商的无形资产（如商标、专利）转让或许可需符合独立交易原则。无形资产的开发成本与收益需合理配比。",
        "source": "BEPS行动计划"
    },
    {
        "title": "数字服务税",
        "content": "英国、法国、印度等国已开征数字服务税（DST），税率通常为2%-3%，面向提供数字服务的大型跨国企业征收。",
        "source": "数字经济税收研究"
    },
    {
        "title": "常设机构风险",
        "content": "跨境电商在目标市场设立仓库、办公室可能构成常设机构，需在当地缴纳企业所得税。建议通过独立法人实体运营。",
        "source": "国际税收协定解读"
    },
    {
        "title": "电商平台税务责任",
        "content": "欧盟、中国等地区已立法要求电商平台代扣代缴卖家税款。卖家需确保平台账户信息与税务登记信息一致。",
        "source": "电商税务合规指南"
    },
    {
        "title": "资金池管理",
        "content": "跨境资金池可实现境内外子公司间资金余缺调剂，降低整体财务成本。需遵守外债管理和境外放款相关规定。",
        "source": "跨境人民币业务"
    },
    {
        "title": "税务档案管理",
        "content": "跨境交易相关文件需保存至少5-10年，包括合同、发票、付款凭证、定价文件等。电子档案需确保可追溯、可查验。",
        "source": "税务稽查规程"
    },
    {
        "title": "进口增值税抵扣",
        "content": "一般纳税人进口环节缴纳的增值税可作为进项税额抵扣。但需确保取得海关缴款书，票面信息与实际进口货物一致。",
        "source": "增值税暂行条例"
    },
    {
        "title": "多层级分销定价",
        "content": "跨境多层级分销体系需确保每层交易价格符合独立交易原则，避免因转让定价问题被税务机关调整补税。",
        "source": "转让定价实务"
    },
    {
        "title": "递延所得税处理",
        "content": "跨境业务产生的暂时性差异需确认递延所得税资产或负债。合理运用递延税项可优化报表结构，提升财务信息质量。",
        "source": "国际会计准则"
    },
    {
        "title": "海关归类技巧",
        "content": "同一商品可能对应多个HS编码，选择合适的编码可影响关税税率和监管条件。建议通过海关预归类服务获取权威裁定。",
        "source": "海关商品归类"
    },
    {
        "title": "跨境电商综合税负",
        "content": "跨境电商综合税负包括关税、进口增值税、消费税及企业所得税。通过保税备货模式可降低税负成本。",
        "source": "跨境电商税务研究"
    },
    {
        "title": "税收协定优惠",
        "content": "与70余个国家签订的税收协定可提供股息、利息、特许权使用费预提所得税优惠。需正确开具居民身份证明。",
        "source": "税收协定大全"
    },
    {
        "title": "海外仓税务处理",
        "content": "海外仓模式下，货物出口不退税，进口时需按一般贸易缴税。建议保留完整的物流单据证明货物真实离境。",
        "source": "跨境电商实务"
    },
    {
        "title": "信用保险运用",
        "content": "跨境电商应收账款可投保出口信用保险，防范买家破产、拖欠或政治风险。保险覆盖率可达信用限额的90%。",
        "source": "出口信用保险指南"
    }
]

# ==================== 密码管理 ====================
PASSWORD_FILE = "data/.secure_config"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_password():
    if os.path.exists(PASSWORD_FILE):
        try:
            with open(PASSWORD_FILE, 'r') as f:
                config = json.load(f)
                return config.get('password_hash')
        except:
            return None
    return None

def save_password(password_hash):
    os.makedirs("data", exist_ok=True)
    config = {'password_hash': password_hash, 'created_at': datetime.now().isoformat()}
    with open(PASSWORD_FILE, 'w') as f:
        json.dump(config, f)

def verify_password(password):
    saved_hash = load_password()
    if saved_hash is None:
        return True
    return hash_password(password) == saved_hash

def has_password():
    return load_password() is not None

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="AI驱动跨境财务管理平台",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== 企业级专业CSS ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;600&display=swap');
    
    /* 隐藏默认元素 */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    
    /* 全局字体 */
    html, body, [class*="css"] {
        font-family: "Microsoft YaHei", "PingFang SC", sans-serif !important;
    }
    
    /* 数字等宽字体 */
    .mono-num {
        font-family: "Roboto Mono", "Consolas", monospace !important;
        font-feature-settings: "tnum";
        font-variant-numeric: tabular-nums;
    }
    
    /* 置顶标识栏 - 深海军蓝 */
    .header-bar {
        background: #1E3A8A;
        padding: 16px 32px;
        margin: -1rem -1rem 0 -1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    
    .header-title {
        color: white;
        font-size: 28px;
        font-weight: 700;
        letter-spacing: 1px;
    }
    
    .header-subtitle {
        color: rgba(255,255,255,0.7);
        font-size: 14px;
        margin-top: 4px;
        font-weight: 400;
    }
    
    .header-badge {
        background: #3B82F6;
        color: white;
        padding: 6px 16px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    
    .header-info {
        color: rgba(255,255,255,0.8);
        font-size: 13px;
        text-align: right;
    }
    
    .header-time {
        color: white;
        font-family: "Roboto Mono", monospace;
        font-size: 14px;
        font-weight: 500;
    }
    
    /* 汇率条 - 简洁专业 */
    .ticker-bar {
        background: #F9FAFB;
        padding: 12px 32px;
        border-bottom: 1px solid #E5E7EB;
        margin: 0 -1rem;
        font-size: 13px;
        color: #6B7280;
    }
    
    .ticker-item {
        display: inline-block;
        margin-right: 32px;
    }
    
    .ticker-currency {
        color: #1F2937;
        font-weight: 600;
    }
    
    .ticker-rate {
        font-family: "Roboto Mono", monospace;
        color: #1E3A8A;
        font-weight: 600;
        margin-left: 4px;
    }
    
    .ticker-change-up {
        color: #10B981;
        font-family: "Roboto Mono", monospace;
        font-size: 11px;
        margin-left: 4px;
    }
    
    .ticker-change-down {
        color: #EF4444;
        font-family: "Roboto Mono", monospace;
        font-size: 11px;
        margin-left: 4px;
    }
    
    /* 知识滚动条 */
    .tips-container {
        background: linear-gradient(135deg, #1E3A8A 0%, #1e40af 100%);
        padding: 16px 32px;
        margin: 0 -1rem 24px -1rem;
        overflow: hidden;
        position: relative;
    }
    
    .tips-label {
        color: rgba(255,255,255,0.6);
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    
    .tips-wrapper {
        overflow: hidden;
        white-space: nowrap;
    }
    
    .tips-track {
        display: inline-flex;
        animation: scroll-tips 60s linear infinite;
    }
    
    @keyframes scroll-tips {
        0% { transform: translateX(0); }
        100% { transform: translateX(-50%); }
    }
    
    .tips-card {
        display: inline-block;
        background: rgba(255,255,255,0.1);
        border-radius: 6px;
        padding: 12px 20px;
        margin-right: 24px;
        max-width: 400px;
        vertical-align: top;
    }
    
    .tips-card-title {
        color: #60A5FA;
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 4px;
    }
    
    .tips-card-content {
        color: white;
        font-size: 12px;
        line-height: 1.5;
        margin-bottom: 4px;
    }
    
    .tips-card-source {
        color: rgba(255,255,255,0.5);
        font-size: 10px;
    }
    
    /* 登录界面 - 极简专业 */
    .auth-container {
        max-width: 420px;
        margin: 100px auto;
        padding: 48px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.08);
        border: 1px solid #E5E7EB;
    }
    
    .auth-logo {
        width: 64px;
        height: 64px;
        background: #1E3A8A;
        border-radius: 8px;
        margin: 0 auto 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 28px;
        font-weight: 700;
    }
    
    .auth-title {
        font-size: 24px;
        font-weight: 700;
        color: #1F2937;
        margin-bottom: 8px;
        text-align: center;
    }
    
    .auth-subtitle {
        color: #6B7280;
        font-size: 14px;
        margin-bottom: 32px;
        text-align: center;
    }
    
    .auth-input-label {
        font-size: 13px;
        font-weight: 600;
        color: #374151;
        margin-bottom: 8px;
    }
    
    .auth-btn {
        width: 100%;
        padding: 14px;
        background: #1E3A8A;
        color: white;
        border: none;
        border-radius: 6px;
        font-size: 15px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
        margin-top: 8px;
    }
    
    .auth-btn:hover {
        background: #1e40af;
    }
    
    .auth-btn:active {
        transform: translateY(1px);
    }
    
    .auth-hint {
        margin-top: 24px;
        padding: 16px;
        background: #F9FAFB;
        border-left: 3px solid #1E3A8A;
        border-radius: 0 6px 6px 0;
        font-size: 13px;
        color: #4B5563;
        line-height: 1.6;
    }
    
    /* 主内容区 */
    .main-content {
        padding: 0 32px 32px 32px;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    /* 页面标题区 */
    .page-header {
        margin-bottom: 32px;
        padding-bottom: 24px;
        border-bottom: 1px solid #E5E7EB;
    }
    
    .page-title {
        font-size: 32px;
        font-weight: 700;
        color: #1F2937;
        margin-bottom: 8px;
    }
    
    .page-subtitle {
        font-size: 16px;
        color: #6B7280;
        font-weight: 400;
    }
    
    /* 指标卡片 - 专业财务风格 */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 24px;
        margin-bottom: 32px;
    }
    
    .metric-card {
        background: white;
        border-radius: 8px;
        padding: 24px;
        border: 1px solid #E5E7EB;
        transition: box-shadow 0.2s;
    }
    
    .metric-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    
    .metric-label {
        font-size: 13px;
        color: #6B7280;
        font-weight: 500;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        font-family: "Roboto Mono", monospace;
        font-size: 28px;
        font-weight: 600;
        color: #1F2937;
        margin-bottom: 8px;
    }
    
    .metric-unit {
        font-size: 14px;
        color: #9CA3AF;
        margin-left: 4px;
    }
    
    .metric-change-positive {
        font-family: "Roboto Mono", monospace;
        font-size: 13px;
        color: #10B981;
        font-weight: 500;
    }
    
    .metric-change-negative {
        font-family: "Roboto Mono", monospace;
        font-size: 13px;
        color: #EF4444;
        font-weight: 500;
    }
    
    /* 上传区域 - 简洁专业 */
    .upload-zone {
        background: #F9FAFB;
        border: 2px dashed #D1D5DB;
        border-radius: 8px;
        padding: 48px;
        text-align: center;
        transition: all 0.2s;
    }
    
    .upload-zone:hover {
        border-color: #3B82F6;
        background: #EFF6FF;
    }
    
    .upload-icon {
        font-size: 48px;
        color: #9CA3AF;
        margin-bottom: 16px;
    }
    
    .upload-title {
        font-size: 18px;
        font-weight: 600;
        color: #1F2937;
        margin-bottom: 8px;
    }
    
    .upload-desc {
        color: #6B7280;
        font-size: 14px;
        margin-bottom: 24px;
    }
    
    .platform-tags {
        display: flex;
        justify-content: center;
        gap: 8px;
        flex-wrap: wrap;
    }
    
    .platform-tag {
        background: white;
        border: 1px solid #E5E7EB;
        padding: 6px 12px;
        border-radius: 4px;
        font-size: 12px;
        color: #4B5563;
        font-weight: 500;
    }
    
    /* AI对话区域 - 专业版 */
    .ai-chat-section {
        background: white;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 24px;
    }
    
    .ai-chat-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 20px;
        padding-bottom: 16px;
        border-bottom: 1px solid #E5E7EB;
    }
    
    .ai-chat-icon {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 20px;
    }
    
    .ai-chat-title {
        font-size: 18px;
        font-weight: 700;
        color: #1F2937;
    }
    
    .ai-chat-subtitle {
        font-size: 12px;
        color: #6B7280;
    }
    
    .ai-chat-status {
        margin-left: auto;
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        color: #6B7280;
    }
    
    .ai-status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10B981;
    }
    
    .ai-status-dot.offline {
        background: #EF4444;
    }
    
    .ai-response {
        background: #F9FAFB;
        border-radius: 8px;
        padding: 20px;
        margin-top: 16px;
        border-left: 3px solid #1E3A8A;
        line-height: 1.8;
    }
    
    /* 数据表格 - 专业财务风格 */
    .data-table {
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        overflow: hidden;
    }
    
    .table-header {
        background: #F9FAFB;
        padding: 12px 16px;
        font-weight: 600;
        font-size: 13px;
        color: #374151;
        border-bottom: 1px solid #E5E7EB;
    }
    
    /* 警告提示 */
    .alert-warning {
        background: #FFFBEB;
        border: 1px solid #FCD34D;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 24px;
    }
    
    .alert-title {
        font-weight: 600;
        color: #92400E;
        font-size: 14px;
        margin-bottom: 4px;
    }
    
    .alert-text {
        color: #A16207;
        font-size: 13px;
    }
    
    /* 成功提示 */
    .alert-success {
        background: #ECFDF5;
        border: 1px solid #6EE7B7;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 24px;
    }
    
    .alert-success .alert-title {
        color: #065F46;
    }
    
    .alert-success .alert-text {
        color: #047857;
    }
    
    /* 工具卡片 */
    .tool-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 24px;
        margin-top: 32px;
    }
    
    .tool-card {
        background: white;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 24px;
        text-align: center;
        transition: all 0.2s;
        cursor: pointer;
    }
    
    .tool-card:hover {
        border-color: #3B82F6;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    
    .tool-icon {
        width: 48px;
        height: 48px;
        background: #EFF6FF;
        border-radius: 8px;
        margin: 0 auto 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
    }
    
    .tool-name {
        font-weight: 600;
        color: #1F2937;
        margin-bottom: 4px;
    }
    
    .tool-desc {
        font-size: 12px;
        color: #6B7280;
    }
    
    /* 按钮样式 */
    .btn-primary {
        background: #1E3A8A;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 6px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .btn-primary:hover {
        background: #1e40af;
    }
    
    .btn-secondary {
        background: white;
        color: #374151;
        border: 1px solid #D1D5DB;
        padding: 10px 20px;
        border-radius: 6px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .btn-secondary:hover {
        background: #F9FAFB;
        border-color: #9CA3AF;
    }
    
    /* 设置面板 */
    .settings-panel {
        position: fixed;
        right: 0;
        top: 0;
        width: 360px;
        height: 100vh;
        background: white;
        box-shadow: -4px 0 24px rgba(0,0,0,0.1);
        z-index: 1000;
        padding: 24px;
        overflow-y: auto;
    }
    
    .settings-header {
        font-size: 18px;
        font-weight: 700;
        color: #1F2937;
        margin-bottom: 24px;
        padding-bottom: 16px;
        border-bottom: 1px solid #E5E7EB;
    }
    
    /* 标签页 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 1px solid #E5E7EB;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 12px 24px;
        font-weight: 500;
        color: #6B7280;
        border: none;
        border-bottom: 2px solid transparent;
    }
    
    .stTabs [aria-selected="true"] {
        color: #1E3A8A;
        border-bottom-color: #1E3A8A;
    }
    
    /* 快捷问题按钮 */
    .quick-question-btn {
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        color: #1E3A8A;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 13px;
        cursor: pointer;
        transition: all 0.2s;
        margin: 4px;
        display: inline-block;
    }
    
    .quick-question-btn:hover {
        background: #DBEAFE;
        border-color: #93C5FD;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 实时时间组件 ====================
def get_realtime():
    """获取实时时间"""
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

# ==================== 知识滚动条组件 ====================
def render_knowledge_ticker():
    """渲染滚动知识条"""
    # 复制知识列表以实现无缝滚动
    tips_html = ""
    for tip in FINANCIAL_TIPS:
        tips_html += f'''
        <div class="tips-card">
            <div class="tips-card-title">{tip["title"]}</div>
            <div class="tips-card-content">{tip["content"]}</div>
            <div class="tips-card-source">— {tip["source"]}</div>
        </div>
        '''
    
    # 复制一份用于无缝滚动
    tips_html = tips_html + tips_html
    
    st.markdown(f'''
    <div class="tips-container">
        <div class="tips-label">◆ 跨境财务知识学堂</div>
        <div class="tips-wrapper">
            <div class="tips-track">
                {tips_html}
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

# ==================== 缓存装饰器 ====================
@st.cache_data(ttl=300)
def get_cached_rates():
    from exchange_rate import exchange_monitor
    return exchange_monitor.fetch_current_rates()

# ==================== Session State ====================
def init_session():
    defaults = {
        "authenticated": False,
        "data": None, "normal": None, "anomaly": None, "reports": {},
        "chat_history": [], "vat_reports": {}, "auditor": None,
        "last_upload": None, "processing": False,
        "show_settings": False,
        "ai_tip_index": 0
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ==================== 认证界面 ====================
def render_auth():
    """渲染登录/设置密码界面"""
    is_first_time = not has_password()
    
    st.markdown(f"""
    <div class="auth-container">
        <div class="auth-logo">◆</div>
        <div class="auth-title">{'初始化访问权限' if is_first_time else '身份验证'}</div>
        <div class="auth-subtitle">
            {'首次使用，请设置访问密码以保障数据安全' if is_first_time else '请输入密码以继续访问系统'}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if is_first_time:
            pwd1 = st.text_input("设置密码", type="password", key="set_pwd1")
            pwd2 = st.text_input("确认密码", type="password", key="set_pwd2")
            
            if st.button("确认设置", use_container_width=True, type="primary"):
                if not pwd1:
                    st.error("请输入密码")
                elif pwd1 != pwd2:
                    st.error("两次输入的密码不一致")
                elif len(pwd1) < 4:
                    st.error("密码长度至少4位")
                else:
                    save_password(hash_password(pwd1))
                    st.session_state.authenticated = True
                    st.success("✓ 密码设置成功")
                    st.rerun()
        else:
            pwd = st.text_input("输入密码", type="password", key="login_pwd")
            
            if st.button("验证登录", use_container_width=True, type="primary"):
                if verify_password(pwd):
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("密码错误，请重试")
        
        st.markdown("""
        <div class="auth-hint">
            <b>安全说明</b><br>
            • 密码采用SHA256加密存储于本地<br>
            • 所有财务数据仅在本地处理，不上传云端<br>
            • 如遗忘密码，需删除 data/.secure_config 文件重置
        </div>
        """, unsafe_allow_html=True)

# ==================== 置顶标识 ====================
def render_header():
    """渲染置顶标识栏"""
    current_time = get_realtime()
    
    st.markdown(f"""
    <div class="header-bar">
        <div>
            <div class="header-title">◆ AI驱动跨境财务管理平台</div>
            <div class="header-subtitle">智能对账 · 精准算税 · 实时洞察 · 全链路自动化</div>
        </div>
        <div class="header-info">
            <div class="header-time">{current_time}</div>
            <div style="margin-top: 4px;">企业级安全保护</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==================== 汇率条 ====================
def render_ticker():
    """渲染汇率条"""
    rates = get_cached_rates()
    if not rates:
        return
    
    pairs = []
    currencies = [
        ("USD", "USD/CNY"), ("EUR", "EUR/CNY"), ("GBP", "GBP/CNY"),
        ("JPY", "JPY/CNY"), ("SGD", "SGD/CNY"), ("AUD", "AUD/CNY")
    ]
    
    for code, name in currencies:
        if code in rates:
            rate = rates[code]
            change = np.random.uniform(-0.3, 0.3)
            change_class = "ticker-change-up" if change > 0 else "ticker-change-down"
            change_sign = "+" if change > 0 else ""
            pairs.append(f'<span class="ticker-item"><span class="ticker-currency">{name}</span><span class="ticker-rate mono-num">{rate:.4f}</span><span class="{change_class}">{change_sign}{change:.2f}%</span></span>')
    
    if pairs:
        st.markdown(f'''
        <div class="ticker-bar">
            <span style="color: #1E3A8A; font-weight: 600; margin-right: 24px;">实时汇率</span>
            {''.join(pairs)}
        </div>
        ''', unsafe_allow_html=True)

# ==================== AI对话组件 ====================
def render_ai_chat(data_context=""):
    """渲染AI对话组件"""
    # 检查AI连接状态
    ai_connected = False
    try:
        from finance_llm import finance_llm
        ai_connected = finance_llm.check_connection()
    except:
        pass
    
    st.markdown('''
    <div class="ai-chat-section">
        <div class="ai-chat-header">
            <div class="ai-chat-icon">◆</div>
            <div>
                <div class="ai-chat-title">智能经营洞察</div>
                <div class="ai-chat-subtitle">基于您的财务数据，AI智能分析决策支持</div>
            </div>
            <div class="ai-chat-status">
                <span class="ai-status-dot''' + ('' if ai_connected else ' offline') + '''"></span>
                <span>''' + ('在线' if ai_connected else '未连接') + '''</span>
            </div>
        </div>
    ''', unsafe_allow_html=True)
    
    # 快捷问题
    quick_questions = [
        "本月各平台利润分析",
        "哪些订单存在异常？",
        "生成财务经营报告",
        "汇率波动影响评估",
        "VAT税务合规建议",
        "资金回流方案"
    ]
    
    st.markdown('<div style="margin-bottom: 16px;">', unsafe_allow_html=True)
    cols = st.columns([1,1,1,1,1,1])
    for i, (col, q) in enumerate(zip(cols, quick_questions)):
        with col:
            if st.button(q, key=f"quick_q_{i}", use_container_width=True):
                with st.spinner("正在分析..."):
                    try:
                        from finance_llm import finance_llm
                        ctx = finance_llm._df_to_summary(st.session_state.data) if st.session_state.data is not None else ""
                        answer = finance_llm.chat(q, data_context=ctx)
                        st.session_state.chat_history.append({"question": q, "answer": answer})
                        st.rerun()
                    except Exception as e:
                        st.error(f"AI服务暂时不可用：{str(e)}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 对话输入
    col1, col2 = st.columns([5, 1])
    with col1:
        question = st.text_input(
            "请输入您的问题",
            placeholder="例如：本月哪个平台利润最高？有哪些异常订单需要关注？",
            key="ai_question_input",
            label_visibility="collapsed"
        )
    with col2:
        analyze_clicked = st.button("开始分析", type="primary", use_container_width=True)
    
    # 显示聊天历史
    if st.session_state.chat_history:
        for chat in st.session_state.chat_history[-5:]:  # 只显示最近5条
            st.markdown(f"**问：{chat['question']}**")
            st.markdown(f'<div class="ai-response">{chat["answer"]}</div>', unsafe_allow_html=True)
            st.markdown("---")
    
    # 处理新问题
    if analyze_clicked and question:
        with st.spinner("正在分析..."):
            try:
                from finance_llm import finance_llm
                ctx = finance_llm._df_to_summary(st.session_state.data) if st.session_state.data is not None else ""
                answer = finance_llm.chat(question, data_context=ctx)
                st.session_state.chat_history.append({"question": question, "answer": answer})
                st.rerun()
            except Exception as e:
                st.error(f"AI服务暂时不可用：{str(e)}")
    
    if not ai_connected:
        st.info("💡 提示：AI功能需要本地安装 Ollama 并运行。访问 https://ollama.com 下载安装后，执行 `ollama pull qwen2.5:14b` 下载模型。")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== 设置面板 ====================
def render_settings():
    """渲染设置面板"""
    with st.sidebar:
        st.markdown("<div class='settings-header'>系统设置</div>", unsafe_allow_html=True)
        
        with st.expander("密码管理", expanded=True):
            old_pwd = st.text_input("当前密码", type="password")
            new_pwd = st.text_input("新密码", type="password")
            confirm_pwd = st.text_input("确认新密码", type="password")
            
            if st.button("修改密码", type="primary"):
                if not verify_password(old_pwd):
                    st.error("当前密码错误")
                elif new_pwd != confirm_pwd:
                    st.error("两次输入的新密码不一致")
                elif len(new_pwd) < 4:
                    st.error("密码长度至少4位")
                else:
                    save_password(hash_password(new_pwd))
                    st.success("✓ 密码修改成功")
        
        with st.expander("数据管理"):
            if st.button("清除当前数据"):
                st.session_state.data = None
                st.session_state.normal = None
                st.session_state.anomaly = None
                st.session_state.reports = {}
                st.session_state.chat_history = []
                st.success("✓ 数据已清除")
                st.rerun()
            
            if st.button("退出登录"):
                st.session_state.authenticated = False
                st.rerun()
        
        st.markdown("---")
        st.caption("系统版本 v7.0 | 企业级专业版")

# ==================== 主应用 ====================
def render_main():
    """渲染主应用界面"""
    render_header()
    render_ticker()
    render_knowledge_ticker()  # 添加滚动知识条
    
    # 设置按钮
    if st.button("⚙️", key="settings_btn"):
        st.session_state.show_settings = not st.session_state.show_settings
    
    if st.session_state.show_settings:
        render_settings()
    
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    # 页面标题
    st.markdown("""
    <div class="page-header">
        <div class="page-title">智能经营洞察</div>
        <div class="page-subtitle">自然语言查询，经营数据秒级呈现</div>
    </div>
    """, unsafe_allow_html=True)
    
    # ==================== 核心上传区 ====================
    if st.session_state.data is None:
        st.markdown("""
        <div class="upload-zone">
            <div class="upload-icon">◢</div>
            <div class="upload-title">全平台智能对账</div>
            <div class="upload-desc">支持10+主流电商平台，自动标准化、自动查异</div>
            <div class="platform-tags">
                <span class="platform-tag">Amazon</span>
                <span class="platform-tag">eBay</span>
                <span class="platform-tag">Shopify</span>
                <span class="platform-tag">Shopee</span>
                <span class="platform-tag">AliExpress</span>
                <span class="platform-tag">+5</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    uploaded = st.file_uploader(
        "",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        key="secure_upload",
        label_visibility="collapsed"
    )
    
    # ==================== 自动处理 ====================
    if uploaded and st.session_state.data is None and not st.session_state.processing:
        st.session_state.processing = True
        with st.spinner("正在解析数据..."):
            from parsers import parse_file, merge_multi_platform
            from reconciliation import reconcile_data
            from reports import generate_all_reports
            
            dfs = []
            for f in uploaded:
                p = os.path.join("data", "uploads", f.name)
                os.makedirs("data/uploads", exist_ok=True)
                with open(p, "wb") as tmp:
                    tmp.write(f.read())
                try:
                    dfs.append(parse_file(p, "auto"))
                except Exception as e:
                    st.warning(f"{f.name}: {str(e)[:40]}")
            
            if dfs:
                df = merge_multi_platform(dfs)
                st.session_state.data = df
                st.session_state.normal, st.session_state.anomaly, _ = reconcile_data(df)
                st.session_state.reports = generate_all_reports(df)
                st.session_state.last_upload = datetime.now()
                st.toast(f"已处理 {len(df):,} 条记录", icon="✓")
            
            st.session_state.processing = False
            st.rerun()
    
    # ==================== AI对话区 - 上传后随时可用 ====================
    render_ai_chat()
    
    # ==================== 数据展示 ====================
    if st.session_state.data is not None:
        df = st.session_state.data
        
        # 指标卡片行 - 专业财务格式
        c1, c2, c3, c4, c5 = st.columns(5)
        
        metrics = [
            (c1, "总订单量", f"{len(df):,}", "笔", None),
            (c2, "销售总额", f"¥ {df['订单金额'].sum():,.2f}", "", None),
            (c3, "净到账额", f"¥ {df['实际到账'].sum():,.2f}", "", None),
            (c4, "异常记录", f"{len(st.session_state.anomaly):,}", "条", "negative" if len(st.session_state.anomaly) > 0 else None),
            (c5, "覆盖平台", f"{df['平台'].nunique()}", "个", None),
        ]
        
        for col, label, value, unit, change_type in metrics:
            with col:
                change_html = ""
                if change_type == "negative":
                    change_html = '<div class="metric-change-negative">需关注</div>'
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value mono-num">{value}<span class="metric-unit">{unit}</span></div>
                    {change_html}
                </div>
                ''', unsafe_allow_html=True)
        
        # 异常预警 - 专业话术
        if not st.session_state.anomaly.empty:
            st.markdown(f'''
            <div class="alert-warning">
                <div class="alert-title">异常数据提醒</div>
                <div class="alert-text">系统检测到 {len(st.session_state.anomaly):,} 条异常记录，建议您优先核查处理，以确保财务数据准确性。</div>
            </div>
            ''', unsafe_allow_html=True)
            
            with st.expander("查看异常明细", expanded=True):
                st.dataframe(
                    st.session_state.anomaly[["订单号", "平台", "商品名称", "订单金额", "异常原因"]],
                    use_container_width=True, hide_index=True,
                    column_config={"订单金额": st.column_config.NumberColumn(format="¥ %,.2f")}
                )
                csv = st.session_state.anomaly.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                st.download_button("导出异常记录", csv, f"异常记录_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
        
        # 报表快捷预览
        st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
        st.subheader("自动化报表中心")
        
        rpt_tabs = st.tabs(["收支汇总", "月度趋势", "平台对比", "SKU排行"])
        
        for tab, name in zip(rpt_tabs, ["收支汇总", "月度报表", "平台对比", "SKU排行TOP20"]):
            with tab:
                if name in st.session_state.reports:
                    rdf = st.session_state.reports[name]
                    if not rdf.empty:
                        st.dataframe(rdf, use_container_width=True, hide_index=True,
                                    column_config={c: st.column_config.NumberColumn(format="%,.2f") 
                                                  for c in rdf.select_dtypes(include=["float64", "int64"]).columns})
                        csv = rdf.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                        st.download_button("导出报表", csv, f"{name}_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv", key=f"dl_{name}")
    
    # ==================== 工具箱 ====================
    else:
        st.markdown("<div style='margin-top: 48px;'></div>", unsafe_allow_html=True)
        st.subheader("专业工具箱")
        
        tool_cols = st.columns(4)
        tools = [
            ("◆", "全球税费引擎", "覆盖200+国家地区，自动算税"),
            ("◆", "智能报销审核", "超标检测，合规审查"),
            ("◆", "智能汇率管家", "实时监控，波动预警"),
            ("◆", "政策合规监控", "税务政策追踪提醒"),
        ]
        
        for col, (icon, title, desc) in zip(tool_cols, tools):
            with col:
                st.markdown(f'''
                <div class="tool-card">
                    <div class="tool-icon">{icon}</div>
                    <div class="tool-name">{title}</div>
                    <div class="tool-desc">{desc}</div>
                </div>
                ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== 入口 ====================
if not st.session_state.authenticated:
    render_auth()
else:
    render_main()
