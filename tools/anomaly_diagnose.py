"""
异常诊断工具模块
包含统计差异 / PLS / SHAP / AutoEncoder 四类异常特征诊断工具
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List
# torch 在需要时导入，避免 DLL 错误影响其他工具


# =========================
# 全局配置
# =========================

DATA_PATH = "data/束流.csv"
MODEL_DIR = "models"
TIME_COL = "时间"
TARGET_COL = "target"


# =========================
# 工具函数
# =========================

def _load_data() -> pd.DataFrame:
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"数据文件不存在: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    df[TIME_COL] = pd.to_datetime(df[TIME_COL])
    return df


def _slice_by_time(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    start_dt = pd.to_datetime(start)
    end_dt = pd.to_datetime(end)
    return df[(df[TIME_COL] >= start_dt) & (df[TIME_COL] <= end_dt)]


def _feature_columns(df: pd.DataFrame) -> List[str]:
    return [c for c in df.columns if c not in [TIME_COL, TARGET_COL]]


# =========================
# 1. 统计差异诊断
# =========================

def diagnose_by_statistical_difference(
    anomaly_start: str,
    anomaly_end: str,
    normal_start: str,
    normal_end: str,
    top_k: int = 10
) -> Dict[str, Any]:
    """
    基于统计差异（Z-score）的异常特征诊断
    """
    df = _load_data()
    normal_df = _slice_by_time(df, normal_start, normal_end)
    anomaly_df = _slice_by_time(df, anomaly_start, anomaly_end)

    features = _feature_columns(df)
    results = []

    for f in features:
        mu = normal_df[f].mean()
        sigma = normal_df[f].std() + 1e-8
        z = (anomaly_df[f].mean() - mu) / sigma
        results.append({"feature": f, "z_score": float(abs(z))})

    results = sorted(results, key=lambda x: x["z_score"], reverse=True)[:top_k]

    return {
        "method": "statistical_difference",
        "anomaly_range": [anomaly_start, anomaly_end],
        "top_features": results
    }


# =========================
# 2. PLS 诊断（已训练模型）
# =========================

def diagnose_by_pls(
    anomaly_start: str,
    anomaly_end: str,
    top_k: int = 10
) -> Dict[str, Any]:
    """
    基于 PLS 模型权重的异常诊断
    """
    model_path = os.path.join(MODEL_DIR, "pls_model.pkl")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"PLS 模型未找到: {model_path}")

    # 加载模型（可能是字典或直接是模型对象）
    pls_data = joblib.load(model_path)
    
    # 如果是字典，提取模型对象
    if isinstance(pls_data, dict):
        if 'model' in pls_data:
            pls = pls_data['model']
        elif 'pls_model' in pls_data:
            pls = pls_data['pls_model']
        else:
            # 尝试直接使用字典中的权重
            if 'coef_' in pls_data or 'weights' in pls_data:
                weights = pls_data.get('coef_', pls_data.get('weights'))
                if weights is not None:
                    df = _load_data()
                    features = _feature_columns(df)
                    weights = np.abs(weights).ravel()
                    results = [
                        {"feature": f, "pls_weight": float(w)}
                        for f, w in zip(features, weights)
                    ]
                    results = sorted(results, key=lambda x: x["pls_weight"], reverse=True)[:top_k]
                    return {
                        "method": "pls",
                        "anomaly_range": [anomaly_start, anomaly_end],
                        "top_features": results
                    }
            raise ValueError(f"PLS 模型格式不正确，字典键: {list(pls_data.keys())}")
    else:
        pls = pls_data

    df = _load_data()
    anomaly_df = _slice_by_time(df, anomaly_start, anomaly_end)
    features = _feature_columns(df)

    weights = np.abs(pls.coef_).ravel()
    results = [
        {"feature": f, "pls_weight": float(w)}
        for f, w in zip(features, weights)
    ]

    results = sorted(results, key=lambda x: x["pls_weight"], reverse=True)[:top_k]

    return {
        "method": "pls",
        "anomaly_range": [anomaly_start, anomaly_end],
        "top_features": results
    }


# =========================
# 3. SHAP 诊断（已训练模型）
# =========================

def diagnose_by_shap(
    anomaly_start: str,
    anomaly_end: str,
    model_name: str = "RF",
    top_k: int = 10
) -> Dict[str, Any]:
    """
    基于 SHAP 的异常特征诊断
    """
    import shap

    # 模型名称映射: RF, LGBM, XGB, MLP, Linear
    model_path = os.path.join(MODEL_DIR, f"{model_name}_regressor.pkl")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"{model_name} 模型未找到: {model_path}")

    model = joblib.load(model_path)

    df = _load_data()
    anomaly_df = _slice_by_time(df, anomaly_start, anomaly_end)
    features = _feature_columns(df)

    X = anomaly_df[features]

    if model_name in ("RF", "LGBM", "XGB"):
        # 树模型专用路径：TreeExplainer 无需背景集，速度快 10-100x
        explainer = shap.TreeExplainer(model)
        explain_X = X.sample(min(500, len(X)), random_state=42)
        sv = explainer.shap_values(explain_X)
        # RF 回归 shap_values 直接是 ndarray；分类模型返回列表取 [1]
        if isinstance(sv, list):
            sv = sv[1]
        mean_abs = np.abs(sv).mean(axis=0)
    else:
        # MLP / Linear 等非树模型：双采样降低计算量
        background = shap.sample(X, min(100, len(X)))
        explain_X  = X.sample(min(300, len(X)), random_state=42)
        explainer   = shap.Explainer(model, background)
        shap_values = explainer(explain_X)
        mean_abs    = np.abs(shap_values.values).mean(axis=0)

    results = [
        {"feature": f, "mean_abs_shap": float(v)}
        for f, v in zip(features, mean_abs)
    ]

    results = sorted(results, key=lambda x: x["mean_abs_shap"], reverse=True)[:top_k]

    return {
        "method": "shap",
        "model": model_name,
        "anomaly_range": [anomaly_start, anomaly_end],
        "top_features": results
    }


# =========================
# 4. AutoEncoder 诊断
# =========================

def diagnose_by_autoencoder(
    anomaly_start: str,
    anomaly_end: str,
    top_k: int = 10
) -> Dict[str, Any]:
    """
    基于自编码器变量级重构误差的异常诊断
    """
    # 延迟导入 torch
    try:
        import torch
        import torch.nn as nn
    except (ImportError, OSError) as e:
        return {
            "success": False,
            "error": str(e),
            "message": "PyTorch 加载失败，请重新安装或使用其他诊断方法"
        }
    
    # 定义 AutoEncoder 模型（架构需要与训练时一致）
    class AutoEncoder(nn.Module):
        def __init__(self, input_dim: int):
            super().__init__()
            # 实际保存的模型架构：input_dim -> 16 -> 8 -> 16 -> input_dim
            self.encoder = nn.Sequential(
                nn.Linear(input_dim, 16),
                nn.ReLU(),
                nn.Linear(16, 8)
            )
            self.decoder = nn.Sequential(
                nn.Linear(8, 16),
                nn.ReLU(),
                nn.Linear(16, input_dim)
            )

        def forward(self, x):
            return self.decoder(self.encoder(x))
    
    model_path = os.path.join(MODEL_DIR, "ae_model.pt")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"AutoEncoder 模型未找到: {model_path}")

    df = _load_data()
    anomaly_df = _slice_by_time(df, anomaly_start, anomaly_end)
    features = _feature_columns(df)

    X = torch.tensor(anomaly_df[features].values, dtype=torch.float32)

    model = AutoEncoder(input_dim=X.shape[1])
    model.load_state_dict(torch.load(model_path))
    model.eval()

    with torch.no_grad():
        recon = model(X)
        mse = ((X - recon) ** 2).mean(dim=0).numpy()

    results = [
        {"feature": f, "mean_reconstruction_error": float(e)}
        for f, e in zip(features, mse)
    ]

    results = sorted(results, key=lambda x: x["mean_reconstruction_error"], reverse=True)[:top_k]

    return {
        "method": "autoencoder",
        "anomaly_range": [anomaly_start, anomaly_end],
        "top_features": results
    }



# =========================
# 异常诊断工具（LLM Function Calling Schema）
# =========================

ANOMALY_DIAGNOSIS_TOOLS = [

    # ---------- 1. 统计差异 ----------
    {
        "type": "function",
        "function": {
            "name": "diagnose_by_statistical_difference",
            "description": (
                "基于统计差异（Z-score）的异常特征诊断方法。"
                "通过比较异常时间段与正常时间段内各变量的统计分布差异，"
                "识别在异常状态下发生显著偏移的关键变量。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "anomaly_start": {
                        "type": "string",
                        "description": "异常时间段起始时间，格式：YYYY-MM-DD HH:MM:SS"
                    },
                    "anomaly_end": {
                        "type": "string",
                        "description": "异常时间段结束时间，格式：YYYY-MM-DD HH:MM:SS"
                    },
                    "normal_start": {
                        "type": "string",
                        "description": "正常工况时间段起始时间，用于统计基准"
                    },
                    "normal_end": {
                        "type": "string",
                        "description": "正常工况时间段结束时间，用于统计基准"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回偏移最显著的前 k 个特征",
                        "default": 10
                    }
                },
                "required": [
                    "anomaly_start",
                    "anomaly_end",
                    "normal_start",
                    "normal_end"
                ]
            }
        }
    },

    # ---------- 2. PLS ----------
    {
        "type": "function",
        "function": {
            "name": "diagnose_by_pls",
            "description": (
                "基于已训练的偏最小二乘（PLS）模型进行异常特征诊断。"
                "通过分析模型中各输入变量对目标束流的线性投影权重，"
                "识别与束流异常变化高度相关的关键变量。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "anomaly_start": {
                        "type": "string",
                        "description": "异常时间段起始时间，格式：YYYY-MM-DD HH:MM:SS"
                    },
                    "anomaly_end": {
                        "type": "string",
                        "description": "异常时间段结束时间，格式：YYYY-MM-DD HH:MM:SS"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回权重最大的前 k 个特征",
                        "default": 10
                    }
                },
                "required": [
                    "anomaly_start",
                    "anomaly_end"
                ]
            }
        }
    },

    # ---------- 3. SHAP ----------
    {
        "type": "function",
        "function": {
            "name": "diagnose_by_shap",
            "description": (
                "基于 SHAP 方法的异常特征诊断工具。"
                "对已训练的回归模型（如随机森林、XGBoost）进行解释，"
                "分析异常时间段内各变量对模型预测结果的贡献程度，"
                "从模型角度识别导致束流偏离的关键变量。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "anomaly_start": {
                        "type": "string",
                        "description": "异常时间段起始时间，格式：YYYY-MM-DD HH:MM:SS"
                    },
                    "anomaly_end": {
                        "type": "string",
                        "description": "异常时间段结束时间，格式：YYYY-MM-DD HH:MM:SS"
                    },
                    "model_name": {
                        "type": "string",
                        "description": "用于 SHAP 解释的回归模型名称，可选: 'RF'(随机森林), 'XGB'(XGBoost), 'LGBM'(LightGBM), 'MLP'(神经网络), 'Linear'(线性回归)",
                        "default": "RF"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回 SHAP 重要性最高的前 k 个特征",
                        "default": 10
                    }
                },
                "required": [
                    "anomaly_start",
                    "anomaly_end"
                ]
            }
        }
    },

    # ---------- 4. AutoEncoder ----------
    {
        "type": "function",
        "function": {
            "name": "diagnose_by_autoencoder",
            "description": (
                "基于已训练自编码器（AutoEncoder）的异常特征诊断方法。"
                "通过分析异常时间段内各变量的重构误差，"
                "识别相对于正常工况分布发生显著偏离的关键变量。"
                "该方法不依赖监督标签，适用于无故障标注场景。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "anomaly_start": {
                        "type": "string",
                        "description": "异常时间段起始时间，格式：YYYY-MM-DD HH:MM:SS"
                    },
                    "anomaly_end": {
                        "type": "string",
                        "description": "异常时间段结束时间，格式：YYYY-MM-DD HH:MM:SS"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回重构误差最大的前 k 个特征",
                        "default": 10
                    }
                },
                "required": [
                    "anomaly_start",
                    "anomaly_end"
                ]
            }
        }
    }
]



ANOMALY_DIAGNOSIS_TOOL_FUNCTIONS = {
    "diagnose_by_statistical_difference": diagnose_by_statistical_difference,
    "diagnose_by_pls": diagnose_by_pls,
    "diagnose_by_shap": diagnose_by_shap,
    "diagnose_by_autoencoder": diagnose_by_autoencoder
}
