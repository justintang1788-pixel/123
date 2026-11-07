"""笔记十二的数据：宏观补充、期货持仓量、个股业绩/融资余额/股东户数。存到 research/data/tf/。"""
import json
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "tf"
for sub in ["", "margin", "fin", "holder", "fut"]:
    (OUT / sub).mkdir(parents=True, exist_ok=True)
EM = "https://datacenter-web.eastmoney.com/api/data/v1/get"

FUT = {"有色": ["CU0", "AL0", "ZN0", "PB0", "NI0", "SN0"],
       "黑色": ["RB0", "HC0", "I0", "J0", "JM0", "SF0", "SM0", "FG0", "SA0"],
       "能化": ["TA0", "MA0", "L0", "PP0", "V0", "BU0", "RU0", "EG0", "EB0", "FU0", "SC0", "UR0"]}


def em(params, tries=4):
    p = {"source": "WEB", "client": "WEB", **params}
    for i in range(tries):
        try:
            with urllib.request.urlopen(EM + "?" + urllib.parse.urlencode(p), timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 ** (i + 1))


def em_all(params, page_size=500):
    rows, page = [], 1
    while True:
        js = em({**params, "pageSize": str(page_size), "pageNumber": str(page)})
        res = js.get("result")
        if not res:
            break
        rows += res["data"]
        if page >= res["pages"]:
            break
        page += 1
    return pd.DataFrame(rows)


def macro():
    out = {}
    d = em_all({"reportName": "RPT_ECONOMY_INDUS_GROW", "columns": "REPORT_DATE,BASE_SAME", "sortColumns": "REPORT_DATE", "sortTypes": "1"})
    out["工业增加值同比"] = d.rename(columns={"BASE_SAME": "value"})
    for name, iid in [("工业用电量当月", "EMI00011561"), ("商品房销售额当月", "EMI01523157"), ("房地产开发投资累计", "EMI00120219")]:
        d = em_all({"reportName": "RPT_INDUSTRY_INDEX", "columns": "REPORT_DATE,INDICATOR_VALUE",
                    "filter": f'(INDICATOR_ID="{iid}")', "sortColumns": "REPORT_DATE", "sortTypes": "1"})
        out[name] = d.rename(columns={"INDICATOR_VALUE": "value"})
    for name, d in out.items():
        d["REPORT_DATE"] = d["REPORT_DATE"].str[:10]
        d = d.drop_duplicates("REPORT_DATE").rename(columns={"REPORT_DATE": "date"})
        d.to_csv(OUT / f"macro_{name}.csv", index=False)
        print("宏观", name, len(d), d["date"].iloc[0], d["date"].iloc[-1], flush=True)


def fut(code):
    import akshare as ak
    d = ak.futures_zh_daily_sina(symbol=code)[["date", "open", "high", "low", "close", "volume", "hold"]]
    d["date"] = d["date"].astype(str)
    d.to_csv(OUT / "fut" / f"{code}.csv", index=False)
    return code, len(d), d["date"].iloc[0]


def stock(code6):
    m = em_all({"reportName": "RPTA_WEB_RZRQ_GGMX", "columns": "DATE,RZYE", "filter": f'(SCODE="{code6}")',
                "sortColumns": "DATE", "sortTypes": "1"})
    if len(m):
        m["DATE"] = m["DATE"].str[:10]
        m.to_csv(OUT / "margin" / f"{code6}.csv", index=False)
    f = em_all({"reportName": "RPT_LICO_FN_CPD", "columns": "REPORTDATE,NOTICE_DATE,YSTZ,SJLTZ",
                "filter": f'(SECURITY_CODE="{code6}")', "sortColumns": "REPORTDATE", "sortTypes": "1"})
    if len(f):
        for c in ["REPORTDATE", "NOTICE_DATE"]:
            f[c] = f[c].str[:10]
        f.to_csv(OUT / "fin" / f"{code6}.csv", index=False)
    h = em_all({"reportName": "RPT_HOLDERNUM_DET", "columns": "END_DATE,HOLDER_NUM,HOLD_NOTICE_DATE",
                "filter": f'(SECURITY_CODE="{code6}")', "sortColumns": "END_DATE", "sortTypes": "1"})
    if len(h):
        for c in ["END_DATE", "HOLD_NOTICE_DATE"]:
            h[c] = h[c].str[:10]
        h.to_csv(OUT / "holder" / f"{code6}.csv", index=False)
    return code6, len(m), len(f), len(h)


if __name__ == "__main__":
    macro()
    with ThreadPoolExecutor(4) as ex:
        for r in ex.map(fut, [c for v in FUT.values() for c in v]):
            print("期货", *r, flush=True)
    codes = []
    for sub in ["multi", "multi2", "multi3"]:
        meta = pd.read_csv(ROOT / "data" / sub / "_meta.csv")
        codes += [c[2:] for c in meta["代码"] if c.startswith(("sh6", "sz0", "sz3")) and not c.startswith("sz399")]
    print("个股", len(codes), flush=True)
    with ThreadPoolExecutor(6) as ex:
        for r in ex.map(stock, codes):
            print("个股", *r, flush=True)
