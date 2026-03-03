#!/usr/bin/env python3
"""
将 test_samples.jsonl 转为 train_beam_tools.jsonl 格式。
每条样本加上 11 个工具定义，并转换为 messages 结构。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_INPUT = os.path.join(ROOT, "data", "train_gen", "train_samples.jsonl")
DEFAULT_OUTPUT = os.path.join(ROOT, "data", "train_gen", "train.jsonl")
TOOLS_PATH = os.path.join(ROOT, "data", "tools_summary.json")


def load_tools():
    """加载 11 个工具定义。优先 tools_summary.json，否则从 tools 模块导入。"""
    if os.path.exists(TOOLS_PATH):
        with open(TOOLS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    import sys
    sys.path.insert(0, ROOT)
    try:
        from tools import TOOLS
        return list(TOOLS)
    except Exception:
        raise FileNotFoundError("未找到 tools_summary.json 且 tools 模块加载失败")


def format_tool_call(tc: dict) -> str:
    return json.dumps({"name": tc["name"], "arguments": tc.get("arguments", {}) or {}}, ensure_ascii=False)


def format_tool_response(resp) -> str:
    return str(resp)


def sample_to_messages(s: dict) -> list:
    """将单条样本转为 messages 列表。支持 single_tool、tool_chain、no_tool。"""
    messages = [{"role": "user", "content": s["question"]}]
    tool_call = s.get("tool_call")
    tool_response = s.get("tool_response")

    if tool_call is None or tool_response is None:
        messages.append({"role": "assistant", "content": s["assistant"]})
        return messages

    if isinstance(tool_call, list):
        for tc, tr in zip(tool_call, tool_response):
            messages.append({"role": "tool_call", "content": format_tool_call(tc)})
            messages.append({"role": "tool_response", "content": format_tool_response(tr)})
    else:
        messages.append({"role": "tool_call", "content": format_tool_call(tool_call)})
        messages.append({"role": "tool_response", "content": format_tool_response(tool_response)})
    messages.append({"role": "assistant", "content": s["assistant"]})
    return messages


def main():
    import argparse
    parser = argparse.ArgumentParser(description="将 test_samples.jsonl 转为 train_beam_tools 格式")
    parser.add_argument("-i", "--input", default=DEFAULT_INPUT, help="输入 test_samples.jsonl 路径")
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT, help="输出 jsonl 路径")
    args = parser.parse_args()
    input_path = args.input if os.path.isabs(args.input) else os.path.join(ROOT, args.input)
    output_path = args.output if os.path.isabs(args.output) else os.path.join(ROOT, args.output)

    if not os.path.exists(input_path):
        print(f"输入文件不存在: {input_path}")
        return

    tools = load_tools()
    tools_str = json.dumps(tools, ensure_ascii=False)
    print(f"已加载 {len(tools)} 个工具")

    samples = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            samples.append(json.loads(line))

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for s in samples:
            messages = sample_to_messages(s)
            rec = {"tools": tools_str, "messages": messages}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"已转换 {len(samples)} 条样本，保存至 {output_path}")


if __name__ == "__main__":
    main()
