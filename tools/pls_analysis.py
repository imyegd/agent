"""
PLS 波动分析工具模块
使用 PLS 模型分析束流数据的波动情况，检测异常
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

# 导入 DataQueryTool，使用相对导入避免循环依赖
try:
    from .data_query import DataQueryTool
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from tools.data_query import DataQueryTool


class PLSAnalysisTool:
    """PLS 分析工具类"""
    
    def __init__(self, model_path: Optional[str] = None, data_path: Optional[str] = None):
        """
        初始化 PLS 分析工具
        
        Args:
            model_path: PLS 模型文件路径，默认为 "models/pls_model.pkl"
            data_path: CSV数据文件路径，默认为 "data/束流.csv"
        """
        # 获取项目根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        self.model_path = model_path or os.path.join(project_root, "models", "pls_model.pkl")
        self.data_path = data_path or os.path.join(project_root, "data", "束流.csv")
        self.pls_model = None
        self.scaler_X = None
        self.scaler_Y = None
        self.eigen_values_pls = None
        self.UCL_T2X = None
        self.UCL_SPEX = None
        self.feature_names = None
        self._load_model()
    
    def _load_model(self):
        """加载 PLS 模型"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"模型文件不存在: {self.model_path}")
        
        print(f"加载 PLS 模型: {self.model_path}")
        artifacts = joblib.load(self.model_path)
        self.pls_model = artifacts['pls_model']
        self.scaler_X = artifacts['scaler_X']
        self.scaler_Y = artifacts.get('scaler_Y', None)
        self.eigen_values_pls = artifacts['eigen_values_pls']
        self.UCL_T2X = artifacts['UCL_T2X']
        self.UCL_SPEX = artifacts['UCL_SPEX_approx']
        self.feature_names = artifacts.get('feature_names', None)
        
        # 如果没有特征名，根据模型维度生成
        if self.feature_names is None:
            n_features = self.pls_model.n_features_in_
            self.feature_names = [f'feature{i+1}' for i in range(n_features)]
        
        print(f"模型加载成功，特征数: {len(self.feature_names)}")
    
    def _compute_pls_stats(self, X_scaled: np.ndarray) -> tuple:
        """
        计算 T²_X 和 SPE_X 统计量
        
        Args:
            X_scaled: 标准化后的特征数据
            
        Returns:
            (T2X, SPEX, E_X) 统计量数组
        """
        # 计算得分矩阵 T
        T = self.pls_model.transform(X_scaled)
        
        # 计算 T²_X 统计量
        T2X = np.sum(T**2 / self.eigen_values_pls, axis=1)
        
        # 计算 SPE_X 统计量
        P_X_matrix = self.pls_model.x_loadings_
        X_hat = np.dot(T, P_X_matrix.T)  # 重构的 X
        E_X = X_scaled - X_hat  # 残差
        SPE_X = np.sum(E_X**2, axis=1)
        
        return T2X, SPE_X, E_X
    
    def analyze_fluctuation(
        self,
        start_time: str,
        end_time: str
    ) -> Dict[str, Any]:
        """
        分析指定时间范围内数据的波动情况
        
        Args:
            start_time: 开始时间，格式如 "2025-08-30 17:23:26"
            end_time: 结束时间，格式如 "2025-08-30 18:23:30"
        
        Returns:
            包含分析结果的字典
        """
        try:
            # 1. 查询数据
            # 确保 DataQueryTool 使用正确的路径
            import os
            data_path_abs = os.path.abspath(self.data_path)
            query_tool = DataQueryTool(data_path=data_path_abs)
            result = query_tool.query_by_time_range(start_time, end_time)
            
            if not result.get('success', False):
                return {
                    "success": False,
                    "error": result.get('error', '未知错误'),
                    "message": "数据查询失败"
                }
            
            # 2. 提取特征数据
            query_tool.df['时间'] = pd.to_datetime(query_tool.df['时间'])
            start_dt = pd.to_datetime(start_time)
            end_dt = pd.to_datetime(end_time)
            mask = (query_tool.df['时间'] >= start_dt) & (query_tool.df['时间'] <= end_dt)
            data_df = query_tool.df[mask].copy()
            
            if len(data_df) == 0:
                return {
                    "success": False,
                    "error": "指定时间范围内没有数据",
                    "message": f"在 {start_time} 到 {end_time} 范围内未找到数据"
                }
            
            # 提取特征列（feature1 到 feature35）
            feature_cols = [col for col in data_df.columns if col.startswith('feature')]
            feature_cols.sort(key=lambda x: int(x.replace('feature', '')))  # 按数字排序
            
            if len(feature_cols) == 0:
                return {
                    "success": False,
                    "error": "数据中未找到特征列",
                    "message": "数据格式不正确，缺少 feature 列"
                }
            
            # 确保特征数量匹配
            if len(feature_cols) != len(self.feature_names):
                return {
                    "success": False,
                    "error": f"特征数量不匹配：数据有 {len(feature_cols)} 个特征，模型需要 {len(self.feature_names)} 个",
                    "message": "数据特征维度与模型不匹配"
                }
            
            X_data = data_df[feature_cols].values
            
            # 3. 数据标准化
            X_scaled = self.scaler_X.transform(X_data)
            
            # 4. 计算统计量
            T2X, SPEX, E_X = self._compute_pls_stats(X_scaled)
            
            # 5. 检测异常
            anomalies_T2X = T2X > self.UCL_T2X
            anomalies_SPEX = SPEX > self.UCL_SPEX
            anomalies_combined = anomalies_T2X | anomalies_SPEX
            
            # 6. 统计信息
            anomaly_count = np.sum(anomalies_combined)
            anomaly_rate = float(anomaly_count / len(T2X)) if len(T2X) > 0 else 0.0
            
            # 7. 找出第一个异常点及其贡献度
            first_anomaly_info = None
            if anomaly_count > 0:
                first_anomaly_idx = np.where(anomalies_combined)[0][0]
                first_anomaly_time = data_df.iloc[first_anomaly_idx]['时间']
                
                anomaly_info = {
                    "index": int(first_anomaly_idx),
                    "time": str(first_anomaly_time),
                    "T2X_value": float(T2X[first_anomaly_idx]),
                    "SPEX_value": float(SPEX[first_anomaly_idx]),
                    "T2X_anomaly": bool(anomalies_T2X[first_anomaly_idx]),
                    "SPEX_anomaly": bool(anomalies_SPEX[first_anomaly_idx])
                }
                
                # 计算贡献度
                if anomalies_T2X[first_anomaly_idx]:
                    t_anomaly = self.pls_model.transform(X_scaled[first_anomaly_idx].reshape(1, -1))[0]
                    T2X_contributions = np.sum(
                        (t_anomaly[:, np.newaxis] * self.pls_model.x_loadings_.T)**2 / 
                        self.eigen_values_pls[:, np.newaxis], 
                        axis=0
                    )
                    top_T2X_features = pd.Series(
                        T2X_contributions, 
                        index=self.feature_names
                    ).sort_values(ascending=False).head(3)
                    anomaly_info["T2X_top_features"] = {
                        name: float(val) for name, val in top_T2X_features.items()
                    }
                
                if anomalies_SPEX[first_anomaly_idx]:
                    e_anomaly = E_X[first_anomaly_idx]
                    SPEX_contributions = e_anomaly**2
                    top_SPEX_features = pd.Series(
                        SPEX_contributions,
                        index=self.feature_names
                    ).sort_values(ascending=False).head(3)
                    anomaly_info["SPEX_top_features"] = {
                        name: float(val) for name, val in top_SPEX_features.items()
                    }
                
                first_anomaly_info = anomaly_info
            
            # 8. 构建返回结果
            result = {
                "success": True,
                "start_time": start_time,
                "end_time": end_time,
                "data_count": len(data_df),
                "statistics": {
                    "T2X_mean": float(np.mean(T2X)),
                    "T2X_max": float(np.max(T2X)),
                    "T2X_min": float(np.min(T2X)),
                    "T2X_std": float(np.std(T2X)),
                    "SPEX_mean": float(np.mean(SPEX)),
                    "SPEX_max": float(np.max(SPEX)),
                    "SPEX_min": float(np.min(SPEX)),
                    "SPEX_std": float(np.std(SPEX))
                },
                "thresholds": {
                    "UCL_T2X": float(self.UCL_T2X),
                    "UCL_SPEX": float(self.UCL_SPEX)
                },
                "anomaly_detection": {
                    "total_samples": len(T2X),
                    "anomaly_count": int(anomaly_count),
                    "anomaly_rate": round(anomaly_rate, 4),
                    "T2X_anomaly_count": int(np.sum(anomalies_T2X)),
                    "SPEX_anomaly_count": int(np.sum(anomalies_SPEX)),
                    "first_anomaly": first_anomaly_info
                },
                "summary": {
                    "has_anomaly": bool(anomaly_count > 0),
                    "status": "异常" if anomaly_count > 0 else "正常",
                    "message": f"检测到 {anomaly_count} 个异常点（异常率: {anomaly_rate:.2%}）" if anomaly_count > 0 
                              else "未检测到异常，数据波动在正常范围内"
                }
            }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"分析失败: {str(e)}"
            }


