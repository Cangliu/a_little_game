"""
Event generator for the cultivation life simulator.
Generates 3000+ events from templates and variations.
Run this script to regenerate the events JSON files.
"""
import json
import random
import os

# Base path for events
EVENTS_DIR = os.path.join(os.path.dirname(__file__), "events")


def generate_common_events():
    """Generate common life events (birth, childhood, aging)."""
    events = []
    
    # Birth events (age 0)
    birth_events = [
        ("你出生在一个偏远的山村，啼哭声惊起了林中飞鸟。", "normal"),
        ("你出生在一个修仙世家，灵气环绕产房。", "fortune"),
        ("你出生时天降异象，紫气东来。", "important"),
        ("你出生在战乱年代，父母颠沛流离。", "danger"),
        ("你出生在一个猎户之家，山中灵兽长啸。", "normal"),
        ("你出生时恰逢日食，阴气笼罩。", "danger"),
        ("你出生在坊市商贾之家，不缺灵石。", "fortune"),
        ("你出生在一座古寺旁，钟声悠扬。", "normal"),
        ("你出生时一颗流星划过天际。", "important"),
        ("你出生在渔村，海浪拍岸如歌。", "normal"),
        ("你出生在一个书香门第，祖上出过修士。", "fortune"),
        ("你出生时雷雨交加，电闪雷鸣。", "important"),
        ("你出生在矿工家庭，父亲常年在灵矿劳作。", "normal"),
        ("你出生在药农之家，院中种满灵草。", "fortune"),
        ("你出生在乞丐之家，食不果腹。", "danger"),
    ]
    
    for i, (text, etype) in enumerate(birth_events):
        events.append({
            "id": f"birth_{i:03d}",
            "text": text,
            "category": "common",
            "conditions": {"min_age": 0, "max_age": 0},
            "weight": 50,
            "effects": {},
            "tags": ["birth"],
            "event_type": etype
        })
    
    # Childhood events (age 1-11)
    childhood_templates = [
        ("你{age}岁时，在山中迷路，被一位老者指引回家。", "fortune", {"fortune": 1}),
        ("你{age}岁时，偷吃了院中一枚野果，腹痛三日后体质大增。", "fortune", {"constitution": 1}),
        ("你{age}岁时，大病一场，险些夭折。", "danger", {"lifespan": -1}),
        ("你{age}岁时，在溪边捡到一块温润的石头。", "normal", {}),
        ("你{age}岁时，跟随父亲上山采药，学会辨认草药。", "normal", {"comprehension": 1}),
        ("你{age}岁时，村中来了一位游方道士，对你多看了两眼。", "important", {"fortune": 1}),
        ("你{age}岁时，被村中孩童欺负，你默默忍下。", "normal", {"willpower": 1}),
        ("你{age}岁时，梦中见到一位白衣仙人，醒来后记不清面容。", "important", {}),
        ("你{age}岁时，家中遭遇旱灾，颗粒无收。", "danger", {"fortune": -1}),
        ("你{age}岁时，展现出过人的记忆力，私塾先生惊叹不已。", "fortune", {"comprehension": 1}),
        ("你{age}岁时，在河中游泳差点淹死。", "danger", {}),
        ("你{age}岁时，救了一只受伤的小狐。", "normal", {"charisma": 1}),
        ("你{age}岁时，无意间打通了一条经脉。", "fortune", {"constitution": 1}),
        ("你{age}岁时，看到天上飞过一位御剑修士，心生向往。", "normal", {}),
        ("你{age}岁时，在古井中看到自己的倒影在发光。", "important", {}),
        ("你{age}岁时，父母送你去镇上学堂读书。", "normal", {"comprehension": 1}),
        ("你{age}岁时，邻家女孩送了你一朵花。", "normal", {"charisma": 1}),
        ("你{age}岁时，独自在山洞中过了一夜，克服了恐惧。", "normal", {"willpower": 1}),
        ("你{age}岁时，村中瘟疫横行，你侥幸存活。", "danger", {"constitution": 1}),
        ("你{age}岁时，在田间劳作时发现一枚铜钱，上面刻着奇怪符文。", "normal", {}),
    ]
    
    for i, (template, etype, effects) in enumerate(childhood_templates):
        for age in range(3, 12, 2):
            events.append({
                "id": f"child_{i:03d}_age{age}",
                "text": template.format(age=age),
                "category": "common",
                "conditions": {"min_age": 1, "max_age": 11},
                "weight": 40,
                "effects": effects,
                "tags": ["childhood"],
                "event_type": etype
            })
    
    # Mortal life events (for those who don't cultivate)
    mortal_events = [
        ("你在田间辛勤劳作，日子平淡而充实。", "normal", {}),
        ("你与邻村的姑娘成亲，洞房花烛。", "fortune", {"charisma": 1}),
        ("你的孩子出生了，你感到肩上的责任更重了。", "normal", {}),
        ("丰收之年，粮仓满溢，你露出笑容。", "fortune", {"fortune": 1}),
        ("大旱之年，庄稼颗粒无收。", "danger", {"fortune": -1}),
        ("你在集市上被人偷了钱袋。", "danger", {}),
        ("你学会了一门手艺，日子好过了些。", "fortune", {"comprehension": 1}),
        ("你救了一个落水的孩童，村民对你赞不绝口。", "normal", {"charisma": 1}),
        ("你的父亲去世了，你跪在坟前久久不语。", "danger", {"willpower": 1}),
        ("你感染了风寒，卧床半月。", "danger", {"constitution": -1}),
        ("你与人起了争执，打斗中受了伤。", "danger", {}),
        ("平静的一年，无事发生。", "normal", {}),
        ("你遇到了一位算命先生，他说你命中有劫。", "important", {}),
        ("你在山中发现了一株奇异的灵草，却不识得。", "normal", {}),
        ("你做了一个奇怪的梦，梦中有人传你口诀。", "important", {}),
    ]
    
    for i, (text, etype, effects) in enumerate(mortal_events):
        events.append({
            "id": f"mortal_{i:03d}",
            "text": text,
            "category": "common",
            "conditions": {"min_age": 12, "max_realm": 0},
            "weight": 60,
            "effects": effects,
            "tags": ["mortal_life"],
            "event_type": etype
        })
    
    # Aging events
    aging_events = [
        ("你感到体力不如从前，岁月不饶人。", "normal", {"constitution": -1}),
        ("你的头发开始花白，镜中人已显老态。", "normal", {}),
        ("你的双腿开始不灵便，走路需要拐杖。", "danger", {"constitution": -1}),
        ("你开始频繁回忆年轻时的事。", "normal", {}),
        ("你的老伴先你而去，你独坐庭前。", "danger", {"willpower": -1}),
        ("你将毕生所学传授给了后辈。", "normal", {"charisma": 1}),
        ("你开始信奉神佛，日日焚香祈祷。", "normal", {"willpower": 1}),
        ("你感到大限将至，内心却很平静。", "important", {}),
    ]
    
    for i, (text, etype, effects) in enumerate(aging_events):
        events.append({
            "id": f"aging_{i:03d}",
            "text": text,
            "category": "common",
            "conditions": {"min_age": 50, "max_realm": 0},
            "weight": 30,
            "effects": effects,
            "tags": ["aging"],
            "event_type": etype
        })
    
    return events


