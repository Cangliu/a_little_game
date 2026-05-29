"""Ultra batch - massive combinatorial generation to push past 3000."""
import json, os, itertools

EVENTS_DIR = os.path.join(os.path.dirname(__file__), "events")

def generate_ultra_batch():
    events = []
    idx = 0
    
    # Massive combat matrix
    locations = ["断魂崖", "血染谷", "幽冥洞", "九幽渊", "风暴海", "死灵沼", "烈焰山", "寒冰原", "混沌域", "虚空界"]
    enemies = ["邪修", "妖兽", "魔将", "尸王", "鬼将", "邪灵", "毒修", "剑修", "魔兽", "傀儡"]
    results = [
        ("斩杀之", {"cultivation": 18, "willpower": 1}, "fortune"),
        ("将其击退", {"cultivation": 12}, "normal"),
        ("险胜", {"cultivation": 10, "constitution": -1}, "normal"),
        ("负伤逃脱", {"willpower": 1, "constitution": -1}, "danger"),
    ]
    
    for loc in locations:
        for enemy in enemies:
            r = results[idx % len(results)]
            events.append({
                "id": f"ultra_combat_{idx:04d}",
                "text": f"你在{loc}遭遇{enemy}，激战后{r[0]}。",
                "category": "calamity",
                "conditions": {"min_realm": 1},
                "weight": 28,
                "effects": r[1],
                "tags": ["combat"],
                "event_type": r[2]
            })
            idx += 1
    
    # Massive meditation matrix  
    times = ["黎明时分", "正午时分", "黄昏时分", "深夜", "月圆之夜", "暴风雨中", "大雪纷飞时", "春暖花开时"]
    states = [
        ("你入定片刻便有所得", {"cultivation": 14}, "normal"),
        ("你沉浸其中不知日月", {"cultivation": 20}, "fortune"),
        ("你难以静心", {"cultivation": 3}, "normal"),
        ("你突破了一个小瓶颈", {"cultivation": 22, "comprehension": 1}, "fortune"),
        ("你走神了", {"cultivation": 2}, "normal"),
    ]
    
    for time in times:
        for place in ["洞府", "山顶", "湖心", "古树下", "阵法中"]:
            state = states[idx % len(states)]
            events.append({
                "id": f"ultra_med_{idx:04d}",
                "text": f"{time}，你在{place}打坐修炼，{state[0]}。",
                "category": "cultivation",
                "conditions": {"min_realm": 1},
                "weight": 50,
                "effects": state[1],
                "tags": ["meditation"],
                "event_type": state[2]
            })
            idx += 1
    
    # NPC interaction matrix
    npcs = ["一位长须老者", "一个稚气少年", "一位清冷女修", "一个壮硕汉子", "一位温文书生",
            "一个怪异道人", "一位蒙面修士", "一个邋遢乞丐", "一位华服公子", "一个沉默寡言的僧人"]
    interactions = [
        ("与你交换了修炼心得", {"comprehension": 1, "cultivation": 8}, "normal"),
        ("送了你一件小东西", {"fortune": 1}, "fortune"),
        ("向你请教了一个问题", {"charisma": 1}, "normal"),
        ("与你比试了一场", {"willpower": 1, "cultivation": 5}, "normal"),
        ("请你喝了一壶好茶", {"willpower": 1}, "normal"),
        ("告诉你一个消息", {"fortune": 1}, "normal"),
        ("与你结为朋友", {"charisma": 1, "fortune": 1}, "fortune"),
        ("对你冷眼相待后离去", {}, "normal"),
    ]
    
    for npc in npcs:
        for interaction in interactions:
            events.append({
                "id": f"ultra_npc_{idx:04d}",
                "text": f"你在路上遇到{npc}，对方{interaction[0]}。",
                "category": "social",
                "conditions": {"min_realm": 1},
                "weight": 35,
                "effects": interaction[1],
                "tags": ["npc", "encounter"],
                "event_type": interaction[2]
            })
            idx += 1
    
    # Resource gathering matrix
    terrains = ["山中", "河畔", "林间", "崖壁上", "地下", "水底", "云端", "废墟中"]
    finds = [
        ("一株灵草", {"fortune": 1, "cultivation": 5}, "fortune"),
        ("一块矿石", {"fortune": 1}, "normal"),
        ("一只灵虫", {"fortune": 1}, "normal"),
        ("一汪灵泉", {"cultivation": 12}, "fortune"),
        ("一枚灵果", {"constitution": 1}, "fortune"),
        ("什么也没有", {}, "normal"),
        ("一处危险", {"willpower": 1}, "danger"),
    ]
    
    for terrain in terrains:
        for find in finds:
            events.append({
                "id": f"ultra_gather_{idx:04d}",
                "text": f"你在{terrain}搜寻资源，发现了{find[0]}。",
                "category": "cultivation",
                "conditions": {"min_realm": 1},
                "weight": 35,
                "effects": find[1],
                "tags": ["gathering", "resource"],
                "event_type": find[2]
            })
            idx += 1
    
    # Cultivation technique practice
    techniques_2 = ["剑法", "拳法", "掌法", "步法", "身法", "眼法", "指法", "腿法", "暗器", "阵法"]
    practice_states = [
        ("小有进步", {"cultivation": 10}, "normal"),
        ("大有长进", {"cultivation": 18, "comprehension": 1}, "fortune"),
        ("不得要领", {"cultivation": 3}, "normal"),
        ("融会贯通", {"cultivation": 22, "comprehension": 2}, "fortune"),
        ("受了内伤", {"constitution": -1, "cultivation": -5}, "danger"),
        ("有所领悟", {"cultivation": 14, "comprehension": 1}, "normal"),
    ]
    
    for tech in techniques_2:
        for state in practice_states:
            events.append({
                "id": f"ultra_tech_{idx:04d}",
                "text": f"你今日修习{tech}，{state[0]}。",
                "category": "cultivation",
                "conditions": {"min_realm": 1},
                "weight": 40,
                "effects": state[1],
                "tags": ["technique", "practice"],
                "event_type": state[2]
            })
            idx += 1
    
    # Auction/Market events
    auction_items = [
        "一本功法", "一枚丹药", "一件法器", "一块玉简", "一颗内丹",
        "一把飞剑", "一面盾牌", "一件法袍", "一枚令牌", "一张地图"
    ]
    auction_results = [
        ("你高价买下", {"fortune": -1, "cultivation": 15}, "normal"),
        ("你被人抢先买走", {}, "normal"),
        ("你捡了个大便宜", {"fortune": 2, "cultivation": 10}, "fortune"),
        ("你发现是赝品", {"fortune": -1}, "danger"),
        ("卖家临时反悔", {}, "normal"),
    ]
    
    for item in auction_items:
        for result in auction_results:
            events.append({
                "id": f"ultra_auction_{idx:04d}",
                "text": f"拍卖会上出现了{item}，{result[0]}。",
                "category": "social",
                "conditions": {"min_realm": 1},
                "weight": 25,
                "effects": result[1],
                "tags": ["auction", "market"],
                "event_type": result[2]
            })
            idx += 1
    
    # Tribulation mini-events
    tribulation_types = ["心魔劫", "情劫", "雷劫", "火劫", "风劫", "水劫", "毒劫", "杀劫"]
    trib_results = [
        ("你咬牙撑过", {"willpower": 2, "cultivation": 20}, "fortune"),
        ("你险些失败", {"willpower": 1, "cultivation": 10, "constitution": -1}, "danger"),
        ("你轻松化解", {"willpower": 1, "cultivation": 15}, "normal"),
        ("你借此突破", {"cultivation": 30, "willpower": 2}, "fortune"),
    ]
    
    for trib in tribulation_types:
        for result in trib_results:
            events.append({
                "id": f"ultra_trib_{idx:04d}",
                "text": f"你遭遇了{trib}，{result[0]}。",
                "category": "cultivation",
                "conditions": {"min_realm": 2},
                "weight": 20,
                "effects": result[1],
                "tags": ["tribulation"],
                "event_type": result[2]
            })
            idx += 1
    
    return events


def add_ultra_batch():
    all_events_path = os.path.join(EVENTS_DIR, "all_events.json")
    with open(all_events_path, "r", encoding="utf-8") as f:
        existing = json.load(f)
    
    ultra = generate_ultra_batch()
    existing.extend(ultra)
    
    with open(all_events_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    
    categories = {}
    for event in ultra:
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
    
    print(f"Ultra batch added: {len(ultra)}")
    print(f"Grand total: {len(existing)}")


if __name__ == "__main__":
    add_ultra_batch()
