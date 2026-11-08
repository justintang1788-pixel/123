"""冬至理论 · 阶段计算小工具

用法：
    python3 stage_tool.py 数据.csv [--anchor 实物|政策和钱|将来的钱] [--freq M|W]
                          [--lag-cond 1] [--lag-q 0] [--show 12] [--out 结果.csv]

数据.csv 的列：
    date        日期（必须）
    close       收盘价（必须）
    volume      成交量（可选）
    条件_xxx    条件这股力的数，越大对价格越好（比如 PMI、需求、利润）
    条件反_xxx  条件这股力的数，越大对价格越坏（比如 库存、产量、母猪存栏）
    取舍_xxx    说了算的人的动作，越大越“贪”、越加码（比如 融资余额、持仓量、增持）
    取舍反_xxx  越大越“怕”、越撤退（比如 减持、解禁、交易所里的币）
    （也可以用英文前缀：C_ / C-  /  Q_ / Q-，减号表示“越大越坏”）

做法（和 references/三股力怎么观.md 一致）：
    每一样数和它自己的过去比（标准分，至少三年历史）→ 同一股力取平均 → 取3期平均去毛刺
    → 和3期以前比看方向 → 得出“正面/反面、往上/往下”。时机这股力用价格自己算：
    离均线多远、6个月涨跌、成交量（近3个月比近12个月）。
    上半圈还是下半圈，由“当家”的那股力定：实物看条件，政策和钱看取舍；
    再按“条件先、时机跟、人性最后”的顺序，定在哪一段。

注意：
    · 宏观、业绩这类数有公布滞后，用 --lag-cond 把条件往后挪（月线一般挪 1）。
    · 只有价格时，只能看时机这股力，分不清上下半圈，工具会照实说。
    · 结果只是参考，最后的判断要结合事实、回头观和价格信号（见 SKILL.md）。
"""
import argparse
import sys

import numpy as np
import pandas as pd

STAGES = ["绝望", "怀疑", "犹豫", "大众共识", "泡沫", "兑现", "幻想", "侥幸", "瓦解", "麻木", "恐慌", "衰竭"]


def zexp(s, minp):
    m = s.expanding(min_periods=minp).mean()
    sd = s.expanding(min_periods=minp).std()
    return (s - m) / sd.replace(0, np.nan)


def direction(L, k):
    D = L - L.shift(k)
    out, last = [], np.nan
    for v in D.values:
        if v != v:
            last = np.nan
        elif v != 0:
            last = 1.0 if v > 0 else -1.0
        out.append(last)
    return pd.Series(out, index=L.index)


def state(L, D):
    if L != L or D != D:
        return "—"
    if D > 0:
        return "反面走完了（往上，还在零下）" if L < 0 else "正面出来了（往上，已在零上）"
    return "正面走完了（往下，还在零上）" if L > 0 else "反面出来了（往下，已在零下）"


def seq_stage(LC, DC, LT, DT, LQ, DQ):
    if any(x != x for x in (LC, DC, LT, DT, LQ, DQ)):
        return None
    key = (DC > 0, DT > 0, DQ > 0)
    table = {(True, False, False): "绝望" if LC < 0 else "怀疑",
             (True, True, False): "犹豫" if LT < 0 else "大众共识",
             (True, True, True): "泡沫" if LQ < 0 else "兑现",
             (False, True, True): "幻想" if LC > 0 else "侥幸",
             (False, False, True): "瓦解" if LT > 0 else "麻木",
             (False, False, False): "恐慌" if LQ > 0 else "衰竭"}
    return table.get(key, "观不清")


def classify(cols):
    C, Q = [], []
    for c in cols:
        for pre, lst, sign in [("条件反_", C, -1), ("条件_", C, 1), ("C-", C, -1), ("C_", C, 1),
                               ("取舍反_", Q, -1), ("取舍_", Q, 1), ("Q-", Q, -1), ("Q_", Q, 1)]:
            if c.startswith(pre):
                lst.append((c, sign))
                break
    return C, Q


