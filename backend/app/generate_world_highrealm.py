"""
高境界World事件生成器
为 world.json 补充 筑基/金丹/元婴/化神 各30个专属事件 = 120新事件
"""
import json
import hashlib
from pathlib import Path


def pick_by_hash(event_id, choices):
    h = int(hashlib.md5(event_id.encode()).hexdigest(), 16)
    return choices[h % len(choices)]

def pick_by_hash_idx(event_id, salt, choices):
    h = int(hashlib.md5(f"{event_id}_{salt}".encode()).hexdigest(), 16)
    return choices[h % len(choices)]


# ============================================================
# 高境界World事件模板
# ============================================================

REALM_2_EVENTS = [
    {"text": "传闻附近山脉发现了一处千年未开的古修士洞府。", "effects": {"add_tag": "explorer"}, "tags": ["world_event"]},
    {"text": "修真界近来妖兽频繁异动，似乎有大事将发。", "effects": {}, "tags": ["world_event"]},
    {"text": "一场百年难遇的灵气潮汐正席卷整片大陆。", "effects": {"cultivation": 10}, "tags": ["world_event"]},
    {"text": "某门派宣布举办筑基期修士的论道大会。", "effects": {"add_tag": "in_sect"}, "tags": ["world_event"]},
    {"text": "一位筑基大圆满的修士成功结丹，引发天象异变。", "effects": {}, "tags": ["world_event"]},
    {"text": "坊市中突然涌入大量高品灵材——似乎有古墓被人打开了。", "effects": {"add_tag": "in_market"}, "tags": ["world_event"]},
    {"text": "一只万年冰蟒出现在了人族的领地边缘。", "effects": {}, "tags": ["world_event"]},
    {"text": "修真界传出消息：北方荒原出现了一座浮空遗迹。", "effects": {"add_tag": "explorer"}, "tags": ["world_event"]},
    {"text": "各派门主齐聚商讨应对魔修入侵之策。", "effects": {"add_tag": "in_sect"}, "tags": ["world_event"]},
    {"text": "一处被封印千年的秘境裂缝正在扩大。", "effects": {}, "tags": ["world_event"]},
    {"text": "附近的灵脉突然枯竭——有人在暗中吸取灵气。", "effects": {}, "tags": ["world_event"]},
    {"text": "一位散修在荒野中悟道成功，引来数十道贺者。", "effects": {}, "tags": ["world_event"]},
    {"text": "天空出现了七彩霞光——是有人在炼制极品丹药。", "effects": {}, "tags": ["world_event"]},
    {"text": "修真界最大的拍卖行宣布将拍卖一件上古残宝。", "effects": {"add_tag": "in_market"}, "tags": ["world_event"]},
    {"text": "一场突如其来的灵雨降临——所有在户外修炼的人都获益不少。", "effects": {"cultivation": 15}, "tags": ["world_event"]},
    {"text": "附近矿脉中发现了一种从未见过的灵矿。", "effects": {}, "tags": ["world_event"]},
    {"text": "一位大能的弟子在公开场合挑战了数位同辈修士。", "effects": {}, "tags": ["world_event"]},
    {"text": "传言南方海域中有蛟龙出没。", "effects": {}, "tags": ["world_event"]},
    {"text": "一本失传功法的残页在坊市上被人天价拍走。", "effects": {"add_tag": "in_market"}, "tags": ["world_event"]},
    {"text": "修真界各派纷纷关闭山门——似乎在防备什么。", "effects": {}, "tags": ["world_event"]},
    {"text": "一处荒原上突然长出了大片灵草——天地造化无常。", "effects": {}, "tags": ["world_event"]},
    {"text": "一位前辈公开收徒——报名者排到了山门外十里。", "effects": {}, "tags": ["world_event"]},
    {"text": "两大宗门因灵脉归属爆发了一场激烈的冲突。", "effects": {}, "tags": ["world_event"]},
    {"text": "有人在深海中发现了一座沉没的城市遗迹。", "effects": {"add_tag": "explorer"}, "tags": ["world_event"]},
    {"text": "修真界的灵石价格突然暴涨——据说是产地出了问题。", "effects": {}, "tags": ["world_event"]},
    {"text": "一只上古灵兽从沉睡中苏醒——整座山都在颤抖。", "effects": {}, "tags": ["world_event"]},
    {"text": "有人在传音符中散播了一条危险信息——修真界人心惶惶。", "effects": {}, "tags": ["world_event"]},
    {"text": "一场覆盖数千里的暴风来袭——据说是两位强者斗法的余波。", "effects": {}, "tags": ["world_event"]},
    {"text": "天空中连续三日出现红月——占星师说这预示着变故。", "effects": {}, "tags": ["world_event"]},
    {"text": "修真界各大势力正在组建联盟以应对即将到来的兽潮。", "effects": {}, "tags": ["world_event"]},
]

