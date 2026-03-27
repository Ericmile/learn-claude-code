#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI 应用入口
中医辨证论治 Agent API 服务
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import chat, health, tongue
from .middleware.cors import cors_config

# 创建 FastAPI 应用
app = FastAPI(
    title="TCM Agent API",
    description="中医辨证论治 Agent API 服务",
    version="1.0.0",
)

# 添加 CORS 中间件
app.add_middleware(CORSMiddleware, **cors_config)

# 注册路由
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(tongue.router, prefix="/api/tongue", tags=["tongue"])
app.include_router(health.router, tags=["health"])


@app.on_event("startup")
async def startup_event():
    """应用启动时的处理"""
    print("=" * 50)
    print("    TCM Agent API 启动成功")
    print("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的处理"""
    print("TCM Agent API 正在关闭...")


# 根路径
@app.get("/")
async def root():
    return {
        "message": "TCM Agent API",
        "version": "1.0.0",
        "docs": "/docs",
    }
