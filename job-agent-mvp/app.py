import streamlit as st

from services.orchestrator import JobAgentOrchestrator


st.set_page_config(page_title="求职智能助手 Agent MVP", layout="wide")
st.title("求职场景智能助手 Agent MVP")
st.caption("聚焦：JD 解析 / 匹配分析 / 项目改写（不编造事实）")

orchestrator = JobAgentOrchestrator()

with st.sidebar:
    st.subheader("目标岗位方向")
    target_role = st.selectbox(
        "请选择目标岗位方向",
        options=[
            "AI算法工程师",
            "LLM应用工程师",
            "数据分析师",
            "后端工程师（AI方向）",
            "产品经理（AI方向）",
        ],
        index=0,
    )

jd_text = st.text_area(
    "JD 输入",
    height=220,
    placeholder="粘贴岗位 JD ...",
)

candidate_text = st.text_area(
    "候选人信息输入",
    height=260,
    placeholder="粘贴候选人背景、经历、项目描述 ...",
)

if st.button("开始分析", type="primary"):
    if not jd_text.strip() or not candidate_text.strip():
        st.warning("请先填写 JD 和候选人信息。")
    else:
        with st.spinner("分析中，请稍候..."):
            result = orchestrator.run(
                jd_text=jd_text,
                candidate_text=candidate_text,
                target_role=target_role,
            )

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("JD 分析结果")
            st.json(result["jd_analysis"], expanded=False)
        with col2:
            st.subheader("匹配分析结果")
            st.json(result["match_analysis"], expanded=False)

        st.subheader("项目改写结果")
        st.json(result["project_rewrite"], expanded=False)

        with st.expander("候选人结构化信息（调试视图）", expanded=False):
            st.json(result["candidate_profile"], expanded=False)

        # ── 模型 / Fallback 状态面板 ──────────────────────────────────
        meta = result["meta"]
        sources = meta.get("sources", {})

        def _source_badge(src: str) -> str:
            if src == "llm":
                return "✅ 模型分析"
            if src == "fallback:no_api_key":
                return "⚠️ Fallback（无 API Key）"
            if src.startswith("fallback:"):
                return f"❌ Fallback（调用失败）"
            return src

        with st.expander("📊 分析来源 & 模型状态", expanded=True):
            if meta["model_enabled"]:
                st.success(f"模型已启用：`{meta['model']}`  |  接口：`{meta['base_url']}`")
            else:
                st.error("模型未启用 — OPENAI_API_KEY 为空，所有结果均来自本地规则 fallback")
                st.info("请在 `job-agent-mvp/.env` 中填写 `OPENAI_API_KEY` 后重启服务")

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("JD 分析", _source_badge(sources.get("jd_analysis", "?")))
            col_b.metric("匹配分析", _source_badge(sources.get("match_analysis", "?")))
            col_c.metric("项目改写", _source_badge(sources.get("project_rewrite", "?")))

            # 若有调用失败，展示具体原因
            failed = {k: v for k, v in sources.items() if v.startswith("fallback:") and v != "fallback:no_api_key"}
            if failed:
                st.warning("以下模块调用 LLM 失败，已降级到本地规则：")
                for module, reason in failed.items():
                    st.code(f"{module}: {reason}", language="text")

        st.caption(f"生成时间: {meta['generated_at']}")

