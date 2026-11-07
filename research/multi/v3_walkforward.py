"""笔记七：第三版方法的滚动向前检验（盖住未来）。规则见 notes/07 第一部分（事先写定）。"""
import itertools
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "v3"
OUT.mkdir(parents=True, exist_ok=True)
COST = 0.001
GRID = list(itertools.product([0.25, 0.30, 0.40], [30, 40, 52], [1.3, 1.5, 2.0]))
THETAS = [0.8, 1.0, 1.2]
YEARS = list(range(2016, 2027))


def load_all():
    inst = {}
    for sub in ["multi", "multi2"]:
        meta = pd.read_csv(ROOT / "data" / sub / "_meta.csv")
        for _, r in meta.iterrows():
            d = pd.read_csv(ROOT / "data" / sub / f"{r['代码']}.csv", parse_dates=["date"]).set_index("date").sort_index()
            d = d[(d["close"] > 0) & d["volume"].notna()]
            w = pd.DataFrame({"open": d["open"].resample("W-FRI").first(), "high": d["high"].resample("W-FRI").max(),
                              "low": d["low"].resample("W-FRI").min(), "close": d["close"].resample("W-FRI").last(),
                              "volume": d["volume"].resample("W-FRI").sum()}).dropna()
            inst[r["名称"]] = w[w["volume"] > 0]
    return inst


def features(w, cold, ma, vmul):
    c, h, l, v, o = w["close"], w["high"], w["low"], w["volume"], w["open"]
    f = {}
    m = c.rolling(ma, min_periods=ma).mean()
    v26 = v.shift(1).rolling(26, min_periods=26).mean()
    v13 = v.rolling(13, min_periods=13).mean()
    v13p = v13.rolling(156, min_periods=52).rank(pct=True)
    peak = c.rolling(104, min_periods=52).max()
    ret = c.pct_change()
    q05 = ret.shift(1).rolling(156, min_periods=104).quantile(0.05)
    panic = (ret <= q05) & (v >= vmul * v26)
    dist = c / m - 1
    f["ma"] = m.values
    f["ma_up"] = (m > m.shift(4)).values
    f["deep"] = ((c / peak - 1).rolling(26, min_periods=1).min() <= -cold).values
    f["low26"] = l.rolling(26, min_periods=26).min().values
    nnl = (l.rolling(4).min() > l.shift(4).rolling(22, min_periods=22).min())
    volup = (v >= vmul * v26) & (c > c.shift(1))
    brk = c > h.shift(1).rolling(4).max()
    f["despair"] = (pd.Series(f["deep"], index=w.index) & nnl & volup & brk).values
    f["panic52"] = panic.rolling(52, min_periods=1).max().fillna(0).astype(bool).values
    f["new52"] = (c > c.shift(1).rolling(52, min_periods=52).max()).values
    f["consensus"] = ((dist >= 0.30) & (v13p >= 0.70)).values
    f["bubble"] = (((dist >= 0.60) | (c / c.shift(13) - 1 >= 0.50)) & (v13p >= 0.90)).values
    f["cashout"] = ((v >= vmul * v26) & (h >= h.rolling(26).max()) & (c < o)).values
    f["low4"], f["low8"], f["low13"] = (l.rolling(k).min().values for k in (4, 8, 13))
    f["close"], f["lowv"] = c.values, l.values
    return f


