"""
Extended event generator - additional events to reach 3000+ total.
"""
import json
import os
import random

EVENTS_DIR = os.path.join(os.path.dirname(__file__), "events")


def generate_extended_cultivation():
    """Generate many more cultivation events through combinatorial templates."""
    events = []
    idx = 0
    
    # Meditation + insight combinations
    meditation_places = [
        "灵山之巅", "古寺废墟", "千年古树下", "地下暗河旁", "星辰之下",
        "血色祭坛上", "仙人遗迹中", "万丈深渊边", "龙脉交汇处", "天外陨石旁",
        "九天雷池中", "冰火两仪阵内", "太虚幻境里", "轮回井边", "混沌之地"
    ]
    
    insights = [
        ("你领悟了五行相生之道", {"cultivation": 20, "comprehension": 1}, "fortune"),
        ("你明白了阴阳调和的真谛", {"cultivation": 18, "willpower": 1}, "fortune"),
        ("你感悟到了天人合一的境界", {"cultivation": 25, "comprehension": 2}, "fortune"),
        ("你顿悟了生死轮回之理", {"cultivation": 30, "willpower": 2}, "important"),
        ("你参透了因果循环的奥义", {"cultivation": 22, "fortune": 1}, "fortune"),
        ("你的道心愈发坚定", {"cultivation": 15, "willpower": 2}, "normal"),
        ("你一无所获，但心境平和了", {"cultivation": 5, "willpower": 1}, "normal"),
        ("你险些入魔，堪堪稳住心神", {"cultivation": -5, "willpower": 1}, "danger"),
        ("你感到天地间一丝法则的痕迹", {"cultivation": 28, "comprehension": 2}, "fortune"),
        ("一道灵光在你脑海中闪过", {"cultivation": 12, "comprehension": 1}, "normal"),
    ]
    
    for place in meditation_places:
        for insight_text, effects, etype in insights:
            events.append({
                "id": f"ext_med_{idx:04d}",
                "text": f"你在{place}入定修炼，{insight_text}。",
                "category": "cultivation",
                "conditions": {"min_realm": 1},
                "weight": 40,
                "effects": effects,
                "tags": ["meditation", "insight"],
                "event_type": etype
            })
            idx += 1
    
    # Combat encounters
    enemies = [
        "一头赤焰蛟", "一只九尾妖狐", "一群山贼", "一位堕落修士",
        "一头铁背熊", "一条毒蛇精", "一只金翅大鹏", "一头穷奇",
        "一位魔道修士", "一群尸傀", "一只千年蜘蛛精", "一头饕餮",
        "一位上古僵尸", "一群血蝙蝠", "一头玄冰蟒"
    ]
    
    combat_results = [
        ("你苦战后险胜", {"cultivation": 15, "willpower": 1}, "normal"),
        ("你轻松击败了对手", {"cultivation": 10}, "normal"),
        ("你被打得狼狈逃窜", {"cultivation": -5, "constitution": -1}, "danger"),
        ("你与对手两败俱伤", {"cultivation": 5, "constitution": -1, "willpower": 1}, "danger"),
        ("你以巧计取胜", {"cultivation": 12, "comprehension": 1}, "fortune"),
        ("你获得了战利品", {"cultivation": 8, "fortune": 1}, "fortune"),
        ("你差点丢了性命", {"willpower": 2, "constitution": -1}, "danger"),
    ]
    
    for enemy in enemies:
        for result_text, effects, etype in combat_results:
            events.append({
                "id": f"ext_combat_{idx:04d}",
                "text": f"你遭遇了{enemy}，{result_text}。",
                "category": "calamity",
                "conditions": {"min_realm": 1},
                "weight": 30,
                "effects": effects,
                "tags": ["combat", "encounter"],
                "event_type": etype
            })
            idx += 1
    
    # Pill consumption events
    pills = [
        ("一枚血气丹", {"constitution": 1}, "normal"),
        ("一枚凝神丹", {"comprehension": 1}, "normal"),
        ("一枚增寿丹", {"lifespan": 2}, "fortune"),
        ("一枚破禁丹", {"cultivation": 30}, "fortune"),
        ("一枚洗髓丹", {"constitution": 2}, "fortune"),
        ("一枚回春丹", {"lifespan": 1, "constitution": 1}, "normal"),
        ("一枚聚灵丹", {"cultivation": 20}, "normal"),
        ("一枚定魂丹", {"willpower": 2}, "normal"),
        ("一枚化毒丹", {"constitution": 1}, "normal"),
        ("一枚天元丹", {"cultivation": 40, "constitution": 1}, "fortune"),
    ]
    
    pill_sources = [
        "你在市集上购得", "师父赐予你", "你自己炼制了", "你在秘境中发现",
        "一位友人赠送", "你击杀妖兽后获得", "拍卖会上竞拍到", "意外从古墓中获得"
    ]
    
    for source in pill_sources:
        for pill_name, effects, etype in pills:
            events.append({
                "id": f"ext_pill_{idx:04d}",
                "text": f"{source}{pill_name}，服下后效力显著。",
                "category": "cultivation",
                "conditions": {"min_realm": 1},
                "weight": 35,
                "effects": effects,
                "tags": ["pill", "consumable"],
                "event_type": etype
            })
            idx += 1
    
    # Technique/Skill learning
    techniques = [
        "御剑术", "火球术", "水遁术", "土盾术", "风刃术",
        "雷法", "冰封术", "分身术", "隐身术", "千里传音",
        "神行术", "金钟罩", "九转玄功", "天罗地网", "六道轮回诀",
        "破妄神通", "天火焚世", "大日如来掌", "虚空挪移", "万剑归宗"
    ]
    
    learn_results = [
        ("初窥门径", {"cultivation": 10, "comprehension": 1}, "normal"),
        ("小有所成", {"cultivation": 15}, "normal"),
        ("融会贯通", {"cultivation": 25, "comprehension": 2}, "fortune"),
        ("走火入魔", {"cultivation": -15, "willpower": -1}, "danger"),
        ("略知皮毛", {"cultivation": 5}, "normal"),
    ]
    
    for tech in techniques:
        for result_text, effects, etype in learn_results:
            events.append({
                "id": f"ext_tech_{idx:04d}",
                "text": f"你修习{tech}，{result_text}。",
                "category": "cultivation",
                "conditions": {"min_realm": 1},
                "weight": 35,
                "effects": effects,
                "tags": ["technique", "learning"],
                "event_type": etype
            })
            idx += 1
    
    return events


