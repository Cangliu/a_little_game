# 觅长生 — 游戏架构全景图

> 修仙人生重开模拟器 · 骨骼血肉叙事引擎

---

## 一、系统总览

```mermaid
graph TB
    subgraph Frontend["前端 (React + TypeScript)"]
        StartScreen["StartScreen\n开始页面"]
        CharCreate["CharacterCreation\n角色创建"]
        GameScreen["GameScreen\n游戏主屏"]
        Summary["SummaryScreen\n结局总结"]
        API["api.ts\nHTTP 客户端"]
    end

    subgraph Backend["后端 (FastAPI + Python)"]
        Router["router.py\n3个API端点"]
        Director["GameDirector\n引擎总控"]

        subgraph Core["核心引擎"]
            EventSys["EventSystem\n事件选择管线"]
            RealmSys["RealmSystem\n境界突破系统"]
            DeathSys["DeathSystem\n死亡判定系统"]
            PhaseMgr["LifePhaseManager\n人生阶段管理"]
        end

        subgraph Narrative["叙事层"]
            MainStory["MainStorylinePlanner\n命运主线(骨骼)"]
            ArcPlanner["StoryArcPlanner\n剧情线规划"]
            PlotHooks["PlotHookManager\n因果伏笔"]
            NarrProv["NarrativeProvider\n叙事扩写"]
        end

        subgraph Social["社交层"]
            NPCMgr["NPCManager\nNPC管理"]
            NPCResolver["EventNPCResolver\nNPC槽位解析"]
            NPCTemplates["NPC模板\n姓名/性格/背景"]
        end

        subgraph Intelligence["AI & 记忆"]
            LLM["LLMClient\nDeepSeek接口"]
            Prompt["PromptBuilder\n提示词构建"]
            MemMgr["MemoryManager\n三层记忆"]
            Compress["MemoryCompressor\n记忆压缩"]
            BM25["BM25Retriever\n关键词检索"]
        end

        subgraph Data["数据层"]
            Models["models.py\nGameState/Realm/Attributes"]
            Config["config.py\n配置常量"]
            State["state.py\n状态管理"]
            Talents["talents.py\n天赋系统"]
            Endings["endings.py\n结局系统"]
            Events["all_events.json\n9185条事件"]
        end
    end

    StartScreen --> API
    CharCreate --> API
    GameScreen --> API
    Summary --> API
    API --> Router
    Router --> Director
    Director --> Core
    Director --> Narrative
    Director --> Social
    Director --> Intelligence
    Core --> Data
    Narrative --> Intelligence
    Social --> Data
```

---

## 二、数据模型层

### 2.1 GameState — 游戏状态全量字段

```
GameState
├── 基础标识
│   ├── game_id: str              # 8位UUID
│   ├── age: int                  # 当前年龄
│   ├── gender: str               # "male" | "female"
│   └── mortal_max_age: int       # 凡人基础寿命 (50-80随机)
│
├── 修仙属性
│   ├── realm: int                # 当前境界 (0-5 Realm枚举)
│   ├── cultivation: int          # 当前修为进度
│   ├── attributes: Attributes    # 六维属性
│   ├── talents: list[str]        # 已选天赋ID列表
│   └── tags: list[str]           # 状态标签列表
│
├── 进程控制
│   ├── events_log: list[dict]            # 完整事件历史
│   ├── used_event_ids: list[str]         # 已触发事件ID (防重复)
│   ├── is_dead: bool                     # 死亡标志
│   ├── death_reason: str                 # 死亡原因
│   ├── is_ascended: bool                 # 飞升标志
│   ├── tribulation_attempted: bool       # 是否已尝试渡劫
│   ├── space_node_found: bool            # 是否已寻得空间节点
│   ├── life_phase: int                   # 人生阶段 (0-7)
│   └── breakthrough_failures: dict       # {realm_int: 失败次数}
│
├── NPC系统
│   ├── npc_registry: dict                # {npc_id: NPC实体dict}
│   └── relationships: list[dict]         # 玩家与NPC的关系列表
│
├── 记忆系统
│   ├── memory_working: list[dict]        # 工作记忆 (最近5条)
│   ├── memory_short_term: list[dict]     # 短期记忆 (近50年)
│   ├── memory_long_term: list[dict]      # 长期记忆 (压缩)
│   └── biography_summary: str            # 压缩传记
│
├── 因果链
│   ├── plot_hooks: list[dict]            # 未解决的伏笔
│   └── resolved_hooks: list[dict]        # 已解决的伏笔
│
├── 剧情线
│   └── active_arcs: list[dict]           # 活跃剧情线
│
└── 命运主线
    └── main_storyline: dict              # 命运骨架
```

