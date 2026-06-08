#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpenClaw 自动对话追踪钩子
在每次对话前后自动记录任务耗时和 token 消耗
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any

# 添加项目路径
sys.path.insert(0, r'D:\code\graduate\llm')

from trail.openclaw.task_tracker import TaskTracker


class AutoTaskTracker:
    """自动任务追踪器 - 用于包装每次对话"""
    
    def __init__(self):
        self.tracker = TaskTracker()
        self._current_task_id: Optional[str] = None
        self._start_time: Optional[float] = None
    
    def on_dialogue_start(self, user_message: str) -> Dict[str, Any]:
        """
        对话开始时的钩子
        
        Args:
            user_message: 用户输入的消息内容
            
        Returns:
            启动信息
        """
        self._start_time = time.time()
        
        # 根据消息内容生成任务名称
        task_name = self._extract_task_name(user_message)
        
        metadata = {
            "message_length": len(user_message),
            "timestamp": datetime.now().isoformat()
        }
        
        record = self.tracker.start_task(task_name, metadata)
        self._current_task_id = record.task_id
        
        return {
            "hook": "dialogue_start",
            "task_id": record.task_id,
            "task_name": record.task_name,
            "start_time": record.start_time
        }
    
    def on_dialogue_end(self, input_tokens: int, output_tokens: int, success: bool = True, 
                        error_message: Optional[str] = None) -> Dict[str, Any]:
        """
        对话结束时的钩子
        
        Args:
            input_tokens: 输入 token 数
            output_tokens: 输出 token 数
            success: 是否成功完成
            error_message: 错误信息（如失败）
            
        Returns:
            完成记录
        """
        if not self._current_task_id:
            return {"error": "没有正在进行的任务"}
        
        tokens = {"input": input_tokens, "output": output_tokens}
        
        if success:
            record = self.tracker.complete_task(tokens)
        else:
            record = self.tracker.fail_task(error_message or "未知错误", tokens)
        
        end_time = time.time()
        actual_duration = end_time - (time.time() - record.duration_seconds) if record.duration_seconds else None
        
        result = {
            "hook": "dialogue_end",
            "task_id": record.task_id,
            "status": record.status,
            "duration_seconds": round(record.duration_seconds, 2),
            "tokens": {
                "input": record.input_tokens,
                "output": record.output_tokens,
                "total": record.total_tokens
            }
        }
        
        if error_message:
            result["error"] = error_message
        
        self._current_task_id = None
        
        return result
    
    def _extract_task_name(self, message: str) -> str:
        """从用户消息中提取任务名称"""
        message = message.strip()
        
        # 关键词映射
        keywords = {
            "查询": "数据查询",
            "束流": "束流数据处理",
            "target": "目标值分析",
            "feature": "特征分析",
            "数据": "数据查询",
            "论文": "论文修改",
            "改写": "文本改写",
            "摘要": "摘要撰写",
            "实验": "实验处理",
            "异常": "异常诊断",
            "可视": "数据可视化",
            "统计": "统计分析",
            "安装": "环境安装",
            "错误": "问题排查",
            "bug": "问题排查",
            "配置": "配置修改",
            "创建": "资源创建",
            "工具": "工具开发",
            "default": "常规对话"
        }
        
        for keyword, task_name in keywords.items():
            if keyword in message:
                return task_name
        
        # 默认返回消息前 20 个字符
        return f"用户请求：{message[:20]}..." if len(message) > 20 else f"用户请求：{message}"
    
    def get_session_stats(self) -> Dict[str, Any]:
        """获取今日会话统计"""
        return self.tracker.get_daily_summary()


# ==================== 使用示例 ====================

if __name__ == "__main__":
    print("[INFO] OpenClaw 自动对话追踪钩子\n")
    
    tracker = AutoTaskTracker()
    
    # 模拟一次对话
    user_msg = "帮我查询 2025-08-30 的束流数据"
    
    print(f"[START] 用户消息：{user_msg}")
    start_result = tracker.on_dialogue_start(user_msg)
    print(f"[INFO] 任务已启动：{start_result['task_id']}")
    
    # 模拟等待和处理
    time.sleep(0.5)
    
    # 模拟完成（实际使用需要从 session_status 获取真实 token 数）
    end_result = tracker.on_dialogue_end(
        input_tokens=120,
        output_tokens=95,
        success=True
    )
    print(f"[END] 任务完成:")
    print(f"  - 耗时：{end_result['duration_seconds']}秒")
    print(f"  - Token: {end_result['tokens']['total']}")
    
    # 查看统计
    stats = tracker.get_session_stats()
    print(f"\n[STATS] 今日统计:")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
