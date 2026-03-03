#!/usr/bin/env python3
"""
阶段1：生成 question + tool_call，输出到 data/train_gen/questions.jsonl
支持单工具(x)、工具链(x)、无工具(x) 三类，x 可配置。
时间范围从 data/束流.csv 动态获取，禁止使用「昨天」「最近一小时」等相对时间。
使用 LLM 根据工具定义生成问题；--no-llm 时回退到模板。
"""

import json
import os
import re
import sys
import time
from typing import List, Optional, Tuple

from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import TOOLS, TOOL_FUNCTIONS

# 默认时间范围（当 CSV 不存在时使用）
DEFAULT_TIME_START = "2025-08-01 00:00:00"
DEFAULT_TIME_END = "2025-09-01 23:59:59"

# 每类样本数量
X = 2


def get_time_range(project_root: str) -> Tuple[str, str]:
    """从 data/束流.csv 读取时间范围，不存在则返回默认值。"""
    csv_path = os.path.join(project_root, "data", "束流.csv")
    if not os.path.exists(csv_path):
        return DEFAULT_TIME_START, DEFAULT_TIME_END
    try:
        import pandas as pd
        df = pd.read_csv(csv_path)
        df["时间"] = pd.to_datetime(df["时间"])
        t_min = df["时间"].min().strftime("%Y-%m-%d %H:%M:%S")
        t_max = df["时间"].max().strftime("%Y-%m-%d %H:%M:%S")
        return t_min, t_max
    except Exception as e:
        print(f"读取时间范围失败: {e}，使用默认值")
        return DEFAULT_TIME_START, DEFAULT_TIME_END


def _extract_json_from_response(text: str) -> Optional[str]:
    """从 LLM 回复中提取 JSON（可能被 ```json ... ``` 包裹）。"""
    text = text.strip()
    # 尝试匹配 ```json ... ``` 或 ``` ... ```
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        return m.group(1).strip()
    # 尝试直接解析整段
    return text


def _call_llm_generate_questions(
    prompt: str,
    client,
    model: str,
    max_retries: int = 2,
) -> List[dict]:
    """调用 LLM 生成问题，返回 [{"question": "...", "tool_call": {...}}, ...]。"""
    for attempt in range(max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
                temperature=0.7,
            )
            raw = resp.choices[0].message.content.strip()
            json_str = _extract_json_from_response(raw)
            if not json_str:
                raise ValueError("无法从回复中提取 JSON")
            data = json.loads(json_str)
            if not isinstance(data, list):
                data = [data]
            return data
        except json.JSONDecodeError as e:
            if attempt < max_retries:
                time.sleep(2)
                continue
            raise ValueError(f"LLM 返回非合法 JSON: {e}")
        except Exception as e:
            if attempt < max_retries:
                time.sleep(2)
                continue
            raise
    return []


# ========== 提示词 ==========

SINGLE_TOOL_PROMPT = """你是一个束流分析领域的对话数据生成助手。请根据以下工具定义，生成 {x} 个用户问题及对应的工具调用。

## 工具定义
```json
{tool_def}
```

## 数据时间范围
- 开始: {time_start}
- 结束: {time_end}
说明：所有涉及时间的参数（如 start_time、end_time、anomaly_start、anomaly_end、normal_start、normal_end 等）必须使用该范围内的具体日期时间，格式为 "YYYY-MM-DD HH:MM:SS"。禁止使用「昨天」「最近一小时」「上周」等相对时间表述。

## 要求
1. 每个问题用自然语言表达，符合真实用户口吻，可口语化。
2. 每个问题对应一次工具调用，tool_call 的 name 必须与工具定义一致，arguments 必须符合 parameters 约束。
3. 可选参数可省略；若包含，需符合类型和描述。
4. 时间参数的值必须在上述时间范围内。

## 输出格式（严格 JSON 数组）
```json
[
  {{"question": "用户问题1", "tool_call": {{"name": "工具名", "arguments": {{...}}}}}},
  {{"question": "用户问题2", "tool_call": {{"name": "工具名", "arguments": {{...}}}}}}
]
```

请直接输出 JSON 数组，不要其他说明。"""