def main():
    ap = argparse.ArgumentParser(description="冬至理论阶段计算")
    ap.add_argument("csv")
    ap.add_argument("--anchor", default="实物", choices=["实物", "政策和钱", "将来的钱"])
    ap.add_argument("--freq", default="M", choices=["M", "W"])
    ap.add_argument("--lag-cond", type=int, default=0, help="条件数据往后挪几期（公布滞后）")
    ap.add_argument("--lag-q", type=int, default=0, help="取舍数据往后挪几期")
    ap.add_argument("--show", type=int, default=12, help="显示最近几期")
    ap.add_argument("--out", help="把每一期的结果存成 CSV")
    a = ap.parse_args()

    d = pd.read_csv(a.csv)
    if "date" not in d or "close" not in d:
        sys.exit("CSV 里要有 date 和 close 两列")
    d["date"] = pd.to_datetime(d["date"])
    d = d.set_index("date").sort_index()
    d = d[pd.to_numeric(d["close"], errors="coerce") > 0]
    rule = "W-FRI"
    if a.freq == "M":
        try:
            pd.Series([1.0], index=pd.to_datetime(["2020-01-01"])).resample("ME").last()
            rule = "ME"
        except ValueError:      # 老版本 pandas 用 "M"
            rule = "M"
    per = dict(M=dict(ma=10, mom=6, v_s=3, v_l=12, sm=3, k=3, minp=36, name="月"),
               W=dict(ma=40, mom=26, v_s=13, v_l=52, sm=4, k=13, minp=156, name="周"))[a.freq]
    g = d.resample(rule)
    m = pd.DataFrame({"close": g["close"].last()})
    if "volume" in d:
        m["volume"] = g["volume"].sum()
    Ccols, Qcols = classify(d.columns)
    for c, _ in Ccols + Qcols:
        m[c] = pd.to_numeric(g[c].last(), errors="coerce")
    m = m.dropna(subset=["close"])
    for c, _ in Ccols:
        m[c] = m[c].ffill().shift(a.lag_cond)
    for c, _ in Qcols:
        m[c] = m[c].ffill().shift(a.lag_q)

    c = m["close"]
    ma = c.rolling(per["ma"], min_periods=per["ma"]).mean()
    T = {"离均线": zexp(c / ma - 1, per["minp"]), "涨跌": zexp(np.log(c).diff(per["mom"]), per["minp"])}
    if "volume" in m and (m["volume"] > 0).sum() > per["minp"]:
        v = m["volume"].where(m["volume"] > 0)
        T["成交量"] = zexp(np.log(v.rolling(per["v_s"]).mean() / v.rolling(per["v_l"]).mean()), per["minp"])
    forces = {"时机": pd.DataFrame(T).mean(axis=1)}
    if Ccols:
        forces["条件"] = pd.DataFrame({k: zexp(sg * m[k], per["minp"]) for k, sg in Ccols}).mean(axis=1)
    if Qcols:
        forces["取舍"] = pd.DataFrame({k: zexp(sg * m[k], per["minp"]) for k, sg in Qcols}).mean(axis=1)
    R = pd.DataFrame(index=m.index)
    R["收盘"] = c
    for nm, comp in forces.items():
        L = comp.rolling(per["sm"], min_periods=per["sm"]).mean()
        R[nm + "分"], R[nm + "方向"] = L, direction(L, per["k"])

    boss = {"实物": "条件", "政策和钱": "取舍", "将来的钱": "条件"}[a.anchor]
    if boss not in forces:
        boss = None
    rows = []
    for t, r in R.iterrows():
        g3 = [r.get(f"{x}分", np.nan) for x in ("条件", "时机", "取舍")] + [r.get(f"{x}方向", np.nan) for x in ("条件", "时机", "取舍")]
        LC, LT, LQ, DC, DT, DQ = g3
        seq = seq_stage(LC, DC, LT, DT, LQ, DQ)
        half = None
        if boss and r.get(boss + "方向") == r.get(boss + "方向"):
            half = "上半圈" if r[boss + "方向"] > 0 else "下半圈"
        stage = seq
        if seq and seq != "观不清" and half:
            seq_half = "上半圈" if STAGES.index(seq) < 6 else "下半圈"
            if seq_half != half:
                stage = f"{half}，段位对不上（三股力的顺序是{seq}）"
        elif seq == "观不清" and half:
            stage = f"{half}，具体段位观不清"
        rows.append((half, stage))
    R["上下半圈"] = [x[0] for x in rows]
    R["阶段"] = [x[1] for x in rows]
    if a.out:
        R.to_csv(a.out, encoding="utf-8-sig", float_format="%.3f")

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)
    print(f"数据：{d.index[0].date()} 到 {d.index[-1].date()}，按{per['name']}算，共 {len(R)} 期；"
          f"锚：{a.anchor}；当家：{boss or '（缺数据）'}；条件 {len(Ccols)} 项，取舍 {len(Qcols)} 项")
    show = R.tail(a.show).copy()
    for col in show.columns:
        if col.endswith("分"):
            show[col] = show[col].round(2)
        if col.endswith("方向"):
            show[col] = show[col].map({1.0: "往上", -1.0: "往下"})
    show.index = show.index.date
    print(show.to_string())
    last = R.iloc[-1]
    print("\n最新一期：")
    for nm in ("条件", "时机", "取舍"):
        if nm + "分" in R:
            print(f"  {nm}：{state(last[nm + '分'], last[nm + '方向'])}，分数 {last[nm + '分']:.2f}")
        else:
            print(f"  {nm}：没有数据")
    ma_label = "10个月" if a.freq == "M" else "40周"
    dc = pd.to_numeric(d["close"], errors="coerce").dropna()
    hi = dc[dc.index >= dc.index[-1] - pd.DateOffset(years=4)]
    after = dc[hi.idxmax():]
    print(f"  价格：{dc.iloc[-1]:,.2f}（{dc.index[-1].date()}）；近四年最高 {hi.max():,.2f}（{hi.idxmax().date()}），离最高 {dc.iloc[-1] / hi.max() - 1:+.1%}；"
          f"最高点以后最低 {after.min():,.2f}（{after.idxmin().date()}），离那个低点 {dc.iloc[-1] / after.min() - 1:+.1%}；"
          f"离{ma_label}均线 {c.iloc[-1] / ma.iloc[-1] - 1:+.1%}，均线{'向上' if ma.iloc[-1] > ma.iloc[-1 - per['k']] else '向下'}")
    if R.index[-1] > dc.index[-1]:
        print(f"  （最后一期的{per['name']}还没过完，数据只到 {dc.index[-1].date()}）")
    if not boss:
        print("  上下半圈：当家的那股力没有数据，分不清。只有价格时，只能看时机这股力（天时不当家）。")
    else:
        print(f"  上下半圈：{last['上下半圈'] or '还算不出（历史太短）'}；阶段参考：{last['阶段'] or '还算不出'}")
    if a.anchor == "将来的钱":
        print("  个股要先看大圈：再拿它所在的大盘或行业指数跑一次，大圈定方向，个股只看比大圈强还是弱。")
    print("\n提醒：这是按数算出来的参考。最后的判断要回头观（前一段走完了吗）、对照价格信号和口头禅，并写下观错的信号。")


if __name__ == "__main__":
    main()