REALM_3_EVENTS = [
    {"text": "一位金丹真人当众渡劫——方圆百里都能看到劫云。", "effects": {}, "tags": ["world_event"]},
    {"text": "远古时期的一座仙府重现人间——各方强者闻风而动。", "effects": {"add_tag": "explorer"}, "tags": ["world_event"]},
    {"text": "修真界传出消息：北方妖族的妖王已经苏醒。", "effects": {}, "tags": ["world_event"]},
    {"text": "一场席卷数万里的灵气风暴正从东方逼近。", "effects": {}, "tags": ["world_event"]},
    {"text": "数十位金丹期强者联手开启了一处远古秘境。", "effects": {"add_tag": "explorer"}, "tags": ["world_event"]},
    {"text": "天地间出现了一道巨大的裂缝——有异界之物正在渗透。", "effects": {}, "tags": ["world_event"]},
    {"text": "一位金丹期强者陨落——他的遗宝散落四方，引发哄抢。", "effects": {"add_tag": "in_market"}, "tags": ["world_event"]},
    {"text": "修真界百年一遇的七星连珠即将到来——是闭关悟道的绝佳时机。", "effects": {"cultivation": 20}, "tags": ["world_event"]},
    {"text": "一座沉寂万年的火山突然喷发——火焰中似乎有什么东西在苏醒。", "effects": {}, "tags": ["world_event"]},
    {"text": "有人公开叫卖一枚据说能助人结丹的秘宝。", "effects": {"add_tag": "in_market"}, "tags": ["world_event"]},
    {"text": "一个隐世数千年的古老门派突然重新出山。", "effects": {}, "tags": ["world_event"]},
    {"text": "深海中的海底龙宫遗址被人发现——引来了大量探险者。", "effects": {"add_tag": "explorer"}, "tags": ["world_event"]},
    {"text": "修真界的天道法则似乎变得更加严苛——突破越来越难了。", "effects": {}, "tags": ["world_event"]},
    {"text": "两大金丹期强者约战——整座山脉都因之战栗。", "effects": {}, "tags": ["world_event"]},
    {"text": "一场瘟疫正在修真界蔓延——据说是远古邪修的诅咒。", "effects": {}, "tags": ["world_event"]},
    {"text": "修真界最古老的藏经阁对外开放了三日。", "effects": {"comprehension": 2}, "tags": ["world_event"]},
    {"text": "天空中出现了远古大能斗法的残影——那是万年前的战斗余波。", "effects": {}, "tags": ["world_event"]},
    {"text": "一片新的灵脉被发现——各方势力正在协商分配方案。", "effects": {}, "tags": ["world_event"]},
    {"text": "一位传说中早已陨落的大能竟然还活着——修真界为之震动。", "effects": {}, "tags": ["world_event"]},
    {"text": "魔修大军压境——各正道门派紧急备战。", "effects": {}, "tags": ["world_event"]},
    {"text": "天降异石——里面蕴含着不属于此界的能量。", "effects": {}, "tags": ["world_event"]},
    {"text": "修真界的灵气浓度近百年来首次出现了回升的趋势。", "effects": {"cultivation": 10}, "tags": ["world_event"]},
    {"text": "一位炼器宗师宣布退隐——他最后一件作品被各方争夺。", "effects": {"add_tag": "in_market"}, "tags": ["world_event"]},
    {"text": "一座浮空岛从云层中降落——上面似乎有一座完整的仙府。", "effects": {"add_tag": "explorer"}, "tags": ["world_event"]},
    {"text": "三大宗门同时闭关——据说在联手推演某件大事。", "effects": {}, "tags": ["world_event"]},
    {"text": "修真界发生了一场大地震——震源似乎来自极深的地底。", "effects": {}, "tags": ["world_event"]},
    {"text": "有人在南方荒漠中建立了一座新城——吸引了众多散修汇聚。", "effects": {}, "tags": ["world_event"]},
    {"text": "一位金丹期修士公开挑战元婴期强者——震惊了整个修真界。", "effects": {}, "tags": ["world_event"]},
    {"text": "天道降下异象——满天星辰在白昼中可见。修士们纷纷仰望。", "effects": {}, "tags": ["world_event"]},
    {"text": "修真界的时间似乎在某些区域开始紊乱——有人一夜白头。", "effects": {}, "tags": ["world_event"]},
]

