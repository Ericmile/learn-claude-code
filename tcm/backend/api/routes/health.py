#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康检查接口
"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "service": "TCM Agent API",
        "timestamp": datetime.now().isoformat(),
    }
