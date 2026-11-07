"""冬至理论论证：H1–H4。规则见 notes/04-论证：冬至理论有没有效果.md 第一部分（事先写定）。"""
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).parent / "output"
DATA = Path(__file__).parent / "data"
RNG = np.random.default_rng(20261107)


# ---------- 公共数据 ----------
def monthly():
    df = pd.read_csv(OUT / "monthly.csv", index_col=0)
    df.index = pd.PeriodIndex(df.index, freq="M")
    return df


def pct_rank(s, window=None, min_obs=24):
    """当月值在“当时以前（含当月）”历史里的分位，0–1。window=None 表示用全部过去。"""
    out = pd.Series(np.nan, index=s.index)
    vals = s.values
    for i in range(len(s)):
        if np.isnan(vals[i]):
            continue
        lo = 0 if window is None else max(0, i - window + 1)
        hist = vals[lo:i + 1]
        hist = hist[~np.isnan(hist)]
        if len(hist) >= min_obs:
            out.iloc[i] = (hist <= vals[i]).mean()
    return out


def heat(df, window=None):
    tr = (df["turnover"] / df["mktcap"]).rolling(3, min_periods=3).mean()
    mr = (df["margin"] / df["mktcap"]).rolling(3, min_periods=3).mean()
    h = pd.concat([pct_rank(tr, window), pct_rank(mr, window)], axis=1).mean(axis=1)
    return h


def direction(p, L=6):
    """破前低转下半圈，破前高转上半圈。返回 +1（上半圈）/ -1（下半圈）。"""
    hi = p.shift(1).rolling(L, min_periods=L).max()
    lo = p.shift(1).rolling(L, min_periods=L).min()
    st, cur = [], np.nan
    for x, h, l in zip(p.values, hi.values, lo.values):
        if not np.isnan(h):
            if x > h:
                cur = 1
            elif x < l:
                cur = -1
            elif np.isnan(cur):
                cur = 1 if x >= (h + l) / 2 else -1
        st.append(cur)
    return pd.Series(st, index=p.index)


def fwd(p, k):
    return p.shift(-k) / p - 1


def fwd_mdd(p, k=12):
    fut = pd.concat([p.shift(-j) for j in range(1, k + 1)], axis=1).min(axis=1)
    return (fut / p - 1).where(p.shift(-k).notna())


# ---------- H1 ----------
def h1(df, window=None, verbose=True):
    p = df["mkt_idx"]
    h = heat(df, window)
    t = pd.DataFrame({"heat": h, "f1": fwd(p, 1), "f3": fwd(p, 3), "f6": fwd(p, 6),
                      "f12": fwd(p, 12), "mdd12": fwd_mdd(p, 12)}).dropna(subset=["heat"])
    t["组"] = np.where(t["heat"] >= 0.8, "热（前20%）", np.where(t["heat"] <= 0.2, "冷（后20%）", "中间"))
    g = t.groupby("组")[["f1", "f3", "f6", "f12", "mdd12"]].mean()
    g["月数"] = t.groupby("组").size()
    g = g.loc[["冷（后20%）", "中间", "热（前20%）"]]
    # 循环平移检验：热度和后12个月涨跌的相关，理论预测为负
    x = t.dropna(subset=["f12"])
    obs = np.corrcoef(x["heat"], x["f12"])[0, 1]
    hv, fv = x["heat"].values, x["f12"].values
    T = len(hv)
    null = [np.corrcoef(np.roll(hv, k), fv)[0, 1] for k in range(12, T - 12)]
    p_one = np.mean(np.array(null) <= obs)
    # 热的“段落”：热度从不足80%升到80%以上的那个月
    starts = t.index[(t["heat"] >= 0.8) & (t["heat"].shift(1) < 0.8)]
    colds = t.index[(t["heat"] <= 0.2) & (t["heat"].shift(1) > 0.2)]
    ep = pd.DataFrame({"开始": list(starts) + list(colds),
                       "类型": ["热"] * len(starts) + ["冷"] * len(colds)})
    ep["之后12个月"] = [t.loc[i, "f12"] for i in ep["开始"]]
    ep["之后12个月最深跌幅"] = [t.loc[i, "mdd12"] for i in ep["开始"]]
    if verbose:
        print("\n=== H1 热度和之后的涨跌 ===")
        print(g.round(3).to_string())
        print(f"热度与之后12个月涨跌的相关 {obs:+.2f}；循环平移下这么负（或更负）的概率 p={p_one:.3f}")
        print(ep.sort_values("开始").round(3).to_string(index=False))
    return g, obs, p_one, ep