### 2.2 Realm 境界枚举

| 值 | 枚举名 | 中文 | 最大寿元 | 修为阈值 | 突破概率 | 时间步长 |
|---|--------|------|---------|---------|---------|---------|
| 0 | MORTAL | 凡人 | 50-80+寿元×3 | — | — | 1年/回合 |
| 1 | QI_REFINING | 练气 | 150年 | 400 | 15% | 1-3年/回合 |
| 2 | FOUNDATION | 筑基 | 300年 | 1000 | 14% | 3-8年/回合 |
| 3 | GOLDEN_CORE | 金丹 | 600年 | 2500 | 14% | 5-15年/回合 |
| 4 | NASCENT_SOUL | 元婴 | 1200年 | 6000 | 13% | 10-30年/回合 |
| 5 | DEITY | 化神 | 1500年 | 22000(空间节点) | — | 20-50年/回合 |

### 2.3 Attributes 六维属性

| 属性 | 字段名 | 默认值 | 随机范围 | 作用 |
|------|--------|--------|---------|------|
| 寿元 | lifespan | 3 | 2-6 | 凡人+寿元×3年；修仙者×(1+0.05×寿元) |
| 根骨 | constitution | 3 | 2-6 | 修为增益基数，渡劫成功率+0.04 |
| 悟性 | comprehension | 3 | 2-6 | 修为增益基数，觉醒概率+0.005，突破+0.008 |
| 福缘 | fortune | 3 | 2-6 | 死亡减免，fortune型事件加权，突破+0.005 |
| 魅力 | charisma | 3 | 2-6 | 社交影响 |
| 心性 | willpower | 3 | 2-6 | 渡劫成功率+0.05 |

### 2.4 GameEvent 事件数据结构

```
GameEvent
├── id: str                    # 事件唯一ID
├── text: str                  # 事件骨架文本
├── expanded_text: str         # LLM扩写后的叙事文本
├── category: str              # cultivation/social/fortune/calamity/world/violence/death/adult/common
├── event_type: str            # normal/important/danger/fortune
├── weight: int                # 基础权重 (默认50)
├── tags: list[str]            # 事件标签
├── keywords: list[str]        # 预提取关键词 (jieba分词)
├── conditions: EventCondition # 触发条件
│   ├── min_age / max_age
│   ├── min_realm / max_realm
│   ├── min_cultivation
│   ├── required_talents
│   ├── required_tags / excluded_tags
│   ├── gender
│   └── min_attribute
├── effects: EventEffect       # 事件效果
│   ├── cultivation: int
│   ├── lifespan/constitution/comprehension/fortune/charisma/willpower: int
│   ├── add_tag / add_tags / remove_tag
│   └── realm_up: bool
├── branches: list             # 事件分支 (可选)
├── creates_hook: dict         # 创建伏笔
└── resolves_hook: str         # 解决伏笔ID
```

---

## 三、GameDirector — 10阶段年度循环