def generate_extended_social():
    """Generate extended social events."""
    events = []
    idx = 0
    
    # Market/Trade events
    items_for_sale = [
        "一柄品质不错的法器", "几枚中品灵石", "一本残缺的功法",
        "一株百年灵药", "一件护身玉符", "一壶灵酒",
        "一把灵茶", "一面铜镜", "一枚古玉", "一套阵旗"
    ]
    
    trade_results = [
        ("买到了好东西", {"fortune": 1}, "fortune"),
        ("被人坑了", {"fortune": -1}, "danger"),
        ("讨价还价后成交", {}, "normal"),
        ("意外发现是个宝贝", {"fortune": 2, "cultivation": 10}, "fortune"),
        ("转手卖了个好价钱", {"fortune": 1, "charisma": 1}, "fortune"),
    ]
    
    for item in items_for_sale:
        for result_text, effects, etype in trade_results:
            events.append({
                "id": f"ext_trade_{idx:04d}",
                "text": f"你在坊市中看到{item}，{result_text}。",
                "category": "social",
                "conditions": {"min_realm": 1},
                "weight": 35,
                "effects": effects,
                "tags": ["trade", "market"],
                "event_type": etype
            })
            idx += 1
    
    # Teaching/Learning events
    subjects = [
        "阵法", "炼器", "符箓", "丹道", "卜算", 
        "驯兽", "种植灵草", "布阵", "医术", "音律"
    ]
    
    for subject in subjects:
        events.append({
            "id": f"ext_learn_{idx:04d}",
            "text": f"你向前辈请教{subject}之道，受益匪浅。",
            "category": "social",
            "conditions": {"min_realm": 1},
            "weight": 30,
            "effects": {"comprehension": 1, "cultivation": 8},
            "tags": ["learning", "social"],
            "event_type": "normal"
        })
        idx += 1
        events.append({
            "id": f"ext_teach_{idx:04d}",
            "text": f"你将{subject}的心得传授给后辈，教学相长。",
            "category": "social",
            "conditions": {"min_realm": 2},
            "weight": 25,
            "effects": {"charisma": 1, "comprehension": 1},
            "tags": ["teaching", "social"],
            "event_type": "normal"
        })
        idx += 1
    
    # Faction/Politics events
    factions = [
        "正道联盟", "魔道圣教", "散修联盟", "妖族", "鬼道",
        "佛门", "儒门", "墨家", "兵家", "阴阳家"
    ]
    
    faction_events = [
        ("{f}势力扩张，对你所在地区施压。", {"willpower": 1}, "danger"),
        ("你帮助了{f}的人，获得好感。", {"charisma": 1, "fortune": 1}, "fortune"),
        ("{f}内部动荡，有人找你帮忙。", {"charisma": 1}, "normal"),
        ("你得罪了{f}的人，被追杀。", {"willpower": 1, "fortune": -1}, "danger"),
        ("{f}公开招募高手，你考虑是否加入。", {}, "normal"),
    ]
    
    for faction in factions:
        for tmpl, effects, etype in faction_events:
            events.append({
                "id": f"ext_faction_{idx:04d}",
                "text": tmpl.format(f=faction),
                "category": "social",
                "conditions": {"min_realm": 1},
                "weight": 25,
                "effects": effects,
                "tags": ["faction", "politics"],
                "event_type": etype
            })
            idx += 1
    
    # Friendship events
    friend_activities = [
        ("你与道友结伴探险，配合默契。", {"charisma": 1, "fortune": 1}, "fortune"),
        ("你与友人品茶论道，相谈甚欢。", {"comprehension": 1, "charisma": 1}, "normal"),
        ("你收到了远方友人的来信。", {"charisma": 1}, "normal"),
        ("你的好友遭遇不测，你伸出援手。", {"charisma": 2, "fortune": -1}, "normal"),
        ("你与友人一起闭关修炼，互相监督。", {"cultivation": 15, "willpower": 1}, "normal"),
        ("朋友背叛了你，你心灰意冷。", {"charisma": -2, "willpower": 1}, "danger"),
        ("你在生死关头被朋友救下。", {"fortune": 1, "charisma": 1}, "fortune"),
        ("你与友人交换了修炼心得。", {"comprehension": 1, "cultivation": 10}, "normal"),
        ("你帮朋友渡过了一次危机。", {"charisma": 2}, "normal"),
        ("你的朋友突破了，你为他高兴。", {"charisma": 1}, "normal"),
    ]
    
    for text, effects, etype in friend_activities:
        events.append({
            "id": f"ext_friend_{idx:04d}",
            "text": text,
            "category": "social",
            "conditions": {"min_realm": 1},
            "weight": 35,
            "effects": effects,
            "tags": ["friendship"],
            "event_type": etype
        })
        idx += 1
    
    return events


