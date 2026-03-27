#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中医辨证论治助手 - Streamlit 主应用
"""
import streamlit as st
from datetime import datetime
import sys
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from api_client import TCMClient
from components import (
    render_message,
    render_welcome,
    render_error,
    render_success,
)

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="中医辨证论治助手",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ==================== 自定义 CSS ====================
st.markdown("""
<style>
    /* 主容器样式 */
    .main-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid #E5E7EB;
        margin-bottom: 2rem;
    }

    /* 消息容器 */
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }

    /* 诊断结果样式 */
    .diagnosis-container {
        background-color: #F0FDF4;
        border-left: 4px solid #10B981;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }

    /* 舌诊结果样式 */
    .tongue-diagnosis-container {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 初始化会话状态 ====================
def init_session_state():
    """初始化 Streamlit 会话状态"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "api_client" not in st.session_state:
        st.session_state.api_client = TCMClient()


init_session_state()

# ==================== 侧边栏 ====================
with st.sidebar:
    st.title("🌿 中医辨证论治")

    st.markdown("---")

    # 健康检查
    health = st.session_state.api_client.health_check()
    if health.get("status") == "ok":
        st.success("✅ 后端服务正常")
    else:
        st.error("❌ 后端服务不可用")
        st.warning("请先启动后端服务：")
        st.code("cd tcm && python run_server.py")

    st.markdown("---")

    # 会话信息
    if st.session_state.session_id:
        st.info(f"💬 会话已创建")
        st.caption(f"消息数：{len(st.session_state.messages)}")
    else:
        st.caption("💬 暂无会话")

    st.markdown("---")

    # 操作按钮
    if st.button("🔄 开始新会话", use_container_width=True):
        st.session_state.session_id = None
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")

    # 使用说明
    st.markdown("""
    ### 📖 使用说明

    1. 描述您的症状
    2. 回答医生的追问
    3. 获取辨证诊断结果
    4. 查看病证分析和方药建议

    ---
    **八纲辨证**
    - 阴阳
    - 表里
    - 寒热
    - 虚实
    """)

# ==================== 主界面 ====================
st.title("🌿 中医辨证论治助手")
st.markdown("**八纲辨证：阴阳、表里、寒热、虚实**")
st.markdown("---")

# 欢迎消息
if len(st.session_state.messages) == 0:
    render_welcome()

# 渲染历史消息
for message in st.session_state.messages:
    render_message(message)

# ==================== 舌诊上传区（当医生询问时显示） ====================
# 检查最后一条助手消息是否需要舌诊
show_tongue_upload = False
if st.session_state.messages:
    last_message = st.session_state.messages[-1]
    if last_message.get("role") == "assistant" and last_message.get("requires_tongue_image"):
        show_tongue_upload = True

if show_tongue_upload:
    st.markdown("---")
    st.markdown("#### 👅 医生建议上传舌象图片")
    st.caption("请拍摄舌头的清晰照片（自然光下，伸舌放松）")

    uploaded_tongue_image = st.file_uploader(
        "选择舌象图片",
        type=["jpg", "jpeg", "png"],
        key="tongue_upload",
        label_visibility="visible",
    )

    if uploaded_tongue_image is not None:
        # 显示上传中的状态
        with st.spinner("🔍 正在分析舌象..."):
            # 调用舌诊 API
            result = st.session_state.api_client.upload_tongue_image(uploaded_tongue_image)

        if result.get("success"):
            # 格式化舌诊结果为文本
            tongue_data = result.get("data", {})
            tongue_text = f"""舌诊结果：
舌质：{tongue_data.get('tongue_color', '未知')}
舌苔：{tongue_data.get('coat_color', '未知')}、{tongue_data.get('coat_thickness', '未知')}
舌体：{tongue_data.get('fat_thin', '未知')}、{tongue_data.get('mark', '未知')}、{tongue_data.get('point', '未知')}、{tongue_data.get('crack', '未知')}、{tongue_data.get('dry_wet', '未知')}"""

            # 添加用户消息（舌诊结果）
            user_message = {
                "role": "user",
                "content": tongue_text,
                "timestamp": datetime.now().isoformat(),
            }
            st.session_state.messages.append(user_message)

            # 立即显示用户消息
            with st.chat_message("user"):
                st.markdown(tongue_text)

            # 继续调用 API 获取医生回复
            with st.spinner("🤔 正在分析..."):
                response = st.session_state.api_client.send_message(
                    message=tongue_text,
                    session_id=st.session_state.session_id,
                    language="zh",
                )

            # 检查错误
            if "error" not in response:
                # 更新会话 ID
                if "session_id" in response:
                    st.session_state.session_id = response["session_id"]

                # 提取助手消息
                assistant_data = response.get("assistant_message", {})
                assistant_message = {
                    "role": "assistant",
                    "content": assistant_data.get("content", ""),
                    "timestamp": assistant_data.get("timestamp", datetime.now().isoformat()),
                    "is_diagnosis": assistant_data.get("is_diagnosis", False),
                    "tool_calls": assistant_data.get("tool_calls", []),
                    "requires_tongue_image": response.get("requires_tongue_image", False),
                }
                st.session_state.messages.append(assistant_message)

                # 显示助手回复
                render_message(assistant_message)

                # 如果是诊断结果，显示完成提示
                if assistant_message["is_diagnosis"]:
                    st.markdown("---")
                    render_success("辨证诊断完成！如果您还有其他问题，请继续描述。")

            # 重新运行以更新界面
            st.rerun()
        else:
            render_error(result.get("error", "舌诊分析失败"))
    st.markdown("---")

# ==================== 输入区 ====================
user_input = st.chat_input("💬 请描述您的症状...")

if user_input:
    # 添加用户消息
    user_message = {
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().isoformat(),
    }
    st.session_state.messages.append(user_message)

    # 立即显示用户消息
    with st.chat_message("user"):
        st.markdown(user_input)

    # 调用 API
    with st.spinner("🤔 正在分析..."):
        response = st.session_state.api_client.send_message(
            message=user_input,
            session_id=st.session_state.session_id,
            language="zh",
        )

    # 检查错误
    if "error" in response:
        render_error(response["error"])
        st.stop()

    # 更新会话 ID
    if "session_id" in response:
        st.session_state.session_id = response["session_id"]

    # 提取助手消息
    assistant_data = response.get("assistant_message", {})
    assistant_message = {
        "role": "assistant",
        "content": assistant_data.get("content", ""),
        "timestamp": assistant_data.get("timestamp", datetime.now().isoformat()),
        "is_diagnosis": assistant_data.get("is_diagnosis", False),
        "tool_calls": assistant_data.get("tool_calls", []),
        "requires_tongue_image": response.get("requires_tongue_image", False),
    }
    st.session_state.messages.append(assistant_message)

    # 显示助手回复
    render_message(assistant_message)

    # 如果是诊断结果，显示完成提示
    if assistant_message["is_diagnosis"]:
        st.markdown("---")
        render_success("辨证诊断完成！如果您还有其他问题，请继续描述。")

    # 重新运行以更新界面
    st.rerun()

# ==================== 底部信息 ====================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #9CA3AF; font-size: 0.875rem;'>
        💡 本助手仅供学习参考，不能替代专业医疗诊断
    </div>
    """,
    unsafe_allow_html=True,
)
