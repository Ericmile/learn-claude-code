#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医案检索服务
"""
import requests
from typing import Optional


class MedicalService:
    """医案检索服务"""

    def __init__(self, api_url: str):
        self.api_url = api_url

    def search_medical_records(
        self,
        chief_complaint: str,
        present_illness: str,
        gender: Optional[str] = None,
        tongue: Optional[str] = None,
        pulse: Optional[str] = None,
        top_k: int = 3,
    ) -> str:
        """
        查询相似医案

        Args:
            chief_complaint: 主诉症状
            present_illness: 现病史
            gender: 性别
            tongue: 舌象
            pulse: 脉象
            top_k: 返回数量

        Returns:
            格式化的医案结果字符串
        """
        payload = {
            "chief_complaint": chief_complaint,
            "present_illness": present_illness,
            "top_k": top_k,
        }

        # 添加可选参数
        if gender:
            payload["gender"] = gender
        if tongue:
            payload["tongue"] = tongue
        if pulse:
            payload["pulse"] = pulse

        try:
            resp = requests.post(self.api_url, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            if not data.get("success"):
                return f"查询失败：{data.get('message', '未知错误')}"

            results = data.get("data", {}).get("results", [])
            if not results:
                return "未找到相似医案"

            # 格式化返回结果
            output = ["\n【相似医案参考】"]
            for i, r in enumerate(results, 1):
                output.append(f"\n{i}. {r.get('name', '未知')}")
                output.append(f"   医生：{r.get('doctor', '未知')}")
                output.append(f"   诊断：{r.get('cm_diagram', '未记载')}")
                if r.get("syndrome"):
                    output.append(f"   证型：{r['syndrome']}")
                if r.get("prescription_form"):
                    output.append(f"   方药：{r['prescription_form']}")
                output.append(f"   相似度：{r.get('score', 0):.2%}")

            return "\n".join(output)

        except requests.exceptions.RequestException as e:
            return f"查询出错：{str(e)}"
        except Exception as e:
            return f"查询出错：{str(e)}"
