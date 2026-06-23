# 一叶浮尘 — 核心引擎架构

> 修仙人生模拟 · 事件驱动叙事引擎

---

## 一、双阶段事件架构

引擎采用 **"规则初筛 + LLM精选"** 的双阶段架构：

```
事件池 (9185条)
  ↓ [规则系统 — 零成本]
  9层过滤 + 权重计算 → top-10 候选事件
  ↓ [LLM Director — 单次调用]
  选1个事件 + 生成叙事(200-300字) + 可选分支
  ↓
  事件效果应用 → NPC解析 → 伏笔处理 → 返回前端
```

**模型路由策略：**
- 默认使用 **Flash** 模型（快速、低成本）
- 满足以下任一条件时升级到 **Pro** 模型：
  - 张力 ≥ 70
  - 活跃 Saga 动量 ≥ 60
  - 刚完成境界突破
  - 世界纪元刚变更

---

## 二、事件数据结构

### 2.1 GameEvent — 事件实体

```
GameEvent
├── id: str                     # 事件唯一ID
├── text: str                   # 事件骨架文本（简短）
├── expanded_text: str          # LLM扩写后的叙事文本（200-300字）
├── category: str               # 事件类别
│   # cultivation / social / fortune / calamity
│   # world / violence / death / adult / common
├── event_type: str             # 事件类型
│   # normal / important / danger / fortune / special
├── weight: int                 # 基础权重（默认50）
├── tags: list[str]             # 事件标签（分类+后果追踪+匹配用）
├── keywords: list[str]         # 预提取关键词（jieba分词，均4.9个/事件）
├── npc_roles: list[str]        # 预标注NPC角色（Layer 8快速匹配）
├── conditions: EventCondition  # 触发条件（详见2.2）
├── effects: EventEffect        # 事件效果（详见2.3）
├── branches: list[EventBranch] # 可选玩家选择分支（详见2.4）
├── creates_hook: dict          # 创建因果伏笔
├── resolves_hook: str          # 解决的伏笔ID
└── duration: int               # 事件额外消耗年数（默认0）
```

### 2.2 EventCondition — 触发条件

所有字段可选，未设置则不检查。

```
EventCondition
├── min_age / max_age: int?          # 年龄约束
├── min_realm / max_realm: int?      # 境界约束 (0凡人 ~ 5化神)
├── min_cultivation: int?            # 最小修为进度
├── required_talents: list[str]      # 必需天赋ID
├── required_tags: list[str]         # 必需状态标签
├── excluded_tags: list[str]         # 排斥状态标签
├── min_attribute: dict?             # 六维属性最小值
└── gender: str?                     # 性别约束 "male"/"female"/None
```

### 2.3 EventEffect — 事件效果

```
EventEffect
├── cultivation: int?                # 修为 ±
├── lifespan: int?                   # 寿元 ±
├── constitution: int?               # 根骨 ±
├── comprehension: int?              # 悟性 ±
├── fortune: int?                    # 福缘 ±
├── charisma: int?                   # 魅力 ±
├── willpower: int?                  # 心性 ±
├── realm_up: bool?                  # 直接突破境界
├── add_tag / add_tags               # 添加状态标签
├── remove_tag: str?                 # 移除状态标签
├── death: bool?                     # 导致死亡
└── trigger_event_id: str?           # 事件链：下一事件ID
```

### 2.4 EventBranch — 玩家选择分支

```
EventBranch
├── text: str                        # 选择文本 (≤20字)
├── effects: EventEffect             # 即时效果
├── result_text: str                 # 选择后叙事结果 (≤200字)
├── consequence_tag: str             # 长期后果标签 (影响Layer 9)
└── consequence_desc: str            # 后果描述 (创建因果伏笔)
```

---

## 三、9层事件选择管线

### 管线总览

```
事件池 (9185条)
  ↓ Layer 1: 人生阶段过滤    [硬过滤]   类别白名单 + 标签黑名单
  ↓ Layer 2: 条件过滤        [硬过滤]   年龄/境界/天赋/标签/性别/属性
  ↓ Layer 3: 去重过滤        [硬过滤]   排除 used_event_ids
  ────────── 以下为权重调整（乘性叠加）──────────
  ↓ Layer 4: 权重计算        事件类型 × 境界相关性 × 张力曲线
  ↓ Layer 5: 伏笔权重        因果链匹配事件提权
  ↓ Layer 6: 关键词加成      三维匹配（剧情线 + 命运主线关键词）
  ↓ Layer 7: 多样性衰减      近期重复类别降权
  ↓ Layer 8: NPC好感度驱动   关联NPC好感度提权
  ↓ Layer 9: 选择后果提权    玩家历史选择的 consequence_tag 匹配
  ↓
  排序取 top-10 → LLM Director 精选1个
```

---

### Layer 1: 人生阶段过滤

8个人生阶段，每阶段有 **类别白名单 + 标签黑名单**：