TOOL_CHAIN_PROMPT = """你是一个束流分析领域的对话数据生成助手。请根据以下工具列表，生成 {x} 个用户问题，这些问题需要**依次调用多个工具**才能完成（工具链）。

## 可用工具
```json
{tools_def}
```

## 数据时间范围
- 开始: {time_start}
- 结束: {time_end}
所有时间参数必须使用该范围内的具体日期时间，格式 "YYYY-MM-DD HH:MM:SS"。禁止使用相对时间。

## 工具链示例
- 先 get_data_info 获取概览，再 query_beam_data 查具体数据
- 先 query_beam_data 查数据，再 detect_anomaly 检测异常
- 先 detect_anomaly 确认异常，再 diagnose_by_xxx 诊断原因

## 要求
1. 每个问题需对应一个工具调用序列（数组），按调用顺序排列。
2. 问题用自然语言表达，体现多步操作意图。
3. tool_call 为数组：`[{{"name": "...", "arguments": {{...}}}}, {{"name": "...", "arguments": {{...}}}}]`
4. 每个调用的 arguments 必须符合对应工具的 parameters。

## 输出格式（严格 JSON 数组）
```json
[
  {{"question": "用户问题1", "tool_call": [{{"name": "工具1", "arguments": {{...}}}}, {{"name": "工具2", "arguments": {{...}}}}]}},
  {{"question": "用户问题2", "tool_call": [{{"name": "工具A", "arguments": {{...}}}}, {{"name": "工具B", "arguments": {{...}}}}]}}
]
```

请直接输出 JSON 数组。"""


NO_TOOL_PROMPT = """你是一个束流分析领域的对话数据生成助手。请生成 {x} 个**不需要调用任何工具**的用户问题。

这类问题通常是：
- 领域概念解释（如「什么是束流？」「离子注入工艺是什么？」）
- 一般性知识问答（如「加速器有哪些应用？」）
- 无法通过现有数据/工具回答的问题

## 要求
1. 问题用自然语言表达，符合真实用户口吻。
2. 每个问题对应 tool_call 为 null（不调用工具）。
3. 问题应与束流、加速器、离子注入等领域相关。

## 输出格式（严格 JSON 数组）
```json
[
  {{"question": "用户问题1", "tool_call": null}},
  {{"question": "用户问题2", "tool_call": null}}
]
```

请直接输出 JSON 数组。"""


# ========== 模板回退（--no-llm 时使用）==========

