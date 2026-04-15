"""
切块策略检索效果对比图（Acc@TopK，K=1~5）
数据来源：experiment/data/evaluation_report.txt
输出：experiment/plot/chunker_topk_accuracy.png
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# ── 字体设置 ───────────────────────────────────────────────────────────
def get_chinese_font():
    candidates = ["SimHei", "Microsoft YaHei", "STHeiti", "Heiti TC", "WenQuanYi Micro Hei"]
    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return name
    return None

font_name = get_chinese_font()
if font_name:
    plt.rcParams["font.sans-serif"] = [font_name]
plt.rcParams["axes.unicode_minus"] = False

# ── 实验数据（来自 evaluation_report.txt，K=1,2,3,4,5） ────────────────
methods = ["固定长度切块", "语义切块", "章节切块", "父子切块"]
K_values = [1, 2, 3, 4, 5]
topk_data = {
    "固定长度切块": [28.95, 44.39, 51.05, 55.61, 59.12],
    "语义切块":     [26.49, 37.72, 44.91, 50.35, 52.98],
    "章节切块":     [28.07, 39.12, 45.09, 50.00, 54.56],
    "父子切块":     [36.32, 48.60, 54.56, 60.18, 65.09],
}

colors     = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]
markers    = ["s",       "^",       "D",       "o"]
linestyles = ["--",      "--",      "--",      "-"]
linewidths = [1.4,       1.4,       1.4,       2.2]

OUT_DIR = os.path.dirname(__file__)

# ── 绘图 ───────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(6.5, 4.2))

for i, method in enumerate(methods):
    ax.plot(
        K_values, topk_data[method],
        color=colors[i], marker=markers[i],
        linestyle=linestyles[i], linewidth=linewidths[i],
        markersize=7, label=method,
        zorder=3 if method == "父子切块" else 2,
    )

ax.set_xlabel("$K$", fontsize=12)
ax.set_ylabel("Acc@Top$K$ (%)", fontsize=12)
ax.set_xticks(K_values)
ax.set_xticklabels([f"Top-{k}" for k in K_values], fontsize=10)
ax.set_ylim(22, 70)
ax.set_yticks(range(25, 71, 5))
ax.tick_params(axis="y", labelsize=10)
ax.grid(True, linestyle=":", linewidth=0.6, color="gray", alpha=0.6)
ax.spines[["top", "right"]].set_visible(False)
ax.legend(loc="upper left", fontsize=10, framealpha=0.85)
# ax.set_title("不同切块策略的 Acc@Top$K$ 检索准确率对比", fontsize=12, pad=10)

fig.tight_layout()
out = os.path.join(OUT_DIR, "chunker_topk_accuracy.png")
fig.savefig(out, dpi=300, bbox_inches="tight")
print(f"已保存：{out}")
plt.close(fig)