REALM_4_EVENTS = [
    {"text": "一位元婴期大能在渡天劫时引动了方圆千里的灵气。", "effects": {}, "tags": ["world_event"]},
    {"text": "虚空中出现了通往上界的裂缝——虽然只有一瞬便消失了。", "effects": {}, "tags": ["world_event"]},
    {"text": "修真界的天道压制似乎松动了——数位强者同时感应到了突破的契机。", "effects": {"cultivation": 25}, "tags": ["world_event"]},
    {"text": "一座太古时期的仙城从地底升起——城中的阵法仍在运转。", "effects": {"add_tag": "explorer"}, "tags": ["world_event"]},
    {"text": "两位元婴期强者的斗法将一座山脉削平了。", "effects": {}, "tags": ["world_event"]},
    {"text": "天地间出现了大量时空裂缝——有其他世界的生物在渗入。", "effects": {}, "tags": ["world_event"]},
    {"text": "修真界所有元婴期以上的修士同时做了一个相同的梦。", "effects": {}, "tags": ["world_event"]},
    {"text": "一尊远古神像睁开了眼——注视着整片大陆。", "effects": {}, "tags": ["world_event"]},
    {"text": "天道降下了一道谕令——所有修士都能感知到那道意志。", "effects": {}, "tags": ["world_event"]},
    {"text": "一片虚空突然碎裂——上界的灵气如瀑布般倾泻而下。", "effects": {"cultivation": 30}, "tags": ["world_event"]},
    {"text": "修真界最古老的大阵突然自行运转——没人知道是谁触发了它。", "effects": {}, "tags": ["world_event"]},
    {"text": "一位元婴强者带回了上界的消息——修真界为之沸腾。", "effects": {}, "tags": ["world_event"]},
    {"text": "数座灵山同时崩塌——底下露出了远古时期的建筑群。", "effects": {"add_tag": "explorer"}, "tags": ["world_event"]},
    {"text": "天地法则出现了短暂的空白——在那一刻所有禁制都失效了。", "effects": {}, "tags": ["world_event"]},
    {"text": "修真界的数位顶尖强者同时闭关——天地间的灵气因之波动。", "effects": {}, "tags": ["world_event"]},
    {"text": "一颗远古星辰在天空中闪耀——它已经消失了万年。", "effects": {}, "tags": ["world_event"]},
    {"text": "一头太古凶兽破开了封印——数十位强者联手才将其重新镇压。", "effects": {}, "tags": ["world_event"]},
    {"text": "修真界的所有灵脉在同一时刻发生了共振。", "effects": {"cultivation": 20}, "tags": ["world_event"]},
    {"text": "一座通天之塔在虚空中显现——据说登顶者可问道于天。", "effects": {}, "tags": ["world_event"]},
    {"text": "天地间的因果之线变得可见了——所有修士都看到了自己的命运纹路。", "effects": {}, "tags": ["world_event"]},
    {"text": "一位即将飞升的强者留下了最后的公开传法。", "effects": {"comprehension": 3}, "tags": ["world_event"]},
    {"text": "修真界的天穹上出现了古老的文字——没人能完全解读。", "effects": {}, "tags": ["world_event"]},
    {"text": "一片新的空间从虚无中诞生了——天地还在生长。", "effects": {}, "tags": ["world_event"]},
    {"text": "所有元婴以上修士的本命法宝在同一刻发出了共鸣。", "effects": {}, "tags": ["world_event"]},
    {"text": "修真界出现了一位新的元婴期强者——打破了百年来无人突破的僵局。", "effects": {}, "tags": ["world_event"]},
    {"text": "一座远古传送阵连通了另一片大陆——新的时代即将开始。", "effects": {}, "tags": ["world_event"]},
    {"text": "天地之间响起了一声叹息——像是某位存在在感慨什么。", "effects": {}, "tags": ["world_event"]},
    {"text": "修真界各方势力达成了千年以来最重要的一次协议。", "effects": {}, "tags": ["world_event"]},
    {"text": "一条沉睡在大地深处的龙脉苏醒了——整片大陆的灵气格局将因此改变。", "effects": {}, "tags": ["world_event"]},
    {"text": "虚空深处传来了战斗的余波——不知是哪两位强者在域外交手。", "effects": {}, "tags": ["world_event"]},
]