| 阶段 | 触发条件 | 允许类别 | 屏蔽标签(部分) |
|------|---------|---------|---------------|
| 婴幼期 | 0-3岁 | common | adult, combat, sect, romance |
| 童年期 | 4-11岁 | common, world | 同上 |
| 凡人青年 | 12-30岁, realm=0 | common, social, fortune, calamity, world, death | qi_refining, sect, breakthrough, practice |
| 凡人暮年 | 31+岁, realm=0 | common, social, world, death | +childhood, birth |
| 初入仙途 | 练气 | cultivation, social, fortune, calamity, world, death, common | birth, childhood, mortal_life, high_realm |
| 修行渐深 | 筑基/金丹 | 同上 | 同上 |
| 大能之境 | 元婴 | 同上 | birth, childhood, mortal_life |
| 顶峰之上 | 化神 | 同上 | birth, childhood, mortal_life |

**额外防护：** 修仙阶段拒绝 max_realm=0 事件；凡人阶段拒绝 min_realm>0 或 cultivation>0 事件。

### Layer 2: 条件过滤

逐项检查 EventCondition 所有字段，任一不满足则过滤。

额外：事件文本叙事年龄不得在当前年龄之前。

### Layer 3: 去重过滤

排除 `state.used_event_ids` 中的事件 ID。

### Layer 4: 权重计算

5个乘性因子叠加：

```
final_weight = base_weight
  × event_type_mod       # ① 事件类型加成
  × special_tag_floor    # ② 特殊标签地板
  × realm_relevance      # ③ 境界相关性衰减
  × adult_realm_mod      # ④ 成人内容境界倍率
  × tension_curve        # ⑤ 张力曲线影响
```

**① 事件类型加成：**

| 类型 | 公式 | 示例 |
|------|------|------|
| fortune | ×(1 + 福缘×0.05) | 福缘5 → ×1.25 |
| danger | ×max(0.5, 1 - 福缘×0.02) | 福缘5 → ×0.9 |
| important | ×1.4 | 确保进入候选池 |
| special | ×2.0 | 稀有事件大幅提权 |

**② 特殊标签地板：**
- adult + special/fortune → 权重 ≥ 20.0
- calamity/combat（非danger） → ×1.15

**③ 境界相关性衰减：**
```
target = (event.min_realm + event.max_realm) / 2
relevance = max(0.1, 1.0 - |当前境界 - target| × 0.25)
```

**④ 成人内容境界倍率：**

| 凡人 | 练气 | 筑基 | 金丹 | 元婴 | 化神 |
|-----|------|------|------|------|------|
| 0.4 | 7.0 | 3.2 | 1.6 | 0.9 | 0.5 |

**⑤ 张力曲线：**

| 张力范围 | danger/important | fortune | 意图 |
|---------|-----------------|---------|------|
| ≥70 (高) | ×0.3 | ×2.0 | 给玩家喘息 |
| 30-70 (中) | ×1.0 | ×1.0 | 正常节奏 |
| <30 (低) | ×2.0 | ×0.5 | 制造冲突 |

### Layer 5: 伏笔权重

事件 `resolves_hook` 匹配因果链时，应用对应的权重倍率乘数。

### Layer 6: 关键词加成

关键词来源：`active_arcs`（剧情线）+ `main_storyline`（命运主线，关键词×3优先级）

**三维匹配：**

| 维度 | 方法 | 说明 |
|------|------|------|
| 1 | 关键词集交集 | arc_keywords ∩ event._keywords (精确) |
| 2 | 文本子串扫描 | arc_keyword in event.text (兜底) |
| 3 | 标签关联映射 | tag_map[kw] ∩ event.tags (语义扩展) |

**权重倍率：** ≥3匹配→×5.0 | =2→×3.5 | =1→×2.5 | =0→×1.0

### Layer 7: 多样性衰减

```
衰减因子 = 0.6 ^ n
n = 同类别在最近5条事件中的出现次数
```

### Layer 8: NPC好感度驱动

三层匹配（OR）：显式NPC ID → 预标注npc_roles → 文本关键词推断

**好感度→倍率：**
```
sentiment ∈ [-100, 100]，0=中性

≥0: mult = 1.0 + (sentiment/100) × 1.5     → [1.0, 2.5]
<0:  mult = max(0.7, 1.0 + (sentiment/100) × 0.3)  → [0.7, 1.0]
```

### Layer 9: 选择后果提权

检查最近10次选择的 `consequence_tag`，匹配候选事件 tags：

| 匹配方式 | 示例 | 加分 |
|---------|------|------|
| 精确匹配 | ctag='betrayal' = tag 'betrayal' | +2.0 |
| 前缀匹配 | ctag='combat_injury' starts with 'combat' | +1.6 |
| 子串匹配 | ctag='betrayal' in 'npc_betrayal' | +1.3 |

最终倍率 = min(1.0 + boost_score, **6.0**)