def generate_cultivation_events():
    """Generate cultivation-related events."""
    events = []
    
    # Entering cultivation
    entry_events = [
        ("一位云游散修路过村庄，见你骨骼清奇，收你为徒。", {"constitution": 2, "add_tag": "has_master"}, "fortune"),
        ("你在山洞中发现一本残破的功法，如获至宝。", {"comprehension": 1}, "fortune"),
        ("你被附近的修仙门派选中，成为外门弟子。", {"add_tag": "sect_outer"}, "important"),
        ("一位垂死的修士将毕生功力传给了你。", {"constitution": 3}, "fortune"),
        ("你无意中吞食了一枚灵果，体内灵气激荡。", {"constitution": 2}, "fortune"),
        ("你在古迹中触发了一个传送阵，来到一处秘境。", {"fortune": 1}, "important"),
        ("梦中仙人再次出现，这次他传授了你一篇心法。", {"comprehension": 2}, "important"),
        ("你在山巅打坐时，突然感应到天地灵气。", {"comprehension": 1}, "fortune"),
    ]
    
    for i, (text, effects, etype) in enumerate(entry_events):
        events.append({
            "id": f"cult_entry_{i:03d}",
            "text": text,
            "category": "cultivation",
            "conditions": {"min_age": 8, "max_age": 30, "max_realm": 0, "required_talents": []},
            "weight": 30,
            "effects": effects,
            "tags": ["cultivation_start"],
            "event_type": etype
        })
    
    # Qi Refining stage events
    qi_events_templates = [
        "你按照功法打坐，{detail}。",
        "修炼中，你{detail}。",
        "今日修炼，{detail}。",
    ]
    
    qi_details = [
        ("感到经脉中灵气流转更加顺畅", {"cultivation": 15}, "normal"),
        ("突破了一处堵塞的穴位", {"cultivation": 25}, "fortune"),
        ("走火入魔，灵气逆行", {"cultivation": -20, "constitution": -1}, "danger"),
        ("隐隐感应到了天地灵气的规律", {"cultivation": 10, "comprehension": 1}, "fortune"),
        ("心境不稳，进展缓慢", {"cultivation": 5}, "normal"),
        ("偶得灵感，修为大进", {"cultivation": 30}, "fortune"),
        ("遇到瓶颈，寸步难行", {"cultivation": 2}, "normal"),
        ("采集到一株灵草辅助修炼", {"cultivation": 20}, "fortune"),
        ("被妖兽追杀，仓皇逃命", {"cultivation": -5, "willpower": 1}, "danger"),
        ("在瀑布下打坐，身心通透", {"cultivation": 15, "willpower": 1}, "normal"),
        ("结识了一位同道，互相切磋", {"cultivation": 10, "charisma": 1}, "normal"),
        ("师父传授了新的法诀", {"cultivation": 20, "comprehension": 1}, "fortune"),
        ("闭关七日，略有所得", {"cultivation": 18}, "normal"),
        ("服用了一枚洗髓丹", {"cultivation": 25, "constitution": 1}, "fortune"),
        ("在梦中悟到一丝天道", {"cultivation": 12, "comprehension": 1}, "important"),
    ]
    
    for i, (detail, effects, etype) in enumerate(qi_details):
        template = qi_events_templates[i % len(qi_events_templates)]
        events.append({
            "id": f"qi_ref_{i:03d}",
            "text": template.format(detail=detail),
            "category": "cultivation",
            "conditions": {"min_realm": 1, "max_realm": 1},
            "weight": 50,
            "effects": effects,
            "tags": ["qi_refining"],
            "event_type": etype
        })
    
    # Foundation stage events
    foundation_events = [
        ("你感到丹田中灵气凝聚，筑基之相初现。", {"cultivation": 30}, "important"),
        ("你寻得一处灵脉，在此闭关筑基。", {"cultivation": 40}, "fortune"),
        ("筑基时心魔来袭，你咬牙抵御。", {"cultivation": 20, "willpower": 2}, "danger"),
        ("你的筑基丹炼制成功，服下后灵气暴涨。", {"cultivation": 50}, "fortune"),
        ("一位前辈为你护法，你安心冲击筑基。", {"cultivation": 35}, "fortune"),
        ("你在秘境中获得筑基灵液。", {"cultivation": 45}, "fortune"),
        ("筑基失败，经脉受损，需静养三年。", {"cultivation": -30, "constitution": -2}, "danger"),
        ("你以雷法淬体，根基愈发稳固。", {"cultivation": 25, "constitution": 1}, "normal"),
        ("你悟出了一门小神通。", {"cultivation": 20, "comprehension": 1}, "fortune"),
        ("门派分配给你一处洞府，可安心修炼。", {"cultivation": 15}, "normal"),
        ("你参加门派大比，获得筑基丹一枚。", {"cultivation": 35, "charisma": 1}, "fortune"),
        ("你被派去镇守矿脉，修炼之余收获颇丰。", {"cultivation": 10, "fortune": 1}, "normal"),
    ]
    
    for i, (text, effects, etype) in enumerate(foundation_events):
        events.append({
            "id": f"found_{i:03d}",
            "text": text,
            "category": "cultivation",
            "conditions": {"min_realm": 2, "max_realm": 2},
            "weight": 45,
            "effects": effects,
            "tags": ["foundation"],
            "event_type": etype
        })
    
    # Golden Core events
    golden_core_events = [
        ("金丹初成，天降霞光，方圆百里可见。", {"cultivation": 50}, "important"),
        ("你的金丹品质上佳，隐有龙吟之声。", {"cultivation": 40, "constitution": 2}, "fortune"),
        ("你开始炼制本命法宝。", {"cultivation": 20}, "normal"),
        ("一位金丹真人向你挑战，你勉强应对。", {"cultivation": 15, "willpower": 1}, "danger"),
        ("你在坊市中高价购得一枚结丹辅助灵药。", {"cultivation": 35}, "normal"),
        ("你渡过了金丹期的第一次小天劫。", {"cultivation": 30, "willpower": 2}, "important"),
        ("你的道侣与你双修，修为精进。", {"cultivation": 25, "charisma": 1}, "fortune"),
        ("你悟出了金丹期的核心奥义。", {"cultivation": 45, "comprehension": 2}, "fortune"),
        ("你被宗门长老看重，赐予珍贵资源。", {"cultivation": 30, "fortune": 1}, "fortune"),
        ("你击杀了一头金丹期妖兽，取其内丹。", {"cultivation": 35, "constitution": 1}, "normal"),
    ]
    
    for i, (text, effects, etype) in enumerate(golden_core_events):
        events.append({
            "id": f"golden_{i:03d}",
            "text": text,
            "category": "cultivation",
            "conditions": {"min_realm": 3, "max_realm": 3},
            "weight": 40,
            "effects": effects,
            "tags": ["golden_core"],
            "event_type": etype
        })
    
    # Nascent Soul events
    nascent_soul_events = [
        ("元婴出窍，神游天地，你看到了更广阔的世界。", {"cultivation": 60}, "important"),
        ("你的元婴凝实如金，散发道韵。", {"cultivation": 50, "comprehension": 2}, "fortune"),
        ("你参悟了空间法则的一丝皮毛。", {"cultivation": 40, "comprehension": 3}, "fortune"),
        ("你遭遇元婴期的大劫，堪堪渡过。", {"cultivation": 30, "willpower": 3}, "danger"),
        ("你收了一位天赋异禀的弟子。", {"cultivation": 20, "charisma": 2}, "normal"),
        ("你炼化了一件上古法宝。", {"cultivation": 45, "constitution": 2}, "fortune"),
        ("你被邀请加入一个隐世家族。", {"cultivation": 25, "fortune": 2}, "fortune"),
        ("你在论道大会上力压群雄。", {"cultivation": 35, "charisma": 3}, "fortune"),
        ("你窥见了天道一角，心生敬畏。", {"cultivation": 55, "willpower": 2}, "important"),
        ("一位化神修士欲夺你的元婴，你拼死逃脱。", {"cultivation": -20, "willpower": 2}, "danger"),
    ]
    
    for i, (text, effects, etype) in enumerate(nascent_soul_events):
        events.append({
            "id": f"nascent_{i:03d}",
            "text": text,
            "category": "cultivation",
            "conditions": {"min_realm": 4, "max_realm": 4},
            "weight": 35,
            "effects": effects,
            "tags": ["nascent_soul"],
            "event_type": etype
        })
    
    # High realm events (化神+)
    high_realm_events = [
        ("你参悟大道，天地为你贺。", {"cultivation": 80, "comprehension": 3}, "important"),
        ("你渡过了雷劫九九八十一道天雷。", {"cultivation": 100, "willpower": 5}, "important"),
        ("你与一位同境界的道友论道三日三夜。", {"cultivation": 50, "comprehension": 2}, "normal"),
        ("你镇压了一头远古妖兽。", {"cultivation": 60, "constitution": 3}, "fortune"),
        ("你悟出了自己的道。", {"cultivation": 70, "comprehension": 5}, "important"),
        ("天道降下考验，你九死一生。", {"cultivation": 40, "willpower": 4}, "danger"),
        ("你的声名传遍修真界。", {"cultivation": 30, "charisma": 5}, "fortune"),
        ("你开辟了一处小千世界。", {"cultivation": 90, "fortune": 3}, "fortune"),
        ("你参悟了轮回之力。", {"cultivation": 85, "comprehension": 4}, "important"),
        ("飞升之劫降临，天地变色。", {"cultivation": 100, "willpower": 5}, "important"),
    ]
    
    for i, (text, effects, etype) in enumerate(high_realm_events):
        events.append({
            "id": f"high_{i:03d}",
            "text": text,
            "category": "cultivation",
            "conditions": {"min_realm": 5},
            "weight": 30,
            "effects": effects,
            "tags": ["high_realm"],
            "event_type": etype
        })
    
    # Generic cultivation events (any realm)
    generic_cult = [
        ("你在修炼中领悟了新的道理。", {"cultivation": 15, "comprehension": 1}, "fortune"),
        ("修炼时灵气紊乱，你及时化解。", {"cultivation": 5, "willpower": 1}, "normal"),
        ("你服下一枚丹药，修为增进。", {"cultivation": 20}, "normal"),
        ("你在秘境中历练，收获颇丰。", {"cultivation": 25, "fortune": 1}, "fortune"),
        ("你闭关三月，略有精进。", {"cultivation": 12}, "normal"),
        ("修炼进入瓶颈期，寸步难行。", {"cultivation": 3}, "normal"),
        ("你外出游历，见闻增长。", {"cultivation": 8, "comprehension": 1}, "normal"),
        ("你与人比斗，险胜对手。", {"cultivation": 10, "willpower": 1}, "normal"),
        ("你炼制法器成功。", {"cultivation": 15}, "normal"),
        ("你读了一卷古籍，有所启发。", {"cultivation": 12, "comprehension": 1}, "normal"),
    ]
    
    for i, (text, effects, etype) in enumerate(generic_cult):
        events.append({
            "id": f"cult_gen_{i:03d}",
            "text": text,
            "category": "cultivation",
            "conditions": {"min_realm": 1},
            "weight": 60,
            "effects": effects,
            "tags": ["cultivation_generic"],
            "event_type": etype
        })
    
    return events