def generate_extended_world():
    """Generate extended world/environment events."""
    events = []
    idx = 0
    
    # Seasonal cultivation events
    seasonal = [
        ("春雷惊蛰，你借天地之力修炼。", {"cultivation": 15}, "normal"),
        ("夏日炎炎，你在火山口感悟火之大道。", {"cultivation": 18, "comprehension": 1}, "normal"),
        ("秋风萧瑟，落叶归根，你有所感悟。", {"cultivation": 12, "willpower": 1}, "normal"),
        ("冬雪纷飞，你在冰天雪地中磨炼心志。", {"willpower": 2, "cultivation": 10}, "normal"),
        ("月圆之夜，你吸收月华精气。", {"cultivation": 20}, "fortune"),
        ("日出之时，你面朝东方打坐。", {"cultivation": 12}, "normal"),
        ("暴风雨中，你感悟水之法则。", {"cultivation": 15, "comprehension": 1}, "normal"),
        ("地震之后，你感悟了大地之力。", {"constitution": 1, "cultivation": 10}, "normal"),
        ("彩虹出现，灵气格外充沛。", {"cultivation": 18}, "fortune"),
        ("极光闪耀，你心旷神怡。", {"cultivation": 15, "willpower": 1}, "fortune"),
        ("天降流火，蕴含纯阳之力。", {"cultivation": 22, "constitution": 1}, "fortune"),
        ("海啸来袭，你在风浪中领悟水遁之术。", {"cultivation": 20, "comprehension": 1}, "normal"),
        ("飓风过境，你借风势修炼。", {"cultivation": 16}, "normal"),
        ("大旱三月，你以此磨炼心性。", {"willpower": 2}, "normal"),
        ("瑞雪兆丰年，灵气复苏。", {"cultivation": 14, "fortune": 1}, "fortune"),
    ]
    
    for text, effects, etype in seasonal:
        events.append({
            "id": f"ext_season_{idx:04d}",
            "text": text,
            "category": "world",
            "conditions": {"min_realm": 1},
            "weight": 35,
            "effects": effects,
            "tags": ["seasonal", "nature"],
            "event_type": etype
        })
        idx += 1
    
    # Historical/Lore events
    lore_events = [
        ("你发现了一段上古历史的记载。", {"comprehension": 1}, "normal"),
        ("你听闻了一位上古大能的传说。", {"willpower": 1}, "normal"),
        ("你找到了一处被遗忘的古战场。", {"fortune": 1}, "normal"),
        ("你在古籍中发现了一个秘密。", {"comprehension": 1, "fortune": 1}, "fortune"),
        ("你遇到了一位记忆了千年的灵魂。", {"comprehension": 2}, "important"),
        ("你见证了一个王朝的覆灭。", {"willpower": 1}, "normal"),
        ("你发现了通往上古秘境的线索。", {"fortune": 2}, "fortune"),
        ("你在石壁上看到了远古修士留下的壁画。", {"comprehension": 1, "cultivation": 8}, "normal"),
        ("你找到了一份远古地图。", {"fortune": 1}, "normal"),
        ("你听到了来自远古的回声。", {"willpower": 1, "comprehension": 1}, "important"),
    ]
    
    for text, effects, etype in lore_events:
        events.append({
            "id": f"ext_lore_{idx:04d}",
            "text": text,
            "category": "world",
            "conditions": {"min_realm": 1},
            "weight": 25,
            "effects": effects,
            "tags": ["lore", "history"],
            "event_type": etype
        })
        idx += 1
    
    # Realm-specific flavor events (no meaningful effects, just atmosphere)
    flavor_events = [
        ("又是平静的一年，你安心修炼。", {"cultivation": 8}, "normal"),
        ("你望着天空出神，不知不觉过了一天。", {}, "normal"),
        ("你在河边钓鱼，享受难得的清闲。", {"willpower": 1}, "normal"),
        ("你整理洞府，打扫得一尘不染。", {}, "normal"),
        ("你酿了一壶灵酒，独自品尝。", {"fortune": 1}, "normal"),
        ("你在山间漫步，欣赏风景。", {"willpower": 1}, "normal"),
        ("你下山采购日常所需。", {}, "normal"),
        ("你给自己的法器做了保养。", {"cultivation": 5}, "normal"),
        ("你翻出了以前的笔记，重新温习。", {"comprehension": 1}, "normal"),
        ("你种下了一株灵草，静待开花。", {"fortune": 1}, "normal"),
        ("你观察蚁群搬家，若有所悟。", {"comprehension": 1}, "normal"),
        ("你在溪边打水，看到水中倒影的自己苍老了些。", {}, "normal"),
        ("你听到远处传来悠扬的琴声。", {"willpower": 1}, "normal"),
        ("夜深人静，你独坐洞府，思考人生。", {"willpower": 1}, "normal"),
        ("你收拾了行囊，打算出去走走。", {}, "normal"),
    ]
    
    for text, effects, etype in flavor_events:
        events.append({
            "id": f"ext_flavor_{idx:04d}",
            "text": text,
            "category": "common",
            "conditions": {"min_realm": 1},
            "weight": 60,
            "effects": effects,
            "tags": ["flavor", "daily_life"],
            "event_type": etype
        })
        idx += 1
    
    return events