# ---------- H2 ----------
def zigzag(p, th=0.25):
    """价格从上一个拐点反向走了 th 以上，就确认上一个拐点。"""
    pts, mode = [], None
    ext_i, ext_v = p.index[0], p.iloc[0]
    for i, v in p.items():
        if mode is None:
            if v >= ext_v * (1 + th):
                mode, ext_i, ext_v = "up", i, v
                pts.append((p.loc[:i].idxmin(), "底"))
            elif v <= ext_v * (1 - th):
                mode, ext_i, ext_v = "down", i, v
                pts.append((p.loc[:i].idxmax(), "顶"))
            continue
        if mode == "up":
            if v > ext_v:
                ext_i, ext_v = i, v
            elif v <= ext_v * (1 - th):
                pts.append((ext_i, "顶")); mode, ext_i, ext_v = "down", i, v
        else:
            if v < ext_v:
                ext_i, ext_v = i, v
            elif v >= ext_v * (1 + th):
                pts.append((ext_i, "底")); mode, ext_i, ext_v = "up", i, v
    return pts


def h2(df, verbose=True):
    p = df["mkt_idx"].dropna()
    pts = zigzag(p)
    c3 = lambda s: s.rolling(3, center=True, min_periods=2).mean()
    tr = c3(df["turnover"] / df["mktcap"])
    mg = df["margin"]
    rows = []
    for j, (t0, kind) in enumerate(pts):
        a = pts[j - 1][0] if j > 0 else p.index[0]
        b = pts[j + 1][0] if j + 1 < len(pts) else p.index[-1]
        lo = t0 - (t0 - a).n // 2
        hi = t0 + (b - t0).n // 2
        row = {"拐点": str(t0), "类型": kind}
        for name, s in [("换手率", tr), ("融资余额", mg)]:
            x = s.loc[lo:hi].dropna()
            if len(x) < 4 or not (x.index[0] <= t0 <= x.index[-1]):
                row[name] = np.nan
                continue
            t = x.idxmax() if kind == "顶" else x.idxmin()
            row[name] = (t - t0).n
        rows.append(row)
    r = pd.DataFrame(rows)
    # 理论预测：换手率（天量/地量）先于价格，融资余额晚于价格
    def score(col, want):
        x = r[col].dropna()
        hit = (x < 0).sum() if want == "先" else (x > 0).sum()
        miss = (x > 0).sum() if want == "先" else (x < 0).sum()
        tie = (x == 0).sum()
        from math import comb
        n = hit + miss
        pval = sum(comb(n, k) for k in range(hit, n + 1)) / 2 ** n if n else np.nan
        return hit, miss, tie, pval
    res = {}
    for kind in ["顶", "底"]:
        sub = r[r["类型"] == kind]
        for col, want in [("换手率", "先"), ("融资余额", "后")]:
            x = sub[col].dropna()
            hit = int((x < 0).sum() if want == "先" else (x > 0).sum())
            miss = int((x > 0).sum() if want == "先" else (x < 0).sum())
            res[(kind, col)] = (hit, miss, int((x == 0).sum()))
    if verbose:
        print("\n=== H2 拐点上的先后（负数=比价格早几个月，正数=晚几个月） ===")
        print(r.to_string(index=False))
        for k, v in res.items():
            print(f"{k[0]} {k[1]}：符合预测 {v[0]}，相反 {v[1]}，同月 {v[2]}")
    return r, res