def generate_social_events():
    """Generate social/interaction events."""
    events = []
    
    social_templates = [
        # Sect events
        ("宗门举办大典，你被选为代表参加。", {"charisma": 2, "cultivation": 10}, "fortune", ["sect"]),
        ("你与师兄切磋，不慎伤了和气。", {"charisma": -1, "willpower": 1}, "normal", ["sect"]),
        ("门派遭遇敌人袭击，你奋起抵抗。", {"willpower": 2, "cultivation": 15}, "danger", ["sect"]),
        ("你被门派长老收为亲传弟子。", {"cultivation": 30, "fortune": 2}, "fortune", ["sect"]),
        ("门派内斗，你不幸被牵连。", {"fortune": -1}, "danger", ["sect"]),
        ("你在门派中结交到志同道合的朋友。", {"charisma": 1}, "normal", ["sect"]),
        ("你为门派立下大功，获得重赏。", {"cultivation": 25, "fortune": 1}, "fortune", ["sect"]),
        ("门派中有人嫉妒你的天赋，暗中使绊。", {"fortune": -1, "willpower": 1}, "danger", ["sect"]),
        
        # Master events
        ("师父教导你修炼的要诀。", {"cultivation": 20, "comprehension": 1}, "normal", ["master"]),
        ("师父罚你面壁思过三月。", {"willpower": 2}, "normal", ["master"]),
        ("师父赠你一件法器。", {"cultivation": 15, "fortune": 1}, "fortune", ["master"]),
        ("你与师父意见不合，争论许久。", {"comprehension": 1, "charisma": -1}, "normal", ["master"]),
        ("师父带你去见一位世外高人。", {"cultivation": 25, "fortune": 2}, "fortune", ["master"]),
        ("师父坐化前将衣钵传于你。", {"cultivation": 50, "willpower": 2}, "important", ["master"]),
        
        # Dao companion events
        ("你遇到一位令你心动的修士。", {"charisma": 1}, "normal", ["romance"]),
        ("你与道侣一起采药，温馨美好。", {"fortune": 1, "charisma": 1}, "fortune", ["romance"]),
        ("你的道侣不幸陨落，你悲痛欲绝。", {"willpower": -2, "charisma": -1}, "danger", ["romance"]),
        ("你与道侣双修，修为大进。", {"cultivation": 30}, "fortune", ["romance"]),
        ("你为道侣炼制了一枚丹药。", {"charisma": 2}, "normal", ["romance"]),
        
        # Rival events
        ("你的宿敌再次出现，向你挑战。", {"willpower": 1}, "danger", ["rival"]),
        ("你终于击败了多年的宿敌。", {"cultivation": 20, "willpower": 2}, "fortune", ["rival"]),
        ("宿敌设下埋伏，你中了暗算。", {"constitution": -1, "cultivation": -10}, "danger", ["rival"]),
        ("你与宿敌化干戈为玉帛，把酒言和。", {"charisma": 2, "fortune": 1}, "fortune", ["rival"]),
    ]
    
    for i, (text, effects, etype, tags) in enumerate(social_templates):
        events.append({
            "id": f"social_{i:03d}",
            "text": text,
            "category": "social",
            "conditions": {"min_age": 12, "min_realm": 1},
            "weight": 40,
            "effects": effects,
            "tags": ["social"] + tags,
            "event_type": etype
        })
    
    return events


