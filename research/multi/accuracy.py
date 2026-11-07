"""冬至理论第三版的“准确率”：交易胜率、信号命中率（和平常比）。"""
import pickle

import numpy as np
import pandas as pd

import v3_walkforward as V

inst = V.load_all()
d = pickle.load(open(V.OUT / "oos.pkl", "rb"))
chosen = d["chosen"]["第三版"]
oos = d["oos"]["第三版"]

# 1) 交易：2016–2026 年滚动挑参数后的每一笔
trades = []
for name, w in inst.items():
    cycs = {th: V.cyc_series(w, th) for th in V.THETAS}
    held = []
    for y, g in chosen.items():
        tgt = pd.Series(V.run(V.features(w, *g[:3]), "v3", cycs[g[3]]), index=w.index)
        held.append(tgt.shift(1)[tgt.index.year == y])
    pos = pd.concat(held).fillna(0)
    r = oos[name].reindex(pos.index).fillna(0)
    inpos = (pos > 0) | (pos.shift(1).fillna(0) > 0)   # 持仓周，含卖出那一周的执行
    run_id = (inpos != inpos.shift()).cumsum()
    for k, seg in r[inpos].groupby(run_id[inpos]):
        trades.append({"标的": name, "开始": seg.index[0], "周数": len(seg), "收益": (1 + seg).prod() - 1})
T = pd.DataFrame(trades)
T = T[T["开始"] >= "2016-01-01"]
win = T["收益"] > 0
print("=== 交易（第三版，2016–2026，34个标的） ===")
print(f"笔数 {len(T)}，赚钱的 {win.mean():.0%}")
print(f"赚钱的那些平均 {T.loc[win, '收益'].mean():+.1%}，亏钱的那些平均 {T.loc[~win, '收益'].mean():+.1%}")
print(f"赚的总和 ÷ 亏的总和 = {T.loc[win, '收益'].sum() / -T.loc[~win, '收益'].sum():.2f}")
print(f"持有周数中位数：赚钱的 {T.loc[win, '周数'].median():.0f}，亏钱的 {T.loc[~win, '周数'].median():.0f}")
big = T.sort_values("收益", ascending=False)
print("最大的5笔：", [(r.标的, str(r.开始.date()), round(r.收益, 2)) for r in big.head(5).itertuples()])
print("最差的5笔：", [(r.标的, str(r.开始.date()), round(r.收益, 2)) for r in big.tail(5).itertuples()])

# 2) 信号命中率：信号之后26周涨跌，和同一个标的随便哪一周比
rows = []
for name, w in inst.items():
    f = V.features(w, 0.30, 40, 1.5)
    c = w["close"]
    f26 = c.shift(-26) / c - 1
    base_up = (f26.dropna() > 0).mean()
    hot_recent = pd.Series(f["consensus"] | f["bubble"], index=w.index).rolling(26, min_periods=1).max().astype(bool)
    sig = {"绝望（含见过恐慌）": pd.Series(f["despair"] & f["panic52"], index=w.index),
           "价格自己证明": pd.Series(f["new52"], index=w.index),
           "泡沫": pd.Series(f["bubble"], index=w.index),
           "兑现": pd.Series(f["cashout"], index=w.index) & hot_recent}
    for k, m in sig.items():
        dates, last = [], None
        for t, v in m.items():
            if v and (last is None or (t - last).days > 26 * 7):
                dates.append(t); last = t
        x = f26.reindex(dates).dropna()
        for v in x:
            rows.append({"信号": k, "标的": name, "之后26周涨了": v > 0, "平常涨的概率": base_up})
S = pd.DataFrame(rows)
print("\n=== 信号之后半年涨没涨（34个标的，全部历史，默认参数） ===")
g = S.groupby("信号").agg(次数=("之后26周涨了", "size"), 之后涨的比例=("之后26周涨了", "mean"),
                         平常涨的比例=("平常涨的概率", "mean"))
print(g.round(2).to_string())
pickle.dump({"trades": T, "signals": S}, open(V.OUT / "accuracy.pkl", "wb"))
