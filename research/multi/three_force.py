"""笔记十二：用条件、时机、取舍判断阶段，随机抽题、遮住未来。规矩见 notes/12 第一部分（事先写定）。

跑法：python3 three_force.py      结果在 research/output/three_force/
"""
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TF = ROOT / "data" / "tf"
OUT = ROOT / "output" / "three_force"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20261107
N_SAMPLE = {"A股大盘": 400, "工业品期货": 800, "A股个股": 1200}
REPS = 2000
COST = 0.001
STAGES = ["绝望", "怀疑", "犹豫", "大众共识", "泡沫", "兑现", "幻想", "侥幸", "瓦解", "麻木", "恐慌", "衰竭"]
UNCLEAR = "观不清"
POS = {"绝望": 1 / 3, "怀疑": 2 / 3, "犹豫": 1, "大众共识": 1, "泡沫": 1, "兑现": 0.5, "幻想": 0.5,
       "侥幸": 0, "瓦解": 0, "麻木": 0, "恐慌": 0, "衰竭": 0}
ZIG = {"A股大盘": 0.20, "工业品期货": 0.25, "A股个股": 0.30}
MONTHS = pd.date_range("2006-01-31", "2026-10-31", freq="ME")

INDEX = {"sh000001": "上证指数", "sh000300": "沪深300", "sz399001": "深证成指", "sh000905": "中证500",
         "sh000016": "上证50", "sz399006": "创业板指"}
FUT = {"有色": {"CU0": "沪铜", "AL0": "沪铝", "ZN0": "沪锌", "PB0": "沪铅", "NI0": "沪镍", "SN0": "沪锡"},
       "黑色": {"RB0": "螺纹钢", "HC0": "热卷", "I0": "铁矿石", "J0": "焦炭", "JM0": "焦煤", "SF0": "硅铁",
              "SM0": "锰硅", "FG0": "玻璃", "SA0": "纯碱"},
       "能化": {"TA0": "PTA", "MA0": "甲醇", "L0": "塑料", "PP0": "聚丙烯", "V0": "PVC", "BU0": "沥青",
              "RU0": "橡胶", "EG0": "乙二醇", "EB0": "苯乙烯", "FU0": "燃料油", "SC0": "原油", "UR0": "尿素"}}
GROUPS = {
    "农业养殖": ["牧原股份", "温氏股份", "新希望", "天邦食品", "唐人神", "海大集团", "北大荒", "隆平高科"],
    "医药中药": ["恒瑞医药", "迈瑞医疗", "片仔癀", "云南白药", "同仁堂", "东阿阿胶", "华润三九", "以岭药业"],
    "消费": ["贵州茅台", "五粮液", "山西汾酒", "泸州老窖", "伊利股份", "海天味业", "中国中免", "格力电器", "美的集团", "海尔智家"],
    "金融": ["中信证券", "东方财富", "华泰证券", "招商银行", "中国平安", "兴业银行", "工商银行", "民生银行", "中国太保"],
    "资源周期": ["中国神华", "紫金矿业", "海螺水泥", "中国石化", "中国石油", "宝钢股份", "江西铜业", "中国铝业", "洛阳钼业",
             "兖矿能源", "陕西煤业", "盐湖股份", "天齐锂业", "万华化学", "中远海控"],
    "制造科技": ["三一重工", "比亚迪", "宁德时代", "隆基绿能", "海康威视", "立讯精密", "京东方A", "北方华创", "上汽集团", "特变电工"],
    "公用地产基建": ["长江电力", "万科A", "保利发展", "中国建筑", "中国中铁"],
}


# ---------------------------------------------------------------- 原始数据，每条都带“哪天能看到”
def month_end(d):
    return (pd.Timestamp(d) + pd.offsets.MonthEnd(0)).normalize()


