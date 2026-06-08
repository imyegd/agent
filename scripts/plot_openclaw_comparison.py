"""绘制本系统与 OpenClaw 性能对比图。"""
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
FONT = "Microsoft YaHei"

MODELS = ["Ours", "OpenClaw (Base)", "OpenClaw + Skills"]
MODELS_CN = ["Ours", "OpenClaw (Base)", "OpenClaw + Skills"]

METRICS = ["平均 Token 消耗", "平均响应时间", "诊断质量评分"]
VALUES = {
    "平均 Token 消耗": [17158.66, 3941.63, 285769.50],
    "平均响应时间": [13.23, 7.55, 127.43],
    "诊断质量评分": [4.2, 0.3, 4.0],
}
DISPLAY = {
    "平均 Token 消耗": ["17,158.66", "3,941.63", "285,769.50"],
    "平均响应时间": ["13.23s", "7.55s", "127.43s"],
    "诊断质量评分": ["4.2/5", "0.3/5", "4.0/5"],
}

COLORS = ["#2E86AB", "#95A5A6", "#E67E22"]
OUT_DIR = Path(__file__).resolve().parents[1] / "docs"


def plot_table(out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 2.8), facecolor="white")
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    col_x = [0.22, 0.42, 0.62, 0.82]
    row_y = [0.78, 0.52, 0.26, 0.0]
    row_h = 0.22

    # booktabs 风格横线
    for y in [0.92, 0.66, 0.02]:
        ax.plot([0.06, 0.94], [y, y], color="black", linewidth=1.8 if y == 0.92 else 1.0)

    # 表头
    headers = ["指标"] + MODELS_CN
    for x, text in zip(col_x, headers):
        ax.text(x, row_y[0] + row_h * 0.55, text, ha="center", va="center",
                fontsize=12, fontweight="bold", fontfamily=FONT)

    # 数据行
    for i, metric in enumerate(METRICS):
        y = row_y[i + 1] + row_h * 0.55
        ax.text(col_x[0], y, metric, ha="center", va="center", fontsize=11, fontfamily=FONT)
        for j, val in enumerate(DISPLAY[metric]):
            ax.text(col_x[j + 1], y, val, ha="center", va="center", fontsize=11, fontfamily=FONT)

    ax.text(0.5, 0.98, "本系统与 OpenClaw 框架性能对比", ha="center", va="top",
            fontsize=14, fontweight="bold", fontfamily=FONT)

    fig.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_bars(out_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.2), facecolor="white")
    fig.suptitle("本系统与 OpenClaw 框架性能对比", fontsize=14, fontweight="bold", fontfamily=FONT, y=1.02)

    x = np.arange(len(MODELS))
    width = 0.55

    for ax, metric in zip(axes, METRICS):
        vals = VALUES[metric]
        bars = ax.bar(x, vals, width, color=COLORS, edgecolor="#333333", linewidth=0.6)
        ax.set_title(metric, fontsize=12, fontweight="bold", fontfamily=FONT, pad=10)
        ax.set_xticks(x)
        ax.set_xticklabels(MODELS, fontsize=9, fontfamily=FONT, rotation=12, ha="right")
        ax.set_axisbelow(True)
        ax.yaxis.grid(True, linestyle="--", alpha=0.4)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        if metric == "平均 Token 消耗":
            ax.set_yscale("log")
            ax.set_ylabel("Token（对数刻度）", fontfamily=FONT, fontsize=10)

        for bar, disp in zip(bars, DISPLAY[metric]):
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h, disp,
                    ha="center", va="bottom", fontsize=9, fontfamily=FONT)

    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plot_table(OUT_DIR / "openclaw_comparison_table.png")
    plot_bars(OUT_DIR / "openclaw_comparison_bars.png")
    print(f"Saved: {OUT_DIR / 'openclaw_comparison_table.png'}")
    print(f"Saved: {OUT_DIR / 'openclaw_comparison_bars.png'}")


if __name__ == "__main__":
    main()
