#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理
"""
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv(override=True)


class Settings(BaseSettings):
    """应用配置"""

    # Anthropic API 配置
    anthropic_api_key: str
    anthropic_base_url: str
    model_id: str

    # 医案检索 API
    medical_record_api: str = "http://192.168.13.12:9528/rag/doctor-record/search"

    # API 配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False


# 从环境变量读取配置
settings = Settings(
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
    anthropic_base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
    model_id=os.getenv("MODEL_ID", "claude-sonnet-4-6"),
)
