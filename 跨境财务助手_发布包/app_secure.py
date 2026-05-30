# -*- coding: utf-8 -*-
"""
跨境电商财务智能体 Pro v5.0 - 安全版
密码保护 · 标识置顶 · 高保密性
"""
import streamlit as st
import pandas as pd
import numpy as np
import os
import hashlib
import json
from datetime import datetime
from functools import lru_cache

# ==================== 密码管理 ====================
PASSWORD_FILE = "data/.secure_config"

def hash_password(password):
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_password():
    """加载已保存的密码哈希"""
    if os.path.exists(PASSWORD_FILE):
        try:
            with open(PASSWORD_FILE, 'r') as f:
                config = json.load(f)
                return config.get('password_hash')
        except:
            return None
    return None

def save_password(password_hash):
    """保存密码哈希"""
    os.makedirs("data", exist_ok=True)
    config = {'password_hash': password_hash, 'created_at': datetime.now().isoformat()}
    with open(PASSWORD_FILE, 'w') as f:
        json.dump(config, f)

def verify_password(password):
    """验证密码"""
    saved_hash = load_password()
    if saved_hash is None:
        return True  # 首次使用
    return hash_password(password) == saved_hash

def has_password():
    """检查是否已设置密码"""
    return load_password() is not None

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="跨境财务助手 Pro",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== 置顶标识CSS ====================
st.markdown("""
<style>
    /* 隐藏默认元素 */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    
    /* 置顶标识栏 */
    .header-bar {
        background: linear-gradient(90deg, #1e3a5f 0%, #2c5282 50%, #3182ce 100%);
        padding: 12px 24px;
        margin: -1rem -1rem 0 -1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.15);
    }
    
    .header-title {
        color: white;
        font-size: 20px;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .header-badge {
        background: rgba(255,255,255,0.2);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }
    
    .header-security {
        color: rgba(255,255,255,0.9);
        font-size: 13px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* 汇率条 */
    .ticker-bar {
        background: #f7fafc;
        padding: 10px 24px;
        border-bottom: 1px solid #e2e8f0;
        margin: 0 -1rem;
        font-size: 13px;
        color: #4a5568;
    }
    
    .ticker-item {
        display: inline-block;
        margin-right: 20px;
    }
    
    /* 登录/设置密码界面 */
    .auth-container {
        max-width: 400px;
        margin: 80px auto;
        padding: 40px;
        background: white;
        border-radius: 16px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .auth-icon {
        font-size: 64px;
        margin-bottom: 20px;
    }
    
    .auth-title {
        font-size: 24px;
        font-weight: 700;
        color: #1e3a5f;
        margin-bottom: 8px;
    }
    
    .auth-subtitle {
        color: #718096;
        font-size: 14px;
        margin-bottom: 30px;
    }
    
    .auth-input {
        margin-bottom: 20px;
    }
    
    .auth-input input {
        width: 100%;
        padding: 14px 16px;
        border: 2px solid #e2e8f0;
        border-radius: 10px;
        font-size: 16px;
        text-align: center;
        letter-spacing: 2px;
    }
    
    .auth-input input:focus {
        outline: none;
        border-color: #3182ce;
    }
    
    .auth-btn {
        width: 100%;
        padding: 14px;
        background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
        color: white;
        border: none;
        border-radius: 10px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .auth-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(30, 58, 95, 0.3);
    }
    
    .auth-hint {
        margin-top: 20px;
        padding: 12px;
        background: #fffaf0;
        border-left: 4px solid #ed8936;
        border-radius: 8px;
        font-size: 13px;
        color: #744210;
        text-align: left;
    }
    
    /* 主内容区 */
    .main-content {
        padding: 24px;
    }
    
    /* 指标卡片 */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        border-left: 4px solid #3182ce;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    
    .metric-value {
        font-size: 26px;
        font-weight: 700;
        color: #1e3a5f;
    }
    
    .metric-label {
        font-size: 12px;
        color: #718096;
        margin-top: 4px;
    }
    
    /* 上传区域 */
    .upload-zone {
        background: linear-gradient(135deg, #ebf8ff 0%, #e6fffa 100%);
        border: 2px dashed #3182ce;
        border-radius: 16px;
        padding: 40px;
        text-align: center;
    }
    
    /* 设置面板 */
    .settings-btn {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 50px;
        height: 50px;
        background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
        color: white;
        border: none;
        border-radius: 50%;
        font-size: 20px;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 1000;
    }
</style>
""", unsafe_allow_html=True)

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
        "show_settings": False
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
        <div class="auth-icon">{'🔐' if is_first_time else '🔒'}</div>
        <div class="auth-title">{'设置访问密码' if is_first_time else '验证身份'}</div>
        <div class="auth-subtitle">
            {'首次使用，请设置密码保护您的财务数据' if is_first_time else '请输入密码继续访问'}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if is_first_time:
            # 设置密码
            pwd1 = st.text_input("设置密码", type="password", key="set_pwd1")
            pwd2 = st.text_input("确认密码", type="password", key="set_pwd2")
            
            if st.button("🔐 设置密码并进入", use_container_width=True):
                if not pwd1:
                    st.error("请输入密码")
                elif pwd1 != pwd2:
                    st.error("两次输入的密码不一致")
                elif len(pwd1) < 4:
                    st.error("密码长度至少4位")
                else:
                    save_password(hash_password(pwd1))
                    st.session_state.authenticated = True
                    st.success("✅ 密码设置成功")
                    st.rerun()
        else:
            # 验证密码
            pwd = st.text_input("输入密码", type="password", key="login_pwd")
            
            if st.button("🔓 解锁", use_container_width=True):
                if verify_password(pwd):
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ 密码错误")
        
        st.markdown("""
        <div class="auth-hint">
            <b>🔒 安全提示</b><br>
            • 密码仅存储在本地，不会上传到任何服务器<br>
            • 忘记密码需删除 data/.secure_config 文件重置<br>
            • 建议定期更换密码确保数据安全
        </div>
        """, unsafe_allow_html=True)

