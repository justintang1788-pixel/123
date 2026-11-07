"""事后探索（不是事先定的，结论要打折扣看）。

起因：事先定的热度里，融资余额在 2010–2015 年是新业务一路增长，分位一直是 1.0，从来到不了“冷”；
换手率用全部历史排位，也被 2019 年以后成交整体变大带偏。这里只换掉热度的量法，其余规则不动。
"""
import numpy as np
import pandas as pd

import validate as V

df = V.monthly()


def heat_tr(df, window=60):
    tr = (df["turnover"] / df["mktcap"]).rolling(3, min_periods=3).mean()
    return V.pct_rank(tr, window)


pd.set_option("display.width", 250)
orig_heat = V.heat
for w in [36, 60]:
    V.heat = lambda d, window=None, w=w: heat_tr(d, w)
    print(f"\n######## 热度 = 只用换手率，在过去 {w} 个月里排位 ########")
    g, o, p, ep = V.h1(df, verbose=False)
    print(g.round(3).to_string())
    print(f"热度与之后12个月涨跌的相关 {o:+.2f}，p={p:.3f}")
    print(ep.sort_values("开始").to_string(index=False))
    P, R = V.backtest(df)
    s = V.stats(R, P)
    s.index = [V.NAMES[k] for k in s.index]
    print(s.round(3).to_string())
    grid = []
    for L in [3, 6, 9, 12]:
        for hot in [0.7, 0.8, 0.9]:
            for cold in [0.1, 0.2, 0.3]:
                Pg, Rg = V.backtest(df, L=L, hot=hot, cold=cold)
                sg = V.stats(Rg, Pg)
                grid.append({k: sg.loc[k, "年化/回撤"] for k in sg.index} |
                            {k + "_mdd": sg.loc[k, "最大回撤"] for k in sg.index})
    G = pd.DataFrame(grid)
    for k in ["C1", "C2", "C"]:
        print(f"{V.NAMES[k]} 比 B：年化/回撤更好 {(G[k] > G['B']).mean():.0%}，回撤更小 {(G[k+'_mdd'] > G['B_mdd']).mean():.0%}；"
              f"比 A：年化/回撤更好 {(G[k] > G['A']).mean():.0%}")
    print("年化/回撤中位数：", G[["A", "B", "C1", "C2", "C"]].median().round(3).to_dict())
V.heat = orig_heat

# 看反应能不能预测后市：降准公布次日的涨跌 vs 之后6、12个月全市场涨跌
print("\n######## 降准次日反应 vs 之后的涨跌 ########")
g3, pv3, ev = V.h3(df, verbose=False)
p = df["mkt_idx"]
cut = ev[ev["chg"] < 0].copy()
cut["ym"] = cut["date"].dt.to_period("M")
cut["之后6个月"] = cut["ym"].map(lambda m: V.fwd(p, 6).get(m, np.nan))
cut["之后12个月"] = cut["ym"].map(lambda m: V.fwd(p, 12).get(m, np.nan))
cut["反应"] = np.where(cut["次日上证"] > 0, "好消息涨了", "好消息没涨")
print(cut.groupby("反应")[["之后6个月", "之后12个月"]].agg(["mean", "count"]).round(3).to_string())
print("相关（次日涨跌 vs 之后12个月）:", round(cut[["次日上证", "之后12个月"]].corr().iloc[0, 1], 2))
for half in ["上半圈", "下半圈"]:
    sub = cut[cut["半圈"] == half]
    print(half, sub.groupby("反应")["之后12个月"].agg(["mean", "count"]).round(3).to_dict())
cut[["REPORT_DATE", "半圈", "次日上证", "之后6个月", "之后12个月"]].to_csv(
    V.OUT / "explore_cut_reaction.csv", index=False, encoding="utf-8-sig")
