#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接解析 OpenClaw 会话日志，提取工具调用统计信息
无需手动 instrumentation，自动从 .jsonl 文件读取
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import sqlite3


LOG_DIR = r"C:\Users\jinta\.openclaw\agents\main\sessions"
TRACKER_DB = r"D:\code\graduate\llm\trail\openclaw\tool_calls.db"


def parse_session_file(file_path: str) -> List[Dict[str, Any]]:
    """
    解析单个 .jsonl 会话文件
    
    返回工具调用列表，每条记录包含：
    - session_id
    - tool_name
    - timestamp (开始和结束)
    - duration_ms
    - status
    - input_tokens / output_tokens
    """
    records = []
    session_id = None
    current_tool_call = None  # 缓存正在等待结果的 tool call
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            msg_type = data.get('type')
            
            # 提取 session ID
            if msg_type == 'session':
                session_id = data.get('id')
                continue
            
            # 提取工具调用
            if msg_type == 'message':
                message = data.get('message', {})
                role = message.get('role')
                
                if role == 'assistant':
                    content = message.get('content', [])
                    for item in content:
                        if item.get('type') == 'toolCall':
                            tool_call = item
                            current_tool_call = {
                                'session_id': session_id,
                                'call_id': tool_call.get('id'),
                                'tool_name': tool_call.get('name'),
                                'arguments': tool_call.get('arguments', {}),
                                'start_time': data.get('timestamp'),
                                'api_info': message.get('usage', {}),
                            }
                
                elif role == 'toolResult' and current_tool_call:
                    # 这是工具调用的结果
                    tool_result = {
                        **current_tool_call,
                        'end_time': data.get('timestamp'),
                        'status': 'error' if data.get('isError') else 'completed',
                        'duration_ms': data.get('details', {}).get('durationMs'),
                        'exit_code': data.get('details', {}).get('exitCode'),
                    }
                    records.append(tool_result)
                    current_tool_call = None
                
                elif role == 'assistant':
                    # 检查是否有 API usage 信息
                    usage = message.get('usage', {})
                    if usage and current_tool_call is None:
                        # 这是普通对话的 token 消耗，不是工具调用
                        pass
    
    return records


def get_all_sessions_from_today() -> List[str]:
    """获取今天的会话文件列表"""
    today = datetime.now().strftime("%Y-%m-%d")
    sessions = []
    
    for file in Path(LOG_DIR).glob("*.jsonl"):
        # 跳过 reset/deleted 文件
        if '.reset.' in str(file) or '.deleted.' in str(file):
            continue
        
        # 简单判断是否是今天（文件名不包含日期信息，只能解析内容）
        sessions.append(str(file))
    
    return sessions


def extract_stats_from_logs() -> Dict[str, Any]:
    """
    从所有日志文件提取今日统计
    
    核心逻辑：
    1. 找到今天的会话文件
    2. 解析每个文件的工具调用
    3. 聚合统计信息
    """
    all_tools = []
    
    # 查找最近的会话文件（按修改时间排序）
    session_files = sorted(
        Path(LOG_DIR).glob("*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    # 只分析最近活跃的 5 个会话（防止扫描太多历史数据）
    recent_files = []
    cutoff_time = datetime.now().timestamp() - (24 * 60 * 60)  # 最近 24 小时
    
    for f in session_files:
        if f.stat().st_mtime >= cutoff_time:
            recent_files.append(str(f))
    
    print(f"[INFO] 分析 {len(recent_files)} 个会话文件...")
    
    for file_path in recent_files:
        tools = parse_session_file(file_path)
        all_tools.extend(tools)
    
    # 聚合统计
    total_tools = len(all_tools)
    completed = sum(1 for t in all_tools if t.get('status') == 'completed')
    failed = sum(1 for t in all_tools if t.get('status') == 'error')
    
    # 按工具分类
    from collections import Counter
    tool_counter = Counter(t['tool_name'] for t in all_tools if t.get('tool_name'))
    
    # 计算平均耗时
    durations = [t['duration_ms'] for t in all_tools if t.get('duration_ms')]
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    # Token 统计（需要从完整的 usage 字段提取）
    # 注意：日志中的 usage 字段可能为 0，因为有些版本不记录详细 token
    total_input = 0
    total_output = 0
    
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "sessions_analyzed": len(recent_files),
        "total_tools_called": total_tools,
        "completed_tools": completed,
        "failed_tools": failed,
        "success_rate": f"{completed/total_tools*100:.1f}%" if total_tools > 0 else "0%",
        "tools_breakdown": [{"tool": k, "count": v} for k, v in tool_counter.most_common()],
        "avg_duration_ms": round(avg_duration, 2),
        "total_duration_seconds": round(sum(durations)/1000, 2),
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_tokens": total_input + total_output,
    }


def save_to_db():
    """将日志分析结果保存到 tracker 数据库"""
    stats = extract_stats_from_logs()
    
    conn = sqlite3.connect(TRACKER_DB)
    cursor = conn.cursor()
    
    # 插入到 sessions 表
    cursor.execute("""
        INSERT INTO sessions (
            session_id, start_time, end_time, total_tools_called,
            total_duration_seconds, tools_breakdown,
            total_input_tokens, total_output_tokens
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        f"log_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        stats['total_tools_called'],
        stats['total_duration_seconds'],
        json.dumps(stats['tools_breakdown'], ensure_ascii=False),
        stats['total_input_tokens'],
        stats['total_output_tokens']
    ))
    
    # 插入工具调用记录
    # （简化版：只插入摘要，不插入每条详细记录）
    
    conn.commit()
    conn.close()
    
    print(f"[OK] 已保存统计到 {TRACKER_DB}")
    return stats


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="解析 OpenClaw 日志并生成统计")
    parser.add_argument('--analyze', action='store_true', help='只分析，不保存')
    parser.add_argument('--save', action='store_true', help='分析并保存到 tracker DB')
    parser.add_argument('--show-session-files', action='store_true', help='列出会话文件')
    
    args = parser.parse_args()
    
    if args.show_session_files:
        files = list(Path(LOG_DIR).glob("*.jsonl"))
        print(f"找到 {len(files)} 个会话文件:")
        for f in files[:10]:  # 只显示前 10 个
            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            print(f"  [{mtime}] {f.name}")
        if len(files) > 10:
            print(f"  ... 还有 {len(files) - 10} 个文件")
    
    elif args.save:
        stats = save_to_db()
        print("\n=== 今日统计 ===")
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    else:
        # 默认：只分析显示
        stats = extract_stats_from_logs()
        print("\n=== 从日志提取的统计 ===")
        print(json.dumps(stats, ensure_ascii=False, indent=2))
