"""
高境界Fortune事件生成器
为 fortune.json 补充 筑基/金丹/元婴/化神 各50个专属事件 = 200新事件
"""
import json
import hashlib
from pathlib import Path

# ============================================================
# 高境界事件模板定义
# ============================================================

# 每个境界50个事件，包含 text, effects, tags
REALM_2_EVENTS = [
    # 筑基（宝物/遗迹/灵兽/突破相关）
    {"text": "你在古修士洞府中找到一枚筑基丹。", "effects": {"cultivation": 30, "constitution": 1}, "tags": ["fortune", "treasure"]},
    {"text": "一座隐秘的灵脉被你偶然发现。", "effects": {"cultivation": 35}, "tags": ["fortune", "discovery"]},
    {"text": "你在拍卖会上以极低的价格买到了一件被错认的法宝。", "effects": {"fortune": 2, "cultivation": 20}, "tags": ["fortune", "treasure"]},
    {"text": "一位游历的散修将一门罕见功法传授于你。", "effects": {"comprehension": 2, "cultivation": 25}, "tags": ["fortune", "encounter"]},
    {"text": "你在雷雨中悟到了金之真意。", "effects": {"comprehension": 3, "willpower": 1}, "tags": ["fortune", "encounter"]},
    {"text": "一株百年灵芝被你在悬崖上采到。", "effects": {"constitution": 2, "cultivation": 20}, "tags": ["fortune", "treasure"]},
    {"text": "你的法器在一次意外中完成了自主进化。", "effects": {"cultivation": 15, "fortune": 2}, "tags": ["fortune", "treasure"]},
    {"text": "一位前辈离去前将毕生收藏赠予了你。", "effects": {"cultivation": 30, "comprehension": 1}, "tags": ["fortune", "encounter"]},
    {"text": "你在秘境中发现了一处上古传送阵。", "effects": {"cultivation": 20, "comprehension": 2}, "tags": ["fortune", "secret_realm"]},
    {"text": "一只受伤的灵兽在你救治后与你结了契约。", "effects": {"constitution": 1, "fortune": 2, "add_tag": "beast_tamer"}, "tags": ["fortune", "beast"]},
    {"text": "你在溪底发现了一块蕴含灵气的异石。", "effects": {"cultivation": 25, "constitution": 1}, "tags": ["fortune", "treasure"]},
    {"text": "你偶入一处时间流速不同的空间修炼了月余。", "effects": {"cultivation": 40}, "tags": ["fortune", "secret_realm"]},
    {"text": "你破解了一道困扰数月的瓶颈。", "effects": {"cultivation": 30, "comprehension": 2}, "tags": ["fortune", "encounter"]},
    {"text": "你在一处废墟中捡到了一面残缺的铜镜法器。", "effects": {"fortune": 2, "willpower": 1}, "tags": ["fortune", "treasure"]},
    {"text": "你的丹田灵力在一次感悟中自行凝实了几分。", "effects": {"cultivation": 35, "comprehension": 1}, "tags": ["fortune", "encounter"]},
    {"text": "一阵灵风裹挟着天地精华从你体内穿过。", "effects": {"cultivation": 25, "constitution": 2}, "tags": ["fortune", "encounter"]},
    {"text": "你在枯井底部发现了一片被封印的药田。", "effects": {"cultivation": 20, "lifespan": 5}, "tags": ["fortune", "discovery"]},
    {"text": "你意外激活了体内一条沉睡的隐脉。", "effects": {"cultivation": 30, "constitution": 2}, "tags": ["fortune", "encounter"]},
    {"text": "你在山中遇到了一位采药的仙人。", "effects": {"comprehension": 3, "cultivation": 15}, "tags": ["fortune", "encounter"]},
    {"text": "一枚品质上佳的储物戒被你在旧物中发现。", "effects": {"fortune": 3}, "tags": ["fortune", "treasure"]},
    {"text": "你找到了一处适合筑基的天然灵穴。", "effects": {"cultivation": 40, "willpower": 1}, "tags": ["fortune", "discovery"]},
    {"text": "你在梦中得到了一位前辈的指点。", "effects": {"comprehension": 3, "cultivation": 15}, "tags": ["fortune", "dream"]},
    {"text": "一株千年何首乌被你从悬崖上摘下。", "effects": {"lifespan": 10, "constitution": 1}, "tags": ["fortune", "treasure"]},
    {"text": "你在一场暴雨后发现了一条被冲刷出来的灵矿脉。", "effects": {"cultivation": 25, "fortune": 1}, "tags": ["fortune", "discovery"]},
    {"text": "你的修炼中偶然触碰到了天地法则的一角。", "effects": {"comprehension": 4}, "tags": ["fortune", "encounter"]},
    {"text": "一个路过的商队遗落了一个装满灵石的包袱。", "effects": {"cultivation": 20, "fortune": 2}, "tags": ["fortune", "treasure"]},
    {"text": "你在古战场的尸骨中找到了一本残卷。", "effects": {"comprehension": 2, "cultivation": 20}, "tags": ["fortune", "treasure"]},
    {"text": "你参悟了一种新的灵力运行路径。", "effects": {"cultivation": 30, "comprehension": 2}, "tags": ["fortune", "encounter"]},
    {"text": "一只灵蝶引你找到了一处百花秘境。", "effects": {"cultivation": 20, "lifespan": 5}, "tags": ["fortune", "discovery"]},
    {"text": "你无意中将两门功法融会贯通。", "effects": {"comprehension": 3, "cultivation": 25}, "tags": ["fortune", "encounter"]},
    {"text": "你在地宫深处发现了一座未被触动的藏宝阁。", "effects": {"cultivation": 25, "fortune": 2}, "tags": ["fortune", "treasure"]},
    {"text": "一场灵气潮汐恰好在你修炼时经过此地。", "effects": {"cultivation": 40}, "tags": ["fortune", "encounter"]},
    {"text": "你在河中淘到了一块品相极好的灵玉。", "effects": {"cultivation": 20, "fortune": 1}, "tags": ["fortune", "treasure"]},
    {"text": "一位故交临终前将一件宝物托付于你。", "effects": {"willpower": 2, "fortune": 2}, "tags": ["fortune", "encounter"]},
    {"text": "你在一棵千年古树的树洞中找到了一卷秘法。", "effects": {"comprehension": 3, "cultivation": 15}, "tags": ["fortune", "treasure"]},
    {"text": "你发现了一处天然的聚灵阵眼。", "effects": {"cultivation": 35, "comprehension": 1}, "tags": ["fortune", "discovery"]},
    {"text": "你在坊市中结识了一位炼器大师，他赠你一件试验之作。", "effects": {"fortune": 2, "constitution": 1}, "tags": ["fortune", "encounter"]},
    {"text": "你在闭关时丹田中突然涌出一股热流，修为直接精进一截。", "effects": {"cultivation": 45}, "tags": ["fortune", "encounter"]},
    {"text": "你从一只死去的妖兽体内取出了一颗完整的妖丹。", "effects": {"cultivation": 30, "constitution": 1}, "tags": ["fortune", "treasure"]},
    {"text": "你无意间踏入了一处远古大能布下的悟道场。", "effects": {"comprehension": 4, "cultivation": 15}, "tags": ["fortune", "secret_realm"]},
    {"text": "你在修炼时进入了一种玄之又玄的顿悟状态。", "effects": {"comprehension": 3, "cultivation": 30}, "tags": ["fortune", "encounter"]},
    {"text": "你在一处荒废的丹房中找到了几枚保存完好的灵丹。", "effects": {"cultivation": 25, "constitution": 1}, "tags": ["fortune", "treasure"]},
    {"text": "一位散修用一本秘籍换走了你手中的寻常物件。", "effects": {"comprehension": 3, "cultivation": 20}, "tags": ["fortune", "encounter"]},
    {"text": "你在灵田中偶然培育出了一株变异灵草。", "effects": {"cultivation": 20, "fortune": 2}, "tags": ["fortune", "discovery"]},
    {"text": "你的血脉中沉睡的力量苏醒了一丝。", "effects": {"constitution": 3, "cultivation": 15}, "tags": ["fortune", "encounter"]},
    {"text": "你在一处温泉中泡了三天三夜，体内杂质尽去。", "effects": {"constitution": 2, "cultivation": 20}, "tags": ["fortune", "discovery"]},
    {"text": "一阵清风中夹带着某种功法的韵味——你凝神感悟了许久。", "effects": {"comprehension": 3, "cultivation": 20}, "tags": ["fortune", "encounter"]},
    {"text": "你在一具白骨旁的玉简中读到了一段珍贵的经验。", "effects": {"comprehension": 2, "cultivation": 25}, "tags": ["fortune", "treasure"]},
    {"text": "你的某条经脉在修炼中突然拓宽了一倍。", "effects": {"cultivation": 35, "constitution": 1}, "tags": ["fortune", "encounter"]},
    {"text": "一只凤血雀落在你肩头——它认你有缘。", "effects": {"fortune": 3, "lifespan": 5}, "tags": ["fortune", "beast"]},
]

