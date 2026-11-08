"""把论文整理成纯文字，方便发 X：一份完整长文（适合 X 文章），一份按章节分篇的长帖，外加一组导读短帖。
输出到 paper/X发布/。跑法：python3 to_x.py
"""
import re
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE.parent / "X发布"
OUT.mkdir(exist_ok=True)
src = (HERE / "冬至理论_v5.src.txt").read_text(encoding="utf-8").splitlines()
MAX_PART = 7000          # 每篇长帖的字数上限（按汉字算两个字符，大约两万二，留出余量）
COPY = "本文为JustinTang洛辰《冬至理论》原创方法，转载请注明出处。"

# 图换成文字（只有讲方法的几张图需要换；其余的图正文已经讲清楚了）
FIG_TEXT = {
    "图6": ["先认锚，再定谁当家：",
           "· 锚是实物（猪、药材、铜、钢材）：条件当家。看供求在变好还是变坏。",
           "· 锚是政策和钱（A股的指数）：人和当家。看杠杆资金在加还是在减，新股增发在多发还是少发。",
           "· 锚是将来的钱（个股）：先看大圈。看大盘和行业在哪个季节，个股只看它比大圈强还是弱。"],
    "图8": ["1. 认清这个东西：靠什么兑现，谁说了算，圈靠什么转；先认锚，再定谁当家。",
           "2. 观三股力的正反面：条件、时机，和说了算的人做了什么。",
           "3. 看当家的那股力往哪边走：往上是上半圈，往下是下半圈。",
           "4. 其他两股力，定在半圈里的哪一段；回头观，前面哪一段已经走完了。",
           "5. 写下：出现什么，就说明我观错了。",
           "6. 算好最坏：认错的位置在哪，最多亏多少，能接受才做。",
           "然后才是怎么做：狠（对的时候）、拿（条件撑着）、忍（还没到时候）、断（错了就走）、趴（势不对）。"],
    "图9": ["· 条件撑着，时机也顺：狠。主仓上，拿住。",
           "· 条件撑着，时机还逆：忍。小钱先站位置，等。",
           "· 条件不撑，时机还顺：不追。热是虚的，有的减。",
           "· 条件不撑，时机也逆：趴。像乌龟一样趴着，有货的断舍离。",
           "两样冲突，以条件为准。"],
    "图10": ["仓位的火候（占你计划仓位的比例）：",
            "· 绝望：三分之一。试，小钱先站位置。",
            "· 怀疑：三分之二。加，回踩不破再加。",
            "· 犹豫：全部。狠，最该狠的一段。",
            "· 大众共识：全部，不再加。拿，认错线收紧。",
            "· 泡沫：不加新的。条件松动就先减。",
            "· 兑现：减一半以上。认错线跟紧。",
            "· 幻想、侥幸：拿着剩下的，跌破认错线就清零。忍，不补仓。",
            "· 瓦解到衰竭：零。趴着，做功课。"],
}
REPLACE = [("把这一节串起来，就是下面这张图。", "把这一节串起来，就是六步："),
           ("可以对照前面的图5，看看每一步走在曲线的什么位置。", "可以对照前面讲的十二段，看看每一步走在哪一段。")]
NUM = "一二三四五六七八九十"


def clean(t):
    t = t.replace("**", "")
    for a, b in REPLACE:
        t = t.replace(a, b)
    t = re.sub(r"^- ", "· ", t)
    t = re.sub(r"([。，；：？！”）])[ 　]+(?=[\u4e00-\u9fff“（])", r"\1", t)
    return t


def table_lines(rows, caption):
    out = [caption] if caption else []
    head, body = rows[0], rows[1:]
    for r in body:
        if len(r) == 2:
            out.append(f"· {r[0]}：{r[1]}")
        else:
            out.append(f"· {r[0]}——" + "；".join(f"{h}：{v}" for h, v in zip(head[1:], r[1:]) if v))
    return out


# ---------------------------------------------------------------- 逐行转成纯文字，按一级标题分节
sections = [["冬至理论", "一个关于市场冷热循环的十二阶段模型", "JustinTang洛辰", ""]]
mode, buf, caption = None, [], None
for raw in src:
    line = raw.rstrip()
    cur = sections[-1]
    if mode:
        if line == "@end":
            if mode == "scene":
                cur += ["【交易场景】"] + [clean(t) for t in buf] + [""]
            elif mode == "table":
                cur += table_lines([r.split("|") for r in buf], caption) + [""]
                caption = None
            else:
                cur += [clean(t) for t in buf] + [""]
            mode, buf = None, []
        elif line:
            buf.append(line)
        continue
    if not line or line == "@titlepage":
        continue
    if line in ("@box", "@scene", "@quote", "@table"):
        mode = line[1:]
    elif line.startswith("# "):
        sections.append(["■ " + line[2:], ""])
    elif line.startswith("## "):
        cur += ["（" + line[3:].split("）", 1)[0].lstrip("（") + "）" + line[3:].split("）", 1)[1], ""]
    elif line.startswith("@keywords "):
        cur += ["关键词：" + line[10:], ""]
    elif line.startswith("@fig "):
        num = line[5:].split("|")[0]
        if num in FIG_TEXT:
            cur += FIG_TEXT[num] + [""]
    elif line.startswith("@caption "):
        caption = line[9:].replace("　", " ")
    elif line.startswith("@stage "):
        num, name, sub, _ = line[7:].split("|")
        cur += [f"第{num}段　{name}：{sub}", ""]
    elif line.startswith("@people "):
        cur += ["▸ " + line[8:], ""]
    elif line.startswith("@key "):
        cur += [clean(line[5:]), ""]
    elif line.startswith("@note ") or line.startswith("@center "):
        t = line.split(" ", 1)[1]
        if "原创方法" not in t:
            cur += [t, ""]
    else:
        cur += [clean(line), ""]


