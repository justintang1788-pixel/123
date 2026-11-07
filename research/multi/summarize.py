"""汇总：信号方向、合并检验、参数稳健性、周期性和效果的关系。"""
import numpy as np
import pandas as pd

import theory_bt as T

pd.set_option("display.width", 250)
rng = np.random.default_rng(11)
codes = list(T.META["代码"])

# 1) 信号：每个标的方向对不对 + 合并所有事件的检验
ss = pd.read_csv(T.OUT / "signals.csv")
ss = ss[ss["次数"] > 0].copy()
ss["超出平常"] = ss["之后26周"] - ss["平常26周"]
ss["方向对"] = np.where(ss["信号"].map(T.EXPECT) == "高", ss["超出平常"] > 0, ss["超出平常"] < 0)
print("=== 各信号：方向和理论一致的标的数 ===")
print(ss.groupby("信号").agg(标的数=("方向对", "size"), 方向对=("方向对", "sum"), 事件总数=("次数", "sum")).to_string())

# 合并检验：把每个事件之后26周的涨跌减去该标的的平常值，平均；随机挑同样多的周做对照
pooled = []
for sig in ["绝望", "泡沫", "兑现", "止损离场"]:
    ex, null_parts = [], []
    for c in codes:
        w = T.weekly(c); f = T.features(w); cl = w["close"]
        fwd = (cl.shift(-26) / cl - 1)
        base = fwd.dropna()
        if sig == "止损离场":
            s0 = f["ma"].first_valid_index()
            _, _, ev = T.run_theory(w.loc[s0:], f.loc[s0:], True)
            dates = [t for t, k in ev if k.startswith("止损离场")]
        else:
            hot_recent = (f["consensus"] | f["bubble"]).rolling(26, min_periods=1).max().astype(bool)
            mask = {"绝望": f["despair"], "泡沫": f["bubble"], "兑现": f["cashout_raw"] & hot_recent}[sig]
            dates = T.first_in(mask)
        d = fwd.reindex(dates).dropna()
        if len(d):
            ex += list(d.values - base.mean())
            null_parts.append((base.values - base.mean(), len(d)))
    obs = np.mean(ex)
    sims = []
    for _ in range(5000):
        sims.append(np.mean(np.concatenate([rng.choice(v, k) for v, k in null_parts])))
    sims = np.array(sims)
    p = (sims >= obs).mean() if T.EXPECT[sig] == "高" else (sims <= obs).mean()
    pooled.append({"信号": sig, "事件数": len(ex), "之后26周比平常多涨": obs, "理论预测": T.EXPECT[sig], "单边p": p})
pooled = pd.DataFrame(pooled)
print("\n=== 合并所有标的的事件 ===")
print(pooled.round(3).to_string(index=False))
pooled.to_csv(T.OUT / "signals_pooled.csv", index=False, encoding="utf-8-sig")

# 2) 参数稳健性：27 组参数，改进版/论文版比简单跟势好的标的数
grid = []
for cold in [0.25, 0.30, 0.40]:
    for ma in [30, 40, 52]:
        for vm in [1.3, 1.5, 2.0]:
            row = {"cold": cold, "ma": ma, "vmul": vm}
            for c in codes:
                res, _ = T.backtest_one(c, cold, ma, vm)
                for k in ["一直拿着", "简单跟势", "冬至·论文版", "冬至·改进版"]:
                    row[(c, k)] = res[k]["年化÷回撤"]
            grid.append(row)
G = pd.DataFrame(grid)
print("\n=== 27 组参数下，比简单跟势“年化÷回撤”更好的标的个数（共10个） ===")
for k in ["冬至·论文版", "冬至·改进版"]:
    wins = [sum(r[(c, k)] > r[(c, "简单跟势")] for c in codes) for _, r in G.iterrows()]
    print(k, "中位数", np.median(wins), "范围", min(wins), "–", max(wins))
print("\n=== 每个标的：27 组参数里，改进版比简单跟势好的比例；比一直拿着好的比例 ===")
per = []
for c in codes:
    per.append({"名称": T.NAME[c], "类别": T.KIND[c],
                "改进版胜跟势": np.mean([r[(c, "冬至·改进版")] > r[(c, "简单跟势")] for _, r in G.iterrows()]),
                "论文版胜跟势": np.mean([r[(c, "冬至·论文版")] > r[(c, "简单跟势")] for _, r in G.iterrows()]),
                "改进版胜拿着": np.mean([r[(c, "冬至·改进版")] > r[(c, "一直拿着")] for _, r in G.iterrows()])})
per = pd.DataFrame(per)
print(per.round(2).to_string(index=False))
per.to_csv(T.OUT / "robustness_per_instrument.csv", index=False, encoding="utf-8-sig")

# 3) 周期性和效果
cyc = pd.read_csv(T.OUT / "cyclicality.csv")
m = cyc.merge(per, on=["名称", "类别"])
print("\n=== 周期性 vs 改进版胜跟势的比例 ===")
print(m[["名称", "方差比_1年", "方差比_2年", "每十年摆动次数", "改进版胜跟势", "论文版胜跟势"]].sort_values("方差比_2年").round(2).to_string(index=False))
print("相关（方差比_2年 vs 改进版胜跟势）:", round(m[["方差比_2年", "改进版胜跟势"]].corr().iloc[0, 1], 2))
print("相关（方差比_2年 vs 论文版胜跟势）:", round(m[["方差比_2年", "论文版胜跟势"]].corr().iloc[0, 1], 2))
