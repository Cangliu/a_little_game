"""Push past 3000 events with more combinations."""
import json, os

EVENTS_DIR = os.path.join(os.path.dirname(__file__), "events")

def generate_mega_batch():
    events = []
    idx = 0
    
    # Extended secret realm exploration
    realms_names = ["太古秘境", "万妖林", "幽冥鬼域", "天火熔炉", "冰封王座", "时光回廊", "星辰墓地", "龙骨荒原", "仙人遗府", "魔渊深处", "紫霄天宫", "黄泉之路"]
    realm_experiences = [
        ("你在其中获得了一份传承", {"cultivation": 25, "comprehension": 1}, "fortune"),
        ("你差点被困在里面", {"willpower": 2}, "danger"),
        ("你收获了不少灵材", {"fortune": 2, "cultivation": 10}, "fortune"),
        ("你与其中的守护者战斗", {"willpower": 1, "cultivation": 12}, "normal"),
        ("你在其中悟道三日", {"comprehension": 2, "cultivation": 18}, "fortune"),
        ("你空手而归", {"cultivation": 3}, "normal"),
        ("你找到了一条密道", {"fortune": 1, "cultivation": 8}, "normal"),
        ("你遇到了其他探险者", {"charisma": 1}, "normal"),
    ]
    
    for rn in realms_names:
        for exp in realm_experiences:
            events.append({
                "id": f"mega_realm_{idx:04d}",
                "text": f"你探索{rn}，{exp[0]}。",
                "category": "fortune",
                "conditions": {"min_realm": 1},
                "weight": 22,
                "effects": exp[1],
                "tags": ["secret_realm", "exploration"],
                "event_type": exp[2]
            })
            idx += 1
    
    # Formation study events
    formations = ["聚灵阵", "护山大阵", "杀阵", "困阵", "幻阵", "传送阵", "封印阵", "天罗阵"]
    formation_results = [
        ("你成功布置完成", {"comprehension": 1, "cultivation": 10}, "fortune"),
        ("阵法反噬，你受了伤", {"constitution": -1}, "danger"),
        ("你改良了阵法，威力大增", {"comprehension": 2, "cultivation": 15}, "fortune"),
        ("你在阵法中修炼，效率翻倍", {"cultivation": 20}, "fortune"),
        ("你研究了很久没有头绪", {"cultivation": 3}, "normal"),
    ]
    
    for formation in formations:
        for result in formation_results:
            events.append({
                "id": f"mega_form_{idx:04d}",
                "text": f"你研究{formation}，{result[0]}。",
                "category": "cultivation",
                "conditions": {"min_realm": 1},
                "weight": 30,
                "effects": result[1],
                "tags": ["formation", "study"],
                "event_type": result[2]
            })
            idx += 1
    
    # Body refining events
    body_methods = ["以雷淬体", "以火锻骨", "以水洗髓", "以风炼神", "以土固基", "以金磨皮", "以木养生"]
    body_results = [
        ("你的体魄更加强韧了", {"constitution": 2, "cultivation": 10}, "fortune"),
        ("疼痛难忍，但你挺过来了", {"constitution": 1, "willpower": 2}, "normal"),
        ("你的身体产生了抗性", {"constitution": 1}, "normal"),
        ("效果甚微", {"cultivation": 3}, "normal"),
        ("你差点承受不住", {"constitution": -1, "willpower": 1}, "danger"),
    ]
    
    for method in body_methods:
        for result in body_results:
            events.append({
                "id": f"mega_body_{idx:04d}",
                "text": f"你尝试{method}，{result[0]}。",
                "category": "cultivation",
                "conditions": {"min_realm": 1},
                "weight": 30,
                "effects": result[1],
                "tags": ["body_refining"],
                "event_type": result[2]
            })
            idx += 1
    
    # Divination/prophecy events
    divinations = [
        ("你占卜吉凶，卦象显示大吉。", {"fortune": 2}, "fortune"),
        ("你占卜吉凶，卦象显示凶险。", {"willpower": 1}, "danger"),
        ("你推算天机，窥见了一丝未来。", {"comprehension": 1, "fortune": 1}, "fortune"),
        ("你推算天机，遭到天道反噬。", {"constitution": -1}, "danger"),
        ("你观星测命，发现命中有一大劫。", {"willpower": 2}, "important"),
        ("你观星测命，运势正旺。", {"fortune": 1, "cultivation": 8}, "fortune"),
        ("你求签问卦，得到一个模糊的答案。", {}, "normal"),
        ("你做了一个预知梦，但记不太清。", {"fortune": 1}, "normal"),
        ("你的直觉告诉你有好事将至。", {"fortune": 1}, "normal"),
        ("你隐隐感到不安。", {"willpower": 1}, "normal"),
    ]
    
    for text, effects, etype in divinations:
        events.append({
            "id": f"mega_div_{idx:04d}",
            "text": text,
            "category": "fortune",
            "conditions": {"min_realm": 1},
            "weight": 25,
            "effects": effects,
            "tags": ["divination"],
            "event_type": etype
        })
        idx += 1
    
    # Pet/Mount events
    pets = ["灵鹤", "白虎", "火凤", "玄龟", "青龙幼崽", "九尾狐", "麒麟", "饕餮兽", "凤凰雏", "墨龙"]
    pet_events_tmpl = [
        ("你偶遇一只{p}，它对你很亲近。", {"fortune": 2, "charisma": 1}, "fortune"),
        ("一只{p}向你发起挑战。", {"willpower": 1, "cultivation": 8}, "normal"),
        ("你在野外看到一只受伤的{p}。", {"fortune": 1, "charisma": 1}, "normal"),
    ]
    
    for pet in pets:
        for tmpl, effects, etype in pet_events_tmpl:
            events.append({
                "id": f"mega_pet_{idx:04d}",
                "text": tmpl.format(p=pet),
                "category": "fortune",
                "conditions": {"min_realm": 1},
                "weight": 20,
                "effects": effects,
                "tags": ["pet", "beast"],
                "event_type": etype
            })
            idx += 1
    
    # Music/Art cultivation
    instruments = ["古琴", "竹箫", "玉笛", "编钟", "琵琶", "古筝"]
    music_results = [
        ("琴音悠扬，你心境通明", {"willpower": 1, "cultivation": 10}, "normal"),
        ("一曲终了，百鸟来朝", {"charisma": 2, "cultivation": 8}, "fortune"),
        ("曲中蕴含大道之理", {"comprehension": 2, "cultivation": 15}, "fortune"),
        ("你弹断了弦", {}, "normal"),
    ]
    
    for inst in instruments:
        for result in music_results:
            events.append({
                "id": f"mega_music_{idx:04d}",
                "text": f"你抚{inst}一曲，{result[0]}。",
                "category": "cultivation",
                "conditions": {"min_realm": 1},
                "weight": 25,
                "effects": result[1],
                "tags": ["music", "art"],
                "event_type": result[2]
            })
            idx += 1
    
    # Cooking/food events (cultivation food)
    dishes = ["灵果羹", "龙肝凤胆汤", "聚灵茶", "仙人酒", "百花蜜", "灵兽肉", "万年雪莲粥", "星辰露"]
    food_effects = [
        ("味道极佳，精力充沛", {"constitution": 1, "cultivation": 8}, "fortune"),
        ("难以下咽，但效果不错", {"cultivation": 12}, "normal"),
        ("你吃了之后灵力暴涨", {"cultivation": 20, "constitution": 1}, "fortune"),
        ("吃坏了肚子", {"constitution": -1}, "danger"),
    ]
    
    for dish in dishes:
        for result in food_effects:
            events.append({
                "id": f"mega_food_{idx:04d}",
                "text": f"你品尝了{dish}，{result[0]}。",
                "category": "common",
                "conditions": {"min_realm": 1},
                "weight": 30,
                "effects": result[1],
                "tags": ["food", "daily"],
                "event_type": result[2]
            })
            idx += 1
    
    # Teaching/Disciple events
    disciple_events = [
        ("你收了一个资质普通的弟子。", {"charisma": 1}, "normal"),
        ("你的弟子突破了，你感到欣慰。", {"charisma": 1, "fortune": 1}, "fortune"),
        ("你的弟子叛出门墙，你痛心疾首。", {"charisma": -1, "willpower": 1}, "danger"),
        ("你的弟子在大比中获胜，为你争光。", {"charisma": 2}, "fortune"),
        ("你为弟子解惑，自己也有了新的理解。", {"comprehension": 1, "cultivation": 5}, "normal"),
        ("你的弟子送了你一件礼物。", {"fortune": 1, "charisma": 1}, "normal"),
        ("你的弟子受了伤，你为其疗伤。", {"charisma": 1}, "normal"),
        ("你的弟子青出于蓝，修为超过了你。", {"willpower": 1, "charisma": 1}, "normal"),
    ]
    
    for text, effects, etype in disciple_events:
        events.append({
            "id": f"mega_disciple_{idx:04d}",
            "text": text,
            "category": "social",
            "conditions": {"min_realm": 3},
            "weight": 25,
            "effects": effects,
            "tags": ["disciple", "teaching"],
            "event_type": etype
        })
        idx += 1
    
    # Charm/romance events
    romance_events = [
        ("你遇到了一位令你心动的修士，但缘分未到。", {"charisma": 1}, "normal"),
        ("你和道侣在月下散步，温馨美好。", {"charisma": 1, "willpower": 1}, "fortune"),
        ("你为心上人摘了一朵绝世灵花。", {"charisma": 2}, "fortune"),
        ("有人向你表白，你婉拒了。", {"charisma": 1, "willpower": 1}, "normal"),
        ("你和道侣吵架了，闷闷不乐。", {"willpower": -1}, "normal"),
        ("你和道侣一起历练，感情更深了。", {"charisma": 1, "fortune": 1}, "fortune"),
        ("你暗恋的人结了道侣，你黯然神伤。", {"willpower": 1}, "normal"),
        ("你收到一封情书，字迹秀丽。", {"charisma": 1}, "normal"),
    ]
    
    for text, effects, etype in romance_events:
        events.append({
            "id": f"mega_romance_{idx:04d}",
            "text": text,
            "category": "social",
            "conditions": {"min_realm": 0, "min_age": 15},
            "weight": 25,
            "effects": effects,
            "tags": ["romance"],
            "event_type": etype
        })
        idx += 1
    
    # Crafting events
    crafts = ["法器", "灵符", "阵盘", "灵墨", "法衣", "灵甲", "飞舟"]
    craft_results = [
        ("精心打造，品质上佳", {"cultivation": 12, "fortune": 1}, "fortune"),
        ("勉强成功", {"cultivation": 5}, "normal"),
        ("失败了，材料浪费", {"fortune": -1}, "danger"),
        ("意外做出精品", {"cultivation": 18, "fortune": 2}, "fortune"),
    ]
    
    for craft in crafts:
        for result in craft_results:
            events.append({
                "id": f"mega_craft_{idx:04d}",
                "text": f"你尝试炼制{craft}，{result[0]}。",
                "category": "cultivation",
                "conditions": {"min_realm": 1},
                "weight": 28,
                "effects": result[1],
                "tags": ["crafting"],
                "event_type": result[2]
            })
            idx += 1
    
    # Spiritual garden events
    plants = ["灵参", "血灵芝", "紫金莲", "九转花", "凤尾竹", "龙血树", "星辰藤", "月华草", "太阳花", "虚空兰"]
    plant_events = [
        ("成功培育", {"fortune": 1, "cultivation": 5}, "fortune"),
        ("枯萎了", {"fortune": -1}, "danger"),
        ("开花结果", {"fortune": 2, "cultivation": 12}, "fortune"),
        ("被灵兽偷吃了", {}, "normal"),
    ]
    
    for plant in plants:
        for result in plant_events:
            events.append({
                "id": f"mega_plant_{idx:04d}",
                "text": f"你种植的{plant}{result[0]}。",
                "category": "cultivation",
                "conditions": {"min_realm": 1},
                "weight": 25,
                "effects": result[1],
                "tags": ["garden", "planting"],
                "event_type": result[2]
            })
            idx += 1
    
    return events


def add_mega_batch():
    all_events_path = os.path.join(EVENTS_DIR, "all_events.json")
    with open(all_events_path, "r", encoding="utf-8") as f:
        existing = json.load(f)
    
    mega = generate_mega_batch()
    existing.extend(mega)
    
    with open(all_events_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    
    categories = {}
    for event in mega:
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
    
    print(f"Mega batch added: {len(mega)}")
    print(f"Grand total: {len(existing)}")


if __name__ == "__main__":
    add_mega_batch()
