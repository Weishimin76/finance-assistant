# -*- coding: utf-8 -*-
"""
AI驱动跨境财务管理平台 v9.1 - 优化升级版
核心升级：
1. 延迟加载优化（AI引擎、报表生成器、平台费率库按需加载）
2. 汇率数据缓存到session state
3. 文件上传后操作引导区域
4. 网络状态显示、关键汇率对、固定知识轮播高度
5. AI对话"正在思考..."加载状态
6. 增强错误处理
"""

import streamlit as st
import pandas as pd
import os
import time
import io
from datetime import datetime

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="AI驱动跨境财务管理平台 v9.1",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== 初始化数据库 ====================
from database import init_db, register_user, login_user, get_user, save_user_data, get_user_data, save_chat, get_chat_history
try:
    init_db()
except Exception as e:
    print(f"[WARN] Database init failed: {e}")

# ==================== 延迟导入模块（按需加载）====================
# 核心解析器和基础工具立即加载
from parsers import parse_file

# 延迟加载的模块 - 使用函数封装
@st.cache_data(ttl=1800)
def _cached_exchange_rates():
    """缓存汇率数据30分钟"""
    try:
        from realtime_data import get_exchange_rates
        return get_exchange_rates()
    except Exception:
        return {"rates": {}, "base": "USD", "updated_at": None, "source": "none"}

@st.cache_data(ttl=3600)
def _cached_vat_rates():
    """缓存VAT税率数据1小时"""
    try:
        from realtime_data import get_vat_rates
        return get_vat_rates()
    except Exception:
        return {"rates": {}}

@st.cache_data(ttl=300)
def _cached_data_status():
    """缓存数据状态5分钟"""
    try:
        from realtime_data import get_data_status
        return get_data_status()
    except Exception:
        return {"network": False}

def _get_finance_ai():
    """延迟加载AI引擎"""
    if st.session_state.get("ai_engine") is None:
        from ai_engine import FinanceAI
        st.session_state.ai_engine = FinanceAI()
    return st.session_state.ai_engine

def _get_report_generator():
    """延迟加载报表生成器"""
    try:
        from report_generator import generate_profit_report, generate_full_report, create_revenue_chart, create_cost_pie, create_platform_comparison, create_profit_gauge
        return {
            "generate_profit_report": generate_profit_report,
            "generate_full_report": generate_full_report,
            "create_revenue_chart": create_revenue_chart,
            "create_cost_pie": create_cost_pie,
            "create_platform_comparison": create_platform_comparison,
            "create_profit_gauge": create_profit_gauge,
        }
    except Exception:
        return None

def _get_platform_fees():
    """延迟加载平台费率库"""
    try:
        from platform_fees import get_all_platforms, get_platform_detail, calculate_platform_commission, search_platform, compare_platforms
        return {
            "get_all_platforms": get_all_platforms,
            "get_platform_detail": get_platform_detail,
            "calculate_platform_commission": calculate_platform_commission,
            "search_platform": search_platform,
            "compare_platforms": compare_platforms,
        }
    except Exception:
        return None

def _get_realtime_data():
    """延迟加载实时数据模块"""
    try:
        from realtime_data import get_exchange_rates, get_vat_rates, get_data_status, auto_update, check_network, get_china_tax_rates, get_us_sales_tax, convert_currency
        return {
            "get_exchange_rates": get_exchange_rates,
            "get_vat_rates": get_vat_rates,
            "get_data_status": get_data_status,
            "auto_update": auto_update,
            "check_network": check_network,
            "get_china_tax_rates": get_china_tax_rates,
            "get_us_sales_tax": get_us_sales_tax,
            "convert_currency": convert_currency,
        }
    except Exception:
        return None

def _get_financial_knowledge():
    """延迟加载财务知识库"""
    try:
        from financial_knowledge import search_knowledge, get_random_tip
        return {"search_knowledge": search_knowledge, "get_random_tip": get_random_tip}
    except Exception:
        return None

# ==================== 启动时自动更新数据（非阻塞）====================
try:
    rt = _get_realtime_data()
    if rt:
        rt["auto_update"]()
except Exception:
    pass

