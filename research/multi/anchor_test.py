"""笔记十四：先认锚，再定谁当家。规矩见 notes/14 第一部分（事先写定）。

跑法：python3 anchor_test.py      结果在 research/output/anchor/
"""
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest

import three_force as TFm

ROOT = TFm.ROOT
AN = ROOT / "data" / "anchor"
OUT = ROOT / "output" / "anchor"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20261108
N_SAMPLE = {"硬锚": 300, "软锚": 800, "未来锚": 1000}
REPS = 2000
COST = 0.001
MONTHS = TFm.MONTHS
NEW_FUT = {"SS0": ("不锈钢", "黑色"), "SP0": ("纸浆", "能化"), "PF0": ("短纤", "能化"), "NR0": ("20号胶", "能化"),
           "LU0": ("低硫燃料油", "能化"), "PG0": ("液化气", "能化"), "CY0": ("棉纱", "能化")}
NEW_IDX = ["sh000852", "sh000922", "sz399005", "sh000986", "sh000987", "sh000988", "sh000989", "sh000990", "sh000991",
           "sh000992", "sh000993", "sh000994", "sh000995", "sz399997", "sz399998", "sz399975", "sz399986", "sz399967",
           "sz399989", "sz399971", "sz399808", "sz399395", "sz399393"]
BASE5 = ["PMI", "PPI同比", "M1同比", "工业增加值同比", "用电量同比"]
ANCHOR_OF = {"工业品期货": "硬锚", "A股大盘": "软锚", "A股个股": "未来锚"}
INCHARGE = {"硬锚": "C", "软锚": "Q", "未来锚": "R"}


def read_opt(p):
    return pd.read_csv(p) if Path(p).exists() else pd.DataFrame()


def build():
    macro = TFm.macro_events()
    mq = TFm.market_q_events()
    paths = TFm.price_paths()
    lifts = pd.read_csv(AN / "lifts.csv", dtype={"SECURITY_CODE": str})
    U = {}
    # 新标的
    for code, (name, grp) in NEW_FUT.items():
        ck = BASE5 + (["商品房销售额同比", "房地产投资同比"] if grp == "黑色" else [])
        U[name] = dict(cls="工业品期货", group=grp, code=code, new=True,
                       daily=TFm.load_daily(TFm.TF / "fut" / f"{code}.csv", code), C={k: macro[k] for k in ck}, Q={}, Qkind="hold")
    for code in NEW_IDX:
        name = paths[code][0]
        U[name] = dict(cls="A股大盘", group="指数", code=code, new=True, daily=TFm.load_daily(paths[code][1]),
                       C={k: macro[k] for k in BASE5}, Q=dict(mq), Qkind="series")
    picked = pd.read_csv(AN / "_picked.csv", dtype={"代码6": str})
    for _, r in picked.iterrows():
        c6 = r["代码6"]
        U[r["名称"]] = dict(cls="A股个股", group="随机新股", code=r["代码"], new=True,
                           daily=TFm.load_daily(AN / "price" / f"{r['代码']}.csv"),
                           fin=read_opt(TFm.TF / "fin" / f"{c6}.csv"), margin=read_opt(TFm.TF / "margin" / f"{c6}.csv"),
                           holder=read_opt(TFm.TF / "holder" / f"{c6}.csv"), Qkind="stock")
    # 老标的（对照）
    for name, u in TFm.build_universe().items():
        u = dict(u, new=False)
        U[name] = u
    for name, u in U.items():
        if u["cls"] == "A股个股":
            c6 = u["code"][2:]
            u["insider"] = read_opt(AN / "insider" / f"{c6}.csv")
            u["buyback"] = read_opt(AN / "buyback" / f"{c6}.csv")
            u["lifts"] = lifts[lifts["SECURITY_CODE"] == c6]
    return U


def direction(L):
    D = L - L.shift(3)
    sgn = np.sign(D).replace(0, np.nan).where(D.notna())
    out, last = sgn.copy(), np.nan
    for i, (dv, sv) in enumerate(zip(D.values, sgn.values)):
        if dv != dv:
            last = np.nan
            continue
        if sv == sv:
            last = sv
        out.iloc[i] = last
    return out