---

## 四、priority_hint — LLM优先级标记

候选进入 LLM Director 时附带的星标提示：

| 标记 | 触发条件 |
|------|---------|
| ★稀有奇遇 | event_type = special |
| ★缘分奇遇 | adult + romance 标签 |
| ★红尘奇事 | adult 标签 |
| ★生死大劫 | danger + calamity/combat |
| ★修仙契机 | important + cultivation_start |
| ★命运转折 | important（一般） |
| ★天大机缘 | fortune + treasure/secret_realm/discovery |

---

## 五、GameDirector — 10阶段年度循环

```
advance_year()
├── 阶段0:  时间步长计算    凡人1年 → 化神20-50年
├── 阶段1:  人生阶段更新    根据 age + realm 重算 phase
├── 阶段2:  自然死亡检查    age ≥ max_age?
├── 阶段3:  凡人觉醒检查    realm=0 时概率觉醒
├── 阶段4:  修为增长        gain = (2+悟性+根骨×0.5)×(1+realm×0.15)×years
├── 阶段5:  突破预兆        修为 ≥ 阈值×80%
├── 阶段6:  年度事件 ◄ 核心
│   ├── 6.1 优先级事件      NPC/宗门/纪元（纯规则，无LLM）
│   ├── 6.2 事件链注入      上回合的 trigger_event_id
│   ├── 6.3 LLM Director    select_candidates(10) → direct_event()
│   ├── 6.4 后处理          效果/NPC/伏笔/因果链
│   └── 6.5 过期伏笔解决    强制解决超时因果
├── 阶段7:  境界突破        修为≥阈值 → 概率突破
├── 阶段8:  意外死亡        随机概率（福缘减免）
├── 阶段9:  渡劫飞升        化神 + cultivation≥22000
└── 阶段10: 年末清理        记忆/NPC老化/剧情/命运推进
```

---

## 六、影响事件选择的因素总览

### 来自玩家角色

| 因素 | 影响层 | 方式 |
|------|-------|------|
| 年龄 | L1, L2 | 阶段判定 + 条件过滤 |
| 境界 | L1, L2, L4 | 阶段判定 + 条件过滤 + 相关性衰减 |
| 六维属性 | L2, L4 | 属性条件 + 福缘影响danger/fortune权重 |
| 天赋 | L2 | required_talents 过滤 |
| 状态标签 | L1, L2 | 黑白名单 + 条件过滤 |
| 性别 | L2 | 性别专属事件 |
| 张力值 | L4 | 高张力缓和 / 低张力冲突 |
| 选择历史 | L9 | consequence_tag 提权 |
| 已触发事件 | L3 | 去重 |
| 近期事件 | L7 | 多样性衰减 |

### 来自NPC系统

| 因素 | 影响层 | 方式 |
|------|-------|------|
| NPC好感度 | L8 | -100~100 → ×0.7~×2.5 |
| NPC关系类型 | L8 | 文本关键词推断 |
| NPC事件驱动 | 阶段6.1 | 师父/道侣/宿敌/故人 |

### 来自叙事系统

| 因素 | 影响层 | 方式 |
|------|-------|------|
| 因果伏笔 | L5 | resolves_hook 匹配提权 |
| 剧情线关键词 | L6 | 三维匹配 ×2.5~×5.0 |
| 命运主线关键词 | L6 | 骨骼引导血肉 |
| 世界纪元 | 阶段6.1 | 纪元转换优先事件 |

### 来自事件自身

| 因素 | 影响层 | 方式 |
|------|-------|------|
| 基础权重 | L4 | 乘性计算起点 |
| 事件类型 | L4 | 不同类型不同倍率 |
| 事件类别 | L1, 配额 | 白名单 + 修炼配额保证 |
| 标签 | L1,L4,L8,L9 | 多层参与 |
| npc_roles | L8 | 快速匹配好感度 |

---

## 七、关键数值速查

| 参数 | 值 |
|------|---|
| 事件池 | 9,185条 |
| 候选数 | top-10 → LLM |
| 好感度范围 | -100 ~ 100 (0=中性) |
| 张力范围 | 0 ~ 100 |
| 张力衰减/回合 | -10.0 |
| 多样性回看 | 最近5条 |
| 多样性衰减因子 | 0.6/次 |
| 后果检查范围 | 最近10次选择 |
| 后果提权上限 | ×6.0 |
| 境界阈值 | {1:400, 2:1000, 3:2500, 4:6000, 5:22000} |
| 时间步长 | {凡人:1, 练气:1-3, 筑基:3-8, 金丹:5-15, 元婴:10-30, 化神:20-50} |
| 最大寿元 | {凡人:80, 练气:150, 筑基:300, 金丹:600, 元婴:1200, 化神:1500} |
| 工作记忆 | 5条 |
| NPC上限 | 20个 |
| NPC名字组合 | 10,360 (男5,880 + 女4,480) |
