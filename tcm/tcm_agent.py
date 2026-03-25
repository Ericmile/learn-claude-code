#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tcm_agent.py - 中医辨证论治 Agent

一位经验丰富的老中医，擅长八纲辨证思维：
    - 阴阳：总纲，判断疾病的性质和方向
    - 表里：判断病变部位的深浅
    - 寒热：判断疾病的性质
    - 虚实：判断邪正盛衰

通过问诊收集患者信息，综合分析后给出诊断和方剂建议。

    +----------+      +-------+      +----------+
    |  患者   | ---> | 中医  | ---> | 辨证分析 |
    |  症状   |      |  Agent |      |  论治   |
    +----------+      +-------+      +----------+
                          ^               |
                          |   继续问诊    |
                          +---------------+
"""

import os
import requests
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(override=True)

if os.getenv("ANTHROPIC_BASE_URL"):
    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)

client = Anthropic(base_url=os.getenv("ANTHROPIC_BASE_URL"))
MODEL = os.environ["MODEL_ID"]

# 医案检索 API 配置
MEDICAL_RECORD_API = "http://192.168.13.12:9528/rag/doctor-record/search"

# 老中医的系统提示
SYSTEM = """你是一位经验丰富的老中医，擅长八纲辨证论治（阴阳、表里、寒热、虚实）。

## 问诊对话要求
问诊过程中保持简洁自然，专注于收集信息：
- 一次只问1-2个相关问题
- 用患者能听懂的语言交流，不要抛出专业术语
- 不要中途展示你的辨证分析过程
- 语气亲切温和，像老医生面对面问诊
- 不要自称老中医

需要收集的信息：主诉症状、持续时间、寒热汗出、二便饮食、舌象脉象等。

## 最终诊断格式
当信息充分可以下诊断时，请输出：

━━━━━━━━━━━━━━━━
【辨证分析】
八纲：[阴阳/表里/寒热/虚实]
证型：[证型名称]

【方药】
方名：XXX
组成：药物及剂量

【调护】
生活建议
━━━━━━━━━━━━━━━━

## 工具使用
在给出最终诊断前，可以使用 search_medical_records 工具查询相似医案作为参考。
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


def search_medical_records(chief_complaint: str, present_illness: str,
                           gender: str = None, tongue: str = None, pulse: str = None) -> str:
    """调用医案检索 API"""
    payload = {
        "chief_complaint": chief_complaint,
        "present_illness": present_illness,
        "top_k": 3
    }
    if gender:
        payload["gender"] = gender
    if tongue:
        payload["tongue"] = tongue
    if pulse:
        payload["pulse"] = pulse

    try:
        resp = requests.post(MEDICAL_RECORD_API, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("success"):
            return f"查询失败：{data.get('message')}"

        results = data.get("data", {}).get("results", [])
        if not results:
            return "未找到相似医案"

        # 格式化返回结果
        output = ["\n【相似医案参考】"]
        for i, r in enumerate(results, 1):
            output.append(f"\n{i}. {r.get('name', '未知')}")
            output.append(f"   医生：{r.get('doctor', '未知')}")
            output.append(f"   诊断：{r.get('cm_diagram', '未记载')}")
            if r.get('syndrome'):
                output.append(f"   证型：{r['syndrome']}")
            if r.get('prescription_form'):
                output.append(f"   方药：{r['prescription_form']}")
            output.append(f"   相似度：{r.get('score', 0):.2%}")

        return "\n".join(output)

    except Exception as e:
        return f"查询出错：{str(e)}"


def agent_loop(messages: list):
    """核心循环：与患者对话，收集信息，进行辨证论治"""
    while True:
        response = client.messages.create(
            model=MODEL,
            system=SYSTEM,
            messages=messages,
            tools=TOOLS,
            extra_body={"enable_thinking": False},
            max_tokens=4000,
        )
        # 记录 assistant 的回复
        messages.append({"role": "assistant", "content": response.content})

        # 处理工具调用
        if response.stop_reason == "tool_use":
            results = []
            output = None
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

                    if tool_name == "search_medical_records":
                        print(f"\033[33m[查询相似医案...]\033[0m")
                        output = search_medical_records(**tool_input)
                        print(output[:500])

                    results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": output if output is not None else ""
                    })
            messages.append({"role": "user", "content": results})
            continue  # 继续循环，让模型基于工具结果生成最终回复

        # 显示回复内容
        for block in response.content:
            if hasattr(block, "text"):
                print(f"\n{block.text}")

        return


if __name__ == "__main__":
    print("=" * 50)
    print("    中医辨证论治 Agent - 八纲辨证")
    print("=" * 50)
    print("您好，请告诉我您哪里不舒服？\n")

    history = []
    while True:
        try:
            query = input("\033[36m患者 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            print("\n\n祝您早日康复！")
            break
        if query.strip().lower() in ("q", "exit", ""):
            print("\n祝您早日康复！")
            break
        history.append({"role": "user", "content": query})
        agent_loop(history)