def insider_force(u, cutoff, months):
    """说了算的人：重要股东增减持、解禁压力、回购。只用 cutoff 当时看得到的（解禁日子事先公布）。"""
    first = u["daily"].index.min() + pd.offsets.MonthEnd(0)
    cols = {}
    ins = u["insider"]
    if len(ins):
        x = ins[pd.to_datetime(ins["NOTICE_DATE"]) <= cutoff].dropna(subset=["CHANGE_FREE_RATIO"])
        sign = np.where(x["DIRECTION"].astype(str).str.contains("增"), 1.0, -1.0)
        ev = pd.Series(sign * x["CHANGE_FREE_RATIO"].astype(float).abs().values,
                       index=pd.to_datetime(x["NOTICE_DATE"]) + pd.offsets.MonthEnd(0))
        m = ev.groupby(level=0).sum().reindex(months, fill_value=0.0)
    else:
        m = pd.Series(0.0, index=months)
    net6 = m.rolling(6, min_periods=6).sum().where(months >= first)
    cols["增减持"] = TFm.zexp(net6, 36)
    lf = u["lifts"]
    if len(lf):
        fd = pd.to_datetime(lf["FREE_DATE"]).values
        ratio = pd.to_numeric(lf["TOTAL_RATIO"], errors="coerce").fillna(0).values
        press = []
        for t in months:
            msk = (fd > np.datetime64(t)) & (fd <= np.datetime64(t + pd.offsets.MonthEnd(3)))
            press.append(-ratio[msk].sum())
        lp = pd.Series(press, index=months).where(months >= first)
    else:
        lp = pd.Series(0.0, index=months).where(months >= first)
    cols["解禁压力"] = TFm.zexp(lp, 36)
    bb = u["buyback"]
    if len(bb):
        st = pd.to_datetime(bb["REPURSTARTDATE"], errors="coerce").dropna()
        st = st[st <= cutoff] + pd.offsets.MonthEnd(0)
        cnt = pd.Series(1.0, index=st.values).groupby(level=0).sum().reindex(months, fill_value=0.0)
        b6 = (cnt.rolling(6, min_periods=6).sum() > 0).astype(float).where(months >= first)
    else:
        b6 = pd.Series(0.0, index=months).where(months >= first)
    cols["回购"] = TFm.zexp(b6, 36)
    df = pd.DataFrame(cols)
    comp = df.mean(axis=1, skipna=True)
    L = comp.rolling(3, min_periods=3).mean()
    return L, direction(L)


def all_forces(u, cutoff):
    F = TFm.forces(u, cutoff)
    months = F.index
    if u["cls"] == "A股个股":
        F["LR"], F["DR"] = insider_force(u, cutoff, months)
    return F


def calls(F, anchor):
    k = INCHARGE[anchor]
    out = pd.DataFrame(index=F.index)
    out["当家判断"] = F[f"D{k}"]
    out["只看条件"] = F["DC"]
    out["只看时机"] = F["DT"]
    out["只看取舍"] = F["DQ"]
    if "DR" in F:
        out["只看说了算的人"] = F["DR"]
    out["只看价格"] = np.where(F["ma10"].notna() & F["close"].notna(), np.where(F["close"] > F["ma10"], 1.0, -1.0), np.nan)
    return out


def right(call, fwd):
    return np.where((fwd == 0) | np.isnan(call) | np.isnan(fwd), np.nan, (np.sign(fwd) == call).astype(float))


def mcnemar(a, b):
    """a、b 是同一批题对没对（0/1，nan 不算）。返回 a 对 b 错、a 错 b 对、单边 p。"""
    ok = ~np.isnan(a) & ~np.isnan(b)
    x = int(((a == 1) & (b == 0) & ok).sum())
    y = int(((a == 0) & (b == 1) & ok).sum())
    p = binomtest(x, x + y, 0.5, alternative="greater").pvalue if x + y else 1.0
    return x, y, p


