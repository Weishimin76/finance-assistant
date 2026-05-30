# -*- coding: utf-8 -*-
"""
跨境电商财务智能体 v3.0 - 简洁高效版
设计理念：打开即用，上传即处理，一屏搞定
"""
import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="跨境财务助手", page_icon="💰", layout="wide", initial_sidebar_state="expanded")

# ==================== 样式 ====================
st.markdown("""<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] { background-color: #f0f2f5; }
    .block-container { padding-top: 1rem; }
    div[data-testid="stMetric"] { background: #f8f9fa; border-radius: 8px; padding: 12px; }
</style>""", unsafe_allow_html=True)

# ==================== Session State ====================
_defaults = {
    "parsed_data": None, "normal_data": None, "anomaly_data": None,
    "anomaly_summary": None, "reports": {}, "chat_history": [],
    "llm_connected": False, "llm_model": "", "vat_reports": {},
    "exchange_rates": None, "exchange_alerts": [],
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ==================== 侧边栏（极简） ====================
with st.sidebar:
    st.markdown("# 💰 跨境财务助手")
    st.caption("v3.0 · 一切从简")

    # LLM 状态（可折叠）
    with st.expander("🤖 AI模型", expanded=False):
        try:
            from finance_llm import finance_llm
            models = finance_llm.list_models()
            if models:
                st.session_state.llm_connected = True
                sel = st.selectbox("模型", models)
                if sel:
                    finance_llm.model = sel
                    st.session_state.llm_model = sel
                st.success("✅ 已连接")
            else:
                st.warning("无可用模型\nollama pull qwen2.5:14b")
        except Exception:
            st.info("Ollama 未启动\n不影响核心功能")

    st.divider()

    # 核心上传区（永远可见）
    st.subheader("📤 扔文件进来")
    uploaded_files = st.file_uploader(
        "拖拽或选择文件（支持多平台混合）",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        key="main_upload"
    )
    if uploaded_files:
        st.caption(f"✅ 已选 {len(uploaded_files)} 个文件，自动检测平台")

    st.divider()
    st.caption("🔒 数据仅本地处理")


# ==================== 工具函数 ====================
def _process(files):
    """上传即处理：自动解析+对账+生成报表，一步到位"""
    from parsers import parse_file, merge_multi_platform
    from reconciliation import reconcile_data
    from reports import generate_all_reports

    all_dfs = []
    for f in files:
        p = os.path.join("data", "uploads", f.name)
        os.makedirs("data/uploads", exist_ok=True)
        with open(p, "wb") as tmp:
            tmp.write(f.read())
        try:
            parsed = parse_file(p, platform="auto")
            all_dfs.append(parsed)
        except Exception as e:
            st.warning(f"{f.name}: {str(e)[:50]}")

    if not all_dfs:
        return False

    df = merge_multi_platform(all_dfs)
    st.session_state.parsed_data = df
    st.session_state.normal_data, st.session_state.anomaly_data, st.session_state.anomaly_summary = reconcile_data(df)
    st.session_state.reports = generate_all_reports(df)
    return True


def _export(df, name):
    csv = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button("📥 导出", data=csv, file_name=f"{name}_{datetime.now().strftime('%m%d')}.csv", mime="text/csv")


def _fmt(df):
    """通用表格格式配置"""
    return {
        c: st.column_config.NumberColumn(format="%.2f")
        for c in df.select_dtypes(include=["float64", "int64"]).columns
    }


# ==================== 自动处理 ====================
if uploaded_files and st.session_state.parsed_data is None:
    with st.spinner("正在自动解析+对账..."):
        ok = _process(uploaded_files)
    if ok:
        st.toast(f"✅ 已处理 {len(st.session_state.parsed_data)} 条记录", icon="✅")
elif uploaded_files and st.button("🔄 重新处理上传的文件"):
    with st.spinner("重新处理中..."):
        _process(uploaded_files)


# ==================== 三个标签页 ====================
tab1, tab2, tab3 = st.tabs(["🏠 工作台", "📊 数据详情", "🛠️ 工具箱"])


# ==================== TAB1: 工作台 ====================
with tab1:
    # ---- 顶部：核心指标 ----
    if st.session_state.parsed_data is not None:
        df = st.session_state.parsed_data
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("总订单", len(df))
        c2.metric("总销售额", f"¥{df['订单金额'].sum():,.0f}")
        c3.metric("净到账", f"¥{df['实际到账'].sum():,.0f}")
        anomaly_n = len(st.session_state.anomaly_data)
        c4.metric("异常", anomaly_n, delta_color="off" if anomaly_n == 0 else "inverse")
        c5.metric("平台", df["平台"].nunique())
    else:
        st.info("📤 **把订单文件拖到左侧上传区**，自动解析对账，无需其他操作")
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("### 📋 支持的平台")
            for p in ["Amazon", "eBay", "Walmart", "Shopify", "Shopee", "速卖通"]:
                st.write(f"• {p}")
        with c2:
            st.markdown("### 🔍 自动检测")
            for d in ["重复订单", "多扣佣金", "价格异常", "负数异常", "数据缺失", "日期异常"]:
                st.write(f"• {d}")
        with c3:
            st.markdown("### 📊 自动生成")
            for r in ["收支汇总", "月度报表", "平台对比", "币种分布", "SKU排行"]:
                st.write(f"• {r}")

    # ---- 中间：异常（只看红的） ----
    if st.session_state.anomaly_data is not None and not st.session_state.anomaly_data.empty:
        st.markdown("---")
        st.subheader(f"🔴 异常记录 ({len(st.session_state.anomaly_data)} 条)")
        st.dataframe(
            st.session_state.anomaly_data[["订单号", "平台", "商品名称", "订单金额", "佣金", "实际到账", "异常原因"]],
            use_container_width=True, hide_index=True,
            column_config={"订单金额": st.column_config.NumberColumn(format="%.2f"),
                            "佣金": st.column_config.NumberColumn(format="%.2f"),
                            "实际到账": st.column_config.NumberColumn(format="%.2f")}
        )
        _export(st.session_state.anomaly_data, "异常记录")

    # ---- 下方左：汇率快览 ----
    st.markdown("---")
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("💱 今日汇率")
        try:
            from exchange_rate import exchange_monitor
            rates = exchange_monitor.fetch_current_rates()
            if rates:
                rows = []
                for c in ["USD", "EUR", "GBP", "JPY", "SGD", "AUD"]:
                    if c in rates:
                        rows.append({"币种": c, "CNY汇率": round(rates[c], 4)})
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                exchange_monitor.record_rates(rates)
            else:
                st.caption("汇率获取失败")
        except Exception:
            st.caption("汇率服务不可用")

    # ---- 下方右：AI问答（内嵌） ----
    with col_right:
        st.subheader("🤖 问AI")
        if st.session_state.llm_connected:
            q = st.text_input("问任何财务问题", placeholder="如：本月利润率多少？哪些SKU退款最高？", key="quick_q")
            if q:
                with st.spinner(""):
                    from finance_llm import finance_llm
                    ctx = ""
                    if st.session_state.parsed_data is not None:
                        ctx = finance_llm._df_to_summary(st.session_state.parsed_data)
                    ans = finance_llm.chat(q, data_context=ctx)
                    st.markdown(ans)
        else:
            st.caption("安装 Ollama 后可用\nollama pull qwen2.5:14b")


# ==================== TAB2: 数据详情 ====================
with tab2:
    if st.session_state.parsed_data is None:
        st.info("👆 先在工作台上传数据")
    else:
        # 报表
        sub1, sub2 = st.tabs(["📈 报表", "📋 原始数据"])

        with sub1:
            if st.session_state.reports:
                for name, rdf in st.session_state.reports.items():
                    with st.expander(name, expanded=(name == "收支汇总")):
                        if rdf.empty:
                            st.caption("无数据")
                        else:
                            st.dataframe(rdf, use_container_width=True, hide_index=True, column_config=_fmt(rdf))
                            _export(rdf, name)

                # AI总结
                if st.session_state.llm_connected:
                    if st.button("📝 AI生成财务总结（给老板）"):
                        with st.spinner("AI分析中..."):
                            from finance_llm import finance_llm
                            st.markdown(finance_llm.generate_summary(st.session_state.parsed_data))

        with sub2:
            st.dataframe(
                st.session_state.parsed_data,
                use_container_width=True, hide_index=True, height=600,
                column_config=_fmt(st.session_state.parsed_data)
            )
            _export(st.session_state.parsed_data, "全部数据")


# ==================== TAB3: 工具箱 ====================
with tab3:
    tools = st.columns(4)
    tool_names = ["🧾 VAT报税", "🧾 报销审核", "💱 汇率换算", "📜 政策监控"]
    tool_keys = ["vat", "expense", "fx", "policy"]

    for i, (col, name, key) in enumerate(zip(tools, tool_names, tool_keys)):
        with col:
            if st.button(name, use_container_width=True, key=f"tool_{key}"):
                st.session_state.active_tool = key

    active = st.session_state.get("active_tool", "")

    st.markdown("---")

    # ---- VAT ----
    if active == "vat":
        st.subheader("🧾 VAT 算税报税")
        from config import config as cfg
        vc1, vc2 = st.columns([1, 2])
        with vc1:
            v_country = st.selectbox("国家", list(cfg.vat_rates.keys()), key="vat_country")
            v_period = st.text_input("期间（留空=本季度）", key="vat_period")
        with vc2:
            st.info(f"税率: **{cfg.vat_rates[v_country]:.0%}**")

        if st.session_state.parsed_data is not None:
            if st.button("🧮 计算", key="vat_calc"):
                from vat import VATCalculator
                calc = VATCalculator()
                rpt = calc.generate_vat_report(st.session_state.parsed_data, v_country, v_period)
                st.session_state.vat_reports[v_country] = rpt
                st.success("✅ 计算完成")

        if v_country in st.session_state.vat_reports:
            rdf = st.session_state.vat_reports[v_country]
            st.dataframe(rdf, use_container_width=True, hide_index=True)
            _export(rdf, f"VAT_{v_country}")
            from vat import VATCalculator
            txt = VATCalculator().export_tax_agent_format(rdf, v_country)
            st.download_button("📥 税代格式", data=txt.encode("utf-8"), file_name=f"VAT税代_{v_country}.csv", mime="text/csv")

        # 截止日
        with st.expander("⏰ 申报截止日"):
            from vat import VATCalculator
            dl = VATCalculator().get_upcoming_deadlines(60)
            if dl.empty:
                st.success("60天内无截止日")
            else:
                st.dataframe(dl, use_container_width=True, hide_index=True)

    # ---- 报销 ----
    elif active == "expense":
        st.subheader("🧾 报销审核")
        with st.form("exp_form"):
            ec1, ec2, ec3 = st.columns(3)
            with ec1:
                e_desc = st.text_input("描述", key="exp_desc")
                e_cat = st.selectbox("分类", ["餐饮", "交通", "住宿", "办公用品", "物流运费", "广告推广", "样品费", "平台费用", "包装材料", "其他"], key="exp_cat")
            with ec2:
                e_amt = st.number_input("金额", min_value=0.0, step=1.0, key="exp_amt")
                e_cur = st.selectbox("币种", ["CNY", "USD", "EUR"], key="exp_cur")
            with ec3:
                e_date = st.text_input("日期", value=datetime.now().strftime("%Y-%m-%d"), key="exp_date")
                e_rcpt = st.selectbox("票据", ["发票", "收据", "无"], key="exp_rcpt")
            if st.form_submit_button("➕ 添加", type="primary"):
                from expense_audit import ExpenseAuditor, ExpenseItem
                if "auditor" not in st.session_state:
                    st.session_state.auditor = ExpenseAuditor()
                st.session_state.auditor.add_expense(ExpenseItem(
                    description=e_desc, amount=e_amt, currency=e_cur,
                    category=e_cat, date=e_date, receipt_type=e_rcpt))
                st.toast(f"✅ +{e_desc} ¥{e_amt}")

        # 批量录入
        st.caption("或批量粘贴（每行一条）：")
        e_batch = st.text_area("描述 金额 票据类型", height=80, placeholder="客户午餐 358元 发票\n快递费 120元 发票", key="exp_batch")
        if st.button("📋 批量添加", key="exp_batch_btn"):
            from expense_audit import ExpenseAuditor
            if "auditor" not in st.session_state:
                st.session_state.auditor = ExpenseAuditor()
            items = st.session_state.auditor.parse_text_expense(e_batch)
            for it in items:
                st.session_state.auditor.add_expense(it)
            st.toast(f"✅ +{len(items)} 条")

        # 结果
        if "auditor" in st.session_state:
            normal, anomaly = st.session_state.auditor.audit()
            summary = st.session_state.auditor.get_summary()
            if not summary.empty:
                st.dataframe(summary, use_container_width=True, hide_index=True)
            if not anomaly.empty:
                st.error(f"🔴 {len(anomaly)} 条超标")
                st.dataframe(anomaly, use_container_width=True, hide_index=True)
            if not normal.empty:
                with st.expander(f"✅ 正常 ({len(normal)}条)"):
                    st.dataframe(normal, use_container_width=True, hide_index=True)
            if st.button("🗑️ 清空"):
                st.session_state.auditor.reset()
                st.rerun()

    # ---- 汇率换算 ----
    elif active == "fx":
        st.subheader("💱 汇率换算")
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            f_from = st.selectbox("从", ["CNY", "USD", "EUR", "GBP", "JPY", "SGD"], key="fx_from")
        with fc2:
            f_to = st.selectbox("到", ["USD", "EUR", "GBP", "JPY", "CNY", "SGD"], index=0, key="fx_to")
        with fc3:
            f_amt = st.number_input("金额", value=10000.0, step=1000.0, key="fx_amt")

        if st.button("💱 换算"):
            from exchange_rate import exchange_monitor
            result = exchange_monitor.get_exchange_suggestion(f_from, f_to, f_amt)
            st.markdown(result)

        # 波动分析
        with st.expander("📊 近7天波动"):
            from exchange_rate import exchange_monitor
            vol = exchange_monitor.analyze_volatility()
            if not vol.empty:
                st.dataframe(vol, use_container_width=True, hide_index=True)
            else:
                st.info("需要多次刷新才能积累历史数据")

    # ---- 政策 ----
    elif active == "policy":
        st.subheader("📜 税务政策监控")
        from tax_policy import tax_policy_monitor
        all_p = tax_policy_monitor.get_policy_changes()
        if all_p.empty:
            st.info("暂无政策信息")
        else:
            for _, row in all_p.iterrows():
                ds = row["日期"].strftime("%Y-%m-%d") if hasattr(row["日期"], "strftime") else str(row["日期"])
                with st.expander(f"{row['严重程度']} {row['政策标题']} ({ds})"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**变了什么**\n" + row["变化内容"])
                    with c2:
                        st.markdown("**影响**\n" + row["影响分析"])
                    st.markdown(f"**你要做**: {row['建议操作']}")

        upcoming = tax_policy_monitor.get_upcoming_policies(90)
        if not upcoming.empty:
            st.warning(f"⚠️ {len(upcoming)} 项政策即将生效")

    # 默认：工具选择提示
    if not active:
        st.info("👆 点击上方按钮选择工具")