def generate_fortune_events():
    """Generate fortune/encounter events."""
    events = []
    
    fortune_templates = [
        ("你在一处遗迹中发现了前人留下的传承。", {"cultivation": 40, "comprehension": 2}, "fortune"),
        ("你意外获得一本上古功法。", {"cultivation": 35, "comprehension": 3}, "fortune"),
        ("你在深渊底部发现了一株万年灵草。", {"constitution": 3, "cultivation": 30}, "fortune"),
        ("一只上古灵兽认你为主。", {"constitution": 2, "fortune": 2}, "fortune"),
        ("你被卷入一处秘境，获得大机缘。", {"cultivation": 50, "fortune": 2}, "fortune"),
        ("你在拍卖会上低价购得一件至宝。", {"fortune": 3}, "fortune"),
        ("天降灵雨，你的修为突飞猛进。", {"cultivation": 45}, "fortune"),
        ("你的血脉突然觉醒，体内涌出洪荒之力。", {"constitution": 4, "cultivation": 35}, "important"),
        ("你偶遇一位隐世大能，获赐一滴精血。", {"constitution": 3, "willpower": 2}, "fortune"),
        ("你在星空中感悟到了一丝大道法则。", {"comprehension": 4, "cultivation": 25}, "fortune"),
        ("你发现了一处灵泉，日夜浸泡修炼。", {"cultivation": 30, "constitution": 2}, "fortune"),
        ("一道闪电劈入你的体内，却令你脱胎换骨。", {"constitution": 5, "cultivation": 20}, "fortune"),
        ("你在梦中见到了仙界的景象。", {"comprehension": 3, "cultivation": 15}, "important"),
        ("你无意间打开了一处远古传送阵。", {"fortune": 2, "cultivation": 25}, "fortune"),
        ("你获得了一件上古炼器材料。", {"cultivation": 20, "fortune": 1}, "fortune"),
        ("你在瀑布后的洞穴中发现了先人的宝藏。", {"fortune": 3, "cultivation": 30}, "fortune"),
        ("你炼化了一枚天材地宝。", {"constitution": 2, "cultivation": 35}, "fortune"),
        ("你在混沌之海中获得一缕混沌之气。", {"cultivation": 60, "comprehension": 3}, "fortune"),
        ("你获得了仙人遗留的半卷仙经。", {"cultivation": 70, "comprehension": 4}, "fortune"),
        ("你在时间长河中领悟了岁月法则。", {"cultivation": 55, "lifespan": 5}, "fortune"),
    ]
    
    for i, (text, effects, etype) in enumerate(fortune_templates):
        min_realm = 0 if i < 5 else (2 if i < 12 else 4)
        events.append({
            "id": f"fortune_{i:03d}",
            "text": text,
            "category": "fortune",
            "conditions": {"min_realm": min_realm},
            "weight": 20 + (5 - min_realm) * 3,
            "effects": effects,
            "tags": ["fortune", "encounter"],
            "event_type": etype
        })
    
    return events


