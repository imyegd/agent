#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpenClaw 监控中间件
在每次 exec/read/write/tool 调用前后自动记录耗时和状态
用法：在 Python 代码中 import并使用monitor_exec替代直接exec
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Any, Dict, Optional

sys.path.insert(0, r'D:\code\graduate\llm')

from trail.openclaw.full_session_tracker import FullSessionTracker


class OpenClawMonitor:
    """OpenClaw 操作监控器"""
    
    def __init__(self, log_dir: str = r"D:\code\graduate\llm\trail\openclaw"):
        self.log_dir = log_dir
        self.tracker = FullSessionTracker(os.path.join(log_dir, "tool_calls.db"))
        self._current_session_id: Optional[str] = None
        self._call_stack: list = []
    
    def start_session(self, user_prompt: str):
        """开始一个会话"""
        self._current_session_id = self.tracker.start_session(user_prompt)
        print(f"[MONITOR] 会话已启动：{self._current_session_id}")
        return self._current_session_id
    
    def end_session(self, input_tokens: int = 0, output_tokens: int = 0):
        """结束当前会话"""
        if not self._current_session_id:
            print("[MONITOR] 警告：没有活跃的会话")
            return
        
        self.tracker.end_session(input_tokens, output_tokens)
        print(f"[MONITOR] 会话已结束：{self._current_session_id}")
        print(f"[MONITOR] Token: input={input_tokens}, output={output_tokens}")
        self._current_session_id = None
    
    def monitor_call(self, tool_name: str, args: Dict[str, Any]) -> 'CallContext':
        """
        监控一个工具调用
        
        使用方式:
            with monitor.monitor_call("exec", {"command": "ls"}) as ctx:
                result = subprocess.run(...)
                ctx.set_result(result)
        """
        if not self._current_session_id:
            print(f"[MONITOR] 警告：没有活跃会话，跳过 {tool_name} 记录")
            return CallContext(None, None)
        
        call_id = self.tracker.record_tool_start(tool_name, args)
        self._call_stack.append(call_id)
        
        return CallContext(self.tracker, call_id)
    
    def get_today_stats(self) -> Dict[str, Any]:
        """获取今日统计"""
        return self.tracker.get_daily_summary()


class CallContext:
    """工具调用上下文管理器"""
    
    def __init__(self, tracker: Optional[FullSessionTracker], call_id: Optional[str]):
        self.tracker = tracker
        self.call_id = call_id
        self.start_time = None
        self.result = None
        self.error = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.tracker and self.call_id:
            end_time = time.time()
            duration_ms = int((end_time - self.start_time) * 1000)
            
            if exc_type:
                # 发生了异常
                self.error = f"{exc_type.__name__}: {str(exc_val)}"
                self.tracker.record_tool_end(
                    self.call_id, 
                    {"error": self.error}, 
                    success=False, 
                    error=self.error
                )
            else:
                # 成功完成
                self.tracker.record_tool_end(
                    self.call_id,
                    self.result or {"duration_ms": duration_ms},
                    success=True
                )
        
        return False  # 不吞掉异常
    
    def set_result(self, result: Any):
        """手动设置结果（在 __exit__ 前）"""
        self.result = result


# ==================== 快捷函数 ====================

# 全局监控器实例
_monitor: Optional[OpenClawMonitor] = None


def init_monitor():
    """初始化全局监控器"""
    global _monitor
    _monitor = OpenClawMonitor()
    return _monitor


def start(prompt: str):
    """开始会话"""
    if not _monitor:
        init_monitor()
    return _monitor.start_session(prompt)


def end(input_tokens: int = 0, output_tokens: int = 0):
    """结束会话"""
    if not _monitor:
        raise RuntimeError("请先调用 init_monitor()")
    _monitor.end_session(input_tokens, output_tokens)


def track(tool_name: str, args: Dict[str, Any]):
    """
    装饰器：跟踪一个函数的执行
    
    使用示例:
        @track("read", {"file_path": "test.txt"})
        def read_file(path):
            return open(path).read()
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not _monitor:
                return func(*args, **kwargs)
            
            with _monitor.monitor_call(tool_name, args if isinstance(args, dict) else {}):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    raise
        return wrapper
    return decorator


# ==================== CLI 入口 ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenClaw 操作监控器")
    parser.add_argument('--start', help='开始会话的用户提示')
    parser.add_argument('--end', action='store_true', help='结束会话')
    parser.add_argument('--input-tokens', type=int, default=0)
    parser.add_argument('--output-tokens', type=int, default=0)
    parser.add_argument('--stats', action='store_true', help='显示今日统计')
    parser.add_argument('--demo', action='store_true', help='运行演示')
    
    args = parser.parse_args()
    
    if args.demo:
        print("=== 运行演示 ===\n")
        monitor = OpenClawMonitor()
        
        monitor.start_session("帮我查询束流数据并生成报告")
        
        with monitor.monitor_call("read", {"path": "data/束流.csv"}):
            time.sleep(0.1)  # 模拟读取
        
        with monitor.monitor_call("query_beam_data", {"start_time": "17:30", "end_time": "18:30"}):
            time.sleep(0.2)  # 模拟查询
        
        with monitor.monitor_call("session_status", {}):
            time.sleep(0.05)  # 模拟状态查询
        
        monitor.end_session(input_tokens=300, output_tokens=200)
        
        print("\n=== 今日统计 ===")
        stats = monitor.get_today_stats()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    elif args.start:
        monitor = OpenClawMonitor()
        start(args.start)
        print(f"[OK] 会话 ID: {args.start}")
    
    elif args.end:
        if not _monitor:
            print("[ERROR] 没有活跃的监控器")
            exit(1)
        end(args.input_tokens, args.output_tokens)
    
    elif args.stats:
        if not _monitor:
            init_monitor()
        stats = _monitor.get_today_stats()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()