```mermaid
graph TD
    Start["advance_year() 开始"] --> S0

    S0["阶段0: 时间步长计算\nTIME_STEP_BY_REALM\n凡人1年 → 化神20-50年"]
    S0 --> S1

    S1["阶段1: 人生阶段更新\nLifePhaseManager.update_phase()\n根据age+realm重算phase"]
    S1 --> S2

    S2{"阶段2: 自然死亡检查\nage >= max_age ?"}
    S2 -->|"化神未渡劫"| Trapped["困死人间\nis_dead=True"]
    S2 -->|"其他境界"| NaturalDeath["寿元耗尽死亡"]
    S2 -->|"未超龄"| S3

    S3{"阶段3: 凡人觉醒检查\nrealm==0 ?"}
    S3 -->|"概率觉醒"| Awaken["灵根觉醒\nrealm → 1"]
    S3 -->|"未觉醒/已修仙"| S4

    S4["阶段4: 修为增长\nprocess_cultivation()\ngain = (2+悟性+根骨×0.5)×(1+realm×0.15)×years"]
    S4 --> S5

    S5{"阶段5: 突破预兆\n修为 ≥ 阈值×80% ?"}
    S5 -->|"是"| Foreshadow["生成突破预兆事件"]
    S5 -->|"否"| S6
    Foreshadow --> S6

    S6["阶段6: 年度事件\n(最复杂阶段)"]
    S6 --> S7

    S7{"阶段7: 境界突破\n修为 ≥ 阈值 ?"}
    S7 -->|"成功"| BT_OK["realm+1, cultivation=0\n触发剧情线规划+命运初始化"]
    S7 -->|"失败"| BT_FAIL["cultivation = 阈值×60%\n失败次数+1"]
    S7 -->|"未达阈值"| S8
    BT_OK --> S8
    BT_FAIL --> S8

    S8{"阶段8: 意外死亡\n随机概率检查"}
    S8 -->|"死亡"| AccDeath["意外身亡"]
    S8 -->|"存活"| S9

    S9{"阶段9: 渡劫飞升\nrealm==5 && cultivation≥22000"}
    S9 -->|"寻得节点+渡劫成功"| Ascend["飞升成仙\nis_ascended=True"]
    S9 -->|"渡劫失败"| TribFail["渡劫陨落\nis_dead=True"]
    S9 -->|"未达条件"| S10

    S10["阶段10: 年末清理\n_post_year_update()\n记忆记录→NPC老化→剧情推进→命运推进"]
    S10 --> End["返回 NextYearResponse"]
```

### 阶段6详细子流程 — 年度事件选择与处理

```mermaid
graph TD
    E6["阶段6入口"] --> E6a
    E6a["6a. 获取伏笔权重调整\nPlotHookManager.get_weight_adjustments()"]
    E6a --> E6b
    E6b["6b. 获取剧情线关键词\n从active_arcs中提取"]
    E6b --> E6c
    E6c["6c. 获取命运关键词\n从当前未完成Beat提取 (×3优先级)"]
    E6c --> E6d
    E6d["6d. 事件选择管线\n6层过滤 (详见第四节)"]
    E6d --> E6e
    E6e["6e. 事件效果应用\napply_effects()"]
    E6e --> E6f
    E6f["6f. NPC槽位解析\nEventNPCResolver.resolve_event()"]
    E6f --> E6g
    E6g["6g. 叙事扩写\nNarrativeProvider.get_event_narrative()"]
    E6g --> E6h
    E6h["6h. 伏笔处理\nPlotHookManager.process_event()"]
    E6h --> E6i
    E6i["6i. NPC关系更新\nupdate_relationship()"]
    E6i --> E6j
    E6j["6j. NPC驱动事件\n师父教导/道侣互动/宿敌挑战"]
    E6j --> E6k
    E6k["6k. 过期伏笔强制解决\ngenerate_forced_resolution()"]
    E6k --> E6out["阶段6结束"]
```

---

## 四、事件选择管线 — 6层过滤

```mermaid
graph LR
    Pool["事件池\n9185条事件"] --> L1
    L1["Layer 1\n人生阶段过滤\n类别白名单+标签黑名单"] --> L2
    L2["Layer 2\n条件过滤\n年龄/境界/标签/性别/属性"] --> L3
    L3["Layer 3\n去重过滤\n排除used_event_ids"] --> L4
    L4["Layer 4\n权重计算\n基础权重×事件类型×境界相关性"] --> L5
    L5["Layer 5\n伏笔权重\n过期×10 / 临近×5 / 一般×3"] --> L6
    L6["Layer 6\n关键词加成\n三维匹配: 词集交集+文本扫描+标签映射"] --> Quota
    Quota["类别配额\n保证≥1个修炼事件"] --> Result["加权随机选取"]
```

### Layer 6 三维关键词匹配详解

| 维度 | 方法 | 说明 |
|------|------|------|
| 维度1 | 关键词集交集 | `arc_keywords ∩ event._keywords` (精确匹配) |
| 维度2 | 文本子串扫描 | `arc_keyword in event.text` (广义兜底) |
| 维度3 | 标签关联映射 | `tag_map[kw] ∩ event.tags` (语义扩展) |

**权重倍率:** 匹配≥3个→×5.0，=2个→×3.5，=1个→×2.5

### Layer 4 权重计算公式