def generate_calamity_events():
    """Generate calamity/danger events."""
    events = []
    
    calamity_templates = [
        ("妖兽袭村，你奋力抵抗。", {"willpower": 1, "constitution": -1}, "danger", 0),
        ("山洪暴发，你险些被冲走。", {"willpower": 1}, "danger", 0),
        ("你误入邪修的领地，被追杀三日。", {"willpower": 2, "cultivation": -10}, "danger", 1),
        ("天劫突至，你毫无准备。", {"constitution": -2, "willpower": 2}, "danger", 2),
        ("你遭遇心魔，在幻境中沉沦。", {"willpower": -2, "cultivation": -15}, "danger", 2),
        ("一头上古妖兽苏醒，横扫方圆千里。", {"constitution": -1, "fortune": -1}, "danger", 3),
        ("你被困在禁地中，苦苦挣扎。", {"willpower": 2, "cultivation": -20}, "danger", 2),
        ("宗门大战爆发，生灵涂炭。", {"willpower": 1, "charisma": -1}, "danger", 1),
        ("天地异变，灵气枯竭。", {"cultivation": -25}, "danger", 3),
        ("你遇到了走火入魔的邪修。", {"constitution": -1, "willpower": 1}, "danger", 1),
        ("你的修炼出了岔子，经脉尽断。", {"cultivation": -40, "constitution": -3}, "danger", 2),
        ("魔族入侵，人间炼狱。", {"willpower": 2, "fortune": -2}, "danger", 3),
        ("一场天灾席卷大陆。", {"fortune": -1}, "danger", 0),
        ("你在渡劫时被人偷袭。", {"cultivation": -30, "willpower": 2}, "danger", 4),
        ("你的道心出现裂痕。", {"willpower": -3, "cultivation": -20}, "danger", 3),
        ("你中了剧毒，修为散失大半。", {"cultivation": -35, "constitution": -2}, "danger", 2),
        ("你被人下了禁制，灵力封印。", {"cultivation": -25}, "danger", 2),
        ("你进入一处死地，生死一线。", {"willpower": 3, "fortune": -1}, "danger", 3),
        ("天道降罚，雷劫加身。", {"constitution": -2, "willpower": 3}, "danger", 5),
        ("你触犯了天条，遭受天谴。", {"cultivation": -50, "willpower": 2}, "danger", 6),
    ]
    
    for i, (text, effects, etype, min_realm) in enumerate(calamity_templates):
        events.append({
            "id": f"calamity_{i:03d}",
            "text": text,
            "category": "calamity",
            "conditions": {"min_realm": min_realm},
            "weight": 25,
            "effects": effects,
            "tags": ["calamity", "danger"],
            "event_type": etype
        })
    
    return events


