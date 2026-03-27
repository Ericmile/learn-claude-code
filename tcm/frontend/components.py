#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit UI 组件
"""
import streamlit as st
from typing import Dict, Any, List
import re


def parse_diagnosis(content: str) -> List[Dict[str, str]]:
    """
    解析诊断结果格式

    将 ━━━━━ 分隔的内容分段，提取标题和内容

    Args:
        content: 诊断结果文本

    Returns:
        分段后的列表，每项包含 title 和 content
    """
    sections = []
    # 按 ━━━ 分隔（支持不同数量的下划线）
    parts = re.split(r"━{3,}", content)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # 查找所有 【标题】
        matches = list(re.finditer(r"【(.+?)】", part))
        if matches:
            last_end = 0
            for i, match in enumerate(matches):
                title = match.group(1)
                start = match.end()

                # 获取内容（到下一个标题或段落结束）
                if i + 1 < len(matches):
                    end = matches[i + 1].start()
                else:
                    end = len(part)

                content_text = part[start:end].strip()
                if content_text:
                    sections.append({"title": title, "content": content_text})
        elif part:
            # 没有标题的部分，直接添加
            sections.append({"title": "详情", "content": part})

    return sections


def render_message(message: Dict[str, Any]):
    """
    渲染单条聊天消息

    Args:
        message: 消息数据，包含 role, content, tool_calls 等
    """
    role = message.get("role", "assistant")
    content = message.get("content", "")
    is_diagnosis = message.get("is_diagnosis", False)
    tool_calls = message.get("tool_calls", [])

    with st.chat_message(role):
        # 渲染主要内容
        if is_diagnosis:
            render_diagnosis(content)
        elif content:
            st.markdown(content)

        # 渲染工具调用
        if tool_calls:
            st.markdown("---")
            for tool_call in tool_calls:
                render_tool_call(tool_call)


def render_diagnosis(content: str):
    """
    渲染诊断结果（可展开的卡片）

    Args:
        content: 诊断结果文本
    """
    sections = parse_diagnosis(content)

    # 使用容器包裹诊断结果
    st.markdown('<div class="diagnosis-container">', unsafe_allow_html=True)

    for i, section in enumerate(sections):
        title = section["title"]
        content_text = section["content"]

        # 根据标题选择图标
        icons = {
            "辨证分析": "🔍",
            "方药": "💊",
            "调护": "🌿",
            "诊断": "📋",
            "证型": "⚕️",
            "病机": "💭",
            "煎服法": "🍵",
        }
        icon = icons.get(title, "📋")

        # 第一部分默认展开
        with st.expander(f"{icon} **{title}**", expanded=(i == 0)):
            # 按行显示内容，保持格式
            lines = content_text.split('\n')
            for line in lines:
                line = line.strip()
                if line:
                    # 识别键值对（如：八纲：...）
                    if '：' in line or ':' in line:
                        st.markdown(f"**{line}**")
                    else:
                        st.markdown(line)

    st.markdown('</div>', unsafe_allow_html=True)


def render_tool_call(tool_call: Dict[str, Any]):
    """
    渲染工具调用信息

    Args:
        tool_call: 工具调用数据
    """
    name = tool_call.get("name", "未知工具")
    status = tool_call.get("status", "pending")
    result = tool_call.get("result", "")
    error = tool_call.get("error", "")

    # 工具名称映射
    name_map = {
        "search_medical_records": "🔍 查询相似医案",
    }
    display_name = name_map.get(name, name)

    # 根据状态显示不同的样式
    if status == "pending":
        st.info(f"⏳ {display_name} - 查询中...")
    elif status == "completed":
        st.success(f"✅ {display_name}")
        if result:
            # 解析医案结果
            lines = result.split('\n')
            case_list = []
            current_case = None

            for line in lines:
                line = line.strip()
                if line.startswith('【相似医案参考】'):
                    continue
                elif line and line[0].isdigit() and '.' in line:
                    # 新医案开始，如 "1. 医案名称"
                    if current_case:
                        case_list.append(current_case)
                    parts = line.split('.', 1)
                    if len(parts) > 1:
                        current_case = {'name': parts[1].strip(), 'details': []}
                elif current_case and line:
                    current_case['details'].append(line)

            if current_case:
                case_list.append(current_case)

            if case_list:
                st.markdown("#### 📚 检索到的相似医案：")
                for i, case in enumerate(case_list, 1):
                    with st.expander(f"{i}. {case['name']}", expanded=False):
                        for detail in case['details']:
                            st.markdown(f"   {detail}")
            else:
                with st.expander("查看原始结果", expanded=False):
                    st.text(result)
    elif status == "failed":
        st.error(f"❌ {display_name}")
        if error:
            st.text(error)


def render_welcome():
    """渲染欢迎消息"""
    st.markdown("""
    ### 👨‍⚕️ 您好，我是中医辨证论治助手

    请告诉我您哪里不舒服？我会通过**八纲辨证**（阴阳、表里、寒热、虚实）
    为您进行专业的中医辨证分析。

    ---
    **您可以这样描述：**
    - 我头痛
    - 最近总是失眠，多梦
    - 胃口不好，吃不下饭
    - 感觉很疲劳，没有精神

    **我会询问：**
    - 症状持续时间
    - 伴随症状
    - 身体状况细节
    - 舌象脉象（如果方便描述）

    **最终会提供：**
    - 八纲辨证分析
    - 证型判断
    - 方药建议
    - 生活调护指导
    """)


def render_error(message: str):
    """
    渲染错误消息

    Args:
        message: 错误消息
    """
    st.error(f"❌ {message}")


def render_success(message: str):
    """
    渲染成功消息

    Args:
        message: 成功消息
    """
    st.success(f"✅ {message}")


def render_tongue_diagnosis(data: Dict[str, Any]):
    """
    渲染舌诊结果卡片

    Args:
        data: 舌诊数据，包含 tongue_color, coat_color, coat_thickness,
              fat_thin, mark, point, crack, dry_wet, seg_image 等
    """
    st.markdown('<div class="tongue-diagnosis-container">', unsafe_allow_html=True)

    # 舌质
    with st.expander("👅 **舌质**", expanded=True):
        st.markdown(f"**舌色：** {data.get('tongue_color', '未知')}")

    # 舌苔
    with st.expander("🍃 **舌苔**", expanded=True):
        st.markdown(f"**苔色：** {data.get('coat_color', '未知')}")
        st.markdown(f"**苔厚薄：** {data.get('coat_thickness', '未知')}")

    # 舌体
    with st.expander("🎯 **舌体**", expanded=True):
        st.markdown(f"**胖瘦：** {data.get('fat_thin', '未知')}")
        st.markdown(f"**齿痕：** {data.get('mark', '未知')}")
        st.markdown(f"**点刺：** {data.get('point', '未知')}")
        st.markdown(f"**裂痕：** {data.get('crack', '未知')}")
        st.markdown(f"**干润：** {data.get('dry_wet', '未知')}")

    # 分割图片（如果有）
    seg_image = data.get('seg_image', '')
    if seg_image:
        with st.expander("🖼️ **舌象分割图**", expanded=False):
            st.image(f"data:image/jpeg;base64,{seg_image}", caption="舌象分割结果")

    st.markdown('</div>', unsafe_allow_html=True)


def render_tongue_upload_message(message: Dict[str, Any]):
    """
    渲染舌诊上传消息

    Args:
        message: 消息数据，包含 role, content, tongue_data 等
    """
    role = message.get("role", "user")
    tongue_data = message.get("tongue_data", {})

    with st.chat_message(role):
        st.markdown("#### 👅 舌诊分析")
        if tongue_data:
            render_tongue_diagnosis(tongue_data)
        else:
            st.error("舌诊分析失败")
