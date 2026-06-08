"""
OpenClaw Skills 效率测试脚本
直接调用工具函数，记录响应时间和 token 消耗
"""
import json
import time
import os
from datetime import datetime
from typing import Dict, Any, List

# 添加项目路径
import sys
sys.path.insert(0, r'D:\code\graduate\llm')

from tools.data_query import query_beam_data, get_data_info
from tools.anomaly_detection import detect_anomaly
from tools.anomaly_diagnose import (
    diagnose_by_statistical_difference,
    diagnose_by_pls,
    diagnose_by_shap,
    diagnose_by_autoencoder
)
from tools.visualization import plot_beam_data

# RAG 工具尝试导入
try:
    from knowledge.rag_tool import (
        explain_diagnosis_features,
        explain_variable_meaning,
        search_domain_knowledge
    )
    RAG_AVAILABLE = True
except ImportError as e:
    RAG_AVAILABLE = False
    print(f"[警告] RAG 知识库模块不可用 ({e})")
    # 定义空函数占位
    def explain_diagnosis_features(*args, **kwargs): return {"success": False, "error": "RAG not available"}
    def explain_variable_meaning(*args, **kwargs): return {"success": False, "error": "RAG not available"}
    def search_domain_knowledge(*args, **kwargs): return {"success": False, "error": "RAG not available"}

# 工具函数映射
TOOL_FUNCTIONS = {
    "query_beam_data": query_beam_data,
    "get_data_info": get_data_info,
    "detect_anomaly": detect_anomaly,
    "diagnose_by_statistical_difference": diagnose_by_statistical_difference,
    "diagnose_by_pls": diagnose_by_pls,
    "diagnose_by_shap": diagnose_by_shap,
    "diagnose_by_autoencoder": diagnose_by_autoencoder,
    "plot_beam_data": plot_beam_data,
    "explain_diagnosis_features": explain_diagnosis_features,
    "explain_variable_meaning": explain_variable_meaning,
    "search_domain_knowledge": search_domain_knowledge,
}

SINGLE_QUESTION_TIMEOUT = 180


def load_test_questions(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def execute_single_tool(tool_name: str, args: Dict) -> Dict[str, Any]:
    """执行单个工具调用"""
    if tool_name not in TOOL_FUNCTIONS:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}
    
    try:
        func = TOOL_FUNCTIONS[tool_name]
        result = func(**args)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_single_test(question_item: Dict, total: int) -> Dict[str, Any]:
    """运行单条测试"""
    qid = question_item["id"]
    question = question_item["question"]
    category = question_item["category"]
    expected_tool = question_item.get("expected_tool_call")
    
    print(f"\n{'='*60}")
    print(f"[{qid}/{total}] ({category}) {question}")
    print('='*60)
    
    t_start = time.time()
    success = True
    error_msg = ""
    result_data = {}
    
    if expected_tool is None:
        # no_tool 类别 - 应该拒答，这里记录为成功但不调工具
        elapsed_ms = (time.time() - t_start) * 1000
        success = True
        result_data = {"no_tool_called": True}
        print(f"  [OK] 无需调用工具")
        
    elif isinstance(expected_tool, dict):
        # 单个工具调用
        tool_name = expected_tool["name"]
        args = expected_tool.get("arguments", {})
        
        result_data = execute_single_tool(tool_name, args)
        elapsed_ms = (time.time() - t_start) * 1000
        
        if result_data.get("success", False):
            print(f"  [OK] 工具 {tool_name} 调用成功，耗时 {elapsed_ms:.0f}ms")
        else:
            success = False
            error_msg = result_data.get("error", "Unknown error")
            print(f"  [FAIL] 工具调用失败：{error_msg}")
            
    elif isinstance(expected_tool, list):
        # 多工具链调用
        for i, tool_call in enumerate(expected_tool):
            tool_name = tool_call["name"]
            args = tool_call.get("arguments", {})
            
            sub_result = execute_single_tool(tool_name, args)
            if not sub_result.get("success", False):
                success = False
                error_msg = f"Tool {i+1} ({tool_name}) failed: {sub_result.get('error', 'Unknown error')}"
                print(f"  [FAIL] 工具链步骤 {i+1}: {tool_name} 失败 - {error_msg}")
                break
        
        if success:
            elapsed_ms = (time.time() - t_start) * 1000
            print(f"  [OK] 工具链全部完成，耗时 {elapsed_ms:.0f}ms")
        else:
            elapsed_ms = (time.time() - t_start) * 1000
    
    # token 统计 - 由于是直接调用 Python 函数，无法获取实际 token 消耗
    # 这里设置为 0，或者可以根据响应大小估算
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    
    record = {
        "id": qid,
        "question": question,
        "category": category,
        "expected_tool_name": question_item.get("tool_name"),
        "success": success,
        "elapsed_ms": round(elapsed_ms, 1),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "tokens_per_sec": 0,  # 无法计算
        "response_summary": str(result_data)[:200] if result_data else "",
    }
    
    if not success:
        record["error"] = error_msg
    
    return record


def compute_summary(results: List[Dict]) -> Dict:
    """计算汇总统计"""
    success_results = [r for r in results if r["success"]]
    n = len(success_results)
    
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
            "min_elapsed_ms": round(min(r["elapsed_ms"] for r in cat_results), 1),
            "max_elapsed_ms": round(max(r["elapsed_ms"] for r in cat_results), 1),
        }
    
    overall = {
        "avg_elapsed_ms": round(sum(r["elapsed_ms"] for r in success_results) / n, 1) if n > 0 else 0,
        "total_elapsed_sec": round(sum(r["elapsed_ms"] for r in success_results) / 1000, 2),
    }
    
    return {
        "total_questions": len(results),
        "successful": n,
        "failed": len(results) - n,
        "overall": overall,
        "by_category": category_stats,
    }


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # D:\code\graduate\llm
    
    # 切换到项目根目录，确保相对路径正确
    os.chdir(project_root)
    
    questions_path = os.path.join(script_dir, "data", "efficiency_test_questions.json")
    output_dir = os.path.join(script_dir, "openclaw")
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = os.path.join(output_dir, f"skills_direct_efficiency_{timestamp}.json")
    
    questions = load_test_questions(questions_path)
    print(f"加载 {len(questions)} 个测试问题")
    print(f"测试模式：直接调用 Python 工具函数（非 LLM）")
    print(f"输出文件：{results_path}")
    
    total = len(questions)
    results = []
    
    for i, item in enumerate(questions):
        record = run_single_test(item, total)
        results.append(record)
    
    summary = compute_summary(results)
    
    output = {
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "model": "Direct Tool Call (Python)",
            "question_count": len(questions),
            "questions_file": "efficiency_test_questions.json",
            "test_mode": "direct_tool_execution",
        },
        "summary": summary,
        "results": results,
    }
    
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print("测试完成！")
    print('='*60)
    print(f"结果文件：{results_path}")
    print(f"总问题数：{summary['total_questions']}  成功：{summary['successful']}  失败：{summary['failed']}")
    
    if "overall" in summary:
        o = summary["overall"]
        print(f"平均响应时间：{o['avg_elapsed_ms']:.0f}ms ({o['avg_elapsed_ms']/1000:.2f}s)")
        print(f"总耗时：{o['total_elapsed_sec']:.1f}s")
        print(f"\n按类别统计:")
        for cat, cs in summary["by_category"].items():
            print(f"  {cat} ({cs['count']}条): 平均={cs['avg_elapsed_ms']:.0f}ms  范围:{cs['min_elapsed_ms']:.0f}~{cs['max_elapsed_ms']:.0f}ms")


if __name__ == "__main__":
    main()