# ---------- H3 ----------
def h3(df, L=6, verbose=True):
    ev = pd.read_csv(DATA / "rrr.csv")
    ev["chg"] = ev["INTEREST_RATE_BA"] - ev["INTEREST_RATE_BB"]
    ev = ev.drop_duplicates("REPORT_DATE")
    ev = ev[ev["chg"] != 0].copy()
    ev["date"] = pd.to_datetime(ev["REPORT_DATE"])
    ev["ym_prev"] = ev["date"].dt.to_period("M") - 1
    st = direction(df["mkt_idx"], L)
    ev["半圈"] = ev["ym_prev"].map(lambda m: st.get(m, np.nan))
    ev = ev.dropna(subset=["半圈"])
    ev["消息"] = np.where(ev["chg"] < 0, "降准（好消息）", "升准（坏消息）")
    ev["半圈"] = ev["半圈"].map({1: "上半圈", -1: "下半圈"})
    ev["次日上证"] = ev["NEXT_SH_RATE"]
    g = ev.groupby(["消息", "半圈"])["次日上证"].agg(["count", "mean", "median", lambda x: (x > 0).mean()])
    g.columns = ["次数", "平均", "中位数", "上涨比例"]
    # 置换检验：同一种消息里，打乱半圈标签，看上下半圈的差别有多常见
    pv = {}
    for news, sub in ev.groupby("消息"):
        up = sub["半圈"] == "上半圈"
        if up.sum() == 0 or (~up).sum() == 0:
            continue
        obs = sub.loc[up, "次日上证"].mean() - sub.loc[~up, "次日上证"].mean()
        vals = sub["次日上证"].values
        null = []
        for _ in range(20000):
            perm = RNG.permutation(up.values)
            null.append(vals[perm].mean() - vals[~perm].mean())
        pv[news] = (obs, np.mean(np.array(null) >= obs))
    if verbose:
        print("\n=== H3 存款准备金率调整：公布次日上证涨跌（%） ===")
        print(g.round(2).to_string())
        for k, (o, pp) in pv.items():
            print(f"{k}：上半圈比下半圈平均多涨 {o:+.2f} 个百分点，置换检验 p={pp:.3f}")
        print(ev[["REPORT_DATE", "消息", "半圈", "次日上证"]].assign(REPORT_DATE=ev["REPORT_DATE"].str[:10]).round(2).to_string(index=False))
    return g, pv, ev


# ---------- H4 ----------
def backtest(df, L=6, hot=0.8, cold=0.2, window=None, start="2010-01", end=None):
    p = df["mkt_idx"]
    st = direction(p, L)
    h = heat(df, window)
    r_next = p.shift(-1) / p - 1      # 下个月的涨跌
    idx = p.loc[start:end].index
    pos = {k: [] for k in ["A", "B", "C1", "C2", "C"]}
    hot_seen = False       # 这个上半圈里是否已经热过
    cold_seen = True       # 这个下半圈里是否已经冷过（开头视为见过）
    in_c2 = False
    in_c = False
    prev_state = None
    for t in idx:
        s, hh = st[t], h[t]
        if s != prev_state:
            if s == -1:
                cold_seen = False
            if s == 1:
                hot_seen = False
        if not np.isnan(hh):
            if hh >= hot and s == 1:
                hot_seen = True
            if hh <= cold and s == -1:
                cold_seen = True
        b = 1.0 if s == 1 else 0.0
        c1 = (0.5 if hot_seen else 1.0) if s == 1 else 0.0
        # C2：进入上半圈时，只有下半圈里见过“冷”才进；没进的就一直等到下一次
        if s == 1 and prev_state == -1:
            in_c2 = cold_seen
            in_c = cold_seen
        if s == -1:
            in_c2 = in_c = False
        if prev_state is None:
            in_c2 = in_c = (s == 1)
        c2 = 1.0 if (s == 1 and in_c2) else 0.0
        c = c1 if (s == 1 and in_c) else 0.0
        for k, v in zip(["A", "B", "C1", "C2", "C"], [1.0, b, c1, c2, c]):
            pos[k].append(v)
        prev_state = s
    P = pd.DataFrame(pos, index=idx)
    R = P.mul(r_next.loc[idx], axis=0).dropna()
    return P, R


def stats(R, P):
    out = {}
    for k in R.columns:
        nav = (1 + R[k]).cumprod()
        yrs = len(R) / 12
        cagr = nav.iloc[-1] ** (1 / yrs) - 1
        mdd = (nav / nav.cummax() - 1).min()
        out[k] = {"年化": cagr, "最大回撤": mdd, "年化/回撤": cagr / abs(mdd) if mdd < 0 else np.nan,
                  "在场时间": P[k].loc[R.index].mean(), "调仓次数": int((P[k].diff().abs() > 0).sum()),
                  "期末净值": nav.iloc[-1]}
    return pd.DataFrame(out).T