REALM_3_EVENTS = [
    # 金丹（仙府/传承/重宝/大机缘）
    {"text": "你在仙府遗址中获得了一位金丹真人的毕生传承。", "effects": {"cultivation": 50, "comprehension": 3}, "tags": ["fortune", "secret_realm"]},
    {"text": "一件上古时期的仙器从地底破土而出，选择了你。", "effects": {"fortune": 3, "cultivation": 30}, "tags": ["fortune", "treasure"]},
    {"text": "你在雷池中淬炼金丹时意外吸收了一道天雷精华。", "effects": {"cultivation": 45, "constitution": 2}, "tags": ["fortune", "encounter"]},
    {"text": "你发现了一座完整的上古药园。", "effects": {"cultivation": 40, "lifespan": 10}, "tags": ["fortune", "discovery"]},
    {"text": "你在虚空裂缝中截取了一缕混沌之气。", "effects": {"comprehension": 4, "cultivation": 30}, "tags": ["fortune", "encounter"]},
    {"text": "一位化神期前辈的残魂为你解答了困惑多年的难题。", "effects": {"comprehension": 5, "cultivation": 20}, "tags": ["fortune", "encounter"]},
    {"text": "你在海底神殿中找到了一颗万年灵珠。", "effects": {"cultivation": 50, "constitution": 2}, "tags": ["fortune", "treasure"]},
    {"text": "天降祥瑞，你的金丹表面多了一道纹路。", "effects": {"cultivation": 60}, "tags": ["fortune", "encounter"]},
    {"text": "你在一处绝地中发现了前人留下的逃生密道——密道中还藏着宝物。", "effects": {"cultivation": 35, "fortune": 2}, "tags": ["fortune", "secret_realm"]},
    {"text": "你的本命法宝在一次战斗后自行突破了品阶。", "effects": {"fortune": 3, "cultivation": 25}, "tags": ["fortune", "treasure"]},
    {"text": "你在一座无人知晓的灵峰上闭关三月。", "effects": {"cultivation": 55, "willpower": 2}, "tags": ["fortune", "discovery"]},
    {"text": "你从天劫的余韵中悟出了一丝雷之本源。", "effects": {"comprehension": 4, "cultivation": 35}, "tags": ["fortune", "encounter"]},
    {"text": "你在古阵中意外触发了一道造化之力。", "effects": {"cultivation": 45, "constitution": 2}, "tags": ["fortune", "secret_realm"]},
    {"text": "一位上古大妖临死前将一身妖力转赠于你。", "effects": {"cultivation": 50, "constitution": 3}, "tags": ["fortune", "encounter"]},
    {"text": "你在秘境最深处发现了一朵万年冰莲。", "effects": {"cultivation": 40, "lifespan": 15}, "tags": ["fortune", "treasure"]},
    {"text": "你悟透了五行相生相克的核心奥义。", "effects": {"comprehension": 5, "cultivation": 30}, "tags": ["fortune", "encounter"]},
    {"text": "一座远古传送阵将你送到了一处灵气浓郁至极的异域。", "effects": {"cultivation": 60}, "tags": ["fortune", "secret_realm"]},
    {"text": "你的识海中突然浮现出一段不属于自己的记忆——是某位大能的修炼心得。", "effects": {"comprehension": 4, "cultivation": 35}, "tags": ["fortune", "dream"]},
    {"text": "你将一块陨铁炼入了本命法宝，品质飞跃。", "effects": {"fortune": 3, "cultivation": 20}, "tags": ["fortune", "treasure"]},
    {"text": "你在一处时间静止的空间中修炼了整整一年。", "effects": {"cultivation": 70}, "tags": ["fortune", "secret_realm"]},
    {"text": "一头太古异种在你面前孵化，第一眼便认了你为主。", "effects": {"fortune": 3, "constitution": 2, "add_tag": "beast_tamer"}, "tags": ["fortune", "beast"]},
    {"text": "你在地脉交汇处悟到了土之真意。", "effects": {"comprehension": 5, "constitution": 2}, "tags": ["fortune", "encounter"]},
    {"text": "你解开了一枚古老玉佩的封印——里面存储着庞大的灵力。", "effects": {"cultivation": 55, "fortune": 1}, "tags": ["fortune", "treasure"]},
    {"text": "你在梦中游历了一处仙境——醒来后修为竟有精进。", "effects": {"cultivation": 40, "comprehension": 3}, "tags": ["fortune", "dream"]},
    {"text": "你发现了一处蕴含先天之气的灵眼。", "effects": {"cultivation": 50, "constitution": 1}, "tags": ["fortune", "discovery"]},
    {"text": "一位隐世老者被你的诚意打动，传你一式绝学。", "effects": {"comprehension": 4, "cultivation": 30}, "tags": ["fortune", "encounter"]},
    {"text": "你的体内有一条隐脉被外力震开——灵力流转更加顺畅。", "effects": {"cultivation": 45, "constitution": 2}, "tags": ["fortune", "encounter"]},
    {"text": "你在古墓中找到了一份完整的金丹期功法。", "effects": {"comprehension": 3, "cultivation": 45}, "tags": ["fortune", "treasure"]},
    {"text": "一颗流星落在你附近——你在陨坑中发现了星辰精华。", "effects": {"cultivation": 50, "fortune": 2}, "tags": ["fortune", "discovery"]},
    {"text": "你在入定时灵魂短暂出窍，看到了天地运转的一角。", "effects": {"comprehension": 5, "willpower": 2}, "tags": ["fortune", "encounter"]},
    {"text": "你在藏经阁中翻到了一本被错误归类的珍贵典籍。", "effects": {"comprehension": 4, "cultivation": 25}, "tags": ["fortune", "treasure"]},
    {"text": "你的丹火在一次偶然中完成了质变。", "effects": {"cultivation": 40, "comprehension": 2}, "tags": ["fortune", "encounter"]},
    {"text": "你在一处被世人遗忘的战场中捡到了一面残盾——它曾属于一位金仙。", "effects": {"fortune": 3, "willpower": 2}, "tags": ["fortune", "treasure"]},
    {"text": "你的金丹在月华浸润下自行圆满了一分。", "effects": {"cultivation": 55}, "tags": ["fortune", "encounter"]},
    {"text": "一条地龙因你的善举而赠你一滴龙血。", "effects": {"constitution": 4, "cultivation": 25}, "tags": ["fortune", "beast"]},
    {"text": "你参加了一场仅限金丹期修士的论道会——获益良多。", "effects": {"comprehension": 4, "willpower": 1}, "tags": ["fortune", "encounter"]},
    {"text": "你的本命灵兽突然进化，带动你的修为也跟着精进。", "effects": {"cultivation": 45, "fortune": 2}, "tags": ["fortune", "beast"]},
    {"text": "你在一条深渊裂缝中发现了远古灵木的残根。", "effects": {"cultivation": 35, "lifespan": 10}, "tags": ["fortune", "treasure"]},
    {"text": "天地异象突现——你恰好在灵气爆发的中心点修炼。", "effects": {"cultivation": 60, "comprehension": 2}, "tags": ["fortune", "encounter"]},
    {"text": "你在一次濒死体验中突破了金丹的一层桎梏。", "effects": {"cultivation": 50, "willpower": 3}, "tags": ["fortune", "encounter"]},
    {"text": "你从一处被封印万年的冰窟中取出了一件仙器碎片。", "effects": {"fortune": 3, "cultivation": 30}, "tags": ["fortune", "treasure"]},
    {"text": "你在星空下悟道三日——日月精华沐浴其身。", "effects": {"cultivation": 45, "comprehension": 3}, "tags": ["fortune", "encounter"]},
    {"text": "一位将死的妖王以命格与你交换了一件宝物。", "effects": {"cultivation": 40, "fortune": 2}, "tags": ["fortune", "encounter"]},
    {"text": "你无意中走入了一处上古仙人的试炼场——并通过了考验。", "effects": {"comprehension": 4, "cultivation": 40}, "tags": ["fortune", "secret_realm"]},
    {"text": "你在海底火山口发现了一块凤凰涅槃后遗留的灵石。", "effects": {"constitution": 3, "cultivation": 35}, "tags": ["fortune", "treasure"]},
    {"text": "你收到了一份匿名寄来的包裹——里面是一枚极品灵丹。", "effects": {"cultivation": 50}, "tags": ["fortune", "treasure"]},
    {"text": "你在修炼间隙偶然触碰到了空间法则的边缘。", "effects": {"comprehension": 5, "cultivation": 20}, "tags": ["fortune", "encounter"]},
    {"text": "一只千年灵龟浮出水面为你挡了一劫——并赠你一片龟甲。", "effects": {"fortune": 3, "lifespan": 10}, "tags": ["fortune", "beast"]},
    {"text": "你在一块玄铁内部发现了一把上古神兵的胚体。", "effects": {"fortune": 4, "cultivation": 20}, "tags": ["fortune", "treasure"]},
    {"text": "你的紫府中突然结出了一颗灵种——这是大道给你的认可。", "effects": {"cultivation": 55, "comprehension": 3}, "tags": ["fortune", "encounter"]},
]

