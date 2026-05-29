"""
Final batch of events to reach 3000+ total.
Uses more combinatorial templates.
"""
import json
import os

EVENTS_DIR = os.path.join(os.path.dirname(__file__), "events")


def generate_final_batch():
    """Generate final batch of events."""
    events = []
    idx = 0
    
    # Realm progression flavor (per year type events)
    year_descriptors = ["平静", "动荡", "丰收", "艰难", "幸运", "平淡", "充实", "孤独"]
    year_activities = [
        ("你潜心修炼", {"cultivation": 12}, "normal"),
        ("你四处游历", {"fortune": 1, "cultivation": 5}, "normal"),
        ("你闭关苦修", {"cultivation": 18, "willpower": 1}, "normal"),
        ("你交友广阔", {"charisma": 1, "cultivation": 5}, "normal"),
        ("你研究阵法", {"comprehension": 1, "cultivation": 8}, "normal"),
        ("你钻研丹道", {"comprehension": 1, "cultivation": 10}, "normal"),
    ]
    
    for desc in year_descriptors:
        for activity, effects, etype in year_activities:
            events.append({
                "id": f"final_year_{idx:04d}",
                "text": f"{desc}的一年，{activity}。",
                "category": "cultivation",
                "conditions": {"min_realm": 1},
                "weight": 55,
                "effects": effects,
                "tags": ["yearly", "flavor"],
                "event_type": etype
            })
            idx += 1
    
    # Extended combat variations with locations
    battle_locations = [
        "荒野中", "城门前", "山谷里", "河岸边", "密林深处",
        "古墓入口", "空中", "地下", "海面上", "悬崖之巅"
    ]
    
    battle_enemies_2 = [
        "邪修", "妖兽", "鬼修", "散修", "魔族弟子",
        "上古傀儡", "化形妖精", "拦路匪徒", "暗杀者", "远古守卫"
    ]
    
    battle_outcomes = [
        ("你大获全胜", {"cultivation": 15, "willpower": 1}, "fortune"),
        ("你惨胜", {"cultivation": 8, "constitution": -1}, "normal"),
        ("你被迫撤退", {"willpower": 1}, "danger"),
        ("你与对手不分胜负", {"cultivation": 10, "willpower": 1}, "normal"),
        ("你一招制敌", {"cultivation": 12, "comprehension": 1}, "fortune"),
    ]
    
    for loc in battle_locations:
        for enemy in battle_enemies_2:
            outcome_text, effects, etype = battle_outcomes[idx % len(battle_outcomes)]
            events.append({
                "id": f"final_battle_{idx:04d}",
                "text": f"你在{loc}遭遇{enemy}，一场恶战后{outcome_text}。",
                "category": "calamity",
                "conditions": {"min_realm": 1},
                "weight": 30,
                "effects": effects,
                "tags": ["combat"],
                "event_type": etype
            })
            idx += 1
    
    # More treasure/resource discovery
    resource_locations = [
        "灵脉深处", "枯井底部", "古树树心", "山洞壁缝中", "河底淤泥里",
        "鸟巢中", "巨石之下", "云层之上", "冰川裂缝中", "沙漠绿洲下"
    ]
    
    resources = [
        ("一块灵石矿", {"fortune": 2}, "fortune"),
        ("一枚储物袋", {"fortune": 1}, "normal"),
        ("一本笔记", {"comprehension": 1}, "normal"),
        ("一枚丹药", {"cultivation": 15}, "fortune"),
        ("一件残破法器", {"cultivation": 8}, "normal"),
        ("一颗兽核", {"cultivation": 12, "constitution": 1}, "fortune"),
        ("一块令牌", {"fortune": 1}, "normal"),
        ("一封密信", {"comprehension": 1, "fortune": 1}, "normal"),
        ("一枚古钱", {"fortune": 1}, "normal"),
        ("一把钥匙", {"fortune": 2}, "fortune"),
    ]
    
    for loc in resource_locations:
        for res_name, effects, etype in resources:
            events.append({
                "id": f"final_res_{idx:04d}",
                "text": f"你在{loc}发现了{res_name}。",
                "category": "fortune",
                "conditions": {"min_realm": 1},
                "weight": 25,
                "effects": effects,
                "tags": ["resource", "discovery"],
                "event_type": etype
            })
            idx += 1
    
    # Cultivation setbacks and recovery
    setbacks = [
        ("修炼中灵气紊乱，你花了数日调息。", {"cultivation": -5, "willpower": 1}, "danger"),
        ("你的功法出现了冲突，需要重新选择方向。", {"cultivation": -10, "comprehension": 1}, "danger"),
        ("你的境界有所松动，需要巩固修为。", {"cultivation": -8}, "normal"),
        ("你发现自己的功法有隐患。", {"cultivation": -15, "comprehension": 1}, "danger"),
        ("你在突破时遭遇回溯，退回原来的境界。", {"cultivation": -20}, "danger"),
        ("你的旧伤复发，影响修炼。", {"constitution": -1, "cultivation": -5}, "danger"),
        ("你的心境出现波动。", {"willpower": -1, "cultivation": -3}, "normal"),
        ("你消耗过度，需要休养。", {"constitution": -1}, "normal"),
    ]
    
    recovery = [
        ("经过调养，你的状态恢复如初。", {"constitution": 1, "cultivation": 10}, "normal"),
        ("你从失败中汲取教训，变得更强了。", {"willpower": 2, "cultivation": 15}, "fortune"),
        ("你找到了问题所在并加以改正。", {"comprehension": 1, "cultivation": 12}, "normal"),
        ("休养生息后，你满血复活。", {"constitution": 1}, "normal"),
        ("你用时间治愈了一切。", {"cultivation": 8, "willpower": 1}, "normal"),
        ("你换了一种修炼方式，效果显著。", {"cultivation": 20, "comprehension": 1}, "fortune"),
        ("你吸取了教训，以后不会再犯同样的错误。", {"willpower": 1, "comprehension": 1}, "normal"),
        ("大病一场后体质反而增强了。", {"constitution": 2}, "fortune"),
    ]
    
    for text, effects, etype in setbacks + recovery:
        events.append({
            "id": f"final_setback_{idx:04d}",
            "text": text,
            "category": "cultivation",
            "conditions": {"min_realm": 1},
            "weight": 35,
            "effects": effects,
            "tags": ["setback" if effects.get("cultivation", 0) < 0 else "recovery"],
            "event_type": etype
        })
        idx += 1
    
    # Mysterious events (atmospheric)
    mysterious = [
        "你看到了一个不应该存在的影子。",
        "深夜里你听到了古怪的低语声。",
        "你的法器突然自己发出了光芒。",
        "你在镜中看到了另一个自己。",
        "时间似乎在这一刻静止了。",
        "你感到有什么东西在注视着你。",
        "天空中出现了一只巨大的眼睛。",
        "你收到了一封来自未来的信。",
        "你的影子突然动了一下。",
        "你在空无一人的地方听到了掌声。",
        "你做了一个关于末日的梦。",
        "你的手掌心出现了一个奇怪的纹路。",
        "你在水面上看到了另一个世界。",
        "你突然忘记了过去一天的事情。",
        "你在修炼时看到了无数平行世界。",
        "你的法宝突然消失，三日后又出现了。",
        "你遇到了一个自称来自未来的人。",
        "你在梦中死了一次，醒来后浑身冷汗。",
        "你发现自己的记忆中多了一段不属于自己的经历。",
        "天地间突然安静了一瞬，万籁俱寂。",
    ]
    
    for text in mysterious:
        events.append({
            "id": f"final_mystery_{idx:04d}",
            "text": text,
            "category": "world",
            "conditions": {"min_realm": 1},
            "weight": 20,
            "effects": {"willpower": 1},
            "tags": ["mysterious", "atmosphere"],
            "event_type": "important"
        })
        idx += 1
    
    # Sect daily life (detailed)
    sect_daily = [
        ("你参加了宗门早课，师兄弟们一起修炼。", {"cultivation": 8, "charisma": 1}, "normal"),
        ("你在藏经阁中发现了一本被遗忘的典籍。", {"comprehension": 1, "cultivation": 10}, "fortune"),
        ("你被安排去看守灵田。", {"cultivation": 5, "fortune": 1}, "normal"),
        ("你在门派任务中获得了功勋点。", {"fortune": 1}, "normal"),
        ("宗门发放月例，你领到了灵石。", {"fortune": 1}, "normal"),
        ("你在练功房中苦练法术。", {"cultivation": 12}, "normal"),
        ("你在丹房中帮忙打下手。", {"comprehension": 1}, "normal"),
        ("你参加了宗门护山大阵的维护。", {"cultivation": 8, "comprehension": 1}, "normal"),
        ("你被派去收集灵草。", {"fortune": 1, "cultivation": 5}, "normal"),
        ("你在宗门广场上观看前辈演武。", {"comprehension": 1, "willpower": 1}, "normal"),
        ("宗门举办诗会，你勉强参加。", {"charisma": 1}, "normal"),
        ("你在宗门的灵池中修炼。", {"cultivation": 15}, "fortune"),
        ("你在宗门附近的山中历练。", {"cultivation": 8, "willpower": 1}, "normal"),
        ("你偷偷去了宗门禁地边缘。", {"fortune": 1, "willpower": 1}, "danger"),
        ("宗门长老考核弟子，你表现中规中矩。", {"cultivation": 5}, "normal"),
    ]
    
    for text, effects, etype in sect_daily:
        events.append({
            "id": f"final_sect_{idx:04d}",
            "text": text,
            "category": "social",
            "conditions": {"min_realm": 1},
            "weight": 40,
            "effects": effects,
            "tags": ["sect", "daily_life"],
            "event_type": etype
        })
        idx += 1
    
    # Extended high-realm events
    high_realm_extended = [
        ("你开始尝试参悟空间法则。", {"cultivation": 30, "comprehension": 2}, "normal"),
        ("你的神识覆盖范围再次扩大。", {"cultivation": 25, "comprehension": 1}, "fortune"),
        ("你尝试凝聚法身。", {"cultivation": 40, "willpower": 2}, "important"),
        ("你在虚空中漫步，俯瞰大地。", {"cultivation": 20, "willpower": 1}, "normal"),
        ("你开始理解时间的本质。", {"cultivation": 35, "comprehension": 3}, "fortune"),
        ("你的实力已可开天辟地。", {"cultivation": 50, "constitution": 3}, "important"),
        ("你开始为飞升做准备。", {"cultivation": 45, "willpower": 2}, "important"),
        ("你的名号响彻三界。", {"charisma": 5, "cultivation": 30}, "fortune"),
        ("你制定了天规地律。", {"willpower": 3, "cultivation": 40}, "important"),
        ("天道开始注意到你。", {"cultivation": 35, "willpower": 3}, "important"),
        ("你与同境界的至强者交手。", {"cultivation": 25, "willpower": 2}, "normal"),
        ("你为天下苍生挡下一劫。", {"charisma": 3, "willpower": 3}, "important"),
        ("你在天地大劫中独善其身。", {"willpower": 4, "fortune": 2}, "fortune"),
        ("你化解了一场灭世之危。", {"charisma": 5, "willpower": 3}, "important"),
        ("你感到飞升的契机就在眼前。", {"cultivation": 60, "willpower": 3}, "important"),
    ]
    
    for text, effects, etype in high_realm_extended:
        events.append({
            "id": f"final_high_{idx:04d}",
            "text": text,
            "category": "cultivation",
            "conditions": {"min_realm": 5},
            "weight": 30,
            "effects": effects,
            "tags": ["high_realm", "endgame"],
            "event_type": etype
        })
        idx += 1
    
    # Weather + cultivation combos
    weathers = ["风", "雨", "雷", "雪", "雾", "霜", "霞", "虹"]
    weather_effects_list = [
        ("你借{w}之势修炼", {"cultivation": 14}, "normal"),
        ("{w}中蕴含灵气，你贪婪吸收", {"cultivation": 18}, "fortune"),
        ("{w}势太猛，你被迫中断修炼", {"cultivation": -3}, "normal"),
        ("你在{w}中感悟天道", {"comprehension": 1, "cultivation": 10}, "fortune"),
    ]
    
    for w in weathers:
        for tmpl, effects, etype in weather_effects_list:
            events.append({
                "id": f"final_weather_{idx:04d}",
                "text": tmpl.format(w=w) + "。",
                "category": "cultivation",
                "conditions": {"min_realm": 1},
                "weight": 40,
                "effects": effects,
                "tags": ["weather", "cultivation"],
                "event_type": etype
            })
            idx += 1
    
    # Time passage events (for older cultivators)
    time_events = [
        ("百年如一日，你的修为稳步增长。", {"cultivation": 20}, "normal"),
        ("岁月流逝，你感到自己在变强。", {"cultivation": 15, "willpower": 1}, "normal"),
        ("你在漫长的岁月中积累了丰富的经验。", {"comprehension": 1, "cultivation": 10}, "normal"),
        ("时光荏苒，你的道心越发坚定。", {"willpower": 2, "cultivation": 12}, "normal"),
        ("你用了很长时间才完善了一门功法。", {"comprehension": 2, "cultivation": 18}, "fortune"),
        ("在时间的长河中，你看到了无数兴亡。", {"willpower": 1, "comprehension": 1}, "normal"),
        ("你修炼了许久，终于有了些许进展。", {"cultivation": 10}, "normal"),
        ("光阴如梭，你又老了一些。", {"cultivation": 5}, "normal"),
        ("你在寂静中等待机缘。", {"willpower": 1}, "normal"),
        ("漫漫修仙路，你且行且珍惜。", {"cultivation": 8, "willpower": 1}, "normal"),
    ]
    
    for text, effects, etype in time_events:
        events.append({
            "id": f"final_time_{idx:04d}",
            "text": text,
            "category": "cultivation",
            "conditions": {"min_realm": 2, "min_age": 100},
            "weight": 45,
            "effects": effects,
            "tags": ["time_passage", "flavor"],
            "event_type": etype
        })
        idx += 1
    
    # Additional herb/material gathering
    herbs = [
        "九叶灵芝", "千年何首乌", "血灵藤", "冰心莲", "火凰花",
        "紫金参", "星辰草", "月华露", "龙涎果", "凤凰泪",
        "七色灵芽", "万毒之母", "天外陨铁", "地心火晶", "渊龙骨"
    ]
    
    herb_events_tmpl = [
        ("你采集到一株{h}，大喜过望。", {"fortune": 1, "cultivation": 10}, "fortune"),
        ("你发现{h}的踪迹，却被人捷足先登。", {"fortune": -1}, "danger"),
        ("你用{h}炼制了丹药。", {"cultivation": 18}, "normal"),
        ("你将{h}种在了自己的灵田中。", {"fortune": 1}, "normal"),
    ]
    
    for herb in herbs:
        for tmpl, effects, etype in herb_events_tmpl:
            events.append({
                "id": f"final_herb_{idx:04d}",
                "text": tmpl.format(h=herb),
                "category": "cultivation",
                "conditions": {"min_realm": 1},
                "weight": 25,
                "effects": effects,
                "tags": ["herb", "resource"],
                "event_type": etype
            })
            idx += 1
    
    # Reputation/fame events
    fame_events = [
        ("你的事迹被写入了修真界的史册。", {"charisma": 2}, "fortune"),
        ("有人为你写了一首诗。", {"charisma": 1}, "normal"),
        ("你的名声传到了其他大陆。", {"charisma": 2, "fortune": 1}, "fortune"),
        ("有年轻修士慕名而来拜师。", {"charisma": 1}, "normal"),
        ("你被人当做反面教材。", {"charisma": -1, "willpower": 1}, "danger"),
        ("你的传说变成了一个神话。", {"charisma": 3}, "fortune"),
        ("有人冒充你的名号行骗。", {"charisma": -1}, "danger"),
        ("你成了某个小宗门的名誉长老。", {"charisma": 2, "fortune": 1}, "fortune"),
        ("关于你的流言蜚语四起。", {"charisma": -1, "willpower": 1}, "normal"),
        ("你救了一城百姓，被尊为恩人。", {"charisma": 3, "fortune": 1}, "fortune"),
    ]
    
    for text, effects, etype in fame_events:
        events.append({
            "id": f"final_fame_{idx:04d}",
            "text": text,
            "category": "social",
            "conditions": {"min_realm": 2},
            "weight": 25,
            "effects": effects,
            "tags": ["fame", "reputation"],
            "event_type": etype
        })
        idx += 1
    
    # Additional death events (more variety)
    extra_deaths = [
        ("你在探索禁地时触发了远古禁制，当场殒命。", 2, "禁制击杀"),
        ("你被仇家暗算，毒发身亡。", 1, "中毒身亡"),
        ("你在渡劫时被天劫劈成飞灰。", 3, "天劫焚身"),
        ("你的寿元耗尽，无力回天。", 0, "油尽灯枯"),
        ("你与强敌同归于尽。", 2, "同归于尽"),
        ("你被困在时空乱流中，再也出不来。", 4, "困于时空"),
        ("你为了救人，燃烧了自己的道果。", 3, "燃道救人"),
        ("你在顿悟时被打断，心脉尽碎。", 2, "悟道失败"),
        ("你被天道抹杀。", 6, "天道抹杀"),
        ("你在封印魔物时力竭而亡。", 3, "封魔殉道"),
    ]
    
    for text, min_realm, reason in extra_deaths:
        events.append({
            "id": f"final_death_{idx:04d}",
            "text": text,
            "category": "death",
            "conditions": {"min_realm": min_realm},
            "weight": 8,
            "effects": {"death": True},
            "tags": ["death"],
            "event_type": "danger",
            "death_reason": reason
        })
        idx += 1
    
    return events


def add_final_batch():
    """Add final batch to reach 3000+ events."""
    final_events = generate_final_batch()
    
    all_events_path = os.path.join(EVENTS_DIR, "all_events.json")
    with open(all_events_path, "r", encoding="utf-8") as f:
        existing = json.load(f)
    
    existing.extend(final_events)
    
    with open(all_events_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    
    # Save by category
    categories = {}
    for event in final_events:
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
        print(f"Final batch {cat}.json: +{len(cat_events)} events")
    
    print(f"\nFinal batch added: {len(final_events)}")
    print(f"Grand total: {len(existing)}")


if __name__ == "__main__":
    add_final_batch()
