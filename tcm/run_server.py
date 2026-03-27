#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TCM Agent API 启动入口
使用此脚本启动可以避免相对导入问题
"""
import sys
from pathlib import Path

# 添加 tcm 目录到 Python 路径
tcm_dir = Path(__file__).parent
sys.path.insert(0, str(tcm_dir))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