REALM_4_EVENTS = [
    # 元婴（大神通/天地异象/上界遗物/法则感悟）
    {"text": "你在元婴出窍时意外闯入了一处上界遗留的道场。", "effects": {"cultivation": 60, "comprehension": 5}, "tags": ["fortune", "secret_realm"]},
    {"text": "一件被封印万年的太古仙器在你手中苏醒了。", "effects": {"fortune": 4, "cultivation": 40}, "tags": ["fortune", "treasure"]},
    {"text": "你在虚空中捕获了一缕大道本源之气。", "effects": {"comprehension": 6, "cultivation": 35}, "tags": ["fortune", "encounter"]},
    {"text": "一场天地异变中你的元婴自行凝实了一倍。", "effects": {"cultivation": 70}, "tags": ["fortune", "encounter"]},
    {"text": "你发现了一座连接上界的残破传送阵。", "effects": {"comprehension": 5, "cultivation": 50}, "tags": ["fortune", "secret_realm"]},
    {"text": "你参悟了时间法则的皮毛。", "effects": {"comprehension": 7, "cultivation": 30}, "tags": ["fortune", "encounter"]},
    {"text": "一位陨落的仙人残魂选择了你作为传承者。", "effects": {"cultivation": 80, "comprehension": 4}, "tags": ["fortune", "encounter"]},
    {"text": "你在星域边缘找到了一颗蕴含星辰之力的宝珠。", "effects": {"cultivation": 60, "fortune": 3}, "tags": ["fortune", "treasure"]},
    {"text": "你的元婴在一次危机中自行蜕变——多了一只法眼。", "effects": {"comprehension": 6, "willpower": 3}, "tags": ["fortune", "encounter"]},
    {"text": "你在一座上古仙城的废墟中找到了完整的元婴期功法。", "effects": {"cultivation": 55, "comprehension": 4}, "tags": ["fortune", "treasure"]},
    {"text": "天降甘露浇灌了你的识海——灵魂力暴涨。", "effects": {"willpower": 4, "cultivation": 50}, "tags": ["fortune", "encounter"]},
    {"text": "你在混沌之海的边缘悟到了虚空之道。", "effects": {"comprehension": 6, "cultivation": 40}, "tags": ["fortune", "encounter"]},
    {"text": "一棵生长了万年的建木碎片被你所得。", "effects": {"lifespan": 20, "cultivation": 45}, "tags": ["fortune", "treasure"]},
    {"text": "你的元神在一次感悟中与天地产生了共鸣。", "effects": {"cultivation": 65, "comprehension": 4}, "tags": ["fortune", "encounter"]},
    {"text": "你在一片死域中发现了一口不灭的先天灵火。", "effects": {"cultivation": 50, "constitution": 3}, "tags": ["fortune", "discovery"]},
    {"text": "一位正在渡劫的大能失败后，劫雷余韵被你吸收。", "effects": {"cultivation": 55, "constitution": 2}, "tags": ["fortune", "encounter"]},
    {"text": "你在梦中经历了一世轮回——醒来后道心圆满了几分。", "effects": {"willpower": 5, "comprehension": 4}, "tags": ["fortune", "dream"]},
    {"text": "一条沉睡万年的龙脉在你脚下苏醒了。", "effects": {"cultivation": 70, "fortune": 2}, "tags": ["fortune", "discovery"]},
    {"text": "你在一面古镜中看到了自己证道的景象。", "effects": {"willpower": 4, "comprehension": 5}, "tags": ["fortune", "vision"]},
    {"text": "你偶然间触碰到了因果法则——看清了一段命运之线。", "effects": {"comprehension": 7, "willpower": 2}, "tags": ["fortune", "encounter"]},
    {"text": "一座浮空仙岛对你敞开了大门。", "effects": {"cultivation": 65, "lifespan": 15}, "tags": ["fortune", "secret_realm"]},
    {"text": "你在地脉深处找到了一眼先天灵泉。", "effects": {"cultivation": 55, "constitution": 3}, "tags": ["fortune", "discovery"]},
    {"text": "你的元婴忽然开口说了一句话——那不是你的意识在驱动它。", "effects": {"comprehension": 6, "willpower": 3}, "tags": ["fortune", "encounter"]},
    {"text": "你在雷渊之底捡到了一颗九天神雷的核心。", "effects": {"cultivation": 60, "constitution": 3}, "tags": ["fortune", "treasure"]},
    {"text": "你的丹田在一次顿悟中扩大了数倍。", "effects": {"cultivation": 75}, "tags": ["fortune", "encounter"]},
    {"text": "一位上界使者路过此地，随手点化了你一句。", "effects": {"comprehension": 7, "cultivation": 30}, "tags": ["fortune", "encounter"]},
    {"text": "你在太古战场的遗迹中找到了一面通天法令。", "effects": {"fortune": 4, "willpower": 3}, "tags": ["fortune", "treasure"]},
    {"text": "你的元婴自行修复了一条被损毁的先天经脉。", "effects": {"cultivation": 60, "constitution": 3}, "tags": ["fortune", "encounter"]},
    {"text": "你在一颗古星的碎片上找到了上古仙文。", "effects": {"comprehension": 6, "cultivation": 35}, "tags": ["fortune", "treasure"]},
    {"text": "天地间一道无名的力量注入了你的体内。", "effects": {"cultivation": 70, "willpower": 2}, "tags": ["fortune", "encounter"]},
    {"text": "你在轮回之井旁悟道七日——终于通透了一层执念。", "effects": {"willpower": 5, "comprehension": 5}, "tags": ["fortune", "encounter"]},
    {"text": "你意外引动了一场小型灵气潮汐——尽数被你吸收。", "effects": {"cultivation": 65}, "tags": ["fortune", "encounter"]},
    {"text": "你在深渊中找到了一尊上古神像——它的眼中闪了一下。", "effects": {"comprehension": 5, "willpower": 3}, "tags": ["fortune", "discovery"]},
    {"text": "你的元神分身在游历中意外获得了一份独立的机缘。", "effects": {"cultivation": 50, "comprehension": 4}, "tags": ["fortune", "encounter"]},
    {"text": "你在一片枯死的灵域中心发现了尚存生机的一株仙草。", "effects": {"lifespan": 20, "cultivation": 40}, "tags": ["fortune", "treasure"]},
    {"text": "你的识海中浮现了一幅完整的功法图——来源不明。", "effects": {"comprehension": 6, "cultivation": 40}, "tags": ["fortune", "dream"]},
    {"text": "你在万丈海底发现了一座保存完好的水府。", "effects": {"cultivation": 55, "fortune": 3}, "tags": ["fortune", "secret_realm"]},
    {"text": "一只太古圣兽的幼崽从蛋中孵化认了你为亲。", "effects": {"fortune": 4, "constitution": 2, "add_tag": "beast_tamer"}, "tags": ["fortune", "beast"]},
    {"text": "你在日月交替之时参悟了阴阳互济之道。", "effects": {"comprehension": 6, "cultivation": 45}, "tags": ["fortune", "encounter"]},
    {"text": "一位故人的遗物中藏着一件你从未发现的密室钥匙。", "effects": {"cultivation": 50, "fortune": 2}, "tags": ["fortune", "treasure"]},
    {"text": "你在一次走火入魔的边缘反而看清了自己的大道。", "effects": {"willpower": 5, "comprehension": 5}, "tags": ["fortune", "encounter"]},
    {"text": "天地间一道无形的屏障被你捅破了——你看见了更广阔的世界。", "effects": {"comprehension": 7, "cultivation": 30}, "tags": ["fortune", "encounter"]},
    {"text": "你在一处远古禁地中取出了被镇压的太阴精玉。", "effects": {"cultivation": 55, "constitution": 3}, "tags": ["fortune", "treasure"]},
    {"text": "你的体内忽然生出了一缕先天之气——这是悟道的征兆。", "effects": {"cultivation": 65, "comprehension": 4}, "tags": ["fortune", "encounter"]},
    {"text": "你在雪域之巅吸收了一道极光的精华。", "effects": {"cultivation": 55, "willpower": 2}, "tags": ["fortune", "encounter"]},
    {"text": "一位将逝的老怪物以大法力为你开辟了一条新路。", "effects": {"cultivation": 60, "comprehension": 5}, "tags": ["fortune", "encounter"]},
    {"text": "你在古仙的棋局中悟到了天机一角。", "effects": {"comprehension": 7, "willpower": 3}, "tags": ["fortune", "encounter"]},
    {"text": "你的本命法宝在你元婴出窍时自行完成了涅槃重生。", "effects": {"fortune": 4, "cultivation": 35}, "tags": ["fortune", "treasure"]},
    {"text": "一座隐藏在虚空夹缝中的仙人洞府向你显露了真容。", "effects": {"cultivation": 60, "fortune": 3}, "tags": ["fortune", "secret_realm"]},
    {"text": "你在入定时灵魂短暂触碰到了天道的一缕意识。", "effects": {"comprehension": 8, "willpower": 3}, "tags": ["fortune", "encounter"]},
]

