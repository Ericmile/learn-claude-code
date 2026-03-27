#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TCM API 客户端
与 FastAPI 后端通信
"""
import requests
from typing import Optional, Dict, Any
from datetime import datetime


class TCMClient:
    """中医辨证 API 客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")

    def create_session(self, language: str = "zh") -> Dict[str, Any]:
        """
        创建新的问诊会话

        Args:
            language: 语言代码 (zh, en, ja)

        Returns:
            包含 session_id 的响应
        """
        try:
            resp = requests.post(
                f"{self.base_url}/api/chat/session",
                json={"language": language},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"创建会话失败：{str(e)}"}

    def send_message(
        self, message: str, session_id: Optional[str] = None, language: str = "zh"
    ) -> Dict[str, Any]:
        """
        发送消息并获取助手回复

        Args:
            message: 用户消息
            session_id: 会话 ID（可选，首次自动创建）
            language: 语言代码

        Returns:
            包含助手回复的响应
        """
        try:
            payload = {"message": message, "language": language}
            if session_id:
                payload["session_id"] = session_id

            resp = requests.post(
                f"{self.base_url}/api/chat/message",
                json=payload,
                timeout=60,  # AI 响应可能较慢
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"发送消息失败：{str(e)}"}

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话详情

        Args:
            session_id: 会话 ID

        Returns:
            会话信息
        """
        try:
            resp = requests.get(
                f"{self.base_url}/api/chat/session/{session_id}",
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"获取会话失败：{str(e)}"}

    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """
        删除会话

        Args:
            session_id: 会话 ID

        Returns:
            删除结果
        """
        try:
            resp = requests.delete(
                f"{self.base_url}/api/chat/session/{session_id}",
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"删除会话失败：{str(e)}"}

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            服务状态
        """
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=5)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException:
            return {"status": "error", "message": "后端服务不可用"}

    def upload_tongue_image(self, image_file) -> Dict[str, Any]:
        """
        上传舌象图片进行舌诊分析

        Args:
            image_file: 图片文件对象

        Returns:
            舌诊分析结果，包含舌质、舌苔、舌体等信息
        """
        try:
            files = {"file": (image_file.name, image_file, image_file.type)}
            resp = requests.post(
                f"{self.base_url}/api/tongue/upload",
                files=files,
                timeout=30,
            )
            resp.raise_for_status()
            return {"success": True, "data": resp.json()}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"上传失败：{str(e)}"}