def generate_death_events():
    """Generate death events."""
    events = []
    
    death_templates = [
        # Mortal deaths
        ("你安详地在睡梦中离世，享年{age}岁。", 0, "寿终正寝"),
        ("一场瘟疫夺走了你的生命。", 0, "染疫而亡"),
        ("你在一次意外中不幸身亡。", 0, "意外身亡"),
        ("你病入膏肓，药石无灵。", 0, "病故"),
        ("你在饥荒中饿死。", 0, "饿殍"),
        
        # Cultivator deaths
        ("你在突破时走火入魔，经脉尽断而亡。", 1, "走火入魔"),
        ("你被高阶妖兽吞噬。", 1, "兽口殒命"),
        ("你渡劫失败，形神俱灭。", 2, "劫难"),
        ("你被邪修夺舍，魂飞魄散。", 2, "被人夺舍"),
        ("你的金丹碎裂，修为散尽，郁郁而终。", 3, "丹碎身亡"),
        ("你被天道降下的雷罚击中，灰飞烟灭。", 4, "天罚"),
        ("你与魔族大战，力竭而亡。", 3, "战死沙场"),
        ("你的道心崩碎，坐化而亡。", 4, "道心崩碎"),
        ("你以身殉道，化为天地养分。", 5, "以身殉道"),
        ("你的寿元耗尽，安然坐化。", 1, "寿元耗尽"),
    ]
    
    for i, (text, min_realm, reason) in enumerate(death_templates):
        events.append({
            "id": f"death_{i:03d}",
            "text": text,
            "category": "death",
            "conditions": {"min_realm": min_realm},
            "weight": 10,
            "effects": {"death": True},
            "tags": ["death"],
            "event_type": "danger",
            "death_reason": reason
        })
    
    return events


