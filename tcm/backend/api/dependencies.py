#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖注入
"""
from ..services.session_service import SessionService
from ..services.agent_service import AgentService
from ..services.medical_service import MedicalService
from ..services.tongue_service import TongueService
from ..config import settings


# 单例实例
_session_service: SessionService = None
_agent_service: AgentService = None
_tongue_service: TongueService = None


def get_session_service() -> SessionService:
    """获取会话服务单例"""
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service


def get_agent_service() -> AgentService:
    """获取 Agent 服务单例"""
    global _agent_service
    if _agent_service is None:
        # 创建医案服务
        medical_service = MedicalService(settings.medical_record_api)
        # 创建 Agent 服务
        _agent_service = AgentService(
            api_key=settings.anthropic_api_key,
            base_url=settings.anthropic_base_url,
            model=settings.model_id,
            medical_api_url=settings.medical_record_api,
        )
    return _agent_service


def get_tongue_service() -> TongueService:
    """获取舌诊服务单例"""
    global _tongue_service
    if _tongue_service is None:
        _tongue_service = TongueService()
    return _tongue_service
