#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent 核心服务
从 tcm_agent.py 重构而来，移除命令行交互，改为返回结构化响应
"""
import os
from anthropic import Anthropic
from typing import List, Dict, Any, Optional
from .medical_service import MedicalService


# 老中医的系统提示
SYSTEM = """你是一位经验丰富的老中医，擅长八纲辨证论治（阴阳、表里、寒热、虚实）。

## 问诊对话要求（重要）
问诊过程中保持简洁自然，专注于收集信息：

**提问原则：**
- 一次只问一个问题，不要一次问多个问题
- 用患者能听懂的语言交流，不要抛出专业术语
- 不要中途展示你的辨证分析过程
- 语气亲切温和，像老医生面对面问诊
- 不要自称老中医

**回答检查（必须执行）：**
每次患者回答后，你必须检查：
1. 患者是否回答了你提出的所有问题？
2. 如果患者只回答了部分问题，必须先追问遗漏的问题
3. 只有当所有问题都得到回答后，再继续下一个话题

**举例：**
- 你问："请问您这个拉肚子的情况有多长时间了？一天大概拉几次？"
- 患者答："持续有几年了"
- 你必须追问："那一天大概拉几次呢？"
- 等患者回答完后，再继续问下一个问题（如大便性状等）

需要收集的信息：主诉症状、持续时间、寒热汗出、饮食、大小便、舌象脉象、睡眠等情况。需要询问患者的疾病史、治疗史、过敏史等信息，然后进行综合考量。

## 舌诊要求（重要）
**舌诊是辨证的重要依据，需要收集舌象信息：**
1. 在问诊过程中，适时询问患者舌象情况
2. 如果患者方便，建议患者拍摄舌头照片进行舌诊分析
3. 患者上传舌象图片后，系统会自动分析并返回舌质、舌苔、舌体等信息
4. 在诊断时，结合舌诊结果进行辨证分析

**询问舌象的方式：**
- "请问您的舌头是什么颜色的？舌苔怎么样？"
- "如果方便的话，可以拍一张舌头的照片，我来帮您分析一下舌象"
- 请用温和的语气建议，不要强迫

## 脉诊要求（重要）
**脉诊是辨证的核心依据，必须收集脉象信息：**
1. 收集脉象信息

**询问脉象的方式：**
- "请您把一下脉搏，数一数每分钟跳多少次？"
- "您的脉搏有力吗？节律规整吗？"
- "如果方便把脉的话，请告诉我脉象情况，这对辨证很重要"
- 请强调脉象的重要性，鼓励患者配合

## 相似医案检索要求（重要）
**在给出最终诊断前，必须使用 search_medical_records 工具查询相似医案：**
1. 收集到足够的症状信息后，先调用 search_medical_records 工具
2. 仔细阅读检索到的相似医案，参考其中的诊断、证型和方药
3. 在诊断结果中，应该体现对相似医案的参考和借鉴
4. 如果检索到的医案中有合适的方剂，可以作为参考但不完全照搬
5. 根据患者具体情况，对参考方剂进行辨证加减

**工具使用时机：**
- 当收集到较完整的症状信息（主诉、现病史、舌象脉象等）后
- 在给出最终诊断和方药之前
- 这是诊断流程的必要步骤

## 最终诊断格式（必须严格遵守）
当信息充分可以下诊断时，请严格按照以下格式输出：

━━━━━━━━━━━━━━━━
【辨证分析】
八纲：阴阳/表里/寒热/虚实
证型：具体证型名称
病机：简要病机分析
参考医案：简要说明参考了哪些相似医案的经验

【方药】
方名：方剂名称（可参考经典方或自拟方）
组成：药物及剂量（如：桂枝10g、芍药10g等）
煎服法：煎煮方法和服用方法
方解：简要说明方义，参考了哪些医案的用药经验

【调护】
生活起居建议
饮食禁忌
情志调节
━━━━━━━━━━━━━━━━