def _build_single_tool_templates(time_start: str, time_end: str, x: int) -> List[dict]:
    """模板：为每个工具生成 x 个问题。"""
    base_date = time_start[:10] if len(time_start) >= 10 else "2025-08-01"
    samples = []

    samples.extend([
        {"question": f"查询{base_date}凌晨2点到3点的束流数据", "tool_call": {"name": "query_beam_data", "arguments": {"start_time": f"{base_date} 02:00:00", "end_time": f"{base_date} 03:00:00"}}},
        {"question": f"帮我看看{base_date}上午10点到11点之间的target和feature1数据", "tool_call": {"name": "query_beam_data", "arguments": {"start_time": f"{base_date} 10:00:00", "end_time": f"{base_date} 11:00:00", "columns": ["时间", "target", "feature1"]}}},
    ][:x])

    samples.extend([
        {"question": "数据集有哪些列？时间范围是多少？", "tool_call": {"name": "get_data_info", "arguments": {}}},
        {"question": "首次使用，先了解一下数据的基本信息", "tool_call": {"name": "get_data_info", "arguments": {"include_target_stats": True, "include_sample": True}}},
    ][:x])

    samples.extend([
        {"question": f"{base_date}凌晨2点到3点这段时间有异常吗？", "tool_call": {"name": "detect_anomaly", "arguments": {"start_time": f"{base_date} 02:00:00", "end_time": f"{base_date} 03:00:00"}}},
        {"question": f"检测{base_date}10点到11点是否存在异常", "tool_call": {"name": "detect_anomaly", "arguments": {"start_time": f"{base_date} 10:00:00", "end_time": f"{base_date} 11:00:00"}}},
    ][:x])

    samples.extend([
        {"question": f"用统计差异方法诊断{base_date}10点到11点的异常，正常时段取{base_date}08点到09点", "tool_call": {"name": "diagnose_by_statistical_difference", "arguments": {"anomaly_start": f"{base_date} 10:00:00", "anomaly_end": f"{base_date} 11:00:00", "normal_start": f"{base_date} 08:00:00", "normal_end": f"{base_date} 09:00:00", "top_k": 10}}},
        {"question": f"Z-score方法诊断异常时段{base_date}14:00-15:00，正常基准{base_date}12:00-13:00", "tool_call": {"name": "diagnose_by_statistical_difference", "arguments": {"anomaly_start": f"{base_date} 14:00:00", "anomaly_end": f"{base_date} 15:00:00", "normal_start": f"{base_date} 12:00:00", "normal_end": f"{base_date} 13:00:00"}}},
    ][:x])

    samples.extend([
        {"question": f"用PLS方法诊断{base_date}10点到11点的异常特征", "tool_call": {"name": "diagnose_by_pls", "arguments": {"anomaly_start": f"{base_date} 10:00:00", "anomaly_end": f"{base_date} 11:00:00", "top_k": 10}}},
        {"question": f"偏最小二乘模型分析{base_date}14:00-15:00的异常，返回前5个关键变量", "tool_call": {"name": "diagnose_by_pls", "arguments": {"anomaly_start": f"{base_date} 14:00:00", "anomaly_end": f"{base_date} 15:00:00", "top_k": 5}}},
    ][:x])

    samples.extend([
        {"question": f"用SHAP方法诊断{base_date}10点到11点的异常，用随机森林模型", "tool_call": {"name": "diagnose_by_shap", "arguments": {"anomaly_start": f"{base_date} 10:00:00", "anomaly_end": f"{base_date} 11:00:00", "model_name": "RF", "top_k": 10}}},
        {"question": f"XGBoost模型的SHAP解释，分析{base_date}14:00-15:00异常", "tool_call": {"name": "diagnose_by_shap", "arguments": {"anomaly_start": f"{base_date} 14:00:00", "anomaly_end": f"{base_date} 15:00:00", "model_name": "XGB"}}},
    ][:x])

    samples.extend([
        {"question": f"用自编码器诊断{base_date}10点到11点的异常特征", "tool_call": {"name": "diagnose_by_autoencoder", "arguments": {"anomaly_start": f"{base_date} 10:00:00", "anomaly_end": f"{base_date} 11:00:00", "top_k": 10}}},
        {"question": f"AutoEncoder分析{base_date}14:00-15:00各变量的重构误差", "tool_call": {"name": "diagnose_by_autoencoder", "arguments": {"anomaly_start": f"{base_date} 14:00:00", "anomaly_end": f"{base_date} 15:00:00"}}},
    ][:x])

    samples.extend([
        {"question": f"绘制{base_date}凌晨2点到3点的束流时序图", "tool_call": {"name": "plot_beam_data", "arguments": {"start_time": f"{base_date} 02:00:00", "end_time": f"{base_date} 03:00:00"}}},
        {"question": f"帮我画一下{base_date}10点到11点的束流曲线，叠加feature1和feature3", "tool_call": {"name": "plot_beam_data", "arguments": {"start_time": f"{base_date} 10:00:00", "end_time": f"{base_date} 11:00:00", "features": ["feature1", "feature3"]}}},
    ][:x])

    if "explain_diagnosis_features" in TOOL_FUNCTIONS:
        samples.extend([
            {"question": "解释一下诊断结果中的feature4、feature5、feature6的物理含义", "tool_call": {"name": "explain_diagnosis_features", "arguments": {"feature_names": ["feature4", "feature5", "feature6"]}}},
            {"question": "诊断出的feature3、feature4是什么？属于哪个子系统？", "tool_call": {"name": "explain_diagnosis_features", "arguments": {"feature_names": ["feature3", "feature4"]}}},
        ][:x])
    if "explain_variable_meaning" in TOOL_FUNCTIONS:
        samples.extend([
            {"question": "灯丝电源电流是什么？", "tool_call": {"name": "explain_variable_meaning", "arguments": {"query": "灯丝电源电流"}}},
            {"question": "加速电源电压是什么？有什么作用？", "tool_call": {"name": "explain_variable_meaning", "arguments": {"query": "加速电源电压"}}},
        ][:x])
    if "search_domain_knowledge" in TOOL_FUNCTIONS:
        samples.extend([
            {"question": "束流强度如何测量？", "tool_call": {"name": "search_domain_knowledge", "arguments": {"query": "束流强度如何测量"}}},
            {"question": "加速器的工作原理是什么？", "tool_call": {"name": "search_domain_knowledge", "arguments": {"query": "加速器的工作原理"}}},
        ][:x])

    return samples


