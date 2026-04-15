"""
OpenClaw 效率测试脚本 - 直接用 ModelScope API 调用指定模型
测试指标：prompt_tokens、completion_tokens、端到端响应时间
"""

import json
import time
import os
from datetime import datetime
from typing import Dict, Any, List

# 从 config 加载配置
import sys
sys.path.insert(0, r'D:\code\graduate\llm')
from config.config import Config

# 使用 openai 兼容 API
from openai import OpenAI

DELAY_BETWEEN_QUESTIONS = 3  # 每题之间的等待秒数
SINGLE_QUESTION_TIMEOUT = 180  # 单题最大执行秒数

# 目标模型
TARGET_MODEL = "Qwen/Qwen3-VL-30B-A3B-Instruct"


def get_client():
    """创建 API 客户端"""
    config = Config.get_api_config()
    return OpenAI(
        api_key=config['api_key'],
        base_url=config['base_url']
    )


def load_test_questions(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_single_test(client: OpenAI, question_item: Dict, total: int) -> Dict[str, Any]:
    """运行单条测试，返回结果"""
    qid = question_item["id"]
    question = question_item["question"]
    category = question_item["category"]
    tool_name = question_item.get("tool_name")

    print(f"\n{'='*60}")
    print(f"[{qid}/{total}] ({category}) {question}")
    print(f"{'='*60}")

    t_start = time.time()
    
    try:
        response = client.chat.completions.create(
            model=TARGET_MODEL,
            messages=[
                {"role": "user", "content": question}
            ],
            timeout=SINGLE_QUESTION_TIMEOUT
        )
        elapsed_ms = (time.time() - t_start) * 1000
        
        success = True
        response_text = response.choices[0].message.content if response.choices else ""
        
        # 获取 token 统计
        prompt_tokens = response.usage.prompt_tokens if response.usage else 0
        completion_tokens = response.usage.completion_tokens if response.usage else 0
        total_tokens = response.usage.total_tokens if response.usage else (prompt_tokens + completion_tokens)
        
        # 计算每秒 tokens
        tokens_per_sec = (total_tokens / (elapsed_ms / 1000)) if elapsed_ms > 0 else 0
        
    except Exception as e:
        elapsed_ms = (time.time() - t_start) * 1000
        success = False
        response_text = ""
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        error_msg = str(e)
        tokens_per_sec = 0
    
    record = {
        "id": qid,
        "question": question,
        "category": category,
        "expected_tool_name": tool_name,
        "success": success,
        "elapsed_ms": round(elapsed_ms, 1),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "tokens_per_sec": round(tokens_per_sec, 2),
        "response_text": response_text[:500] if response_text else "",  # 限制长度
    }
    
    if not success:
        record["error"] = error_msg
    
    status = "OK" if success else "FAIL"
    if success:
        print(f"  [{status}] 耗时: {elapsed_ms:.0f}ms | tokens: {prompt_tokens}+{completion_tokens}={total_tokens} | 速度: {tokens_per_sec:.1f} tok/s")
    else:
        print(f"  [{status}] 耗时: {elapsed_ms:.0f}ms | 错误：{error_msg}")

    return record


def compute_summary(results: List[Dict]) -> Dict:
    """从全部结果计算汇总统计"""
    success_results = [r for r in results if r["success"]]
    n = len(success_results)
    if n == 0:
        return {"error": "no successful results"}

    def avg(key):
        return round(sum(r[key] for r in success_results) / n, 2)

    def total(key):
        return sum(r[key] for r in success_results)

    by_category = {}
    for r in success_results:
        cat = r["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(r)

    category_stats = {}
    for cat, cat_results in by_category.items():
        cn = len(cat_results)
        category_stats[cat] = {
            "count": cn,
            "avg_elapsed_ms": round(sum(r["elapsed_ms"] for r in cat_results) / cn, 1),
            "avg_prompt_tokens": round(sum(r["prompt_tokens"] for r in cat_results) / cn, 1),
            "avg_completion_tokens": round(sum(r["completion_tokens"] for r in cat_results) / cn, 1),
            "avg_total_tokens": round(sum(r["total_tokens"] for r in cat_results) / cn, 1),
            "avg_tokens_per_sec": round(sum(r["tokens_per_sec"] for r in cat_results) / cn, 2),
        }

    return {
        "total_questions": len(results),
        "successful": n,
        "failed": len(results) - n,
        "overall": {
            "avg_elapsed_ms": avg("elapsed_ms"),
            "avg_prompt_tokens": avg("prompt_tokens"),
            "avg_completion_tokens": avg("completion_tokens"),
            "avg_total_tokens": avg("total_tokens"),
            "avg_tokens_per_sec": avg("tokens_per_sec"),
            "total_prompt_tokens": total("prompt_tokens"),
            "total_completion_tokens": total("completion_tokens"),
            "total_tokens": total("total_tokens"),
            "total_elapsed_sec": round(total("elapsed_ms") / 1000, 2),
        },
        "by_category": category_stats,
    }


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    questions_path = os.path.join(script_dir, "data", "efficiency_test_questions.json")
    output_dir = os.path.join(script_dir, "openclaw")
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = os.path.join(output_dir, f"openclaw_efficiency_results_{timestamp}.json")

    questions = load_test_questions(questions_path)
    print(f"加载 {len(questions)} 个测试问题")
    print(f"目标模型：{TARGET_MODEL}")
    print(f"API 地址：{Config.BASE_URL}")

    client = get_client()

    total = len(questions)
    results = []
    for i, item in enumerate(questions):
        record = run_single_test(client, item, total)
        results.append(record)

        if i < total - 1:
            print(f"  等待 {DELAY_BETWEEN_QUESTIONS}s 后继续...")
            time.sleep(DELAY_BETWEEN_QUESTIONS)

    summary = compute_summary(results)

    output = {
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "model": TARGET_MODEL,
            "question_count": len(questions),
            "questions_file": "efficiency_test_questions.json",
            "base_url": Config.BASE_URL,
        },
        "summary": summary,
        "results": results,
    }

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print("测试完成！")
    print(f"{'='*60}")
    print(f"结果文件：{results_path}")
    print(f"总问题数：{summary['total_questions']}  成功：{summary['successful']}  失败：{summary['failed']}")
    if "overall" in summary:
        o = summary["overall"]
        print(f"平均响应时间：{o['avg_elapsed_ms']:.0f}ms ({o['avg_elapsed_ms']/1000:.2f}s)")
        print(f"平均 tokens: prompt={o['avg_prompt_tokens']:.0f}  completion={o['avg_completion_tokens']:.0f}  total={o['avg_total_tokens']:.0f}")
        print(f"平均速度：{o['avg_tokens_per_sec']:.1f} tokens/s")
        print(f"总 tokens: {o['total_tokens']}")
        print(f"总耗时：{o['total_elapsed_sec']:.1f}s")
        print(f"\n按类别统计:")
        for cat, cs in summary["by_category"].items():
            print(f"  {cat} ({cs['count']}条): 平均耗时={cs['avg_elapsed_ms']:.0f}ms  平均 tokens={cs['avg_total_tokens']:.0f}  平均速度={cs['avg_tokens_per_sec']:.1f} tok/s")


if __name__ == "__main__":
    main()