REALM_5_EVENTS = [
    {"text": "天道降下了亘古未有的大劫——整个修真界都在颤抖。", "effects": {}, "tags": ["world_event"]},
    {"text": "有人成功飞升了——在天地间留下了一道永恒的痕迹。", "effects": {"comprehension": 3}, "tags": ["world_event"]},
    {"text": "修真界的天道法则正在改写——一个新的纪元即将降临。", "effects": {}, "tags": ["world_event"]},
    {"text": "上界的大门短暂开启了——仙气倾泻而下洗礼了整片大陆。", "effects": {"cultivation": 35}, "tags": ["world_event"]},
    {"text": "一位化神期大能自爆了——方圆万里化为焦土。", "effects": {}, "tags": ["world_event"]},
    {"text": "时间在某些地方开始倒流——过去的亡魂短暂地出现了。", "effects": {}, "tags": ["world_event"]},
    {"text": "天地间的法则之锁松动了——飞升的可能性正在增加。", "effects": {"cultivation": 30}, "tags": ["world_event"]},
    {"text": "修真界的历史长河在所有化神修士眼前展开——他们看到了开天辟地。", "effects": {"comprehension": 4}, "tags": ["world_event"]},
    {"text": "一位从上界坠落的仙人出现在了修真界——浑身伤痕累累。", "effects": {}, "tags": ["world_event"]},
    {"text": "修真界最古老的预言正在逐一应验。", "effects": {}, "tags": ["world_event"]},
    {"text": "天地之间的灵气浓度在一夜之间翻了一倍。", "effects": {"cultivation": 40}, "tags": ["world_event"]},
    {"text": "所有化神期强者同时感应到了一道来自更高层面的召唤。", "effects": {}, "tags": ["world_event"]},
    {"text": "修真界的天穹碎了一角——透过裂缝能看到另一重天地。", "effects": {}, "tags": ["world_event"]},
    {"text": "一场涉及整个大陆的大战即将到来——所有势力都在备战。", "effects": {}, "tags": ["world_event"]},
    {"text": "天道意志亲自降临——在大地上留下了一行文字。", "effects": {"comprehension": 5}, "tags": ["world_event"]},
    {"text": "修真界与魔界之间的屏障正在变薄——融合似乎不可避免。", "effects": {}, "tags": ["world_event"]},
    {"text": "三位化神期大能同时渡劫——天空中九道天雷交织如龙。", "effects": {}, "tags": ["world_event"]},
    {"text": "修真界的因果之网出现了紊乱——许多人的命运轨迹发生了偏转。", "effects": {}, "tags": ["world_event"]},
    {"text": "一座万古仙山从虚空中降临——压在了修真界的中心位置。", "effects": {}, "tags": ["world_event"]},
    {"text": "所有修真者的梦中出现了同一个画面——那是末日的预兆。", "effects": {}, "tags": ["world_event"]},
    {"text": "修真界最强大的封印裂开了——被镇压亿万年的存在正在苏醒。", "effects": {}, "tags": ["world_event"]},
    {"text": "天地间出现了一条通往仙界的虹桥——但仅存在了七日。", "effects": {"cultivation": 30}, "tags": ["world_event"]},
    {"text": "轮回之力在人间具现——死去的强者纷纷短暂复生。", "effects": {}, "tags": ["world_event"]},
    {"text": "修真界的大道显化了——它的形状像一棵无限延伸的大树。", "effects": {"comprehension": 4}, "tags": ["world_event"]},
    {"text": "所有法宝在同一刻颤鸣——天地共震。", "effects": {}, "tags": ["world_event"]},
    {"text": "一位化神期强者证道成仙——整个大陆都沐浴在仙光之中。", "effects": {"cultivation": 25}, "tags": ["world_event"]},
    {"text": "天道降下了选择——修真界的走向将由此刻的决定来决定。", "effects": {}, "tags": ["world_event"]},
    {"text": "万古岁月中沉淀的道韵在空气中弥漫——每一口呼吸都是修行。", "effects": {"cultivation": 30, "comprehension": 3}, "tags": ["world_event"]},
    {"text": "修真界诞生了有史以来最强的一人——天地为之让路。", "effects": {}, "tags": ["world_event"]},
    {"text": "一个新的时代在旧时代的废墟上拉开了序幕。", "effects": {}, "tags": ["world_event"]},
]