def run(f, version, cyc=None):
    """version: 'paper' 或 'v3'。cyc: 每周是否周期型（v3 用）。返回每周末定下的目标仓位。"""
    n = len(f["close"])
    tgt = np.zeros(n)
    pos, stop, st = 0.0, np.nan, "等"
    hi, wk, sold_b, sold_c, hot = np.nan, 0, False, False, False
    c, lo = f["close"], f["lowv"]
    for t in range(n):
        if np.isnan(f["ma"][t]):
            continue
        if pos == 0:
            entered = False
            if f["despair"][t] and (version == "paper" or f["panic52"][t]):
                pos, stop, st, entered = 1 / 3, f["low26"][t], "绝望", True
            elif version == "v3" and f["new52"][t] and not np.isnan(f["low13"][t]):
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
                    wk += 1
                    stop = max(stop, f["low8"][t])
                    if c[t] > f["ma"][t] and f["ma_up"][t] and wk >= 4 and not sold_b:
                        pos, st = 1.0, "犹豫"
                if st == "犹豫":
                    stop = max(stop, f["low13"][t])
                if st in ("怀疑", "犹豫") and f["consensus"][t]:
                    st, hot = "大众共识", True
                if st == "大众共识":
                    stop = max(stop, f["low4"][t])
                trend = version == "v3" and not cyc[t]
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


def returns(w, tgt):
    o, c = w["open"].values, w["close"].values
    w1 = np.r_[0, tgt[:-1]]          # 本周开盘起的仓位（上周末定）
    w2 = np.r_[0, 0, tgt[:-2]]       # 本周开盘前的仓位
    prev_c = np.r_[np.nan, c[:-1]]
    r = w2 * (o / prev_c - 1) + w1 * (c / o - 1) - COST * np.abs(w1 - w2)
    return pd.Series(np.nan_to_num(r), index=w.index)


def cyc_series(w, theta):
    """每年第一周，用这之前的全部周线算两年方差比；不满6年按趋势型。"""
    c = w["close"]
    out = np.zeros(len(c), dtype=bool)
    years = c.index.year
    for y in sorted(set(years)):
        past = c[c.index < pd.Timestamp(f"{y}-01-01")]
        if len(past) < 312:
            flag = False
        else:
            lr = np.log(past)
            vr = lr.diff(104).dropna().var() / (104 * lr.diff().dropna().var())
            flag = vr < theta
        out[years == y] = flag
    return out


def calmar(r):
    r = r.dropna()
    if len(r) < 52:
        return np.nan
    nav = (1 + r).cumprod()
    yrs = (r.index[-1] - r.index[0]).days / 365.25
    cagr = nav.iloc[-1] ** (1 / yrs) - 1
    mdd = (nav / nav.cummax() - 1).min()
    return cagr / abs(mdd) if mdd < 0 else 0.0


def stats(r):
    r = r.dropna()
    nav = (1 + r).cumprod()
    yrs = (r.index[-1] - r.index[0]).days / 365.25
    cagr = nav.iloc[-1] ** (1 / yrs) - 1
    mdd = (nav / nav.cummax() - 1).min()
    return {"年化": cagr, "最大回撤": mdd, "年化÷回撤": cagr / abs(mdd) if mdd < 0 else np.nan}


