#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查看单次 OpenClaw 对话的详细工具调用记录
用法：python show_session.py [会话文件名]
"""

import sys
import json
from pathlib import Path
from datetime import datetime


LOG_DIR = r"C:\Users\jinta\.openclaw\agents\main\sessions"


def parse_session_file(file_path: str):
    """解析单个会话文件，提取工具调用详情"""
    
    tool_calls = []
    session_id = None
    current_tool = None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
            except:
                continue
            
            msg_type = data.get('type')
            
            if msg_type == 'session':
                session_id = data.get('id')
                start_time = data.get('timestamp')
                continue
            
            if msg_type == 'message':
                message = data.get('message', {})
                role = message.get('role')
                
                # 工具调用
                if role == 'assistant':
                    content = message.get('content', [])
                    usage = message.get('usage', {})
                    
                    for item in content:
                        if item.get('type') == 'toolCall':
                            current_tool = {
                                'call_id': item.get('id'),
                                'tool_name': item.get('name'),
                                'arguments': item.get('arguments', {}),
                                'start_time': data.get('timestamp'),
                                'input_tokens': usage.get('input', 0),
                                'output_tokens': usage.get('output', 0),
                            }
                
                # 工具结果
                elif role == 'toolResult' and current_tool:
                    details = data.get('details', {})
                    duration_ms = details.get('durationMs', 0)
                    
                    tool_calls.append({
                        **current_tool,
                        'end_time': data.get('timestamp'),
                        'duration_ms': duration_ms,
                        'status': 'error' if data.get('isError') else 'completed',
                        'exit_code': details.get('exitCode'),
                    })
                    current_tool = None
    
    return session_id, start_time, tool_calls


def format_duration(ms):
    """格式化耗时"""
    if ms >= 1000:
        return f"{ms/1000:.2f}s"
    return f"{ms}ms"


def main():
    # 如果没有指定文件，列出最近的会话
    if len(sys.argv) < 2:
        files = sorted(
            Path(LOG_DIR).glob("*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        print("\n=== 最近的会话 ===")
        for i, f in enumerate(files[:10], 1):
            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            tools_count = len(list(open(f, 'r', encoding='utf-8')))
            print(f"{i}. [{mtime}] {f.name}")
        
        print("\n用法：python show_session.py <会话文件名>")
        print("示例：python show_session.py d76bcbe7-45a8-4687-b402-1d3ad610bfa4.jsonl")
        return
    
    file_name = sys.argv[1]
    file_path = Path(LOG_DIR) / file_name
    
    if not file_path.exists():
        print(f"[错误] 文件不存在：{file_path}")
        return
    
    session_id, start_time, tool_calls = parse_session_file(str(file_path))
    
    if not tool_calls:
        print("[信息] 这个会话没有工具调用")
        return
    
    total_input = sum(t['input_tokens'] for t in tool_calls)
    total_output = sum(t['output_tokens'] for t in tool_calls)
    total_duration = sum(t['duration_ms'] for t in tool_calls)
    
    print(f"\n{'='*60}")
    print(f"会话 ID: {session_id}")
    print(f"开始时间: {start_time}")
    print(f"工具调用数: {len(tool_calls)}")
    print(f"总耗时：{format_duration(total_duration)}")
    print(f"Token: input={total_input}, output={total_output}")
    print('='*60)
    
    for i, t in enumerate(tool_calls, 1):
        args_str = json.dumps(t['arguments'], ensure_ascii=False)[:100]
        if len(json.dumps(t['arguments'], ensure_ascii=False)) > 100:
            args_str += "..."
        
        print(f"\n{i}. [{t['tool_name']}] {format_duration(t['duration_ms'])}")
        print(f"   参数：{args_str}")
        if t['status'] == 'error':
            print(f"   ⚠️ 状态：错误 (退出码：{t['exit_code']})")


if __name__ == "__main__":
    main()
