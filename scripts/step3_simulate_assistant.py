#!/usr/bin/env python3
"""
阶段3：读取 with_responses.jsonl，用 LLM 根据 question + tool_response 生成 assistant 回复，
输出完整 train_samples.jsonl
无工具样本：根据 question 直接生成
配置：使用 config.Config 或环境变量 MODELSCOPE_API_KEY, MODELSCOPE_BASE_URL, MODELSCOPE_LLM_MODEL
"""

import json
import os
import sys
import time

from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _template_fallback(question: str, tool_response, category: str) -> str:
    """无 LLM 时的模板回退。"""
    if category == "no_tool" or tool_response is None:
        return "根据您的问题，我无法调用工具直接回答，建议您使用数据查询或知识检索工具获取更准确的信息。"
    if isinstance(tool_response, list):
        return "已依次完成工具调用，结果已汇总。"
    if isinstance(tool_response, dict):
        if tool_response.get("success"):
            return "工具调用成功，已根据返回结果为您整理信息。"
        return f"工具调用失败: {tool_response.get('error', '未知错误')}"
    return "处理完成。"


def _call_llm(question: str, tool_response, category: str, client, model: str) -> str:
    """调用 LLM 生成 assistant 回复。"""
    if category == "no_tool" or tool_response is None:
        prompt = f"用户问题：{question}\n\n请生成简洁、专业的助手回复，直接回答用户问题，无需调用工具。"
    else:
        resp_str = json.dumps(tool_response, ensure_ascii=False, indent=2)
        prompt = f"用户问题：{question}\n\n工具返回结果：\n{resp_str}\n\n请根据用户问题和工具返回结果，生成简洁、专业的助手回复，用自然语言总结关键信息。"
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM 调用失败: {e}，使用模板回退")
        return _template_fallback(question, tool_response, category)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="阶段3：模拟 assistant 回复")
    parser.add_argument("-i", "--input", default="data/train_gen/with_responses.jsonl", help="输入文件")
    parser.add_argument("-o", "--output", default="data/train_gen/train_samples.jsonl", help="输出文件")
    parser.add_argument("--no-llm", action="store_true", help="不使用 LLM，仅用模板回退")
    parser.add_argument("--delay", type=float, default=2.0, help="每次 LLM 调用间隔（秒），降低限流风险，默认 2")
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = args.input if os.path.isabs(args.input) else os.path.join(project_root, args.input)
    output_path = args.output if os.path.isabs(args.output) else os.path.join(project_root, args.output)

    if not os.path.exists(input_path):
        print(f"输入文件不存在: {input_path}")
        sys.exit(1)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 初始化 LLM 客户端
    client = None
    model = ""
    if not args.no_llm:
        try:
            from config.config import Config
            cfg = Config.get_api_config()
            if cfg.get("api_key"):
                from openai import OpenAI
                client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])
                model = cfg.get("model", "Qwen/Qwen2.5-7B-Instruct")
                print(f"使用 LLM: {model}")
            else:
                print("未配置 API_KEY，使用模板回退")
        except Exception as e:
            print(f"加载配置失败: {e}，使用模板回退")

    records = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))

    results = []
    for i, rec in enumerate(tqdm(records, desc="生成 assistant", unit="条")):
        question = rec["question"]
        tool_response = rec.get("tool_response")
        category = rec.get("category", "single_tool")

        if client and model:
            if i > 0:
                time.sleep(args.delay)
            assistant = _call_llm(question, tool_response, category, client, model)
        else:
            assistant = _template_fallback(question, tool_response, category)

        results.append({
            "question": question,
            "tool_call": rec.get("tool_call"),
            "tool_response": tool_response,
            "assistant": assistant,
            "category": category,
        })

    with open(output_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"已生成 {len(results)} 条完整样本，保存至 {output_path}")


if __name__ == "__main__":
    main()