```
final_weight = base_weight
             × event_type_mod        # fortune: ×(1+福缘×0.05), danger: ×max(0.5, 1-福缘×0.02)
             × realm_relevance       # max(0.1, 1.0 - |realm - target_realm| × 0.25)
             × adult_realm_mod       # 仅adult标签: {0:0.4, 1:7.0, 2:3.2, 3:1.6, 4:0.9, 5:0.5}
```

---

## 五、境界系统

### 5.1 修为增长

```
每年修为增益 = int((2 + 悟性 + 根骨×0.5) × (1 + 境界×0.15) × 时间步长年数)
```

### 5.2 凡人觉醒概率

| 年龄段 | 基础概率 | 属性加成 |
|--------|---------|---------|
| 1-10岁 | 1% | +悟性×0.5% + 福缘×0.3% |
| 11-15岁 | 10% | 同上 |
| 16-20岁 | 20% | 同上 |
| 21-30岁 | 15% | 同上 |
| 31岁+ | 5% | 同上 |

### 5.3 境界突破

```
成功率 = min(35%, BREAKTHROUGH_BASE_CHANCE[realm] + 悟性×0.008 + 福缘×0.005)

成功: realm += 1, cultivation = 0
失败: cultivation = threshold × 60%, breakthrough_failures[realm] += 1
失败≥3次: 特殊叙事文本
```

### 5.4 渡劫飞升 (化神 realm=5)

```
空间节点发现概率 = min(6%, 1.5% + 福缘×0.3% + 悟性×0.2%)
飞升成功率 = min(92%, 30% + 心性×5% + 根骨×4% + 福缘×3% + 悟性×2%)
```

---

## 六、死亡系统

### 6.1 自然死亡 — 寿元计算

```
凡人最大寿元 = mortal_max_age + 寿元×3
修仙者最大寿元 = REALM_MAX_AGE[realm] × (1 + 寿元×0.05)
```

### 6.2 意外死亡

```
凡人分阶段:
  0-5岁: 保护 (0%)
  6-12岁: 0.2%
  13-20岁: 0.3%
  21-35岁: 0.5%
  36-50岁: 1%
  51岁+: 2% + (age-50)/20 × 1% (递增)

修仙者: 0.0005 × (age/max_age)³ × 5

福缘减免: death_chance × max(0.1, 1 - 福缘×0.03)
```

---

## 七、人生阶段系统

```mermaid
graph LR
    I["INFANCY\n婴幼期\n0-3岁"] --> C["CHILDHOOD\n童年期\n4-11岁"]
    C --> MY["MORTAL_YOUTH\n凡人青年\n12-30岁"]
    MY --> MO["MORTAL_OLD\n凡人暮年\n31+岁"]
    C -->|"觉醒"| EC["EARLY_CULTIVATOR\n初入仙途\n练气"]
    MY -->|"觉醒"| EC
    EC --> MC["MID_CULTIVATOR\n修行渐深\n筑基/金丹"]
    MC --> HC["HIGH_CULTIVATOR\n大能之境\n元婴"]
    HC --> PC["PEAK_CULTIVATOR\n顶峰之上\n化神"]
```

| 阶段 | 允许的事件类别 | 屏蔽标签 | 叙事基调 |
|------|---------------|---------|---------|
| 婴幼期 | common | mortal_life, aging, adult, sect, romance, combat... | 懵懂天真，尚在襁褓 |
| 童年期 | common, world | 同上 | 童年记忆，朦胧初现 |
| 凡人青年 | common, social, fortune, calamity, world, death | qi_refining, sect, breakthrough, practice... | 红尘烟火，凡人悲欢 |
| 凡人暮年 | common, social, world, death | 同上 + childhood, birth | 夕阳余晖，人事已非 |
| 初入仙途 | cultivation, social, fortune, calamity, world, death, common | birth, childhood, mortal_life, high_realm | 仙路初启，意气风发 |
| 修行渐深 | 同上 | 同上 | 道途渐深，历劫成长 |
| 大能之境 | 同上 | birth, childhood, mortal_life | 俯瞰天下，纵横无敌 |
| 顶峰之上 | 同上 | birth, childhood, mortal_life | 天地之巅，求索飞升 |

---

## 八、叙事系统 — 骨骼血肉架构

### 8.1 命运主线 (骨骼) — MainStorylinePlanner

