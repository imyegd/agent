"""
数据查询工具模块
提供从 CSV 文件中查询束流数据的功能。
"""

import os
from typing import Optional, Dict, Any, List

import pandas as pd


class DataQueryTool:
    """数据查询工具类"""
    
    def __init__(self, data_path: str = "data/束流.csv"):
        """
        初始化数据查询工具
        
        Args:
            data_path: CSV数据文件路径
        """
        self.data_path = data_path
        self.df = None
        self._load_data()
    
    def _load_data(self):
        """加载CSV数据"""
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"数据文件不存在: {self.data_path}")
        
        self.df = pd.read_csv(self.data_path)
        # 将时间列转换为datetime类型
        self.df['时间'] = pd.to_datetime(self.df['时间'])
        print(f"数据加载成功，共 {len(self.df)} 条记录")
    
    @staticmethod
    def _format_timestamp(value: Any) -> Optional[str]:
        """将时间值格式化为统一字符串。"""
        if value is None or pd.isna(value):
            return None
        try:
            return pd.to_datetime(value).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return str(value)

    def _standard_error(self, message: str, error_type: str, suggestion: str) -> Dict[str, Any]:
        """统一错误输出结构。"""
        return {
            "success": False,
            "tool": "query_beam_data",
            "message": message,
            "error": {
                "type": error_type,
                "detail": message,
                "suggestion": suggestion
            }
        }

    def query_by_time_range(
        self,
        start_time: str,
        end_time: str,
        columns: Optional[List[str]] = None,
        limit: int = 20,
        include_statistics: bool = True
    ) -> Dict[str, Any]:
        """
        根据时间范围查询数据
        
        Args:
            start_time: 开始时间，格式如 "2025-08-31 02:00:00" 或 "2025-08-31T02:00:00"
            end_time: 结束时间，格式如 "2025-08-31 03:00:00" 或 "2025-08-31T03:00:00"
            columns: 需要返回的列名列表，默认返回所有列
        
        Returns:
            包含查询结果的字典，包括数据、统计信息等
        """
        if limit <= 0 or limit > 200:
            return self._standard_error(
                message=f"limit 参数不合法: {limit}",
                error_type="invalid_limit",
                suggestion="请传入 1 到 200 之间的整数。"
            )

        try:
            start_dt = pd.to_datetime(start_time)
            end_dt = pd.to_datetime(end_time)
        except Exception:
            return self._standard_error(
                message=f"时间格式解析失败: start_time={start_time}, end_time={end_time}",
                error_type="invalid_datetime_format",
                suggestion="请使用 'YYYY-MM-DD HH:MM:SS' 或 ISO 格式时间。"
            )

        if start_dt > end_dt:
            return self._standard_error(
                message=f"开始时间不能晚于结束时间: {start_time} > {end_time}",
                error_type="invalid_time_range",
                suggestion="请确保 start_time <= end_time。"
            )

        mask = (self.df['时间'] >= start_dt) & (self.df['时间'] <= end_dt)
        matched_df = self.df[mask]

        selected_columns = list(self.df.columns)
        ignored_columns: List[str] = []

        if columns:
            selected_columns = [col for col in columns if col in self.df.columns]
            ignored_columns = [col for col in columns if col not in self.df.columns]
            if not selected_columns:
                return self._standard_error(
                    message="columns 中没有可用列名。",
                    error_type="invalid_columns",
                    suggestion=f"请从可用列中选择: {list(self.df.columns)}"
                )
            matched_df = matched_df[selected_columns]

        returned_df = matched_df.head(limit).copy()
        if "时间" in returned_df.columns:
            returned_df["时间"] = returned_df["时间"].dt.strftime("%Y-%m-%d %H:%M:%S")

        response: Dict[str, Any] = {
            "success": True,
            "tool": "query_beam_data",
            "message": "查询成功" if len(matched_df) > 0 else "查询成功，但时间范围内无数据",
            "query": {
                "start_time": self._format_timestamp(start_dt),
                "end_time": self._format_timestamp(end_dt),
                "columns": columns or [],
                "limit": limit,
                "include_statistics": include_statistics
            },
            "summary": {
                "matched_records": int(len(matched_df)),
                "returned_records": int(len(returned_df)),
                "selected_columns": list(returned_df.columns),
                "ignored_columns": ignored_columns,
                "dataset_time_range": {
                    "start": self._format_timestamp(self.df["时间"].min()),
                    "end": self._format_timestamp(self.df["时间"].max())
                },
                "actual_result_time_range": {
                    "start": self._format_timestamp(matched_df["时间"].min()) if len(matched_df) > 0 and "时间" in matched_df.columns else None,
                    "end": self._format_timestamp(matched_df["时间"].max()) if len(matched_df) > 0 and "时间" in matched_df.columns else None
                }
            },
            "data": returned_df.to_dict("records")
        }

        if include_statistics and len(matched_df) > 0 and "target" in matched_df.columns:
            response["statistics"] = {
                "target_mean": float(matched_df["target"].mean()),
                "target_max": float(matched_df["target"].max()),
                "target_min": float(matched_df["target"].min()),
                "target_std": float(matched_df["target"].std()) if len(matched_df) > 1 else 0.0
            }

        return response
    
    def get_data_summary(
        self,
        include_target_stats: bool = True,
        include_sample: bool = True,
        sample_size: int = 3
    ) -> Dict[str, Any]:
        """
        获取数据集的概要信息
        
        Returns:
            数据集概要信息字典
        """
        if sample_size <= 0 or sample_size > 50:
            sample_size = 3

        info: Dict[str, Any] = {
            "success": True,
            "tool": "get_data_info",
            "message": "数据集信息获取成功",
            "data_info": {
                "total_records": int(len(self.df)),
                "columns": list(self.df.columns),
                "time_column": "时间",
                "target_column": "target" if "target" in self.df.columns else None,
                "time_range": {
                    "start": self._format_timestamp(self.df["时间"].min()),
                    "end": self._format_timestamp(self.df["时间"].max())
                }
            }
        }

        if include_target_stats and "target" in self.df.columns:
            info["data_info"]["target_stats"] = {
                "mean": float(self.df["target"].mean()),
                "max": float(self.df["target"].max()),
                "min": float(self.df["target"].min()),
                "std": float(self.df["target"].std())
            }

        if include_sample:
            sample_df = self.df.head(sample_size).copy()
            if "时间" in sample_df.columns:
                sample_df["时间"] = sample_df["时间"].dt.strftime("%Y-%m-%d %H:%M:%S")
            info["sample"] = sample_df.to_dict("records")

        return info