def macro_events():
    """宏观：第 m 月的数，到 m+1 月底才算看得到。返回 {名称: Series(index=能看到的月底, value)}。"""
    mm = pd.read_csv(ROOT / "output" / "monthly.csv")
    mm["m"] = pd.to_datetime(mm["ym"]) + pd.offsets.MonthEnd(0)
    ev = {}
    for col, name in [("pmi", "PMI"), ("ppi_yoy", "PPI同比"), ("m1_yoy", "M1同比")]:
        s = mm.set_index("m")[col].dropna()
        ev[name] = pd.Series(s.values - (50 if col == "pmi" else 0), index=s.index + pd.offsets.MonthEnd(1))

    def monthly(name):
        d = pd.read_csv(TF / f"macro_{name}.csv")
        s = pd.Series(d["value"].values, index=pd.to_datetime(d["date"]) + pd.offsets.MonthEnd(0)).sort_index()
        return s[~s.index.duplicated()]

    s = monthly("工业增加值同比")
    ev["工业增加值同比"] = pd.Series(s.values, index=s.index + pd.offsets.MonthEnd(1))
    for name, key in [("工业用电量当月", "用电量同比"), ("商品房销售额当月", "商品房销售额同比")]:
        s = monthly(name).reindex(pd.date_range(monthly(name).index[0], monthly(name).index[-1], freq="ME"))
        yoy = (s / s.shift(12) - 1) * 100
        yoy = yoy.rolling(3, min_periods=1).mean().dropna()
        ev[key] = pd.Series(yoy.values, index=yoy.index + pd.offsets.MonthEnd(1))
    s = monthly("房地产开发投资累计")
    s = s.reindex(pd.date_range(s.index[0], s.index[-1], freq="ME"))
    yoy = ((s / s.shift(12) - 1) * 100).dropna()
    ev["房地产投资同比"] = pd.Series(yoy.values, index=yoy.index + pd.offsets.MonthEnd(1))
    return ev


def market_q_events():
    """A股大盘的取舍：全市场融资余额6个月变化；新股加增发12个月合计占总市值。月底就看得到。"""
    mm = pd.read_csv(ROOT / "output" / "monthly.csv")
    mm["m"] = pd.to_datetime(mm["ym"]) + pd.offsets.MonthEnd(0)
    mm = mm.set_index("m")
    mg = np.log(mm["margin"]).diff(6)
    raise_ = (mm["ipo"].fillna(0) + mm["seo"].fillna(0)).rolling(12, min_periods=12).sum() / mm["mktcap"] * 100
    return {"融资余额6个月变化": mg.dropna(), "募资占市值": raise_.dropna()}


def load_daily(path, code=None):
    """数据修正（跑结果之前发现，见 notes/12 第二部分）：
    沪锡第一天价格是坏数据；燃料油 2014–2018 年几乎没人交易（15个月成交量为0），2018-07-16 新合约上市后才用。"""
    d = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    if code == "SN0":
        d = d.drop(pd.to_datetime(["2015-03-27"]), errors="ignore")
    if code == "FU0":
        d = d[d.index >= "2018-07-16"]
    return d[(d["close"] > 0)]


def price_paths():
    paths = {}
    for sub in ["multi", "multi2", "multi3"]:
        meta = pd.read_csv(ROOT / "data" / sub / "_meta.csv")
        for _, r in meta.iterrows():
            paths[r["代码"]] = (r["名称"], ROOT / "data" / sub / f"{r['代码']}.csv")
    return paths


def build_universe():
    """每个标的：类别、组、日线、取舍和条件的原始事件。"""
    macro = macro_events()
    mq = market_q_events()
    paths = price_paths()
    U = {}
    base5 = ["PMI", "PPI同比", "M1同比", "工业增加值同比", "用电量同比"]
    for code, name in INDEX.items():
        U[name] = dict(cls="A股大盘", group="指数", code=code, daily=load_daily(paths[code][1]),
                       C={k: macro[k] for k in base5}, Q=dict(mq), Qkind="series")
    for grp, d in FUT.items():
        ckeys = base5 + (["商品房销售额同比", "房地产投资同比"] if grp == "黑色" else [])
        for code, name in d.items():
            daily = load_daily(TF / "fut" / f"{code}.csv", code)
            U[name] = dict(cls="工业品期货", group=grp, code=code, daily=daily,
                           C={k: macro[k] for k in ckeys}, Q={}, Qkind="hold")
    for grp, names in GROUPS.items():
        for name in names:
            code = next(c for c, (n, _) in paths.items() if n == name)
            c6 = code[2:]
            fin = pd.read_csv(TF / "fin" / f"{c6}.csv") if (TF / "fin" / f"{c6}.csv").exists() else pd.DataFrame()
            mg = pd.read_csv(TF / "margin" / f"{c6}.csv") if (TF / "margin" / f"{c6}.csv").exists() else pd.DataFrame()
            hd = pd.read_csv(TF / "holder" / f"{c6}.csv") if (TF / "holder" / f"{c6}.csv").exists() else pd.DataFrame()
            U[name] = dict(cls="A股个股", group=grp, code=code, daily=load_daily(paths[code][1]),
                           fin=fin, margin=mg, holder=hd, Qkind="stock")
    return U