def generate_extended_special():
    """Generate special conditional events (talent-specific, etc)."""
    events = []
    idx = 0
    
    # Sword cultivation events (requires sword talent)
    sword_events = [
        ("你的剑意更加凝练，仿佛能斩断虚空。", {"cultivation": 25, "willpower": 1}, "fortune"),
        ("你在剑阵中苦修，剑法大进。", {"cultivation": 20, "comprehension": 1}, "normal"),
        ("你的飞剑发出龙吟，品阶提升。", {"cultivation": 15, "fortune": 1}, "fortune"),
        ("你与一位剑修论剑三日。", {"comprehension": 2, "willpower": 1}, "fortune"),
        ("你领悟了剑道的真谛：天下万物皆为剑。", {"cultivation": 35, "comprehension": 3}, "important"),
        ("你的本命飞剑通灵了。", {"cultivation": 30, "fortune": 2}, "fortune"),
        ("一万柄飞剑向你臣服。", {"cultivation": 50, "charisma": 2}, "important"),
        ("你在悬崖上练剑，剑气纵横。", {"cultivation": 18, "willpower": 1}, "normal"),
    ]
    
    for text, effects, etype in sword_events:
        events.append({
            "id": f"ext_sword_{idx:04d}",
            "text": text,
            "category": "cultivation",
            "conditions": {"min_realm": 1, "required_talents": ["sword_bone"]},
            "weight": 40,
            "effects": effects,
            "tags": ["sword", "special"],
            "event_type": etype
        })
        idx += 1
    
    # Alchemy-specific events
    alchemy_events = [
        ("你的丹术又有精进，废丹率降低了。", {"comprehension": 1, "fortune": 1}, "normal"),
        ("你炼出了一炉极品丹药，引来天象。", {"cultivation": 30, "fortune": 2}, "fortune"),
        ("你发明了新的丹方，轰动一时。", {"charisma": 2, "comprehension": 2}, "fortune"),
        ("你的丹炉爆了，差点把洞府炸塌。", {"fortune": -1, "constitution": -1}, "danger"),
        ("你用独特的手法炼出了变异灵丹。", {"cultivation": 35, "fortune": 1}, "fortune"),
        ("有人慕名而来请你炼丹。", {"charisma": 1, "fortune": 1}, "normal"),
        ("你创造了新的丹道流派。", {"comprehension": 3, "charisma": 2}, "important"),
        ("你炼丹时悟道。", {"cultivation": 20, "comprehension": 2}, "fortune"),
    ]
    
    for text, effects, etype in alchemy_events:
        events.append({
            "id": f"ext_alch_{idx:04d}",
            "text": text,
            "category": "cultivation",
            "conditions": {"min_realm": 1, "required_talents": ["pill_talent"]},
            "weight": 40,
            "effects": effects,
            "tags": ["alchemy", "special"],
            "event_type": etype
        })
        idx += 1
    
    # Beast taming events
    beast_events = [
        ("你驯服了一只灵鹤作为坐骑。", {"fortune": 1, "charisma": 1}, "fortune"),
        ("你的灵宠进化了！", {"fortune": 2}, "fortune"),
        ("你与灵兽心意相通，配合无间。", {"willpower": 1, "fortune": 1}, "normal"),
        ("一只上古凶兽对你俯首称臣。", {"constitution": 2, "fortune": 2}, "fortune"),
        ("你的灵宠受了重伤，你为它疗伤。", {"charisma": 1}, "normal"),
        ("你在灵兽中发现了一只变异品种。", {"fortune": 2}, "fortune"),
        ("你建立了自己的灵兽园。", {"fortune": 1, "charisma": 2}, "fortune"),
        ("灵兽们自发为你护法。", {"willpower": 1, "fortune": 1}, "fortune"),
    ]
    
    for text, effects, etype in beast_events:
        events.append({
            "id": f"ext_beast_{idx:04d}",
            "text": text,
            "category": "cultivation",
            "conditions": {"min_realm": 1, "required_talents": ["beast_affinity"]},
            "weight": 40,
            "effects": effects,
            "tags": ["beast", "special"],
            "event_type": etype
        })
        idx += 1
    
    # Destiny/fortune events
    destiny_events = [
        ("你在绝境中逢生，化险为夷。", {"fortune": 1, "willpower": 1}, "fortune"),
        ("所有危机似乎都在有意避开你。", {"fortune": 1}, "fortune"),
        ("你的运气好到不可思议，连敌人都震惊了。", {"fortune": 2}, "fortune"),
        ("一件至宝从天而降，恰好落在你面前。", {"cultivation": 25, "fortune": 2}, "fortune"),
        ("气运加身，万事顺遂。", {"fortune": 2, "cultivation": 15}, "fortune"),
        ("冥冥中有一股力量在保护你。", {"willpower": 2, "fortune": 1}, "important"),
        ("天道似乎格外垂青于你。", {"cultivation": 20, "fortune": 2}, "fortune"),
        ("你无意中化解了一场大劫。", {"fortune": 2, "willpower": 1}, "fortune"),
    ]
    
    for text, effects, etype in destiny_events:
        events.append({
            "id": f"ext_destiny_{idx:04d}",
            "text": text,
            "category": "fortune",
            "conditions": {"min_realm": 0, "required_talents": ["fortune_child"]},
            "weight": 45,
            "effects": effects,
            "tags": ["destiny", "special"],
            "event_type": etype
        })
        idx += 1
    
    # Reincarnation memory events
    reincarnation_events = [
        ("你的前世记忆突然涌出一些片段。", {"comprehension": 2, "cultivation": 20}, "important"),
        ("前世的修炼经验帮你避免了走弯路。", {"cultivation": 25, "comprehension": 1}, "fortune"),
        ("你回忆起了前世的一门绝学。", {"cultivation": 35, "comprehension": 3}, "fortune"),
        ("前世的仇家似乎找到了你。", {"willpower": 2, "fortune": -1}, "danger"),
        ("你梦到了前世飞升时的场景。", {"cultivation": 30, "willpower": 2}, "important"),
        ("前世的道侣转世了，你们再次相遇。", {"charisma": 3, "fortune": 2}, "fortune"),
        ("你解封了前世留下的一件宝物。", {"cultivation": 40, "fortune": 2}, "fortune"),
        ("前世的记忆让你对生死有了更深的理解。", {"willpower": 3, "comprehension": 2}, "important"),
    ]
    
    for text, effects, etype in reincarnation_events:
        events.append({
            "id": f"ext_reincarn_{idx:04d}",
            "text": text,
            "category": "fortune",
            "conditions": {"min_realm": 0, "required_talents": ["reincarnation"]},
            "weight": 40,
            "effects": effects,
            "tags": ["reincarnation", "special"],
            "event_type": etype
        })
        idx += 1
    
    # Bloodline awakening events  
    bloodline_events = [
        ("你的血脉再次躁动，力量在增长。", {"constitution": 2, "cultivation": 15}, "fortune"),
        ("你的血脉觉醒了新的能力。", {"constitution": 3, "cultivation": 20}, "fortune"),
        ("血脉之力失控，你痛苦不堪。", {"constitution": -1, "willpower": 2}, "danger"),
        ("你变身为半妖形态，实力暴涨。", {"constitution": 4, "cultivation": 30}, "important"),
        ("远古血脉中的记忆帮你领悟了一种神通。", {"comprehension": 2, "cultivation": 25}, "fortune"),
        ("你的血脉吸引了同族的注意。", {"charisma": 1, "fortune": 1}, "normal"),
        ("血脉纯度提升，你感到力量在蜕变。", {"constitution": 3, "lifespan": 2}, "fortune"),
        ("你完全掌控了血脉之力。", {"constitution": 5, "willpower": 2}, "important"),
    ]
    
    for text, effects, etype in bloodline_events:
        events.append({
            "id": f"ext_blood_{idx:04d}",
            "text": text,
            "category": "cultivation",
            "conditions": {"min_realm": 1, "required_talents": ["ancient_bloodline"]},
            "weight": 40,
            "effects": effects,
            "tags": ["bloodline", "special"],
            "event_type": etype
        })
        idx += 1
    
    return events