REALM_5_EVENTS = [
    # 化神（天道法则/仙界残留/大道感悟/超凡入圣）
    {"text": "你在天地崩裂时窥见了造化之秘。", "effects": {"comprehension": 8, "cultivation": 50}, "tags": ["fortune", "encounter"]},
    {"text": "一座仙界碎片从天而降——你是方圆千里唯一能接住它的人。", "effects": {"cultivation": 90, "fortune": 4}, "tags": ["fortune", "treasure"]},
    {"text": "你的化神之力引发了天地共鸣——大道在你面前显化。", "effects": {"comprehension": 9, "willpower": 4}, "tags": ["fortune", "encounter"]},
    {"text": "你在时间长河中截取了一段属于自己的命运线。", "effects": {"cultivation": 80, "comprehension": 5}, "tags": ["fortune", "encounter"]},
    {"text": "一位飞升者在消失前向你投掷了一件东西——你接住了。", "effects": {"fortune": 5, "cultivation": 60}, "tags": ["fortune", "treasure"]},
    {"text": "你在太虚之中找到了一片尚未崩塌的道域。", "effects": {"cultivation": 85, "comprehension": 6}, "tags": ["fortune", "secret_realm"]},
    {"text": "天道降下功德金光浇灌了你的元神。", "effects": {"cultivation": 90, "willpower": 4}, "tags": ["fortune", "encounter"]},
    {"text": "你从一颗陨落的星辰核心中提取了星辰本源。", "effects": {"cultivation": 75, "constitution": 4}, "tags": ["fortune", "treasure"]},
    {"text": "你在一次入定中经历了九世轮回——每一世都有一份感悟留下。", "effects": {"comprehension": 9, "willpower": 5}, "tags": ["fortune", "dream"]},
    {"text": "你悟到了生死轮回的真谛——肉身开始缓慢蜕变。", "effects": {"constitution": 5, "cultivation": 60, "lifespan": 30}, "tags": ["fortune", "encounter"]},
    {"text": "你在混沌深处发现了一片诞生中的小千世界。", "effects": {"comprehension": 8, "cultivation": 60}, "tags": ["fortune", "discovery"]},
    {"text": "一座天门在你头顶虚影浮现——虽然转瞬即逝，可你记住了它的样子。", "effects": {"comprehension": 9, "willpower": 4}, "tags": ["fortune", "encounter"]},
    {"text": "你的化神法相在天地灵力的洗礼下凝实了数倍。", "effects": {"cultivation": 90}, "tags": ["fortune", "encounter"]},
    {"text": "你与天道达成了某种默契——你能感觉到它在注视你。", "effects": {"comprehension": 8, "fortune": 3}, "tags": ["fortune", "encounter"]},
    {"text": "你从一位陨落的大帝遗骸中得到了一滴精血。", "effects": {"constitution": 5, "cultivation": 70}, "tags": ["fortune", "treasure"]},
    {"text": "你在证道之途上跨过了最关键的一步——天地为之一静。", "effects": {"cultivation": 100, "comprehension": 5}, "tags": ["fortune", "encounter"]},
    {"text": "一枚仙界遗留的造化神珠落入了你的丹田。", "effects": {"cultivation": 85, "fortune": 4}, "tags": ["fortune", "treasure"]},
    {"text": "你在虚空中与另一位化神期强者论道三日——彼此获益匪浅。", "effects": {"comprehension": 7, "cultivation": 50}, "tags": ["fortune", "encounter"]},
    {"text": "你的元神在雷劫中完成了涅槃——焕然一新。", "effects": {"cultivation": 80, "constitution": 4, "willpower": 3}, "tags": ["fortune", "encounter"]},
    {"text": "你在太古之地找到了一处尚存仙气的洞天。", "effects": {"cultivation": 75, "lifespan": 25}, "tags": ["fortune", "secret_realm"]},
    {"text": "你以化神之力凝练了一滴液态灵力——这是传说中的仙露。", "effects": {"cultivation": 70, "fortune": 3}, "tags": ["fortune", "encounter"]},
    {"text": "你的本命法宝在你突破时自行化为仙器。", "effects": {"fortune": 5, "cultivation": 50}, "tags": ["fortune", "treasure"]},
    {"text": "你在一块混沌石中找到了一枚完整的道果种子。", "effects": {"comprehension": 9, "cultivation": 60}, "tags": ["fortune", "treasure"]},
    {"text": "你在太虚深处遇见了自己前世的残魂——它将记忆还给了你。", "effects": {"comprehension": 8, "willpower": 5}, "tags": ["fortune", "dream"]},
    {"text": "一道天雷精华主动融入了你的体内。", "effects": {"constitution": 4, "cultivation": 65}, "tags": ["fortune", "encounter"]},
    {"text": "你在一处遗忘之地找到了仙界陨落时散落的碎片。", "effects": {"cultivation": 80, "fortune": 3}, "tags": ["fortune", "treasure"]},
    {"text": "你在顿悟中看见了自己飞升的画面——那不是幻觉。", "effects": {"willpower": 5, "comprehension": 7}, "tags": ["fortune", "vision"]},
    {"text": "天地间的法则之力被你撬动了一丝——万物为之震颤。", "effects": {"comprehension": 9, "cultivation": 55}, "tags": ["fortune", "encounter"]},
    {"text": "你在劫云之上发现了一座被遗忘的仙人道场。", "effects": {"cultivation": 75, "comprehension": 6}, "tags": ["fortune", "secret_realm"]},
    {"text": "你的化神法相在一次战斗中自行觉醒了神通。", "effects": {"cultivation": 70, "fortune": 3}, "tags": ["fortune", "encounter"]},
    {"text": "一位天仙的道韵残留被你的神识捕捉到了。", "effects": {"comprehension": 9, "cultivation": 40}, "tags": ["fortune", "encounter"]},
    {"text": "你在寂灭之地悟到了「无」之真意。", "effects": {"comprehension": 10, "willpower": 4}, "tags": ["fortune", "encounter"]},
    {"text": "你的三花聚顶在一次感悟中完成——离飞升只差一步。", "effects": {"cultivation": 95, "comprehension": 5}, "tags": ["fortune", "encounter"]},
    {"text": "一口上古仙剑从地底飞出认你为主。", "effects": {"fortune": 5, "cultivation": 50}, "tags": ["fortune", "treasure"]},
    {"text": "你在天劫之后吸收了劫云中残留的天道气息。", "effects": {"cultivation": 80, "comprehension": 5}, "tags": ["fortune", "encounter"]},
    {"text": "一座浮空仙宫的主人在沉睡万年后苏醒——选你为继承者。", "effects": {"cultivation": 90, "fortune": 4}, "tags": ["fortune", "secret_realm"]},
    {"text": "你在虚空乱流中意外发现了一条通往更高境界的线索。", "effects": {"comprehension": 8, "cultivation": 60}, "tags": ["fortune", "discovery"]},
    {"text": "你的元神脱离了肉身的桎梏——在太虚中自由翱翔了三日。", "effects": {"comprehension": 7, "willpower": 4}, "tags": ["fortune", "encounter"]},
    {"text": "一位即将飞升的老友将道场托付给了你。", "effects": {"cultivation": 70, "fortune": 3}, "tags": ["fortune", "encounter"]},
    {"text": "你在岁月长河中感知到了自己的命运轨迹——并轻轻拨动了它。", "effects": {"fortune": 5, "comprehension": 6}, "tags": ["fortune", "encounter"]},
    {"text": "天地间的灵气在你周围形成了永恒的旋涡——你已被大道认可。", "effects": {"cultivation": 100}, "tags": ["fortune", "encounter"]},
    {"text": "你在太阳精火中淬炼了七七四十九日——浴火重生。", "effects": {"constitution": 5, "cultivation": 70}, "tags": ["fortune", "encounter"]},
    {"text": "你以化神之力打开了一处尘封的上界通道。", "effects": {"cultivation": 80, "comprehension": 6}, "tags": ["fortune", "secret_realm"]},
    {"text": "你在感悟大道时引发了方圆百里的天花乱坠。", "effects": {"cultivation": 85, "comprehension": 5}, "tags": ["fortune", "encounter"]},
    {"text": "一尊远古时期的造化鼎认你为主——它等了太久了。", "effects": {"fortune": 5, "cultivation": 60}, "tags": ["fortune", "treasure"]},
    {"text": "你在绝世大战的废墟中收集到了数位强者遗留的道韵。", "effects": {"comprehension": 8, "cultivation": 55}, "tags": ["fortune", "treasure"]},
    {"text": "你的神识在一瞬间覆盖了整个大陆——你看见了一切。", "effects": {"comprehension": 9, "willpower": 4}, "tags": ["fortune", "encounter"]},
    {"text": "一面映照万物的古镜为你指出了飞升的路径。", "effects": {"comprehension": 10, "fortune": 3}, "tags": ["fortune", "vision"]},
    {"text": "你在太虚之境得到了一缕仙界灵液。", "effects": {"cultivation": 85, "lifespan": 30}, "tags": ["fortune", "treasure"]},
    {"text": "天降紫气灌顶——你的化神之路再无阻碍。", "effects": {"cultivation": 100, "comprehension": 5}, "tags": ["fortune", "encounter"]},
]


