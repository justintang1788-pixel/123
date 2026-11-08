"""把第五版模板展开成排版源文件：交易场景、案例、真实行情附录从第三版取用。"""
import re
from pathlib import Path

HERE = Path(__file__).parent
v3 = (HERE.parent / "v3_build" / "冬至理论_v3.src.txt").read_text(encoding="utf-8")
tpl = (HERE / "冬至理论_v5.tpl.txt").read_text(encoding="utf-8")

# 第三版各阶段的交易场景
scenes, stage = {}, None
for m in re.finditer(r"@stage [^|]+\|([^|]+)\||@scene\n(.*?)\n@end", v3, re.S):
    if m.group(1):
        stage = m.group(1)
    else:
        scenes[stage] = m.group(2)

SCENE_FIX = {
    "绝望": [("按冬至理论看，恐慌来过了，坏消息不跌，涨了没人信，像是绝望段。",
             "按冬至理论看，库存多的坏消息砸不动了，药农也在减种，条件的反面走完了，像是绝望段。")],
    "侥幸": [("按冬至理论，这就是侥幸段，是最该止损的地方。",
             "按冬至理论，这就是侥幸段，条件已经翻到了反面，是最该断的地方。")],
}

def section(title_prefix):
    i = v3.index("\n# " + title_prefix)
    j = v3.index("\n# ", i + 1)
    return v3[i + 1:j]

CASE_FIX = [
    ("我跟他说，恐慌来过了，坏消息也不跌了，这像是绝望段。他半信半疑。收货之前，我们算了一笔账：最坏是报价跌破前低，这批货认赔，亏的只是一点小钱，他亏得起；最好是赶上整个上涨，这批货能翻一番，他想要。两条都满足，他就只收了一小批，止损定在前面那个最低价。",
     "我跟他说，产地在减种，库存多的坏消息也砸不动了，条件的反面走完了，这像是绝望段。他半信半疑。收货之前，我们算了一笔账：最坏是报价跌破前低，这批货认赔，亏的只是一点小钱，他接受得了。他就收了一小批，也没定要赚多少，认错的位置定在前面那个最低价。"),
    ("这是犹豫段，最顺的一段。老周这时候主要做一件事：拿着，不折腾。止损已经提到成本上面，最坏也就是不赚不亏。",
     "这是犹豫段，最顺的一段，也是最该狠的一段。老周把该收的货都收齐了，然后就拿着，不折腾。认错的位置已经提到成本上面，最坏也就是不赚不亏。"),
    ("这是泡沫段。药材是有冬天的东西，所以老周按周期型的办法，先出了一半，剩下的看前一周的最低价，跌破就再出。他后来跟我抱怨，说出早了，少赚了不少。我说，出早了是少赚，出晚了是要命。",
     "这是泡沫段。老周盯的是条件：产地扩种的消息一条接一条，明年的货肯定多，条件开始松了。他先出了一半，剩下的看前一周的最低价，跌破就再出。他后来跟我抱怨，说出早了，少赚了不少。我说，你本来就没定要赚多少，出早了是少赚，出晚了是要命。"),
    ("两个人看的是同一个行情，差的就是有没有一套规矩。",
     "两个人看的是同一个行情，差的就是分不分得清对和错。"),
    ("还要补一句。老周做的是药材，药材有冬天，所以这套办法在他手里好用。要是他拿同样的办法，去做一只一路向上的好股票，结局就不一样了：等冷，可能一等好几年；热了就卖，可能卖在半山腰。这就是第四节说的，先看这东西有没有冬天。",
     "还要补一句。药材的圈小，冬天来得勤，所以这套办法在老周手里观得清清楚楚。要是拿同样的眼光去观一只圈很大的好股票，就得先认清它的圈：它的条件还站在正面，冬天还远，死等冬天，可能一等好几年。"),
]

out = []
for line in tpl.split("\n"):
    if line.startswith("@scene-from "):
        name = line[len("@scene-from "):].strip()
        txt = scenes[name]
        for a, b in SCENE_FIX.get(name, []):
            assert a in txt, (name, a[:20]); txt = txt.replace(a, b)
        out += ["@scene", txt, "@end"]
    elif line.strip() == "@case-from-v3":
        txt = section("七、案例推演")
        txt = txt.split("\n", 1)[1].strip("\n")   # 去掉标题
        for a, b in CASE_FIX:
            assert a in txt, a[:20]; txt = txt.replace(a, b)
        txt = txt.replace("可以对照前面的图4，", "可以对照前面的图5，")   # 价格走势图现在是图5
        out.append(txt)
    elif line.strip() == "@appendix-real-from-v3":
        txt = section("附录三　一轮真实的行情").replace("# 附录三", "# 附录二").rstrip("\n")
        txt = txt.replace("和第二版相比，这里改了一处：2015年9月到12月，原来写的是麻木，", "这里要特别说一处：2015年9月到12月，很容易被当成麻木，")
        txt += "\n\n这一轮还有一点最值得记住：2015年全国规模以上工业企业的利润其实是下降的，条件根本没撑着，涨全靠钱和人气。所以热得快，塌得也狠。条件不撑，再热也是虚的。"
        out.append(txt)
    else:
        out.append(line)
src = re.sub(r"\n{3,}", "\n\n", "\n".join(out))
(HERE / "冬至理论_v5.src.txt").write_text(src, encoding="utf-8")
left = re.findall(r"@(scene-from|case-from|appendix-real)", src)
print("ok", len(src), "未展开：", left)