# World事件expanded_text开头
WORLD_OPENINGS = [
    "消息传来时你正在修炼——你停了下来，侧耳倾听。",
    "你从旁人口中得知了这件事——修真界的风云从不等人。",
    "天际的异象你也看到了——你抬头注视了很久。",
    "这件事在修真界掀起了轩然大波——就连你这样不问世事的人也有所耳闻。",
    "你站在山巅远眺——能感知到远方的灵气波动。那里正在发生大事。",
    "传音符接连不断地飞来——世间正发生着什么。你叹了口气，决定关注一下。",
    "你在坊市中听到了纷纷议论——看来这件事已经传遍了。",
    "你的灵识感知到了天地间微妙的变化——修行至今，这种感觉从不骗人。",
    "你本无意插手世间纷争——可有些事大到无法忽视。",
    "你从闭关中被一阵天地异动惊醒——出关后才知道发生了什么。",
    "消息是一位故交通过传音符告诉你的——你听完后沉默了许久。",
    "你亲眼目睹了天边的异象——那不是幻觉，是真真切切发生了。",
    "你原本在洞府中安静修炼——可天地灵气的突然波动让你不得不出关查看。",
    "整个修真界都在谈论此事——你走到哪里都能听到。",
    "你的道友来信说了这件事——字里行间带着震惊和不安。",
]