if __name__ == "__main__":
    inst = load_all()
    print("标的数", len(inst), flush=True)
    R = {"一直拿着": {}, "简单跟势": {}, "论文版": {}, "第三版": {}}
    for name, w in inst.items():
        R["一直拿着"][name] = {None: w["close"].pct_change().fillna(0)}
        R["简单跟势"][name] = {ma: returns(w, (w["close"] > w["close"].rolling(ma, min_periods=ma).mean()).astype(float).values)
                           for ma in [30, 40, 52]}
        cycs = {th: cyc_series(w, th) for th in THETAS}
        R["论文版"][name], R["第三版"][name] = {}, {}
        for g in GRID:
            f = features(w, *g)
            R["论文版"][name][g] = returns(w, run(f, "paper"))
            for th in THETAS:
                R["第三版"][name][g + (th,)] = returns(w, run(f, "v3", cycs[th]))
        print(name, "ok", flush=True)
    with open(OUT / "returns.pkl", "wb") as fh:
        pickle.dump(R, fh)

    # 滚动向前：每年只用这一年以前的数据挑参数
    chosen = {k: {} for k in R}
    oos = {k: {} for k in R}
    for method, per in R.items():
        variants = list(next(iter(per.values())).keys())
        for y in YEARS:
            cut = pd.Timestamp(f"{y}-01-01")
            if len(variants) == 1:
                best = variants[0]
            else:
                score = {}
                for v in variants:
                    vals = []
                    for name, rv in per.items():
                        past = rv[v][rv[v].index < cut]
                        first = past.ne(0).idxmax() if past.ne(0).any() else None
                        if first is None or (cut - first).days < 3 * 365:
                            continue
                        vals.append(calmar(past.loc[first:]))
                    score[v] = np.nanmedian(vals) if vals else -np.inf
                best = max(score, key=score.get)
            chosen[method][y] = best
            for name, rv in per.items():
                seg = rv[best][(rv[best].index >= cut) & (rv[best].index < pd.Timestamp(f"{y + 1}-01-01"))]
                oos[method].setdefault(name, []).append(seg)
    oos = {m: {n: pd.concat(v) for n, v in d.items()} for m, d in oos.items()}
    with open(OUT / "oos.pkl", "wb") as fh:
        pickle.dump({"oos": oos, "chosen": chosen}, fh)

    print("\n=== 每年挑出来的参数（只用当年以前的数据） ===")
    print(pd.DataFrame(chosen).to_string())

    rows = []
    for name in inst:
        row = {"标的": name}
        for m in R:
            r = oos[m][name]
            first = inst[name].index[inst[name]["close"].rolling(52).count().ge(52).argmax()]
            r = r[r.index >= max(first, pd.Timestamp("2016-01-01"))]
            s = stats(r)
            row.update({f"{m}_{k}": v for k, v in s.items()})
        rows.append(row)
    T = pd.DataFrame(rows)
    T.to_csv(OUT / "oos_per_instrument.csv", index=False, encoding="utf-8-sig")
    pd.set_option("display.width", 250)
    print("\n=== 2016–2026 每个标的（年化÷回撤） ===")
    print(T[["标的"] + [f"{m}_年化÷回撤" for m in R]].round(2).to_string(index=False))
    n = len(T)
    c1 = int((T["第三版_年化÷回撤"] > T["简单跟势_年化÷回撤"]).sum())
    c2 = int((T["第三版_最大回撤"] > T["一直拿着_最大回撤"]).sum())
    print(f"\n标准1：第三版“年化÷回撤”胜过简单跟势 {c1}/{n}")
    print(f"标准2：第三版最大回撤小于一直拿着 {c2}/{n}")
    print(f"（参考）论文版胜过简单跟势 {int((T['论文版_年化÷回撤'] > T['简单跟势_年化÷回撤']).sum())}/{n}；"
          f"第三版胜过一直拿着 {int((T['第三版_年化÷回撤'] > T['一直拿着_年化÷回撤']).sum())}/{n}")
    print("中位数：", {m: round(T[f"{m}_年化÷回撤"].median(), 3) for m in R},
          "最大回撤中位数：", {m: round(T[f"{m}_最大回撤"].median(), 3) for m in R})

    port = {}
    for m in R:
        df = pd.DataFrame(oos[m])
        df = df[df.index >= pd.Timestamp("2016-01-01")]
        port[m] = df.mean(axis=1, skipna=True)
    P = pd.DataFrame(port)
    P.to_csv(OUT / "portfolio_weekly.csv", encoding="utf-8-sig")
    ps = pd.DataFrame({m: stats(P[m]) for m in P}).T
    print("\n=== 34个标的等权组合，2016–2026 ===")
    print(ps.round(3).to_string())
    print("标准3：第三版组合“年化÷回撤”高于跟势和一直拿着：",
          bool(ps.loc["第三版", "年化÷回撤"] > ps.loc["简单跟势", "年化÷回撤"] and ps.loc["第三版", "年化÷回撤"] > ps.loc["一直拿着", "年化÷回撤"]))
