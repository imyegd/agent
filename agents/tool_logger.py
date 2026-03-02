"""
工具调用日志模块
每次 LLM 调用工具时，记录调用信息到 logs/ 目录下，按天分文件。

日志格式：JSON Lines，每次调用一行。

日志字段：
  timestamp   - 调用时刻（ISO 格式）
  session_id  - 会话 ID（每个 Agent 实例唯一）
  call_index  - 本会话第几次工具调用
  tool        - 工具函数名
  args        - 入参（完整记录）
  success     - 是否执行成功
  duration_ms - 执行耗时（毫秒）
  summary     - 结果摘要（关键字段，非全量输出）
  error       - 失败时的错误信息
"""

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional


_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")


def _ensure_log_dir():
    os.makedirs(_LOG_DIR, exist_ok=True)


def _log_path() -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(_LOG_DIR, f"tool_calls_{today}.jsonl")


def extract_tool_summary(tool_name: str, result: Dict[str, Any]) -> str:
    """
    从工具返回结果中提取关键摘要（公开函数，供 agent 使用）。
    """
    if not isinstance(result, dict):
        return str(result)[:200]

    if not result.get("success", True):
        return f"失败: {result.get('message') or result.get('error', '未知错误')}"

    try:
        if tool_name == "query_beam_data":
            s = result.get("summary", {})
            return (f"匹配 {s.get('matched_records', '?')} 条，"
                    f"返回 {s.get('returned_records', '?')} 条")

        elif tool_name == "get_data_info":
            info = result.get("data_info", {})
            tr = info.get("time_range", {})
            return (f"共 {info.get('total_records', '?')} 条，"
                    f"时间范围 {tr.get('start', '?')} ~ {tr.get('end', '?')}")

        elif tool_name == "detect_anomaly":
            return (f"is_anomaly={result.get('is_anomaly')}, "
                    f"anomaly_ratio={result.get('anomaly_ratio', 0):.2%}")

        elif tool_name in ("diagnose_by_statistical_difference",
                           "diagnose_by_pls",
                           "diagnose_by_shap",
                           "diagnose_by_autoencoder"):
            features = result.get("top_features", [])
            top3 = [f.get("feature", "?") for f in features[:3]]
            return f"top features: {', '.join(top3)}（共 {len(features)} 个）"

        elif tool_name == "explain_diagnosis_features":
            s = result.get("summary", {})
            return (f"找到 {s.get('found_count', '?')} 个，"
                    f"未找到 {s.get('not_found_count', '?')} 个")

        elif tool_name == "explain_variable_meaning":
            s = result.get("summary", {})
            return f"匹配 {s.get('matched_count', '?')} 个变量"

        elif tool_name == "search_domain_knowledge":
            s = result.get("summary", {})
            return f"检索到 {s.get('retrieved_count', '?')} 条知识"

        elif tool_name == "plot_beam_data":
            stats = result.get("stats", {})
            count = stats.get("count", "?")
            ratio = stats.get("anomaly_ratio")
            base = f"已绘制 {count} 条数据"
            if ratio is not None:
                base += f"，异常占比 {ratio:.1%}"
            return base

        else:
            return result.get("message", "执行成功")

    except Exception:
        return "摘要提取失败"


class ToolCallLogger:
    """
    工具调用日志记录器。
    每个 Agent 实例持有一个，共享 session_id 和调用计数。
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or uuid.uuid4().hex[:8]
        self._call_index = 0
        _ensure_log_dir()

    def log(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Optional[Dict[str, Any]],
        duration_ms: float,
        error: Optional[str] = None
    ):
        self._call_index += 1
        success = error is None and (result is None or result.get("success", True))

        entry = {
            "timestamp": datetime.now().isoformat(timespec="milliseconds"),
            "session_id": self.session_id,
            "call_index": self._call_index,
            "tool": tool_name,
            "args": args,
            "success": success,
            "duration_ms": round(duration_ms, 1),
            "summary": extract_tool_summary(tool_name, result) if result else "无返回结果",
        }
        if error:
            entry["error"] = error

        try:
            with open(_log_path(), "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[ToolLogger] 写日志失败: {e}")

    def reset(self):
        self._call_index = 0
