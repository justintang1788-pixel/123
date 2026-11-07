"""第三版论文用图，配色沿用第二版。"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Wedge, Rectangle, FancyBboxPatch

plt.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei"]
plt.rcParams["axes.unicode_minus"] = False
ROOT = Path(__file__).resolve().parent.parent.parent
IMG = ROOT / "paper" / "images_v3"
STAGES = ["绝望", "怀疑", "犹豫", "大众共识", "泡沫", "兑现", "幻想", "侥幸", "瓦解", "麻木", "恐慌", "衰竭"]
WARM = ["#F2D9A3", "#EEC07A", "#E7A35E", "#DD8248", "#C6603A", "#A3432F"]
COOL = ["#BACCE2", "#97AFD0", "#7895BE", "#5578AA", "#3E5F91", "#2E4A72"]
COL = WARM + COOL
RED, BLUE, GOLD, GRAY, INK = "#A3432F", "#2E4A72", "#B08D57", "#7A7A7A", "#2B2B2B"
BULL, BEAR = "#C8603A", "#5B7DAE"


def fig_people():
    fig, ax = plt.subplots(figsize=(11, 6.2))
    for s in range(12):
        ax.add_patch(Rectangle((s + 0.5, 0.2), 1, 7.6, color=COL[s], alpha=0.10, lw=0))
    ratios = ["一比五", "二比四", "三比三", "四比二", "五比一", "六比零", "五比一", "四比二", "三比三", "二比四", "一比五", "零比六"]
    for s in range(1, 13):
        for p in range(1, 7):
            bull = (p <= s) if s <= 6 else (p > s - 6)
            ax.scatter(s, p, s=300, color=BULL if bull else BEAR, edgecolor="white", lw=1.8, zorder=3)
        ax.text(s, 6.75, ratios[s - 1], ha="center", fontsize=10, color=GRAY)
        ax.text(s, 0.35, STAGES[s - 1] if s != 4 else "大众\n共识", ha="center", va="center", fontsize=11.5,
                color=INK, fontweight="bold")
    ax.axvline(6.5, color=GRAY, lw=0.8, ls=":")
    types = ["做这一行的人", "老手", "专业的人", "老股民", "跟风、借钱的", "外行"]
    for p, t in enumerate(types, 1):
        ax.text(0.35, p, t, ha="right", va="center", fontsize=10, color=INK)
    ax.text(0.35, 7.25, "从最懂行（下）\n到最外行（上）", ha="right", va="center", fontsize=8.5, color=GRAY)
    ax.scatter([7, 11], [1, 6], s=620, facecolor="none", edgecolor=BLUE, lw=1.6, zorder=4)
    ax.annotate("最懂行的人最先走", xy=(7.18, 1.18), xytext=(7.4, 1.5), fontsize=10.5, color=BLUE, va="center",
                arrowprops=dict(arrowstyle="-", color=BLUE, lw=1.0))
    ax.annotate("最晚进来的人最后割", xy=(10.82, 5.82), xytext=(10.6, 5.5), fontsize=10.5, color=BLUE, va="center",
                ha="right", arrowprops=dict(arrowstyle="-", color=BLUE, lw=1.0))
    ax.annotate("六个人都买了\n没有第七个人来接", xy=(6, 6.2), xytext=(4.6, 7.4), fontsize=10.5, color=RED,
                arrowprops=dict(arrowstyle="-", color=RED, lw=1.1), ha="center")
    ax.scatter([], [], s=120, color=BULL, label="钱在里面（看多）")
    ax.scatter([], [], s=120, color=BEAR, label="钱在外面（看空）")
    ax.legend(loc="upper left", bbox_to_anchor=(-0.12, 1.12), ncol=2, frameon=False, fontsize=10)
    ax.set_xlim(-1.3, 12.6)
    ax.set_ylim(-0.1, 8.0)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(IMG / "图2-屋里六个人.png", dpi=200)


def fig_wheel(path, cover=False):
    fig, ax = plt.subplots(figsize=(7.6, 7.6))
    R, w = 1.0, 0.36
    for k in range(12):
        if k < 6:
            a1, a2 = 270 - 30 * (k + 1), 270 - 30 * k
        else:
            j = k - 6
            a1, a2 = 90 - 30 * (j + 1), 90 - 30 * j
        ax.add_patch(Wedge((0, 0), R, a1, a2, width=w, facecolor=COL[k], edgecolor="white", lw=3))
        mid = np.deg2rad((a1 + a2) / 2)
        r = R - w / 2
        name = STAGES[k] if STAGES[k] != "大众共识" else "大众\n共识"
        dark = k in (3, 4, 5, 9, 10, 11)
        ax.text(r * np.cos(mid), r * np.sin(mid), name, ha="center", va="center", fontsize=13 if k != 3 else 11,
                fontweight="bold", color="white" if dark else INK)
        num = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"][k]
        ax.text(1.14 * np.cos(mid), 1.14 * np.sin(mid), num, ha="center", va="center", fontsize=9, color=GRAY)
    # 价格最高、最低
    ax.plot([0, 0], [R - w - 0.02, R + 0.06], color=RED, lw=2.2)
    ax.plot([0, 0], [-(R - w - 0.02), -(R + 0.06)], color=BLUE, lw=2.2)
    ax.text(0, R + 0.10, "价格最高", ha="center", va="bottom", fontsize=11, color=RED, fontweight="bold")
    ax.text(0, -(R + 0.10), "价格最低", ha="center", va="top", fontsize=11, color=BLUE, fontweight="bold")
    if not cover:
        marks = [(105, "夏至·太阳要走", RED), (75, "三伏·感觉最热", RED),
                 (285, "冬至·太阳回头", BLUE), (255, "三九·感觉最冷", BLUE)]
        for ang, lab, c in marks:
            t = np.deg2rad(ang)
            ax.scatter(1.0 * np.cos(t), 1.0 * np.sin(t), s=60, color="white", edgecolor=c, lw=2, zorder=5)
            x, y = 1.36 * np.cos(t), 1.36 * np.sin(t)
            ax.text(x + (-0.12 if np.cos(t) < 0 else 0.12), y, lab, ha="right" if np.cos(t) < 0 else "left",
                    va="center", fontsize=10.5, color=c)
    ax.text(0, 0.17, "冬至理论", ha="center", va="center", fontsize=24, color=BLUE, fontweight="bold")
    ax.text(0, 0.0, "十二阶段循环", ha="center", va="center", fontsize=11, color=GRAY)
    ax.text(0, -0.16, "最冷的那天，太阳已经回头", ha="center", va="center", fontsize=9.5, color=BLUE)
    ax.text(0, -0.28, "最热的那天，太阳已经要走", ha="center", va="center", fontsize=9.5, color=RED)
    ax.annotate("", xy=(-1.22, 0.55), xytext=(-1.22, -0.55), arrowprops=dict(arrowstyle="->", color="#C86A3A", lw=1.6))
    ax.annotate("", xy=(1.22, -0.55), xytext=(1.22, 0.55), arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.6))
    ax.text(-1.34, 0, "上\n涨\n六\n阶\n段", ha="center", va="center", fontsize=10.5, color="#C86A3A")
    ax.text(1.34, 0, "下\n跌\n六\n阶\n段", ha="center", va="center", fontsize=10.5, color=BLUE)
    lim = 1.85 if not cover else 1.55
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-1.55, 1.55)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=200)


def fig_path():
    x = np.linspace(0, 12, 1200)
    base = np.interp(x, [0, 0.4, 1, 2, 3, 4, 5, 5.55, 5.8, 6.0, 6.3, 7, 7.6, 8, 9, 10, 11, 11.6, 12],
                     [1.05, 1.0, 1.15, 1.35, 1.75, 2.4, 3.6, 4.3, 4.0, 4.38, 3.5, 3.3, 3.55, 2.9, 2.35, 1.95, 1.4, 1.05, 1.02])
    rng = np.random.default_rng(3)
    noise = np.convolve(rng.normal(0, 0.035, len(x)), np.ones(25) / 25, mode="same")
    y = base + noise
    fig, ax = plt.subplots(figsize=(11, 5.6))
    for s in range(12):
        ax.add_patch(Rectangle((s, 0.0), 1, 5.2, color=COL[s], alpha=0.16, lw=0))
        ax.text(s + 0.5, 0.42, STAGES[s] if s != 3 else "大众\n共识", ha="center", va="center", fontsize=11.5,
                fontweight="bold", color=INK)
        ax.text(s + 0.5, 0.08, ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"][s],
                ha="center", fontsize=9, color=GRAY)
    ax.plot(x, y, color=BLUE, lw=2.6)
    ax.axvline(6, color=RED, lw=1, ls="--")
    def mark(xx, txt, c, dy, ha="center"):
        yy = np.interp(xx, x, y)
        ax.scatter(xx, yy, s=70, color="white", edgecolor=c, lw=2.2, zorder=5)
        ax.annotate(txt, xy=(xx, yy), xytext=(xx, yy + dy), ha=ha, fontsize=10.5, color=c,
                    arrowprops=dict(arrowstyle="-", color=c, lw=1))
    mark(5.55, "① 太阳要走\n（后来的人进完了）", RED, 0.55, "right")
    mark(6.0, "② 价格最高", RED, 0.45, "left")
    mark(7.6, "③ 感觉最热\n（跌了还在加仓）", RED, 0.9)
    mark(11.6, "① 太阳回头\n（想卖的卖完了）", BLUE, 0.9)
    mark(0.4, "② 价格最低", BLUE, 0.7, "left")
    mark(1.0, "③ 感觉最冷\n（涨了没人信）", BLUE, 1.25, "left")
    ax.text(3, 5.38, "上涨六阶段", ha="center", fontsize=13, color=RED, fontweight="bold")
    ax.text(9, 5.35, "下跌六阶段", ha="center", fontsize=13, color=BLUE, fontweight="bold")
    ax.set_xlim(0, 12)
    ax.set_ylim(0.0, 5.6)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_xlabel("时间（各段长短不一，图中等宽只为好看）", color=GRAY, fontsize=10)
    ax.set_ylabel("价格（示意）", color=GRAY, fontsize=10)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.tight_layout()
    fig.savefig(IMG / "图4-价格走势与三个时刻.png", dpi=200)


def weekly_close(sub, code):
    d = pd.read_csv(ROOT / "research" / "data" / sub / f"{code}.csv", parse_dates=["date"]).set_index("date")
    return d["close"].resample("W-FRI").last().dropna()


def fig_types():
    egg = weekly_close("multi2", "JD0")
    mt = weekly_close("multi", "sh600519")
    mt = mt[mt.index >= egg.index[0]]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, s, title, c in [(axes[0], egg, "鸡蛋期货：两年方差比 0.18，周期型\n涨多了会跌回来，在一个区间里来回", BLUE),
                            (axes[1], mt, "贵州茅台：两年方差比 2.16，趋势型\n跌下来过一阵又创新高", RED)]:
        ax.plot(s.index, s / s.iloc[0], color=c, lw=1.6)
        ax.set_yscale("log")
        ax.set_title(title, loc="left", fontsize=11, color=INK)
        ax.grid(alpha=0.25)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    axes[0].set_ylabel("相对起点（对数刻度）", color=GRAY)
    fig.tight_layout()
    fig.savefig(IMG / "图5-周期型和趋势型.png", dpi=200)


def fig_result():
    P = pd.read_csv(ROOT / "research" / "output" / "v3" / "portfolio_weekly.csv", index_col=0, parse_dates=True)
    lab = {"一直拿着": ("一直拿着", INK, 2.0), "简单跟势": ("简单跟势", "#8AA1C1", 1.5),
           "论文版": ("第二版规矩", GRAY, 1.5), "第三版": ("第三版规矩", RED, 2.4)}
    fig, ax = plt.subplots(figsize=(11, 4.8))
    for k, (name, c, lw) in lab.items():
        r = P[k].fillna(0)
        nav = (1 + r).cumprod()
        cagr = nav.iloc[-1] ** (52 / len(r)) - 1
        mdd = (nav / nav.cummax() - 1).min()
        ax.plot(nav.index, nav, color=c, lw=lw, label=f"{name}：年化 {cagr:.1%}，最大回撤 {mdd:.1%}")
    ax.legend(frameon=False, fontsize=10, loc="upper left")
    ax.set_ylabel("净值（2016年初=1）", color=GRAY)
    ax.grid(alpha=0.25)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.tight_layout()
    fig.savefig(IMG / "图6-盖住未来的检验.png", dpi=200)


if __name__ == "__main__":
    fig_people()
    fig_wheel(IMG / "图3-十二阶段循环图.png")
    fig_wheel(IMG / "封面.png", cover=True)
    fig_path()
    fig_types()
    fig_result()
    print("ok")
