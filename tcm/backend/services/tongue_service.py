#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
舌诊服务
调用外部舌诊 API 进行舌象分析
"""
import requests
import base64
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class TongueService:
    """舌诊诊断服务"""

    def __init__(self, api_url: str = "http://192.168.13.12:8001"):
        self.api_url = api_url

    def upload_image(self, image_bytes: bytes, filename: str = "tongue.jpg") -> Dict[str, Any]:
        """
        上传舌象图片进行分析

        Args:
            image_bytes: 图片字节数据
            filename: 文件名

        Returns:
            舌诊分析结果，包含：
            - color: 舌色（淡白舌、淡红舌、红舌等）
            - crack: 裂痕情况
            - coat_color: 苔色
            - coat_thickness: 苔厚薄
            - fat_thin: 胖瘦
            - dry_wet: 干润
            - mark: 齿痕
            - point: 点刺
            - seg_image: 分割图片的 base64
        """
        try:
            files = {"file": (filename, image_bytes, "image/jpeg")}

            response = requests.post(
                f"{self.api_url}/upload_image",
                files=files,
                timeout=30,
            )

            # 记录原始响应用于调试
            logger.info(f"舌诊API响应状态: {response.status_code}")

            # 检查是否成功
            if response.status_code != 200:
                logger.warning(f"舌诊API返回非200状态: {response.status_code}, 响应: {response.text[:200]}")
                return {
                    "success": False,
                    "error": f"舌诊分析失败（状态码: {response.status_code}）",
                }

            data = response.json()
            logger.info(f"舌诊API返回数据: {data}")

            # 检查API返回的错误信息
            if data.get("code") == 500:
                error_msg = data.get("msg", "未知错误")
                logger.warning(f"舌诊API返回错误: {error_msg}")
                return {
                    "success": False,
                    "error": f"舌诊分析失败：{error_msg}",
                }

            # 提取实际数据（可能在data字段中）
            tongue_data = data.get("data", {})
            if not tongue_data:
                # 如果没有data字段，直接使用根数据
                tongue_data = data

            # 格式化舌诊结果
            result = {
                "success": True,
                "data": {
                    "tongue_color": tongue_data.get("color", "未知"),
                    "crack": tongue_data.get("crack", "未知"),
                    "coat_color": tongue_data.get("coat_color", "未知"),
                    "coat_thickness": tongue_data.get("coat_thickness", "未知"),
                    "fat_thin": tongue_data.get("fat_thin", "未知"),
                    "dry_wet": tongue_data.get("dry_wet", "未知"),
                    "mark": tongue_data.get("mark", "未知"),
                    "point": tongue_data.get("point", "未知"),
                    "seg_image": tongue_data.get("seg_image", ""),
                },
            }

            return result

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"舌诊API调用失败：{str(e)}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"舌诊分析出错：{str(e)}",
            }

    def format_diagnosis_text(self, data: Dict[str, Any]) -> str:
        """
        将舌诊结果格式化为可读文本

        Args:
            data: 舌诊数据

        Returns:
            格式化的诊断文本
        """
        lines = [
            "【舌诊结果】",
            "",
            "**舌质**",
            f"- 舌色：{data.get('tongue_color', '未知')}",
            "",
            "**舌苔**",
            f"- 苔色：{data.get('coat_color', '未知')}",
            f"- 苔厚薄：{data.get('coat_thickness', '未知')}",
            "",
            "**舌体**",
            f"- 胖瘦：{data.get('fat_thin', '未知')}",
            f"- 齿痕：{data.get('mark', '未知')}",
            f"- 点刺：{data.get('point', '未知')}",
            f"- 裂痕：{data.get('crack', '未知')}",
            f"- 干润：{data.get('dry_wet', '未知')}",
        ]

        return "\n".join(lines)
