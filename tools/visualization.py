"""
可视化工具模块
提供束流数据的时序图绘制功能。
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import rcParams

# 中文字体配置
rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
rcParams["axes.unicode_minus"] = False

DATA_PATH = "data/束流.csv"
OUTPUT_DIR = "output"
TIME_COL = "时间"
TARGET_COL = "target"

# 莫兰迪色系，与前端 UI 保持一致
_PALETTE = [
    "#7A94A4",  # 烟雨蓝（target 主线）
    "#A8B8A0",  # 灰绿
    "#C4A882",  # 灰豆沙
    "#9B8FAE",  # 灰紫
    "#B0C4C4",  # 灰青
    "#C48B8B",  # 灰红
]


def _ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def _load_slice(start_time: str, end_time: str) -> pd.DataFrame:
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"数据文件不存在: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    df[TIME_COL] = pd.to_datetime(df[TIME_COL])
    start_dt = pd.to_datetime(start_time)
    end_dt = pd.to_datetime(end_time)
    return df[(df[TIME_COL] >= start_dt) & (df[TIME_COL] <= end_dt)].copy()


def plot_beam_data(
    start_time: str,
    end_time: str,
    features: Optional[List[str]] = None,
    anomaly_mask: Optional[List[bool]] = None,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    绘制指定时间段内的束流时序图。

    主图永远显示 target（束流强度），可选同屏叠加若干特征曲线。
    若传入 anomaly_mask，会在图上用红色底色高亮异常区域。

    Args:
        start_time:    开始时间，格式 "YYYY-MM-DD HH:MM:SS"
        end_time:      结束时间，格式 "YYYY-MM-DD HH:MM:SS"
        features:      可选，额外叠加绘制的特征列名列表（最多 5 个）
        anomaly_mask:  可选，与数据行一一对应的布尔列表，True 表示该行为异常点
        title:         可选，图表标题；不传则自动生成

    Returns:
        {
          "success": bool,
          "plot_path": str,      # 相对路径，供前端加载
          "message": str,
          "stats": {             # target 基础统计
            "count": int,
            "mean": float,
            "max": float,
            "min": float,
            "anomaly_ratio": float   # 仅当传入 anomaly_mask 时
          }
        }
    """
    try:
        df = _load_slice(start_time, end_time)
    except FileNotFoundError as e:
        return {"success": False, "message": str(e)}

    if df.empty:
        return {
            "success": False,
            "message": f"时间段 {start_time} ~ {end_time} 内无数据",
        }

    if TARGET_COL not in df.columns:
        return {"success": False, "message": f"数据中不存在 '{TARGET_COL}' 列"}

    # 校验 features
    valid_features: List[str] = []
    if features:
        available = [c for c in df.columns if c not in [TIME_COL, TARGET_COL]]
        valid_features = [f for f in features[:5] if f in available]

    # 校验 anomaly_mask
    mask_series: Optional[pd.Series] = None
    if anomaly_mask is not None and len(anomaly_mask) == len(df):
        mask_series = pd.Series(anomaly_mask, index=df.index)

    # ===== 绘图 =====
    n_axes = 1 + len(valid_features)
    fig_height = 3.5 + 2.2 * (n_axes - 1)
    fig, axes = plt.subplots(
        n_axes, 1,
        figsize=(12, fig_height),
        sharex=True,
        gridspec_kw={"hspace": 0.08}
    )
    if n_axes == 1:
        axes = [axes]

    fig.patch.set_facecolor("#F6F7F8")

    def _style_ax(ax):
        ax.set_facecolor("#FFFFFF")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#CCCCCC")
        ax.spines["bottom"].set_color("#CCCCCC")
        ax.tick_params(colors="#666666", labelsize=9)
        ax.yaxis.label.set_color("#444444")
        ax.grid(axis="y", color="#EEEEEE", linewidth=0.8)

    def _shade_anomalies(ax, time_col, mask):
        """用浅红色填充异常时段"""
        if mask is None:
            return
        in_block = False
        blk_start = None
        for t, flag in zip(time_col, mask):
            if flag and not in_block:
                blk_start = t
                in_block = True
            elif not flag and in_block:
                ax.axvspan(blk_start, t, color="#C48B8B", alpha=0.18, linewidth=0)
                in_block = False
        if in_block:
            ax.axvspan(blk_start, time_col.iloc[-1], color="#C48B8B", alpha=0.18, linewidth=0)

    time_col = df[TIME_COL]

    # --- 主图：target ---
    ax0 = axes[0]
    _style_ax(ax0)
    ax0.plot(time_col, df[TARGET_COL], color=_PALETTE[0], linewidth=1.4,
             label="target（束流强度）")
    _shade_anomalies(ax0, time_col, mask_series)
    ax0.set_ylabel("target", fontsize=10)
    ax0.legend(loc="upper right", fontsize=9, framealpha=0.6)

    # --- 副图：各 feature ---
    for i, feat in enumerate(valid_features):
        ax = axes[i + 1]
        _style_ax(ax)
        color = _PALETTE[(i + 1) % len(_PALETTE)]
        ax.plot(time_col, df[feat], color=color, linewidth=1.2, label=feat)
        _shade_anomalies(ax, time_col, mask_series)
        ax.set_ylabel(feat, fontsize=10)
        ax.legend(loc="upper right", fontsize=9, framealpha=0.6)

    # --- X 轴格式 ---
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    axes[-1].xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.setp(axes[-1].xaxis.get_majorticklabels(), rotation=20, ha="right")

    # --- 标题 ---
    start_short = start_time[:16]
    end_short = end_time[:16]
    chart_title = title or f"束流数据时序图  {start_short} ~ {end_short}"
    fig.suptitle(chart_title, fontsize=13, color="#333333",
                 y=1.01 if n_axes == 1 else 1.0, fontweight="semibold")

    # 异常比例注释
    if mask_series is not None:
        ratio = mask_series.sum() / len(mask_series)
        axes[0].text(
            0.01, 0.96,
            f"异常占比 {ratio:.1%}",
            transform=axes[0].transAxes,
            fontsize=9, color="#C48B8B", va="top"
        )

    # ===== 保存 =====
    _ensure_output_dir()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
    filename = f"beam_{ts}.png"
    save_path = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(save_path, dpi=130, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)

    # 统计
    stats: Dict[str, Any] = {
        "count": int(len(df)),
        "mean": round(float(df[TARGET_COL].mean()), 4),
        "max": round(float(df[TARGET_COL].max()), 4),
        "min": round(float(df[TARGET_COL].min()), 4),
    }
    if mask_series is not None:
        stats["anomaly_ratio"] = round(float(mask_series.mean()), 4)

    return {
        "success": True,
        "plot_path": save_path,
        "message": f"已生成时序图，包含 {len(df)} 条记录",
        "stats": stats,
    }


# ===== LLM Function Calling 描述 =====

VISUALIZATION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "plot_beam_data",
            "description": (
                "绘制指定时间段内的束流时序图（折线图）。"
                "主图始终显示 target（束流强度），可选叠加若干特征曲线。"
                "仅在用户明确要求查看图表/可视化时调用，不要自动附加到每次查询。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "string",
                        "description": "开始时间，格式 'YYYY-MM-DD HH:MM:SS'"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "结束时间，格式 'YYYY-MM-DD HH:MM:SS'"
                    },
                    "features": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "可选。在 target 下方额外绘制的特征列名，最多 5 个，如 ['feature1', 'feature3']。"
                    },
                    "title": {
                        "type": "string",
                        "description": "可选。图表标题，不传则自动生成。"
                    }
                },
                "required": ["start_time", "end_time"]
            }
        }
    }
]

VISUALIZATION_TOOL_FUNCTIONS = {
    "plot_beam_data": plot_beam_data,
}
