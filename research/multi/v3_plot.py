"""笔记七的图：34个标的等权组合（2016–2026，参数每年只用过去的数据挑），以及第三版的平均仓位。"""
import pickle
from math import comb

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import v3_walkforward as V

plt.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei"]
plt.rcParams["axes.unicode_minus"] = False
P = pd.read_csv(V.OUT / "portfolio_weekly.csv", index_col=0, parse_dates=True)
d = pickle.load(open(V.OUT / "oos.pkl", "rb"))
chosen = d["chosen"]["第三版"]

# 第三版每周的平均仓位（按每年挑出的参数重算目标仓位）
inst = V.load_all()
expo = {}
for name, w in inst.items():
    cycs = {th: V.cyc_series(w, th) for th in V.THETAS}
    parts = []
    for y, g in chosen.items():
        f = V.features(w, *g[:3])
        tgt = pd.Series(V.run(f, "v3", cycs[g[3]]), index=w.index).shift(1)
        parts.append(tgt[(tgt.index.year == y)])
    expo[name] = pd.concat(parts)
E = pd.DataFrame(expo)
E = E[E.index >= "2016-01-01"].mean(axis=1)
print("第三版平均仓位（34个标的平均）:", round(E.mean(), 3))

fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True, gridspec_kw={"height_ratios": [3, 1.4, 1.2]})
col = {"一直拿着": "#222222", "简单跟势": "#2b6cb0", "论文版": "#7b3fa0", "第三版": "#c0392b"}
for m in ["一直拿着", "简单跟势", "论文版", "第三版"]:
    nav = (1 + P[m].fillna(0)).cumprod()
    s = V.stats(P[m])
    axes[0].plot(nav.index, nav, color=col[m], lw=2.2 if m in ("第三版", "一直拿着") else 1.4,
                 label=f"{m}：年化 {s['年化']:.1%}，最大回撤 {s['最大回撤']:.1%}，年化÷回撤 {s['年化÷回撤']:.2f}")
    axes[1].plot(nav.index, nav / nav.cummax() - 1, color=col[m], lw=1.2)
axes[0].set_title("34个标的等权组合，2016–2026（每年的参数只用当年以前的数据挑）", loc="left", fontsize=12)
axes[0].legend(fontsize=9, frameon=False, loc="upper left")
axes[0].set_ylabel("净值")
axes[0].grid(alpha=0.25)
axes[1].set_ylabel("回撤")
axes[1].grid(alpha=0.25)
axes[2].fill_between(E.index, E, color="#c0392b", alpha=0.35, step="mid")
axes[2].set_ylabel("第三版平均仓位")
axes[2].set_ylim(0, 1)
axes[2].grid(alpha=0.25)
fig.tight_layout()
fig.savefig(V.OUT / "v3_portfolio.png", dpi=150)
k, n = 20, 34
print("20/34 的二项检验单边p:", round(sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n, 3))
