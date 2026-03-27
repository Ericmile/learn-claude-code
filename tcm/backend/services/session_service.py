#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话管理服务
"""
from typing import Dict, Optional, List, Any
import uuid
from datetime import datetime
from ..models.session import Session


class SessionService:
    """会话管理服务（内存存储）"""

    def __init__(self):
        self.sessions: Dict[str, Session] = {}

    def create_session(self, language: str = "zh") -> Session:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        session = Session(session_id=session_id, language=language)
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def add_message(
        self,
        session_id: str,
        role: str,
        content: Any,
        tool_calls: Optional[List[dict]] = None,
    ):
        """添加消息到会话"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        return session.add_message(role, content, tool_calls)

    def format_messages_for_api(self, session_id: str) -> List[Dict[str, Any]]:
        """
        将会话消息格式化为 Anthropic API 需要的格式

        Returns:
            Anthropic API 消息列表
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        formatted = []
        for msg in session.messages:
            if msg.role == "user":
                formatted.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant":
                # 处理复杂的 content（包含工具调用）
                if isinstance(msg.content, dict) and "blocks" in msg.content:
                    formatted.append({
                        "role": "assistant",
                        "content": msg.content["blocks"],
                    })
                else:
                    formatted.append({"role": "assistant", "content": msg.content})
            elif msg.role == "tool":
                # 工具结果
                formatted.append({"role": "user", "content": msg.content})

        return formatted
