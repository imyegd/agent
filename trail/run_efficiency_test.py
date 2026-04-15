"""
系统效率测试脚本
测试指标：prompt_tokens、completion_tokens、端到端响应时间、工具调用情况
"""

import matplotlib
matplotlib.use('Agg')

import json
import time
import os
import sys
import signal
import threading
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.llm_agent import BeamDataAgent
from config import Config

DELAY_BETWEEN_QUESTIONS = 3          # 每题之间的等待秒数
SINGLE_QUESTION_TIMEOUT = 120        # 单题最大执行秒数


class EfficiencyTestAgent(BeamDataAgent):
    """在 BeamDataAgent 基础上添加 token 计数功能"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._token_stats = self._empty_token_stats()

    @staticmethod
    def _empty_token_stats():
        return {
            "llm_call_count": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "per_call": [],
        }

    def reset_token_stats(self):
        self._token_stats = self._empty_token_stats()

    def get_token_stats(self):
        return dict(self._token_stats)

    def _call_llm(self, messages, tools=None):
        response = super()._call_llm(messages, tools)

        usage = getattr(response, "usage", None)
        if usage:
            prompt_t = getattr(usage, "prompt_tokens", 0) or 0
            completion_t = getattr(usage, "completion_tokens", 0) or 0
            total_t = getattr(usage, "total_tokens", 0) or (prompt_t + completion_t)

            self._token_stats["llm_call_count"] += 1
            self._token_stats["prompt_tokens"] += prompt_t
            self._token_stats["completion_tokens"] += completion_t
            self._token_stats["total_tokens"] += total_t
            self._token_stats["per_call"].append({
                "call_index": self._token_stats["llm_call_count"],
                "prompt_tokens": prompt_t,
                "completion_tokens": completion_t,
                "total_tokens": total_t,
            })

        return response


def load_test_questions(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _run_chat_with_timeout(agent, question, timeout):
    """在子线程中执行 agent.chat，主线程等待 timeout 秒"""
    result_holder = {"result": None, "error": None}

    def _target():
        try:
            result_holder["result"] = agent.chat(question)
        except Exception as e:
            result_holder["error"] = str(e)

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join(timeout=timeout)

    if t.is_alive():
        return None, f"超时（>{timeout}s）"
    return result_holder["result"], result_holder["error"]


def run_single_test(agent: EfficiencyTestAgent, question_item: Dict, total: int) -> Dict[str, Any]:
    """运行单条测试，返回结果"""
    qid = question_item["id"]
    question = question_item["question"]
    category = question_item["category"]
    tool_name = question_item.get("tool_name")

    print(f"\n{'='*60}")
    print(f"[{qid}/{total}] ({category}) {question}")
    print(f"{'='*60}")

    agent.reset_conversation()
    agent.reset_token_stats()

    t_start = time.time()
    result, error = _run_chat_with_timeout(agent, question, SINGLE_QUESTION_TIMEOUT)
    elapsed_ms = (time.time() - t_start) * 1000

    if result is not None:
        success = True
        response_text = result.get("response", "")
    else:
        success = False
        response_text = ""
        if error is None:
            error = "未知错误"

    token_stats = agent.get_token_stats()

    tool_calls_made = []
    for msg in agent.conversation_history:
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                func = tc.get("function", {})
                try:
                    args = json.loads(func["arguments"]) if isinstance(func.get("arguments"), str) else func.get("arguments", {})
                except (json.JSONDecodeError, TypeError):
                    args = {}
                tool_calls_made.append({"name": func.get("name", ""), "arguments": args})

    record = {
        "id": qid,
        "question": question,
        "category": category,
        "expected_tool_name": tool_name,
        "success": success,
        "error": error,
        "elapsed_ms": round(elapsed_ms, 1),
        "prompt_tokens": token_stats["prompt_tokens"],
        "completion_tokens": token_stats["completion_tokens"],
        "total_tokens": token_stats["total_tokens"],
        "llm_call_count": token_stats["llm_call_count"],
        "token_per_call": token_stats["per_call"],
        "tool_calls_made": tool_calls_made,
        "tool_call_count": len(tool_calls_made),
        "response_text": response_text,
    }

    status = "OK" if success else "FAIL"
    print(f"  [{status}] 耗时: {elapsed_ms:.0f}ms | tokens: {token_stats['prompt_tokens']}+{token_stats['completion_tokens']}={token_stats['total_tokens']} | LLM调用: {token_stats['llm_call_count']}次 | 工具调用: {len(tool_calls_made)}次")
    if error:
        print(f"  错误: {error}")

    return record


def compute_summary(results: List[Dict]) -> Dict:
    """从全部结果计算汇总统计"""
    success_results = [r for r in results if r["success"]]
    n = len(success_results)
    if n == 0:
        return {"error": "no successful results"}

    def avg(key):
        return round(sum(r[key] for r in success_results) / n, 2)

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
            "avg_llm_calls": round(sum(r["llm_call_count"] for r in cat_results) / cn, 2),
            "avg_tool_calls": round(sum(r["tool_call_count"] for r in cat_results) / cn, 2),
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
            "avg_llm_calls": avg("llm_call_count"),
            "avg_tool_calls": avg("tool_call_count"),
            "total_prompt_tokens": sum(r["prompt_tokens"] for r in success_results),
            "total_completion_tokens": sum(r["completion_tokens"] for r in success_results),
            "total_tokens": sum(r["total_tokens"] for r in success_results),
        },
        "by_category": category_stats,
    }


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    questions_path = os.path.join(script_dir, "data", "efficiency_test_questions.json")
    output_dir = os.path.join(script_dir, "data")
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = os.path.join(output_dir, f"efficiency_results_{timestamp}.json")

    questions = load_test_questions(questions_path)
    print(f"加载 {len(questions)} 个测试问题")

    config = Config.get_api_config()
    agent = EfficiencyTestAgent(
        api_key=config["api_key"],
        base_url=config["base_url"],
        model=config["model"],
    )
    print(f"模型: {config['model']}")

    total = len(questions)
    results = []
    for i, item in enumerate(questions):
        record = run_single_test(agent, item, total)
        results.append(record)

        if i < total - 1:
            print(f"  等待 {DELAY_BETWEEN_QUESTIONS}s 后继续...")
            time.sleep(DELAY_BETWEEN_QUESTIONS)

    summary = compute_summary(results)

    output = {
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "model": config["model"],
            "question_count": len(questions),
            "questions_file": "efficiency_test_questions.json",
        },
        "summary": summary,
        "results": results,
    }

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print("测试完成！")
    print(f"{'='*60}")
    print(f"结果文件: {results_path}")
    print(f"总问题数: {summary['total_questions']}  成功: {summary['successful']}  失败: {summary['failed']}")
    if "overall" in summary:
        o = summary["overall"]
        print(f"平均响应时间: {o['avg_elapsed_ms']:.0f}ms")
        print(f"平均 tokens: prompt={o['avg_prompt_tokens']:.0f}  completion={o['avg_completion_tokens']:.0f}  total={o['avg_total_tokens']:.0f}")
        print(f"总 tokens: {o['total_tokens']}")
        print(f"\n按类别统计:")
        for cat, cs in summary["by_category"].items():
            print(f"  {cat} ({cs['count']}条): 平均耗时={cs['avg_elapsed_ms']:.0f}ms  平均tokens={cs['avg_total_tokens']:.0f}  平均LLM调用={cs['avg_llm_calls']}次  平均工具调用={cs['avg_tool_calls']}次")


if __name__ == "__main__":
    main()
