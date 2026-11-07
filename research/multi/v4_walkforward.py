"""笔记十一：第四版规矩的滚动向前检验（盖住未来），每一笔都留底。规矩见 notes/11 第一部分（事先写定）。

跑法：python3 v4_walkforward.py      结果在 research/output/v4/
"""
import pickle
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

import v3_walkforward as V

ROOT = V.ROOT
OUT = ROOT / "output" / "v4"
OUT.mkdir(parents=True, exist_ok=True)
GRID, THETAS, YEARS = V.GRID, V.THETAS, V.YEARS
TARGETS = [0.2, 0.3, 0.5, 1.0]
RISKS = [0.05, 0.10]
DEFAULT = (0.30, 40, 1.5)
STAGE = ["等", "绝望", "怀疑", "犹豫", "大众共识", "泡沫", "兑现", "到目标后空仓"]
BATCHES = [("multi", 1), ("multi2", 2), ("multi3", 3)]


def group_of(code):
    if code.startswith(("hk", "us")):
        return "境外指数"
    if code.startswith(("sh000", "sz399")):
        return "A股指数"
    if code.startswith(("sh", "sz")):
        return "A股个股"
    return "国债期货" if code in ("T0", "TF0", "TS0") else "商品期货"


def load_all():
    inst, meta = {}, []
    for sub, batch in BATCHES:
        p = ROOT / "data" / sub / "_meta.csv"
        if not p.exists():
            continue
        for _, r in pd.read_csv(p).iterrows():
            d = pd.read_csv(ROOT / "data" / sub / f"{r['代码']}.csv", parse_dates=["date"]).set_index("date").sort_index()
            d = d[(d["close"] > 0) & d["volume"].notna()]
            w = pd.DataFrame({"open": d["open"].resample("W-FRI").first(), "high": d["high"].resample("W-FRI").max(),
                              "low": d["low"].resample("W-FRI").min(), "close": d["close"].resample("W-FRI").last(),
                              "volume": d["volume"].resample("W-FRI").sum()}).dropna()
            w = w[w["volume"] > 0]
            if len(w) < 156:
                continue
            inst[r["名称"]] = w
            meta.append({"标的": r["名称"], "代码": r["代码"], "批次": batch, "大类": group_of(r["代码"]),
                         "起": w.index[0].date(), "周数": len(w)})
    return inst, pd.DataFrame(meta).set_index("标的")


def _size(want, cur, price, stop, risk):
    """最坏能接受：仓位 × 离认错线的距离 不超过 risk。只在进场、加仓时用，只会让仓位更小。"""
    if risk is None:
        return want
    d = (price - stop) / price
    new = want if d <= 0 else min(want, risk / d)
    return max(cur, new)


def run4(f, bubble_low4=False, target=None, risk=None, log=False):
    """第四版（周线）。返回每周末定下的目标仓位；log=True 时同时返回阶段和事件。"""
    n = len(f["close"])
    tgt = np.zeros(n)
    stg = np.zeros(n, dtype=np.int8)
    ev = [""] * n if log else None
    pos, stop, st = 0.0, np.nan, 0
    hi, wk, sold_b, sold_c, hot = np.nan, 0, False, False, False
    ref, cut = np.nan, False
    c, lo = f["close"], f["lowv"]
    ma, ma_up, despair, panic52, new52 = f["ma"], f["ma_up"], f["despair"], f["panic52"], f["new52"]
    low4, low8, low13, low26 = f["low4"], f["low8"], f["low13"], f["low26"]
    consensus, bubble, cashout = f["consensus"], f["bubble"], f["cashout"]
    for t in range(n):
        if ma[t] != ma[t]:
            continue
        e = ""
        if pos == 0:
            want = 0.0
            if despair[t] and panic52[t]:
                want, stop, st, e = 1 / 3, low26[t], 1, "绝望进场"
            elif new52[t] and low13[t] == low13[t]:
                want, stop, st, e = 2 / 3, low13[t], 2, "价格证明进场"
            if want > 0:
                pos = _size(want, 0.0, c[t], stop, risk)
                hi, wk, sold_b, sold_c, hot = c[t], 0, False, False, False
                ref, cut = c[t], False
        else:
            if c[t] < stop:
                pos, st, stop, cut = 0.0, 0, np.nan, False
                e = "跌破认错线，全部卖掉"
            else:
                if st == 1 and c[t] > hi and low8[t] > stop:
                    st, wk = 2, 0
                    stop = max(stop, low8[t])
                    pos = _size(2 / 3, pos, c[t], stop, risk)
                    e = "回踩没破，加到2/3"
                if st == 2:
                    wk += 1
                    stop = max(stop, low8[t])
                    if c[t] > ma[t] and ma_up[t] and wk >= 4 and not sold_b:
                        st = 3
                        pos = _size(1.0, pos, c[t], max(stop, low13[t]), risk)
                        e = "站上向上的均线，加满"
                if st == 3:
                    stop = max(stop, low13[t])
                if (st == 2 or st == 3) and consensus[t]:
                    st, hot = 4, True
                    e = e or "大众共识，不再加，认错线收紧"
                if st == 4:
                    stop = max(stop, low4[t])
                if bubble[t] and not sold_b:
                    sold_b, hot, st = True, True, 5
                    e = "泡沫，不加也不卖，认错线跟紧"
                if st == 5:
                    stop = max(stop, low4[t] if bubble_low4 else lo[t])
                if hot and cashout[t] and not sold_c:
                    pos, sold_c, st = pos / 2, True, 6
                    e = "兑现，卖一半"
                if st == 6:
                    stop = max(stop, lo[t])
                hi = max(hi, c[t])
                if target is not None and not cut and c[t] >= ref * (1 + target):
                    cut = True
                    e = f"赚到{target:.0%}，全部卖掉"
        tgt[t] = 0.0 if cut else pos
        stg[t] = 7 if cut else st
        if log:
            ev[t] = e
    return (tgt, stg, ev) if log else tgt


