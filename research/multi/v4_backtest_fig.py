"""第四版回测的图：等权组合的净值和回撤（全部标的、第三批新标的）。存到 research/output/v4/ 和 paper/images_v4/。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from v4_walkforward import OUT, ROOT

plt.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei"]
plt.rcParams["axes.unicode_minus"] = False
RED, BLUE, GOLD, GRAY, INK = "#A3432F", "#2E4A72", "#B08D57", "#7A7A7A", "#2B2B2B"
STY = {"一直拿着": (GRAY, 1.3, "-"), "简单跟势": (GOLD, 1.3, "-"), "第四版": (RED, 2.2, "-")}


def main():
    fig, axes = plt.subplots(2, 2, figsize=(12, 6.6), gridspec_kw={"height_ratios": [2.2, 1]}, sharex="col")
    for j, (label, title) in enumerate([("全部标的", "全部标的"), ("第三批新标的", "这次新加的标的（之前从没用过）")]):
        P = pd.read_csv(OUT / f"portfolio_weekly_{label}.csv", index_col=0, parse_dates=True)
        n = pd.read_csv(OUT / "per_instrument.csv")
        n = len(n) if label == "全部标的" else int((n["批次"] == 3).sum())
        ax, bx = axes[0, j], axes[1, j]
        for m, (c, lw, ls) in STY.items():
            nav = (1 + P[m]).cumprod()
            dd = nav / nav.cummax() - 1
            ax.plot(nav.index, nav, color=c, lw=lw, ls=ls, label=m)
            bx.plot(dd.index, dd * 100, color=c, lw=lw, ls=ls)
            ax.text(nav.index[-1], nav.iloc[-1], f" {nav.iloc[-1]:.2f}", color=c, fontsize=9.5, va="center")
        ax.set_title(f"{title}，{n}个，等权", fontsize=12, color=INK, loc="left")
        ax.axhline(1, color=GRAY, lw=0.6, ls=":")
        ax.set_ylabel("净值（2016年初=1）", fontsize=10)
        bx.set_ylabel("离最高点（%）", fontsize=10)
        for a in (ax, bx):
            a.spines[["top", "right"]].set_visible(False)
            a.tick_params(labelsize=9)
        if j == 0:
            ax.legend(frameon=False, fontsize=10, loc="upper left")
    fig.tight_layout()
    fig.savefig(OUT / "v4_portfolio.png", dpi=200)
    img = ROOT.parent / "paper" / "images_v4"
    fig.savefig(img / "图6-第四版回测.png", dpi=200)
    print("图已存")


if __name__ == "__main__":
    main()
