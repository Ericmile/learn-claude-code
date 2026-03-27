#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
舌诊 API 接口
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Dict, Any
import logging

from ...services.tongue_service import TongueService
from ..dependencies import get_tongue_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload")
async def upload_tongue_image(
    file: UploadFile = File(..., description="舌象图片文件"),
    tongue_service: TongueService = Depends(get_tongue_service),
) -> Dict[str, Any]:
    """
    上传舌象图片进行舌诊分析

    Args:
        file: 上传的图片文件

    Returns:
        舌诊分析结果，包含舌质、舌苔、舌体等信息
        或者错误信息，包含 error_type 和 allow_manual_input
    """
    # 验证文件类型
    if not file.content_type or not file.content_type.startswith("image/"):
        return {
            "success": False,
            "error": "请上传图片文件（支持 JPG、PNG 格式）",
            "error_type": "upload_failed",
            "allow_manual_input": True,
        }

    try:
        # 读取文件内容
        image_bytes = await file.read()

        # 调用舌诊服务
        result = tongue_service.upload_image(image_bytes, file.filename or "tongue.jpg")

        # 返回完整结果（包含成功和失败的所有情况）
        return result

    except Exception as e:
        logger.error(f"舌诊上传处理错误：{str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "舌诊分析过程中发生错误，请稍后重试",
            "error_type": "recognize_failed",
            "allow_manual_input": True,
        }
