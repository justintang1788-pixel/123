"""把第四版回测的记录整理成一个 Excel 文件：research/output/v4/第四版回测记录.xlsx"""
import pickle

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from v4_walkforward import OUT

MAIN = ["一直拿着", "简单跟势", "第三版", "第四版"]
EXTRA = ["第四版＋目标20%", "第四版＋目标30%", "第四版＋目标50%", "第四版＋目标100%",
         "第四版＋最坏5%", "第四版＋最坏10%", "第四版·按圈挑参数", "第四版·泡沫用4周低点"]

NOTE = [
    ("这是什么", "《冬至理论》第四版规矩的回测记录。规矩、标的、成败标准都在跑之前写好，见 notes/11-第四版回测.md 第一部分。"),
    ("盖住未来", "2016–2026年，每年年初只用那一年以前的数据挑参数，再去跑那一年。所有标的用同一组参数（“按圈挑参数”那一栏除外）。"),
    ("执行", "周五收盘看信号，下周一开盘买卖；每次买卖收0.1%成本；空仓不算利息；期货按全额资金算，不加杠杆。"),
    ("只测了价格", "这次没有条件数据（产量、库存、存栏）。第四版里“观条件”的地方，都用价格代替；“以条件为准”这一条本身没有测到。"),
    ("汇总", "四条成败标准过没过；各种做法的等权组合。"),
    ("每个标的", "每个标的在每种做法下的年化、最大回撤、年化÷回撤（2016年起，或者从这个标的有满一年数据起）。"),
    ("每笔交易", "第四版主检验的每一笔：什么时候、因为什么进场，中间怎么加减，什么时候、因为什么走，赚亏多少。"
                 "“价格涨跌”是出场价比进场价；“对本标的资金的盈亏”算上了仓位大小和成本。"),
    ("每周记录", "第四版主检验，每个标的每一周：收盘价、所处阶段、周末定下的仓位、这周发生的事、这周盈亏、净值。"),
    ("每年参数", "每一年挑出来用的参数。"),
    ("每年收益", "各种做法的等权组合，每一年赚亏多少。"),
    ("信号", "每次出现“绝望”“价格自己证明”“泡沫”“兑现”信号之后，26周涨了还是跌了（默认参数，全部历史）。"),
    ("批次", "1、2批是以前用过的34个标的；3批是这次新加的，这次之前从没用过。"),
]


def autosize(ws, maxw=48):
    for col in ws.columns:
        L = max((len(str(c.value)) if c.value is not None else 0) for c in col[:300])
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(maxw, max(8, L * 1.6 + 2))


def pct(ws, cols, fmt="0.0%"):
    hdr = [c.value for c in ws[1]]
    for name in cols:
        if name in hdr:
            j = hdr.index(name) + 1
            for row in ws.iter_rows(min_row=2, min_col=j, max_col=j):
                for c in row:
                    c.number_format = fmt


def main():
    T = pd.read_csv(OUT / "per_instrument.csv")
    TR = pd.read_csv(OUT / "trades.csv")
    WL = pd.read_csv(OUT / "weekly_log.csv")
    C = pd.read_csv(OUT / "chosen_params.csv")
    S = pd.read_csv(OUT / "signals.csv")
    res = pickle.load(open(OUT / "result.pkl", "rb"))
    P = pd.read_csv(OUT / "portfolio_weekly_全部标的.csv", index_col=0, parse_dates=True)
    yr = ((1 + P).groupby(P.index.year).prod() - 1)[MAIN + EXTRA]
    yr.index.name = "年份"

    summ = []
    for label, d in res.items():
        for k in ["标准1", "标准2", "标准3", "标准4"]:
            summ.append({"范围": label, "标准": k, "过没过": "过" if d[k] else "没过"})
    summ = pd.DataFrame(summ)
    ports = []
    for label, d in res.items():
        ps = d["组合"].copy()
        ps.insert(0, "范围", label)
        ps.index.name = "做法"
        ports.append(ps.reset_index())
    ports = pd.concat(ports)

    cols_inst = ["标的", "代码", "批次", "大类", "起", "周数"]
    keep = cols_inst + [f"{m}_{k}" for m in MAIN + EXTRA for k in ["年化", "最大回撤", "年化÷回撤"]]
    T = T[[c for c in keep if c in T.columns]]

    path = OUT / "第四版回测记录.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        pd.DataFrame(NOTE, columns=["项目", "说明"]).to_excel(xw, sheet_name="说明", index=False)
        summ.to_excel(xw, sheet_name="汇总", index=False)
        ports.to_excel(xw, sheet_name="汇总", index=False, startrow=len(summ) + 3)
        T.to_excel(xw, sheet_name="每个标的", index=False)
        TR.to_excel(xw, sheet_name="每笔交易", index=False)
        WL.to_excel(xw, sheet_name="每周记录", index=False)
        C.to_excel(xw, sheet_name="每年参数", index=False)
        yr.reset_index().to_excel(xw, sheet_name="每年收益", index=False)
        S.to_excel(xw, sheet_name="信号", index=False)
        wb = xw.book
        head = PatternFill("solid", fgColor="2E4A72")
        for ws in wb.worksheets:
            for c in ws[1]:
                c.font, c.fill = Font(bold=True, color="FFFFFF"), head
                c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            ws.freeze_panes = "B2" if ws.title not in ("说明", "汇总") else "A2"
            autosize(ws)
        ws = wb["说明"]
        ws.column_dimensions["B"].width = 110
        for row in ws.iter_rows(min_row=2):
            row[1].alignment = Alignment(wrap_text=True, vertical="top")
        ws = wb["汇总"]
        r0 = len(summ) + 4
        for c in ws[r0]:
            c.font, c.fill = Font(bold=True, color="FFFFFF"), head
        for row in ws.iter_rows(min_row=r0 + 1, min_col=3, max_col=4):
            for c in row:
                c.number_format = "0.0%"
        pct(wb["每个标的"], [c for c in T.columns if c.endswith(("_年化", "_最大回撤"))])
        for c in [c for c in T.columns if c.endswith("÷回撤")]:
            pct(wb["每个标的"], [c], "0.00")
        pct(wb["每笔交易"], ["进场仓位", "最高仓位"], "0.00")
        pct(wb["每笔交易"], ["价格涨跌", "对本标的资金的盈亏", "持有中最大浮亏", "持有中最大浮盈"])
        pct(wb["每周记录"], ["这周盈亏"], "0.00%")
        pct(wb["每周记录"], ["周末定的仓位", "净值"], "0.000")
        pct(wb["每年收益"], list(yr.columns))
        pct(wb["信号"], ["之后26周涨跌", "这个标的平常涨的概率"])
        wb["每笔交易"].column_dimensions["K"].width = 70
    print("写好", path)


if __name__ == "__main__":
    main()
