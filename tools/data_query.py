"""
数据查询工具模块
提供从CSV文件中查询束流数据的功能
"""

import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any
import os


class DataQueryTool:
    """数据查询工具类"""
    
    def __init__(self, data_path: str = "束流.csv"):
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
    
    def query_by_time_range(
        self,
        start_time: str,
        end_time: str,
        columns: Optional[list] = None
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
        try:
            # 解析时间
            start_dt = pd.to_datetime(start_time)
            end_dt = pd.to_datetime(end_time)
            
            # 查询数据
            mask = (self.df['时间'] >= start_dt) & (self.df['时间'] <= end_dt)
            result_df = self.df[mask]
            
            # 选择特定列
            if columns:
                available_columns = [col for col in columns if col in result_df.columns]
                if available_columns:
                    result_df = result_df[available_columns]
            
            
            # 构建返回结果
            # 先将时间列转换为字符串
            result_df_copy = result_df.copy()
            if '时间' in result_df_copy.columns:
                result_df_copy['时间'] = result_df_copy['时间'].dt.strftime('%Y-%m-%d %H:%M:%S')

            return {
                "success": True,
                "count": len(result_df),
                "start_time": start_time,
                "end_time": end_time,
                "data": result_df_copy.to_dict('records'),  # 使用转换后的副本
                "statistics": {
                    "target_mean": float(result_df['target'].mean()) if 'target' in result_df.columns else None,
                    "target_max": float(result_df['target'].max()) if 'target' in result_df.columns else None,
                    "target_min": float(result_df['target'].min()) if 'target' in result_df.columns else None,
                    "target_std": float(result_df['target'].std()) if 'target' in result_df.columns else None,
                },
                "columns": list(result_df.columns)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"查询失败: {str(e)}"
            }
    
    def get_data_summary(self) -> Dict[str, Any]:
        """
        获取数据集的概要信息
        
        Returns:
            数据集概要信息字典
        """
        return {
            "total_records": len(self.df),
            "columns": list(self.df.columns),
            "time_range": {
                "start": str(self.df['时间'].min()),
                "end": str(self.df['时间'].max())
            },
            "target_stats": {
                "mean": float(self.df['target'].mean()),
                "max": float(self.df['target'].max()),
                "min": float(self.df['target'].min()),
                "std": float(self.df['target'].std())
            }
        }


# 定义供LLM调用的工具函数
def query_beam_data(start_time: str, end_time: str, columns: list = None) -> Dict[str, Any]:
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
    return tool.query_by_time_range(start_time, end_time, columns)


def get_data_info() -> Dict[str, Any]:
    """
    获取数据集的概要信息
    
    Returns:
        数据集概要信息字典
    """
    tool = DataQueryTool()
    return tool.get_data_summary()


# 定义给LLM的工具描述（OpenAI Function Calling格式）
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_beam_data",
            "description": "查询指定时间范围内的束流数据。可以查询某个时间段的束流强度、传感器数据等信息。",
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
                        "description": "需要返回的列名列表，例如 ['时间', 'target', 'feature1']。如果不指定，则返回所有列。"
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
            "description": "获取束流数据集的概要信息，包括数据总量、时间范围、列名、统计信息等。",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]


# 工具函数映射
TOOL_FUNCTIONS = {
    "query_beam_data": query_beam_data,
    "get_data_info": get_data_info
}

