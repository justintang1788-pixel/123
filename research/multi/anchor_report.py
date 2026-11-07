"""笔记十四：整理成 Excel，并画论文用图（各类东西里，哪一股力判断上下半圈最准）。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from anchor_test import OUT, ROOT

plt.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei"]
plt.rcParams["axes.unicode_minus"] = False
RED, BLUE, GOLD, GRAY, INK, GREEN = "#A3432F", "#2E4A72", "#B08D57", "#BBBBBB", "#2B2B2B", "#3E7D4F"

NOTE = [
    ("这是什么", "检验“先认锚，再定谁当家”：硬锚（期货）看条件，软锚（A股指数）看取舍，未来锚（个股）看说了算的人。"
               "随机抽题、遮住未来，只用笔记十二没用过的标的算成败。规矩在跑之前写好，见 notes/14。"),
    ("标的", "7个新期货；23个新A股指数；从全部融资融券标的里随机抽的100只新股票（实际进题99只）。"),
    ("对没对", "判断在上半圈、之后6个月涨了，算对；判断在下半圈、之后6个月跌了，算对。1表示对，0表示错。"),
    ("每道题", "2100道随机题：每一股力的方向（+1往上，-1往下）、当家那股力的判断、之后3/6/12个月涨跌、各种判断对没对。"),
    ("汇总", "运行记录原文。"),
]


def excel():
    S = pd.read_csv(OUT / "samples.csv")
    log = (OUT / "run.log").read_text(encoding="utf-8").splitlines()
    keep = ["标的", "锚", "组", "月底", "当家判断", "只看条件", "只看时机", "只看取舍", "只看说了算的人", "只看价格",
            "之后3个月", "之后6个月", "之后12个月", "当家判断对了", "只看条件对了", "只看时机对了", "只看取舍对了",
            "只看说了算的人对了", "只看价格对了"]
    path = OUT / "第二次盲测记录.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        pd.DataFrame(NOTE, columns=["项目", "说明"]).to_excel(xw, sheet_name="说明", index=False)
        pd.DataFrame({"运行记录": log}).to_excel(xw, sheet_name="汇总", index=False)
        S[[c for c in keep if c in S]].to_excel(xw, sheet_name="每道题", index=False)
        head = PatternFill("solid", fgColor="2E4A72")
        for ws in xw.book.worksheets:
            for c in ws[1]:
                c.font, c.fill = Font(bold=True, color="FFFFFF"), head
                c.alignment = Alignment(horizontal="center", wrap_text=True)
            ws.freeze_panes = "A2"
            for col in ws.columns:
                L = max((len(str(c.value)) if c.value is not None else 0) for c in col[:200])
                ws.column_dimensions[get_column_letter(col[0].column)].width = min(40, max(8, L * 1.5 + 2))
        xw.book["说明"].column_dimensions["B"].width = 110
        xw.book["汇总"].column_dimensions["A"].width = 150
    print("写好", path)


def fig():
    S = pd.read_csv(OUT / "samples.csv")
    groups = [("硬锚：7个期货", "硬锚", "条件"), ("软锚：23个A股指数", "软锚", "取舍"), ("未来锚：99只随机股票", "未来锚", "说了算的人")]
    bars = [("条件", "只看条件对了", GREEN), ("时机", "只看时机对了", GOLD), ("取舍", "只看取舍对了", BLUE),
            ("说了算的人", "只看说了算的人对了", RED), ("只看价格", "只看价格对了", GRAY)]
    fig, ax = plt.subplots(figsize=(11, 4.8))
    w = 0.16
    for gi, (lab, anc, boss) in enumerate(groups):
        s = S[S["锚"] == anc]
        for bi, (bn, col, c) in enumerate(bars):
            if col not in s or s[col].isna().all():
                continue
            v = np.nanmean(s[col]) * 100
            x = gi + (bi - 2) * w
            edge = INK if bn == boss else "none"
            ax.bar(x, v, w * 0.92, color=c, edgecolor=edge, linewidth=1.8 if bn == boss else 0)
            ax.text(x, v + 0.4, f"{v:.0f}", ha="center", fontsize=9, color=INK)
    ax.axhline(50, color=INK, lw=0.8, ls=":")
    ax.text(2.55, 50.3, "瞎猜", fontsize=9, color=INK)
    ax.set_xticks(range(3))
    ax.set_xticklabels([g[0] for g in groups], fontsize=11)
    ax.set_ylim(40, 66)
    ax.set_ylabel("分对上下半圈的比例（%）", fontsize=10)
    from matplotlib.patches import Patch
    hs = [Patch(color=c, label=bn) for bn, _, c in bars] + [Patch(facecolor="white", edgecolor=INK, linewidth=1.8, label="当家的那股力")]
    ax.legend(handles=hs, ncol=6, frameon=False, fontsize=10, loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "谁当家.png", dpi=200)
    fig.savefig(ROOT.parent / "paper" / "images_v5" / "图7-谁当家.png", dpi=200)
    print("图已存")


if __name__ == "__main__":
    excel()
    fig()