# ---------------------------------------------------------------- 遮住未来：只用 cutoff 以前看得到的东西
def zexp(s, minp):
    m = s.expanding(min_periods=minp).mean()
    sd = s.expanding(min_periods=minp).std()
    return (s - m) / sd.replace(0, np.nan)


def asof_monthly(ev, months):
    """事件序列（index=能看到的日子）→ 每个月底能看到的最新值。"""
    ev = ev.sort_index()
    pos = np.searchsorted(ev.index.values, months.values, side="right") - 1
    out = np.where(pos >= 0, ev.values[np.clip(pos, 0, None)], np.nan)
    return pd.Series(out, index=months)


def monthly_price(daily, months):
    g = daily.groupby(daily.index + pd.offsets.MonthEnd(0))
    m = pd.DataFrame({"close": g["close"].last(), "volume": g["volume"].sum()})
    if "hold" in daily:
        m["hold"] = g["hold"].mean()
    return m.reindex(months)


def forces(u, cutoff):
    """只用 cutoff（某个月底）以前看得到的数据，从头算三股力。返回每个月的 L（3个月平均后的分数）和 D（3个月方向）。"""
    months = MONTHS[MONTHS <= cutoff]
    daily = u["daily"][u["daily"].index <= cutoff]
    mp = monthly_price(daily, months)
    c = mp["close"]
    # 时机
    ma10 = c.rolling(10, min_periods=10).mean()
    vol = mp["volume"].where(mp["volume"] > 0)
    T = pd.DataFrame({"离均线": zexp(c / ma10 - 1, 36), "6个月涨跌": zexp(np.log(c).diff(6), 36),
                      "成交量": zexp(np.log(vol.rolling(3, min_periods=3).mean() / vol.rolling(12, min_periods=12).mean()), 36)})
    # 条件、取舍
    if u["cls"] in ("A股大盘", "工业品期货"):
        C = pd.DataFrame({k: zexp(asof_monthly(ev[ev.index <= cutoff], months), 36) for k, ev in u["C"].items()})
    else:
        fin = u["fin"]
        cols = {}
        if len(fin):
            f = fin[pd.to_datetime(fin["NOTICE_DATE"]) <= cutoff].copy()
            f = f.sort_values(["NOTICE_DATE", "REPORTDATE"], kind="mergesort").drop_duplicates("REPORTDATE", keep="last")
            for col, nm in [("YSTZ", "营收同比"), ("SJLTZ", "净利润同比")]:
                v = f[col].clip(-100, 200)
                z = zexp(v.reset_index(drop=True), 8)
                ev = pd.Series(z.values, index=pd.to_datetime(f["NOTICE_DATE"]).values).dropna()
                ev = ev[~ev.index.duplicated(keep="last")]
                cols[nm] = asof_monthly(ev, months) if len(ev) else pd.Series(np.nan, index=months)
        C = pd.DataFrame(cols, index=months)
    if u["Qkind"] == "series":
        Q = pd.DataFrame({k: zexp(asof_monthly(ev[ev.index <= cutoff], months), 36) for k, ev in u["Q"].items()})
    elif u["Qkind"] == "hold":
        h = mp["hold"].where(mp["hold"] > 0)
        Q = pd.DataFrame({"持仓量": zexp(np.log(h.rolling(3, min_periods=3).mean() / h.rolling(24, min_periods=24).mean()), 36)})
    else:
        cols = {}
        mg = u["margin"]
        if len(mg):
            s = pd.Series(mg["RZYE"].values, index=pd.to_datetime(mg["DATE"])).sort_index()
            s = s[s.index <= cutoff]
            sm = s.groupby(s.index + pd.offsets.MonthEnd(0)).last().reindex(months)
            sm = sm.where(sm > 0)
            cols["融资余额6个月变化"] = zexp(np.log(sm).diff(6), 36)
        hd = u["holder"]
        if len(hd):
            h = hd.dropna(subset=["HOLDER_NUM", "HOLD_NOTICE_DATE"])
            h = h[pd.to_datetime(h["HOLD_NOTICE_DATE"]) <= cutoff].sort_values(["HOLD_NOTICE_DATE", "END_DATE"], kind="mergesort")
            ev = pd.Series(h["HOLDER_NUM"].values.astype(float), index=pd.to_datetime(h["HOLD_NOTICE_DATE"]).values)
            ev = ev[~ev.index.duplicated(keep="last")]
            hm = asof_monthly(ev, months) if len(ev) else pd.Series(np.nan, index=months)
            hm = hm.where(hm > 0)
            cols["股东户数6个月变化"] = zexp(np.log(hm).diff(6), 36)
        Q = pd.DataFrame(cols, index=months)
    out = {}
    for k, df in [("C", C), ("T", T), ("Q", Q)]:
        comp = df.mean(axis=1, skipna=True) if df.shape[1] else pd.Series(np.nan, index=months)
        L = comp.rolling(3, min_periods=3).mean()
        D = L - L.shift(3)
        sgn = np.sign(D).replace(0, np.nan)
        sgn = sgn.where(D.notna())
        # 3个月没变化的，沿用上一次的方向
        filled = sgn.copy()
        last = np.nan
        for i, (dv, sv) in enumerate(zip(D.values, sgn.values)):
            if dv != dv:
                last = np.nan
                continue
            if sv == sv:
                last = sv
            filled.iloc[i] = last
        out[f"L{k}"], out[f"D{k}"] = L, filled
    out["close"] = c
    out["ma10"] = ma10
    return pd.DataFrame(out)