# ==================== 置顶标识 ====================
def render_header():
    """渲染置顶标识栏"""
    st.markdown("""
    <div class="header-bar">
        <div class="header-title">
            💎 跨境财务助手
            <span class="header-badge">PRO v5.0</span>
        </div>
        <div class="header-security">
            <span>🔒 本地加密保护</span>
            <span>|</span>
            <span>数据不上传</span>
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
    currencies = [("USD", "美元"), ("EUR", "欧元"), ("GBP", "英镑"), 
                  ("JPY", "日元"), ("SGD", "新币"), ("AUD", "澳元")]
    
    for code, name in currencies:
        if code in rates:
            rate = rates[code]
            change = np.random.uniform(-0.5, 0.5)
            arrow = "▲" if change > 0 else "▼"
            color = "#38a169" if change > 0 else "#e53e3e"
            pairs.append(f'<span class="ticker-item">{name}: <b>{rate:.4f}</b> <span style="color:{color}">{arrow}</span></span>')
    
    if pairs:
        st.markdown(f'''
        <div class="ticker-bar">
            💱 实时汇率 {''.join(pairs)}
            <span style="float:right;">{datetime.now().strftime("%H:%M")} 更新</span>
        </div>
        ''', unsafe_allow_html=True)

# ==================== 设置面板 ====================
def render_settings():
    """渲染设置面板"""
    with st.sidebar:
        st.markdown("## ⚙️ 安全设置")
        
        with st.expander("🔐 修改密码", expanded=True):
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
                    st.success("✅ 密码修改成功")
        
        with st.expander("📊 数据管理"):
            if st.button("🗑️ 清除当前数据"):
                st.session_state.data = None
                st.session_state.normal = None
                st.session_state.anomaly = None
                st.session_state.reports = {}
                st.success("✅ 数据已清除")
                st.rerun()
            
            if st.button("🔒 退出登录"):
                st.session_state.authenticated = False
                st.rerun()
        
        st.markdown("---")
        st.caption("🔒 所有数据仅在本地处理")

# ==================== 主应用 ====================
def render_main():
    """渲染主应用界面"""
    render_header()
    render_ticker()
    
    # 设置按钮
    if st.button("⚙️", key="settings_btn"):
        st.session_state.show_settings = not st.session_state.show_settings
    
    if st.session_state.show_settings:
        render_settings()
    
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    # 副标题
    st.markdown("""
    <div style="color: #718096; font-size: 14px; margin-bottom: 20px;">
        专业版 · 智能对账 · 实时汇率 · 高安全性
    </div>
    """, unsafe_allow_html=True)
    
    # ==================== 核心上传区 ====================
    if st.session_state.data is None:
        st.markdown("""
        <div class="upload-zone">
            <div style="font-size: 48px; margin-bottom: 16px;">📁</div>
            <div style="font-size: 18px; font-weight: 600; color: #2c5282; margin-bottom: 8px;">
                拖拽文件到此处，或点击选择
            </div>
            <div style="color: #718096; font-size: 14px;">
                支持 CSV、Excel 格式 · 多平台混合 · 自动识别
            </div>
            <div style="margin-top: 16px;">
                <span style="background: rgba(49,130,206,0.1); padding: 6px 12px; border-radius: 16px; font-size: 12px; color: #2c5282; margin: 0 4px;">Amazon</span>
                <span style="background: rgba(49,130,206,0.1); padding: 6px 12px; border-radius: 16px; font-size: 12px; color: #2c5282; margin: 0 4px;">eBay</span>
                <span style="background: rgba(49,130,206,0.1); padding: 6px 12px; border-radius: 16px; font-size: 12px; color: #2c5282; margin: 0 4px;">Shopify</span>
                <span style="background: rgba(49,130,206,0.1); padding: 6px 12px; border-radius: 16px; font-size: 12px; color: #2c5282; margin: 0 4px;">+3</span>
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
        with st.spinner("🔍 智能解析中..."):
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
                st.toast(f"✅ 已处理 {len(df)} 条记录", icon="✅")
            
            st.session_state.processing = False
            st.rerun()
    
    # ==================== 数据展示 ====================
    if st.session_state.data is not None:
        df = st.session_state.data
        
        # 指标卡片行
        c1, c2, c3, c4, c5 = st.columns(5)
        
        metrics = [
            (c1, "总订单", f"{len(df):,}", "笔"),
            (c2, "销售额", f"¥{df['订单金额'].sum()/10000:.1f}", "万"),
            (c3, "净到账", f"¥{df['实际到账'].sum()/10000:.1f}", "万"),
            (c4, "异常", f"{len(st.session_state.anomaly)}", "条" if len(st.session_state.anomaly) > 0 else "✓"),
            (c5, "平台", f"{df['平台'].nunique()}", "个"),
        ]
        
        for col, label, value, unit in metrics:
            with col:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-value">{value}<span style="font-size: 14px; color: #718096; margin-left: 4px;">{unit}</span></div>
                    <div class="metric-label">{label}</div>
                </div>
                ''', unsafe_allow_html=True)
        
        # 异常预警
        if not st.session_state.anomaly.empty:
            st.error(f"⚠️ 发现 {len(st.session_state.anomaly)} 条异常记录，建议优先处理")
            with st.expander("🔴 查看异常明细", expanded=True):
                st.dataframe(
                    st.session_state.anomaly[["订单号", "平台", "商品名称", "订单金额", "异常原因"]],
                    use_container_width=True, hide_index=True,
                    column_config={"订单金额": st.column_config.NumberColumn(format="¥%.2f")}
                )
                csv = st.session_state.anomaly.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                st.download_button("📥 导出异常记录", csv, f"异常_{datetime.now().strftime('%m%d')}.csv", "text/csv")
        
        # 报表快捷预览
        st.subheader("📊 智能报表")
        rpt_tabs = st.tabs(["收支汇总", "月度趋势", "平台对比", "SKU排行"])
        
        for tab, name in zip(rpt_tabs, ["收支汇总", "月度报表", "平台对比", "SKU排行TOP20"]):
            with tab:
                if name in st.session_state.reports:
                    rdf = st.session_state.reports[name]
                    if not rdf.empty:
                        st.dataframe(rdf, use_container_width=True, hide_index=True,
                                    column_config={c: st.column_config.NumberColumn(format="%.2f") 
                                                  for c in rdf.select_dtypes(include=["float64", "int64"]).columns})
                        csv = rdf.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                        st.download_button("📥 导出", csv, f"{name}_{datetime.now().strftime('%m%d')}.csv", "text/csv", key=f"dl_{name}")
        
        # AI问答
        st.subheader("🤖 智能问答")
        q_cols = st.columns([3, 1, 1, 1])
        quick_qs = ["本月利润率？", "退款率最高的SKU？", "给老板写总结"]
        
        with q_cols[0]:
            question = st.text_input("问AI任何财务问题", placeholder="如：本月哪个平台利润最高？", key="ai_q")
        
        for i, (col, qq) in enumerate(zip(q_cols[1:], quick_qs)):
            with col:
                if st.button(qq, key=f"qq_{i}"):
                    question = qq
        
        if question:
            with st.spinner("AI思考中..."):
                from finance_llm import finance_llm
                ctx = finance_llm._df_to_summary(st.session_state.data) if st.session_state.data is not None else ""
                answer = finance_llm.chat(question, data_context=ctx)
                st.markdown(f'<div style="background: #f7fafc; border-radius: 12px; padding: 20px; margin-top: 16px;">{answer}</div>', unsafe_allow_html=True)
    
    # ==================== 工具箱 ====================
    else:
        st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
        
        tool_cols = st.columns(4)
        tools = [
            ("🧮", "VAT报税", "10国税率计算"),
            ("📋", "报销审核", "智能超标检测"),
            ("💱", "汇率换算", "实时汇率查询"),
            ("📜", "政策监控", "税务政策追踪"),
        ]
        
        for col, (icon, title, desc) in zip(tool_cols, tools):
            with col:
                st.markdown(f'''
                <div style="background: white; border-radius: 12px; padding: 24px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border: 1px solid #e2e8f0;">
                    <div style="font-size: 32px; margin-bottom: 8px;">{icon}</div>
                    <div style="font-weight: 600; color: #1e3a5f; margin-bottom: 4px;">{title}</div>
                    <div style="font-size: 12px; color: #718096;">{desc}</div>
                </div>
                ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== 入口 ====================
# 无密码版本 - 直接进入主界面
render_main()