**重要提示：**
1. 必须包含【辨证分析】【方药】【调护】三个部分
2. 辨证分析必须包含：八纲、证型、病机、参考医案
3. 方药必须包含：方名、组成（具体剂量）、煎服法、方解
4. 方解中应说明如何参考相似医案的用药经验
5. 必须用 ━━━━━━━━━━━━━━━━ 分隔符包围整个诊断结果
"""

# 工具定义
TOOLS = [{
    "name": "search_medical_records",
    "description": "查询相似医案来辅助诊断。需要主诉和现病史，可选性别、舌象、脉象。",
    "input_schema": {
        "type": "object",
        "properties": {
            "chief_complaint": {
                "type": "string",
                "description": "患者主诉症状"
            },
            "present_illness": {
                "type": "string",
                "description": "现病史，症状的起因、发展和变化"
            },
            "gender": {
                "type": "string",
                "description": "患者性别（男/女）"
            },
            "tongue": {
                "type": "string",
                "description": "舌象观察"
            },
            "pulse": {
                "type": "string",
                "description": "脉象特征"
            }
        },
        "required": ["chief_complaint", "present_illness"]
    }
}]


class AgentService:
    """Agent 核心服务"""

    def __init__(self, api_key: str, base_url: str, model: str, medical_api_url: str):
        self.client = Anthropic(api_key=api_key, base_url=base_url)
        self.model = model
        self.medical_service = MedicalService(medical_api_url)

    async def process_message(
        self, messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        处理消息，通过 Agent 循环获取响应

        Args:
            messages: Anthropic API 格式的消息列表

        Returns:
            {
                "content": str,                    # 助手回复内容
                "tool_calls": List[dict],         # 工具调用列表
                "is_diagnosis": bool,              # 是否是诊断结果
                "requires_follow_up": bool,        # 是否需要继续追问
                "response_blocks": List[dict]      # 原始响应块（用于存储）
            }
        """
        tool_calls = []
        response_blocks = None

        # Agent 循环：处理工具调用
        while True:
            # 调用 Anthropic API
            response = self.client.messages.create(
                model=self.model,
                system=SYSTEM,
                messages=messages,
                tools=TOOLS,
                max_tokens=4000,
            )

            # 保存响应内容
            response_blocks = response.content
            messages.append({"role": "assistant", "content": response.content})

            # 检查是否需要调用工具
            if response.stop_reason != "tool_use":
                # 没有工具调用，退出循环
                break

            # 处理工具调用
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    tool_id = block.id

                    # 记录工具调用
                    tool_calls.append({
                        "id": tool_id,
                        "name": tool_name,
                        "input": tool_input,
                        "status": "pending",
                    })

                    # 执行工具
                    if tool_name == "search_medical_records":
                        result = self.medical_service.search_medical_records(**tool_input)
                        # 更新工具调用结果
                        tool_calls[-1]["result"] = result
                        tool_calls[-1]["status"] = "completed"
                    else:
                        result = f"未知工具：{tool_name}"
                        tool_calls[-1]["error"] = result
                        tool_calls[-1]["status"] = "failed"

                    # 添加到工具结果列表
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": result,
                    })

            # 将工具结果作为用户消息发送
            messages.append({"role": "user", "content": tool_results})

        # 提取最终文本内容
        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

        # 判断是否是诊断结果
        is_diagnosis = self._detect_diagnosis(content)

        # 判断是否需要继续追问
        requires_follow_up = not is_diagnosis

        # 判断是否需要舌诊图片
        requires_tongue_image = self._detect_tongue_request(content)

        # 判断是否需要脉象输入
        requires_pulse_input = self._detect_pulse_request(content)

        return {
            "content": content,
            "tool_calls": tool_calls,
            "is_diagnosis": is_diagnosis,
            "requires_follow_up": requires_follow_up,
            "requires_tongue_image": requires_tongue_image,
            "requires_pulse_input": requires_pulse_input,
            "response_blocks": response_blocks,
        }

    def _detect_diagnosis(self, content: str) -> bool:
        """检测响应是否包含诊断格式"""
        return "━━━━" in content and ("【辨证分析】" in content or "【方药】" in content)

    def _detect_tongue_request(self, content: str) -> bool:
        """检测响应是否包含询问舌象"""
        tongue_keywords = [
            "舌象", "舌头", "舌色", "舌苔", "舌质",
            "拍一张舌头", "舌的照片", "舌诊",
            "看一下您的舌头", "观察舌头",
        ]
        for keyword in tongue_keywords:
            if keyword in content:
                return True
        return False

    def _detect_pulse_request(self, content: str) -> bool:
        """检测响应是否包含询问脉象"""
        pulse_keywords = [
            "脉象", "把脉", "脉", "脉搏", "按脉",
            "数一数脉搏", "测脉搏", "脉搏次数",
            "桡动脉", "手腕脉搏", "脉率",
        ]
        for keyword in pulse_keywords:
            if keyword in content:
                return True
        return False