def variants_for(name, w):
    """一个标的上，所有做法、所有参数的每周收益。"""
    R = {"一直拿着": {None: w["close"].pct_change().fillna(0).values},
         "简单跟势": {ma: V.returns(w, (w["close"] > w["close"].rolling(ma, min_periods=ma).mean()).astype(float).values).values
                  for ma in [30, 40, 52]}}
    cycs = {th: V.cyc_series(w, th) for th in THETAS}
    keys = ["第三版", "第四版", "第四版·泡沫用4周低点"] + [f"第四版＋目标{x:.0%}" for x in TARGETS] + \
           [f"第四版＋最坏{r:.0%}" for r in RISKS]
    for k in keys:
        R[k] = {}
    for g in GRID:
        f = V.features(w, *g)
        for th in THETAS:
            R["第三版"][g + (th,)] = V.returns(w, V.run(f, "v3", cycs[th])).values
        R["第四版"][g] = V.returns(w, run4(f)).values
        R["第四版·泡沫用4周低点"][g] = V.returns(w, run4(f, bubble_low4=True)).values
        for x in TARGETS:
            R[f"第四版＋目标{x:.0%}"][g] = V.returns(w, run4(f, target=x)).values
        for r in RISKS:
            R[f"第四版＋最坏{r:.0%}"][g] = V.returns(w, run4(f, risk=r)).values
    return name, R


def _worker(args):
    return variants_for(*args)


def calmar_np(r, d):
    if len(r) < 52:
        return np.nan
    nav = np.cumprod(1 + r)
    yrs = (d[-1] - d[0]) / 365.25
    if yrs <= 0 or nav[-1] <= 0:
        return np.nan if yrs <= 0 else -np.inf
    cagr = nav[-1] ** (1 / yrs) - 1
    mdd = np.min(nav / np.maximum.accumulate(nav) - 1)
    return cagr / abs(mdd) if mdd < 0 else 0.0


def past_score(r, days, cut_day, k):
    """和 V.calmar 一样：只用 cut 以前的数据，从第一次有盈亏的那周算起，满三年才算。"""
    nz = np.flatnonzero(r[:k])
    if len(nz) == 0 or cut_day - days[nz[0]] < 3 * 365:
        return None
    return calmar_np(r[nz[0]:k], days[nz[0]:k])


def stats(r):
    r = r.dropna()
    nav = (1 + r).cumprod()
    yrs = (r.index[-1] - r.index[0]).days / 365.25
    cagr = nav.iloc[-1] ** (1 / yrs) - 1
    mdd = (nav / nav.cummax() - 1).min()
    return {"年化": cagr, "最大回撤": mdd, "年化÷回撤": cagr / abs(mdd) if mdd < 0 else np.nan}


def fmt_param(m, v):
    if v is None:
        return "—"
    if m == "简单跟势":
        return f"均线{v}周"
    s = f"跌透{v[0]:.0%} 均线{v[1]}周 放量{v[2]}倍"
    return s + (f" 分界线{v[3]}" if len(v) == 4 else "")


