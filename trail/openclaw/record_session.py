#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpenClaw 单次对话追踪脚本
用法：python record_session.py "任务描述" input_tokens output_tokens
"""

import sys
import os
import json

# 添加项目根目录到路径
sys.path.insert(0, r'D:\code\graduate\llm')

from trail.openclaw.task_tracker import TaskTracker


def main():
    if len(sys.argv) < 4:
        print("用法：python record_session.py \"任务描述\" input_tokens output_tokens")
        print("")
        print("示例:")
        print('  python record_session.py "束流数据查询" 150 80')
        print('  python record_session.py "论文第 3 章改写" 300 200')
        sys.exit(1)
    
    task_name = sys.argv[1]
    
    try:
        input_tokens = int(sys.argv[2])
        output_tokens = int(sys.argv[3])
    except ValueError:
        print("[ERROR] token 数必须是整数")
        sys.exit(1)
    
    # 执行追踪
    tracker = TaskTracker()
    tracker.start_task(task_name)
    result = tracker.complete_task({"input": input_tokens, "output": output_tokens})
    
    # 输出结果
    print(json.dumps({
        "success": True,
        "task_id": result.task_id,
        "task_name": result.task_name,
        "duration_seconds": round(result.duration_seconds, 2),
        "tokens": {
            "input": result.input_tokens,
            "output": result.output_tokens,
            "total": result.total_tokens
        }
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