def _build_tool_chain_templates(time_start: str, time_end: str, x: int) -> List[dict]:
    base_date = time_start[:10] if len(time_start) >= 10 else "2025-08-01"
    return [
        {
            "question": f"先获取数据概览，再查询{base_date}10点到11点的束流数据",
            "tool_call": [
                {"name": "get_data_info", "arguments": {}},
                {"name": "query_beam_data", "arguments": {"start_time": f"{base_date} 10:00:00", "end_time": f"{base_date} 11:00:00"}},
            ],
        },
        {
            "question": f"查询{base_date}14点到15点数据并检测是否有异常",
            "tool_call": [
                {"name": "query_beam_data", "arguments": {"start_time": f"{base_date} 14:00:00", "end_time": f"{base_date} 15:00:00"}},
                {"name": "detect_anomaly", "arguments": {"start_time": f"{base_date} 14:00:00", "end_time": f"{base_date} 15:00:00"}},
            ],
        },
    ][:x]


def _build_no_tool_templates(x: int) -> List[dict]:
    return [
        {"question": "什么是束流？", "tool_call": None},
        {"question": "离子注入工艺主要应用在哪些领域？", "tool_call": None},
    ][:x]


# ========== LLM 生成 ==========

def _get_single_tools_for_llm() -> List[dict]:
    """获取可用于 LLM 的单工具列表（跳过 RAG 若不可用）。"""
    result = []
    for t in TOOLS:
        if not isinstance(t, dict):
            continue
        fn = t.get("function", {})
        name = fn.get("name")
        if name and name in TOOL_FUNCTIONS:
            result.append(t)
    return result


def build_single_tool_questions_llm(
    time_start: str,
    time_end: str,
    x: int,
    client,
    model: str,
    delay: float,
) -> List[dict]:
    """用 LLM 为每个工具生成 x 个问题。"""
    tools = _get_single_tools_for_llm()
    all_samples = []
    for i, tool_def in enumerate(tqdm(tools, desc="单工具问题生成", unit="个")):
        if i > 0:
            time.sleep(delay)
        tool_json = json.dumps(tool_def, ensure_ascii=False, indent=2)
        prompt = SINGLE_TOOL_PROMPT.format(
            x=x,
            tool_def=tool_json,
            time_start=time_start,
            time_end=time_end,
        )
        try:
            samples = _call_llm_generate_questions(prompt, client, model)
            for s in samples:
                if isinstance(s.get("tool_call"), dict) and s.get("question"):
                    all_samples.append(s)
        except Exception as e:
            print(f"  工具 {tool_def.get('function', {}).get('name')} 生成失败: {e}，跳过")
    return all_samples