# ==================== CSS样式 ====================
st.markdown("""
<style>
    /* 隐藏Streamlit默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    .stApp {padding-top: 0;}

    /* 全局字体 */
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;600&family=Noto+Sans+SC:wght@300;400;500;700&display=swap');

    /* 主容器 */
    .main-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 0 20px;
    }

    /* 顶部标识栏 */
    .top-bar {
        background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 100%);
        color: white;
        padding: 12px 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-radius: 0 0 12px 12px;
        margin-bottom: 0;
        box-shadow: 0 2px 12px rgba(30, 58, 138, 0.3);
    }
    .top-bar .logo {
        font-size: 20px;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .top-bar .logo span {
        color: #60A5FA;
    }
    .top-bar .user-info {
        display: flex;
        align-items: center;
        gap: 16px;
        font-size: 14px;
    }
    .top-bar .time-display {
        font-family: 'Roboto Mono', monospace;
        color: #93C5FD;
    }
    .network-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 4px;
        vertical-align: middle;
    }
    .network-online { background: #10B981; box-shadow: 0 0 6px #10B981; }
    .network-offline { background: #EF4444; box-shadow: 0 0 6px #EF4444; }

    /* 数据状态栏 */
    .data-status-bar {
        background: #F8FAFC;
        padding: 6px 24px;
        font-size: 12px;
        color: #6B7280;
        border-bottom: 1px solid #E5E7EB;
        display: flex;
        justify-content: center;
        gap: 32px;
        flex-wrap: wrap;
    }
    .data-status-bar .status-item {
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
    .data-status-bar .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
    }
    .status-green { background: #10B981; }
    .status-yellow { background: #F59E0B; }
    .status-red { background: #EF4444; }

    /* 汇率条 */
    .rate-bar {
        background: #F0F4FF;
        padding: 8px 24px;
        display: flex;
        justify-content: center;
        gap: 32px;
        font-size: 13px;
        border-bottom: 1px solid #E0E7FF;
        flex-wrap: wrap;
    }
    .rate-item {
        color: #374151;
        font-family: 'Roboto Mono', monospace;
    }
    .rate-item .rate-label {
        color: #6B7280;
        margin-right: 4px;
    }
    .rate-item .rate-value {
        color: #1E3A8A;
        font-weight: 600;
    }
    .rate-item .rate-up { color: #10B981; }
    .rate-item .rate-down { color: #EF4444; }

    /* 知识轮播条 - 固定高度 */
    .knowledge-bar {
        background: linear-gradient(90deg, #1E3A8A, #2563EB);
        color: white;
        padding: 10px 24px;
        text-align: center;
        font-size: 13px;
        letter-spacing: 0.5px;
        min-height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-sizing: border-box;
    }
    .knowledge-bar .tip-icon {
        margin-right: 8px;
    }

    /* Tab样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #F8FAFC;
        padding: 8px 16px;
        border-radius: 12px 12px 0 0;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 500;
        color: #6B7280;
        background: transparent;
    }
    .stTabs [aria-selected="true"] {
        background: #1E3A8A !important;
        color: white !important;
        border-radius: 8px;
    }

    /* 指标卡片 */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        border: 1px solid #E5E7EB;
        text-align: center;
    }
    .metric-card .metric-value {
        font-family: 'Roboto Mono', monospace;
        font-size: 24px;
        font-weight: 700;
        margin: 4px 0;
    }
    .metric-card .metric-label {
        font-size: 13px;
        color: #6B7280;
    }
    .metric-card .metric-positive { color: #10B981; }
    .metric-card .metric-negative { color: #EF4444; }
    .metric-card .metric-neutral { color: #1E3A8A; }

    /* 上传区域 */
    .upload-area {
        border: 2px dashed #93C5FD;
        border-radius: 16px;
        padding: 40px;
        text-align: center;
        background: linear-gradient(135deg, #F0F7FF 0%, #EFF6FF 100%);
        transition: all 0.3s;
    }
    .upload-area:hover {
        border-color: #3B82F6;
        background: linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%);
    }

    /* AI对话区域 */
    .chat-container {
        background: #F8FAFC;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #E5E7EB;
        max-height: 500px;
        overflow-y: auto;
    }
    .chat-msg-user {
        background: #1E3A8A;
        color: white;
        padding: 10px 16px;
        border-radius: 12px 12px 0 12px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
        font-size: 14px;
    }
    .chat-msg-ai {
        background: white;
        color: #1F2937;
        padding: 10px 16px;
        border-radius: 12px 12px 12px 0;
        margin: 8px 0;
        max-width: 80%;
        font-size: 14px;
        border: 1px solid #E5E7EB;
        line-height: 1.6;
    }
    .chat-msg-time {
        font-size: 11px;
        color: #9CA3AF;
        margin-top: 2px;
    }

    /* 快捷问题按钮 */
    .quick-btn {
        display: inline-block;
        background: #EFF6FF;
        color: #1E3A8A;
        border: 1px solid #BFDBFE;
        border-radius: 20px;
        padding: 6px 16px;
        font-size: 13px;
        cursor: pointer;
        transition: all 0.2s;
        margin: 4px;
    }
    .quick-btn:hover {
        background: #1E3A8A;
        color: white;
    }

    /* 异常预警 */
    .alert-warning {
        background: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin: 8px 0;
        font-size: 14px;
    }
    .alert-danger {
        background: #FEE2E2;
        border-left: 4px solid #EF4444;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin: 8px 0;
        font-size: 14px;
    }
    .alert-success {
        background: #D1FAE5;
        border-left: 4px solid #10B981;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin: 8px 0;
        font-size: 14px;
    }

    /* 登录页面 */
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 50%, #1E40AF 100%);
    }
    .login-card {
        background: white;
        border-radius: 20px;
        padding: 40px;
        width: 420px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    .login-card h1 {
        color: #1E3A8A;
        text-align: center;
        font-size: 24px;
        margin-bottom: 8px;
    }
    .login-card .subtitle {
        color: #6B7280;
        text-align: center;
        font-size: 14px;
        margin-bottom: 24px;
    }

    /* VAT税率表 */
    .vat-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
    }
    .vat-table th {
        background: #1E3A8A;
        color: white;
        padding: 10px 16px;
        text-align: left;
    }
    .vat-table td {
        padding: 8px 16px;
        border-bottom: 1px solid #E5E7EB;
    }
    .vat-table tr:nth-child(even) {
        background: #F8FAFC;
    }

    /* 发送按钮 - 大且醒目 */
    div[data-testid="stButton"] > button[kind="primary"] {
        background: #1E3A8A;
        border-color: #1E3A8A;
        font-weight: 600;
        padding: 8px 32px;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background: #2563EB;
        border-color: #2563EB;
    }

    /* 数据表格美化 */
    .dataframe-container {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #E5E7EB;
    }

    /* 金额颜色 */
    .amount-positive { color: #10B981; font-family: 'Roboto Mono', monospace; }
    .amount-negative { color: #EF4444; font-family: 'Roboto Mono', monospace; }
    .amount-neutral { color: #1E3A8A; font-family: 'Roboto Mono', monospace; }

    /* 滚动条 */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #F1F5F9; }
    ::-webkit-scrollbar-thumb { background: #94A3B8; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #64748B; }

    /* 平台详情卡片 */
    .platform-detail-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .platform-detail-card h3 {
        color: #1E3A8A;
        margin-bottom: 12px;
    }

    /* 导出按钮区域 */
    .export-area {
        display: flex;
        gap: 12px;
        margin: 16px 0;
        flex-wrap: wrap;
    }

    /* 操作引导区域 */
    .action-guide {
        background: linear-gradient(135deg, #F0F7FF 0%, #EFF6FF 100%);
        border-radius: 16px;
        padding: 24px;
        border: 1px solid #BFDBFE;
        margin: 16px 0;
    }
    .action-guide h4 {
        color: #1E3A8A;
        margin-bottom: 16px;
    }
    .action-btn-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
    }
    @media (max-width: 768px) {
        .action-btn-grid { grid-template-columns: repeat(2, 1fr); }
    }

    /* 数据概览卡片 */
    .data-overview {
        background: white;
        border-radius: 12px;
        padding: 16px 20px;
        border: 1px solid #E5E7EB;
        margin-bottom: 16px;
    }
    .data-overview-item {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        margin-right: 24px;
        font-size: 14px;
        color: #374151;
    }
    .data-overview-label {
        color: #6B7280;
    }
    .data-overview-value {
        font-weight: 600;
        color: #1E3A8A;
        font-family: 'Roboto Mono', monospace;
    }

    /* 正在思考动画 */
    .thinking-indicator {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #6B7280;
        font-size: 14px;
        padding: 12px 16px;
        background: #F3F4F6;
        border-radius: 12px;
        max-width: 200px;
    }
    .thinking-dots {
        display: flex;
        gap: 4px;
    }
    .thinking-dots span {
        width: 8px;
        height: 8px;
        background: #1E3A8A;
        border-radius: 50%;
        animation: thinking-bounce 1.4s infinite ease-in-out both;
    }
    .thinking-dots span:nth-child(1) { animation-delay: -0.32s; }
    .thinking-dots span:nth-child(2) { animation-delay: -0.16s; }
    @keyframes thinking-bounce {
        0%, 80%, 100% { transform: scale(0); }
        40% { transform: scale(1); }
    }
</style>
""", unsafe_allow_html=True)


