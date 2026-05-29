"""Final push to cross 3000 events."""
import json, os

EVENTS_DIR = os.path.join(os.path.dirname(__file__), "events")

def generate_last_batch():
    events = []
    idx = 0
    
    # Gossip/rumor events
    rumors = [
        "有人说某处出现了上古仙器。", "传言某位大能即将飞升。", "据说某个秘境即将开启。",
        "有人声称发现了长生不死的方法。", "传闻魔道又有了新动作。", "听说远方爆发了一场大战。",
        "据说有人炼出了九品仙丹。", "传言某位失踪已久的前辈现身了。",
        "有人在讨论最近的天象异变。", "据说妖族和人族要议和了。",
        "传闻有人打通了通往仙界的路。", "听说某个门派被灭了满门。",
        "有人声称看到了真龙。", "传言某处灵脉即将枯竭。",
        "据说天道即将降下大劫。", "听说有人逆天改命成功了。",
    ]
    for text in rumors:
        events.append({
            "id": f"last_rumor_{idx:04d}", "text": text, "category": "world",
            "conditions": {"min_realm": 1}, "weight": 30, "effects": {},
            "tags": ["rumor", "world"], "event_type": "normal"
        })
        idx += 1
    
    # Philosophical questions during cultivation
    questions = [
        ("你在修炼中思考：何为道？", {"comprehension": 1}, "normal"),
        ("你在思考：修仙的意义是什么？", {"willpower": 1}, "normal"),
        ("你在想：实力与仁义哪个更重要？", {"willpower": 1}, "normal"),
        ("你在反思：自己走的路是否正确？", {"comprehension": 1, "willpower": 1}, "normal"),
        ("你开始怀疑自己修炼的功法。", {"comprehension": 1}, "normal"),
        ("你思考着长生与孤独的关系。", {"willpower": 2}, "important"),
        ("你在想：如果有来世，还会选择修仙吗？", {"willpower": 1}, "normal"),
        ("你思考着因果报应是否真的存在。", {"comprehension": 1}, "normal"),
    ]
    for text, effects, etype in questions:
        events.append({
            "id": f"last_phil_{idx:04d}", "text": text, "category": "cultivation",
            "conditions": {"min_realm": 1}, "weight": 35, "effects": effects,
            "tags": ["philosophy"], "event_type": etype
        })
        idx += 1
    
    # Extended terrain exploration
    terrains = [
        "一片被诅咒的森林", "一座会移动的浮岛", "一条永不结冰的河", "一座倒悬的山峰",
        "一片永夜之地", "一处灵气异常的区域", "一座水晶洞穴", "一片开满黑花的原野",
        "一处时间流速不同的空间", "一座隐藏在瀑布后的仙府",
        "一片会唱歌的竹林", "一个充满迷雾的峡谷"
    ]
    terrain_results = [
        ("你探索了一番，有所收获。", {"fortune": 1, "cultivation": 10}, "fortune"),
        ("你在此修炼了一段时间。", {"cultivation": 15}, "normal"),
        ("你什么也没发现。", {}, "normal"),
        ("你差点迷失在其中。", {"willpower": 1}, "danger"),
        ("你发现了一个秘密。", {"fortune": 2, "comprehension": 1}, "fortune"),
    ]
    for terrain in terrains:
        for result in terrain_results:
            events.append({
                "id": f"last_terrain_{idx:04d}", "text": f"你发现了{terrain}，{result[0]}",
                "category": "fortune", "conditions": {"min_realm": 1}, "weight": 22,
                "effects": result[1], "tags": ["terrain", "exploration"], "event_type": result[2]
            })
            idx += 1
    
    # Idle/Rest events
    rest_events = [
        ("你决定休息一下，调养身心。", {"willpower": 1}, "normal"),
        ("你泡了个温泉，浑身舒畅。", {"constitution": 1}, "normal"),
        ("你睡了一个好觉，精神饱满。", {"willpower": 1}, "normal"),
        ("你在花园中散步，心情舒畅。", {}, "normal"),
        ("你看了一天的云，发呆。", {}, "normal"),
        ("你下棋消磨时间。", {"comprehension": 1}, "normal"),
        ("你画了一幅画。", {"comprehension": 1}, "normal"),
        ("你写了一首诗。", {"charisma": 1}, "normal"),
        ("你整理了多年收集的灵材。", {"fortune": 1}, "normal"),
        ("你给洞府布置了新的禁制。", {"comprehension": 1, "cultivation": 5}, "normal"),
    ]
    for text, effects, etype in rest_events:
        events.append({
            "id": f"last_rest_{idx:04d}", "text": text, "category": "common",
            "conditions": {"min_realm": 1}, "weight": 45, "effects": effects,
            "tags": ["rest", "daily"], "event_type": etype
        })
        idx += 1
    
    # Animal/creature encounters
    creatures = ["灵鹿", "仙鹤", "白狐", "金鲤", "彩蝶", "玉兔", "神龟", "朱雀", "青鸾", "银狼"]
    creature_events = [
        ("{c}在你身边停留了片刻。", {"fortune": 1}, "normal"),
        ("{c}为你带来了一件礼物。", {"fortune": 2}, "fortune"),
        ("{c}和你玩耍了半天。", {"charisma": 1}, "normal"),
    ]
    for c in creatures:
        for tmpl, effects, etype in creature_events:
            events.append({
                "id": f"last_creature_{idx:04d}", "text": f"一只{tmpl.format(c=c)}",
                "category": "fortune", "conditions": {"min_realm": 1}, "weight": 20,
                "effects": effects, "tags": ["creature"], "event_type": etype
            })
            idx += 1
    
    # Book/scroll reading events
    books = [
        "《道德经》", "《周易》", "《山海经》", "《太上感应篇》", "《黄庭经》",
        "《抱朴子》", "《列子》", "《庄子》", "《清静经》", "《参同契》"
    ]
    for book in books:
        events.append({
            "id": f"last_book_{idx:04d}", "text": f"你研读{book}，若有所悟。",
            "category": "cultivation", "conditions": {"min_realm": 0}, "weight": 30,
            "effects": {"comprehension": 1, "cultivation": 8}, "tags": ["reading"],
            "event_type": "normal"
        })
        idx += 1
        events.append({
            "id": f"last_book2_{idx:04d}", "text": f"你通读{book}三遍，终有所得。",
            "category": "cultivation", "conditions": {"min_realm": 1}, "weight": 25,
            "effects": {"comprehension": 2, "cultivation": 12}, "tags": ["reading"],
            "event_type": "fortune"
        })
        idx += 1
    
    return events


def add_last():
    all_events_path = os.path.join(EVENTS_DIR, "all_events.json")
    with open(all_events_path, "r", encoding="utf-8") as f:
        existing = json.load(f)
    
    last = generate_last_batch()
    existing.extend(last)
    
    with open(all_events_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    
    categories = {}
    for event in last:
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
    
    print(f"Last batch added: {len(last)}")
    print(f"GRAND TOTAL: {len(existing)}")


if __name__ == "__main__":
    add_last()