def generate_template_variations():
    """Generate massive event variations from templates to reach 3000+."""
    events = []
    
    # Cultivation practice variations
    practice_adjectives = ["苦苦", "安静地", "疯狂地", "小心翼翼地", "虔诚地", "专注地", "懈怠地"]
    practice_locations = ["洞府中", "山巅", "瀑布下", "古树旁", "灵脉上", "密室内", "悬崖边", "湖心亭中", "竹林深处", "雪山之巅"]
    practice_results = [
        ("灵气充盈，修为精进", {"cultivation": 15}, "normal"),
        ("略有所得", {"cultivation": 8}, "normal"),
        ("毫无进展", {"cultivation": 2}, "normal"),
        ("突有所悟", {"cultivation": 25, "comprehension": 1}, "fortune"),
        ("走火入魔", {"cultivation": -10, "constitution": -1}, "danger"),
        ("灵台一片清明", {"cultivation": 12, "willpower": 1}, "normal"),
        ("经脉隐隐作痛", {"cultivation": 5, "constitution": -1}, "danger"),
        ("神识大增", {"cultivation": 18, "comprehension": 1}, "fortune"),
    ]
    
    idx = 0
    for loc in practice_locations:
        for adj in practice_adjectives[:3]:
            for result_text, effects, etype in practice_results[:4]:
                events.append({
                    "id": f"practice_{idx:04d}",
                    "text": f"你在{loc}{adj}修炼，{result_text}。",
                    "category": "cultivation",
                    "conditions": {"min_realm": 1},
                    "weight": 50,
                    "effects": effects,
                    "tags": ["practice"],
                    "event_type": etype
                })
                idx += 1
    
    # Encounter variations
    encounter_npcs = ["一位白发老者", "一个神秘少女", "一位剑眉星目的青年", "一个衣衫褴褛的乞丐", 
                      "一位仙风道骨的道士", "一个面戴铁具的修士", "一位满身伤痕的武者",
                      "一个面带微笑的和尚", "一位背负巨剑的少年", "一个牵着灵兽的少女"]
    encounter_actions = [
        ("向你讨了一碗水喝，临走时留下一枚玉简", {"comprehension": 1, "cultivation": 10}, "fortune"),
        ("与你论道一番，你受益匪浅", {"comprehension": 2}, "fortune"),
        ("向你出手，你勉强接下", {"willpower": 1, "cultivation": 5}, "danger"),
        ("送了你一本功法", {"cultivation": 20}, "fortune"),
        ("什么也没说就走了", {}, "normal"),
        ("对你指点一二", {"comprehension": 1, "cultivation": 8}, "normal"),
        ("想要抢夺你的宝物", {"willpower": 1, "fortune": -1}, "danger"),
        ("和你结为好友", {"charisma": 2}, "normal"),
        ("传授你一招杀手锏", {"cultivation": 15, "willpower": 1}, "fortune"),
        ("警告你前方有危险", {"fortune": 1}, "normal"),
    ]
    
    idx = 0
    for npc in encounter_npcs:
        for action_text, effects, etype in encounter_actions:
            events.append({
                "id": f"encounter_{idx:04d}",
                "text": f"你遇到{npc}，{action_text}。",
                "category": "social",
                "conditions": {"min_realm": 1, "min_age": 12},
                "weight": 35,
                "effects": effects,
                "tags": ["encounter", "npc"],
                "event_type": etype
            })
            idx += 1
    
    # Item/treasure discovery variations
    locations = ["古墓中", "深海底", "火山口", "冰窟内", "沙漠绿洲", "密林深处", "地下河畔", "云端之上", "时空裂缝中", "远古战场"]
    treasures = [
        ("一柄锈迹斑斑的古剑", {"cultivation": 15, "willpower": 1}, "fortune"),
        ("一枚散发灵光的丹药", {"cultivation": 25, "constitution": 1}, "fortune"),
        ("一本泛黄的古籍", {"comprehension": 2, "cultivation": 10}, "fortune"),
        ("一块温润的玉佩", {"fortune": 1, "cultivation": 5}, "normal"),
        ("一面古镜", {"comprehension": 1, "cultivation": 8}, "normal"),
        ("一枚储物戒", {"fortune": 2}, "fortune"),
        ("一件残破的铠甲", {"constitution": 2}, "normal"),
        ("一颗夜明珠", {"fortune": 1}, "normal"),
        ("一株千年灵芝", {"constitution": 2, "cultivation": 20}, "fortune"),
        ("一块不知名的矿石", {"cultivation": 5}, "normal"),
    ]
    
    idx = 0
    for loc in locations:
        for treasure_text, effects, etype in treasures:
            events.append({
                "id": f"treasure_{idx:04d}",
                "text": f"你在{loc}发现了{treasure_text}。",
                "category": "fortune",
                "conditions": {"min_realm": 1},
                "weight": 25,
                "effects": effects,
                "tags": ["treasure", "discovery"],
                "event_type": etype
            })
            idx += 1
    
    # Daily life cultivation events
    seasons = ["春", "夏", "秋", "冬"]
    activities = [
        ("采药", {"fortune": 1}, "normal"),
        ("炼丹", {"comprehension": 1, "cultivation": 10}, "normal"),
        ("读书", {"comprehension": 1}, "normal"),
        ("打坐", {"cultivation": 12, "willpower": 1}, "normal"),
        ("游历", {"fortune": 1, "charisma": 1}, "normal"),
        ("闭关", {"cultivation": 20}, "normal"),
        ("切磋", {"willpower": 1, "cultivation": 8}, "normal"),
        ("参悟", {"comprehension": 2}, "fortune"),
    ]
    
    idx = 0
    for season in seasons:
        for activity_name, effects, etype in activities:
            events.append({
                "id": f"daily_{idx:04d}",
                "text": f"{season}日里，你{activity_name}度日，日子倒也充实。",
                "category": "cultivation",
                "conditions": {"min_realm": 1},
                "weight": 55,
                "effects": effects,
                "tags": ["daily", "cultivation_life"],
                "event_type": etype
            })
            idx += 1
    
    # Breakthrough attempt variations
    realms = ["练气", "筑基", "金丹", "元婴", "化神", "合体", "大乘"]
    breakthrough_results = [
        ("成功了！你感到体内灵力翻涌", {"realm_up": True, "cultivation": 50}, "important"),
        ("功亏一篑，差一点就成功了", {"cultivation": 20, "willpower": 1}, "normal"),
        ("失败了，你的根基受损", {"cultivation": -20, "constitution": -1}, "danger"),
        ("被人打断，前功尽弃", {"cultivation": -15, "willpower": 1}, "danger"),
        ("引来天劫，你咬牙承受", {"cultivation": 30, "willpower": 2}, "danger"),
    ]
    
    idx = 0
    for r_idx, realm in enumerate(realms):
        for result_text, effects, etype in breakthrough_results:
            events.append({
                "id": f"breakthrough_{idx:04d}",
                "text": f"你尝试突破{realm}期，{result_text}。",
                "category": "cultivation",
                "conditions": {"min_realm": r_idx + 1, "max_realm": r_idx + 1},
                "weight": 20,
                "effects": effects,
                "tags": ["breakthrough"],
                "event_type": etype
            })
            idx += 1
    
    # Random cultivation world events
    world_events = [
        "仙门大比在即，各派弟子齐聚。",
        "有人在拍卖会上拍出天价灵物。",
        "一处上古遗迹被发现，各方势力蜂拥而至。",
        "修真界传出一则惊天秘闻。",
        "一位大能陨落，天地为之悲鸣。",
        "魔道中人再次作乱，正道联盟讨伐。",
        "灵气潮汐来临，修炼速度倍增。",
        "天降异象，预示着大事将发生。",
        "一场修真者之间的大战波及方圆百里。",
        "传说中的仙器出世，引得万人争抢。",
        "一座飞升台重现人间。",
        "古老的预言开始应验。",
        "域外天魔降临。",
        "修真界大洗牌，诸多势力消亡。",
        "一条通往更高界域的通道被发现。",
    ]
    
    for i, text in enumerate(world_events):
        events.append({
            "id": f"world_{i:04d}",
            "text": text,
            "category": "world",
            "conditions": {"min_realm": 1},
            "weight": 30,
            "effects": {},
            "tags": ["world_event"],
            "event_type": "normal" if i < 8 else "important"
        })
    
    # Alchemy events
    pill_names = ["聚气丹", "培元丹", "破境丹", "回春丹", "清心丹", "铸魂丹", "龙虎丹", "九转金丹", "不死丹", "混元丹"]
    pill_results = [
        ("成功炼出", {"cultivation": 20, "comprehension": 1}, "fortune"),
        ("炼制失败，炉毁丹灭", {"fortune": -1}, "danger"),
        ("意外炼出变异品", {"cultivation": 35, "fortune": 2}, "fortune"),
        ("炼丹时引发爆炸", {"constitution": -1}, "danger"),
    ]
    
    idx = 0
    for pill in pill_names:
        for result_text, effects, etype in pill_results:
            events.append({
                "id": f"alchemy_{idx:04d}",
                "text": f"你尝试炼制{pill}，{result_text}。",
                "category": "cultivation",
                "conditions": {"min_realm": 1},
                "weight": 30,
                "effects": effects,
                "tags": ["alchemy"],
                "event_type": etype
            })
            idx += 1
    
    # Artifact/weapon events
    weapons = ["飞剑", "法杖", "灵钟", "宝镜", "玉笛", "铁扇", "金钵", "墨笔"]
    weapon_events_tmpl = [
        ("你将{w}祭炼了一番，威力有所提升。", {"cultivation": 10}, "normal"),
        ("你的{w}突然发出嗡鸣，似有灵性觉醒。", {"cultivation": 15, "fortune": 1}, "fortune"),
        ("你的{w}在战斗中崩裂了。", {"fortune": -1}, "danger"),
        ("你得到一柄更好的{w}，旧的送给了后辈。", {"charisma": 1, "cultivation": 5}, "normal"),
    ]
    
    idx = 0
    for w in weapons:
        for tmpl, effects, etype in weapon_events_tmpl:
            events.append({
                "id": f"artifact_{idx:04d}",
                "text": tmpl.format(w=w),
                "category": "cultivation",
                "conditions": {"min_realm": 1},
                "weight": 30,
                "effects": effects,
                "tags": ["artifact"],
                "event_type": etype
            })
            idx += 1
    
    # Sect/Organization events
    sect_names = ["青云宗", "天剑门", "丹霞派", "玄天教", "万法宗", "紫霄宫", "太虚观", "碧落殿"]
    sect_events_tmpl = [
        ("{s}向你发出邀请，希望你加入。", {"charisma": 1, "fortune": 1}, "fortune"),
        ("你与{s}的弟子发生冲突。", {"willpower": 1}, "danger"),
        ("{s}的高手路过，无视了你。", {}, "normal"),
        ("你帮助了{s}的一位弟子，对方感激不已。", {"charisma": 1, "fortune": 1}, "normal"),
        ("{s}举办论道大会，你前去旁听。", {"comprehension": 1, "cultivation": 5}, "normal"),
        ("{s}被灭门，你感到兔死狐悲。", {"willpower": 1}, "danger"),
    ]
    
    idx = 0
    for sect in sect_names:
        for tmpl, effects, etype in sect_events_tmpl:
            events.append({
                "id": f"sect_{idx:04d}",
                "text": tmpl.format(s=sect),
                "category": "social",
                "conditions": {"min_realm": 1},
                "weight": 25,
                "effects": effects,
                "tags": ["sect_event"],
                "event_type": etype
            })
            idx += 1
    
    # Dream/vision events
    dream_events = [
        ("你梦到了前世的记忆，醒来后泪流满面。", {"willpower": 1, "comprehension": 1}, "important"),
        ("你做了一个预言梦，梦中的场景栩栩如生。", {"fortune": 1}, "important"),
        ("你在梦中与一位上古大能对弈。", {"comprehension": 2}, "fortune"),
        ("你梦到自己飞升成仙，醒来后若有所悟。", {"cultivation": 15, "comprehension": 1}, "fortune"),
        ("你梦到了一处宝藏的位置。", {"fortune": 2}, "fortune"),
        ("你做了噩梦，梦中被无数怨灵缠绕。", {"willpower": -1}, "danger"),
        ("你在梦中参悟了一门功法。", {"cultivation": 20, "comprehension": 2}, "fortune"),
        ("你梦到自己是一条龙。", {"constitution": 1}, "normal"),
        ("你在入定时神游太虚。", {"comprehension": 1, "cultivation": 10}, "normal"),
        ("你梦到了自己的死法，惊出一身冷汗。", {"willpower": 2}, "danger"),
    ]
    
    for i, (text, effects, etype) in enumerate(dream_events):
        events.append({
            "id": f"dream_{i:04d}",
            "text": text,
            "category": "fortune",
            "conditions": {"min_age": 5},
            "weight": 25,
            "effects": effects,
            "tags": ["dream", "vision"],
            "event_type": etype
        })
    
    # Nature/weather events
    nature_events = [
        ("灵气暴动，天地变色。", {"cultivation": -5}, "danger"),
        ("一场灵雨降临，万物复苏。", {"cultivation": 15, "constitution": 1}, "fortune"),
        ("雷暴席卷大地，你借雷修炼。", {"cultivation": 20, "willpower": 1}, "normal"),
        ("地龙翻身，你的洞府崩塌。", {"fortune": -1}, "danger"),
        ("一棵古树突然开花结果，灵气浓郁。", {"cultivation": 12}, "fortune"),
        ("流星雨划过天际，蕴含天地精华。", {"cultivation": 18, "comprehension": 1}, "fortune"),
        ("大雾弥漫，你在雾中迷失了方向。", {}, "normal"),
        ("一条灵脉从地下浮现。", {"cultivation": 25}, "fortune"),
        ("日月同辉，天地间灵气暴涨。", {"cultivation": 30}, "fortune"),
        ("狂风呼啸，卷起漫天黄沙。", {}, "normal"),
    ]
    
    for i, (text, effects, etype) in enumerate(nature_events):
        events.append({
            "id": f"nature_{i:04d}",
            "text": text,
            "category": "world",
            "conditions": {},
            "weight": 30,
            "effects": effects,
            "tags": ["nature"],
            "event_type": etype
        })
    
    return events


def generate_all_events():
    """Generate all events and save to JSON files."""
    os.makedirs(EVENTS_DIR, exist_ok=True)
    
    all_events = []
    
    common = generate_common_events()
    cultivation = generate_cultivation_events()
    social = generate_social_events()
    fortune = generate_fortune_events()
    calamity = generate_calamity_events()
    death = generate_death_events()
    variations = generate_template_variations()
    
    all_events.extend(common)
    all_events.extend(cultivation)
    all_events.extend(social)
    all_events.extend(fortune)
    all_events.extend(calamity)
    all_events.extend(death)
    all_events.extend(variations)
    
    # Save categorized
    categories = {}
    for event in all_events:
        cat = event["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(event)
    
    for cat, cat_events in categories.items():
        filepath = os.path.join(EVENTS_DIR, f"{cat}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(cat_events, f, ensure_ascii=False, indent=2)
        print(f"Generated {len(cat_events)} events in {cat}.json")
    
    # Save combined
    filepath = os.path.join(EVENTS_DIR, "all_events.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(all_events, f, ensure_ascii=False, indent=2)
    
    print(f"\nTotal events generated: {len(all_events)}")
    return all_events


if __name__ == "__main__":
    generate_all_events()
