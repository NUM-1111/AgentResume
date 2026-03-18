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

        st.caption(
            f"模型状态: {'已启用' if result['meta']['model_enabled'] else '未启用(本地降级)'} | "
            f"模型: {result['meta']['model']}"
        )

