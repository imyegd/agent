#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整会话追踪器 - 记录每次对话中的所有工具调用
用法：运行此脚本启动 "被追踪的 session"，所有 tool calls 都会被记录
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict, field
import sqlite3


LOG_DIR = r"D:\code\graduate\llm\trail\openclaw"
DB_PATH = os.path.join(LOG_DIR, "tool_calls.db")


@dataclass
class ToolCallRecord:
    """单个工具调用记录"""
    session_id: str                    # 会话 ID
    call_id: str                       # 工具调用 ID
    tool_name: str                     # 工具名 (read/write/exec/memory_search 等)
    start_time: str                    # 开始时间
    end_time: Optional[str]            # 结束时间
    duration_ms: Optional[int]         # 耗时 (毫秒)
    status: str                        # running | completed | failed
    input_args: Optional[str]          # 输入参数 (JSON 字符串)
    output_result: Optional[str]       # 输出结果 (JSON 字符串，截断)
    error_message: Optional[str]       # 错误信息


@dataclass  
class SessionSummary:
    """会话摘要"""
    session_id: str
    start_time: str
    end_time: Optional[str]
    total_tools_called: int
    total_duration_seconds: float
    tools_breakdown: Dict[str, int]     # 各工具调用次数
    total_input_tokens: int             # 需要手动填入或从 API 获取
    total_output_tokens: int