WORLD_SCENES = [
    "你沉思了良久——这件事对修真界的格局恐怕会有深远影响。而你身处其中，不可能独善其身。你决定密切关注后续发展。",
    "你闭上眼感悟了一番——天地的变化中也蕴含着机缘。能从中获益多少，就看各人的悟性了。你决定把握这个机会。",
    "你抬头望了望天——修真界从来都不平静。强者争锋、天道无常——而你只能在其中寻找属于自己的路。",
    "你心中有了计较——这件事对你而言既是风险也是机会。你决定做好两手准备。",
    "你摇了摇头——这世间之事纷繁复杂，你管不了那么多。做好自己的修炼才是正经。可你还是默默记住了这个消息。",
    "你感到了一丝紧迫——修真界的格局在变，你若不跟上节奏便会被淘汰。你暗暗下定决心要更加努力。",
    "你望着天边的方向出了一会儿神——这个世界从来都不缺故事。而你自己也是其中的一个角色。你深吸一口气，转身回去继续修炼。",
    "你将此事记在心中——也许未来某一天它会与你产生关联。修道之人当有预见之明。",
]

WORLD_CLOSINGS = [
    "你在心中默默盘算了一番——然后转身回去继续自己的修炼。路是自己走的。",
    "你深吸一口气——管它天塌地陷，你只管修好自己的道。",
    "你将此事暂且搁下——目前你能做的只有变得更强。足够强了，才有资格参与这些。",
    "你重新入定——世事纷扰，不变的只有你脚下这条大道。继续走便是。",
    "你关上了洞府的门——外面的风浪再大，也要先稳住自己的根基。",
]

WORLD_MIDDLES = [
    "你细细品味着这个消息中蕴含的信息——以你的阅历，你能从中读出许多旁人读不出的东西。",
    "你在原地站了很久——任由山风吹拂。你的心绪翻涌了片刻才慢慢平息下来。",
    "你默默将此事与近来的种种异象联系到了一起——越想越觉得这不是巧合。",
    "你回想起曾经在某本古籍中读到过类似的记载——如果所料不差的话，这只是开始。",
    "你环顾四周——同修们的脸上写满了或兴奋、或忧虑的神色。每个人都在思考这意味着什么。",
    "你闭目感知了一下天地灵气的状态——确实与往日有所不同。变化已经开始了。",
    "你想起师父在很久以前说过的一句话——当时你不以为意，如今却觉得意味深长。",
    "你在脑中推演了几种可能的走向——每一种都不容乐观。但也每一种都藏着机缘。",
]


def generate_world_expanded(event_id, text):
    opening = pick_by_hash(event_id, WORLD_OPENINGS)
    middle = pick_by_hash_idx(event_id, "mid", WORLD_MIDDLES)
    scene = pick_by_hash_idx(event_id, "scene", WORLD_SCENES)
    closing = pick_by_hash_idx(event_id, "closing", WORLD_CLOSINGS)
    return f"{opening}{middle}{scene}{closing}"


def main():
    input_path = Path(__file__).parent / "events" / "world.json"
    
    with open(input_path, 'r', encoding='utf-8') as f:
        events = json.load(f)
    
    print(f"原有 {len(events)} 个World事件")
    
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
            event_id = f"world_r{realm}_{i+1:03d}"
            if event_id in existing_ids:
                continue
            
            new_event = {
                "id": event_id,
                "text": ev_template["text"],
                "category": "world",
                "conditions": {"min_realm": realm},
                "weight": 30,
                "effects": ev_template["effects"],
                "tags": ev_template["tags"],
                "event_type": "normal",
                "expanded_text": generate_world_expanded(event_id, ev_template["text"]),
            }
            events.append(new_event)
            existing_ids.add(event_id)
            new_count += 1
    
    # 重写所有world事件的expanded_text
    for ev in events:
        ev['expanded_text'] = generate_world_expanded(ev['id'], ev['text'])
    
    with open(input_path, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    
    print(f"新增 {new_count} 个高境界事件")
    print(f"总计 {len(events)} 个World事件")
    
    from collections import Counter
    realm_dist = Counter(ev.get('conditions', {}).get('min_realm', 0) for ev in events)
    print(f"境界分布: {dict(sorted(realm_dist.items()))}")
    
    lengths = [len(ev['expanded_text']) for ev in events]
    print(f"文案长度: min={min(lengths)}, avg={sum(lengths)//len(lengths)}, max={max(lengths)}")


if __name__ == '__main__':
    main()