def main():
    t0 = time.time()
    logf = open(OUT / "run.log", "w", encoding="utf-8")

    def say(*a):
        s = " ".join(str(x) for x in a)
        print(s, flush=True)
        logf.write(s + "\n")
        logf.flush()

    inst, meta = load_all()
    say(f"第四版回测  开始 {time.strftime('%Y-%m-%d %H:%M')}  标的 {len(inst)} 个",
        dict(meta["批次"].value_counts().sort_index()), dict(meta["大类"].value_counts()))
    with Pool(4) as pool:
        res = dict(pool.map(_worker, list(inst.items()), chunksize=1))
    say(f"所有做法、所有参数算完，用时 {time.time() - t0:.0f} 秒")
    methods = list(next(iter(res.values())).keys())
    days = {n: ((w.index - pd.Timestamp("1990-01-01")).days).values for n, w in inst.items()}
    idx = {n: w.index for n, w in inst.items()}

    # 滚动向前：每年年初只用这之前的数据挑参数
    chosen = {m: {} for m in methods}
    chosen_own = {}
    for m in methods:
        vs = list(res[next(iter(res))][m].keys())
        for y in YEARS:
            cut = pd.Timestamp(f"{y}-01-01")
            cday = (cut - pd.Timestamp("1990-01-01")).days
            if len(vs) == 1:
                chosen[m][y] = vs[0]
                continue
            per_v = {v: [] for v in vs}
            for n in inst:
                k = int(np.searchsorted(idx[n], cut))
                for v in vs:
                    s = past_score(res[n][m][v], days[n], cday, k)
                    if s is not None:
                        per_v[v].append(s)
                        if m == "第四版":
                            chosen_own.setdefault((n, y), {})[v] = s
            score = {v: (np.nanmedian(x) if len(x) else -np.inf) for v, x in per_v.items()}
            chosen[m][y] = max(score, key=score.get)
    say(f"挑参数完成，用时 {time.time() - t0:.0f} 秒")

    # 按圈挑参数：每个标的只看自己过去
    methods_all = methods + ["第四版·按圈挑参数"]
    own_pick = {}
    for n in inst:
        for y in YEARS:
            sc = {v: s for v, s in chosen_own.get((n, y), {}).items() if s == s}
            own_pick[(n, y)] = max(sc, key=sc.get) if sc else chosen["第四版"][y]

    def stitch(m, n):
        r = pd.Series(np.nan, index=idx[n])
        for y in YEARS:
            v = own_pick[(n, y)] if m == "第四版·按圈挑参数" else chosen[m][y]
            src = res[n]["第四版" if m == "第四版·按圈挑参数" else m][v]
            msk = idx[n].year == y
            r[msk] = src[msk]
        return r

    start = {}
    for n, w in inst.items():
        first = w.index[w["close"].rolling(52).count().ge(52).argmax()]
        start[n] = max(first, pd.Timestamp("2016-01-01"))
    oos = {m: {n: stitch(m, n).loc[start[n]:] for n in inst} for m in methods_all}
    with open(OUT / "oos.pkl", "wb") as fh:
        pickle.dump({"oos": oos, "chosen": chosen, "own_pick": own_pick, "meta": meta}, fh)

    C = pd.DataFrame({m: {y: fmt_param(m, v) for y, v in chosen[m].items()} for m in methods})
    C.index.name = "年份"
    C.to_csv(OUT / "chosen_params.csv", encoding="utf-8-sig")
    say("\n=== 每年挑出来的参数（只用当年以前的数据） ===")
    say(C[["简单跟势", "第三版", "第四版"]].to_string())

    rows = []
    for n in inst:
        row = {"标的": n, **meta.loc[n].to_dict()}
        for m in methods_all:
            s = stats(oos[m][n])
            row.update({f"{m}_{k}": v for k, v in s.items()})
        rows.append(row)
    T = pd.DataFrame(rows)
    T.to_csv(OUT / "per_instrument.csv", index=False, encoding="utf-8-sig")

    from scipy.stats import binomtest

    def criteria(TT, label):
        n = len(TT)
        a = TT["第四版_年化÷回撤"] > TT["简单跟势_年化÷回撤"]
        p = binomtest(int(a.sum()), n, 0.5, alternative="greater").pvalue
        b = TT["第四版_最大回撤"] > TT["一直拿着_最大回撤"]
        say(f"\n--- {label}：{n} 个标的 ---")
        say(f"标准1  第四版“年化÷回撤”胜过简单跟势 {int(a.sum())}/{n}（{a.mean():.0%}），符号检验 p = {p:.4f}  "
            f"→ {'过' if a.mean() > 0.5 and p < 0.05 else '没过'}")
        say(f"标准2  第四版最大回撤小于一直拿着 {int(b.sum())}/{n}（{b.mean():.0%}） → {'过' if b.mean() > 0.5 else '没过'}")
        say("中位数 年化÷回撤：", {m: round(TT[f"{m}_年化÷回撤"].median(), 3) for m in methods_all})
        say("中位数 最大回撤：", {m: round(TT[f"{m}_最大回撤"].median(), 3) for m in methods_all})
        say("中位数 年化：", {m: round(TT[f"{m}_年化"].median(), 3) for m in methods_all})
        v3 = TT["第四版_年化÷回撤"] > TT["第三版_年化÷回撤"]
        say(f"（参考）第四版胜过第三版 {int(v3.sum())}/{n}；胜过一直拿着 "
            f"{int((TT['第四版_年化÷回撤'] > TT['一直拿着_年化÷回撤']).sum())}/{n}")
        return a.mean() > 0.5 and p < 0.05, b.mean() > 0.5

    def portfolio(names):
        P = {}
        for m in methods_all:
            df = pd.DataFrame({n: oos[m][n] for n in names})
            P[m] = df.mean(axis=1, skipna=True)
        P = pd.DataFrame(P).dropna(how="all")
        return P

    def port_report(P, label):
        ps = pd.DataFrame({m: stats(P[m]) for m in P}).T
        say(f"\n=== 等权组合：{label}，{P.index[0].date()} 到 {P.index[-1].date()} ===")
        say(ps.round(3).to_string())
        c3 = ps.loc["第四版", "年化÷回撤"] > max(ps.loc["简单跟势", "年化÷回撤"], ps.loc["一直拿着", "年化÷回撤"])
        tg = [m for m in P if m.startswith("第四版＋目标")]
        c4a = all(ps.loc["第四版", "年化÷回撤"] > ps.loc[m, "年化÷回撤"] for m in tg)
        say(f"标准3  第四版组合“年化÷回撤”高于简单跟势和一直拿着 → {'过' if c3 else '没过'}")
        return ps, c3, c4a

    say("\n=== 2016–2026 每个标的（年化÷回撤），只列主要做法 ===")
    pd.set_option("display.width", 250)
    say(T[["标的", "批次", "大类"] + [f"{m}_年化÷回撤" for m in ["一直拿着", "简单跟势", "第三版", "第四版"]]]
        .round(2).to_string(index=False))

    result = {}
    for label, TT in [("全部标的", T), ("第三批新标的", T[T["批次"] == 3]), ("第一、二批", T[T["批次"] < 3])]:
        c1, c2 = criteria(TT, label)
        P = portfolio(TT["标的"].tolist())
        ps, c3, c4a = port_report(P, label)
        tg = [m for m in methods_all if m.startswith("第四版＋目标")]
        c4b = all(TT["第四版_年化÷回撤"].median() > TT[f"{m}_年化÷回撤"].median() for m in tg)
        say(f"标准4  没有预期：组合高于四档目标 {'是' if c4a else '否'}；中位数高于四档目标 {'是' if c4b else '否'} "
            f"→ {'过' if c4a and c4b else '没过'}")
        result[label] = {"标准1": c1, "标准2": c2, "标准3": c3, "标准4": c4a and c4b, "组合": ps}
        P.to_csv(OUT / f"portfolio_weekly_{label}.csv", encoding="utf-8-sig")
        yr = (1 + P).groupby(P.index.year).prod() - 1
        say(f"\n每年收益（{label}组合）：")
        say(yr[["一直拿着", "简单跟势", "第三版", "第四版"]].round(3).to_string())

    say("\n=== 按大类（全部标的）：第四版 vs 简单跟势、一直拿着 ===")
    for gname, TT in T.groupby("大类"):
        a = (TT["第四版_年化÷回撤"] > TT["简单跟势_年化÷回撤"]).sum()
        b = (TT["第四版_最大回撤"] > TT["一直拿着_最大回撤"]).sum()
        P = portfolio(TT["标的"].tolist())
        ps = pd.DataFrame({m: stats(P[m]) for m in ["一直拿着", "简单跟势", "第四版"]}).T
        say(f"{gname}（{len(TT)}个）：胜跟势 {a}/{len(TT)}，回撤小于一直拿着 {b}/{len(TT)}；组合 年化÷回撤 "
            + "  ".join(f"{m} {ps.loc[m, '年化']:.1%}/{ps.loc[m, '最大回撤']:.1%}/{ps.loc[m, '年化÷回撤']:.2f}" for m in ps.index))
    pickle.dump(result, open(OUT / "result.pkl", "wb"))

    # ---------- 逐笔记录：第四版主检验 ----------
    say("\n生成逐笔记录 ...")
    trades, weekly = [], []
    for n, w in inst.items():
        cache = {}
        tg_s = pd.Series(0.0, index=w.index)
        st_s = pd.Series(0, index=w.index, dtype=int)
        ev_s = pd.Series("", index=w.index, dtype=object)
        for y in YEARS:
            g = chosen["第四版"][y]
            if g not in cache:
                cache[g] = run4(V.features(w, *g), log=True)
            tg, stg, ev = cache[g]
            msk = w.index.year == y
            tg_s[msk], st_s[msk], ev_s[msk] = tg[msk], stg[msk], np.array(ev, dtype=object)[msk]
        # 2016 年以前的部分不算（盖住未来只从2016年开始）
        s0 = start[n]
        keep = w.index >= s0
        tg_s[~keep] = 0.0
        r = pd.Series(V.returns(w, tg_s.values).values, index=w.index)
        o, hgh, low, cl = w["open"].values, w["high"].values, w["low"].values, w["close"].values
        tv = tg_s.values
        N = len(tv)
        t = 0
        while t < N:
            if tv[t] > 0:
                t0 = t
                while t < N and tv[t] > 0:
                    t += 1
                t1 = t - 1
                ent = ev_s.iloc[t0] if ev_s.iloc[t0] in ("绝望进场", "价格证明进场") else "换年换参数后接手"
                if t0 + 1 >= N:
                    break
                ep = o[t0 + 1]
                closed = t1 + 2 < N
                xp = o[t1 + 2] if closed else cl[-1]
                xr = ev_s.iloc[t1 + 1] if t1 + 1 < N else ""
                if not closed:
                    xr = "还拿着（到最后一周）"
                elif not xr:
                    xr = "换年换参数后空仓"
                changes = []
                for k in range(t0 + 1, t1 + 1):
                    if tv[k] != tv[k - 1]:
                        changes.append(f"{w.index[k].date()} {ev_s.iloc[k] or '换年换参数'}→{tv[k]:.2f}")
                seg = r.iloc[t0 + 1: (t1 + 3 if closed else N)]
                span = slice(t0 + 1, min(t1 + 2, N))
                trades.append({
                    "标的": n, "批次": meta.loc[n, "批次"], "大类": meta.loc[n, "大类"],
                    "进场信号周": w.index[t0].date(), "进场执行日(周一开盘)": (w.index[t0 + 1] - pd.Timedelta(days=4)).date(),
                    "进场价": ep, "进场方式": ent, "进场阶段": STAGE[st_s.iloc[t0]], "进场仓位": tv[t0],
                    "最高仓位": tv[t0:t1 + 1].max(), "中间加减": "；".join(changes),
                    "出场信号周": w.index[t1 + 1].date() if t1 + 1 < N else None,
                    "出场执行日(周一开盘)": (w.index[t1 + 2] - pd.Timedelta(days=4)).date() if closed else None,
                    "出场价": xp, "出场原因": xr, "出场前阶段": STAGE[st_s.iloc[t1]],
                    "持有周数": (t1 + 2 if closed else N) - (t0 + 1),
                    "价格涨跌": xp / ep - 1,
                    "对本标的资金的盈亏": float((1 + seg).prod() - 1),
                    "持有中最大浮亏": low[span].min() / ep - 1, "持有中最大浮盈": hgh[span].max() / ep - 1,
                })
            else:
                t += 1
        nav = (1 + r[keep]).cumprod()
        for k in np.flatnonzero(keep):
            dt = w.index[k]
            weekly.append({"标的": n, "周五": dt.date(), "收盘": cl[k], "阶段": STAGE[st_s.iloc[k]],
                           "周末定的仓位": tv[k], "这周发生的事": ev_s.iloc[k], "这周盈亏": r.iloc[k],
                           "净值": nav.loc[dt]})
    TR = pd.DataFrame(trades)
    TR.to_csv(OUT / "trades.csv", index=False, encoding="utf-8-sig", float_format="%.4f")
    WL = pd.DataFrame(weekly)
    WL.to_csv(OUT / "weekly_log.csv", index=False, encoding="utf-8-sig", float_format="%.4f")
    win = TR["对本标的资金的盈亏"] > 0
    say(f"\n=== 第四版逐笔（2016–2026，{len(inst)} 个标的） ===")
    for label, TT in [("全部", TR), ("第三批新标的", TR[TR["批次"] == 3]), ("第一、二批", TR[TR["批次"] < 3])]:
        wn = TT["对本标的资金的盈亏"] > 0
        pf = TT.loc[wn, "对本标的资金的盈亏"].sum() / -TT.loc[~wn, "对本标的资金的盈亏"].sum()
        say(f"{label}：{len(TT)} 笔，赚钱的 {wn.mean():.0%}，赚的平均 {TT.loc[wn, '对本标的资金的盈亏'].mean():+.1%}，"
            f"亏的平均 {TT.loc[~wn, '对本标的资金的盈亏'].mean():+.1%}，赚的总和÷亏的总和 {pf:.2f}，"
            f"持有周数中位数 赚 {TT.loc[wn, '持有周数'].median():.0f} / 亏 {TT.loc[~wn, '持有周数'].median():.0f}")
    say("按进场方式：")
    say(TR.groupby("进场方式").agg(笔数=("标的", "size"), 赚钱的比例=("对本标的资金的盈亏", lambda x: (x > 0).mean()),
                                平均=("对本标的资金的盈亏", "mean"), 持有周数中位数=("持有周数", "median")).round(3).to_string())
    say("按出场原因：")
    say(TR.groupby("出场原因").agg(笔数=("标的", "size"), 平均=("对本标的资金的盈亏", "mean")).round(3).to_string())
    big = TR.sort_values("对本标的资金的盈亏", ascending=False)
    say("最好的10笔：", [(x.标的, str(x.进场信号周), round(x.对本标的资金的盈亏, 2)) for x in big.head(10).itertuples()])
    say("最差的10笔：", [(x.标的, str(x.进场信号周), round(x.对本标的资金的盈亏, 2)) for x in big.tail(10).itertuples()])

    # ---------- 信号之后半年（默认参数，全部历史） ----------
    rows = []
    for n, w in inst.items():
        f = V.features(w, *DEFAULT)
        c = w["close"]
        f26 = c.shift(-26) / c - 1
        base_up = (f26.dropna() > 0).mean()
        hot_recent = pd.Series(f["consensus"] | f["bubble"], index=w.index).rolling(26, min_periods=1).max().astype(bool)
        sig = {"绝望（含见过恐慌）": pd.Series(f["despair"] & f["panic52"], index=w.index),
               "价格自己证明": pd.Series(f["new52"], index=w.index),
               "泡沫": pd.Series(f["bubble"], index=w.index),
               "兑现": pd.Series(f["cashout"], index=w.index) & hot_recent}
        for k, msk in sig.items():
            last = None
            for t, v in msk.items():
                if v and (last is None or (t - last).days > 26 * 7):
                    last = t
                    x = f26.get(t)
                    if x == x and x is not None:
                        rows.append({"信号": k, "标的": n, "批次": meta.loc[n, "批次"], "大类": meta.loc[n, "大类"],
                                     "信号周": t.date(), "之后26周涨跌": x, "之后26周涨了": x > 0, "这个标的平常涨的概率": base_up})
    S = pd.DataFrame(rows)
    S.to_csv(OUT / "signals.csv", index=False, encoding="utf-8-sig", float_format="%.4f")
    for label, SS in [("全部", S), ("第三批新标的", S[S["批次"] == 3]), ("第一、二批", S[S["批次"] < 3])]:
        g = SS.groupby("信号").agg(次数=("之后26周涨了", "size"), 之后涨的比例=("之后26周涨了", "mean"),
                                 平常涨的比例=("这个标的平常涨的概率", "mean"))
        g["p(高于平常)"] = [binomtest(int(SS[SS["信号"] == k]["之后26周涨了"].sum()), int(g.loc[k, "次数"]),
                                   g.loc[k, "平常涨的比例"], alternative="greater").pvalue for k in g.index]
        say(f"\n=== 信号之后半年涨没涨（{label}，默认参数，全部历史） ===")
        say(g.round(3).to_string())
    say(f"\n全部完成，用时 {time.time() - t0:.0f} 秒")


if __name__ == "__main__":
    main()
