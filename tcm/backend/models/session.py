#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话模型
"""
from pydantic import BaseModel
from typing import List, Any, Optional, Literal
from datetime import datetime


class SessionMessage(BaseModel):
    """会话消息"""
    role: Literal["user", "assistant", "tool"]
    content: Any  # 字符串或工具结果列表
    timestamp: datetime
    tool_calls: Optional[List[dict]] = None  # 用于存储 assistant 的工具调用信息


class Session:
    """会话"""
    def __init__(
        self,
        session_id: str,
        language: str = "zh",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.session_id = session_id
        self.messages: List[SessionMessage] = []
        self.language = language
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    def add_message(self, role: str, content: Any, tool_calls: Optional[List[dict]] = None):
        """添加消息"""
        msg = SessionMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            tool_calls=tool_calls,
        )
        self.messages.append(msg)
        self.updated_at = datetime.now()
        return msg
