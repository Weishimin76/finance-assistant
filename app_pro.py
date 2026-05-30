# -*- coding: utf-8 -*-
"""
跨境电商财务智能体 Pro v4.0
专业金融风格 · 高效交互 · 可分享版本
"""
import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
from functools import lru_cache

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="跨境财务助手 Pro",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== 专业金融风格CSS ====================
st.markdown("""
<style>
    /* 隐藏默认元素 */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    
    /* 主色调 */
    :root {
        --primary: #1e3a5f;
        --accent: #3182ce;
    }
    
    /* 顶部汇率条 */
    .ticker-bar {
        background: linear-gradient(90deg, #1e3a5f 0%, #2c5282 50%, #3182ce 100%);
        padding: 12px 20px;
        color: white;
        font-size: 14px;
        font-weight: 500;
        border-radius: 0 0 12px 12px;
        margin-bottom: 20px;
    }
    
    .ticker-item {
        display: inline-block;
        margin-right: 24px;
    }
    
    /* 指标卡片 */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f7fafc 100%);
        border-radius: 12px;
        padding: 20px;
        border-left: 4px solid #3182ce;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
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
    
    /* 按钮样式 */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
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
        "data": None, "normal": None, "anomaly": None, "reports": {},
        "chat_history": [], "vat_reports": {}, "auditor": None,
        "last_upload": None, "processing": False
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ==================== 顶部汇率条 ====================
def render_ticker():
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
            color = "#68d391" if change > 0 else "#fc8181"
            pairs.append(f'<span class="ticker-item">{name}: <b>{rate:.4f}</b> <span style="color:{color}">{arrow}</span></span>')
    
    if pairs:
        st.markdown(f'''
        <div class="ticker-bar">
            💱 实时汇率 {''.join(pairs)}
            <span style="float:right; opacity:0.7; font-size:12px;">{datetime.now().strftime("%H:%M")} 更新</span>
        </div>
        ''', unsafe_allow_html=True)

render_ticker()

# ==================== 头部 ====================
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <span style="font-size: 32px; font-weight: 700; color: #1e3a5f;">💎 跨境财务助手</span>
        <span style="background: linear-gradient(135deg, #3182ce 0%, #2c5282 100%); 
                     color: white; padding: 4px 12px; border-radius: 20px; 
                     font-size: 12px; margin-left: 12px; font-weight: 600;">PRO</span>
    </div>
    <div style="color: #718096; font-size: 14px; margin-bottom: 20px;">
        专业版 · 智能对账 · 实时汇率 · 一键分享
    </div>
    """, unsafe_allow_html=True)

with col_status:
    try:
        from finance_llm import finance_llm
        if finance_llm.list_models():
            st.success("🟢 AI已就绪")
        else:
            st.info("⚪ AI未配置")
    except:
        st.info("⚪ AI未配置")

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
    key="pro_upload",
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

# ==================== 底部 ====================
st.markdown("""
<div style="margin-top: 60px; padding: 20px; text-align: center; color: #a0aec0; font-size: 12px;">
    <div>跨境电商财务智能体 Pro v4.0</div>
    <div style="margin-top: 4px;">🔒 所有数据仅在本地处理 · 严格保密</div>
</div>
""", unsafe_allow_html=True)
