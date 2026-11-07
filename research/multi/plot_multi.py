"""每个标的：价格、冬至改进版的持仓、四种信号；以及周期性和效果的散点图。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import theory_bt as T

plt.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei"]
plt.rcParams["axes.unicode_minus"] = False
codes = list(T.META["代码"])
bt = pd.read_csv(T.OUT / "backtest.csv")

fig, axes = plt.subplots(5, 2, figsize=(13, 15))
for ax, c in zip(axes.flat, codes):
    w = T.weekly(c); f = T.features(w)
    s0 = f["ma"].first_valid_index()
    w2, f2 = w.loc[s0:], f.loc[s0:]
    pos, stage, ev = T.run_theory(w2, f2, True)
    ax.plot(w2.index, w2["close"], color="#222", lw=1.0)
    ax.set_yscale("log")
    y0, y1 = w2["close"].min() * 0.9, w2["close"].max() * 1.1
    ax.fill_between(w2.index, y0, y1, where=pos.values > 0, color="#d4a017", alpha=0.18, step="post", lw=0)
    mk = {"进场": ("^", "#2f855a"), "泡沫": ("o", "#c0392b"), "兑现": ("v", "#e67e22"), "止损": ("x", "#555")}
    for t, k in ev:
        key = next(x for x in mk if k.startswith(x))
        m, col = mk[key]
        ax.scatter(t, w2.loc[t, "close"], marker=m, color=col, s=28, zorder=3)
    r = bt[(bt["代码"] == c)].set_index("做法")
    ax.set_title(f"{T.NAME[c]}（{T.KIND[c]}）  年化÷回撤：拿着 {r.loc['一直拿着','年化÷回撤']:.2f}，"
                 f"跟势 {r.loc['简单跟势','年化÷回撤']:.2f}，冬至改进 {r.loc['冬至·改进版','年化÷回撤']:.2f}",
                 fontsize=9.5, loc="left")
    ax.set_ylim(y0, y1)
    ax.tick_params(labelsize=8)
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
handles = [plt.Line2D([], [], color="#222", lw=1, label="收盘价（周线，对数）"),
           plt.Rectangle((0, 0), 1, 1, color="#d4a017", alpha=0.3, label="冬至·改进版持仓"),
           plt.Line2D([], [], marker="^", ls="", color="#2f855a", label="进场"),
           plt.Line2D([], [], marker="o", ls="", color="#c0392b", label="泡沫·卖一半"),
           plt.Line2D([], [], marker="v", ls="", color="#e67e22", label="兑现·再卖一半"),
           plt.Line2D([], [], marker="x", ls="", color="#555", label="止损离场")]
fig.legend(handles=handles, loc="lower center", ncol=6, fontsize=10, frameon=False)
fig.tight_layout(rect=(0, 0.025, 1, 1))
fig.savefig(T.OUT / "multi_backtest.png", dpi=130)

per = pd.read_csv(T.OUT / "robustness_per_instrument.csv")
cyc = pd.read_csv(T.OUT / "cyclicality.csv")
m = cyc.merge(per, on=["名称", "类别"])
fig, ax = plt.subplots(figsize=(8.5, 5.8))
ax.scatter(m["方差比_2年"], m["论文版胜跟势"], color="#2b6cb0", s=60, label="论文版（只在跌透后进场）")
ax.scatter(m["方差比_2年"], m["改进版胜跟势"], color="#c0392b", s=60, marker="s", label="改进版（加上“价格自己证明”）")
for _, r in m.iterrows():
    dy = -10 if r["名称"] != "长江电力" else 6
    ax.annotate(r["名称"], (r["方差比_2年"], r["论文版胜跟势"]), fontsize=8, color="#2b6cb0", xytext=(4, dy), textcoords="offset points")
    ax.annotate(r["名称"], (r["方差比_2年"], r["改进版胜跟势"]), fontsize=8, color="#c0392b", xytext=(4, 4), textcoords="offset points")
ax.axvline(1, color="#999", ls="--", lw=0.8)
ax.axhline(0.5, color="#999", ls=":", lw=0.8)
ax.set_xlabel("两年方差比（<1：涨多了会跌回来，像有周期；>1：涨了还接着涨，像有趋势）")
ax.set_ylabel("27组参数里，比“简单跟势”更好的比例")
ax.set_title("周期型标的适合论文版，趋势型标的适合改进版", loc="left")
ax.legend(fontsize=9, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2)
fig.tight_layout()
fig.savefig(T.OUT / "cyclicality_vs_theory.png", dpi=150)
print("ok")