# 定义供LLM调用的工具函数
def query_beam_data(
    start_time: str,
    end_time: str,
    columns: Optional[List[str]] = None,
    limit: int = 20,
    include_statistics: bool = True
) -> Dict[str, Any]:
    """
    查询指定时间范围内的束流数据
    
    Args:
        start_time: 开始时间，格式如 "2025-08-31 02:00:00" 或 "2025-08-31T02:00:00"
        end_time: 结束时间，格式如 "2025-08-31 03:00:00" 或 "2025-08-31T03:00:00"
        columns: 需要返回的列名列表，默认返回所有列
    
    Returns:
        包含查询结果的字典
    """
    tool = DataQueryTool()
    return tool.query_by_time_range(
        start_time=start_time,
        end_time=end_time,
        columns=columns,
        limit=limit,
        include_statistics=include_statistics
    )


def get_data_info(
    include_target_stats: bool = True,
    include_sample: bool = True,
    sample_size: int = 3
) -> Dict[str, Any]:
    """
    获取数据集的概要信息
    
    Returns:
        数据集概要信息字典
    """
    tool = DataQueryTool()
    return tool.get_data_summary(
        include_target_stats=include_target_stats,
        include_sample=include_sample,
        sample_size=sample_size
    )


# 定义数据查询工具的工具描述（OpenAI Function Calling格式）
DATA_QUERY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_beam_data",
            "description": (
                "按时间范围查询束流数据，适合先做数据核对、趋势分析前取样、异常诊断前数据确认。"
                "返回统一结构：query + summary + data + (可选)statistics。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "string",
                        "description": "开始时间，支持格式：'YYYY-MM-DD HH:MM:SS' 或 'YYYY-MM-DDTHH:MM:SS'。例如：'2025-08-31 02:00:00' 或 '2025-08-31T02:00:00'"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "结束时间，支持格式：'YYYY-MM-DD HH:MM:SS' 或 'YYYY-MM-DDTHH:MM:SS'。例如：'2025-08-31 03:00:00' 或 '2025-08-31T03:00:00'"
                    },
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "可选。需要返回的列名列表，例如 ['时间', 'target', 'feature1']。不传则返回所有列。"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "可选。返回样本条数上限，范围 1-200，默认 20。"
                    },
                    "include_statistics": {
                        "type": "boolean",
                        "description": "可选。是否返回 target 统计信息（均值/最大/最小/标准差），默认 true。"
                    }
                },
                "required": ["start_time", "end_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_data_info",
            "description": (
                "获取数据集元信息（总记录数、时间范围、列名、target 统计、样本记录）。"
                "建议在首次查询前调用，用于确定时间范围和可用列。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "include_target_stats": {
                        "type": "boolean",
                        "description": "可选。是否返回 target 统计信息，默认 true。"
                    },
                    "include_sample": {
                        "type": "boolean",
                        "description": "可选。是否返回前几条样本数据，默认 true。"
                    },
                    "sample_size": {
                        "type": "integer",
                        "description": "可选。样本条数，范围 1-50，默认 3。"
                    }
                }
            }
        }
    }
]

# 数据查询工具函数映射
DATA_QUERY_TOOL_FUNCTIONS = {
    "query_beam_data": query_beam_data,
    "get_data_info": get_data_info
}