def stage_of(LC, DC, LT, DT, LQ, DQ):
    if any(x != x for x in (LC, DC, LT, DT, LQ, DQ)):
        return None
    key = (DC > 0, DT > 0, DQ > 0)
    if key == (True, False, False):
        return "绝望" if LC < 0 else "怀疑"
    if key == (True, True, False):
        return "犹豫" if LT < 0 else "大众共识"
    if key == (True, True, True):
        return "泡沫" if LQ < 0 else "兑现"
    if key == (False, True, True):
        return "幻想" if LC > 0 else "侥幸"
    if key == (False, False, True):
        return "瓦解" if LT > 0 else "麻木"
    if key == (False, False, False):
        return "恐慌" if LQ > 0 else "衰竭"
    return UNCLEAR


def call_of(stage, DC):
    """上半圈=1，下半圈=-1。观不清以条件为准。"""
    if stage is None:
        return np.nan
    if stage == UNCLEAR:
        return 1 if DC > 0 else -1
    return 1 if STAGES.index(stage) < 6 else -1


def judge(u, cutoff):
    F = forces(u, cutoff)
    r = F.iloc[-1]
    st = stage_of(r.LC, r.DC, r.LT, r.DT, r.LQ, r.DQ)
    return st, r


# ---------------------------------------------------------------- 事后回头观：之字形找高低点，每段按时间平均分六段
def zigzag(v, th):
    """涨跌超过 th 才算一段。返回 [(位置, '高'/'低')]，最后一个没确认的不算。"""
    pts, mode, ext, hi_i, lo_i = [], 0, 0, 0, 0
    for i in range(1, len(v)):
        if mode == 0:
            hi_i = i if v[i] > v[hi_i] else hi_i
            lo_i = i if v[i] < v[lo_i] else lo_i
            if v[i] >= v[lo_i] * (1 + th):
                pts.append((lo_i, "低"))
                mode, ext = 1, i
            elif v[i] <= v[hi_i] * (1 - th):
                pts.append((hi_i, "高"))
                mode, ext = -1, i
        elif mode == 1:
            if v[i] > v[ext]:
                ext = i
            elif v[i] <= v[ext] * (1 - th):
                pts.append((ext, "高"))
                mode, ext = -1, i
        else:
            if v[i] < v[ext]:
                ext = i
            elif v[i] >= v[ext] * (1 + th):
                pts.append((ext, "低"))
                mode, ext = 1, i
    return pts


