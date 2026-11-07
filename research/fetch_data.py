"""从东方财富数据中心下载冬至理论检验所需的原始数据，存到 research/data/。

只用一个接口 datacenter-web.eastmoney.com/api/data/v1/get，按报表名分页拉取。
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

BASE = "https://datacenter-web.eastmoney.com/api/data/v1/get"
DATA = Path(__file__).parent / "data"

# 报表名 -> (排序列, 保留的列, 说明)
REPORTS = {
    "margin_daily": ("RPTA_RZRQ_LSHJ", "DIM_DATE",
                     "DIM_DATE,NEW,LTSZ,RZYE,RZYEZB,RZMRE,RZJME,RZRQYE",
                     "日频：沪深300收盘(NEW)、流通市值、融资余额"),
    "market_monthly": ("RPT_ECONOMY_STOCK_STATISTICS", "REPORT_DATE", "ALL",
                       "月频：沪深两市成交额、成交量、上证最高最低"),
    "new_accounts": ("RPT_STOCK_OPEN_DATA", "STATISTICS_DATE", "ALL",
                     "月频：新增投资者数(2015-04 至 2023-08)"),
    "holder_change": ("RPT_SHARE_HOLDER_INCREASE", "NOTICE_DATE",
                      "NOTICE_DATE,END_DATE,SECURITY_CODE,DIRECTION,CHANGE_NUM_SYMBOL,TRADE_AVERAGE_PRICE,CLOSE_PRICE,MARKET",
                      "逐条：重要股东增减持"),
    "seo": ("RPT_SEO_DETAIL", "ISSUE_LISTING_DATE",
            "SECURITY_CODE,ISSUE_LISTING_DATE,TOTAL_RAISE_FUNDS,SEO_TYPE,ISSUE_WAY",
            "逐条：增发"),
    "ipo": ("RPTA_APP_IPOAPPLY", "LISTING_DATE",
            "SECURITY_CODE,LISTING_DATE,ISSUE_PRICE,ISSUE_NUM,TOTAL_RAISE_FUNDS",
            "逐条：新股上市"),
    "ppi": ("RPT_ECONOMY_PPI", "REPORT_DATE", "ALL", "月频：PPI"),
    "money_supply": ("RPT_ECONOMY_CURRENCY_SUPPLY", "REPORT_DATE", "ALL", "月频：M0/M1/M2"),
    "pmi": ("RPT_ECONOMY_PMI", "REPORT_DATE", "ALL", "月频：PMI"),
    "rmb_loan": ("RPT_ECONOMY_RMB_LOAN", "REPORT_DATE", "ALL", "月频：新增人民币贷款"),
}


def get(params, retries=4):
    url = BASE + "?" + urllib.parse.urlencode(params)
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # 网络抖动就退避重试
            if i == retries - 1:
                raise
            time.sleep(2 ** (i + 1))


def fetch_parallel(report, sort_col, columns, page_size=500, workers=6):
    """大表用多线程按页拉，失败的页单独重试。"""
    from concurrent.futures import ThreadPoolExecutor
    params = lambda pg: {"reportName": report, "columns": columns, "pageSize": page_size,
                         "pageNumber": pg, "sortColumns": sort_col, "sortTypes": 1,
                         "source": "WEB", "client": "WEB"}
    first = get(params(1))["result"]
    pages = first["pages"]
    out = {1: first["data"]}

    def one(pg):
        return pg, get(params(pg), retries=6)["result"]["data"]

    with ThreadPoolExecutor(workers) as ex:
        for i, (pg, data) in enumerate(ex.map(one, range(2, pages + 1)), 1):
            out[pg] = data
            if i % 25 == 0:
                print(f"  {report} 已拉 {i + 1}/{pages} 页", flush=True)
    rows = [r for pg in sorted(out) for r in out[pg]]
    return pd.DataFrame(rows)


def fetch(report, sort_col, columns, page_size=500):
    rows, page = [], 1
    while True:
        if page % 25 == 0:
            print(f"  {report} 第 {page} 页", flush=True)
        js = get({"reportName": report, "columns": columns, "pageSize": page_size,
                  "pageNumber": page, "sortColumns": sort_col, "sortTypes": 1,
                  "source": "WEB", "client": "WEB"})
        if not js.get("success"):
            raise RuntimeError(f"{report}: {js.get('message')}")
        res = js["result"]
        rows += res["data"]
        if page >= res["pages"]:
            break
        page += 1
        time.sleep(0.3)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    names = sys.argv[1:] or list(REPORTS)
    for name in names:
        report, sort_col, cols, note = REPORTS[name]
        df = (fetch_parallel if name == "holder_change" else fetch)(report, sort_col, cols)
        out = DATA / f"{name}.csv"
        df.to_csv(out, index=False, encoding="utf-8-sig")
        print(f"{name:15s} {len(df):7d} 行  {note}")
