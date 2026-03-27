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
            - success: 是否成功
            - data: 舌诊数据（成功时）
            - error: 错误信息（失败时）
            - error_type: 错误类型（upload_failed/recognize_failed/invalid_data）
        """
        # 1. 验证图片数据
        if not image_bytes or len(image_bytes) == 0:
            logger.error("上传的图片数据为空")
            return {
                "success": False,
                "error": "上传的图片文件为空，请重新选择",
                "error_type": "upload_failed",
            }

        if len(image_bytes) > 10 * 1024 * 1024:
            logger.error(f"图片文件过大: {len(image_bytes)} bytes")
            return {
                "success": False,
                "error": "图片文件大小不能超过10MB，请压缩后重新上传",
                "error_type": "upload_failed",
            }

        try:
            files = {"file": (filename, image_bytes, "image/jpeg")}

            response = requests.post(
                f"{self.api_url}/upload_image",
                files=files,
                timeout=30,
            )

            # 记录原始响应用于调试
            logger.info(f"舌诊API响应状态: {response.status_code}")

            # 2. 处理上传失败的情况
            if response.status_code != 200:
                logger.warning(f"舌诊API返回非200状态: {response.status_code}, 响应: {response.text[:200]}")
                return {
                    "success": False,
                    "error": "舌象识别服务暂时不可用，请稍后重试",
                    "error_type": "recognize_failed",
                    "allow_manual_input": True,  # 允许手动输入
                }

            # 3. 解析响应数据
            try:
                data = response.json()
            except ValueError as e:
                logger.error(f"解析API响应失败: {str(e)}, 响应内容: {response.text[:200]}")
                return {
                    "success": False,
                    "error": "舌象识别返回数据格式异常，请稍后重试",
                    "error_type": "recognize_failed",
                    "allow_manual_input": True,
                }

            logger.info(f"舌诊API返回数据: {data}")

            # 检查API返回的错误信息
            if data.get("code") == 500:
                error_msg = data.get("msg", "未知错误")
                logger.warning(f"舌诊API返回错误: {error_msg}")
                return {
                    "success": False,
                    "error": f"舌象识别失败：{error_msg}",
                    "error_type": "recognize_failed",
                    "allow_manual_input": True,
                }

            # 提取实际数据（可能在data字段中）
            tongue_data = data.get("data", {})
            if not tongue_data:
                # 如果没有data字段，直接使用根数据
                tongue_data = data

            # 4. 验证识别结果的完整性
            required_fields = ["color", "coat_color", "coat_thickness", "fat_thin",
                             "dry_wet", "mark", "point", "crack"]
            missing_fields = [f for f in required_fields if f not in tongue_data or not tongue_data[f]]

            if missing_fields:
                logger.warning(f"舌诊识别结果不完整，缺少字段: {missing_fields}")
                # 即使不完整也返回已有数据，但标记为部分成功
                pass

            # 5. 检查识别结果是否异常（所有值都是"未知"或空）
            valid_values = [v for v in tongue_data.values() if v and v != "未知"]
            if len(valid_values) == 0:
                logger.error("舌诊识别结果全部为空或未知")
                return {
                    "success": False,
                    "error": "未能从图片中识别出舌象特征，请确保图片清晰后重新上传",
                    "error_type": "invalid_data",
                    "allow_manual_input": True,
                }

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
                "partial": len(missing_fields) > 0,  # 标记是否为部分识别
            }

            if result["partial"]:
                result["warning"] = f"部分特征未能识别（{len(missing_fields)}项），您可以补充描述"

            return result

        except requests.exceptions.Timeout:
            logger.error("舌诊API调用超时")
            return {
                "success": False,
                "error": "舌象识别超时，请稍后重试",
                "error_type": "recognize_failed",
                "allow_manual_input": True,
            }
        except requests.exceptions.ConnectionError:
            logger.error("舌诊API连接失败")
            return {
                "success": False,
                "error": "无法连接到舌象识别服务，请检查网络或稍后重试",
                "error_type": "recognize_failed",
                "allow_manual_input": True,
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"舌诊API请求异常: {str(e)}")
            return {
                "success": False,
                "error": "舌象识别服务异常，请稍后重试",
                "error_type": "recognize_failed",
                "allow_manual_input": True,
            }
        except Exception as e:
            logger.error(f"舌诊分析未知错误: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": "舌象分析过程中发生错误，请稍后重试",
                "error_type": "recognize_failed",
                "allow_manual_input": True,
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
