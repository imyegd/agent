"""
数据查询工具调用测试
验证 query_beam_data / get_data_info 是否可正常通过 TOOL_FUNCTIONS 调用。
"""

import os
import sys
from datetime import timedelta

import pandas as pd

# 添加项目根路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools import TOOL_FUNCTIONS


def _print_title(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def _get_time_windows():
    """从数据集信息动态构造测试时间窗口。"""
    info = TOOL_FUNCTIONS["get_data_info"](
        include_target_stats=False,
        include_sample=False
    )
    if not info.get("success"):
        raise RuntimeError(f"无法获取数据集时间范围: {info}")

    tr = info["data_info"]["time_range"]
    start = pd.to_datetime(tr["start"])
    end = pd.to_datetime(tr["end"])

    # 正常窗口：起始 10 分钟
    normal_start = start
    normal_end = min(start + timedelta(minutes=10), end)

    # 异常窗口：末尾 10 分钟
    anomaly_end = end
    anomaly_start = max(start, end - timedelta(minutes=10))

    # SHAP 专用短窗口（减少耗时）
    shap_end = end
    shap_start = max(start, end - timedelta(minutes=2))

    return {
        "start": start,
        "end": end,
        "normal_start": normal_start,
        "normal_end": normal_end,
        "anomaly_start": anomaly_start,
        "anomaly_end": anomaly_end,
        "shap_start": shap_start,
        "shap_end": shap_end
    }


def test_data_query_tools():
    _print_title("测试数据查询类工具")

    if "get_data_info" not in TOOL_FUNCTIONS or "query_beam_data" not in TOOL_FUNCTIONS:
        raise RuntimeError("工具注册失败：未找到 get_data_info 或 query_beam_data")

    # 示例 1：获取数据集信息
    _print_title("示例 1：调用 get_data_info")
    info = TOOL_FUNCTIONS["get_data_info"](
        include_target_stats=True,
        include_sample=True,
        sample_size=2
    )
    print(f"success: {info.get('success')}")
    print(f"tool: {info.get('tool')}")
    print(f"message: {info.get('message')}")
    print(f"time_range: {info.get('data_info', {}).get('time_range')}")
    assert info.get("success") is True
    assert info.get("tool") == "get_data_info"

    time_range = info["data_info"]["time_range"]
    start = pd.to_datetime(time_range["start"])
    end = pd.to_datetime(time_range["end"])

    # 示例 2：全范围查询（限制返回条数）
    _print_title("示例 2：调用 query_beam_data（全范围 + 指定列）")
    result_full = TOOL_FUNCTIONS["query_beam_data"](
        start_time=start.strftime("%Y-%m-%d %H:%M:%S"),
        end_time=end.strftime("%Y-%m-%d %H:%M:%S"),
        columns=["时间", "target", "feature1"],
        limit=5,
        include_statistics=True
    )
    print(f"success: {result_full.get('success')}")
    print(f"matched_records: {result_full.get('summary', {}).get('matched_records')}")
    print(f"returned_records: {result_full.get('summary', {}).get('returned_records')}")
    print(f"sample_data_count: {len(result_full.get('data', []))}")
    assert result_full.get("success") is True
    assert result_full.get("tool") == "query_beam_data"
    assert "summary" in result_full

    # 示例 3：局部时间窗口查询
    _print_title("示例 3：调用 query_beam_data（局部时间窗口）")
    mid_start = start
    mid_end = min(start + timedelta(minutes=30), end)
    result_window = TOOL_FUNCTIONS["query_beam_data"](
        start_time=mid_start.strftime("%Y-%m-%d %H:%M:%S"),
        end_time=mid_end.strftime("%Y-%m-%d %H:%M:%S"),
        limit=3,
        include_statistics=False
    )
    print(f"success: {result_window.get('success')}")
    print(f"message: {result_window.get('message')}")
    print(f"actual_result_time_range: {result_window.get('summary', {}).get('actual_result_time_range')}")
    assert result_window.get("success") is True

    # 示例 4：异常参数测试（非法 limit）
    _print_title("示例 4：非法参数验证（limit=0）")
    result_invalid = TOOL_FUNCTIONS["query_beam_data"](
        start_time=start.strftime("%Y-%m-%d %H:%M:%S"),
        end_time=end.strftime("%Y-%m-%d %H:%M:%S"),
        limit=0
    )
    print(f"success: {result_invalid.get('success')}")
    print(f"error: {result_invalid.get('error')}")
    assert result_invalid.get("success") is False

    _print_title("测试完成：数据查询工具可正常调用")


def test_anomaly_diagnosis_tools():
    _print_title("测试异常检测与诊断类工具")

    required_tools = [
        "detect_anomaly",
        "diagnose_by_statistical_difference",
        "diagnose_by_pls",
        "diagnose_by_shap",
        "diagnose_by_autoencoder",
    ]
    missing = [name for name in required_tools if name not in TOOL_FUNCTIONS]
    if missing:
        raise RuntimeError(f"工具注册缺失: {missing}")

    w = _get_time_windows()
    anomaly_start = w["anomaly_start"].strftime("%Y-%m-%d %H:%M:%S")
    anomaly_end = w["anomaly_end"].strftime("%Y-%m-%d %H:%M:%S")
    normal_start = w["normal_start"].strftime("%Y-%m-%d %H:%M:%S")
    normal_end = w["normal_end"].strftime("%Y-%m-%d %H:%M:%S")
    shap_start = w["shap_start"].strftime("%Y-%m-%d %H:%M:%S")
    shap_end = w["shap_end"].strftime("%Y-%m-%d %H:%M:%S")

    _print_title("示例 5：detect_anomaly")
    detect_res = TOOL_FUNCTIONS["detect_anomaly"](
        start_time=anomaly_start,
        end_time=anomaly_end
    )
    print(f"success: {detect_res.get('success')}")
    print(f"is_anomaly: {detect_res.get('is_anomaly')}")
    print(f"anomaly_ratio: {detect_res.get('anomaly_ratio')}")
    assert "success" in detect_res

    _print_title("示例 6：diagnose_by_statistical_difference")
    stat_res = TOOL_FUNCTIONS["diagnose_by_statistical_difference"](
        anomaly_start=anomaly_start,
        anomaly_end=anomaly_end,
        normal_start=normal_start,
        normal_end=normal_end,
        top_k=5
    )
    print(f"method: {stat_res.get('method')}")
    print(f"top_features_count: {len(stat_res.get('top_features', []))}")
    assert stat_res.get("method") == "statistical_difference"

    _print_title("示例 7：diagnose_by_pls")
    pls_res = TOOL_FUNCTIONS["diagnose_by_pls"](
        anomaly_start=anomaly_start,
        anomaly_end=anomaly_end,
        top_k=5
    )
    print(f"method: {pls_res.get('method')}")
    print(f"top_features_count: {len(pls_res.get('top_features', []))}")
    assert pls_res.get("method") == "pls"

    _print_title("示例 8：diagnose_by_shap（短时间窗口，降低耗时）")
    shap_res = TOOL_FUNCTIONS["diagnose_by_shap"](
        anomaly_start=shap_start,
        anomaly_end=shap_end,
        model_name="RF",
        top_k=3
    )
    print(f"method: {shap_res.get('method')}")
    print(f"model: {shap_res.get('model')}")
    print(f"top_features_count: {len(shap_res.get('top_features', []))}")
    assert shap_res.get("method") == "shap"

    _print_title("示例 9：diagnose_by_autoencoder")
    ae_res = TOOL_FUNCTIONS["diagnose_by_autoencoder"](
        anomaly_start=anomaly_start,
        anomaly_end=anomaly_end,
        top_k=5
    )
    print(f"success: {ae_res.get('success', True)}")
    print(f"method: {ae_res.get('method')}")
    print(f"top_features_count: {len(ae_res.get('top_features', []))}")
    if ae_res.get("success") is False:
        print(f"autoencoder_error: {ae_res.get('error')}")
    else:
        assert ae_res.get("method") == "autoencoder"

    _print_title("测试完成：异常检测与诊断工具可调用")


def test_rag_tools():
    _print_title("测试 RAG 知识检索类工具")

    required_tools = [
        "explain_diagnosis_features",
        "explain_variable_meaning",
        "search_domain_knowledge"
    ]
    missing = [name for name in required_tools if name not in TOOL_FUNCTIONS]
    if missing:
        raise RuntimeError(f"RAG 工具注册缺失: {missing}")

    _print_title("示例 10：explain_diagnosis_features（承接诊断结果）")
    diag_res = TOOL_FUNCTIONS["explain_diagnosis_features"](
        feature_names=["feature4", "feature5", "feature6"],
        top_k=3
    )
    print(f"success: {diag_res.get('success')}")
    print(f"message: {diag_res.get('message')}")
    print(f"found_count: {diag_res.get('summary', {}).get('found_count')}")
    print(f"not_found_count: {diag_res.get('summary', {}).get('not_found_count')}")
    if diag_res.get("success"):
        results = diag_res.get("results", [])
        if results:
            print(f"第一个特征: {results[0].get('variable_name')}")
            print(f"  类型: {results[0].get('type')}")
            print(f"  所属系统: {results[0].get('parent_system')}")
    else:
        print(f"error: {diag_res.get('error')}")

    _print_title("示例 11：explain_variable_meaning（变量含义查询 - featureN）")
    var_res1 = TOOL_FUNCTIONS["explain_variable_meaning"](
        query="feature6",
        top_k=3
    )
    print(f"success: {var_res1.get('success')}")
    print(f"message: {var_res1.get('message')}")
    print(f"matched_count: {var_res1.get('summary', {}).get('matched_count')}")
    if var_res1.get("success") and var_res1.get("results"):
        first_match = var_res1["results"][0]
        print(f"变量名: {first_match.get('variable_name')}")
        print(f"匹配类型: {first_match.get('match_type')}")
    else:
        print(f"error: {var_res1.get('error')}")

    _print_title("示例 12：explain_variable_meaning（变量含义查询 - 中文名）")
    var_res2 = TOOL_FUNCTIONS["explain_variable_meaning"](
        query="灯丝电源电流",
        top_k=3
    )
    print(f"success: {var_res2.get('success')}")
    print(f"message: {var_res2.get('message')}")
    print(f"matched_count: {var_res2.get('summary', {}).get('matched_count')}")

    _print_title("示例 13：search_domain_knowledge（常规 RAG）")
    rag_res = TOOL_FUNCTIONS["search_domain_knowledge"](
        query="束流强度如何测量",
        top_k=3
    )
    print(f"success: {rag_res.get('success')}")
    print(f"message: {rag_res.get('message')}")
    if rag_res.get("success"):
        print(f"retrieved_count: {rag_res.get('summary', {}).get('retrieved_count')}")
        results = rag_res.get("results", [])
        if results:
            print(f"第一条结果摘要: {results[0].get('content')[:80]}...")
    else:
        print(f"error: {rag_res.get('error')}")

    _print_title("测试完成：RAG 工具可调用")


if __name__ == "__main__":
    test_data_query_tools()
    test_anomaly_diagnosis_tools()
    test_rag_tools()
