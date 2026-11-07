"""多标的日线：股票、指数走腾讯行情接口，商品期货走新浪期货接口。存到 research/data/multi/。"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "data" / "multi"
OUT.mkdir(parents=True, exist_ok=True)

# 代码: (名称, 类别, 复权方式)
TX = {
    "sh000001": ("上证指数", "情绪周期", ""),
    "sh600030": ("中信证券", "情绪周期", "hfq"),
    "sz002714": ("牧原股份", "供给周期", "hfq"),
    "sz300498": ("温氏股份", "供给周期", "hfq"),
    "sh600519": ("贵州茅台", "对照", "hfq"),
    "sh600900": ("长江电力", "对照", "hfq"),
}
SINA = {
    "LH0": ("生猪期货", "供给周期"),
    "RB0": ("螺纹钢期货", "供给周期"),
    "CU0": ("沪铜期货", "供给周期"),
    "M0": ("豆粕期货", "供给周期"),
}


def tx_daily(symbol, adjust="", start_year=1990, end_year=2026):
    url = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"
    rows = []
    for y in range(start_year, end_year + 1, 2):
        q = {"_var": f"kline_day{adjust}{y}",
             "param": f"{symbol},day,{y}-01-01,{y + 1}-12-31,640,{adjust}", "r": "0.1"}
        for i in range(4):
            try:
                with urllib.request.urlopen(url + "?" + urllib.parse.urlencode(q), timeout=20) as r:
                    txt = r.read().decode("utf-8")
                break
            except Exception:
                if i == 3:
                    raise
                time.sleep(2 ** (i + 1))
        js = json.loads(txt[txt.find("={") + 1:])["data"][symbol]
        key = next((k for k in ("hfqday", "qfqday", "day") if k in js), None)
        if key:
            rows += [r[:6] for r in js[key]]
        time.sleep(0.2)
    df = pd.DataFrame(rows, columns=["date", "open", "close", "high", "low", "volume"])
    for c in ["open", "close", "high", "low", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.drop_duplicates("date").sort_values("date").reset_index(drop=True)


if __name__ == "__main__":
    import akshare as ak
    meta = []
    for code, (name, kind, adj) in TX.items():
        df = tx_daily(code, adj)
        df.to_csv(OUT / f"{code}.csv", index=False)
        meta.append((code, name, kind, df["date"].iloc[0], df["date"].iloc[-1], len(df)))
        print(code, name, len(df), df["date"].iloc[0], df["date"].iloc[-1], flush=True)
    for code, (name, kind) in SINA.items():
        df = ak.futures_zh_daily_sina(symbol=code)[["date", "open", "close", "high", "low", "volume"]]
        df["date"] = df["date"].astype(str)
        df.to_csv(OUT / f"{code}.csv", index=False)
        meta.append((code, name, kind, df["date"].iloc[0], df["date"].iloc[-1], len(df)))
        print(code, name, len(df), df["date"].iloc[0], df["date"].iloc[-1], flush=True)
    pd.DataFrame(meta, columns=["代码", "名称", "类别", "起", "止", "天数"]).to_csv(OUT / "_meta.csv", index=False, encoding="utf-8-sig")