```mermaid
graph TD
    BT["首次境界突破"] --> Gen["生成命运主线\n(LLM优先 / 原型模板回退)"]
    Gen --> Arch["5种命运原型"]
    Arch --> B0["Beat 0: 灵根觉醒\ntarget_realm=1"]
    B0 --> B1["Beat 1: 初修\ntarget_realm=1"]
    B1 --> B2["Beat 2: 筑基\ntarget_realm=2"]
    B2 --> B3["Beat 3: 金丹/劫难\ntarget_realm=3"]
    B3 --> B4["Beat 4: 元婴\ntarget_realm=4"]
    B4 --> B5["Beat 5: 飞升\ntarget_realm=5"]

    Event["每年事件"] -->|"关键词匹配≥2"| Advance["推进命运节拍"]
    Event -->|"重大事件"| Pivot["血肉反哺\n改写未来节拍"]
```

**DestinyBeat 数据结构:**
```
DestinyBeat
├── description: str         # 节拍描述
├── target_realm: int        # 预期触发境界 (0-5)
├── keywords: list[str]      # 匹配关键词 (来自KEYWORD_PALETTE)
├── is_completed: bool
├── completion_age: int
├── completion_summary: str
├── is_modified: bool        # 是否被血肉反哺改写
└── original_description: str
```

**MainStoryline 数据结构:**
```
MainStoryline
├── storyline_id: str
├── archetype: str           # 天命修仙/红尘历劫/逆天改命/剑道孤峰/问道长生
├── archetype_description: str
├── destiny_beats: list[DestinyBeat]  # 6个命运节拍
├── current_beat_index: int
├── momentum: int            # 命运契合度 (0-100)
├── pivots: list[dict]       # 血肉反哺记录
├── created_at_age: int
└── is_completed: bool
```

**KEYWORD_PALETTE (关键词调色板):**
```
修行: 修炼、闭关、突破、感悟、入定、炼化、功法、心法、领悟
感悟: 顿悟、悟道、参悟、天道、道心、真谛、本源、法则
战斗: 击败、遭遇、围攻、追杀、切磋、比试、偷袭、重伤
社交: 拜师、传承、宗门、同门、弟子、道侣、师父、散修
机缘: 秘境、遗迹、宝物、丹药、灵石、法宝、灵泉、传承
劫难: 走火入魔、心魔、天劫、陨落、背叛、生死、情劫
境界: 觉醒、灵根、筑基、金丹、元婴、化神、渡劫、飞升
天地: 灵气、天地、法则、封印、禁制、阵法、神通、仙术
生物: 灵兽、妖兽、灵草、灵芝、灵丹
```

**血肉反哺触发词:** 陨落、走火入魔、大机缘、背叛、永别、决裂

### 8.2 剧情线 (血肉) — StoryArcPlanner

```
StoryArc
├── arc_id: str
├── theme: str               # "师徒情仇" / "道侣生死" / "问道之路"
├── npc_id / npc_name: str   # 关联NPC
├── phase: str               # setup → rising → climax → resolution
├── planned_beats: list[str] # 3-5个叙事节拍
├── current_beat_index: int
├── created_at_realm: int
└── is_completed: bool
```

**境界对应预设剧情线:**

| 境界 | 剧情线1 | 剧情线2 |
|------|--------|--------|
| 练气 | 初入仙途 | 师徒之谊 (绑定师父NPC) |
| 筑基 | 根基之路 | 同门情谊 (绑定同门NPC) |
| 金丹 | 问道金丹 | 宿敌恩怨 (绑定宿敌NPC) |
| 元婴 | 元婴蜕变 | 道侣之缘 (绑定道侣NPC) |
| 化神 | 天道之问 | 故人因果 (绑定最佳故人NPC) |

### 8.3 因果伏笔 — PlotHookManager

```
PlotHook
├── hook_id: str             # 如 "avenge_master"
├── description: str         # 伏笔描述
├── created_age: int
├── npc_id / npc_name: str   # 关联NPC
├── resolution_tags: list    # 可解决伏笔的事件标签
├── max_wait_years: int      # 最大等待年限 (默认100年)
├── is_resolved: bool
└── resolved_age: int
```

**权重调整策略:**
- 过期伏笔 (years_elapsed ≥ max_wait): ×10
- 临近过期 (剩余<20年): ×5
- 一般伏笔: ×3

---

## 九、NPC系统