def pick_by_hash(event_id, choices):
    h = int(hashlib.md5(event_id.encode()).hexdigest(), 16)
    return choices[h % len(choices)]


def pick_by_hash_idx(event_id, salt, choices):
    h = int(hashlib.md5(f"{event_id}_{salt}".encode()).hexdigest(), 16)
    return choices[h % len(choices)]


# 高境界开头（比低境界更宏大/更有气魄）
HIGH_REALM_OPENINGS = [
    "你已经不是当年那个四处奔波寻找机缘的小修士了——可机缘这东西从来不挑人。",
    "修至此境，你早已不为外物所动——可当它出现在你面前时，你还是忍不住多看了一眼。",
    "天地大道自有安排——你不信命，可这一次你觉得也许命运在注视你。",
    "你的灵识覆盖了方圆数十里——所以你比任何人都更早感知到了那股异常。",
    "修炼至今，真正让你心动的东西已经不多了。可今天例外。",
    "你本在闭关——是一阵强烈的感应将你从入定中惊醒。那个方向有东西在呼唤你。",
    "千年修道，你阅历之广足以让你分辨什么是真正的造化——而这一次是真的。",
    "你不再像年轻时那样大惊小怪——可当那道气息扑面而来时，你的瞳孔仍然猛地收缩了。",
    "你在这个境界已经停留了太久——你知道自己需要一个契机。而它来了。",
    "以你如今的修为，能让你心跳加速的东西已经寥寥无几——可偏偏今日就撞上了一个。",
    "你原本只是随意神游太虚——可你的元神忽然被什么东西吸引了过去。",
    "你在修道路上见过太多机缘——大部分不过尔尔。可今日这一份不同。",
    "你甚至不确定这是运气还是实力——也许到了你这个境界，两者已经分不清了。",
    "万年修行，你的直觉从未出错过。此刻它在告诉你——就是这里。",
    "你停下了脚步——以你如今的感知，不可能漏掉这么明显的异象。",
    "你已经见惯了天地异象——可眼前这一幕仍让你屏住了呼吸。",
    "冥冥之中你感到了一股牵引——那是只有到了这个境界才能感知到的天地意志。",
    "你抬头看了一眼天穹——嗯，那道裂缝不是你的错觉。有东西在从更高的地方落下来。",
    "你的道心告诉你这里有属于你的东西——修至此境，你已学会相信自己的道心。",
    "一万年也好一千年也好——修道之人不计时日。可你知道这一刻值得记住。",
]

