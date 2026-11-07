"""H4 净值曲线和 H1 热度分组图。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import validate as V

plt.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei"]
plt.rcParams["axes.unicode_minus"] = False

df = V.monthly()
P, R = V.backtest(df)
nav = (1 + R).cumprod()
x = nav.index.to_timestamp()
fig, axes = plt.subplots(2, 1, figsize=(11, 7.2), gridspec_kw={"height_ratios": [3, 1.3]}, sharex=True)
ax = axes[0]
style = {"A": ("#222222", 2.2, "-"), "B": ("#2b6cb0", 1.6, "-"), "C1": ("#d4a017", 1.4, "--"),
         "C2": ("#7b3fa0", 1.4, "--"), "C": ("#c0392b", 2.0, "-")}
for k in ["A", "B", "C1", "C2", "C"]:
    c, lw, ls = style[k]
    ax.plot(x, nav[k], color=c, lw=lw, ls=ls, label=V.NAMES[k])
ax.set_yscale("log")
ax.set_ylabel("净值（2010年1月=1，对数刻度）")
ax.set_title("按事先定的规则回测：2010年1月到2026年9月，全市场指数，月度", loc="left", fontsize=12)
ax.legend(fontsize=9, loc="upper left", frameon=False)
ax.grid(alpha=0.25)
h = V.heat(df).loc[nav.index]
axes[1].fill_between(x, h, color="#c0392b", alpha=0.35, step="mid")
axes[1].axhline(0.8, color="#c0392b", lw=0.8, ls="--")
axes[1].axhline(0.2, color="#2b6cb0", lw=0.8, ls="--")
axes[1].set_ylim(0, 1)
axes[1].set_ylabel("热度（0–1）")
axes[1].set_title("热度：换手率和融资占比的历史分位（虚线：热 0.8、冷 0.2）", loc="left", fontsize=10)
fig.tight_layout()
fig.savefig(V.OUT / "validate_h4_nav.png", dpi=150)
print("ok")
