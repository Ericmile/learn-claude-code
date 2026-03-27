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
    """
    # 验证文件类型
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")

    try:
        # 读取文件内容
        image_bytes = await file.read()

        # 检查文件大小（限制为10MB）
        if len(image_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="图片文件大小不能超过10MB")

        # 调用舌诊服务
        result = tongue_service.upload_image(image_bytes, file.filename)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "舌诊分析失败"))

        return result["data"]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"舌诊上传处理错误：{str(e)}")
        raise HTTPException(status_code=500, detail=f"舌诊分析失败：{str(e)}")