HIGH_REALM_CLOSINGS = [
    "你收好所得——面上平静如水。修至此境，你早已喜怒不形于色。可心底确实轻快了几分。",
    "你默默消化着这份收获——它将使你离大道更近一步。",
    "你望了一眼天穹——天道无言，可你隐约感到它在对你微笑。",
    "你长身而起——这份造化来得恰到好处。你知道自己该做什么了。",
    "你将此事记入道心深处——不是为了记忆，而是让它成为你大道的一部分。",
    "你闭目感悟了良久——等你睁开眼时，天地在你眼中又清晰了几分。",
    "修道至此，你已不再为得失所动——可你仍然心存感激。大道不负苦心人。",
    "你没有声张——以你如今的城府，外人从你脸上看不出任何端倪。",
    "你深吸一口气——嗯，天地灵气今日格外甘甜。你微微一笑。",
    "你坐在原地消化了整整三日——这份收获比你想象的还要深远。",
]


def generate_high_realm_expanded(event_id, text, realm):
    """为高境界事件生成expanded_text"""
    opening = pick_by_hash(event_id, HIGH_REALM_OPENINGS)
    closing = pick_by_hash_idx(event_id, "closing", HIGH_REALM_CLOSINGS)
    
    # 根据text内容生成中间段
    mid_scenes = [
        f"你凝神感知——确认了它的真实性之后才缓缓伸出手。{text}那一刻你能清晰感受到自身修为的跃升——像是一扇门被推开了。",
        f"你几乎不需要刻意去找——以你的修为，这种级别的灵物主动就会向你靠拢。{text}你闭目感悟了片刻——嗯，确实是难得的造化。",
        f"你从容不迫——以你的见识，你知道该怎么处理这种级别的机缘。{text}你将其缓缓收入体内——灵力的反馈如潮水般涌来。",
        f"天地之间似乎有一道无形的力量在推动着一切朝你汇聚。{text}你沉默了很久——然后缓缓点了点头，接受了这份馈赠。",
        f"你甚至不需要出手——它自己飘向了你。{text}你心中并无太大波澜——修至此境，你知道这些都是应得之物。",
        f"你站在原地一动不动——只用意念便完成了整个过程。{text}你微微一笑——这个境界的好处就是，很多事情变得轻而易举了。",
        f"你用了极长的时间来确认——不是怀疑它的真伪，而是在评估它能给你带来多大的提升。{text}答案让你很满意。",
        f"你以大神通将其封存——不急着用，等最合适的时机再取出。{text}你知道好东西要在对的时候用才能发挥最大价值。",
    ]
    
    scene = pick_by_hash_idx(event_id, "scene", mid_scenes)
    return f"{opening}{scene}{closing}"