def join(lines):
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n"


full = join(sum(sections, []) + ["", COPY])
pass
# X 文章有单独的标题栏，正文去掉第一行“冬至理论”
(OUT / "冬至理论_X文章正文（标题另填）.txt").write_text(full.split("\n", 1)[1].lstrip(), encoding="utf-8")


# ---------------------------------------------------------------- 分篇长帖：节太长的再按二级标题拆开，然后装箱
def weight(t):
    return sum(1 if ord(ch) < 0x1100 else 2 for ch in t)


units = []
for sec in sections:
    text = join(sec)
    if len(text) <= MAX_PART:
        units.append(text)
        continue
    head, cur = sec[0], []
    for ln in sec:
        if re.match(r"^（[一二三四五六七八九十]+）", ln) and cur and len(join(cur)) > 1500:
            units.append(join(cur)); cur = [head + "（续）", ""] if False else []
        cur.append(ln)
    units.append(join(cur))
parts, cur = [], ""
for u in units:
    if cur and len(cur) + len(u) > MAX_PART:
        parts.append(cur); cur = ""
    cur += ("\n" if cur else "") + u
parts.append(cur)
n = len(parts)
THREAD = [
    "冬里藏春，夏里藏秋。行情最差、人人想跑的时候，价格却不再往下走了；行情最火、人人想买的时候，价格却涨不动了。我把这件事整理成了一套方法，叫《冬至理论》。",
    "为什么会这样？事先变，人后觉。冬至那天太阳已经回头，最冷的三九还在后面。市场也一样：事情先变，价格给人的冷和热，慢半拍。",
    "推着行情走的是三股力：时机是天，钱、人气和趋势；条件是地，事实和供求；人性是人，说了算的那拨人的贪和怕。每股力有正反两面，就是屋里的六个人。",
    "一圈十二段。上涨六段：绝望、怀疑、犹豫、大众共识、泡沫、兑现；下跌六段：幻想、侥幸、瓦解、麻木、恐慌、衰竭。条件先转，时机跟着，人性最后走到头。",
    "判断之前，先认清这个东西：价格最后靠什么兑现？谁说了算？圈靠什么转？然后先认锚，再定谁当家。实物看条件，A股指数看杠杆和发行节奏，个股先看大圈。",
    "消息怎么看？先辨对不对，再问它想干什么。对的，归到条件里；对不上的，才去问动机。最后都看价格的反应：消息是话，反应是钱。",
    "怎么做？最坏的结果你能接受，就可以去做。没有预期，就是最好的预期。势对了，像老虎一样扑上去；势不对，像乌龟一样趴着。",
    "市场只有一个方向：不是做多，也不是做空，而是做对。以条件为准，没有偏好，才更接近真理。全文分篇发在下面。",
]
out = ["《冬至理论》X 发布稿", "",
       f"一、导读短帖（{len(THREAD)}条，可以连成一串发；每条都在140个汉字以内）", ""]
for i, t in enumerate(THREAD, 1):
    out += [f"——第{i}条（{len(t)}字）——", f"{t}（{i}/{len(THREAD)}）", ""]
out += [f"二、全文分篇长帖（共{n}篇；每篇都在{MAX_PART}字以内）", ""]
for i, p in enumerate(parts, 1):
    first = p.strip().splitlines()[0].lstrip("■ ")
    body = p.strip()
    if i == 1:
        body = body.split("\n", 1)[1].lstrip()      # 第1篇开头的“冬至理论”和篇名重复，去掉
    tail = f"\n\n（{i}/{n}）" + ("" if i == n else "未完，下一篇接着讲。") + f"\n{COPY}"
    text = f"冬至理论（{i}/{n}）\n\n" + body + tail
    out += [f"================ 第{i}篇（{len(text)}字，X 计数约{weight(text)}） ================", text, ""]
    print(f"第{i}篇：{len(text)}字，计数约{weight(text)}，开头：{first[:20]}")
(OUT / "冬至理论_X长帖分篇.txt").write_text("\n".join(out), encoding="utf-8")
print("全文", len(full), "字；导读", [len(t) for t in THREAD])
