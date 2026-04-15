"""
检索策略效果对比图（Acc@TopK，K=1~5）
数据来源：experiment/data/parent_child_methods_comparison.txt
输出：experiment/plot/retriever_topk_accuracy.png
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

# ── 实验数据（来自 parent_child_methods_comparison.txt，K=1,2,3,4,5） ──
methods = ["图谱检索", "混合检索", "混合检索 + 图谱"]
K_values = [1, 2, 3, 4, 5]
topk_data = {
    "图谱检索": [23.68, 32.81, 39.47, 44.91, 48.77],
    "混合检索":             [42.81, 55.26, 61.58, 66.14, 69.30],
    "混合检索 + 图谱":             [46.14, 58.42, 64.91, 69.12, 71.93],
}

colors     = ["#4C72B0", "#DD8452", "#C44E52"]
markers    = ["s",       "^",       "o"]
linestyles = ["--",      "--",      "-"]
linewidths = [1.4,       1.4,       2.2]

OUT_DIR = os.path.dirname(__file__)

# ── 绘图 ───────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(6.5, 4.2))

for i, method in enumerate(methods):
    ax.plot(
        K_values, topk_data[method],
        color=colors[i], marker=markers[i],
        linestyle=linestyles[i], linewidth=linewidths[i],
        markersize=7, label=method,
        zorder=3 if method == "混合检索 + 图谱" else 2,
    )

ax.set_xlabel("$K$", fontsize=12)
ax.set_ylabel("Acc@Top$K$ (%)", fontsize=12)
ax.set_xticks(K_values)
ax.set_xticklabels([f"Top-{k}" for k in K_values], fontsize=10)
ax.set_ylim(20, 80)
ax.set_yticks(range(20, 80, 5))
ax.tick_params(axis="y", labelsize=10)
ax.grid(True, linestyle=":", linewidth=0.6, color="gray", alpha=0.6)
ax.spines[["top", "right"]].set_visible(False)
ax.legend(loc="upper left", fontsize=10, framealpha=0.85)
# ax.set_title("不同检索策略的 Acc@Top$K$ 检索准确率对比", fontsize=12, pad=10)

fig.tight_layout()
out = os.path.join(OUT_DIR, "kg_retriever_topk_accuracy.png")
fig.savefig(out, dpi=300, bbox_inches="tight")
print(f"已保存：{out}")
plt.close(fig)
