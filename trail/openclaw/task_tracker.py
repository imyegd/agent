#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpenClaw 任务追踪器
记录每次执行任务的耗时和 token 消耗
"""

import os
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

LOG_DIR = r"D:\code\graduate\llm\trail\openclaw"


@dataclass
class TaskRecord:
    """任务记录数据类"""
    task_id: str                          # 任务唯一标识
    task_name: str                        # 任务名称/描述
    start_time: str                       # 开始时间 (ISO 格式)
    end_time: Optional[str]               # 结束时间 (ISO 格式)，完成前为 None
    duration_seconds: Optional[float]     # 耗时 (秒)，未完成为 None
    input_tokens: Optional[int]           # 输入 token 数
    output_tokens: Optional[int]          # 输出 token 数
    total_tokens: Optional[int]           # 总 token 数
    status: str                           # 状态: running | completed | failed
    error_message: Optional[str]          # 错误信息（如有）
    metadata: Dict[str, Any]              # 额外元数据


class TaskTracker:
    """任务追踪器"""
    
    def __init__(self, log_dir: str = LOG_DIR):
        self.log_dir = log_dir
        self._ensure_log_dir()
        self._current_task: Optional[TaskRecord] = None
    
    def _ensure_log_dir(self):
        """确保日志目录存在"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _generate_task_id(self) -> str:
        """生成任务 ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        import random
        suffix = random.randint(1000, 9999)
        return f"task_{timestamp}_{suffix}"
    
    def _load_existing_records(self, log_file: str) -> list:
        """加载已有记录"""
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("records", [])
            except Exception:
                return []
        return []
    
    def start_task(self, task_name: str, metadata: Optional[Dict[str, Any]] = None) -> TaskRecord:
        """
        开始一个新任务
        
        Args:
            task_name: 任务名称/描述
            metadata: 额外元数据
            
        Returns:
            任务记录对象
        """
        self._current_task = TaskRecord(
            task_id=self._generate_task_id(),
            task_name=task_name,
            start_time=self._get_timestamp(),
            end_time=None,
            duration_seconds=None,
            input_tokens=None,
            output_tokens=None,
            total_tokens=None,
            status="running",
            error_message=None,
            metadata=metadata or {}
        )
        return self._current_task
    
    def update_tokens(self, input_tokens: int, output_tokens: int):
        """更新 token 消耗"""
        if self._current_task:
            self._current_task.input_tokens = input_tokens
            self._current_task.output_tokens = output_tokens
            self._current_task.total_tokens = input_tokens + output_tokens
    
    def complete_task(self, tokens: Optional[Dict[str, int]] = None):
        """
        完成任务
        
        Args:
            tokens: token 消耗字典，如 {"input": 100, "output": 50}
        """
        if not self._current_task:
            raise ValueError("没有正在进行的任务")
        
        if tokens:
            self.update_tokens(tokens.get("input", 0), tokens.get("output", 0))
        
        end_time = self._get_timestamp()
        start_dt = datetime.strptime(self._current_task.start_time, "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        duration = (end_dt - start_dt).total_seconds()
        
        self._current_task.end_time = end_time
        self._current_task.duration_seconds = duration
        self._current_task.status = "completed"
        
        self._save_record(self._current_task)
        record = self._current_task
        self._current_task = None
        
        return record
    
    def fail_task(self, error_message: str, tokens: Optional[Dict[str, int]] = None):
        """
        标记任务失败
        
        Args:
            error_message: 错误信息
            tokens: token 消耗字典
        """
        if not self._current_task:
            raise ValueError("没有正在进行的任务")
        
        if tokens:
            self.update_tokens(tokens.get("input", 0), tokens.get("output", 0))
        
        self._current_task.end_time = self._get_timestamp()
        self._current_task.error_message = error_message
        self._current_task.status = "failed"
        
        self._save_record(self._current_task)
        record = self._current_task
        self._current_task = None
        
        return record
    
    def _save_record(self, record: TaskRecord):
        """保存单条记录到日志文件"""
        log_file = os.path.join(self.log_dir, f"task_log_{datetime.now().strftime('%Y%m%d')}.json")
        
        records = self._load_existing_records(log_file)
        records.append(asdict(record))
        
        summary = self._generate_summary(records)
        
        output_data = {
            "log_date": datetime.now().strftime("%Y-%m-%d"),
            "generated_at": self._get_timestamp(),
            "summary": summary,
            "records": records
        }
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    def _generate_summary(self, records: list) -> Dict[str, Any]:
        """生成统计摘要"""
        completed = [r for r in records if r["status"] == "completed"]
        failed = [r for r in records if r["status"] == "failed"]
        running = [r for r in records if r["status"] == "running"]
        
        total_duration = sum(r.get("duration_seconds", 0) or 0 for r in completed)
        avg_duration = total_duration / len(completed) if completed else 0
        
        total_input_tokens = sum(r.get("input_tokens", 0) or 0 for r in completed)
        total_output_tokens = sum(r.get("output_tokens", 0) or 0 for r in completed)
        
        return {
            "total_tasks": len(records),
            "completed_tasks": len(completed),
            "failed_tasks": len(failed),
            "running_tasks": len(running),
            "success_rate": f"{len(completed) / len(records) * 100:.1f}%" if records else "0%",
            "total_duration_seconds": round(total_duration, 2),
            "avg_duration_seconds": round(avg_duration, 2),
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens
        }
    
    def get_daily_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        获取指定日期的统计摘要
        
        Args:
            date: 日期字符串 "YYYY-MM-DD"，不传则使用今天
            
        Returns:
            统计摘要字典
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        log_file = os.path.join(self.log_dir, f"task_log_{date.replace('-', '')}.json")
        
        if not os.path.exists(log_file):
            return {
                "date": date,
                "total_tasks": 0,
                "message": f"{date} 没有任务记录"
            }
        
        with open(log_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("summary", {})


# ============ LLM 可调用的工具函数 ============

def track_task_start(task_name: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    开始追踪一个新任务
    
    Args:
        task_name: 任务名称/描述
        metadata: 额外元数据（可选）
        
    Returns:
        任务启动信息
    """
    tracker = TaskTracker()
    record = tracker.start_task(task_name, metadata)
    
    return {
        "success": True,
        "action": "task_started",
        "task_id": record.task_id,
        "task_name": record.task_name,
        "start_time": record.start_time,
        "message": f"任务已启动，task_id={record.task_id}"
    }


