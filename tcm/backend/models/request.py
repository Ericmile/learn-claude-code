#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
请求模型
"""
from pydantic import BaseModel, Field
from typing import Optional


class SessionCreateRequest(BaseModel):
    """创建会话请求"""
    language: str = Field(default="zh", description="语言代码 (zh, en, ja)")


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息或症状描述", min_length=1)
    session_id: Optional[str] = Field(None, description="会话 ID，用于保持对话连续性")
    language: str = Field(default="zh", description="语言代码")