class FullSessionTracker:
    """完整会话追踪器"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._ensure_db()
        self._current_session_id: Optional[str] = None
    
    def _ensure_db(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 工具调用记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                call_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_ms INTEGER,
                status TEXT NOT NULL,
                input_args TEXT,
                output_result TEXT,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 会话摘要表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                start_time TEXT NOT NULL,
                end_time TEXT,
                total_tools_called INTEGER DEFAULT 0,
                total_duration_seconds REAL DEFAULT 0,
                tools_breakdown TEXT,  -- JSON 字符串
                total_input_tokens INTEGER DEFAULT 0,
                total_output_tokens INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tool_calls_session ON tool_calls(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tool_calls_tool_name ON tool_calls(tool_name)")
        
        conn.commit()
        conn.close()
    
    def start_session(self, user_prompt: str) -> str:
        """开始一个新会话追踪"""
        import random
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = random.randint(1000, 9999)
        session_id = f"session_{timestamp}_{suffix}"
        
        self._current_session_id = session_id
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sessions (session_id, start_time, total_tools_called)
            VALUES (?, ?, 0)
        """, (session_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        # 记录用户 prompt 作为一个虚拟工具调用
        cursor.execute("""
            INSERT INTO tool_calls (session_id, call_id, tool_name, start_time, status, input_args)
            VALUES (?, ?, 'user_prompt', ?, 'completed', ?)
        """, (session_id, f"{session_id}_prompt_0", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
              user_prompt[:500]))
        
        conn.commit()
        conn.close()
        
        return session_id
    
    def record_tool_start(self, tool_name: str, args: Dict[str, Any]) -> str:
        """记录工具调用开始"""
        if not self._current_session_id:
            raise ValueError("没有活跃的会话")
        
        import random
        call_id = f"{self._current_session_id}_tool_{random.randint(10000, 99999)}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 插入记录（先只写基本信息）
        cursor.execute("""
            INSERT INTO tool_calls (session_id, call_id, tool_name, start_time, status, input_args)
            VALUES (?, ?, ?, ?, 'running', ?)
        """, (self._current_session_id, call_id, tool_name, 
              datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              json.dumps(args, ensure_ascii=False)[:2000]))  # 限制长度
        
        conn.commit()
        conn.close()
        
        return call_id
    
    def record_tool_end(self, call_id: str, result: Any, success: bool = True, error: Optional[str] = None):
        """记录工具调用结束"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        start_time_cursor = cursor.execute(
            "SELECT start_time FROM tool_calls WHERE call_id = ?", (call_id,)
        ).fetchone()
        
        if start_time_cursor:
            start_time = start_time_cursor[0]
            start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            duration_ms = int((end_dt - start_dt).total_seconds() * 1000)
        else:
            duration_ms = None
        
        # 更新记录
        cursor.execute("""
            UPDATE tool_calls 
            SET end_time = ?, duration_ms = ?, status = ?, output_result = ?, error_message = ?
            WHERE call_id = ?
        """, (end_time, duration_ms, 
              'completed' if success else 'failed',
              json.dumps(result, ensure_ascii=False)[:5000] if result else None,  # 限制长度
              error,
              call_id))
        
        # 更新会话统计
        cursor.execute("""
            UPDATE sessions 
            SET total_tools_called = total_tools_called + 1
            WHERE session_id = ?
        """, (self._current_session_id,))
        
        conn.commit()
        conn.close()
    
    def end_session(self, input_tokens: int = 0, output_tokens: int = 0):
        """结束会话并计算摘要"""
        if not self._current_session_id:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 计算总耗时
        total_duration = cursor.execute("""
            SELECT COALESCE(SUM(duration_ms), 0) FROM tool_calls 
            WHERE session_id = ? AND status = 'completed'
        """, (self._current_session_id,)).fetchone()[0]
        
        # 按工具类型统计
        tools_breakdown = cursor.execute("""
            SELECT tool_name, COUNT(*) FROM tool_calls 
            WHERE session_id = ?
            GROUP BY tool_name
        """, (self._current_session_id,)).fetchall()
        
        breakdown_json = json.dumps(dict(tools_breakdown), ensure_ascii=False)
        
        # 更新会话摘要
        cursor.execute("""
            UPDATE sessions 
            SET end_time = ?, total_duration_seconds = ?, tools_breakdown = ?,
                total_input_tokens = ?, total_output_tokens = ?
            WHERE session_id = ?
        """, (end_time, round(total_duration / 1000, 2), breakdown_json,
              input_tokens, output_tokens, self._current_session_id))
        
        conn.commit()
        conn.close()
        self._current_session_id = None
    
    def get_session_report(self, session_id: str) -> Dict[str, Any]:
        """获取会话报告"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 会话摘要
        session_data = cursor.execute("""
            SELECT * FROM sessions WHERE session_id = ?
        """, (session_id,)).fetchone()
        
        if not session_data:
            return {"error": f"会话 {session_id} 不存在"}
        
        # 工具调用详情
        calls = cursor.execute("""
            SELECT * FROM tool_calls WHERE session_id = ? ORDER BY start_time
        """, (session_id,)).fetchall()
        
        conn.close()
        
        columns = ['id', 'session_id', 'call_id', 'tool_name', 'start_time', 'end_time',
                   'duration_ms', 'status', 'input_args', 'output_result', 'error_message']
        
        return {
            "session": dict(zip(columns[:-3], session_data[:-3])),
            "tools_called": len(calls),
            "calls": [dict(zip(columns, call)) for call in calls]
        }
    
    def get_daily_summary(self, date: str = None) -> Dict[str, Any]:
        """获取日期范围的统计"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 当日会话数
        sessions_count = cursor.execute("""
            SELECT COUNT(*) FROM sessions 
            WHERE DATE(start_time) = DATE(?)
        """, (date,)).fetchone()[0]
        
        # 当日工具调用总数
        tools_count = cursor.execute("""
            SELECT COUNT(*) FROM tool_calls t
            INNER JOIN sessions s ON t.session_id = s.session_id
            WHERE DATE(s.start_time) = DATE(?)
        """, (date,)).fetchone()[0]
        
        # 按工具分类统计
        tools_breakdown = cursor.execute("""
            SELECT t.tool_name, COUNT(*) as count, AVG(t.duration_ms) as avg_ms
            FROM tool_calls t
            INNER JOIN sessions s ON t.session_id = s.session_id
            WHERE DATE(s.start_time) = DATE(?) AND t.status = 'completed' AND t.duration_ms IS NOT NULL
            GROUP BY t.tool_name
            ORDER BY count DESC
        """, (date,)).fetchall()
        
        # 总 token 消耗
        total_tokens = cursor.execute("""
            SELECT SUM(total_input_tokens), SUM(total_output_tokens) FROM sessions
            WHERE DATE(start_time) = DATE(?)
        """, (date,)).fetchone()
        
        conn.close()
        
        return {
            "date": date,
            "sessions_count": sessions_count,
            "tools_called": tools_count,
            "tools_breakdown": [{"tool": t[0], "count": t[1], "avg_ms": round(t[2], 2) if t[2] else 0} 
                               for t in tools_breakdown],
            "total_input_tokens": total_tokens[0] or 0,
            "total_output_tokens": total_tokens[1] or 0,
            "total_tokens": (total_tokens[0] or 0) + (total_tokens[1] or 0)
        }


# ==================== CLI 入口 ====================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenClaw 完整会话追踪器")
    subparsers = parser.add_subparsers(dest='command')
    
    # start 子命令
    start_parser = subparsers.add_parser('start', help='开始一个新会话')
    start_parser.add_argument('prompt', help='用户提示词')
    
    # tool 子命令
    tool_parser = subparsers.add_parser('tool', help='记录工具调用')
    tool_parser.add_argument('name', help='工具名称')
    tool_parser.add_argument('--args', help='工具参数 (JSON)')
    tool_parser.add_argument('--result', help='工具结果 (JSON)')
    tool_parser.add_argument('--success', action='store_true', default=True)
    tool_parser.add_argument('--error', help='错误信息')
    
    # end 子命令
    end_parser = subparsers.add_parser('end', help='结束当前会话')
    end_parser.add_argument('--input-tokens', type=int, default=0)
    end_parser.add_argument('--output-tokens', type=int, default=0)
    
    # report 子命令
    report_parser = subparsers.add_parser('report', help='获取会话报告')
    report_parser.add_argument('session_id', help='会话 ID')
    
    # stats 子命令
    stats_parser = subparsers.add_parser('stats', help='获取今日/指定日期统计')
    stats_parser.add_argument('--date', help='日期 (YYYY-MM-DD)，默认今天')
    
    args = parser.parse_args()
    tracker = FullSessionTracker()
    
    if args.command == 'start':
        session_id = tracker.start_session(args.prompt)
        print(json.dumps({"success": True, "session_id": session_id}, ensure_ascii=False))
    
    elif args.command == 'tool':
        call_id = tracker.record_tool_start(args.name, json.loads(args.args or '{}'))
        if args.result:
            tracker.record_tool_end(call_id, json.loads(args.result), args.success, args.error)
        print(json.dumps({"success": True, "call_id": call_id}, ensure_ascii=False))
    
    elif args.command == 'end':
        tracker.end_session(args.input_tokens, args.output_tokens)
        print(json.dumps({"success": True, "message": "会话已结束"}, ensure_ascii=False))
    
    elif args.command == 'report':
        report = tracker.get_session_report(args.session_id)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    
    elif args.command == 'stats':
        stats = tracker.get_daily_summary(args.date)
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
