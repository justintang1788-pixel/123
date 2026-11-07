"""多标的：周期性测量 + 冬至理论周线回测 + 信号检验。规则见 notes/05 第一部分（事先写定）。"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "multi"
OUT = ROOT / "output" / "multi"
OUT.mkdir(parents=True, exist_ok=True)
META = pd.read_csv(DATA / "_meta.csv")
NAME = dict(zip(META["代码"], META["名称"]))
KIND = dict(zip(META["代码"], META["类别"]))
COST = 0.001


def weekly(code):
    d = pd.read_csv(DATA / f"{code}.csv", parse_dates=["date"]).set_index("date").sort_index()
    d = d[(d["close"] > 0) & d["volume"].notna()]
    w = pd.DataFrame({"open": d["open"].resample("W-FRI").first(), "high": d["high"].resample("W-FRI").max(),
                      "low": d["low"].resample("W-FRI").min(), "close": d["close"].resample("W-FRI").last(),
                      "volume": d["volume"].resample("W-FRI").sum()}).dropna()
    return w[w["volume"] > 0]


# ---------- 第一部分：周期性 ----------
def zigzag(p, th=0.30):
    pts, mode = [], None
    ext_i, ext_v = p.index[0], p.iloc[0]
    first_lo, first_hi = (p.index[0], p.iloc[0]), (p.index[0], p.iloc[0])
    for i, v in p.items():
        if mode is None:
            if v < first_lo[1]:
                first_lo = (i, v)
            if v > first_hi[1]:
                first_hi = (i, v)
            if v >= first_lo[1] * (1 + th):
                pts.append((first_lo[0], "底", first_lo[1])); mode, ext_i, ext_v = "up", i, v
            elif v <= first_hi[1] * (1 - th):
                pts.append((first_hi[0], "顶", first_hi[1])); mode, ext_i, ext_v = "down", i, v
            continue
        if mode == "up":
            if v > ext_v:
                ext_i, ext_v = i, v
            elif v <= ext_v * (1 - th):
                pts.append((ext_i, "顶", ext_v)); mode, ext_i, ext_v = "down", i, v
        else:
            if v < ext_v:
                ext_i, ext_v = i, v
            elif v >= ext_v * (1 + th):
                pts.append((ext_i, "底", ext_v)); mode, ext_i, ext_v = "up", i, v
    return pts


def variance_ratio(p, q):
    r = np.log(p).diff().dropna()
    rq = np.log(p).diff(q).dropna()
    return rq.var() / (q * r.var())


def cyclicality(code):
    w = weekly(code)
    p = w["close"]
    yrs = (p.index[-1] - p.index[0]).days / 365.25
    pts = zigzag(p)
    swings = [abs(pts[i + 1][2] / pts[i][2] - 1) for i in range(len(pts) - 1)]
    troughs = [t for t, k, _ in pts if k == "底"]
    gaps = np.diff([t.toordinal() for t in troughs]) / 365.25 if len(troughs) > 1 else np.array([])
    return {"代码": code, "名称": NAME[code], "类别": KIND[code], "年数": round(yrs, 1),
            "每十年摆动次数": round(len(swings) / yrs * 10, 1),
            "摆动幅度中位数": np.median(swings) if swings else np.nan,
            "方差比_1年": variance_ratio(p, 52), "方差比_2年": variance_ratio(p, 104),
            "大底间隔中位数_年": np.median(gaps) if len(gaps) else np.nan,
            "大底间隔离散度": (gaps.std() / gaps.mean()) if len(gaps) > 1 else np.nan,
            "大底个数": len(troughs)}


# ---------- 第二部分：冬至理论回测 ----------
def features(w, cold=0.30, ma=40, vmul=1.5):
    f = pd.DataFrame(index=w.index)
    c, h, l, v, o = w["close"], w["high"], w["low"], w["volume"], w["open"]
    f["ma"] = c.rolling(ma, min_periods=ma).mean()
    f["ma_up"] = f["ma"] > f["ma"].shift(4)
    v26 = v.shift(1).rolling(26, min_periods=26).mean()
    v13 = v.rolling(13, min_periods=13).mean()
    f["v13_pct"] = v13.rolling(156, min_periods=52).rank(pct=True)
    peak = c.rolling(104, min_periods=52).max()
    f["deep"] = (c / peak - 1).rolling(26, min_periods=1).min() <= -cold
    f["low26"] = l.rolling(26, min_periods=26).min()
    f["no_new_low"] = l.rolling(4).min() > l.shift(4).rolling(22, min_periods=22).min()
    f["vol_up"] = (v >= vmul * v26) & (c > c.shift(1))
    f["breakout"] = c > h.shift(1).rolling(4).max()
    f["despair"] = f["deep"] & f["no_new_low"] & f["vol_up"] & f["breakout"]
    f["new52"] = c > c.shift(1).rolling(52, min_periods=52).max()
    f["dist"] = c / f["ma"] - 1
    f["r13"] = c / c.shift(13) - 1
    f["consensus"] = (f["dist"] >= 0.30) & (f["v13_pct"] >= 0.70)
    f["bubble"] = ((f["dist"] >= 0.60) | (f["r13"] >= 0.50)) & (f["v13_pct"] >= 0.90)
    f["cashout_raw"] = (v >= vmul * v26) & (h >= h.rolling(26).max()) & (c < o)
    f["low4"], f["low8"], f["low13"] = l.rolling(4).min(), l.rolling(8).min(), l.rolling(13).min()
    return f


def run_theory(w, f, improved=True):
    c, l = w["close"].values, w["low"].values
    n = len(w)
    target = np.zeros(n)
    stage = np.array(["等"] * n, dtype=object)
    events = []
    pos, stop, st = 0.0, np.nan, "等"
    hi_since, weeks23, sold_b, sold_c, hot = np.nan, 0, False, False, False
    for t in range(n):
        r = f.iloc[t]
        if pos == 0:
            if r["despair"]:
                pos, stop, st = 1 / 3, r["low26"], "绝望"
                hi_since, weeks23, sold_b, sold_c, hot = c[t], 0, False, False, False
                events.append((w.index[t], "进场·绝望"))
            elif improved and r["new52"] and not np.isnan(r["low13"]):
                pos, stop, st = 2 / 3, r["low13"], "怀疑"
                hi_since, weeks23, sold_b, sold_c, hot = c[t], 0, False, False, False
                events.append((w.index[t], "进场·价格证明"))
        else:
            if c[t] < stop:
                events.append((w.index[t], f"止损离场（{st}）"))
                pos, st, stop = 0.0, "等", np.nan
            else:
                if st == "绝望" and c[t] > hi_since and r["low8"] > stop:
                    pos, st, weeks23 = 2 / 3, "怀疑", 0
                    stop = max(stop, r["low8"])
                if st == "怀疑":
                    weeks23 += 1
                    stop = max(stop, r["low8"])
                    if c[t] > r["ma"] and r["ma_up"] and weeks23 >= 4 and not sold_b:
                        pos, st = 1.0, "犹豫"
                if st == "犹豫":
                    stop = max(stop, r["low13"])
                if st in ("怀疑", "犹豫") and r["consensus"]:
                    st, hot = "大众共识", True
                if st == "大众共识":
                    stop = max(stop, r["low4"])
                if r["bubble"] and not sold_b:
                    pos, sold_b, st, hot = pos / 2, True, "泡沫", True
                    events.append((w.index[t], "泡沫·卖一半"))
                if st in ("泡沫", "兑现"):
                    # 泡沫段起用“上一周最低价”做止损；兑现段沿用，不再放松（论文：很紧的止损，跌破就走）
                    stop = max(stop, l[t])
                if hot and r["cashout_raw"] and not sold_c:
                    pos, sold_c, st = pos / 2, True, "兑现"
                    stop = max(stop, l[t])
                    events.append((w.index[t], "兑现·再卖一半"))
                hi_since = max(hi_since, c[t])
        target[t] = pos
        stage[t] = st
    return pd.Series(target, index=w.index), pd.Series(stage, index=w.index), events


def run_ma(w, f):
    return (w["close"] > f["ma"]).astype(float).where(f["ma"].notna(), 0.0)


def perf(w, target):
    """周末收盘定仓位，下周开盘执行。"""
    o, c = w["open"], w["close"]
    prev_w = target.shift(1).fillna(0)
    prev_w2 = target.shift(2).fillna(0)
    # 第 t 周：开盘前持有 prev_w2，开盘换成 prev_w
    ret = prev_w2 * (o / c.shift(1) - 1) + prev_w * (c / o - 1) - COST * (prev_w - prev_w2).abs()
    ret = ret.fillna(0)
    nav = (1 + ret).cumprod()
    yrs = (w.index[-1] - w.index[0]).days / 365.25
    cagr = nav.iloc[-1] ** (1 / yrs) - 1
    mdd = (nav / nav.cummax() - 1).min()
    return {"年化": cagr, "最大回撤": mdd, "年化÷回撤": cagr / abs(mdd) if mdd < 0 else np.nan,
            "在场": prev_w.mean(), "买卖次数": int((prev_w.diff().abs() > 1e-9).sum())}, nav


def backtest_one(code, cold=0.30, ma=40, vmul=1.5):
    w = weekly(code)
    f = features(w, cold, ma, vmul)
    start = f["ma"].first_valid_index()
    w2, f2 = w.loc[start:], f.loc[start:]
    res, navs = {}, {}
    bh = pd.Series(1.0, index=w2.index)
    for k, tgt in [("一直拿着", bh), ("简单跟势", run_ma(w2, f2)),
                   ("冬至·论文版", run_theory(w2, f2, False)[0]), ("冬至·改进版", run_theory(w2, f2, True)[0])]:
        res[k], navs[k] = perf(w2, tgt)
    return res, navs


# ---------- 信号检验 ----------
def first_in(mask, gap=26):
    idx, last = [], None
    for t, m in zip(mask.index, mask.values):
        if m and (last is None or (t - last).days > gap * 7):
            idx.append(t); last = t
    return idx


def signal_study(code, rng):
    w = weekly(code)
    f = features(w)
    c = w["close"]
    fwd26, fwd52 = c.shift(-26) / c - 1, c.shift(-52) / c - 1
    fut_min = pd.concat([c.shift(-k) for k in range(1, 27)], axis=1).min(axis=1)
    mdd26 = (fut_min / c - 1).where(c.shift(-26).notna())
    hot_recent = (f["consensus"] | f["bubble"]).rolling(26, min_periods=1).max().astype(bool)
    _, _, ev = run_theory(w.loc[f["ma"].first_valid_index():], f.loc[f["ma"].first_valid_index():], True)
    exits = [t for t, k in ev if k.startswith("止损离场")]
    sig = {"绝望": first_in(f["despair"]), "泡沫": first_in(f["bubble"]),
           "兑现": first_in(f["cashout_raw"] & hot_recent), "止损离场": exits}
    rows = []
    base26, base52, basem = fwd26.dropna(), fwd52.dropna(), mdd26.dropna()
    for k, dates in sig.items():
        d26 = fwd26.reindex(dates).dropna()
        d52 = fwd52.reindex(dates).dropna()
        dm = mdd26.reindex(dates).dropna()
        if len(d26) == 0:
            rows.append({"代码": code, "名称": NAME[code], "信号": k, "次数": 0}); continue
        # 随便挑同样多周的对照：观测均值在随机均值里排第几
        sims = np.array([rng.choice(base26.values, len(d26)).mean() for _ in range(4000)])
        rows.append({"代码": code, "名称": NAME[code], "信号": k, "次数": len(d26),
                     "之后26周": d26.mean(), "平常26周": base26.mean(),
                     "之后52周": d52.mean() if len(d52) else np.nan, "平常52周": base52.mean(),
                     "之后26周最深跌幅": dm.mean(), "平常26周最深跌幅": basem.mean(),
                     "随机里比它低的比例": (sims < d26.mean()).mean()})
    return pd.DataFrame(rows)


EXPECT = {"绝望": "高", "泡沫": "低", "兑现": "低", "止损离场": "低"}

if __name__ == "__main__":
    pd.set_option("display.width", 250)
    codes = list(META["代码"])
    cyc = pd.DataFrame([cyclicality(c) for c in codes])
    cyc.to_csv(OUT / "cyclicality.csv", index=False, encoding="utf-8-sig")
    print("=== 周期性 ===")
    print(cyc.round(2).to_string(index=False))

    rows, allnav = [], {}
    for c in codes:
        res, navs = backtest_one(c)
        allnav[c] = navs
        for k, v in res.items():
            rows.append({"代码": c, "名称": NAME[c], "类别": KIND[c], "做法": k, **v})
    bt = pd.DataFrame(rows)
    bt.to_csv(OUT / "backtest.csv", index=False, encoding="utf-8-sig")
    print("\n=== 回测 ===")
    piv = bt.pivot(index="名称", columns="做法", values="年化÷回撤")[["一直拿着", "简单跟势", "冬至·论文版", "冬至·改进版"]]
    print(piv.round(2).to_string())
    print(bt.pivot(index="名称", columns="做法", values="年化")[["一直拿着", "简单跟势", "冬至·论文版", "冬至·改进版"]].round(3).to_string())
    print(bt.pivot(index="名称", columns="做法", values="最大回撤")[["一直拿着", "简单跟势", "冬至·论文版", "冬至·改进版"]].round(3).to_string())
    print(bt.pivot(index="名称", columns="做法", values="在场")[["一直拿着", "简单跟势", "冬至·论文版", "冬至·改进版"]].round(2).to_string())
    pd.to_pickle(allnav, OUT / "navs.pkl")

    rng = np.random.default_rng(7)
    ss = pd.concat([signal_study(c, rng) for c in codes], ignore_index=True)
    ss.to_csv(OUT / "signals.csv", index=False, encoding="utf-8-sig")
    print("\n=== 信号检验 ===")
    print(ss.round(3).to_string(index=False))
