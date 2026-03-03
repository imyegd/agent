#!/usr/bin/env python3
"""
统计 test_samples.jsonl 中每个工具的调用量。
支持 single_tool（单个调用）和 tool_chain（多步调用）。
"""
import json
import os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_INPUT = os.path.join(ROOT, "data", "train_gen", "test_samples.jsonl")


def count_tool_calls(input_path: str) -> Counter:
    """统计每个工具的调用次数。"""
    counts = Counter()
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            tc = rec.get("tool_call")
            if tc is None:
                continue
            if isinstance(tc, list):
                for call in tc:
                    name = call.get("name")
                    if name:
                        counts[name] += 1
            elif isinstance(tc, dict):
                name = tc.get("name")
                if name:
                    counts[name] += 1
    return counts


def main():
    import argparse
    parser = argparse.ArgumentParser(description="统计工具调用量")
    parser.add_argument("-i", "--input", default=DEFAULT_INPUT, help="输入文件路径")
    args = parser.parse_args()
    input_path = args.input if os.path.isabs(args.input) else os.path.join(ROOT, args.input)
    if not os.path.exists(input_path):
        print(f"文件不存在: {input_path}")
        return
    counts = count_tool_calls(input_path)
    total = sum(counts.values())
    print(f"文件: {input_path}")
    print(f"总调用次数: {total}")
    print("-" * 40)
    for name, n in sorted(counts.items(), key=lambda x: -x[1]):
        pct = (n / total * 100) if total else 0
        print(f"  {name}: {n} ({pct:.1f}%)")
    print("-" * 40)
    print(f"涉及工具数: {len(counts)}")


if __name__ == "__main__":
    main()