# 定义 PLS 分析工具的工具描述（OpenAI Function Calling格式）
PLS_ANALYSIS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "analyze_beam_fluctuation",
            "description": "分析指定时间范围内束流数据的波动情况。使用 PLS 模型检测数据是否超过阈值，识别异常点并分析异常原因。适用于检测数据漂移、结构变化等异常情况。",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "string",
                        "description": "开始时间，支持格式：'YYYY-MM-DD HH:MM:SS' 或 'YYYY-MM-DDTHH:MM:SS'。例如：'2025-08-30 17:23:26' 或 '2025-08-30T17:23:26'"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "结束时间，支持格式：'YYYY-MM-DD HH:MM:SS' 或 'YYYY-MM-DDTHH:MM:SS'。例如：'2025-08-30 18:23:30' 或 '2025-08-30T18:23:30'"
                    }
                },
                "required": ["start_time", "end_time"]
            }
        }
    }
]


# 定义供LLM调用的工具函数
def analyze_beam_fluctuation(start_time: str, end_time: str) -> Dict[str, Any]:
    """
    分析指定时间范围内束流数据的波动情况
    
    使用 PLS 模型检测数据是否超过阈值，识别异常点并分析异常原因。
    
    Args:
        start_time: 开始时间，格式如 "2025-08-30 17:23:26" 或 "2025-08-30T17:23:26"
        end_time: 结束时间，格式如 "2025-08-30 18:23:30" 或 "2025-08-30T18:23:30"
    
    Returns:
        包含分析结果的字典，包括：
        - 统计信息（T2X 和 SPEX 的均值、最大值、最小值等）
        - 异常检测结果（异常点数量、异常率等）
        - 第一个异常点的详细信息（包括导致异常的主要特征）
    """
    try:
        tool = PLSAnalysisTool()
        return tool.analyze_fluctuation(start_time, end_time)
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"PLS 分析失败: {str(e)}"
        }


# PLS 分析工具函数映射
PLS_ANALYSIS_TOOL_FUNCTIONS = {
    "analyze_beam_fluctuation": analyze_beam_fluctuation
}

