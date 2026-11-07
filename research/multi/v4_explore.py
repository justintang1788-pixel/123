"""笔记十一第三部分（事后补看，不算成败）：把参数固定住，27组参数各跑一遍2016–2026，看结论稳不稳。"""
from multiprocessing import Pool

import numpy as np
import pandas as pd

import v3_walkforward as V
import v4_walkforward as W

KEYS = ["第四版", "目标20%", "目标30%", "目标50%", "目标100%", "最坏5%", "最坏10%"]


def one(args):
    name, w = args
    first = w.index[w["close"].rolling(52).count().ge(52).argmax()]
    s0 = max(first, pd.Timestamp("2016-01-01"))
    out = {}
    for g in W.GRID:
        f = V.features(w, *g)
        tg = {"第四版": W.run4(f)}
        for x in W.TARGETS:
            tg[f"目标{x:.0%}"] = W.run4(f, target=x)
        for r in W.RISKS:
            tg[f"最坏{r:.0%}"] = W.run4(f, risk=r)
        tg["跟势"] = (w["close"] > w["close"].rolling(g[1], min_periods=g[1]).mean()).astype(float).values
        keep = w.index >= s0
        out[g] = {k: (pd.Series(V.returns(w, v).values, index=w.index)[keep], float(v[keep].mean())) for k, v in tg.items()}
    bh = w["close"].pct_change().fillna(0)[w.index >= s0]
    return name, out, bh


if __name__ == "__main__":
    inst, meta = W.load_all()
    with Pool(4) as p:
        res = p.map(one, list(inst.items()), chunksize=1)
    rows = []
    for g in W.GRID:
        per = {k: {} for k in KEYS + ["跟势"]}
        expo = {k: [] for k in KEYS + ["跟势"]}
        for name, out, bh in res:
            for k in per:
                per[k][name], e = out[g][k]
                expo[k].append(e)
        cal = {k: pd.Series({n: W.stats(r)["年化÷回撤"] for n, r in per[k].items()}) for k in per}
        port = {k: W.stats(pd.DataFrame(per[k]).mean(axis=1))["年化÷回撤"] for k in per}
        new = meta.index[meta["批次"] == 3]
        rows.append({"参数": W.fmt_param("第四版", g),
                     "第四版胜跟势(全部)": (cal["第四版"] > cal["跟势"]).mean(),
                     "第四版胜跟势(新标的)": (cal["第四版"] > cal["跟势"])[new].mean(),
                     **{f"组合·{k}": port[k] for k in ["跟势"] + KEYS},
                     **{f"中位数·{k}": cal[k].median() for k in KEYS},
                     **{f"平均仓位·{k}": np.mean(expo[k]) for k in ["跟势", "第四版", "目标30%", "最坏5%"]}})
    D = pd.DataFrame(rows)
    D.to_csv(W.OUT / "explore_fixed_params.csv", index=False, encoding="utf-8-sig", float_format="%.4f")
    pd.set_option("display.width", 300)
    print(D.round(3).to_string(index=False))
    print("\n27组参数里：")
    print(f"  第四版胜跟势的标的过半：全部 {(D['第四版胜跟势(全部)'] > 0.5).sum()}/27，新标的 {(D['第四版胜跟势(新标的)'] > 0.5).sum()}/27")
    print(f"  第四版组合比值高于跟势组合：{(D['组合·第四版'] > D['组合·跟势']).sum()}/27")
    for k in KEYS[1:]:
        print(f"  {k}：组合比值高于不定目标的 {(D[f'组合·{k}'] > D['组合·第四版']).sum()}/27，"
              f"中位数高于不定目标的 {(D[f'中位数·{k}'] > D['中位数·第四版']).sum()}/27")
    print("  平均仓位（27组平均）：", {k: round(D[f'平均仓位·{k}'].mean(), 3) for k in ["跟势", "第四版", "目标30%", "最坏5%"]})
