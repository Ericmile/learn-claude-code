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
    if "show_manual_tongue_input" not in st.session_state:
        st.session_state.show_manual_tongue_input = False


init_session_state()


# ==================== 辅助函数 ====================
def continue_diagnosis(tongue_text: str):
    """
    继续诊断流程

    Args:
        tongue_text: 舌象描述文本
    """
    # 继续调用 API 获取医生回复
    with st.spinner("🤔 正在分析..."):
        response = st.session_state.api_client.send_message(
            message=tongue_text,
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
        "requires_pulse_input": response.get("requires_pulse_input", False),
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
    # 只有当需要舌诊且还未完成诊断时才显示上传区
    if (last_message.get("role") == "assistant" and
        last_message.get("requires_tongue_image") and
        not last_message.get("is_diagnosis")):
        show_tongue_upload = True

# 检查最后一条用户消息是否已经是舌诊结果（防止重复处理）
has_tongue_result = False
if show_tongue_upload:
    for msg in reversed(st.session_state.messages):
        if msg.get("role") == "user":
            has_tongue_result = msg.get("content", "").startswith("舌诊结果：")
            break

if show_tongue_upload and not has_tongue_result:
    st.markdown("---")
    st.markdown("#### 👅 医生建议上传舌象图片")
    st.caption("请拍摄舌头的清晰照片（自然光下，伸舌放松）")

    # 上传舌象图片
    uploaded_tongue_image = st.file_uploader(
        "选择舌象图片",
        type=["jpg", "jpeg", "png"],
        key="tongue_upload",
        label_visibility="visible",
    )

    # 或者手动描述
    st.markdown("---")
    st.markdown("##### 或手动描述舌象")
    if st.button("✏️ 手动输入舌象信息", use_container_width=True, key="btn_manual_input"):
        st.session_state.show_manual_tongue_input = True

    # 处理图片上传
    if uploaded_tongue_image is not None:
        # 显示上传中的状态
        with st.spinner("🔍 正在分析舌象..."):
            result = st.session_state.api_client.upload_tongue_image(uploaded_tongue_image)

        if result.get("success"):
            # 重置手动输入状态
            st.session_state.show_manual_tongue_input = False

            # 显示成功消息（如果有警告）
            if result.get("partial"):
                st.warning(f"⚠️ {result.get('warning', '部分特征未能识别')}")

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
            continue_diagnosis(tongue_text)

        else:
            # 上传或识别失败
            error_msg = result.get("error", "舌诊分析失败")
            error_type = result.get("error_type", "unknown")

            if error_type == "upload_failed":
                st.error(f"❌ 上传失败：{error_msg}")
            elif error_type == "recognize_failed":
                st.error(f"❌ 识别失败：{error_msg}")
            elif error_type == "invalid_data":
                st.error(f"❌ 识别结果异常：{error_msg}")

            # 兜底策略：显示手动输入选项
            st.markdown("---")
            st.info("💡 您可以选择手动描述舌象，继续完成诊断")
            st.session_state.show_manual_tongue_input = True

    # 手动输入舌象信息（兜底策略）
    if st.session_state.show_manual_tongue_input:
        st.markdown("##### ✏️ 手动描述舌象")
        st.caption("请用一句话描述您的舌象情况，例如：舌淡红，苔薄白，有齿痕")

        with st.form("manual_tongue_form"):
            tongue_desc = st.text_area(
                "舌象描述",
                placeholder="例如：舌质淡红，舌苔薄白，舌体胖大有齿痕...",
                height=80,
                label_visibility="visible",
            )

            submitted = st.form_submit_button("提交", use_container_width=True)

            if submitted and tongue_desc.strip():
                # 构建舌象描述文本
                tongue_text = f"舌诊结果：{tongue_desc.strip()}"

                # 添加用户消息
                user_message = {
                    "role": "user",
                    "content": tongue_text,
                    "timestamp": datetime.now().isoformat(),
                }
                st.session_state.messages.append(user_message)

                # 立即显示用户消息
                with st.chat_message("user"):
                    st.markdown(tongue_text)

                # 重置手动输入状态
                st.session_state.show_manual_tongue_input = False

                # 继续诊断
                continue_diagnosis(tongue_text)

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

    # 如果用户回复了舌诊请求，清除之前的标记
    if st.session_state.messages:
        for msg in reversed(st.session_state.messages):
            if msg.get("role") == "assistant" and msg.get("requires_tongue_image"):
                msg["requires_tongue_image"] = False
                break

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
        "requires_pulse_input": response.get("requires_pulse_input", False),
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