def generate_extended_misc():
    """Generate miscellaneous events for variety."""
    events = []
    idx = 0
    
    # Funny/absurd events (for entertainment value)
    funny_events = [
        ("你打坐时放了个屁，差点走火入魔。", {"cultivation": 3}, "normal"),
        ("你的法宝认错了主人，追着别人跑。", {"charisma": 1}, "normal"),
        ("你炼丹时打了个喷嚏，丹炉炸了。", {"fortune": -1}, "danger"),
        ("你梦游时无意中突破了瓶颈。", {"cultivation": 20}, "fortune"),
        ("你的宠物灵兽比你先突破了。", {"willpower": 1}, "normal"),
        ("你在坊市迷路，却发现了一家隐藏的宝店。", {"fortune": 2}, "fortune"),
        ("你以为遇到了仙人，结果是个卖假药的。", {"fortune": -1}, "danger"),
        ("你答应帮人看家，结果看的是一座灵矿。", {"fortune": 2, "cultivation": 10}, "fortune"),
        ("你摘了一朵花，被花的主人追杀三天。", {"willpower": 1}, "danger"),
        ("你无意间说了一句话，被人当做了箴言流传。", {"charisma": 2}, "fortune"),
        ("你做了一个梦，梦中自己是只蝴蝶。", {"comprehension": 1}, "normal"),
        ("你在悬崖边打坐，差点被风吹下去。", {"willpower": 1}, "normal"),
        ("有人请你去降妖，结果是只猫在闹。", {}, "normal"),
        ("你试图驯服一条龙，被追了三座山。", {"willpower": 2, "constitution": -1}, "danger"),
        ("你在论道大会上睡着了，鼾声如雷。", {"charisma": -1}, "normal"),
    ]
    
    for text, effects, etype in funny_events:
        events.append({
            "id": f"ext_funny_{idx:04d}",
            "text": text,
            "category": "common",
            "conditions": {"min_realm": 1},
            "weight": 25,
            "effects": effects,
            "tags": ["funny", "flavor"],
            "event_type": etype
        })
        idx += 1
    
    # Philosophical/poetic events
    poetic_events = [
        ("花开花落，你在其中看到了轮回。", {"comprehension": 1, "willpower": 1}, "normal"),
        ("水滴石穿，你明白了坚持的意义。", {"willpower": 2}, "normal"),
        ("你在夜空中看到了自己的道。", {"comprehension": 2, "cultivation": 15}, "fortune"),
        ("你领悟到：大道至简。", {"comprehension": 2, "willpower": 1}, "fortune"),
        ("你在一片落叶中看到了天道的痕迹。", {"comprehension": 1, "cultivation": 10}, "normal"),
        ("你开始明白什么是真正的自由。", {"willpower": 2, "comprehension": 1}, "fortune"),
        ("你在孤独中找到了内心的平静。", {"willpower": 2}, "normal"),
        ("你终于理解了师父当年说的话。", {"comprehension": 2, "willpower": 1}, "fortune"),
        ("你看淡了红尘俗世，心如止水。", {"willpower": 3}, "fortune"),
        ("你在生死之间顿悟了道的真谛。", {"comprehension": 3, "cultivation": 25}, "important"),
        ("观沧海而知浩瀚，你心胸开阔了。", {"willpower": 1, "comprehension": 1}, "normal"),
        ("你在古琴声中入定，心境通明。", {"willpower": 1, "cultivation": 12}, "normal"),
        ("你看着日升日落，时光如梭。", {}, "normal"),
        ("你开始思考：何为仙？何为道？", {"comprehension": 1}, "normal"),
        ("你站在山顶俯瞰众生，心生悲悯。", {"charisma": 1, "willpower": 1}, "normal"),
    ]
    
    for text, effects, etype in poetic_events:
        events.append({
            "id": f"ext_poetic_{idx:04d}",
            "text": text,
            "category": "cultivation",
            "conditions": {"min_realm": 1},
            "weight": 30,
            "effects": effects,
            "tags": ["poetic", "philosophy"],
            "event_type": etype
        })
        idx += 1
    
    # Exploration/Adventure events
    explore_locations = [
        "一座被遗忘的古城", "一片诡异的迷雾森林", "一处地下宫殿",
        "一座浮空岛", "一片死亡沙漠", "一个次元裂缝",
        "一座冰封的古塔", "一片血色大地", "一处仙人洞府遗迹",
        "一座海底龙宫", "一片幽暗密林", "一座活火山内部"
    ]
    
    explore_results = [
        ("你满载而归。", {"fortune": 2, "cultivation": 15}, "fortune"),
        ("你空手而回，但收获了经验。", {"comprehension": 1}, "normal"),
        ("你差点回不来了。", {"willpower": 2, "constitution": -1}, "danger"),
        ("你发现了一个惊天秘密。", {"comprehension": 2, "fortune": 1}, "fortune"),
        ("你在其中修炼了很久。", {"cultivation": 25}, "normal"),
        ("你遇到了同行的修士，结伴前行。", {"charisma": 1, "fortune": 1}, "normal"),
    ]
    
    for loc in explore_locations:
        for result_text, effects, etype in explore_results:
            events.append({
                "id": f"ext_explore_{idx:04d}",
                "text": f"你探索了{loc}，{result_text}",
                "category": "fortune",
                "conditions": {"min_realm": 1},
                "weight": 25,
                "effects": effects,
                "tags": ["exploration", "adventure"],
                "event_type": etype
            })
            idx += 1
    
    # More mortal life events for non-cultivators
    mortal_extended = [
        ("你在田间发现一只受伤的鹤。", {"fortune": 1}, "normal"),
        ("你的邻居搬走了。", {}, "normal"),
        ("镇上来了一个马戏团。", {"charisma": 1}, "normal"),
        ("你学会了一首新歌。", {"charisma": 1}, "normal"),
        ("你帮助了一位迷路的老人。", {"fortune": 1, "charisma": 1}, "normal"),
        ("你在溪边发现了金沙。", {"fortune": 2}, "fortune"),
        ("你的庄稼丰收了。", {"fortune": 1}, "fortune"),
        ("你被蛇咬了一口，好在无毒。", {"willpower": 1}, "normal"),
        ("你开了一家小店。", {"fortune": 1, "charisma": 1}, "normal"),
        ("你的名声在十里八乡传开了。", {"charisma": 2}, "fortune"),
    ]
    
    for text, effects, etype in mortal_extended:
        events.append({
            "id": f"ext_mortal_{idx:04d}",
            "text": text,
            "category": "common",
            "conditions": {"max_realm": 0, "min_age": 10},
            "weight": 50,
            "effects": effects,
            "tags": ["mortal_life"],
            "event_type": etype
        })
        idx += 1
    
    return events


def extend_all_events():
    """Add extended events to existing event files."""
    extended_cult = generate_extended_cultivation()
    extended_social = generate_extended_social()
    extended_world = generate_extended_world()
    extended_special = generate_extended_special()
    extended_misc = generate_extended_misc()
    
    all_extended = extended_cult + extended_social + extended_world + extended_special + extended_misc
    
    # Load existing events
    all_events_path = os.path.join(EVENTS_DIR, "all_events.json")
    with open(all_events_path, "r", encoding="utf-8") as f:
        existing = json.load(f)
    
    # Merge
    existing.extend(all_extended)
    
    # Save combined
    with open(all_events_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    
    # Also save by category
    categories = {}
    for event in all_extended:
        cat = event["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(event)
    
    for cat, cat_events in categories.items():
        filepath = os.path.join(EVENTS_DIR, f"{cat}.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                existing_cat = json.load(f)
            existing_cat.extend(cat_events)
        else:
            existing_cat = cat_events
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(existing_cat, f, ensure_ascii=False, indent=2)
        print(f"Extended {cat}.json: +{len(cat_events)} events")
    
    print(f"\nTotal extended events added: {len(all_extended)}")
    print(f"Grand total: {len(existing)}")


if __name__ == "__main__":
    extend_all_events()
