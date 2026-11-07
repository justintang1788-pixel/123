"""第0步：判断一个标的是周期型还是趋势型。

用法：python3 classify_type.py sz000858 JD0 sh600519
  股票、指数用 sh/sz 开头的代码（股票自动后复权），期货用新浪主力连续代码（如 LH0、RB0）。

看两样：
  1. 两年方差比：<0.8 周期型；0.8–1.2 说不准（按趋势型对待，不要只靠“等冷”）；>1.2 趋势型。
     （0.8 这条线是看了34个标的以后定的，属于事后经验，还要再验证。）
  2. 创新高年份占比：过去每一年里，有几成的年份创过历史新高。高说明一路向上，低说明在一个大区间里来回。
数据少于8年的，结论不可靠。
"""
import sys

import numpy as np
import pandas as pd

from fetch_multi import tx_daily


def load(code):
    if code[:2] in ("sh", "sz"):
        is_index = code.startswith(("sh000", "sz399"))
        d = tx_daily(code, "" if is_index else "hfq")
    else:
        import akshare as ak
        d = ak.futures_zh_daily_sina(symbol=code)[["date", "close"]]
    d["date"] = pd.to_datetime(d["date"])
    return d.set_index("date")["close"].astype(float).resample("W-FRI").last().dropna()


def judge(p):
    r = np.log(p).diff().dropna()
    vr = np.log(p).diff(104).dropna().var() / (104 * r.var())
    ath = p.cummax()
    years = sorted(set(p.index.year))[1:]
    yearly_max = p.groupby(p.index.year).max()
    nh = np.mean([yearly_max[y] > ath[p.index.year < y].max() for y in years]) if years else np.nan
    yrs = (p.index[-1] - p.index[0]).days / 365.25
    if vr < 0.8:
        t = "周期型：可以用论文版（等冷再进、热了分批卖）"
    elif vr <= 1.2:
        t = "说不准：按趋势型对待，进场要加“价格自己证明”"
    else:
        t = "趋势型：不要只等冷，用“价格自己证明”进场，主要靠止损控制回撤"
    if yrs < 8:
        t += "（数据不到8年，仅供参考）"
    return vr, nh, yrs, t


if __name__ == "__main__":
    for code in sys.argv[1:] or ["sz000858", "JD0"]:
        vr, nh, yrs, t = judge(load(code))
        print(f"{code}: 两年方差比 {vr:.2f}，创新高年份占比 {nh:.0%}，数据 {yrs:.1f} 年 → {t}")