NAMES = {"A": "A 一直拿着", "B": "B 只看方向（破前低走、破前高进）", "C1": "C1 B+热时减半",
         "C2": "C2 B+没见过冷不再进", "C": "C 冬至理论（C1+C2）"}


def h4(df, verbose=True):
    P, R = backtest(df)
    s = stats(R, P)
    s.index = [NAMES[k] for k in s.index]
    halves = {}
    for a, b in [("2010-01", "2017-12"), ("2018-01", None)]:
        P2, R2 = backtest(df, start=a, end=b)
        halves[f"{a[:4]}–{(b or '2026')[:4]}"] = stats(R2, P2)
    grid = []
    for L in [3, 6, 9, 12]:
        for hot in [0.7, 0.8, 0.9]:
            for cold in [0.1, 0.2, 0.3]:
                for w in [None, 60]:
                    Pg, Rg = backtest(df, L=L, hot=hot, cold=cold, window=w)
                    sg = stats(Rg, Pg)
                    grid.append({"L": L, "hot": hot, "cold": cold, "window": w or "全部",
                                 **{f"{k}_年化/回撤": sg.loc[k, "年化/回撤"] for k in sg.index},
                                 **{f"{k}_最大回撤": sg.loc[k, "最大回撤"] for k in sg.index},
                                 **{f"{k}_年化": sg.loc[k, "年化"] for k in sg.index}})
    G = pd.DataFrame(grid)
    if verbose:
        print("\n=== H4 回测（2010-01 起，月度） ===")
        print(s.round(3).to_string())
        for k, v in halves.items():
            v.index = [NAMES[i] for i in v.index]
            print(f"\n-- {k} --")
            print(v[["年化", "最大回撤", "年化/回撤", "在场时间"]].round(3).to_string())
        print(f"\n-- 参数换一圈（{len(G)} 组） --")
        for k in ["C1", "C2", "C"]:
            better_ratio = (G[f"{k}_年化/回撤"] > G["B_年化/回撤"]).mean()
            better_mdd = (G[f"{k}_最大回撤"] > G["B_最大回撤"]).mean()
            better_ret = (G[f"{k}_年化"] > G["B_年化"]).mean()
            print(f"{NAMES[k]} 比 B：年化/回撤更好 {better_ratio:.0%}，回撤更小 {better_mdd:.0%}，年化更高 {better_ret:.0%}")
        print(f"B 比 A：年化/回撤更好 {(G['B_年化/回撤'] > G['A_年化/回撤']).mean():.0%}，回撤更小 {(G['B_最大回撤'] > G['A_最大回撤']).mean():.0%}")
        print("各做法年化/回撤的中位数：", {NAMES[k]: round(G[f'{k}_年化/回撤'].median(), 3) for k in ['A', 'B', 'C1', 'C2', 'C']})
    return s, halves, G, P, R


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    df = monthly()
    g1, o1, p1, ep = h1(df)
    print("\n（稳健性）热度只用过去60个月排位：")
    h1(df, window=60, verbose=False)
    g1b, o1b, p1b, _ = h1(df, window=60, verbose=False)
    print(g1b.round(3).to_string()); print(f"相关 {o1b:+.2f}，p={p1b:.3f}")
    r2, res2 = h2(df)
    g3, pv3, ev3 = h3(df)
    s4, halves4, G4, P4, R4 = h4(df)
    g1.to_csv(OUT / "validate_h1.csv", encoding="utf-8-sig")
    ep.to_csv(OUT / "validate_h1_episodes.csv", index=False, encoding="utf-8-sig")
    r2.to_csv(OUT / "validate_h2.csv", index=False, encoding="utf-8-sig")
    ev3.to_csv(OUT / "validate_h3_events.csv", index=False, encoding="utf-8-sig")
    s4.to_csv(OUT / "validate_h4.csv", encoding="utf-8-sig")
    G4.to_csv(OUT / "validate_h4_grid.csv", index=False, encoding="utf-8-sig")
    P4.to_csv(OUT / "validate_h4_positions.csv", encoding="utf-8-sig")
