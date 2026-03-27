#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
响应模型
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime


class ToolCall(BaseModel):
    """工具调用信息"""
    id: str
    name: str
    input: Dict[str, Any]
    status: Literal["pending", "completed", "failed"] = "pending"
    result: Optional[str] = None
    error: Optional[str] = None


class AssistantMessage(BaseModel):
    """助手消息"""
    content: str
    tool_calls: List[ToolCall] = []
    is_diagnosis: bool = False
    timestamp: datetime


class ChatResponse(BaseModel):
    """聊天响应"""
    session_id: str
    assistant_message: AssistantMessage
    requires_follow_up: bool = True
    requires_tongue_image: bool = False  # 是否需要舌诊图片


class SessionResponse(BaseModel):
    """会话响应"""
    session_id: str
    created_at: datetime
    message_count: int
    language: str