# ==================== 工具函数 ====================
def format_amount(value, currency="CNY"):
    """格式化金额：千分位、币种符号、2位小数"""
    symbols = {"CNY": "¥", "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "SGD": "S$", "AUD": "A$", "CAD": "C$", "HKD": "HK$"}
    symbol = symbols.get(currency, currency + " ")
    try:
        val = float(value)
        if val >= 0:
            return f"{symbol}{val:,.2f}"
        else:
            return f"-{symbol}{abs(val):,.2f}"
    except (ValueError, TypeError):
        return f"{symbol}0.00"


def format_amount_colored(value, currency="CNY"):
    """格式化金额并带颜色"""
    try:
        val = float(value)
        if val > 0:
            return f'<span class="amount-positive">{format_amount(value, currency)}</span>'
        elif val < 0:
            return f'<span class="amount-negative">{format_amount(value, currency)}</span>'
        else:
            return f'<span class="amount-neutral">{format_amount(value, currency)}</span>'
    except (ValueError, TypeError):
        return f'<span class="amount-neutral">{format_amount(value, currency)}</span>'


def get_current_time():
    """获取当前时间字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def init_session_defaults():
    """初始化session_state默认值"""
    defaults = {
        "user_id": None,
        "username": "",
        "user_info": None,
        "parsed_data": None,
        "normal_data": None,
        "anomaly_data": None,
        "anomaly_summary": None,
        "reports": {},
        "chat_messages": [],
        "ai_engine": None,
        "file_hash": None,
        "exchange_data": None,
        "vat_data": None,
        "data_status": None,
        "last_data_refresh": 0,
        "upload_action": None,
        "is_processing": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# 初始化session state
init_session_defaults()


# ==================== 数据刷新管理 ====================
def refresh_realtime_data():
    """检查并刷新实时数据（30分钟间隔）"""
    now = time.time()
    if now - st.session_state.last_data_refresh > 30 * 60:
        try:
            st.session_state.exchange_data = _cached_exchange_rates()
            st.session_state.vat_data = _cached_vat_rates()
            st.session_state.data_status = _cached_data_status()
            st.session_state.last_data_refresh = now
        except Exception:
            pass
    # 首次加载
    if st.session_state.exchange_data is None:
        try:
            st.session_state.exchange_data = _cached_exchange_rates()
        except Exception:
            st.session_state.exchange_data = {"rates": {}, "base": "USD", "updated_at": None, "source": "none"}
    if st.session_state.vat_data is None:
        try:
            st.session_state.vat_data = _cached_vat_rates()
        except Exception:
            st.session_state.vat_data = {"rates": {}}
    if st.session_state.data_status is None:
        try:
            st.session_state.data_status = _cached_data_status()
        except Exception:
            st.session_state.data_status = {"network": False}


def check_network_status():
    """检查网络状态（使用延迟加载模块）"""
    rt = _get_realtime_data()
    if rt:
        try:
            return rt["check_network"]()
        except Exception:
            pass
    # 回退到session状态
    status = st.session_state.data_status
    return status.get("network", False) if status else False


# ==================== 登录/注册页面 ====================
def show_login_page():
    """显示登录/注册页面"""
    st.markdown("""
    <div class="login-container">
        <div class="login-card">
            <h1>◆ AI跨境财务管理平台</h1>
            <p class="subtitle">v9.1 优化升级版 · 实时数据 · 22平台费率 · Excel报表 · 可视化图表</p>
    """, unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["登录", "注册"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("用户名", placeholder="请输入用户名", key="login_username")
            password = st.text_input("密码", type="password", placeholder="请输入密码", key="login_password")
            submitted = st.form_submit_button("登 录", use_container_width=True, type="primary")
            if submitted:
                if not username or not password:
                    st.error("请输入用户名和密码")
                else:
                    user_id = login_user(username, password)
                    if user_id:
                        st.session_state.user_id = user_id
                        st.session_state.username = username
                        st.session_state.user_info = get_user(user_id)
                        st.success("登录成功！")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("用户名或密码错误")

    with tab_register:
        with st.form("register_form"):
            reg_username = st.text_input("用户名", placeholder="请设置用户名", key="reg_username")
            reg_password = st.text_input("密码", type="password", placeholder="请设置密码（至少6位）", key="reg_password")
            reg_confirm = st.text_input("确认密码", type="password", placeholder="请再次输入密码", key="reg_confirm")
            reg_email = st.text_input("邮箱", placeholder="请输入邮箱地址", key="reg_email")
            reg_company = st.text_input("公司名称", placeholder="请输入公司名称", key="reg_company")
            reg_submitted = st.form_submit_button("注 册", use_container_width=True, type="primary")
            if reg_submitted:
                if not reg_username or not reg_password:
                    st.error("用户名和密码不能为空")
                elif len(reg_password) < 6:
                    st.error("密码长度至少6位")
                elif reg_password != reg_confirm:
                    st.error("两次输入的密码不一致")
                elif not reg_email or "@" not in reg_email:
                    st.error("请输入有效的邮箱地址")
                elif not reg_company:
                    st.error("请输入公司名称")
                else:
                    user_id = register_user(reg_username, reg_password, reg_email, reg_company)
                    if user_id:
                        st.success("注册成功！请切换到登录标签页登录")
                    else:
                        st.error("用户名已存在，请更换")

    st.markdown("</div></div>", unsafe_allow_html=True)


# ==================== 顶部标识栏 ====================
def show_top_bar():
    """显示顶部标识栏"""
    current_time = get_current_time()
    username = st.session_state.get("username", "")
    company = ""
    if st.session_state.get("user_info"):
        company = st.session_state.user_info.get("company", "")

    # 网络状态
    network_ok = check_network_status()
    network_class = "network-online" if network_ok else "network-offline"
    network_text = "在线" if network_ok else "离线"

    col_left, col_right = st.columns([3, 1])
    with col_left:
        st.markdown("""
        <div class="top-bar">
            <div class="logo">◆ <span>AI跨境财务管理平台</span> v9.1</div>
        </div>
        """, unsafe_allow_html=True)
    with col_right:
        st.markdown(f"""
        <div class="top-bar">
            <div class="user-info">
                <span class="time-display">{current_time}</span>
                <span>{username}</span>
                <span style="color:#93C5FD; font-size:12px;">{company}</span>
                <span class="network-dot {network_class}"></span>
                <span style="font-size:12px;">{network_text}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ==================== 数据状态栏 ====================
def show_data_status_bar():
    """显示数据状态栏"""
    refresh_realtime_data()

    ex_data = st.session_state.exchange_data
    vat_data = st.session_state.vat_data
    status = st.session_state.data_status

    ex_time = "未更新"
    if ex_data and ex_data.get("updated_at"):
        try:
            dt = datetime.fromisoformat(ex_data["updated_at"])
            ex_time = dt.strftime("%H:%M:%S")
        except Exception:
            ex_time = "未知"

    vat_time = "内置数据"
    if vat_data and vat_data.get("updated_at"):
        try:
            dt = datetime.fromisoformat(vat_data["updated_at"])
            vat_time = dt.strftime("%H:%M:%S")
        except Exception:
            vat_time = "未知"

    network_ok = status.get("network", False) if status else False
    net_class = "status-green" if network_ok else "status-red"
    net_text = "在线" if network_ok else "离线"

    ex_source = ex_data.get("source", "无") if ex_data else "无"
    ex_cached = ex_data.get("is_cached", False) if ex_data else False
    ex_class = "status-green" if not ex_cached else "status-yellow"
    if ex_source == "none":
        ex_class = "status-red"

    st.markdown(f"""
    <div class="data-status-bar">
        <span class="status-item">
            <span class="status-dot {ex_class}"></span>
            汇率更新: {ex_time} (来源: {ex_source})
        </span>
        <span class="status-item">
            <span class="status-dot status-green"></span>
            税率更新: {vat_time}
        </span>
        <span class="status-item">
            <span class="status-dot {net_class}"></span>
            网络状态: {net_text}
        </span>
    </div>
    """, unsafe_allow_html=True)


# ==================== 汇率条 ====================
def show_rate_bar():
    """显示汇率条（8组关键货币对）"""
    refresh_realtime_data()
    ex_data = st.session_state.exchange_data
    rates = ex_data.get("rates", {}) if ex_data else {}

    # 8组关键货币对
    pairs = [
        ("USD", "美元"), ("EUR", "欧元"), ("GBP", "英镑"), ("JPY", "日元"),
        ("SGD", "新加坡元"), ("AUD", "澳元"), ("CAD", "加元"), ("HKD", "港币"),
    ]

    rate_items = []
    for code, name in pairs:
        if code in rates:
            val = rates[code]
            rate_items.append(
                f'<span class="rate-item"><span class="rate-label">{name}:</span> '
                f'<span class="rate-value">{val:.4f}</span></span>'
            )

    if rate_items:
        update_time = ""
        if ex_data and ex_data.get("updated_at"):
            try:
                dt = datetime.fromisoformat(ex_data["updated_at"])
                update_time = dt.strftime("%H:%M")
            except Exception:
                pass
        time_label = f" 更新于 {update_time}" if update_time else ""
        st.markdown(
            f'<div class="rate-bar">{"".join(rate_items)}'
            f'<span style="color:#9CA3AF; font-size:11px; margin-left:16px;">{time_label}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        # 备用静态汇率
        st.markdown("""
        <div class="rate-bar">
            <span class="rate-item"><span class="rate-label">美元:</span> <span class="rate-value">7.2450</span></span>
            <span class="rate-item"><span class="rate-label">欧元:</span> <span class="rate-value">7.8920</span></span>
            <span class="rate-item"><span class="rate-label">英镑:</span> <span class="rate-value">9.2150</span></span>
            <span class="rate-item"><span class="rate-label">日元:</span> <span class="rate-value">0.0468</span></span>
            <span class="rate-item"><span class="rate-label">新加坡元:</span> <span class="rate-value">5.3680</span></span>
            <span class="rate-item"><span class="rate-label">澳元:</span> <span class="rate-value">4.7820</span></span>
            <span class="rate-item"><span class="rate-label">加元:</span> <span class="rate-value">5.3120</span></span>
            <span class="rate-item"><span class="rate-label">港币:</span> <span class="rate-value">0.9280</span></span>
        </div>
        """, unsafe_allow_html=True)


# ==================== 知识轮播条 ====================
def show_knowledge_bar():
    """显示知识轮播条（固定高度，避免页面跳动）"""
    fk = _get_financial_knowledge()
    if fk:
        try:
            tip = fk["get_random_tip"]()
        except Exception:
            tip = None
    else:
        tip = None

    if tip:
        tip_text = tip.get("answer", "")[:80]
        category = tip.get("category", "财务知识")
        st.markdown(
            f'<div class="knowledge-bar">'
            f'<span class="tip-icon">&#128161;</span>'
            f'[{category}] {tip_text}...'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        # 固定高度的占位，避免页面跳动
        st.markdown(
            f'<div class="knowledge-bar">'
            f'<span class="tip-icon">&#128161;</span>'
            f'[财务知识] 定期核对各平台账单，确保订单金额与实际到账一致，是财务管理的基础...'
            f'</div>',
            unsafe_allow_html=True
        )


# ==================== 文件处理 ====================
def process_uploaded_files(files):
    """处理上传的文件：解析并展示（增强错误处理）"""
    all_dfs = []
    errors = []
    for f in files:
        save_path = os.path.join("data", "uploads", f.name)
        os.makedirs("data/uploads", exist_ok=True)
        with open(save_path, "wb") as tmp:
            tmp.write(f.getbuffer())
        try:
            parsed = parse_file(save_path, platform="auto")
            all_dfs.append(parsed)
        except ValueError as e:
            error_msg = str(e)
            if "不支持的文件格式" in error_msg:
                errors.append(f"文件格式不支持: {f.name}")
            elif "文件为空" in error_msg:
                errors.append(f"文件为空: {f.name}")
            elif "缺少必要列" in error_msg or "列数过少" in error_msg:
                errors.append(f"文件缺少必要列: {f.name}")
            else:
                errors.append(f"解析 {f.name} 失败: {error_msg[:80]}")
        except Exception as e:
            errors.append(f"解析 {f.name} 时发生未知错误: {str(e)[:80]}")

    # 显示错误信息
    for err in errors:
        st.error(err)

    if not all_dfs:
        if not errors:
            st.error("所有文件解析失败，请检查文件格式")
        return False

    # 合并多平台数据
    if len(all_dfs) == 1:
        df = all_dfs[0]
    else:
        df = pd.concat(all_dfs, ignore_index=True)

    st.session_state.parsed_data = df

    # 计算异常数据
    anomaly_data = []
    total_orders = len(df)
    for col in ["订单金额", "佣金", "实际到账"]:
        if col in df.columns:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                outliers = df[(df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)]
                for _, row in outliers.iterrows():
                    anomaly_data.append({
                        "订单号": row.get("订单号", ""),
                        "平台": row.get("平台", ""),
                        "异常原因": f"{col}异常 ({row[col]:.2f})",
                        "订单金额": row.get("订单金额", 0),
                    })

    st.session_state.anomaly_data = pd.DataFrame(anomaly_data) if anomaly_data else pd.DataFrame()

    # 保存到数据库
    if st.session_state.user_id:
        try:
            save_user_data(
                st.session_state.user_id,
                "parsed_data",
                df.to_json(orient="records", force_ascii=False),
                f.name
            )
        except Exception:
            pass

    return True


def get_data_overview(df):
    """获取数据概览信息"""
    overview = {}
    overview["行数"] = len(df)
    overview["列数"] = len(df.columns)

    # 日期范围
    if "交易日期" in df.columns:
        dates = df["交易日期"].dropna()
        dates = dates[dates != ""]
        if len(dates) > 0:
            try:
                overview["日期范围"] = f"{min(dates)} 至 {max(dates)}"
            except Exception:
                overview["日期范围"] = "未知"
        else:
            overview["日期范围"] = "未知"
    else:
        overview["日期范围"] = "未知"

    # 总金额
    if "订单金额" in df.columns:
        overview["总金额"] = df["订单金额"].sum()
    else:
        overview["总金额"] = 0

    # 平台分布
    if "平台" in df.columns:
        overview["平台"] = df["平台"].value_counts().to_dict()
    else:
        overview["平台"] = {}

    return overview


# ==================== 操作引导区域 ====================
def show_action_guide(df):
    """显示文件上传后的操作引导区域"""
    st.markdown("<div class='action-guide'>", unsafe_allow_html=True)
    st.markdown("#### 您想做什么？")

    actions = [
        ("分析数据并生成报表", "chart_with_upwards_trend", "对数据进行深度分析，生成可视化报表"),
        ("检查异常订单", "warning", "检测价格异常、佣金异常等异常订单"),
        ("计算利润和成本", "moneybag", "计算毛利润、净利润、成本结构分析"),
        ("对比各平台表现", "bar_chart", "对比不同平台的销售额、利润率等指标"),
        ("导出Excel报表", "file_folder", "将数据导出为Excel格式的专业报表"),
        ("询问AI关于这份数据的问题", "robot_face", "向AI助手询问关于这份数据的任何问题"),
    ]

    cols = st.columns(3)
    for i, (label, icon, desc) in enumerate(actions):
        with cols[i % 3]:
            if st.button(label, key=f"action_{i}", use_container_width=True):
                st.session_state.upload_action = label
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def handle_upload_action(df, action):
    """处理用户选择的操作"""
    if action == "分析数据并生成报表":
        st.info("数据已加载，请查看下方的数据表格、收支汇总、月度趋势等标签页。")
    elif action == "检查异常订单":
        if st.session_state.anomaly_data is not None and not st.session_state.anomaly_data.empty:
            st.warning(f"发现 {len(st.session_state.anomaly_data)} 条异常记录，请在下方查看。")
        else:
            st.success("未检测到明显异常订单。")
    elif action == "计算利润和成本":
        total_sales = df["订单金额"].sum() if "订单金额" in df.columns else 0
        total_cost = df["佣金"].sum() if "佣金" in df.columns else 0
        total_net = df["实际到账"].sum() if "实际到账" in df.columns else (total_sales - total_cost)
        st.markdown(f"""
        <div class="data-overview">
            <div class="data-overview-item">
                <span class="data-overview-label">总销售额:</span>
                <span class="data-overview-value">{format_amount(total_sales)}</span>
            </div>
            <div class="data-overview-item">
                <span class="data-overview-label">总成本:</span>
                <span class="data-overview-value">{format_amount(total_cost)}</span>
            </div>
            <div class="data-overview-item">
                <span class="data-overview-label">净利润:</span>
                <span class="data-overview-value">{format_amount(total_net)}</span>
            </div>
            <div class="data-overview-item">
                <span class="data-overview-label">利润率:</span>
                <span class="data-overview-value">{total_net/total_sales*100:.1f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif action == "对比各平台表现":
        st.info("请查看下方的'平台对比'标签页，或使用'AI财务助手'询问平台对比问题。")
    elif action == "导出Excel报表":
        st.info("请使用下方的'导出Excel报表'按钮导出数据。")
    elif action == "询问AI关于这份数据的问题":
        st.info("请切换到'AI财务助手'标签页，输入您关于这份数据的问题。")


# ==================== Tab1: 智能工作台 ====================
def show_workspace():
    """显示智能工作台"""
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # 大上传框（居中，大且明显）
    uploaded_files = st.file_uploader(
        "拖拽或点击上传财务文件（支持CSV、Excel格式）",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        key="workspace_upload",
        label_visibility="visible"
    )

    # 自动处理上传的文件
    if uploaded_files:
        file_names = ",".join([f.name for f in uploaded_files])
        file_sizes = sum([f.size for f in uploaded_files])
        current_hash = f"{file_names}_{file_sizes}"

        if st.session_state.file_hash != current_hash:
            with st.spinner("正在自动解析数据并生成报表..."):
                success = process_uploaded_files(uploaded_files)
            if success:
                st.session_state.file_hash = current_hash
                st.toast(f"已处理 {len(st.session_state.parsed_data)} 条记录", icon="✅")

    # 显示数据结果
    if st.session_state.parsed_data is not None:
        df = st.session_state.parsed_data

        # ---- 数据概览 ----
        overview = get_data_overview(df)
        st.markdown(f"""
        <div class="data-overview">
            <div class="data-overview-item">
                <span class="data-overview-label">数据行数:</span>
                <span class="data-overview-value">{overview['行数']:,}</span>
            </div>
            <div class="data-overview-item">
                <span class="data-overview-label">数据列数:</span>
                <span class="data-overview-value">{overview['列数']}</span>
            </div>
            <div class="data-overview-item">
                <span class="data-overview-label">日期范围:</span>
                <span class="data-overview-value">{overview['日期范围']}</span>
            </div>
            <div class="data-overview-item">
                <span class="data-overview-label">总金额:</span>
                <span class="data-overview-value">{format_amount(overview['总金额'])}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ---- 操作引导区域 ----
        show_action_guide(df)

        # 处理用户选择的操作
        if st.session_state.upload_action:
            handle_upload_action(df, st.session_state.upload_action)
            # 重置操作状态（保留显示但不再重复处理）
            # st.session_state.upload_action = None

        # ---- 数据预览（前5行）----
        with st.expander("数据预览（前5行）", expanded=True):
            display_cols = ["订单号", "平台", "商品名称", "SKU", "数量", "订单金额", "佣金", "实际到账", "交易状态"]
            available_cols = [c for c in display_cols if c in df.columns]
            if not available_cols:
                available_cols = list(df.columns[:10])
            st.dataframe(
                df[available_cols].head(5),
                use_container_width=True,
                hide_index=True,
                column_config={
                    c: st.column_config.NumberColumn(format="%.2f")
                    for c in available_cols if c in ["订单金额", "佣金", "手续费", "运费", "实际到账", "退款金额"]
                }
            )

        # ---- 指标卡片 ----
        total_orders = len(df)
        total_sales = df["订单金额"].sum() if "订单金额" in df.columns else 0
        total_cost = df["佣金"].sum() if "佣金" in df.columns else 0
        total_net = df["实际到账"].sum() if "实际到账" in df.columns else (total_sales - total_cost)
        anomaly_count = len(st.session_state.anomaly_data) if st.session_state.anomaly_data is not None and not st.session_state.anomaly_data.empty else 0

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">总订单数</div>
                <div class="metric-value metric-neutral">{total_orders:,}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            color = "metric-positive" if total_sales >= 0 else "metric-negative"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">总收入</div>
                <div class="metric-value {color}">{format_amount(total_sales)}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            color = "metric-positive" if total_cost >= 0 else "metric-negative"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">总成本</div>
                <div class="metric-value {color}">{format_amount(total_cost)}</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            color = "metric-positive" if total_net >= 0 else "metric-negative"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">净利润</div>
                <div class="metric-value {color}">{format_amount(total_net)}</div>
            </div>
            """, unsafe_allow_html=True)
        with col5:
            alert_color = "metric-negative" if anomaly_count > 0 else "metric-positive"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">异常数</div>
                <div class="metric-value {alert_color}">{anomaly_count}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ---- 异常预警列表 ----
        if st.session_state.anomaly_data is not None and not st.session_state.anomaly_data.empty:
            st.markdown(f"#### 异常预警 ({len(st.session_state.anomaly_data)} 条)")
            show_anomalies = st.session_state.anomaly_data.head(5)
            for _, row in show_anomalies.iterrows():
                reason = row.get("异常原因", "未知异常")
                order_id = row.get("订单号", "")
                platform = row.get("平台", "")
                amount = row.get("订单金额", 0)
                st.markdown(
                    f'<div class="alert-warning">'
                    f'<strong>[{platform}] {order_id}</strong> - '
                    f'{reason} | 金额: {format_amount(amount)}'
                    f'</div>',
                    unsafe_allow_html=True
                )
            if len(st.session_state.anomaly_data) > 5:
                st.info(f"还有 {len(st.session_state.anomaly_data) - 5} 条异常记录，详见下方数据表格")
            st.markdown("<br>", unsafe_allow_html=True)

        # ---- 数据表格 + 报表标签页 ----
        data_tab, summary_tab, trend_tab, platform_tab, sku_tab = st.tabs([
            "数据表格", "收支汇总", "月度趋势", "平台对比", "SKU排行"
        ])

        with data_tab:
            # 导出CSV按钮
            csv_data = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                "导出全部数据(CSV)",
                data=csv_data,
                file_name=f"财务数据_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

            # 显示数据表格
            display_cols = ["订单号", "平台", "商品名称", "SKU", "数量", "订单金额", "佣金", "实际到账", "交易状态"]
            available_cols = [c for c in display_cols if c in df.columns]
            if not available_cols:
                available_cols = list(df.columns[:10])
            st.dataframe(
                df[available_cols],
                use_container_width=True,
                hide_index=True,
                height=400,
                column_config={
                    c: st.column_config.NumberColumn(format="%.2f")
                    for c in available_cols if c in ["订单金额", "佣金", "手续费", "运费", "实际到账", "退款金额"]
                }
            )

        with summary_tab:
            # 收支汇总
            summary_data = {}
            if "平台" in df.columns:
                for plat, group in df.groupby("平台"):
                    rev = group["订单金额"].sum() if "订单金额" in group.columns else 0
                    fee = group["佣金"].sum() if "佣金" in group.columns else 0
                    net = group["实际到账"].sum() if "实际到账" in group.columns else (rev - fee)
                    summary_data[plat] = {
                        "订单数": len(group),
                        "总收入": round(rev, 2),
                        "总佣金": round(fee, 2),
                        "净利润": round(net, 2),
                        "利润率": f"{net/rev*100:.1f}%" if rev > 0 else "N/A",
                    }
            if summary_data:
                st.dataframe(
                    pd.DataFrame(summary_data).T,
                    use_container_width=True,
                    hide_index=True,
                )

        with trend_tab:
            # 月度趋势（使用st.line_chart替代plotly，避免JS错误）
            try:
                if "交易日期" in df.columns:
                    df["月份"] = pd.to_datetime(df["交易日期"], errors="coerce").dt.to_period("M").astype(str)
                    monthly = df.groupby("月份").agg(
                        收入=("订单金额", "sum"),
                        成本=("佣金", "sum"),
                        利润=("实际到账", "sum")
                    ).reset_index()
                    if not monthly.empty:
                        st.line_chart(monthly.set_index("月份")[["收入", "成本", "利润"]])
                    else:
                        st.info("无法生成趋势图：日期格式不正确")
                else:
                    st.info("数据中无交易日期字段，无法生成趋势图")
            except Exception as e:
                st.warning(f"趋势图生成失败: {str(e)[:60]}")

        with platform_tab:
            # 平台对比（使用st.bar_chart替代plotly）
            try:
                if "平台" in df.columns and "订单金额" in df.columns:
                    platform_data = df.groupby("平台")["订单金额"].sum().reset_index()
                    platform_data = platform_data.sort_values("订单金额", ascending=False)
                    if not platform_data.empty:
                        st.bar_chart(platform_data.set_index("平台"))
                    else:
                        st.info("无法生成平台对比图")
                else:
                    st.info("数据中缺少平台或订单金额字段")
            except Exception as e:
                st.warning(f"平台对比图生成失败: {str(e)[:60]}")

        with sku_tab:
            # SKU排行
            if "SKU" in df.columns:
                sku_stats = df.groupby("SKU").agg(
                    订单数=("订单金额", "count"),
                    总收入=("订单金额", "sum"),
                ).reset_index().sort_values("总收入", ascending=False)
                st.dataframe(
                    sku_stats,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "总收入": st.column_config.NumberColumn(format="%.2f"),
                    }
                )
            else:
                st.info("数据中无SKU字段")

        st.markdown("<br>", unsafe_allow_html=True)

        # ---- 导出按钮区域 ----
        st.markdown("#### 导出报表")
        col_exp1, col_exp2 = st.columns(2)

        with col_exp1:
            # 导出Excel报表
            try:
                rg = _get_report_generator()
                if rg:
                    import tempfile
                    temp_dir = tempfile.gettempdir()
                    excel_path = os.path.join(temp_dir, f"profit_report_{st.session_state.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
                    rg["generate_profit_report"](df, excel_path)
                    with open(excel_path, "rb") as f:
                        excel_bytes = f.read()
                    st.download_button(
                        "导出Excel报表",
                        data=excel_bytes,
                        file_name=f"财务报表_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True,
                    )
                else:
                    st.info("报表生成器模块暂不可用")
            except Exception as e:
                st.warning(f"Excel导出失败: {str(e)[:60]}")

        with col_exp2:
            # 导出HTML报告
            try:
                rg = _get_report_generator()
                if rg:
                    import tempfile
                    temp_dir = tempfile.gettempdir()
                    report_result = rg["generate_full_report"](df, st.session_state.user_id or 0, temp_dir)
                    html_path = report_result.get("html", "")
                    if html_path and os.path.exists(html_path):
                        with open(html_path, "rb") as f:
                            html_bytes = f.read()
                        st.download_button(
                            "导出HTML可视化报告",
                            data=html_bytes,
                            file_name=f"财务分析报告_{datetime.now().strftime('%Y%m%d')}.html",
                            mime="text/html",
                            use_container_width=True,
                        )
                    else:
                        st.info("HTML报告生成失败")
                else:
                    st.info("报表生成器模块暂不可用")
            except Exception as e:
                st.warning(f"HTML报告导出失败: {str(e)[:60]}")

    else:
        # 无数据时的引导
        st.markdown("""
        <div class="upload-area">
            <div style="font-size: 48px; margin-bottom: 16px;">&#128193;</div>
            <div style="font-size: 18px; color: #1E3A8A; font-weight: 600; margin-bottom: 8px;">
                拖拽或点击上方区域上传财务文件
            </div>
            <div style="font-size: 14px; color: #6B7280;">
                支持 CSV、Excel 格式 · 自动识别平台 · 上传即分析 · 支持Excel/HTML报表导出
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 功能介绍
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div style="font-size:24px; margin-bottom:8px;">&#128203;</div>
                <div style="font-weight:600; color:#1E3A8A; margin-bottom:4px;">22个平台</div>
                <div style="font-size:13px; color:#6B7280;">
                    Amazon · eBay · Walmart<br>
                    Shopify · Shopee · Temu<br>
                    TikTok Shop · 更多...
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class="metric-card">
                <div style="font-size:24px; margin-bottom:8px;">&#128269;</div>
                <div style="font-weight:600; color:#1E3A8A; margin-bottom:4px;">智能检测</div>
                <div style="font-size:13px; color:#6B7280;">
                    重复订单 · 多扣佣金<br>
                    价格异常 · 退款遗漏
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div class="metric-card">
                <div style="font-size:24px; margin-bottom:8px;">&#128202;</div>
                <div style="font-weight:600; color:#1E3A8A; margin-bottom:4px;">可视化图表</div>
                <div style="font-size:13px; color:#6B7280;">
                    收支汇总 · 月度趋势<br>
                    平台对比 · SKU排行
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown("""
            <div class="metric-card">
                <div style="font-size:24px; margin-bottom:8px;">&#128190;</div>
                <div style="font-weight:600; color:#1E3A8A; margin-bottom:4px;">报表导出</div>
                <div style="font-size:13px; color:#6B7280;">
                    Excel专业报表<br>
                    HTML可视化报告
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ==================== Tab2: AI财务助手 ====================
def show_ai_assistant():
    """显示AI财务助手"""
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # AI引擎状态（延迟加载）
    ai = _get_finance_ai()
    engine_status = ai.get_engine_status()

    # 数据源状态显示
    status_cols = st.columns(4)
    with status_cols[0]:
        kb_status = engine_status.get("knowledge_base", {})
        st.markdown(f"""
        <div class="alert-success">
            <strong>内置知识库</strong>: {kb_status.get('desc', '可用') if isinstance(kb_status, dict) else '可用'} &#128994;
        </div>
        """, unsafe_allow_html=True)
    with status_cols[1]:
        ollama_status = engine_status.get("ollama", {})
        if isinstance(ollama_status, dict) and ollama_status.get("available"):
            st.markdown(f"""
            <div class="alert-success">
                <strong>Ollama</strong>: {ollama_status.get('desc', '可用')} &#128994;
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="alert-warning">
                <strong>Ollama</strong>: 未连接 &#9898;
            </div>
            """, unsafe_allow_html=True)
    with status_cols[2]:
        refresh_realtime_data()
        ex_ok = st.session_state.exchange_data and st.session_state.exchange_data.get("source") != "none"
        st.markdown(f"""
        <div class="alert-success">
            <strong>实时数据</strong>: {'在线 &#128994;' if ex_ok else '离线 &#128308;'}
        </div>
        """, unsafe_allow_html=True)
    with status_cols[3]:
        network_ok = check_network_status()
        st.markdown(f"""
        <div class="alert-success">
            <strong>联网搜索</strong>: {'可用 &#128994;' if network_ok else '不可用 &#128308;'}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 对话历史显示区域
    st.markdown("#### 对话记录")
    chat_container = st.container()

    # 加载历史对话
    if not st.session_state.chat_messages and st.session_state.user_id:
        history = get_chat_history(st.session_state.user_id, limit=20)
        if history:
            for item in reversed(history):
                st.session_state.chat_messages.append({
                    "role": "user",
                    "content": item["question"],
                    "time": item.get("created_at", ""),
                })
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": item["answer"],
                    "time": item.get("created_at", ""),
                })

    # 显示对话历史
    with chat_container:
        if st.session_state.chat_messages:
            for msg in st.session_state.chat_messages:
                if msg["role"] == "user":
                    time_str = f'<div class="chat-msg-time">{msg.get("time", "")}</div>' if msg.get("time") else ""
                    st.markdown(
                        f'<div class="chat-msg-user">{msg["content"]}{time_str}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    time_str = f'<div class="chat-msg-time">{msg.get("time", "")}</div>' if msg.get("time") else ""
                    st.markdown(
                        f'<div class="chat-msg-ai">{msg["content"]}{time_str}</div>',
                        unsafe_allow_html=True
                    )
        else:
            st.info("暂无对话记录，请在下方输入您的问题")

    # 显示"正在思考..."加载状态
    if st.session_state.get("is_processing", False):
        st.markdown("""
        <div class="thinking-indicator">
            <div class="thinking-dots">
                <span></span><span></span><span></span>
            </div>
            <span>AI正在思考...</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 快捷问题按钮（8个）
    st.markdown("#### 快捷问题")
    quick_questions = [
        "本月利润率如何？",
        "VAT申报流程是什么？",
        "Amazon FBA费用怎么算？",
        "各国VAT税率是多少？",
        "各平台佣金对比",
        "汇率波动对利润的影响？",
        "中国增值税怎么计算？",
        "如何降低跨境物流成本？",
    ]
    q_cols = st.columns(4)
    for i, q in enumerate(quick_questions):
        with q_cols[i % 4]:
            if st.button(q, key=f"quick_{i}", use_container_width=True):
                st.session_state.quick_question = q
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 大输入框 + 发送按钮（type="primary"，大且明显）
    input_col, btn_col = st.columns([5, 1])
    with input_col:
        user_input = st.text_area(
            "输入您的财务问题",
            placeholder="例如：本月哪个平台利润最高？如何优化税务成本？VAT申报流程是什么？",
            key="ai_input",
            label_visibility="collapsed",
            height=80,
        )
    with btn_col:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        send_clicked = st.button("发送分析", type="primary", use_container_width=True, key="ai_send")

    # 处理快捷问题
    if "quick_question" in st.session_state and st.session_state.quick_question:
        user_input = st.session_state.quick_question
        st.session_state.quick_question = None
        send_clicked = True

    # 处理发送
    if send_clicked and user_input and user_input.strip():
        question = user_input.strip()
        now_str = get_current_time()

        # 添加用户消息
        st.session_state.chat_messages.append({"role": "user", "content": question, "time": now_str})

        # 构建数据上下文
        data_context = ""
        if st.session_state.parsed_data is not None:
            df = st.session_state.parsed_data
            data_context = (
                f"当前数据概览：\n"
                f"总订单数: {len(df)}\n"
                f"总销售额: {df['订单金额'].sum():,.2f}\n"
                f"总佣金: {df['佣金'].sum():,.2f}\n"
                f"实际到账: {df['实际到账'].sum():,.2f}\n"
                f"平台分布: {df['平台'].value_counts().to_dict()}\n"
                f"币种分布: {df['币种'].value_counts().to_dict()}\n"
            )

        # 调用AI（带"正在思考..."状态）
        st.session_state.is_processing = True
        with st.spinner("AI正在分析..."):
            try:
                answer = ai.chat(question, context=data_context)
            except Exception as e:
                answer = f"抱歉，AI分析过程中出现错误: {str(e)[:100]}。请稍后重试或联系技术支持。"

        st.session_state.is_processing = False

        # 添加AI回复
        st.session_state.chat_messages.append({"role": "assistant", "content": answer, "time": now_str})

        # 保存到数据库
        if st.session_state.user_id:
            try:
                save_chat(st.session_state.user_id, question, answer)
            except Exception:
                pass

        st.rerun()

    # 清空对话按钮
    if st.session_state.chat_messages:
        if st.button("清空对话记录"):
            st.session_state.chat_messages = []
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ==================== Tab3: 平台费率 ====================
def show_platform_fees():
    """显示平台费率"""
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # 延迟加载平台费率模块
    pf = _get_platform_fees()
    if not pf:
        st.error("平台费率模块加载失败，请检查依赖是否安装正确。")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # 获取所有平台
    all_platforms = pf["get_all_platforms"]()
    platform_names = {p["key"]: p["name"] for p in all_platforms}

    # 平台选择器
    selected_key = st.selectbox(
        "选择平台",
        options=list(platform_names.keys()),
        format_func=lambda x: platform_names[x],
        key="platform_selector"
    )

    if selected_key:
        # 获取平台详情
        detail = pf["get_platform_detail"](selected_key)

        if "error" in detail:
            st.error(detail["error"])
        else:
            # 平台名称和类型
            st.markdown(f"""
            <div class="platform-detail-card">
                <h3>{detail['platform']}</h3>
                <p><strong>类型:</strong> {detail.get('type', '未知')} |
                <strong>数据更新:</strong> {detail.get('updated', '未知')} |
                <strong>来源:</strong> {detail.get('source', '未知')}</p>
            </div>
            """, unsafe_allow_html=True)

            # 所有费率详情（表格形式）
            st.markdown("##### 费率详情")
            fee_rows = []
            for fee_key, fee_info in detail.get("fees", {}).items():
                desc = fee_info.get("desc", fee_key)
                rates = fee_info.get("rates", {})
                # 将rates展开为字符串
                rate_strs = []
                for k, v in rates.items():
                    if isinstance(v, dict):
                        sub_strs = [f"{sk}:{sv}" for sk, sv in v.items()]
                        rate_strs.append(f"{k}({', '.join(sub_strs[:3])})")
                    else:
                        rate_strs.append(f"{k}: {v}")
                fee_rows.append({
                    "费率类型": desc,
                    "费率详情": " | ".join(rate_strs[:5]),
                })

            if fee_rows:
                st.dataframe(
                    pd.DataFrame(fee_rows),
                    use_container_width=True,
                    hide_index=True,
                    height=300,
                )

            # 费用计算器
            st.markdown("##### 费用计算器")
            calc_col1, calc_col2 = st.columns(2)
            with calc_col1:
                calc_amount = st.number_input(
                    "输入销售金额",
                    min_value=0.0,
                    value=1000.0,
                    step=100.0,
                    key="platform_calc_amount",
                    format="%.2f"
                )
            with calc_col2:
                calc_category = st.selectbox(
                    "商品类目",
                    options=["默认", "电子产品", "服装", "珠宝", "3C数码", "家居"],
                    key="platform_calc_category"
                )

            if st.button("计算佣金", type="primary", key="calc_commission_btn"):
                result = pf["calculate_platform_commission"](selected_key, calc_amount, calc_category)
                if "error" in result:
                    st.warning(result["error"])
                else:
                    col_r1, col_r2, col_r3 = st.columns(3)
                    with col_r1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">佣金率</div>
                            <div class="metric-value metric-neutral">{result.get('commission_rate_display', 'N/A')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_r2:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">佣金金额</div>
                            <div class="metric-value metric-negative">{format_amount(result.get('commission', 0))}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_r3:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">到手金额</div>
                            <div class="metric-value metric-positive">{format_amount(result.get('net_amount', 0))}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    if result.get("disclaimer"):
                        st.caption(result["disclaimer"])

    st.markdown("<br>", unsafe_allow_html=True)

    # ---- 平台对比功能 ----
    st.markdown("---")
    st.markdown("##### 平台费用对比")
    st.caption("选择多个平台，输入金额，对比各平台佣金和到手金额")

    compare_keys = st.multiselect(
        "选择对比平台（最多5个）",
        options=list(platform_names.keys()),
        format_func=lambda x: platform_names[x],
        default=["amazon", "ebay", "shopee"],
        key="compare_platforms_select",
        max_selections=5,
    )

    compare_amount = st.number_input(
        "对比金额",
        min_value=0.0,
        value=1000.0,
        step=100.0,
        key="compare_amount_input",
        format="%.2f"
    )

    if st.button("开始对比", type="primary", key="compare_btn"):
        if len(compare_keys) < 2:
            st.warning("请至少选择2个平台进行对比")
        else:
            comparison = pf["compare_platforms"](compare_keys, compare_amount)
            comp_rows = []
            for p in comparison.get("platforms", []):
                if "error" in p:
                    comp_rows.append({
                        "平台": p.get("platform", "未知"),
                        "状态": "无法计算",
                        "佣金率": "-",
                        "佣金": "-",
                        "到手金额": "-",
                    })
                else:
                    comp_rows.append({
                        "平台": p.get("platform", "未知"),
                        "状态": "可计算",
                        "佣金率": p.get("commission_rate_display", "-"),
                        "佣金": f"{p.get('commission', 0):.2f}",
                        "到手金额": f"{p.get('net_amount', 0):.2f}",
                    })

            if comp_rows:
                st.dataframe(
                    pd.DataFrame(comp_rows),
                    use_container_width=True,
                    hide_index=True,
                )

                if comparison.get("fee_difference_display"):
                    st.info(f"费用差异: {comparison['fee_difference_display']}")

    st.markdown('</div>', unsafe_allow_html=True)


# ==================== Tab4: 税费计算 ====================
def show_tax_calculator():
    """显示税费计算"""
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # VAT计算器
    st.markdown("#### VAT 增值税计算器")
    st.markdown("输入销售金额和国家，自动计算应缴VAT税额")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("##### 计算器")
        vat_amount = st.number_input("销售金额（不含税）", min_value=0.0, value=10000.0, step=100.0, key="vat_amount_input", format="%.2f")
        vat_currency = st.selectbox("币种", ["EUR", "GBP", "USD", "CNY"], key="vat_currency_input")

        # 从realtime_data获取国家列表
        refresh_realtime_data()
        vat_rates_data = st.session_state.vat_data.get("rates", {}) if st.session_state.vat_data else {}
        vat_countries = list(vat_rates_data.keys())
        if not vat_countries:
            vat_countries = ["德国", "法国", "意大利", "西班牙", "英国", "荷兰", "波兰", "比利时", "瑞典", "日本", "澳大利亚", "加拿大"]

        vat_country = st.selectbox("目的国", vat_countries, key="vat_country_input")

        if st.button("计算VAT", type="primary", use_container_width=True, key="vat_calc_btn"):
            if vat_country in vat_rates_data:
                country_info = vat_rates_data[vat_country]
                tax_rate = country_info.get("standard_rate", 0)
                reduced_rate = country_info.get("reduced_rate", 0)
                tax_amount = vat_amount * tax_rate
                total_with_tax = vat_amount + tax_amount

                st.markdown(f"""
                <div class="metric-card" style="margin-top:16px;">
                    <div class="metric-label">标准VAT税率</div>
                    <div class="metric-value metric-neutral">{tax_rate:.1%}</div>
                </div>
                """, unsafe_allow_html=True)

                if reduced_rate:
                    st.markdown(f"""
                    <div class="metric-card" style="margin-top:8px;">
                        <div class="metric-label">优惠税率</div>
                        <div class="metric-value metric-neutral">{reduced_rate:.1%}</div>
                    </div>
                    """, unsafe_allow_html=True)

                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">应缴税额</div>
                        <div class="metric-value metric-negative">{format_amount(tax_amount, vat_currency)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_r2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">含税总额</div>
                        <div class="metric-value metric-neutral">{format_amount(total_with_tax, vat_currency)}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning(f"未找到 {vat_country} 的税率信息")

    with col_right:
        st.markdown("##### 各国VAT税率表")
        vat_table_data = []
        for country, info in vat_rates_data.items():
            std_rate = info.get("standard_rate", 0)
            reduced_rate = info.get("reduced_rate", 0)
            code = info.get("country_code", "")
            vat_table_data.append({
                "国家": country,
                "代码": code,
                "标准税率": f"{std_rate:.1%}" if std_rate else "N/A",
                "优惠税率": f"{reduced_rate:.1%}" if reduced_rate else "无",
            })

        if vat_table_data:
            st.dataframe(
                pd.DataFrame(vat_table_data),
                use_container_width=True,
                hide_index=True,
                height=400
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # 中国税率查询
    with st.expander("中国税率查询"):
        try:
            rt = _get_realtime_data()
            if rt:
                china_tax = rt["get_china_tax_rates"]()
                china_rates = china_tax.get("rates", {})

                for tax_type, tax_info in china_rates.items():
                    st.markdown(f"**{tax_type}**")
                    if isinstance(tax_info, dict):
                        for sub_key, sub_val in tax_info.items():
                            if isinstance(sub_val, dict):
                                rate_val = sub_val.get("税率", sub_val.get("标准税率", ""))
                                scope = sub_val.get("适用范围", "")
                                note = sub_val.get("note", "")
                                st.markdown(f"  - {sub_key}: **{rate_val}** {scope} {note}")
                            else:
                                st.markdown(f"  - {sub_key}: {sub_val}")
        except Exception:
            st.info("中国税率数据暂不可用")

    # 美国销售税查询
    with st.expander("美国销售税查询"):
        try:
            rt = _get_realtime_data()
            if rt:
                us_tax = rt["get_us_sales_tax"]()
                us_rates = us_tax.get("rates", {})

                us_table = []
                for state, rate in us_rates.items():
                    us_table.append({
                        "州": state,
                        "销售税率": f"{rate:.2%}" if rate > 0 else "免税",
                    })

                if us_table:
                    st.dataframe(
                        pd.DataFrame(us_table),
                        use_container_width=True,
                        hide_index=True,
                        height=400
                    )
        except Exception:
            st.info("美国销售税数据暂不可用")

    st.markdown('</div>', unsafe_allow_html=True)


# ==================== Tab5: 汇率工具 ====================
def show_exchange_tools():
    """显示汇率工具"""
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    st.markdown("#### 汇率工具")
    st.markdown("实时汇率查询与换算计算器")

    # 实时汇率表（20+货币）
    st.markdown("##### 实时汇率表")
    refresh_realtime_data()
    ex_data = st.session_state.exchange_data
    rates = ex_data.get("rates", {}) if ex_data else {}

    currency_names = {
        "USD": "美元", "EUR": "欧元", "GBP": "英镑", "JPY": "日元",
        "SGD": "新加坡元", "AUD": "澳元", "CAD": "加元", "HKD": "港币",
        "KRW": "韩元", "THB": "泰铢", "INR": "印度卢比", "MYR": "马来西亚林吉特",
        "PHP": "菲律宾比索", "IDR": "印尼盾", "VND": "越南盾", "RUB": "俄罗斯卢布",
        "BRL": "巴西雷亚尔", "MXN": "墨西哥比索", "NZD": "新西兰元", "CHF": "瑞士法郎",
    }

    if rates:
        rate_rows = []
        for code, name in currency_names.items():
            if code in rates:
                rate_rows.append({
                    "货币": f"{name} ({code})",
                    "兑美元汇率": round(rates[code], 4),
                })
        if rate_rows:
            st.dataframe(
                pd.DataFrame(rate_rows),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "兑美元汇率": st.column_config.NumberColumn(format="%.4f")
                }
            )

        # 更新时间
        update_time = ""
        if ex_data and ex_data.get("updated_at"):
            try:
                dt = datetime.fromisoformat(ex_data["updated_at"])
                update_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass
        if update_time:
            st.caption(f"数据更新时间: {update_time} | 来源: {ex_data.get('source', '未知')}")
    else:
        st.info("汇率获取失败，请检查网络连接")

    st.markdown("<br>", unsafe_allow_html=True)

    # 汇率换算计算器
    st.markdown("##### 汇率换算计算器")
    calc_col1, calc_col2, calc_col3 = st.columns(3)
    with calc_col1:
        fx_from = st.selectbox("原始币种", ["USD", "CNY", "EUR", "GBP", "JPY", "SGD", "AUD", "CAD", "HKD"], key="fx_from_currency")
    with calc_col2:
        fx_to = st.selectbox("目标币种", ["CNY", "USD", "EUR", "GBP", "JPY", "SGD", "AUD", "CAD", "HKD"], index=0, key="fx_to_currency")
    with calc_col3:
        fx_amount = st.number_input("金额", min_value=0.0, value=10000.0, step=1000.0, key="fx_amount_input", format="%.2f")

    if st.button("换算", type="primary", use_container_width=True, key="fx_convert_btn"):
        try:
            rt = _get_realtime_data()
            if rt:
                result = rt["convert_currency"](fx_amount, fx_from, fx_to)
                if result is not None:
                    st.markdown(f"""
                    <div class="metric-card" style="margin-top:16px;">
                        <div class="metric-label">换算结果</div>
                        <div class="metric-value metric-neutral">{format_amount(fx_amount, fx_from)} = {format_amount(result, fx_to)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("换算失败，汇率数据不可用")
            else:
                st.error("实时数据模块暂不可用")
        except Exception as e:
            st.error(f"换算失败: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)


# ==================== 主应用 ====================
def main():
    """主应用入口"""
    # 检查登录状态
    if st.session_state.user_id is None:
        show_login_page()
        return

    # ---- 顶部标识栏 ----
    show_top_bar()

    # ---- 数据状态栏 ----
    show_data_status_bar()

    # ---- 汇率条 ----
    show_rate_bar()

    # ---- 知识轮播条 ----
    show_knowledge_bar()

    # ---- 退出按钮 ----
    if st.button("退出登录", key="logout_btn"):
        st.session_state.user_id = None
        st.session_state.username = ""
        st.session_state.user_info = None
        st.session_state.parsed_data = None
        st.session_state.normal_data = None
        st.session_state.anomaly_data = None
        st.session_state.anomaly_summary = None
        st.session_state.reports = {}
        st.session_state.chat_messages = []
        st.session_state.ai_engine = None
        st.session_state.file_hash = None
        st.session_state.exchange_data = None
        st.session_state.vat_data = None
        st.session_state.data_status = None
        st.session_state.last_data_refresh = 0
        st.session_state.upload_action = None
        st.session_state.is_processing = False
        st.rerun()

    # ---- 主内容区（5个Tab）----
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "智能工作台",
        "AI财务助手",
        "平台费率",
        "税费计算",
        "汇率工具"
    ])

    with tab1:
        show_workspace()

    with tab2:
        show_ai_assistant()

    with tab3:
        show_platform_fees()

    with tab4:
        show_tax_calculator()

    with tab5:
        show_exchange_tools()


# ==================== 启动 ====================
if __name__ == "__main__":
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "parsed_data" not in st.session_state:
        st.session_state.parsed_data = None
    if "normal_data" not in st.session_state:
        st.session_state.normal_data = None
    if "anomaly_data" not in st.session_state:
        st.session_state.anomaly_data = None
    if "anomaly_summary" not in st.session_state:
        st.session_state.anomaly_summary = None
    if "reports" not in st.session_state:
        st.session_state.reports = {}
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "ai_engine" not in st.session_state:
        st.session_state.ai_engine = None
    if "file_hash" not in st.session_state:
        st.session_state.file_hash = None
    if "exchange_data" not in st.session_state:
        st.session_state.exchange_data = None
    if "vat_data" not in st.session_state:
        st.session_state.vat_data = None
    if "data_status" not in st.session_state:
        st.session_state.data_status = None
    if "last_data_refresh" not in st.session_state:
        st.session_state.last_data_refresh = 0
    if "upload_action" not in st.session_state:
        st.session_state.upload_action = None
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    main(Fix session_state init for Streamlit Cloud)
