"""笔记六：第二批标的验证“第0步”。规则、参数全部照搬 theory_bt.py，不做调整。"""
from math import comb
from pathlib import Path

import numpy as np
import pandas as pd

import theory_bt as T

ROOT = Path(__file__).resolve().parent.parent
T.DATA = ROOT / "data" / "multi2"
T.OUT = ROOT / "output" / "multi2"
T.OUT.mkdir(parents=True, exist_ok=True)
T.META = pd.read_csv(T.DATA / "_meta.csv")
T.NAME = dict(zip(T.META["代码"], T.META["名称"]))
T.KIND = dict(zip(T.META["代码"], T.META["类别"]))
codes = list(T.META["代码"])
rng = np.random.default_rng(20261107)
pd.set_option("display.width", 250)


def week_returns(w, target):
    o, c = w["open"], w["close"]
    pw, pw2 = target.shift(1).fillna(0), target.shift(2).fillna(0)
    return (pw2 * (o / c.shift(1) - 1) + pw * (c / o - 1) - T.COST * (pw - pw2).abs()).fillna(0)


def calmar(r):
    nav = (1 + r).cumprod()
    yrs = (r.index[-1] - r.index[0]).days / 365.25
    cagr = nav.iloc[-1] ** (1 / yrs) - 1
    mdd = (nav / nav.cummax() - 1).min()
    return cagr / abs(mdd) if mdd < 0 else np.nan


def strategies(w, f):
    return {"简单跟势": T.run_ma(w, f), "冬至·论文版": T.run_theory(w, f, False)[0],
            "冬至·改进版": T.run_theory(w, f, True)[0]}


rows = []
for c in codes:
    w = T.weekly(c)
    cyc = T.cyclicality(c)
    # 全样本默认参数
    f = T.features(w)
    s0 = f["ma"].first_valid_index()
    w2, f2 = w.loc[s0:], f.loc[s0:]
    st = strategies(w2, f2)
    full = {k: calmar(week_returns(w2, v)) for k, v in st.items()}
    # 27 组参数：赢过简单跟势的比例
    wins = {"论文版": [], "改进版": []}
    for cold in [0.25, 0.30, 0.40]:
        for ma in [30, 40, 52]:
            for vm in [1.3, 1.5, 2.0]:
                res, _ = T.backtest_one(c, cold, ma, vm)
                wins["论文版"].append(res["冬至·论文版"]["年化÷回撤"] > res["简单跟势"]["年化÷回撤"])
                wins["改进版"].append(res["冬至·改进版"]["年化÷回撤"] > res["简单跟势"]["年化÷回撤"])
    # 前一半定类型，后一半看结果
    mid = w.index[len(w) // 2]
    vr_first = T.variance_ratio(w["close"].loc[:mid], 104)
    second = {k: calmar(week_returns(w2, v).loc[mid:]) for k, v in st.items()}
    rows.append({"代码": c, "名称": T.NAME[c], "类别": T.KIND[c], "年数": cyc["年数"],
                 "方差比_2年": cyc["方差比_2年"], "前一半方差比_2年": vr_first, "分界": mid.date(),
                 "论文版胜跟势比例": np.mean(wins["论文版"]), "改进版胜跟势比例": np.mean(wins["改进版"]),
                 **{f"全_{k}": v for k, v in full.items()}, **{f"后半_{k}": v for k, v in second.items()}})
    print(c, T.NAME[c], "done", flush=True)

R = pd.DataFrame(rows)
R.to_csv(T.OUT / "batch2_results.csv", index=False, encoding="utf-8-sig")
print(R[["名称", "类别", "方差比_2年", "前一半方差比_2年", "论文版胜跟势比例", "改进版胜跟势比例",
         "全_简单跟势", "全_冬至·论文版", "全_冬至·改进版"]].round(2).to_string(index=False))


def perm_corr(x, y, sign, n=20000):
    obs = np.corrcoef(x, y)[0, 1]
    null = np.array([np.corrcoef(rng.permutation(x), y)[0, 1] for _ in range(n)])
    p = (null >= obs).mean() if sign > 0 else (null <= obs).mean()
    return obs, p


print("\n===== 检验一 =====")
r1, p1 = perm_corr(R["方差比_2年"].values, R["改进版胜跟势比例"].values, +1)
r2, p2 = perm_corr(R["方差比_2年"].values, R["论文版胜跟势比例"].values, -1)
print(f"1. 方差比 vs 改进版胜跟势：相关 {r1:+.2f}，单边p={p1:.4f}（要求正相关、p<0.05）")
print(f"   方差比 vs 论文版胜跟势：相关 {r2:+.2f}，单边p={p2:.4f}（要求负相关、p<0.05）")
R["该用"] = np.where(R["方差比_2年"] < 1, "冬至·论文版", "冬至·改进版")
R["挑对"] = [r[f"全_{r['该用']}"] > r[f"全_{'冬至·改进版' if r['该用'] == '冬至·论文版' else '冬至·论文版'}"] for _, r in R.iterrows()]
k, n = int(R["挑对"].sum()), len(R)
pb = sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n
print(f"2. 按类型挑版本，挑对 {k}/{n}，二项检验单边p={pb:.4f}（要求过半且p<0.05）")
print(R[["名称", "方差比_2年", "该用", "全_冬至·论文版", "全_冬至·改进版", "挑对"]].round(2).to_string(index=False))

print("\n===== 检验二（前一半定类型，只看后一半） =====")
R["后半该用"] = np.where(R["前一半方差比_2年"] < 1, "冬至·论文版", "冬至·改进版")
R["后半_按类型"] = [r[f"后半_{r['后半该用']}"] for _, r in R.iterrows()]
beat = int((R["后半_按类型"] > R["后半_简单跟势"]).sum())
print(f"3. 按类型选版本，后一半“年化÷回撤”比简单跟势好：{beat}/{n}")
means = {k: R[k].mean() for k in ["后半_按类型", "后半_冬至·论文版", "后半_冬至·改进版", "后半_简单跟势"]}
meds = {k: R[k].median() for k in means}
print("   平均：", {k: round(v, 3) for k, v in means.items()})
print("   中位数：", {k: round(v, 3) for k, v in meds.items()})
print(R[["名称", "前一半方差比_2年", "后半该用", "后半_简单跟势", "后半_冬至·论文版", "后半_冬至·改进版", "后半_按类型"]].round(2).to_string(index=False))
same = (np.sign(R["前一半方差比_2年"] - 1) == np.sign(R["方差比_2年"] - 1)).mean()
print(f"前一半和全样本分出的类型一致的比例：{same:.0%}")
R.to_csv(T.OUT / "batch2_results.csv", index=False, encoding="utf-8-sig")