def track_task_complete(input_tokens: int, output_tokens: int) -> Dict[str, Any]:
    """
    标记任务完成并记录 token 消耗
    
    Args:
        input_tokens: 输入 token 数
        output_tokens: 输出 token 数
        
    Returns:
        任务完成记录
    """
    tracker = TaskTracker()
    record = tracker.complete_task({
        "input": input_tokens,
        "output": output_tokens
    })
    
    return {
        "success": True,
        "action": "task_completed",
        "task_id": record.task_id,
        "duration_seconds": round(record.duration_seconds, 2),
        "tokens": {
            "input": record.input_tokens,
            "output": record.output_tokens,
            "total": record.total_tokens
        },
        "message": f"任务完成，耗时{record.duration_seconds:.2f}秒，共{record.total_tokens} tokens"
    }


def track_task_fail(error_message: str, input_tokens: int = 0, output_tokens: int = 0) -> Dict[str, Any]:
    """
    标记任务失败
    
    Args:
        error_message: 错误信息
        input_tokens: 输入 token 数（失败时可能有部分消耗）
        output_tokens: 输出 token 数
        
    Returns:
        任务失败记录
    """
    tracker = TaskTracker()
    record = tracker.fail_task(error_message, {
        "input": input_tokens,
        "output": output_tokens
    })
    
    return {
        "success": False,
        "action": "task_failed",
        "task_id": record.task_id,
        "error": error_message,
        "message": f"任务失败：{error_message}"
    }


def get_daily_stats(date: Optional[str] = None) -> Dict[str, Any]:
    """
    获取指定日期的任务统计
    
    Args:
        date: 日期字符串 "YYYY-MM-DD"，不传则使用今天
        
    Returns:
        统计信息
    """
    tracker = TaskTracker()
    summary = tracker.get_daily_summary(date)
    
    return {
        "success": True,
        "action": "get_daily_stats",
        "date": date or datetime.now().strftime("%Y-%m-%d"),
        "stats": summary
    }


# 工具函数映射
TRACKER_FUNCTIONS = {
    "track_task_start": track_task_start,
    "track_task_complete": track_task_complete,
    "track_task_fail": track_task_fail,
    "get_daily_stats": get_daily_stats
}


# 测试入口
if __name__ == "__main__":
    # 示例：手动测试
    print("[INFO] OpenClaw 任务追踪器测试\n")
    
    # 模拟一个任务
    tracker = TaskTracker()
    record = tracker.start_task("测试任务：数据查询")
    print(f"[OK] 任务启动：{record.task_id}")
    
    time.sleep(1)  # 模拟工作
    
    result = tracker.complete_task({"input": 150, "output": 80})
    print(f"[OK] 任务完成:")
    print(f"  - 耗时：{result.duration_seconds:.2f}秒")
    print(f"  - Token: {result.total_tokens} (输入:{result.input_tokens}, 输出:{result.output_tokens})")
    print(f"\n[LOG] 日志已保存到：{LOG_DIR}")
