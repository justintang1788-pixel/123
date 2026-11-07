"""第四版用图：屋里的六个人（三股力的正反面）、圈的大小。配色沿用第二版。"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Rectangle

from v3_paper_figs import COL, STAGES, RED, BLUE, GRAY, INK, BULL, BEAR, weekly_close

plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "WenQuanYi Zen Hei"]
plt.rcParams["axes.unicode_minus"] = False
IMG = Path(__file__).resolve().parent.parent.parent / "paper" / "images_v4"


def fig_forces():
    fig, ax = plt.subplots(figsize=(11.5, 6.4))
    for s in range(12):
        ax.add_patch(Rectangle((s + 0.5, 0.25), 1, 6.55, color=COL[s], alpha=0.10, lw=0))
    ratios = ["一比五", "二比四", "三比三", "四比二", "五比一", "六比零", "五比一", "四比二", "三比三", "二比四", "一比五", "零比六"]
    for s in range(1, 13):
        for p in range(1, 7):
            bull = (p <= s) if s <= 6 else (p > s - 6)
            ax.scatter(s, p, s=300, color=BULL if bull else BEAR, edgecolor="white", lw=1.8, zorder=3)
        ax.text(s, 6.6, ratios[s - 1], ha="center", fontsize=10, color=GRAY)
        ax.text(s, 0.4, STAGES[s - 1] if s != 4 else "大众\n共识", ha="center", va="center", fontsize=11.5,
                color=INK, fontweight="bold")
    ax.axvline(6.5, color=GRAY, lw=0.8, ls=":")
    for y0, name, c in [(1.5, "条件\n（地）", "#8a6d3b"), (3.5, "时机\n（天）", BLUE), (5.5, "人性\n（人）", RED)]:
        ax.text(0.05, y0, name, ha="center", va="center", fontsize=11.5, color=c, fontweight="bold")
        ax.plot([0.42, 0.42], [y0 - 0.85, y0 + 0.85], color=c, lw=2)
    ax.annotate("条件最先转", xy=(1, 1), xytext=(1.6, 1.5), fontsize=10.5, color="#8a6d3b", va="center",
                arrowprops=dict(arrowstyle="-", color="#8a6d3b", lw=1))
    ax.scatter([6, 7], [6, 1], s=640, facecolor="none", edgecolor=[RED, BLUE], lw=1.8, zorder=4)
    ax.annotate("人性最后走到头", xy=(5.82, 6.12), xytext=(4.6, 7.2), fontsize=10.5, color=RED, ha="center",
                arrowprops=dict(arrowstyle="-", color=RED, lw=1))
    ax.annotate("这一刻，条件已经转身", xy=(7.18, 1.18), xytext=(7.4, 1.55), fontsize=10.5, color=BLUE, va="center",
                arrowprops=dict(arrowstyle="-", color=BLUE, lw=1))
    ax.scatter([], [], s=120, color=BULL, label="站在涨的一边（正面）")
    ax.scatter([], [], s=120, color=BEAR, label="站在跌的一边（反面）")
    ax.legend(loc="upper left", bbox_to_anchor=(-0.04, 1.13), ncol=2, frameon=False, fontsize=10)
    ax.set_xlim(-0.5, 12.6)
    ax.set_ylim(0.0, 7.8)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(IMG / "图2-屋里六个人.png", dpi=200)


def fig_circles():
    egg = weekly_close("multi2", "JD0")
    mt = weekly_close("multi", "sh600519")
    mt = mt[mt.index >= egg.index[0]]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, s, title, c in [(axes[0], egg, "鸡蛋期货：圈小，两三年就转一圈", BLUE),
                            (axes[1], mt, "贵州茅台：圈大，这些年还走在它的大圈里", RED)]:
        ax.plot(s.index, s / s.iloc[0], color=c, lw=1.6)
        ax.set_yscale("log")
        ax.set_title(title, loc="left", fontsize=11.5, color=INK)
        ax.grid(alpha=0.25)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    axes[0].set_ylabel("相对起点（对数刻度）", color=GRAY)
    fig.tight_layout()
    fig.savefig(IMG / "图5-圈的大小.png", dpi=200)


if __name__ == "__main__":
    fig_forces()
    fig_circles()
    print("ok")