def main():
    t0 = time.time()
    logf = open(OUT / "run.log", "w", encoding="utf-8")

    def say(*a):
        s = " ".join(str(x) for x in a)
        print(s, flush=True)
        logf.write(s + "\n")
        logf.flush()

    U = build()
    say(f"先认锚，再定谁当家  开始 {time.strftime('%Y-%m-%d %H:%M')}  标的 {len(U)} 个；新标的",
        pd.Series([ANCHOR_OF[u['cls']] for u in U.values() if u['new']]).value_counts().to_dict())
    end = MONTHS[-1]
    rows = []
    for name, u in U.items():
        F = all_forces(u, end)
        anc = ANCHOR_OF[u["cls"]]
        C = calls(F, anc)
        c = F["close"]
        for h in (3, 6, 12):
            C[f"之后{h}个月"] = c.shift(-h) / c - 1
        C["标的"], C["锚"], C["组"], C["新标的"] = name, anc, u["group"], u["new"]
        for k in ["LC", "DC", "LT", "DT", "LQ", "DQ", "LR", "DR", "close"]:
            C[k] = F[k] if k in F else np.nan
        rows.append(C.reset_index().rename(columns={"index": "月底"}))
    CEN = pd.concat(rows, ignore_index=True)
    CEN.to_csv(OUT / "census.csv", index=False, encoding="utf-8-sig", float_format="%.4f")
    say(f"整段算完 {time.time() - t0:.0f} 秒")

    rng = np.random.RandomState(SEED)
    elig = CEN[CEN["新标的"] & CEN["当家判断"].notna() & CEN["只看价格"].notna() & CEN["之后6个月"].notna()
               & (CEN["月底"] >= "2012-01-01") & (CEN["月底"] <= "2026-04-30")]
    pick = []
    for anc, n in N_SAMPLE.items():
        pool = elig[elig["锚"] == anc].index.values
        pick += list(rng.choice(pool, size=min(n, len(pool)), replace=False))
    S = CEN.loc[pick].reset_index(drop=True)
    # 遮住未来：切数据从头算，核对
    mism = 0
    for i, r in S.iterrows():
        F = all_forces(U[r["标的"]], r["月底"])
        k = INCHARGE[r["锚"]]
        v = F[f"D{k}"].iloc[-1]
        if not (v == r["当家判断"]):
            mism += 1
    say(f"随机抽题 {len(S)} 道；切数据从头算和整段算不一致的 {mism} 道（应为0）；用时 {time.time() - t0:.0f} 秒")
    names = ["当家判断", "只看条件", "只看时机", "只看取舍", "只看说了算的人", "只看价格"]
    for nm in names:
        if nm in S:
            S[nm + "对了"] = right(S[nm].values.astype(float), S["之后6个月"].values)
    S.to_csv(OUT / "samples.csv", index=False, encoding="utf-8-sig", float_format="%.4f")

    results = {}
    for anc in N_SAMPLE:
        say(f"\n==================== {anc}（当家：{ {'C': '条件', 'Q': '取舍', 'R': '说了算的人'}[INCHARGE[anc]] }） ====================")
        s = S[S["锚"] == anc]
        cen = CEN[(CEN["锚"] == anc) & CEN["新标的"] & CEN["当家判断"].notna()]
        acc = np.nanmean(s["当家判断对了"])
        inst = list(cen["标的"].unique())
        arr = {n: cen[cen["标的"] == n]["当家判断"].values for n in inst}
        posm = {n: {t: i for i, t in enumerate(cen[cen["标的"] == n]["月底"])} for n in inst}
        ki = np.array([inst.index(n) for n in s["标的"]])
        kp = np.array([posm[n][t] for n, t in zip(s["标的"], s["月底"])])
        lens = np.array([len(arr[n]) for n in inst])
        fwd = s["之后6个月"].values
        null = []
        for _ in range(REPS):
            off = np.array([rng.randint(24, L - 24) if L > 60 else rng.randint(1, max(2, L)) for L in lens])
            cc = np.array([arr[inst[i]][(p - off[i]) % lens[i]] for i, p in zip(ki, kp)])
            null.append(np.nanmean(right(cc, fwd)))
        null = np.array(null)
        p1 = (1 + (null >= acc).sum()) / (1 + REPS)
        say(f"题数 {len(s)}，标的 {s['标的'].nunique()} 个；之后6个月涨的题占 {(s['之后6个月'] > 0).mean():.0%}；"
            f"判断在上半圈的占 {(s['当家判断'] > 0).mean():.0%}")
        say(f"标准1  当家那股力对了 {acc:.1%}；瞎猜平均 {null.mean():.1%}，95%分位 {np.percentile(null, 95):.1%}；p = {p1:.4f} → {'过' if p1 < 0.05 else '没过'}")
        res = {"题数": len(s), "当家对的比例": acc, "瞎猜": null.mean(), "标准1": p1 < 0.05}
        tests = [("标准2", "只看价格"), ("标准3", "只看时机")] + ([("标准4", "只看条件")] if anc != "硬锚" else [])
        for lab, other in tests:
            x, y, p = mcnemar(s["当家判断对了"].values, s[other + "对了"].values)
            oa = np.nanmean(s[other + "对了"])
            ok = acc > oa and p < 0.05
            say(f"{lab}  当家 {acc:.1%} vs {other} {oa:.1%}；当家对它错 {x} 道，当家错它对 {y} 道；p = {p:.4f} → {'过' if ok else '没过'}")
            res[lab] = ok
        say("（参考）每一股力单独判断：" + "，".join(f"{nm} {np.nanmean(s[nm + '对了']):.1%}" for nm in names if nm + "对了" in s and s[nm + "对了"].notna().any()))
        for h in (3, 12):
            x = s.dropna(subset=[f"之后{h}个月"])
            say(f"（参考）看之后{h}个月：当家对 {np.nanmean(right(x['当家判断'].values, x[f'之后{h}个月'].values)):.1%}，"
                f"只看价格对 {np.nanmean(right(x['只看价格'].values, x[f'之后{h}个月'].values)):.1%}")
        # 老标的（对照）：整段每个月
        old = CEN[(CEN["锚"] == anc) & ~CEN["新标的"] & CEN["当家判断"].notna() & CEN["之后6个月"].notna()
                  & (CEN["月底"] >= "2012-01-01")]
        if len(old):
            say(f"（对照）老标的整段每个月 {len(old)} 个：当家对 {np.nanmean(right(old['当家判断'].values, old['之后6个月'].values)):.1%}，"
                + "，".join(f"{nm} {np.nanmean(right(old[nm].values.astype(float), old['之后6个月'].values)):.1%}"
                           for nm in names[1:] if nm in old and old[nm].notna().any()))
        results[anc] = res

    # 买卖：上半圈拿着，下半圈空仓（新标的，整段每个月）
    say("\n==================== 上半圈拿着、下半圈空仓（新标的，2012年起，月底判断，下月第一天开盘执行） ====================")
    for anc in N_SAMPLE:
        per = {"当家判断": {}, "10个月均线": {}, "一直拿着": {}}
        for name, u in U.items():
            if not u["new"] or ANCHOR_OF[u["cls"]] != anc:
                continue
            d = u["daily"]
            fo = d.groupby(d.index + pd.offsets.MonthEnd(0))["open"].first().reindex(MONTHS)
            c = CEN[CEN["标的"] == name].set_index("月底")
            c = c[(c.index >= "2011-12-31") & c["当家判断"].notna()]
            if len(c) < 24:
                continue
            ret = np.nan_to_num(fo.shift(-2).reindex(c.index).values / fo.shift(-1).reindex(c.index).values - 1)
            idx = c.index + pd.offsets.MonthEnd(1)
            for lab, pos in [("当家判断", (c["当家判断"] > 0).astype(float).values),
                             ("10个月均线", (c["只看价格"] > 0).astype(float).values), ("一直拿着", np.ones(len(c)))]:
                prev = np.r_[0, pos[:-1]]
                per[lab][name] = pd.Series(pos * ret - COST * np.abs(pos - prev) * (lab != "一直拿着"), index=idx)
        say(f"{anc}（{len(per['当家判断'])}个）：")
        for lab, d in per.items():
            P = pd.DataFrame(d).mean(axis=1)
            P = P[P.index <= "2026-10-31"]
            nav = (1 + P).cumprod()
            cagr = nav.iloc[-1] ** (12 / len(P)) - 1
            mdd = (nav / nav.cummax() - 1).min()
            say(f"  {lab:6s} 年化 {cagr:6.1%}  最大回撤 {mdd:6.1%}  年化÷回撤 {cagr / abs(mdd):5.2f}")
    say("\n=== 汇总（只看新标的） ===")
    say(pd.DataFrame(results).T.to_string())
    pd.to_pickle(results, OUT / "results.pkl")
    say(f"\n全部完成，用时 {time.time() - t0:.0f} 秒")


if __name__ == "__main__":
    main()
