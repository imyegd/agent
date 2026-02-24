"""
异常检测工具模块
基于回归预测偏差 + 3σ 工程判据
"""

import pandas as pd
import numpy as np
import joblib
from typing import Dict, Any
import os


class AnomalyDetectionTool:

    def __init__(
        self,
        data_path: str = "data/束流.csv",
        model_path: str = "models/RF_regressor.pkl",
        stats_path: str = "models/normal_stats.npy"
    ):
        self.data_path = data_path
        self.model = joblib.load(model_path)
        self.normal_stats = np.load(stats_path, allow_pickle=True).item()
        self.df = self._load_data()

    def _load_data(self) -> pd.DataFrame:
        df = pd.read_csv(self.data_path)
        df['时间'] = pd.to_datetime(df['时间'])
        return df

    def detect(
        self,
        start_time: str,
        end_time: str
    ) -> Dict[str, Any]:

        start_dt = pd.to_datetime(start_time)
        end_dt = pd.to_datetime(end_time)

        seg = self.df[(self.df['时间'] >= start_dt) & (self.df['时间'] <= end_dt)]
        if seg.empty:
            return {"success": False, "message": "时间段内无数据"}

        X = seg.drop(columns=['时间', 'target'])
        y_true = seg['target'].values
        y_pred = self.model.predict(X)

        # normal_stats 中的键是 'mu' 和 'sigma'
        mu = self.normal_stats['mu']
        sigma = self.normal_stats['sigma']

        is_anomaly = np.any(np.abs(y_pred - mu) > 3 * sigma)

        return {
            "success": True,
            "is_anomaly": bool(is_anomaly),
            "anomaly_ratio": float(np.mean(np.abs(y_pred - mu) > 3 * sigma)),
            "prediction_mean": float(y_pred.mean()),
            "normal_mean": float(mu),
            "normal_std": float(sigma)
        }


# LLM 调用接口
def detect_anomaly(start_time: str, end_time: str) -> Dict[str, Any]:
    """
    异常检测接口函数
    """
    tool = AnomalyDetectionTool()
    return tool.detect(start_time, end_time)


# 工具函数映射
ANOMALY_DETECTION_TOOL_FUNCTIONS = {
    "detect_anomaly": detect_anomaly
}


ANOMALY_DETECTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "detect_anomaly",
            "description": "基于回归预测偏差和3σ工程判据判断指定时间段是否存在异常。",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"}
                },
                "required": ["start_time", "end_time"]
            }
        }
    }
]
