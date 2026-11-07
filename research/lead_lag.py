"""各层和价格的领先/滞后：用“3个月平均 减 过去12个月平均”作为每个序列的周期成分，
在 -12 到 +12 个月里找和价格周期成分相关最强的那个滞后。
正的滞后 = 这一层落后于价格；负的 = 领先价格。"""
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).parent / "output"
df = pd.read_csv(OUT / "monthly.csv", index_col=0)
df.index = pd.PeriodIndex(df.index, freq="M")

raw = {
    "人气·新开户": df["new_inv"],
    "人气·换手率": df["turnover"] / df["mktcap"],
    "资金·融资余额/市值": df["margin"] / df["mktcap"],
    "谁在卖·IPO+增发/市值": (df["ipo"] + df["seo"]) / df["mktcap"],
    "太阳候选·M1-M2": df["m1_m2"],
    "太阳候选·PMI": df["pmi"],
    "利润·PPI同比": df["ppi_yoy"],
}
if "net_reduce" in df:
    raw["谁在卖·股东净减持/市值"] = df["net_reduce"] / df["mktcap"]


def cyc(s):
    return s.rolling(3, min_periods=3).mean() - s.shift(1).rolling(12, min_periods=12).mean()


pc = cyc(np.log(df["mkt_idx"]))
rows = []
for k, s in raw.items():
    c = cyc(s)
    corr = {L: c.corr(pc.shift(L)) for L in range(-12, 13)}
    L = max(corr, key=lambda x: abs(corr[x]))
    rows.append({"层": k, "同期相关": round(corr[0], 2), "最强相关": round(corr[L], 2), "在滞后(月)": L,
                 "样本": f"{c.dropna().index[0]}–{c.dropna().index[-1]}"})
t = pd.DataFrame(rows).set_index("层")
t.to_csv(OUT / "lead_lag.csv", encoding="utf-8-sig")
print(t.to_string())