### 9.1 NPC实体

```
NPC
├── npc_id: str
├── name: str                # 修仙风格姓名
├── gender: str
├── realm: int               # NPC境界 (±1于玩家)
├── personality: str         # 温和/冷漠/狡诈/正直/神秘/暴烈
├── role_tags: list[str]     # sword_master/alchemy_elder/sect_leader/wanderer/merchant/mysterious_elder
├── first_met_age: int
├── last_seen_age: int
├── appearance_count: int
├── is_alive: bool
├── backstory: str
└── max_age: int             # NPC寿元
```

### 9.2 Relationship 关系模型

```
Relationship
├── npc_id: str
├── relation_type: str       # 师父/同门/宿敌/道侣/挚友/泛泛之交
├── sentiment: int           # 好感度 (0-100, 50=中立)
├── last_interaction_age: int
├── interaction_count: int
├── key_memory: str          # 最重要的交互摘要
├── interactions: list       # 完整交互历史
└── unresolved_hooks: list   # 与该NPC相关的未解决伏笔
```

### 9.3 NPC驱动事件

```mermaid
graph LR
    NPCCheck["check_npc_events()"] --> Master{"有师父NPC?\n间隔5-10年"}
    NPCCheck --> Lover{"有道侣NPC?\n间隔3-5年"}
    NPCCheck --> Rival{"有宿敌NPC?\n间隔10-20年"}
    NPCCheck --> Reunion{"高好感NPC?\n30年未见面"}
    Master --> MasterEv["师父教导事件"]
    Lover --> LoverEv["道侣互动事件"]
    Rival --> RivalEv["宿敌挑战事件"]
    Reunion --> ReunionEv["故人重逢事件"]
```

### 9.4 NPC姓名生成

- **复姓池:** 慕容、司马、上官、欧阳、长孙、独孤、公孙、端木、轩辕、南宫、百里、东方、诸葛、令狐、宇文、尉迟
- **男名池:** 逸、玄、辰、渊、墨、无极、长青、九霄、天行、云深...
- **女名池:** 如烟、若兰、紫萱、清雪、月华、灵犀、婉清、素心...

### 9.5 性格行为模板

| 性格 | 言谈 | 行为 | 冲突 |
|------|------|------|------|
| 温和 | 语气平和，常以微笑示人 | 乐于助人 | 调和矛盾 |
| 冷漠 | 言简意赅，不喜寒暄 | 独来独往 | 冷眼旁观 |
| 狡诈 | 话中有话 | 表面热情实则盘算 | 借刀杀人 |
| 正直 | 直言不讳，嫉恶如仇 | 路见不平拔刀相助 | 堂堂正正 |
| 神秘 | 常用隐喻 | 行踪不定 | 来去无踪 |
| 暴烈 | 大嗓门，喜怒形于色 | 雷厉风行 | 先打后问 |

---

## 十、三层记忆系统

```mermaid
graph TD
    Event["新事件发生"] --> WM["Working Memory\n工作记忆\n容量: 5条\n完整文本"]
    WM -->|"超出5条"| STM["Short-term Memory\n短期记忆\n范围: 近50年\n摘要形式 (1-2句)"]
    STM -->|"每30年压缩"| LTM["Long-term Memory\n长期记忆\n永久保存\n严重压缩"]

    LTM --> BM25_R["BM25 Retriever\n关键词检索"]
    BM25_R --> AI_CTX["AI上下文构建"]
    WM --> AI_CTX
    STM --> AI_CTX

    Compress["MemoryCompressor"] --> Rule["规则压缩\n关键事件保留\n普通事件每3条留1条"]
    Compress --> LLM_C["LLM压缩\n批量10条→3-5句摘要"]
```

**不可遗忘事件判定:**
- event_type 为 `important` 或 `danger`
- 文本包含: 突破、飞升、觉醒、灵根、渡劫、拜师、传承、道侣、结仇、走火入魔、陨落、大机缘、生死...
- 标签包含: `npc_interaction`, `breakthrough`, `death`, `awakening`

---

## 十一、AI系统

### 11.1 LLMClient

```
模型: deepseek-v4-0324 (Flash版本)
超时: 8秒硬限制
API密钥: DEEPSEEK_API_KEY 环境变量
不可用时: 自动降级为规则文本
```

### 11.2 PromptBuilder — 5种提示词模板

