"""笔记六的图：两批标的放在一起，看方差比和“赢过简单跟势的比例”。另附事后统计。"""
from math import comb
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei"]
plt.rcParams["axes.unicode_minus"] = False
ROOT = Path(__file__).resolve().parent.parent
b1 = pd.read_csv(ROOT / "output" / "multi" / "cyclicality.csv").merge(
    pd.read_csv(ROOT / "output" / "multi" / "robustness_per_instrument.csv"), on=["名称", "类别"])
b1 = b1.rename(columns={"论文版胜跟势": "论文版胜跟势比例", "改进版胜跟势": "改进版胜跟势比例"})
b2 = pd.read_csv(ROOT / "output" / "multi2" / "batch2_results.csv")

fig, axes = plt.subplots(1, 2, figsize=(13, 5.4), sharey=True)
for ax, col, title in [(axes[0], "论文版胜跟势比例", "论文版（只在跌透以后进场）"),
                       (axes[1], "改进版胜跟势比例", "改进版（再加上“价格自己证明”）")]:
    ax.scatter(b1["方差比_2年"], b1[col], facecolor="none", edgecolor="#888", s=55, label="第一批（发现用）")
    ax.scatter(b2["方差比_2年"], b2[col], color="#c0392b" if "改进" in col else "#2b6cb0", s=45, label="第二批（验证用）")
    for _, r in b2.iterrows():
        ax.annotate(r["名称"], (r["方差比_2年"], r[col]), fontsize=7.5, xytext=(3, 3), textcoords="offset points", color="#333")
    r1 = np.corrcoef(b1["方差比_2年"], b1[col])[0, 1]
    r2 = np.corrcoef(b2["方差比_2年"], b2[col])[0, 1]
    ax.set_title(f"{title}\n相关：第一批 {r1:+.2f}，第二批 {r2:+.2f}", loc="left", fontsize=11)
    ax.axvline(1, color="#999", ls="--", lw=0.8)
    ax.axhline(0.5, color="#999", ls=":", lw=0.8)
    ax.set_xlabel("两年方差比（<1 像周期，>1 像趋势）")
axes[0].set_ylabel("27组参数里，比“简单跟势”更好的比例")
axes[0].legend(fontsize=9, frameon=False, loc="upper right")
fig.tight_layout()
fig.savefig(ROOT / "output" / "multi2" / "batch2_vs_batch1.png", dpi=150)

# 事后统计（不是事先定的）
allr = pd.concat([b1[["名称", "方差比_2年", "论文版胜跟势比例", "改进版胜跟势比例"]],
                  b2[["名称", "方差比_2年", "论文版胜跟势比例", "改进版胜跟势比例"]]], ignore_index=True)
for col in ["论文版胜跟势比例", "改进版胜跟势比例"]:
    for lab, sub in [("周期型(<1)", allr[allr["方差比_2年"] < 1]), ("趋势型(≥1)", allr[allr["方差比_2年"] >= 1])]:
        k, n = int((sub[col] >= 0.5).sum()), len(sub)
        print(f"{col} {lab}: {k}/{n} 个标的在过半参数下赢过跟势")
k, n = int((allr["改进版胜跟势比例"] >= 0.5).sum()), len(allr)
p = sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n
print(f"两批合计，改进版在过半参数下赢过跟势：{k}/{n}，二项检验单边p={p:.3f}")
print("ok")