def hindsight(close, th):
    """事后回头观：低点到高点按时间平均分成绝望到兑现，高点到低点分成幻想到衰竭。"""
    c = close.dropna()
    lab = pd.Series(None, index=close.index, dtype=object)
    if len(c) < 3:
        return lab
    pts = zigzag(c.values, th)
    for (a, ka), (b, kb) in zip(pts[:-1], pts[1:]):
        for k in range(a, b):
            part = min(5, int(6 * (k - a) / (b - a)))
            lab[c.index[k]] = STAGES[part] if ka == "低" else STAGES[6 + part]
    return lab


def ring_dist(a, b):
    d = abs(STAGES.index(a) - STAGES.index(b))
    return min(d, 12 - d)


# ---------------------------------------------------------------- 主程序
def main():
    t0 = time.time()
    logf = open(OUT / "run.log", "w", encoding="utf-8")

    def say(*a):
        s = " ".join(str(x) for x in a)
        print(s, flush=True)
        logf.write(s + "\n")
        logf.flush()

    U = build_universe()
    say(f"三股力判断阶段  开始 {time.strftime('%Y-%m-%d %H:%M')}  标的 {len(U)} 个",
        pd.Series([u['cls'] for u in U.values()]).value_counts().to_dict())
    end = MONTHS[-1]
    # 1) 整段算一遍（每个标的每个月），只用来核对和做对照
    rows = []
    for name, u in U.items():
        F = forces(u, end)
        lab = hindsight(F["close"], ZIG[u["cls"]])
        c = F["close"]
        for h in (3, 6, 12):
            F[f"之后{h}个月"] = c.shift(-h) / c - 1
        for t, r in F.iterrows():
            st = stage_of(r.LC, r.DC, r.LT, r.DT, r.LQ, r.DQ)
            rows.append({"标的": name, "类别": u["cls"], "组": u["group"], "月底": t, "条件分": r.LC, "条件方向": r.DC,
                         "时机分": r.LT, "时机方向": r.DT, "取舍分": r.LQ, "取舍方向": r.DQ, "阶段": st,
                         "三样判断": call_of(st, r.DC),
                         "只看价格": (1 if r.close > r.ma10 else -1) if r.ma10 == r.ma10 and r.close == r.close else np.nan,
                         "事后阶段": lab.get(t), "收盘": r.close,
                         "之后3个月": r["之后3个月"], "之后6个月": r["之后6个月"], "之后12个月": r["之后12个月"]})
    CEN = pd.DataFrame(rows)
    CEN.to_csv(OUT / "census.csv", index=False, encoding="utf-8-sig", float_format="%.4f")
    say(f"整段算完 {time.time() - t0:.0f} 秒；有阶段的月份 {CEN['阶段'].notna().sum()}")

    # 2) 随机抽题
    rng = np.random.RandomState(SEED)
    elig = CEN[CEN["阶段"].notna() & CEN["之后6个月"].notna() & (CEN["月底"] >= "2012-01-01") & (CEN["月底"] <= "2026-04-30")]
    samples = []
    for cls, n in N_SAMPLE.items():
        pool = elig[elig["类别"] == cls].index.values
        pick = rng.choice(pool, size=min(n, len(pool)), replace=False)
        samples += list(pick)
    S = CEN.loc[samples].copy().reset_index(drop=True)
    # 每一道题：切数据，从头算
    mism = 0
    judged = []
    for i, r in S.iterrows():
        st, fr = judge(U[r["标的"]], r["月底"])
        if st != r["阶段"]:
            mism += 1
        judged.append((st, fr.LC, fr.DC, fr.LT, fr.DT, fr.LQ, fr.DQ))
    S["盲测阶段"] = [j[0] for j in judged]
    S["盲测三样判断"] = [call_of(j[0], j[2]) for j in judged]
    say(f"随机抽题 {len(S)} 道，切数据从头算和整段算不一致的 {mism} 道（应为0）  用时 {time.time() - t0:.0f} 秒")
    S["用到的数据截止"] = S["月底"]
    S["三样对了"] = np.where(S["之后6个月"] == 0, False, np.sign(S["之后6个月"]) == S["盲测三样判断"])
    S["只看价格对了"] = np.where(S["之后6个月"] == 0, False, np.sign(S["之后6个月"]) == S["只看价格"])
    S["和事后差几段"] = [ring_dist(a, b) if (a in STAGES and isinstance(b, str)) else np.nan
                    for a, b in zip(S["盲测阶段"], S["事后阶段"])]
    S.to_csv(OUT / "samples.csv", index=False, encoding="utf-8-sig", float_format="%.4f")

    # 3) 检验
    from scipy.stats import binomtest
    results = {}
    for cls in N_SAMPLE:
        say(f"\n==================== {cls} ====================")
        s = S[S["类别"] == cls]
        cen = CEN[(CEN["类别"] == cls) & CEN["阶段"].notna()]
        names = s["标的"].unique()
        acc = s["三样对了"].mean()
        # 瞎猜：每个标的的判断整段错开随机挪
        inst_list = list(cen["标的"].unique())
        arr = {n: cen[cen["标的"] == n]["三样判断"].values for n in inst_list}
        posmap = {n: {t: i for i, t in enumerate(cen[cen["标的"] == n]["月底"])} for n in inst_list}
        ki = np.array([inst_list.index(n) for n in s["标的"]])
        kp = np.array([posmap[n][t] for n, t in zip(s["标的"], s["月底"])])
        fwd = s["之后6个月"].values
        lens = np.array([len(arr[n]) for n in inst_list])
        null = []
        for _ in range(REPS):
            off = np.array([rng.randint(24, L - 24) if L > 60 else rng.randint(1, L) for L in lens])
            cc = np.array([arr[inst_list[i]][(p - off[i]) % lens[i]] for i, p in zip(ki, kp)])
            null.append(np.mean(np.where(fwd == 0, False, np.sign(fwd) == cc)))
        null = np.array(null)
        p1 = (1 + (null >= acc).sum()) / (1 + REPS)
        base_up = (s["之后6个月"] > 0).mean()
        say(f"题数 {len(s)}，标的 {len(names)} 个；之后6个月涨的题占 {base_up:.0%}；判断为上半圈的题占 {(s['盲测三样判断'] > 0).mean():.0%}")
        say(f"标准1  分上下半圈：三样判断对了 {acc:.1%}；瞎猜（整段错开）平均 {null.mean():.1%}，95%分位 {np.percentile(null, 95):.1%}；"
            f"p = {p1:.4f} → {'过' if p1 < 0.05 else '没过'}")
        pacc = s["只看价格对了"].mean()
        b = int((s["三样对了"] & ~s["只看价格对了"]).sum())
        cnt = int((~s["三样对了"] & s["只看价格对了"]).sum())
        p2 = binomtest(b, b + cnt, 0.5, alternative="greater").pvalue if b + cnt else 1.0
        say(f"标准2  三样 {acc:.1%} vs 只看价格 {pacc:.1%}；三样对价格错 {b} 道，三样错价格对 {cnt} 道；p = {p2:.4f} → "
            f"{'过' if (acc > pacc and p2 < 0.05) else '没过'}")
        # 顺序：观不清的比例
        dirs = {n: cen[cen["标的"] == n][["条件方向", "时机方向", "取舍方向"]].values for n in cen["标的"].unique()}
        allv = np.vstack(list(dirs.values()))
        obs_unc = np.mean(((allv[:, 0] > 0) & (allv[:, 1] < 0) & (allv[:, 2] > 0)) | ((allv[:, 0] < 0) & (allv[:, 1] > 0) & (allv[:, 2] < 0)))
        null3 = []
        for _ in range(REPS):
            tot = []
            for n, a in dirs.items():
                L = len(a)
                if L < 50:
                    tot.append(a)
                    continue
                b2 = a.copy()
                for j in (1, 2):
                    b2[:, j] = np.roll(a[:, j], rng.randint(24, L - 24))
                tot.append(b2)
            v = np.vstack(tot)
            null3.append(np.mean(((v[:, 0] > 0) & (v[:, 1] < 0) & (v[:, 2] > 0)) | ((v[:, 0] < 0) & (v[:, 1] > 0) & (v[:, 2] < 0))))
        null3 = np.array(null3)
        p3 = (1 + (null3 <= obs_unc).sum()) / (1 + REPS)
        say(f"标准3  观不清占 {obs_unc:.1%}（整段每个月）；三股力各转各的时平均 {null3.mean():.1%}，5%分位 {np.percentile(null3, 5):.1%}；"
            f"p = {p3:.4f} → {'过' if p3 < 0.05 else '没过'}")
        # 冬天开头 vs 夏天开头
        g1 = s[s["盲测阶段"].isin(["绝望", "怀疑"])]["之后6个月"].values
        g2 = s[s["盲测阶段"].isin(["兑现", "幻想"])]["之后6个月"].values
        if len(g1) and len(g2):
            obs4 = g1.mean() - g2.mean()
            allg = np.r_[g1, g2]
            null4 = []
            for _ in range(REPS):
                perm = rng.permutation(allg)
                null4.append(perm[:len(g1)].mean() - perm[len(g1):].mean())
            p4 = (1 + (np.array(null4) >= obs4).sum()) / (1 + REPS)
        else:
            obs4, p4 = np.nan, 1.0
        say(f"标准4  绝望、怀疑之后6个月平均 {g1.mean() if len(g1) else np.nan:+.1%}（{len(g1)}道）vs 兑现、幻想 "
            f"{g2.mean() if len(g2) else np.nan:+.1%}（{len(g2)}道）；p = {p4:.4f} → {'过' if p4 < 0.05 else '没过'}")
        results[cls] = {"标准1": p1 < 0.05, "标准2": acc > pacc and p2 < 0.05, "标准3": p3 < 0.05, "标准4": p4 < 0.05,
                        "三样对的比例": acc, "瞎猜": null.mean(), "只看价格": pacc, "观不清": obs_unc, "观不清瞎猜": null3.mean()}
        # 每个阶段
        tab = s.groupby("盲测阶段").agg(题数=("标的", "size"), 之后3个月=("之后3个月", "mean"), 之后6个月=("之后6个月", "mean"),
                                    之后12个月=("之后12个月", "mean"), 之后6个月涨的比例=("之后6个月", lambda x: (x > 0).mean()))
        tab = tab.reindex([x for x in STAGES + [UNCLEAR] if x in tab.index])
        say("\n每个阶段（随机抽的题）：")
        say(tab.round(3).to_string())
        for h in (3, 12):
            x = s.dropna(subset=[f"之后{h}个月"])
            a = np.mean(np.where(x[f"之后{h}个月"] == 0, False, np.sign(x[f"之后{h}个月"]) == x["盲测三样判断"]))
            pa = np.mean(np.where(x[f"之后{h}个月"] == 0, False, np.sign(x[f"之后{h}个月"]) == x["只看价格"]))
            say(f"（参考）看之后{h}个月：三样对 {a:.1%}，只看价格对 {pa:.1%}（{len(x)}道）")
        # 事后回头观
        x = s.dropna(subset=["和事后差几段"])
        if len(x):
            stser = {n: cen[cen["标的"] == n].set_index("月底")["阶段"] for n in cen["标的"].unique()}
            hk = [(r["标的"], r["月底"], r["事后阶段"]) for _, r in x.iterrows()]
            nd = []
            for _ in range(500):
                sh = {n: pd.Series(np.roll(ser.values, rng.randint(1, len(ser))), index=ser.index) for n, ser in stser.items()}
                dd = [ring_dist(sh[n][t], hs) for n, t, hs in hk if sh[n][t] in STAGES]
                nd.append(np.mean(dd))
            half = np.mean([(STAGES.index(a) < 6) == (STAGES.index(b) < 6) for a, b in zip(x["盲测阶段"], x["事后阶段"])])
            say(f"（参考）和事后回头观比：{len(x)}道，平均差 {x['和事后差几段'].mean():.2f} 段（瞎猜 {np.mean(nd):.2f}，"
                f"p = {(1 + (np.array(nd) <= x['和事后差几段'].mean()).sum()) / 501:.3f}）；上下半圈一致 {half:.0%}；"
                f"差0段 {(x['和事后差几段'] == 0).mean():.0%}，差1段以内 {(x['和事后差几段'] <= 1).mean():.0%}")
        if cls != "A股大盘":
            say("\n按组：")
            for gname, gx in s.groupby("组"):
                say(f"  {gname}：{len(gx)}道，三样对 {gx['三样对了'].mean():.0%}，只看价格对 {gx['只看价格对了'].mean():.0%}，"
                    f"之后6个月涨的题占 {(gx['之后6个月'] > 0).mean():.0%}")

    # 4) 照火候表做买卖（整段，每个月）
    say("\n==================== 照火候表做买卖（2012年起，月底判断，下月第一天开盘执行） ====================")
    trade_rows, port = [], {}
    for name, u in U.items():
        d = u["daily"]
        first_open = d.groupby(d.index + pd.offsets.MonthEnd(0))["open"].first().reindex(MONTHS)
        cen = CEN[CEN["标的"] == name].set_index("月底")
        cen = cen[cen.index >= "2011-12-31"]
        valid = cen["阶段"].notna()
        if valid.sum() < 24:
            continue
        cen = cen.loc[cen.index[valid.values.argmax()]:]
        pos = np.array([POS.get(st, (1 / 3 if dc > 0 else 0)) if isinstance(st, str) else 0
                        for st, dc in zip(cen["阶段"], cen["条件方向"])], dtype=float)
        ma = (cen["只看价格"] > 0).astype(float).values
        o1 = first_open.shift(-1).reindex(cen.index).values
        o2 = first_open.shift(-2).reindex(cen.index).values
        ret = np.nan_to_num(o2 / o1 - 1)
        prev = np.r_[0, pos[:-1]]
        prevm = np.r_[0, ma[:-1]]
        r_t = pos * ret - COST * np.abs(pos - prev)
        r_m = ma * ret - COST * np.abs(ma - prevm)
        idx = cen.index + pd.offsets.MonthEnd(1)
        port.setdefault(u["cls"], {}).setdefault("三样火候", {})[name] = pd.Series(r_t, index=idx)
        port[u["cls"]].setdefault("10个月均线", {})[name] = pd.Series(r_m, index=idx)
        port[u["cls"]].setdefault("一直拿着", {})[name] = pd.Series(ret, index=idx)
        for t, st, p, r1 in zip(cen.index, cen["阶段"], pos, r_t):
            trade_rows.append({"标的": name, "类别": u["cls"], "月底判断": t.date(), "阶段": st, "下个月仓位": p, "下个月盈亏": r1})
    pd.DataFrame(trade_rows).to_csv(OUT / "trading_monthly.csv", index=False, encoding="utf-8-sig", float_format="%.4f")

    def mstats(r):
        r = r.dropna()
        r = r[r.index <= "2026-10-31"]
        nav = (1 + r).cumprod()
        yrs = len(r) / 12
        cagr = nav.iloc[-1] ** (1 / yrs) - 1
        mdd = (nav / nav.cummax() - 1).min()
        return cagr, mdd, cagr / abs(mdd) if mdd < 0 else np.nan

    for cls, d in port.items():
        say(f"\n{cls}（等权组合）：")
        for m, per in d.items():
            P = pd.DataFrame(per).mean(axis=1)
            a, b, c = mstats(P)
            per_c = [mstats(x)[2] for x in per.values()]
            say(f"  {m:8s} 年化 {a:6.1%}  最大回撤 {b:6.1%}  年化÷回撤 {c:5.2f}   单个标的比值中位数 {np.nanmedian(per_c):.2f}")
        win = sum(mstats(d["三样火候"][n])[2] > mstats(d["10个月均线"][n])[2] for n in d["三样火候"])
        say(f"  三样火候比10个月均线好的标的 {win}/{len(d['三样火候'])}")
    pd.to_pickle({"results": results}, OUT / "results.pkl")
    say("\n=== 汇总 ===")
    say(pd.DataFrame(results).T[["标准1", "标准2", "标准3", "标准4", "三样对的比例", "瞎猜", "只看价格", "观不清", "观不清瞎猜"]].to_string())
    say(f"\n全部完成，用时 {time.time() - t0:.0f} 秒")


if __name__ == "__main__":
    main()
