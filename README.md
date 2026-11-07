# 冬至理论研究

用十二个阶段看清行情走到了哪里。作者：justintang。

## 目录

- `paper/冬至理论.md`：论文第一版（2026-10-16）
- `paper/冬至理论_v2.docx`、`paper/冬至理论_v2.md`：论文第二版（2026年10月），图在 `paper/images_v2/`
- `paper/冬至理论_v3.docx`、`paper/冬至理论_v3.md`：**论文第三版（2026年11月）**，按检验结果修订；图在 `paper/images_v3/`，排版源文件和脚本在 `paper/v3_build/`
- `paper/冬至理论_v4.docx`、`paper/冬至理论_v4.pdf`、`paper/冬至理论_v4.md`：**论文第四版（2026年11月）**，以条件为准，时机、条件、人性的正反面；附录三是按第四版规矩重跑的回测；源文件在 `paper/v4_build/`
- `notes/`：研究笔记
  - `01-股票市场的六层顺序.md`：用 2010–2026 年 A 股数据检验图2的六层顺序
  - `02-六样东西怎么量化（草案）.md`：六样东西的量化选项、v0 自动标注和第一次事先检验
  - `03-读第二版：推理方式从哪里改.md`：第二版的三个发现和改进后的推理步骤
  - `04-论证：冬至理论有没有效果.md`：A股全市场上的事先登记检验（H1–H4）
  - `05-多标的回测：什么有周期，冬至理论管不管用.md`：10个标的的周期性、信号检验和回测
  - `06-换一批标的验证第0步.md`：第二批24个标的的事先登记验证
  - `07-第三版方法：盖住未来的回测.md`：第三版规矩的滚动向前检验（2016–2026）
  - `08-深究：第三版还有哪些问题.md`：拆零件检验和问题清单
  - `09-中药材回测：原报告怎么读、下一步怎么测.md`：作者的 Grok bot 中药材回测的方法评估和下一步设计
  - `10-方法论与十二消息卦.md`：十二阶段与十二消息卦的对应，条件、时机、人性的方法论
  - `11-第四版回测.md`：按第四版规矩重跑的回测（158个标的，事先登记，逐笔留底）
  - `14-先认锚，再定谁当家：第二次随机盲测.md`：用新标的检验“先认锚，再定谁当家”（硬锚看条件、软锚看取舍、个股看说了算的人）
  - `13-第零步：认清这个东西.md`：判断之前先问三件事：价格靠什么兑现、谁说了算、圈靠什么转；各类东西的三股力该看什么
  - `12-三股力判断阶段：随机盲测.md`：按理论本身的办法（先分类，再用条件、时机、取舍判断阶段），随机抽题、遮住未来检验
  - `手工标注模板_2016-2024.csv`：请作者按月手工标阶段，用来定规则和检验
- `research/`：数据和代码
  - `fetch_data.py`：从东方财富数据中心下载原始数据到 `research/data/`
  - `build_monthly.py`：整理成月度表 `research/output/monthly.csv`
  - `layer_order.py`、`lead_lag.py`：各层在顶部、底部谁先谁后
  - `johnson_test.py`、`johnson_maxnull.py`：六层是不是按固定顺序一层一层地翻
  - `classify_v0.py`：v0 自动标注，算各阶段之后的涨跌
  - `validate.py`、`validate_explore.py`、`validate_plot.py`：笔记四的检验
  - `multi/`：笔记五到八、十一的多标的数据下载、回测和作图
    - `fetch_batch3.py`、`v4_walkforward.py`、`v4_explore.py`、`v4_excel.py`、`v4_backtest_fig.py`：笔记十一（第四版回测）
  - `anchor_test.py` 等（在 `multi/` 里）、`data/anchor/`、`output/anchor/`：笔记十四的程序、数据和记录（`第二次盲测记录.xlsx`）
  - `three_force.py` 等（在 `multi/` 里）、`data/tf/`、`output/three_force/`：笔记十二的程序、数据和记录（`三股力盲测记录.xlsx`）
  - `output/v4/`：第四版回测的记录：`第四版回测记录.xlsx`（八张表）、`trades.csv`（每一笔）、`weekly_log.csv`（每一周）等

## 运行

需要 Python 3、pandas、numpy、matplotlib。

```bash
cd research
python3 fetch_data.py
python3 build_monthly.py
python3 layer_order.py
python3 lead_lag.py
python3 johnson_test.py 24
python3 classify_v0.py
```
