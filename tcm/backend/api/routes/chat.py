#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天 API 接口
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import List

from ...models.request import ChatRequest, SessionCreateRequest
from ...models.response import ChatResponse, SessionResponse, AssistantMessage, ToolCall
from ...services.session_service import SessionService
from ...services.agent_service import AgentService
from ..dependencies import get_session_service, get_agent_service


router = APIRouter()


@router.post("/session", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,
    session_service: SessionService = Depends(get_session_service),
):
    """创建新的问诊会话"""
    session = session_service.create_session(language=request.language)
    return SessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        message_count=0,
        language=session.language,
    )


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    agent_service: AgentService = Depends(get_agent_service),
    session_service: SessionService = Depends(get_session_service),
):
    """
    发送消息并获取助手回复

    如果没有提供 session_id，会自动创建新会话
    """
    # 获取或创建会话
    if request.session_id:
        session = session_service.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        session = session_service.create_session(language=request.language)

    # 添加用户消息
    session_service.add_message(session.session_id, "user", request.message)

    # 格式化消息供 API 使用
    messages = session_service.format_messages_for_api(session.session_id)

    # 通过 Agent 处理消息
    try:
        result = await agent_service.process_message(messages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理消息时出错：{str(e)}")

    # 构建工具调用响应
    tool_calls = []
    for tc in result.get("tool_calls", []):
        tool_calls.append(ToolCall(
            id=tc["id"],
            name=tc["name"],
            input=tc["input"],
            status=tc["status"],
            result=tc.get("result"),
            error=tc.get("error"),
        ))

    # 添加助手回复到会话
    session_service.add_message(
        session.session_id,
        "assistant",
        {"blocks": result["response_blocks"]},
        tool_calls=result.get("tool_calls"),
    )

    # 返回响应
    return ChatResponse(
        session_id=session.session_id,
        assistant_message=AssistantMessage(
            content=result["content"],
            tool_calls=tool_calls,
            is_diagnosis=result["is_diagnosis"],
            timestamp=datetime.now(),
        ),
        requires_follow_up=result["requires_follow_up"],
        requires_tongue_image=result.get("requires_tongue_image", False),
    )


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
):
    """获取会话详情"""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    return SessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        message_count=len(session.messages),
        language=session.language,
    )


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
):
    """删除会话"""
    success = session_service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"message": "会话已删除"}