| 模板 | 用途 | 输出限制 |
|------|------|---------|
| NARRATIVE_SYSTEM | 事件叙事生成 | ≤200字 |
| CONTEXTUAL_NARRATIVE_SYSTEM | 上下文感知叙事扩写 | 200-300字 |
| COMPRESSION_SYSTEM | 记忆压缩 | ≤150字 |
| NPC_INTERACTION_SYSTEM | NPC互动描写 | ≤100字 |
| MAIN_STORYLINE_SYSTEM | 命运主线生成 | ≤1000字符 JSON |

### 11.3 硬约束 (所有提示词共享)

```
- 不得描写超越当前境界的神通
- 不得自行决定死亡、突破、飞升
- 不得创造事件骨架中未提及的重大转折
- 性别一致性
- 与NPC历史交互保持一致
```

---

## 十二、前端架构

```mermaid
graph TB
    App["App.tsx\n状态机: start→playing→summary"] --> Start["StartScreen\n开始页面\n封面+开始按钮"]
    App --> Create["CharacterCreation\n角色创建\n20点属性分配+3天赋"]
    App --> Game["GameScreen\n游戏主屏\n打字机效果+自动播放"]
    App --> Sum["SummaryScreen\n结局总结\n称号+评分+大事记"]

    Game --> TW["TypewriterEvent\n逐字显示叙事文本\n35ms/字"]
    Game --> AgeCalc["extractEventAge()\n中文数字年龄解析"]
    Game --> AutoPlay["autoPlay模式\n有叙事:1800ms间隔\n无叙事:400ms间隔"]

    API_TS["api.ts"] --> StartAPI["POST /api/game/start"]
    API_TS --> NextAPI["POST /api/game/next-year"]
    API_TS --> SumAPI["GET /api/game/summary/{id}"]
```

### 12.1 API端点

| 端点 | 方法 | 请求 | 响应 |
|------|------|------|------|
| `/api/game/start` | POST | 无 | game_id, age, realm, realm_name, gender |
| `/api/game/next-year` | POST | {game_id} | NextYearResponse (age, realm, events, is_dead, is_ascended...) |
| `/api/game/summary/{id}` | GET | — | LifeSummary (total_age, max_realm, death_reason, key_events, score...) |

---

## 十三、天赋系统

**4个稀有度，共37个天赋:**

| 稀有度 | 数量 | 权重 | 代表天赋 |
|--------|------|------|---------|
| Legendary (4) | 5 | ×1 | 混沌体、先天道体、仙灵根、命星护体、转世大能 |
| Epic (3) | 11 | ×2 | 火灵根、水灵根、剑骨、丹道奇才、天命之子、金刚心... |
| Rare (2) | 12 | ×3 | 灵根、天生神力、过目不忘、长寿相、命硬... |
| Common (1) | 10 | ×4 | 体健、勤奋、善良、好奇心、谨慎、勇敢... |

**选取规则:** 随机生成10个天赋供选择，保证至少1个Epic+级别天赋，玩家选3个。

---

## 十四、结局系统

### 14.1 结局类型与评分

| 结局 | 基础分 |
|------|--------|
| 飞升成仙 | 999 |
| 渡劫陨落 | 600 |
| 困死人间 | 500 |
| 凡人死亡 | 按境界称号 |

### 14.2 最终评分公式

```
总分 = 基础分 + sum(六维属性) × 2 + min(age ÷ 10, 50)
```

---

## 十五、关键词提取 (jieba分词)

```
自定义词典: 120+ 修仙领域术语 (freq=10000强制分词)
停用词表: 86个 (代词/功能词/双字虚词)
提取流程: jieba.lcut() → 过滤单字 → 过滤非汉字 → 过滤停用词 → 2字词优先 → 最多12个
事件池: 9185条事件, 平均4.9个关键词/事件
```

---

## 十六、配置常量速查

| 常量 | 值 |
|------|---|
| REALM_THRESHOLDS | {1:400, 2:1000, 3:2500, 4:6000, 5:22000} |
| BREAKTHROUGH_BASE_CHANCE | {1:0.15, 2:0.14, 3:0.14, 4:0.13} |
| SPACE_NODE_BASE_CHANCE | 0.015 (1.5%) |
| FORESHADOW_THRESHOLD | 0.80 (80%) |
| TIME_STEP_BY_REALM | {0:(1,1), 1:(1,3), 2:(3,8), 3:(5,15), 4:(10,30), 5:(20,50)} |
| REALM_MAX_AGE | {凡人:80, 练气:150, 筑基:300, 金丹:600, 元婴:1200, 化神:1500} |
| WORKING_MEMORY_SIZE | 5条 |
| SHORT_TERM_MAX_AGE | 50年 |
| COMPRESSION_INTERVAL | 30年 |
| MAX_NPCS | 20 |