def build_tool_chain_questions_llm(
    time_start: str,
    time_end: str,
    x: int,
    client,
    model: str,
    delay: float,
) -> List[dict]:
    """用 LLM 生成工具链问题。"""
    tools_def = json.dumps(TOOLS, ensure_ascii=False, indent=2)
    prompt = TOOL_CHAIN_PROMPT.format(
        x=x,
        tools_def=tools_def,
        time_start=time_start,
        time_end=time_end,
    )
    time.sleep(delay)
    try:
        samples = _call_llm_generate_questions(prompt, client, model)
        result = []
        for s in samples:
            if isinstance(s.get("tool_call"), list) and s.get("question"):
                result.append(s)
        return result[:x]
    except Exception as e:
        print(f"工具链问题生成失败: {e}，使用模板")
        return _build_tool_chain_templates(time_start, time_end, x)


def build_no_tool_questions_llm(x: int, client, model: str, delay: float) -> List[dict]:
    """用 LLM 生成无工具问题。"""
    prompt = NO_TOOL_PROMPT.format(x=x)
    time.sleep(delay)
    try:
        samples = _call_llm_generate_questions(prompt, client, model)
        result = []
        for s in samples:
            if s.get("tool_call") is None and s.get("question"):
                result.append(s)
        return result[:x]
    except Exception as e:
        print(f"无工具问题生成失败: {e}，使用模板")
        return _build_no_tool_templates(x)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="阶段1：生成 question + tool_call")
    parser.add_argument("-o", "--output", default="data/train_gen/questions.jsonl", help="输出文件路径")
    parser.add_argument("-x", type=int, default=2, help="每类样本数量")
    parser.add_argument("--no-llm", action="store_true", help="不使用 LLM，使用模板生成")
    parser.add_argument("--delay", type=float, default=2.0, help="LLM 调用间隔（秒）")
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    time_start, time_end = get_time_range(project_root)
    print(f"时间范围: {time_start} ~ {time_end}")

    x = args.x
    records = []

    if args.no_llm:
        print("使用模板生成（--no-llm）")
        for s in _build_single_tool_templates(time_start, time_end, x):
            records.append({**s, "category": "single_tool"})
        for s in _build_tool_chain_templates(time_start, time_end, x):
            records.append({**s, "category": "tool_chain"})
        for s in _build_no_tool_templates(x):
            records.append({**s, "category": "no_tool"})
    else:
        try:
            from config.config import Config
            cfg = Config.get_api_config()
            if not cfg.get("api_key"):
                print("未配置 API_KEY，回退到模板")
                args.no_llm = True
                for s in _build_single_tool_templates(time_start, time_end, x):
                    records.append({**s, "category": "single_tool"})
                for s in _build_tool_chain_templates(time_start, time_end, x):
                    records.append({**s, "category": "tool_chain"})
                for s in _build_no_tool_templates(x):
                    records.append({**s, "category": "no_tool"})
            else:
                from openai import OpenAI
                client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])
                model = cfg.get("model", "Qwen/Qwen2.5-7B-Instruct")
                print(f"使用 LLM 生成: {model}")

                for s in build_single_tool_questions_llm(time_start, time_end, x, client, model, args.delay):
                    records.append({**s, "category": "single_tool"})
                for s in build_tool_chain_questions_llm(time_start, time_end, x, client, model, args.delay):
                    records.append({**s, "category": "tool_chain"})
                for s in build_no_tool_questions_llm(x, client, model, args.delay):
                    records.append({**s, "category": "no_tool"})
        except Exception as e:
            print(f"LLM 初始化失败: {e}，回退到模板")
            for s in _build_single_tool_templates(time_start, time_end, x):
                records.append({**s, "category": "single_tool"})
            for s in _build_tool_chain_templates(time_start, time_end, x):
                records.append({**s, "category": "tool_chain"})
            for s in _build_no_tool_templates(x):
                records.append({**s, "category": "no_tool"})

    output_path = args.output
    if not os.path.isabs(output_path):
        output_path = os.path.join(project_root, output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"已生成 {len(records)} 条问题，保存至 {output_path}")
    print(f"  单工具: {sum(1 for r in records if r['category'] == 'single_tool')}")
    print(f"  工具链: {sum(1 for r in records if r['category'] == 'tool_chain')}")
    print(f"  无工具: {sum(1 for r in records if r['category'] == 'no_tool')}")


if __name__ == "__main__":
    main()
