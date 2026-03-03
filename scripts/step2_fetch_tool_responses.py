#!/usr/bin/env python3
"""
阶段2：读取 questions.jsonl，调用真实工具获取 tool_response，输出到 with_responses.jsonl
单工具：调用一次；工具链：按顺序依次调用；无工具：tool_response 为 null
"""

import json
import os
import sys
from typing import Union

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import TOOL_FUNCTIONS


def call_tool(name: str, arguments: dict) -> Union[dict, str]:
    """调用单个工具，返回结果。失败时返回错误信息 dict。"""
    if name not in TOOL_FUNCTIONS:
        return {"success": False, "error": f"未知工具: {name}"}
    try:
        fn = TOOL_FUNCTIONS[name]
        result = fn(**arguments) if arguments else fn()
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_responses_for_record(record: dict) -> dict:
    """为一条记录获取 tool_response。"""
    question = record["question"]
    tool_call = record["tool_call"]
    category = record.get("category", "single_tool")

    if category == "no_tool" or tool_call is None:
        return {**record, "tool_response": None}

    if category == "tool_chain":
        # tool_call 为数组
        responses = []
        for tc in tool_call:
            name = tc.get("name")
            args = tc.get("arguments", {}) or {}
            resp = call_tool(name, args)
            responses.append(resp)
        return {**record, "tool_response": responses}

    # single_tool
    name = tool_call.get("name")
    args = tool_call.get("arguments", {}) or {}
    resp = call_tool(name, args)
    return {**record, "tool_response": resp}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="阶段2：获取 tool_response")
    parser.add_argument("-i", "--input", default="data/train_gen/questions.jsonl", help="输入文件")
    parser.add_argument("-o", "--output", default="data/train_gen/with_responses.jsonl", help="输出文件")
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = args.input if os.path.isabs(args.input) else os.path.join(project_root, args.input)
    output_path = args.output if os.path.isabs(args.output) else os.path.join(project_root, args.output)

    if not os.path.exists(input_path):
        print(f"输入文件不存在: {input_path}")
        sys.exit(1)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    records = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))

    results = []
    for i, rec in enumerate(records):
        try:
            out = fetch_responses_for_record(rec)
            results.append(out)
        except Exception as e:
            print(f"第 {i+1} 条处理失败: {e}")
            results.append({**rec, "tool_response": {"success": False, "error": str(e)}})

    with open(output_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"已处理 {len(results)} 条，保存至 {output_path}")


if __name__ == "__main__":
    main()