def main():
    input_path = Path(__file__).parent / "events" / "fortune.json"
    
    with open(input_path, 'r', encoding='utf-8') as f:
        events = json.load(f)
    
    print(f"原有 {len(events)} 个Fortune事件")
    
    # 获取现有最大编号
    existing_ids = {ev['id'] for ev in events}
    
    all_realm_events = [
        (2, REALM_2_EVENTS),
        (3, REALM_3_EVENTS),
        (4, REALM_4_EVENTS),
        (5, REALM_5_EVENTS),
    ]
    
    new_count = 0
    for realm, realm_events in all_realm_events:
        for i, ev_template in enumerate(realm_events):
            event_id = f"fortune_r{realm}_{i+1:03d}"
            if event_id in existing_ids:
                continue
            
            new_event = {
                "id": event_id,
                "text": ev_template["text"],
                "category": "fortune",
                "conditions": {"min_realm": realm},
                "weight": 35,
                "effects": ev_template["effects"],
                "tags": ev_template["tags"],
                "event_type": "fortune",
                "expanded_text": generate_high_realm_expanded(event_id, ev_template["text"], realm),
            }
            events.append(new_event)
            existing_ids.add(event_id)
            new_count += 1
    
    with open(input_path, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    
    print(f"新增 {new_count} 个高境界事件")
    print(f"总计 {len(events)} 个Fortune事件")
    
    # 统计境界分布
    from collections import Counter
    realm_dist = Counter(ev.get('conditions', {}).get('min_realm', 0) for ev in events)
    print(f"境界分布: {dict(sorted(realm_dist.items()))}")
    
    # 新增事件的文案统计
    new_events = [ev for ev in events if ev['id'].startswith('fortune_r')]
    if new_events:
        lengths = [len(ev['expanded_text']) for ev in new_events]
        print(f"新事件文案长度: min={min(lengths)}, avg={sum(lengths)//len(lengths)}, max={max(lengths)}")


if __name__ == '__main__':
    main()
