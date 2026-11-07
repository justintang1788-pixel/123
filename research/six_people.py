"""画论文图2的两种读法：后进先出（论文原图）和先进先出（建议）。

人数在两种画法下完全一样，区别只在“谁先变”。
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei"]
plt.rcParams["axes.unicode_minus"] = False

STAGES = ["绝望", "怀疑", "犹豫", "大众\n共识", "泡沫", "兑现", "幻想", "侥幸", "瓦解", "麻木", "恐慌", "衰竭"]
BULL, BEAR = "#c75f34", "#5779a8"


def bullish(person, stage, fifo):
    """person 1..6 = 第几个变成看多的人；stage 1..12。"""
    if stage <= 6:
        return person <= stage
    k = stage - 6  # 下跌段已经有 k 个人变成看空
    return person > k if fifo else person <= 6 - k


def panel(ax, fifo, title, note):
    for s in range(1, 13):
        for p in range(1, 7):
            ax.scatter(s, p, s=230, color=BULL if bullish(p, s, fifo) else BEAR,
                       edgecolor="white", linewidth=1.5, zorder=3)
    # 突出第5个人：泡沫段进场
    ax.add_patch(plt.Rectangle((0.5, 4.55), 12, 0.9, fill=False, ec="#222", lw=1.2, ls="--", zorder=2))
    out = 11 if fifo else 8
    # 圈出第5个人变回看空的那一段
    ax.scatter(out, 5, s=620, facecolor="none", edgecolor="#111", linewidth=2.0, zorder=4)
    ax.text(0.5, 6.55, "虚线框：泡沫段才进来的那个人。黑圈：" + note, ha="left", va="bottom", fontsize=10, color="#222")
    ax.axvline(6.5, color="#999", lw=0.8, ls=":")
    ax.set_xlim(0.4, 12.6)
    ax.set_ylim(0.4, 7.1)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(STAGES, fontsize=10)
    ax.set_yticks(range(1, 7))
    ax.set_yticklabels([f"第{i}个变看多的人" for i in range(1, 7)], fontsize=9)
    ax.set_title(title, fontsize=12, loc="left")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)


fig, axes = plt.subplots(2, 1, figsize=(11, 8.2))
panel(axes[0], False, "论文图2的画法：后进先出（最后进来的人最先走）",
      "按这张图，他在侥幸段就变看空、走了")
panel(axes[1], True, "建议的画法：先进先出（最早进来的人最先走）",
      "他到恐慌段才变看空、割掉，和老周朋友的故事一样")
fig.text(0.5, 0.01, "橙色＝看多，蓝色＝看空。两种画法每一段的人数完全一样，不一样的只是“谁先变”。",
         ha="center", fontsize=10, color="#444")
fig.tight_layout(rect=(0, 0.03, 1, 1))
out = Path(__file__).resolve().parent.parent / "notes" / "images" / "六个人谁先进谁先出.png"
fig.savefig(out, dpi=150)
print(out)