---

## 十七、项目文件结构

```
a_little_game/
├── backend/
│   ├── app/
│   │   ├── engine/                    # 核心引擎
│   │   │   ├── __init__.py
│   │   │   ├── director.py            # GameDirector (10阶段循环)
│   │   │   ├── event_system.py        # 事件选择管线 (6层过滤)
│   │   │   ├── realm_system.py        # 境界突破/觉醒/渡劫
│   │   │   ├── death_system.py        # 自然死亡/意外死亡
│   │   │   ├── life_phase.py          # 8个人生阶段
│   │   │   ├── main_storyline.py      # 命运主线 (骨骼)
│   │   │   ├── story_arc.py           # 剧情线规划 (血肉)
│   │   │   ├── plot_hooks.py          # 因果伏笔系统
│   │   │   ├── narrative.py           # 叙事扩写
│   │   │   ├── event_npc_resolver.py  # NPC槽位解析
│   │   │   ├── config.py              # 配置常量
│   │   │   ├── state.py               # 状态管理
│   │   │   ├── ai/                    # AI子系统
│   │   │   │   ├── llm_client.py      # DeepSeek客户端
│   │   │   │   ├── prompt_builder.py  # 提示词构建
│   │   │   │   └── prompt_templates.py # 提示词模板
│   │   │   ├── npc/                   # NPC子系统
│   │   │   │   ├── models.py          # NPC/Relationship模型
│   │   │   │   ├── npc_manager.py     # NPC生命周期管理
│   │   │   │   └── npc_templates.py   # 姓名/性格/背景模板
│   │   │   └── memory/               # 记忆子系统
│   │   │       ├── memory_manager.py  # 三层记忆管理
│   │   │       ├── compressor.py      # 记忆压缩器
│   │   │       └── retriever.py       # BM25检索器
│   │   ├── events/                    # 事件数据
│   │   │   ├── all_events.json        # 9185条事件 (含预提取关键词)
│   │   │   └── *.json                 # 分类事件文件
│   │   ├── main.py                    # FastAPI入口
│   │   ├── router.py                  # API路由
│   │   ├── models.py                  # 数据模型
│   │   ├── talents.py                 # 天赋系统 (37个)
│   │   └── endings.py                 # 结局系统
│   ├── .env                           # 环境变量 (API密钥)
│   └── requirements.txt               # 依赖 (FastAPI, jieba, openai...)
├── frontend/
│   ├── src/
│   │   ├── pages/                     # 页面组件
│   │   │   ├── StartScreen.tsx        # 开始页
│   │   │   ├── CharacterCreation.tsx  # 角色创建
│   │   │   ├── GameScreen.tsx         # 游戏主屏
│   │   │   └── SummaryScreen.tsx      # 结局总结
│   │   ├── utils/
│   │   │   ├── api.ts                 # HTTP客户端
│   │   │   └── types.ts              # TypeScript类型
│   │   ├── App.tsx                    # 主应用组件
│   │   ├── App.css / index.css        # 样式
│   │   └── main.tsx                   # 入口
│   └── package.json
├── Dockerfile.backend / Dockerfile.frontend
└── docker-compose.yml
```

---

## 十八、技术栈

| 层 | 技术 | 版本 |
|----|------|------|
| 后端框架 | FastAPI | — |
| 数据验证 | Pydantic | — |
| 中文分词 | jieba | ≥0.42 |
| LLM接口 | OpenAI SDK (DeepSeek) | — |
| 前端框架 | React + TypeScript | — |
| 构建工具 | Vite | — |
| 样式 | Tailwind CSS | — |
| 容器化 | Docker + docker-compose | — |

---

> 代码行数统计: Python 11,581行 / TypeScript 1,251行 / CSS 599行 / HTML 19行 = **13,472行代码**
> 数据行数: all_events.json 243,870行 + 其他JSON 66,043行 = **309,913行数据**
