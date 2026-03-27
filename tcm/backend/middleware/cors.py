#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORS 配置
"""

# Vue 开发服务器默认端口
FRONTEND_URLS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]

# CORS 中间件配置
cors_config = {
    "allow_origins": FRONTEND_URLS,
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
