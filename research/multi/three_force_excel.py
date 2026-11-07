"""笔记十二的记录整理成 Excel：research/output/three_force/三股力盲测记录.xlsx"""
import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from three_force import OUT, STAGES, UNCLEAR

NOTE = [
    ("这是什么", "用冬至理论自己的办法判断阶段：先分类，每一类用条件、时机、取舍三股力的正反面判断阶段。随机抽“某个标的、某个月底”，"
               "只用那一天以前看得到的数据判断，再揭开之后的行情打分。规矩在跑之前写好，见 notes/12。"),
    ("三类", "A股大盘（6个指数）、工业品期货（27个）、A股个股（65只，分七组）。生猪、中药材没有长历史的条件数据，这次没测。"),
    ("遮住未来", "宏观数据晚一个月才用；公司业绩、股东户数按公告日；价格、成交、持仓、融资余额用到当月最后一天。"
               "每一道题都把数据切到那一天，从头重算。"),
    ("每道题", "随机抽的题：三股力的分数（和自己历史比的高低）和方向（+1往上，-1往下）、判断的阶段、之后3/6/12个月涨跌、"
              "只看价格的判断、事后回头观的阶段、对没对。"),
    ("每个月", "每个标的每个月都算一遍的结果（不抽），用来核对和画图。"),
    ("每个阶段", "随机抽的题里，判断为每个阶段之后的平均涨跌。"),
    ("买卖", "照火候表按阶段定仓位，每个月的仓位和盈亏。"),
    ("对没对", "判断在上半圈（绝望到兑现），之后6个月涨了算对；判断在下半圈（幻想到衰竭），之后6个月跌了算对。"
              "观不清的时候以条件为准。"),
]


def style(ws, head):
    for c in ws[1]:
        c.font, c.fill = Font(bold=True, color="FFFFFF"), head
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.freeze_panes = "A2"
    for col in ws.columns:
        L = max((len(str(c.value)) if c.value is not None else 0) for c in col[:200])
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(40, max(8, L * 1.5 + 2))


def main():
    S = pd.read_csv(OUT / "samples.csv")
    C = pd.read_csv(OUT / "census.csv")
    TM = pd.read_csv(OUT / "trading_monthly.csv")
    log = (OUT / "run.log").read_text(encoding="utf-8").splitlines()
    tab = (S.groupby(["类别", "盲测阶段"]).agg(题数=("标的", "size"), 之后3个月平均=("之后3个月", "mean"),
                                         之后6个月平均=("之后6个月", "mean"), 之后12个月平均=("之后12个月", "mean"),
                                         之后6个月涨的比例=("之后6个月", lambda x: (x > 0).mean())).reset_index())
    order = {s: i for i, s in enumerate(STAGES + [UNCLEAR])}
    tab = tab.sort_values(["类别", "盲测阶段"], key=lambda x: x.map(order) if x.name == "盲测阶段" else x)
    cols = ["标的", "类别", "组", "月底", "条件分", "条件方向", "时机分", "时机方向", "取舍分", "取舍方向", "盲测阶段",
            "盲测三样判断", "只看价格", "之后3个月", "之后6个月", "之后12个月", "三样对了", "只看价格对了", "事后阶段", "和事后差几段"]
    path = OUT / "三股力盲测记录.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        pd.DataFrame(NOTE, columns=["项目", "说明"]).to_excel(xw, sheet_name="说明", index=False)
        pd.DataFrame({"运行记录": log}).to_excel(xw, sheet_name="汇总", index=False)
        S[cols].to_excel(xw, sheet_name="每道题", index=False)
        tab.to_excel(xw, sheet_name="每个阶段", index=False)
        C.to_excel(xw, sheet_name="每个月", index=False)
        TM.to_excel(xw, sheet_name="买卖", index=False)
        head = PatternFill("solid", fgColor="2E4A72")
        for ws in xw.book.worksheets:
            style(ws, head)
        xw.book["说明"].column_dimensions["B"].width = 110
        for row in xw.book["说明"].iter_rows(min_row=2):
            row[1].alignment = Alignment(wrap_text=True, vertical="top")
        xw.book["汇总"].column_dimensions["A"].width = 160
    print("写好", path)


if __name__ == "__main__":
    main()
