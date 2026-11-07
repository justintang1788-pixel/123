"""拆零件：第三版里哪一部分在起作用。34个标的，默认参数（跌透30%、均线40周、放量1.5倍、分界线0.8），全部历史。"""
import numpy as np
import pandas as pd

import v3_walkforward as V


def run_variant(f, cyc, use_despair=True, use_proof=True, type_heat=True, pure=False):
    n = len(f["close"]); tgt = np.zeros(n)
    pos, stop, st = 0.0, np.nan, "等"
    hi, wk, sold_b, sold_c, hot = np.nan, 0, False, False, False
    c, lo = f["close"], f["lowv"]
    for t in range(n):
        if np.isnan(f["ma"][t]):
            continue
        if pure:   # 纯跟势：创一年新高满仓进，13周最低价跟踪止损
            if pos == 0 and f["new52"][t] and not np.isnan(f["low13"][t]):
                pos, stop = 1.0, f["low13"][t]
            elif pos > 0:
                if c[t] < stop:
                    pos = 0.0
                else:
                    stop = max(stop, f["low13"][t])
            tgt[t] = pos
            continue
        if pos == 0:
            entered = False
            if use_despair and f["despair"][t] and f["panic52"][t]:
                pos, stop, st, entered = 1 / 3, f["low26"][t], "绝望", True
            elif use_proof and f["new52"][t] and not np.isnan(f["low13"][t]):
                pos, stop, st, entered = 2 / 3, f["low13"][t], "怀疑", True
            if entered:
                hi, wk, sold_b, sold_c, hot = c[t], 0, False, False, False
        else:
            if c[t] < stop:
                pos, st, stop = 0.0, "等", np.nan
            else:
                if st == "绝望" and c[t] > hi and f["low8"][t] > stop:
                    pos, st, wk = 2 / 3, "怀疑", 0
                    stop = max(stop, f["low8"][t])
                if st == "怀疑":
                    wk += 1; stop = max(stop, f["low8"][t])
                    if c[t] > f["ma"][t] and f["ma_up"][t] and wk >= 4 and not sold_b:
                        pos, st = 1.0, "犹豫"
                if st == "犹豫":
                    stop = max(stop, f["low13"][t])
                if st in ("怀疑", "犹豫") and f["consensus"][t]:
                    st, hot = "大众共识", True
                if st == "大众共识":
                    stop = max(stop, f["low4"][t])
                trend = (not cyc[t]) if type_heat else True
                if f["bubble"][t] and not sold_b:
                    sold_b, hot, st = True, True, "泡沫"
                    if not trend:
                        pos = pos / 2
                if st == "泡沫":
                    stop = max(stop, f["low4"][t] if trend else lo[t])
                if hot and f["cashout"][t] and not sold_c:
                    pos, sold_c, st = pos / 2, True, "兑现"
                if st == "兑现":
                    stop = max(stop, lo[t])
                hi = max(hi, c[t])
        tgt[t] = pos
    return tgt


VARIANTS = {
    "第三版（全部零件）": dict(),
    "去掉“绝望”进场": dict(use_despair=False),
    "去掉“价格证明”进场": dict(use_proof=False),
    "去掉按类型处理热": dict(type_heat=False),
    "纯跟势（只用新高进、止损出）": dict(pure=True),
}

inst = V.load_all()
rows, port = [], {}
for name, w in inst.items():
    f = V.features(w, 0.30, 40, 1.5)
    cyc = V.cyc_series(w, 0.8)
    s0 = w.index[~np.isnan(f["ma"])][0]
    for k, kw in VARIANTS.items():
        r = V.returns(w, run_variant(f, cyc, **kw))
        r = r[r.index >= s0]
        st = V.stats(r)
        rows.append({"标的": name, "做法": k, **st})
        port.setdefault(k, {})[name] = r
    bh = w["close"].pct_change().fillna(0); bh = bh[bh.index >= s0]
    rows.append({"标的": name, "做法": "一直拿着", **V.stats(bh)}); port.setdefault("一直拿着", {})[name] = bh
D = pd.DataFrame(rows)
piv = D.pivot(index="标的", columns="做法", values="年化÷回撤")
base = piv["第三版（全部零件）"]
print("=== 每种做法：年化÷回撤 的中位数；比“第三版全部零件”好的标的数 ===")
for k in list(VARIANTS) + ["一直拿着"]:
    print(f"{k:16s} 中位数 {piv[k].median():.3f}   比第三版好 {int((piv[k] > base).sum())}/34")
print("\n=== 等权组合（2008年以后，各标的有数据就算） ===")
for k, d in port.items():
    P = pd.DataFrame(d)
    P = P[P.index >= "2008-01-01"].mean(axis=1)
    s = V.stats(P)
    print(f"{k:16s} 年化 {s['年化']:.1%}  最大回撤 {s['最大回撤']:.1%}  年化÷回撤 {s['年化÷回撤']:.2f}")
D.to_csv(V.OUT / "ablation.csv", index=False, encoding="utf-8-sig")
