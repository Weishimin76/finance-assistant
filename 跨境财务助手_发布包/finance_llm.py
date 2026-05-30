# -*- coding: utf-8 -*-
"""
跨境电商财务智能体 - LLM 财务问答模块
使用 Ollama 本地大模型进行自然语言问答和分析
"""
import json
import pandas as pd
from typing import Optional
from config import config


# 系统提示词 - 严格限制只回答跨境电商财务问题
SYSTEM_PROMPT = """你是一个专业的跨境电商财务助手。你的职责是帮助财务人员处理跨境电商相关的财务问题。

## 严格规则：
1. 只回答跨境电商财务相关问题，其他问题一律拒绝回答
2. 输出尽量用表格，简洁明了，不要写废话
3. 不确定的数据必须标注"待确认"，绝对不能编造数据
4. 涉及金额时，必须标明币种
5. 涉及税务问题时，必须声明"请以税代最终确认为准"
6. 所有财务数据严格保密

## 你擅长的领域：
- 多平台订单对账和异常检测
- 跨境电商收入/支出分析
- VAT 税务计算和申报
- 汇率波动分析
- 利润计算（扣除平台佣金、运费、税费等）
- 财务报表解读
- 退款和售后财务处理
- 跨境支付和结算

## 回答格式要求：
- 优先使用表格
- 关键数据加粗
- 结论先行，细节在后
- 如需计算，展示计算过程
"""


class FinanceLLM:
    """财务 LLM 问答引擎"""

    def __init__(self, model: str = None):
        self.model = model or config.ollama_model
        self.base_url = config.ollama_base_url
        self._client = None

    def _get_client(self):
        """懒加载 Ollama 客户端"""
        if self._client is None:
            try:
                import ollama
                self._client = ollama.Client(host=self.base_url)
            except ImportError:
                raise ImportError("请安装 ollama: pip install ollama")
            except Exception as e:
                raise ConnectionError(f"无法连接 Ollama 服务 ({self.base_url}): {e}\n请确保 Ollama 已启动")
        return self._client

    def check_connection(self) -> bool:
        """检查 Ollama 连接状态"""
        try:
            import ollama
            client = ollama.Client(host=self.base_url)
            models = client.list()
            return True
        except Exception:
            return False

    def list_models(self) -> list:
        """列出可用模型"""
        try:
            import ollama
            client = ollama.Client(host=self.base_url)
            models = client.list()
            return [m["name"] for m in models.get("models", [])]
        except Exception:
            return []

    def chat(self, question: str, data_context: str = "") -> str:
        """
        发送问题给 LLM

        Args:
            question: 用户问题
            data_context: 附带的数据上下文（如当前报表摘要）

        Returns:
            LLM 回答
        """
        client = self._get_client()

        # 构建消息
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if data_context:
            messages.append({
                "role": "system",
                "content": f"以下是当前的财务数据上下文，请基于这些数据回答问题：\n\n{data_context}"
            })

        messages.append({"role": "user", "content": question})

        try:
            response = client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": 0.3,  # 低温度，更精确
                    "num_predict": 2048,
                }
            )
            return response["message"]["content"]
        except Exception as e:
            return f"⚠️ LLM 回复失败: {str(e)}\n\n请检查 Ollama 是否正常运行，模型 '{self.model}' 是否已下载。"

    def analyze_data(self, df: pd.DataFrame, question: str) -> str:
        """
        基于数据进行分析

        Args:
            df: 要分析的数据
            question: 分析问题

        Returns:
            分析结果
        """
        # 将 DataFrame 转换为文本摘要
        data_summary = self._df_to_summary(df)
        return self.chat(question, data_context=data_summary)

    def generate_summary(self, df: pd.DataFrame) -> str:
        """
        自动生成财务数据总结（给老板看的版本）

        Args:
            df: 标准化订单数据

        Returns:
            人话总结
        """
        question = (
            "请基于以下财务数据，生成一份简洁的财务总结。要求：\n"
            "1. 用老板能看懂的语言\n"
            "2. 突出关键数据（总收入、净利润、退款率等）\n"
            "3. 如有异常情况，重点说明\n"
            "4. 用表格展示核心指标\n"
            "5. 控制在200字以内"
        )
        return self.analyze_data(df, question)

    def compare_periods(self, df_current: pd.DataFrame, df_previous: pd.DataFrame) -> str:
        """
        对比两个时期的数据

        Args:
            df_current: 当前期数据
            df_previous: 对比期数据

        Returns:
            对比分析结果
        """
        current_summary = self._df_to_summary(df_current)
        previous_summary = self._df_to_summary(df_previous)

        question = (
            "请对比以下两个时期的财务数据，生成对比分析报告：\n"
            "1. 用表格展示关键指标对比\n"
            "2. 标注同比/环比变化\n"
            "3. 突出显著变化项\n"
            "4. 给出简要结论"
        )

        context = f"【当前期数据】\n{current_summary}\n\n【对比期数据】\n{previous_summary}"
        return self.chat(question, data_context=context)

    def _df_to_summary(self, df: pd.DataFrame) -> str:
        """将 DataFrame 转换为文本摘要"""
        if df.empty:
            return "暂无数据"

        lines = []
        lines.append(f"数据概览: {len(df)} 条记录")

        # 基本信息
        if "平台" in df.columns:
            platforms = df["平台"].unique()
            lines.append(f"涉及平台: {', '.join(platforms)}")

        if "交易日期" in df.columns:
            dates = pd.to_datetime(df["交易日期"], errors="coerce").dropna()
            if not dates.empty:
                lines.append(f"时间范围: {dates.min().strftime('%Y-%m-%d')} 至 {dates.max().strftime('%Y-%m-%d')}")

        # 金额汇总
        numeric_cols = ["订单金额", "佣金", "手续费", "运费", "退款金额", "实际到账"]
        for col in numeric_cols:
            if col in df.columns:
                total = df[col].sum()
                lines.append(f"{col}合计: {total:,.2f}")

        # 按平台汇总
        if "平台" in df.columns and "订单金额" in df.columns:
            lines.append("\n各平台销售额:")
            platform_sales = df.groupby("平台")["订单金额"].sum().sort_values(ascending=False)
            for platform, amount in platform_sales.items():
                lines.append(f"  {platform}: {amount:,.2f}")

        # 币种分布
        if "币种" in df.columns:
            currencies = df["币种"].value_counts()
            lines.append(f"\n币种分布: {dict(currencies)}")

        # 交易状态
        if "交易状态" in df.columns:
            statuses = df["交易状态"].value_counts()
            lines.append(f"交易状态: {dict(statuses)}")

        return "\n".join(lines)


# 全局实例
finance_llm = FinanceLLM()
