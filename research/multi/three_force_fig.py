"""笔记十二的图：三个例子，价格上涂上遮住未来判断出来的阶段，下面是三股力的分数。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch

from three_force import OUT, STAGES, UNCLEAR

plt.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei"]
plt.rcParams["axes.unicode_minus"] = False
WARM = ["#F2D9A3", "#EEC07A", "#E7A35E", "#DD8248", "#C6603A", "#A3432F"]
COOL = ["#BACCE2", "#97AFD0", "#7895BE", "#5578AA", "#3E5F91", "#2E4A72"]
COL = dict(zip(STAGES, WARM + COOL))
COL[UNCLEAR] = "#DDDDDD"
INK, GRAY = "#2B2B2B", "#7A7A7A"
EXAMPLES = ["上证指数", "螺纹钢", "牧原股份"]


def main():
    C = pd.read_csv(OUT / "census.csv", parse_dates=["月底"])
    fig, axes = plt.subplots(len(EXAMPLES) * 2, 1, figsize=(12, 4.2 * len(EXAMPLES)),
                             gridspec_kw={"height_ratios": [2.2, 1] * len(EXAMPLES)})
    for k, name in enumerate(EXAMPLES):
        d = C[(C["标的"] == name) & (C["月底"] >= "2012-01-01")].set_index("月底")
        ax, bx = axes[2 * k], axes[2 * k + 1]
        for t, st in d["阶段"].items():
            if isinstance(st, str):
                ax.axvspan(t - pd.offsets.MonthBegin(1), t, color=COL[st], lw=0, alpha=0.9)
        ax.plot(d.index, d["收盘"], color=INK, lw=1.4)
        ax.set_yscale("log")
        ax.set_title(f"{name}：价格（对数刻度），底色是每个月底只用当时数据判断的阶段", loc="left", fontsize=11, color=INK)
        for lab, col, c2 in [("条件", "条件分", "#3E7D4F"), ("时机", "时机分", "#C6603A"), ("取舍", "取舍分", "#2E4A72")]:
            bx.plot(d.index, d[col], lw=1.3, color=c2, label=lab)
        bx.axhline(0, color=GRAY, lw=0.7, ls=":")
        bx.set_ylabel("分数", fontsize=9)
        bx.legend(ncol=3, frameon=False, fontsize=9, loc="upper left")
        for a in (ax, bx):
            a.spines[["top", "right"]].set_visible(False)
            a.tick_params(labelsize=9)
            a.set_xlim(d.index[0] - pd.offsets.MonthBegin(1), d.index[-1])
    handles = [Patch(color=COL[s], label=s) for s in STAGES + [UNCLEAR]]
    fig.legend(handles=handles, ncol=13, loc="lower center", frameon=False, fontsize=9, bbox_to_anchor=(0.5, 0.0))
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT / "三股力阶段示例.png", dpi=170)
    print("图已存")


if __name__ == "__main__":
    main()
