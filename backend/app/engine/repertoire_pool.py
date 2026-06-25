"""Repertoire Pool — static name pools for cultivation combat assets.

Provides pre-built names for 6 categories of combat-related items:
- 功法 (Techniques): sword arts, body cultivation, elemental arts
- 法宝 (Treasures): weapons, armor, utility artifacts
- 秘术 (Secret Arts): forbidden techniques, divination, curses
- 傀儡 (Puppets): mechanical golems, combat automatons
- 灵兽 (Spirit Beasts): contracted beasts, mounts
- 天地精华 (Elements): bonded natural forces (fire, lightning, etc.)

Each pool is organized by realm tier (low/mid/high).
The system randomly samples from these pools when acquisition events fire.
"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import GameState


# ═══════════════════════════════════════════════════════════════════════════════
# ██ TECHNIQUE POOL (功法) — 120+ entries
# ═══════════════════════════════════════════════════════════════════════════════

TECHNIQUE_POOL = {
    "low": [
        # ── 剑法 ──
        {"name": "清风剑诀", "type": "sword", "category": "technique", "desc": "以灵力驭剑，化风为刃", "power": 1},
        {"name": "落叶剑法", "type": "sword", "category": "technique", "desc": "剑如落叶飘忽，攻敌不备", "power": 1},
        {"name": "青莲剑诀", "type": "sword", "category": "technique", "desc": "剑出如莲绽放，层层叠叠", "power": 2},
        {"name": "惊鸿剑", "type": "sword", "category": "technique", "desc": "一剑快如惊鸿，转瞬即逝", "power": 2},
        {"name": "断流剑法", "type": "sword", "category": "technique", "desc": "剑气如水截断，势不可挡", "power": 2},
        {"name": "松风剑意", "type": "sword", "category": "technique", "desc": "仿松间之风，柔中带刚", "power": 1},
        # ── 火系 ──
        {"name": "烈焰掌", "type": "fire", "category": "technique", "desc": "掌心凝火，焚尽万物", "power": 1},
        {"name": "火鸦术", "type": "fire", "category": "technique", "desc": "化灵力为火鸦群攻", "power": 1},
        {"name": "赤阳功", "type": "fire", "category": "technique", "desc": "修炼纯阳真气，克制阴寒", "power": 1},
        {"name": "焰灵诀", "type": "fire", "category": "technique", "desc": "引灵火入体，攻守兼备", "power": 2},
        {"name": "三昧真火诀", "type": "fire", "category": "technique", "desc": "凝聚三昧真火，焚烧万物", "power": 2},
        {"name": "炎爆术", "type": "fire", "category": "technique", "desc": "灵力压缩爆炸，范围杀伤", "power": 1},
        # ── 冰系 ──
        {"name": "寒冰术", "type": "ice", "category": "technique", "desc": "凝结水汽成冰，冰封方圆", "power": 1},
        {"name": "玄冰指", "type": "ice", "category": "technique", "desc": "指尖凝冰，冻人经脉", "power": 2},
        {"name": "霜华诀", "type": "ice", "category": "technique", "desc": "周身霜华弥漫，近者皆冻", "power": 1},
        {"name": "冰棱术", "type": "ice", "category": "technique", "desc": "凝冰为棱射出，穿透力强", "power": 1},
        {"name": "寒潭心法", "type": "ice", "category": "technique", "desc": "心如寒潭不波，冰系威力倍增", "power": 2},
        # ── 雷系 ──
        {"name": "落雷诀", "type": "thunder", "category": "technique", "desc": "引天雷入体，化为雷击", "power": 2},
        {"name": "雷光闪", "type": "thunder", "category": "technique", "desc": "身化雷光闪避，瞬间反击", "power": 2},
        {"name": "奔雷掌", "type": "thunder", "category": "technique", "desc": "掌中藏雷，一掌雷鸣", "power": 1},
        {"name": "电蛇术", "type": "thunder", "category": "technique", "desc": "放出电蛇游走，麻痹对手", "power": 1},
        # ── 身法 ──
        {"name": "疾风步", "type": "movement", "category": "technique", "desc": "身法如风，来去无踪", "power": 1},
        {"name": "灵蛇步", "type": "movement", "category": "technique", "desc": "身形游走如蛇，难以捕捉", "power": 1},
        {"name": "踏云步", "type": "movement", "category": "technique", "desc": "脚踏灵气如踏云，凌空而行", "power": 1},
        {"name": "鬼影步", "type": "movement", "category": "technique", "desc": "残影迷人，真身难辨", "power": 2},
        {"name": "燕回身法", "type": "movement", "category": "technique", "desc": "如燕般灵活转向，闪避绝佳", "power": 1},
        # ── 体修 ──
        {"name": "铁壁功", "type": "body", "category": "technique", "desc": "周身灵力凝甲，刀枪不入", "power": 1},
        {"name": "金刚拳", "type": "body", "category": "technique", "desc": "拳劲刚猛，力开金石", "power": 1},
        {"name": "裂石掌", "type": "body", "category": "technique", "desc": "掌力凝实如石，一掌碎岩", "power": 1},
        {"name": "铜皮铁骨功", "type": "body", "category": "technique", "desc": "肉身坚逾铜铁，硬抗法术", "power": 2},
        {"name": "蛮牛劲", "type": "body", "category": "technique", "desc": "爆发力惊人，力大无穷", "power": 1},
        {"name": "龟息功", "type": "body", "category": "technique", "desc": "闭息养气，伤势恢复加速", "power": 1},
        # ── 水/土/风 ──
        {"name": "碧水诀", "type": "water", "category": "technique", "desc": "驭水为盾，亦可化水刃伤敌", "power": 1},
        {"name": "土遁术", "type": "earth", "category": "technique", "desc": "遁入土中，来去自如", "power": 1},
        {"name": "风刃术", "type": "wind", "category": "technique", "desc": "凝风为刃，无形杀人", "power": 2},
        {"name": "流沙掌", "type": "earth", "category": "technique", "desc": "掌下生沙，困敌陷足", "power": 1},
        {"name": "水龙吟", "type": "water", "category": "technique", "desc": "驭水化龙形攻击", "power": 2},
        {"name": "旋风斩", "type": "wind", "category": "technique", "desc": "以身为轴旋转出风刃", "power": 1},
        # ── 辅助/特殊 ──
        {"name": "养气诀", "type": "auxiliary", "category": "technique", "desc": "温养灵力，加速恢复", "power": 1},
        {"name": "听风术", "type": "perception", "category": "technique", "desc": "以灵力感知四方，洞察先机", "power": 1},
        {"name": "缠丝手", "type": "binding", "category": "technique", "desc": "灵力化丝缠绕，困敌原地", "power": 1},
        {"name": "破甲锥", "type": "pierce", "category": "technique", "desc": "集中灵力于一点，破防利器", "power": 2},
        {"name": "金光咒", "type": "light", "category": "technique", "desc": "金光护体，驱邪避秽", "power": 1},
        {"name": "隐匿术", "type": "auxiliary", "category": "technique", "desc": "收敛气息，不被察觉", "power": 1},
        {"name": "凝神诀", "type": "auxiliary", "category": "technique", "desc": "凝练神识，提升精神力", "power": 1},
        {"name": "化毒术", "type": "poison", "category": "technique", "desc": "将灵力化为毒素侵蚀敌人", "power": 1},
        {"name": "飞针术", "type": "pierce", "category": "technique", "desc": "以灵力驭针，暗器防不胜防", "power": 1},
        {"name": "灵盾术", "type": "auxiliary", "category": "technique", "desc": "凝聚灵力护盾抵挡攻击", "power": 1},
        {"name": "蚀骨掌", "type": "poison", "category": "technique", "desc": "掌力附腐蚀之气，中者骨蚀", "power": 2},
        {"name": "摄魂术", "type": "illusion", "category": "technique", "desc": "以神识攻击扰乱对手心神", "power": 2},
    ],
    "mid": [
        # ── 剑法 ──
        {"name": "天罡剑意", "type": "sword", "category": "technique", "desc": "剑意如山，一剑破万法", "power": 3},
        {"name": "太虚剑诀", "type": "sword", "category": "technique", "desc": "剑出无形，虚实难辨", "power": 3},
        {"name": "万剑归宗", "type": "sword", "category": "technique", "desc": "千万剑气汇聚一点", "power": 4},
        {"name": "残虹剑法", "type": "sword", "category": "technique", "desc": "剑光如虹划过，残影灼目", "power": 3},
        {"name": "无影剑诀", "type": "sword", "category": "technique", "desc": "剑速极快，肉眼不可见", "power": 3},
        {"name": "九曲剑意", "type": "sword", "category": "technique", "desc": "剑意九折九转，难以预判", "power": 4},
        # ── 火/雷 ──
        {"name": "九幽焚天诀", "type": "fire", "category": "technique", "desc": "引九幽真火，焚天灭地", "power": 3},
        {"name": "星陨术", "type": "fire", "category": "technique", "desc": "凝聚星火坠落，范围毁灭", "power": 4},
        {"name": "业火诀", "type": "fire", "category": "technique", "desc": "心中业火化为攻击，愈怒愈强", "power": 3},
        {"name": "雷霆万钧", "type": "thunder", "category": "technique", "desc": "引天地雷霆，万钧之势", "power": 3},
        {"name": "紫电青雷", "type": "thunder", "category": "technique", "desc": "双雷齐发，天威难挡", "power": 3},
        {"name": "天罚雷阵", "type": "thunder", "category": "technique", "desc": "布雷阵困敌，雷劫降临", "power": 4},
        # ── 冰/水 ──
        {"name": "玄天冰魄", "type": "ice", "category": "technique", "desc": "极寒之力凝魄，冻裂虚空", "power": 3},
        {"name": "冰封万里", "type": "ice", "category": "technique", "desc": "方圆万里尽化冰原", "power": 4},
        {"name": "寒渊诀", "type": "ice", "category": "technique", "desc": "引深渊寒气，冻彻骨髓", "power": 3},
        {"name": "沧海决", "type": "water", "category": "technique", "desc": "化沧海之力为己用", "power": 3},
        # ── 体修/身法 ──
        {"name": "不动明王身", "type": "body", "category": "technique", "desc": "肉身如神，万邪不侵", "power": 3},
        {"name": "玄武真身", "type": "body", "category": "technique", "desc": "化身玄武，攻防一体", "power": 3},
        {"name": "八荒炼体诀", "type": "body", "category": "technique", "desc": "以天地精华淬炼肉身", "power": 4},
        {"name": "虚空挪移", "type": "movement", "category": "technique", "desc": "撕裂空间短距瞬移", "power": 4},
        {"name": "瞬步术", "type": "movement", "category": "technique", "desc": "一步千里，速度惊人", "power": 3},
        # ── 特殊 ──
        {"name": "大衍心经", "type": "dao", "category": "technique", "desc": "推演天机，预判敌手", "power": 3},
        {"name": "千幻魔音", "type": "illusion", "category": "technique", "desc": "以音攻心，幻境困敌", "power": 3},
        {"name": "山河印", "type": "earth", "category": "technique", "desc": "凝聚山河之力，镇压万物", "power": 4},
        {"name": "断魂指", "type": "pierce", "category": "technique", "desc": "一指点出，直取元神", "power": 4},
        {"name": "涅槃诀", "type": "recovery", "category": "technique", "desc": "濒死爆发，浴火重生", "power": 4},
        {"name": "万毒归元功", "type": "poison", "category": "technique", "desc": "以毒养身，百毒不侵", "power": 3},
        {"name": "天魔舞", "type": "illusion", "category": "technique", "desc": "舞姿迷惑心神，趁虚攻击", "power": 3},
        {"name": "五行轮转功", "type": "dao", "category": "technique", "desc": "五行相生相克灵活切换", "power": 4},
        {"name": "天地归元诀", "type": "recovery", "category": "technique", "desc": "吸收天地灵气极速恢复", "power": 3},
        {"name": "阴阳二气瓶", "type": "dao", "category": "technique", "desc": "操控阴阳二气攻敌", "power": 3},
        {"name": "血影缠身", "type": "binding", "category": "technique", "desc": "以血气化影缠绕困敌", "power": 3},
        {"name": "碎空掌", "type": "body", "category": "technique", "desc": "一掌击碎空间壁垒", "power": 4},
    ],
    "high": [
        {"name": "万法归一", "type": "dao", "category": "technique", "desc": "融万法于一身，以意念驭天地", "power": 5},
        {"name": "太上忘情诀", "type": "dao", "category": "technique", "desc": "斩断情丝，心如止水", "power": 5},
        {"name": "天地同寿", "type": "body", "category": "technique", "desc": "肉身与天地共鸣，近乎不灭", "power": 5},
        {"name": "一念成空", "type": "dao", "category": "technique", "desc": "一念之间，化实为虚", "power": 5},
        {"name": "神魔变", "type": "body", "category": "technique", "desc": "化身神魔，力压万法", "power": 5},
        {"name": "混沌剑意", "type": "sword", "category": "technique", "desc": "剑含混沌，斩断因果", "power": 5},
        {"name": "天劫引", "type": "thunder", "category": "technique", "desc": "借天劫之力攻敌", "power": 5},
        {"name": "轮回道", "type": "dao", "category": "technique", "desc": "窥探轮回，掌控生死", "power": 5},
        {"name": "虚空大挪移", "type": "movement", "category": "technique", "desc": "跨越虚空，万里瞬至", "power": 5},
        {"name": "诛仙剑阵", "type": "sword", "category": "technique", "desc": "四剑合一，诛仙灭神", "power": 5},
        {"name": "无极真经", "type": "dao", "category": "technique", "desc": "无极生太极，道法自然", "power": 5},
        {"name": "灭世雷劫", "type": "thunder", "category": "technique", "desc": "召唤毁灭级雷劫降临", "power": 5},
        {"name": "时空冻结", "type": "ice", "category": "technique", "desc": "冻结时空片段，万物静止", "power": 5},
        {"name": "焚天怒焰", "type": "fire", "category": "technique", "desc": "引天地怒火，焚尽苍穹", "power": 5},
        {"name": "天道镇压", "type": "dao", "category": "technique", "desc": "借天道之力镇压一切", "power": 5},
        {"name": "六道轮回拳", "type": "body", "category": "technique", "desc": "拳蕴六道之力，超脱生死", "power": 5},
        {"name": "湮灭之瞳", "type": "perception", "category": "technique", "desc": "目光所及万物湮灭", "power": 5},
        {"name": "不死真身", "type": "body", "category": "technique", "desc": "真身不死不灭，超越极限", "power": 5},
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# ██ TREASURE POOL (法宝) — 120+ entries
# ═══════════════════════════════════════════════════════════════════════════════

TREASURE_POOL = {
    "low": [
        # ── 兵器 ──
        {"name": "青锋剑", "type": "weapon", "category": "treasure", "desc": "锋利异常的灵剑", "power": 1},
        {"name": "紫霄剑", "type": "weapon", "category": "treasure", "desc": "剑身泛紫光，斩灵力如泥", "power": 2},
        {"name": "赤炎刀", "type": "weapon", "category": "treasure", "desc": "刀身附火焰，灼烧敌人", "power": 1},
        {"name": "寒玉剑", "type": "weapon", "category": "treasure", "desc": "剑身覆冰霜，伤口难愈", "power": 2},
        {"name": "玉骨扇", "type": "weapon", "category": "treasure", "desc": "以玉骨为架，扇风成刃", "power": 1},
        {"name": "月牙铲", "type": "weapon", "category": "treasure", "desc": "铲形法器，克制鬼修", "power": 1},
        {"name": "风雷旗", "type": "weapon", "category": "treasure", "desc": "可召风雷之力攻敌", "power": 2},
        {"name": "铜皮鼓", "type": "weapon", "category": "treasure", "desc": "鼓声震魂，扰人心神", "power": 1},
        {"name": "银丝网", "type": "weapon", "category": "treasure", "desc": "抛出后可困缚敌人", "power": 1},
        {"name": "碎星锤", "type": "weapon", "category": "treasure", "desc": "锤重千斤，一击碎石", "power": 1},
        {"name": "穿云枪", "type": "weapon", "category": "treasure", "desc": "枪尖锐利，可穿透护盾", "power": 2},
        {"name": "七星针", "type": "weapon", "category": "treasure", "desc": "七枚飞针同出，防不胜防", "power": 1},
        {"name": "翠竹剑", "type": "weapon", "category": "treasure", "desc": "以灵竹炼制，轻盈灵动", "power": 1},
        {"name": "裂地斧", "type": "weapon", "category": "treasure", "desc": "斧重如山，劈地裂石", "power": 2},
        {"name": "缚魂索", "type": "weapon", "category": "treasure", "desc": "锁链法器，束缚元神", "power": 2},
        # ── 防具 ──
        {"name": "玄铁盾", "type": "armor", "category": "treasure", "desc": "以玄铁铸就的护盾", "power": 1},
        {"name": "金丝甲", "type": "armor", "category": "treasure", "desc": "金蚕丝编就，刀枪不入", "power": 2},
        {"name": "碧波环", "type": "armor", "category": "treasure", "desc": "水属性护罩，抵御物理攻击", "power": 1},
        {"name": "龟甲符", "type": "armor", "category": "treasure", "desc": "贴身佩戴可挡致命一击", "power": 2},
        {"name": "霞光镜", "type": "armor", "category": "treasure", "desc": "可反射光系法术", "power": 1},
        {"name": "云纹袍", "type": "armor", "category": "treasure", "desc": "法袍内含灵阵，自动防御", "power": 1},
        {"name": "蛟鳞甲", "type": "armor", "category": "treasure", "desc": "蛟龙之鳞制成，水火难伤", "power": 2},
        {"name": "护心镜", "type": "armor", "category": "treasure", "desc": "贴于胸前，护住心脉", "power": 1},
        # ── 辅助 ──
        {"name": "追风靴", "type": "utility", "category": "treasure", "desc": "穿上后身法提升数倍", "power": 1},
        {"name": "避火珠", "type": "utility", "category": "treasure", "desc": "可挡火系法术一击", "power": 1},
        {"name": "灵犀簪", "type": "utility", "category": "treasure", "desc": "佩戴后神识增强三成", "power": 1},
        {"name": "聚灵珠", "type": "utility", "category": "treasure", "desc": "加速灵力恢复", "power": 1},
        {"name": "隐身斗篷", "type": "utility", "category": "treasure", "desc": "短时隐匿身形", "power": 2},
        {"name": "定风珠", "type": "utility", "category": "treasure", "desc": "可破风系法术", "power": 1},
        {"name": "传音玉简", "type": "utility", "category": "treasure", "desc": "千里传音，联络同伴", "power": 1},
        {"name": "照妖镜", "type": "utility", "category": "treasure", "desc": "照破幻术和化形", "power": 1},
        {"name": "储物袋", "type": "utility", "category": "treasure", "desc": "内含小空间，储物方便", "power": 1},
        {"name": "疗伤丹瓶", "type": "utility", "category": "treasure", "desc": "自动分泌疗伤灵液", "power": 1},
        {"name": "避毒珠", "type": "utility", "category": "treasure", "desc": "百毒不侵，解毒圣品", "power": 2},
        {"name": "乌金钩", "type": "weapon", "category": "treasure", "desc": "弯钩暗器，防不胜防", "power": 1},
        {"name": "青铜镜", "type": "utility", "category": "treasure", "desc": "铜镜照邪，驱散阴气", "power": 1},
        {"name": "灵纹笔", "type": "utility", "category": "treasure", "desc": "可画灵纹符箓的法笔", "power": 1},
        {"name": "流星锤", "type": "weapon", "category": "treasure", "desc": "铁链连锤，砸碎护盾", "power": 2},
        {"name": "碧血剑", "type": "weapon", "category": "treasure", "desc": "以碧血祭炼的妖剑", "power": 2},
        {"name": "金蛟剪", "type": "weapon", "category": "treasure", "desc": "蛟形双剪，绞碎万物", "power": 2},
        {"name": "千斤坠", "type": "weapon", "category": "treasure", "desc": "重力法器，压制敌人", "power": 1},
        {"name": "灵蛛丝", "type": "utility", "category": "treasure", "desc": "坚韧无比的灵蛛所吐之丝", "power": 1},
        {"name": "翠玉葫芦", "type": "utility", "category": "treasure", "desc": "可收纳灵液的炼丹辅助", "power": 1},
        {"name": "暗影匕", "type": "weapon", "category": "treasure", "desc": "隐于暗处的暗杀匕首", "power": 1},
        {"name": "护身玉佩", "type": "armor", "category": "treasure", "desc": "玉佩碎裂替主挡灾", "power": 1},
        {"name": "五毒幡", "type": "weapon", "category": "treasure", "desc": "幡上蕴含五种剧毒", "power": 2},
        {"name": "镇魂铃", "type": "utility", "category": "treasure", "desc": "铃声镇压邪祟魂魄", "power": 1},
        {"name": "焚香炉", "type": "utility", "category": "treasure", "desc": "焚灵香安神静心", "power": 1},
        {"name": "铁骨伞", "type": "armor", "category": "treasure", "desc": "伞面可挡法术攻击", "power": 1},
        {"name": "九环杖", "type": "weapon", "category": "treasure", "desc": "杖上九环响动摄魂", "power": 1},
    ],
    "mid": [
        # ── 兵器 ──
        {"name": "七星剑", "type": "weapon", "category": "treasure", "desc": "剑分七段，七星连珠", "power": 3},
        {"name": "破天锤", "type": "weapon", "category": "treasure", "desc": "一锤之力，破碎虚空", "power": 4},
        {"name": "凤血琴", "type": "weapon", "category": "treasure", "desc": "凤血祭炼，音波杀人", "power": 3},
        {"name": "飞仙剑", "type": "weapon", "category": "treasure", "desc": "极快飞剑，千里取首", "power": 3},
        {"name": "冰魄神针", "type": "weapon", "category": "treasure", "desc": "极寒暗器，中者经脉尽封", "power": 3},
        {"name": "血蝠幡", "type": "weapon", "category": "treasure", "desc": "以血祭幡，释放万千血蝠", "power": 3},
        {"name": "噬魂钟", "type": "weapon", "category": "treasure", "desc": "钟鸣夺魄，震裂元神", "power": 4},
        {"name": "落日弓", "type": "weapon", "category": "treasure", "desc": "弓引落日之力，一箭穿山", "power": 4},
        {"name": "天蛇鞭", "type": "weapon", "category": "treasure", "desc": "鞭如天蛇游动，缠杀敌手", "power": 3},
        {"name": "碧落剑", "type": "weapon", "category": "treasure", "desc": "碧光万丈，剑气纵横", "power": 3},
        {"name": "玄冥枪", "type": "weapon", "category": "treasure", "desc": "枪出如龙，玄冥之力蚀骨", "power": 4},
        {"name": "风火轮", "type": "weapon", "category": "treasure", "desc": "风火二轮齐飞，追敌不止", "power": 3},
        # ── 防具 ──
        {"name": "天蚕宝衣", "type": "armor", "category": "treasure", "desc": "天蚕丝织就，水火不侵", "power": 3},
        {"name": "九转玲珑塔", "type": "armor", "category": "treasure", "desc": "九层宝塔，镇压万邪", "power": 4},
        {"name": "龙鳞甲", "type": "armor", "category": "treasure", "desc": "真龙鳞片打造，坚不可摧", "power": 4},
        {"name": "玄天盾", "type": "armor", "category": "treasure", "desc": "凝聚玄天之力的护盾", "power": 3},
        {"name": "金刚罩", "type": "armor", "category": "treasure", "desc": "罩体金光，刀枪不入", "power": 3},
        # ── 辅助 ──
        {"name": "乾坤袋", "type": "utility", "category": "treasure", "desc": "内有乾坤，可收纳万物", "power": 3},
        {"name": "紫金葫芦", "type": "utility", "category": "treasure", "desc": "可收人灵魂，亦可炼丹", "power": 4},
        {"name": "玄天宝鉴", "type": "utility", "category": "treasure", "desc": "照破幻术，洞察万物", "power": 3},
        {"name": "万象珠", "type": "utility", "category": "treasure", "desc": "内含小世界，可困敌于其中", "power": 4},
        {"name": "天机算盘", "type": "utility", "category": "treasure", "desc": "推演天机，预判敌手", "power": 3},
        {"name": "定海神珠", "type": "utility", "category": "treasure", "desc": "定一方天地，阵法核心", "power": 4},
        {"name": "星辰罗盘", "type": "utility", "category": "treasure", "desc": "指引方向，破阵有奇效", "power": 3},
        {"name": "回天丹炉", "type": "utility", "category": "treasure", "desc": "炼制高阶丹药的宝炉", "power": 3},
        {"name": "天河锁", "type": "weapon", "category": "treasure", "desc": "锁链横空，封锁天河", "power": 4},
        {"name": "万刃伞", "type": "weapon", "category": "treasure", "desc": "伞开万刃飞出，密如雨点", "power": 3},
        {"name": "九阳瓶", "type": "utility", "category": "treasure", "desc": "瓶中装九颗小太阳", "power": 4},
        {"name": "太虚尺", "type": "weapon", "category": "treasure", "desc": "一尺量天地，法则之器", "power": 3},
        {"name": "阴阳双鱼玉", "type": "armor", "category": "treasure", "desc": "阴阳平衡护体", "power": 3},
        {"name": "百花裙", "type": "armor", "category": "treasure", "desc": "百花灵力编织，自动疗伤", "power": 3},
        {"name": "覆海印", "type": "weapon", "category": "treasure", "desc": "印落如覆海，镇压万方", "power": 4},
        {"name": "灵虚笛", "type": "weapon", "category": "treasure", "desc": "笛音控人心神", "power": 3},
        {"name": "悟道石", "type": "utility", "category": "treasure", "desc": "坐于其上感悟天地", "power": 3},
        {"name": "五行灵珠", "type": "utility", "category": "treasure", "desc": "五行合一的灵珠", "power": 4},
    ],
    "high": [
        {"name": "混元珠", "type": "utility", "category": "treasure", "desc": "混沌之力凝聚，攻防一体", "power": 5},
        {"name": "斩仙剑", "type": "weapon", "category": "treasure", "desc": "传说中的仙器，可斩真仙", "power": 5},
        {"name": "造化玉碟", "type": "utility", "category": "treasure", "desc": "记载天地法则，悟之可成道", "power": 5},
        {"name": "太极图", "type": "armor", "category": "treasure", "desc": "阴阳互生，万法不侵", "power": 5},
        {"name": "封神榜", "type": "utility", "category": "treasure", "desc": "可定他人生死因果", "power": 5},
        {"name": "盘古斧", "type": "weapon", "category": "treasure", "desc": "开天辟地之力，一斧劈虚空", "power": 5},
        {"name": "天尊印", "type": "weapon", "category": "treasure", "desc": "镇压天地之印，重逾万山", "power": 5},
        {"name": "大日金轮", "type": "weapon", "category": "treasure", "desc": "凝聚大日精华，焚灭万物", "power": 5},
        {"name": "无量塔", "type": "armor", "category": "treasure", "desc": "无量世界化为堡垒", "power": 5},
        {"name": "轮回镜", "type": "utility", "category": "treasure", "desc": "照见轮回，可逆转因果", "power": 5},
        {"name": "山河社稷图", "type": "utility", "category": "treasure", "desc": "自含一方世界，镇压天地", "power": 5},
        {"name": "诛仙四剑", "type": "weapon", "category": "treasure", "desc": "绝诛陷戮四剑合一", "power": 5},
        {"name": "天帝战甲", "type": "armor", "category": "treasure", "desc": "远古天帝遗甲，坚逾万界", "power": 5},
        {"name": "虚无之锤", "type": "weapon", "category": "treasure", "desc": "一锤击入虚无，不可抵挡", "power": 5},
        {"name": "天命灵灯", "type": "utility", "category": "treasure", "desc": "灯火不灭则命不绝", "power": 5},
        {"name": "万界之门", "type": "utility", "category": "treasure", "desc": "可通往任何世界的门户", "power": 5},
        {"name": "永恒之冠", "type": "armor", "category": "treasure", "desc": "戴者永生不死", "power": 5},
        {"name": "碎星弓", "type": "weapon", "category": "treasure", "desc": "一箭射碎星辰", "power": 5},
        {"name": "万灵鼎", "type": "utility", "category": "treasure", "desc": "可炼化万灵为己用", "power": 5},
        {"name": "天罗地网", "type": "weapon", "category": "treasure", "desc": "铺天盖地无处可逃", "power": 5},
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# ██ SECRET ART POOL (秘术) — 120+ entries
# ═══════════════════════════════════════════════════════════════════════════════

SECRET_ART_POOL = {
    "low": [
        {"name": "幻身术", "type": "illusion", "category": "secret_art", "desc": "分化幻影迷惑敌人", "power": 1},
        {"name": "摄魂眼", "type": "mental", "category": "secret_art", "desc": "目光对视可短暂控制心神", "power": 2},
        {"name": "遁甲术", "type": "escape", "category": "secret_art", "desc": "借天地之势遁逃无踪", "power": 1},
        {"name": "凝血术", "type": "curse", "category": "secret_art", "desc": "令敌人血液凝滞运转不畅", "power": 2},
        {"name": "移形换位", "type": "space", "category": "secret_art", "desc": "瞬间与目标交换位置", "power": 2},
        {"name": "噬灵术", "type": "drain", "category": "secret_art", "desc": "吸取对手灵力为己用", "power": 2},
        {"name": "迷心雾", "type": "illusion", "category": "secret_art", "desc": "释放迷雾使人失去方向", "power": 1},
        {"name": "追踪术", "type": "tracking", "category": "secret_art", "desc": "标记目标，千里追踪", "power": 1},
        {"name": "镜花水月", "type": "illusion", "category": "secret_art", "desc": "创造虚假景象欺骗感官", "power": 1},
        {"name": "蚀心咒", "type": "curse", "category": "secret_art", "desc": "暗中种下心魔种子", "power": 2},
        {"name": "固魂术", "type": "auxiliary", "category": "secret_art", "desc": "稳固魂魄，抵御神魂攻击", "power": 1},
        {"name": "解毒秘法", "type": "auxiliary", "category": "secret_art", "desc": "以秘法化解百毒", "power": 1},
        {"name": "观气术", "type": "perception", "category": "secret_art", "desc": "可看透对手修为深浅", "power": 1},
        {"name": "潜行术", "type": "escape", "category": "secret_art", "desc": "完全隐匿气息行踪", "power": 1},
        {"name": "灵犀通", "type": "auxiliary", "category": "secret_art", "desc": "与同伴心意相通配合无间", "power": 1},
        {"name": "弱点洞察", "type": "perception", "category": "secret_art", "desc": "洞察敌人法术弱点", "power": 2},
        {"name": "反噬术", "type": "curse", "category": "secret_art", "desc": "将受到的伤害反弹一部分", "power": 2},
        {"name": "替身术", "type": "escape", "category": "secret_art", "desc": "以物替身承受致命一击", "power": 2},
        {"name": "化雾隐身", "type": "escape", "category": "secret_art", "desc": "化为雾气逃脱束缚", "power": 1},
        {"name": "窃听术", "type": "perception", "category": "secret_art", "desc": "远距离窃听他人交谈", "power": 1},
        {"name": "嫁祸术", "type": "curse", "category": "secret_art", "desc": "转移因果，嫁祸他人", "power": 2},
        {"name": "灵目术", "type": "perception", "category": "secret_art", "desc": "夜间视物如昼", "power": 1},
        {"name": "封印术", "type": "binding", "category": "secret_art", "desc": "封印对手灵力一段时间", "power": 2},
        {"name": "化尸术", "type": "curse", "category": "secret_art", "desc": "加速腐化死尸以障对手", "power": 1},
        {"name": "共鸣术", "type": "auxiliary", "category": "secret_art", "desc": "与法宝共鸣增加威力", "power": 1},
        {"name": "夺舍反制", "type": "mental", "category": "secret_art", "desc": "抵御他人夺舍之术", "power": 2},
        {"name": "灵力锁", "type": "binding", "category": "secret_art", "desc": "锁定敌人使其无法聚气", "power": 2},
        {"name": "引蛇出洞", "type": "tracking", "category": "secret_art", "desc": "诱出隐藏的敌人", "power": 1},
        {"name": "千面变", "type": "illusion", "category": "secret_art", "desc": "改变容貌气息伪装他人", "power": 1},
        {"name": "摸骨术", "type": "perception", "category": "secret_art", "desc": "触摸即知对方体质天赋", "power": 1},
        {"name": "死气感应", "type": "perception", "category": "secret_art", "desc": "感应死亡气息提前预警", "power": 1},
        {"name": "硬化术", "type": "auxiliary", "category": "secret_art", "desc": "使物体竅时坂化为钢铁", "power": 1},
        {"name": "到文读心", "type": "mental", "category": "secret_art", "desc": "读取对方表层思绪", "power": 2},
        {"name": "波动屏障", "type": "auxiliary", "category": "secret_art", "desc": "屏蔽一切灵力波动探测", "power": 1},
        {"name": "破阵眉", "type": "auxiliary", "category": "secret_art", "desc": "眼中看穿阵法破绽", "power": 2},
        {"name": "灵气覆压", "type": "binding", "category": "secret_art", "desc": "释放灵压使低阶修士动弹不得", "power": 2},
        {"name": "探宝术", "type": "perception", "category": "secret_art", "desc": "感知附近宝物灵草位置", "power": 1},
        {"name": "风水术", "type": "auxiliary", "category": "secret_art", "desc": "察观地势寻找灵脉宝地", "power": 1},
        {"name": "统灵秘法", "type": "binding", "category": "secret_art", "desc": "强化与灵兽的统御联系", "power": 1},
        {"name": "灵胎种子", "type": "curse", "category": "secret_art", "desc": "种下灵胎种子持续吸取敌人灵力", "power": 2},
        {"name": "破妖术", "type": "perception", "category": "secret_art", "desc": "识破妖兽化形伪装", "power": 1},
        {"name": "地脉感应", "type": "perception", "category": "secret_art", "desc": "感知地下灵脉走向", "power": 1},
        {"name": "消影术", "type": "escape", "category": "secret_art", "desc": "身影完全消失片刻", "power": 2},
        {"name": "点穴手", "type": "binding", "category": "secret_art", "desc": "点封穴道使对手无法动弹", "power": 2},
        {"name": "血灵术", "type": "drain", "category": "secret_art", "desc": "以自身精血为代价爆发战力", "power": 2},
        {"name": "风水转向", "type": "fate", "category": "secret_art", "desc": "改变战场地势为己所用", "power": 1},
        {"name": "凝神抽取", "type": "drain", "category": "secret_art", "desc": "吸取对手精神力补充自己", "power": 2},
        {"name": "灾厄转嫁", "type": "fate", "category": "secret_art", "desc": "将自身灾厄转移到所触物体", "power": 2},
    ],
    "mid": [
        {"name": "天眼通", "type": "perception", "category": "secret_art", "desc": "开天眼洞察万里之外", "power": 3},
        {"name": "夺命十三针", "type": "curse", "category": "secret_art", "desc": "十三道灵针封穴夺命", "power": 4},
        {"name": "七杀阵法", "type": "formation", "category": "secret_art", "desc": "一人可布七杀阵", "power": 4},
        {"name": "移星换斗", "type": "space", "category": "secret_art", "desc": "挪移星辰之力为己用", "power": 4},
        {"name": "傀儡替身", "type": "escape", "category": "secret_art", "desc": "傀儡替死，金蝉脱壳", "power": 3},
        {"name": "因果逆转", "type": "fate", "category": "secret_art", "desc": "短暂逆转一段因果", "power": 4},
        {"name": "噬魂大法", "type": "drain", "category": "secret_art", "desc": "吞噬对手魂魄增强己身", "power": 4},
        {"name": "血遁术", "type": "escape", "category": "secret_art", "desc": "燃烧精血瞬间远遁", "power": 3},
        {"name": "万象幻阵", "type": "illusion", "category": "secret_art", "desc": "幻阵困敌，虚实莫辨", "power": 3},
        {"name": "灵魂烙印", "type": "curse", "category": "secret_art", "desc": "在敌人魂魄上留下控制印记", "power": 4},
        {"name": "天机推演", "type": "fate", "category": "secret_art", "desc": "推演未来走势趋吉避凶", "power": 3},
        {"name": "还魂秘术", "type": "auxiliary", "category": "secret_art", "desc": "短时间内复活刚死之人", "power": 4},
        {"name": "千里传讯", "type": "auxiliary", "category": "secret_art", "desc": "跨越千里传递完整信息", "power": 3},
        {"name": "禁制破解", "type": "auxiliary", "category": "secret_art", "desc": "破解他人设下的禁制封印", "power": 3},
        {"name": "心魔种子", "type": "mental", "category": "secret_art", "desc": "在敌人识海种下心魔", "power": 4},
        {"name": "九宫锁天阵", "type": "formation", "category": "secret_art", "desc": "九宫阵锁天封地", "power": 4},
        {"name": "血脉觉醒", "type": "auxiliary", "category": "secret_art", "desc": "激发隐藏血脉之力", "power": 3},
        {"name": "空间折叠", "type": "space", "category": "secret_art", "desc": "折叠空间缩短距离", "power": 3},
        {"name": "命格替换", "type": "fate", "category": "secret_art", "desc": "以他人命格替换自身劫数", "power": 4},
        {"name": "万毒噬心", "type": "curse", "category": "secret_art", "desc": "万毒汇聚攻心，无药可解", "power": 4},
        {"name": "通灵秘法", "type": "auxiliary", "category": "secret_art", "desc": "沟通天地灵物获取信息", "power": 3},
        {"name": "镇魂大阵", "type": "formation", "category": "secret_art", "desc": "镇压魂魄，令人无法动弹", "power": 3},
        {"name": "血祭秘术", "type": "curse", "category": "secret_art", "desc": "以血为祭释放禁术之力", "power": 4},
        {"name": "四象封印", "type": "formation", "category": "secret_art", "desc": "以四象之力封印敌人", "power": 4},
        {"name": "拟态变化", "type": "illusion", "category": "secret_art", "desc": "模拟任何生物的形态和能力", "power": 3},
        {"name": "天地绝杀阵", "type": "formation", "category": "secret_art", "desc": "绝杀大阵，入者必死", "power": 4},
        {"name": "三花聚顶", "type": "auxiliary", "category": "secret_art", "desc": "精气神三花合一爆发", "power": 4},
        {"name": "神通千变", "type": "illusion", "category": "secret_art", "desc": "神通广大，千变万化", "power": 3},
        {"name": "因果丝", "type": "fate", "category": "secret_art", "desc": "看穿人与人之间的因果线", "power": 3},
        {"name": "天罚代行", "type": "curse", "category": "secret_art", "desc": "以天罚之名击杀敌人", "power": 4},
        {"name": "天地大权术", "type": "binding", "category": "secret_art", "desc": "片区重力倍增压制敌人", "power": 3},
        {"name": "强制解契", "type": "curse", "category": "secret_art", "desc": "强行解除敌人与灵兽的契约", "power": 3},
        {"name": "血脉共振", "type": "auxiliary", "category": "secret_art", "desc": "引发同血脉修士的力量共振", "power": 3},
        {"name": "幻梦结界", "type": "illusion", "category": "secret_art", "desc": "将敌人拉入梦境世界", "power": 4},
        {"name": "元神出窍", "type": "escape", "category": "secret_art", "desc": "元神离体远程作战", "power": 4},
    ],
    "high": [
        {"name": "天道契约", "type": "fate", "category": "secret_art", "desc": "与天道立约，违者天罚", "power": 5},
        {"name": "时空逆流", "type": "space", "category": "secret_art", "desc": "逆转短暂时空", "power": 5},
        {"name": "万灵归宗", "type": "drain", "category": "secret_art", "desc": "吸收方圆万灵之力", "power": 5},
        {"name": "灭世禁咒", "type": "curse", "category": "secret_art", "desc": "毁天灭地的终极禁术", "power": 5},
        {"name": "大挪移术", "type": "space", "category": "secret_art", "desc": "瞬移至任何去过之地", "power": 5},
        {"name": "乾坤大阵", "type": "formation", "category": "secret_art", "desc": "以乾坤为阵，困锁天地", "power": 5},
        {"name": "逆天改命", "type": "fate", "category": "secret_art", "desc": "违逆天命，改写命运", "power": 5},
        {"name": "万法禁制", "type": "binding", "category": "secret_art", "desc": "禁绝一切法术运转", "power": 5},
        {"name": "神念化身", "type": "mental", "category": "secret_art", "desc": "神念化为实体分身作战", "power": 5},
        {"name": "大因果术", "type": "fate", "category": "secret_art", "desc": "操控因果长河，改写过去", "power": 5},
        {"name": "万界通道", "type": "space", "category": "secret_art", "desc": "打开通往其他世界的通道", "power": 5},
        {"name": "天劫转嫁", "type": "fate", "category": "secret_art", "desc": "将天劫转嫁他人承受", "power": 5},
        {"name": "太古禁术", "type": "curse", "category": "secret_art", "desc": "太古时代的禁忌之术", "power": 5},
        {"name": "万界融合", "type": "space", "category": "secret_art", "desc": "融合万界之力为一击", "power": 5},
        {"name": "命运织布", "type": "fate", "category": "secret_art", "desc": "重新编织天地命运线", "power": 5},
        {"name": "魂灭天诛", "type": "mental", "category": "secret_art", "desc": "一诛灭魂，万灵俱灭", "power": 5},
        {"name": "天地封锁", "type": "binding", "category": "secret_art", "desc": "封锁整片天地，万物禁止", "power": 5},
        {"name": "混沌重开", "type": "space", "category": "secret_art", "desc": "将一切打回混沌未开状态", "power": 5},
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# ██ PUPPET POOL (傀儡) — 100+ entries
# ═══════════════════════════════════════════════════════════════════════════════

PUPPET_POOL = {
    "low": [
        {"name": "铁甲木偶", "type": "melee", "category": "puppet", "desc": "铁皮包裹的格斗傀儡", "power": 1},
        {"name": "飞刃傀儡", "type": "ranged", "category": "puppet", "desc": "可发射暗器的小型傀儡", "power": 1},
        {"name": "探路蜘蛛", "type": "scout", "category": "puppet", "desc": "蛛形侦察傀儡，隐蔽性强", "power": 1},
        {"name": "石人守卫", "type": "defense", "category": "puppet", "desc": "石头傀儡，防御力惊人", "power": 1},
        {"name": "竹节蛇", "type": "melee", "category": "puppet", "desc": "竹节相连的蛇形傀儡", "power": 1},
        {"name": "风筝鸢", "type": "scout", "category": "puppet", "desc": "空中侦查的鸟形傀儡", "power": 1},
        {"name": "自爆蜂", "type": "ranged", "category": "puppet", "desc": "冲向敌人自爆的小型傀儡", "power": 2},
        {"name": "盾卫傀儡", "type": "defense", "category": "puppet", "desc": "持盾格挡的护卫傀儡", "power": 1},
        {"name": "毒烟人", "type": "ranged", "category": "puppet", "desc": "释放毒烟的人形傀儡", "power": 2},
        {"name": "铁臂猿", "type": "melee", "category": "puppet", "desc": "力大无穷的猿形傀儡", "power": 2},
        {"name": "灵光蝶", "type": "scout", "category": "puppet", "desc": "发光引路的蝶形傀儡", "power": 1},
        {"name": "钢针鼠", "type": "melee", "category": "puppet", "desc": "全身钢针的鼠形傀儡", "power": 1},
        {"name": "回旋镖傀", "type": "ranged", "category": "puppet", "desc": "抛出后自动回收的飞傀", "power": 1},
        {"name": "锁链傀儡", "type": "melee", "category": "puppet", "desc": "以锁链缠绕困敌的傀儡", "power": 2},
        {"name": "陷阱蛛网", "type": "defense", "category": "puppet", "desc": "自动布置蛛网陷阱", "power": 1},
        {"name": "传信鸽", "type": "scout", "category": "puppet", "desc": "传递消息的机关鸽", "power": 1},
        {"name": "烈焰蟾蜍", "type": "ranged", "category": "puppet", "desc": "喷射火焰的蟾蜍傀儡", "power": 2},
        {"name": "掘地鼹鼠", "type": "scout", "category": "puppet", "desc": "潜入地下探路的傀儡", "power": 1},
        {"name": "双刃螳螂", "type": "melee", "category": "puppet", "desc": "双臂如刀的螳螂傀儡", "power": 2},
        {"name": "玄铁龟壳", "type": "defense", "category": "puppet", "desc": "龟形防御傀儡，极难击破", "power": 2},
        {"name": "飞刃螢火虫", "type": "ranged", "category": "puppet", "desc": "发射火焰飞刃的虫形傀儡", "power": 2},
        {"name": "铁子兵", "type": "melee", "category": "puppet", "desc": "小型铁人军团，数量取胜", "power": 1},
        {"name": "金翅雁", "type": "scout", "category": "puppet", "desc": "金属雁形侦察傀儡，快速传信", "power": 1},
        {"name": "碰碰车", "type": "melee", "category": "puppet", "desc": "小型冲撞车傀儡，排山倒海", "power": 1},
        {"name": "吹箭蛇", "type": "ranged", "category": "puppet", "desc": "口吐毒针的蛇形傀儡", "power": 1},
        {"name": "电弧蟹", "type": "ranged", "category": "puppet", "desc": "螯间放电的蟹形傀儡", "power": 2},
        {"name": "铁甲牲牛", "type": "defense", "category": "puppet", "desc": "抵挡冲击的牛形傀儡", "power": 1},
        {"name": "地钻蟲蛇", "type": "scout", "category": "puppet", "desc": "钻入地下破坏阵法根基", "power": 2},
        {"name": "灵光火狐", "type": "ranged", "category": "puppet", "desc": "喷射灵火的狐形傀儡", "power": 2},
        {"name": "飞镖鹰", "type": "ranged", "category": "puppet", "desc": "飞行投掷暗器的鹰形傀儡", "power": 1},
        {"name": "捕兽网蛛", "type": "defense", "category": "puppet", "desc": "布置巨网困捕敌人", "power": 1},
        {"name": "穿山甲虫", "type": "melee", "category": "puppet", "desc": "钻山裂石的甲虫傀儡", "power": 2},
        {"name": "司南针蛟", "type": "scout", "category": "puppet", "desc": "可指引方向的导航傀儡", "power": 1},
        {"name": "吹笛人", "type": "melee", "category": "puppet", "desc": "以笛音指挥其他傀儡协同作战", "power": 2},
        {"name": "玄武盾阵", "type": "defense", "category": "puppet", "desc": "多具盾傀儡组成护盾阵型", "power": 2},
        {"name": "追踪犬", "type": "scout", "category": "puppet", "desc": "嵌入嘲风的犬形追踪傀儡", "power": 1},
        {"name": "毒爆蚂蚁", "type": "ranged", "category": "puppet", "desc": "微型自爆毒蛇，防不胜防", "power": 2},
        {"name": "火波狸", "type": "ranged", "category": "puppet", "desc": "逎火球的狸形傀儡", "power": 1},
        {"name": "射月弓傀", "type": "ranged", "category": "puppet", "desc": "自动射箭的弓箭傀儡", "power": 2},
        {"name": "铁卫巨人", "type": "defense", "category": "puppet", "desc": "两丈高铁人守卫傀儡", "power": 2},
        {"name": "地鼻虾蚣", "type": "melee", "category": "puppet", "desc": "钻入地下突袭的虾蚣傀儡", "power": 2},
        {"name": "灵触章鱼", "type": "binding", "category": "puppet", "desc": "触手缠绕困敌的海形傀儡", "power": 2},
        {"name": "铁蜂群", "type": "ranged", "category": "puppet", "desc": "成群出击的微型铁蜂傀儡", "power": 1},
        {"name": "光影雀", "type": "scout", "category": "puppet", "desc": "投射光影信息的侦查傀儡", "power": 1},
        {"name": "铁笛人", "type": "melee", "category": "puppet", "desc": "吹笛发出音波攻击的人形傀儡", "power": 2},
        {"name": "磨盘巨云", "type": "melee", "category": "puppet", "desc": "旋转磨盘碾压敌人的巨型傀儡", "power": 2},
        {"name": "火属弹射人", "type": "ranged", "category": "puppet", "desc": "发射火系弹丸的人形傀儡", "power": 2},
        {"name": "坐骑战马", "type": "melee", "category": "puppet", "desc": "可坐骑冲锷的战马傀儡", "power": 2},
        {"name": "护卫石像", "type": "defense", "category": "puppet", "desc": "石像守卫，拍碎一切进犯者", "power": 2},
        {"name": "钢爪鹰", "type": "melee", "category": "puppet", "desc": "钢爪擕抑的鹰形傀儡", "power": 2},
        {"name": "纽丝傀娃", "type": "melee", "category": "puppet", "desc": "以灵丝控制的精密人形傀儡", "power": 2},
    ],
    "mid": [
        {"name": "天机战偶", "type": "melee", "category": "puppet", "desc": "精密机关驱动的战斗傀儡", "power": 3},
        {"name": "雷火巨人", "type": "melee", "category": "puppet", "desc": "体内蕴含雷火之力的巨型傀儡", "power": 4},
        {"name": "千面傀儡", "type": "scout", "category": "puppet", "desc": "可变化容貌的间谍傀儡", "power": 3},
        {"name": "万刃蜈蚣", "type": "melee", "category": "puppet", "desc": "百足千刃的巨型蜈蚣傀", "power": 4},
        {"name": "玄天神弩", "type": "ranged", "category": "puppet", "desc": "自动瞄准发射的弩炮傀儡", "power": 3},
        {"name": "金刚力士", "type": "defense", "category": "puppet", "desc": "金刚不坏之身的护卫傀儡", "power": 4},
        {"name": "影杀傀儡", "type": "melee", "category": "puppet", "desc": "隐于暗处的暗杀型傀儡", "power": 3},
        {"name": "百臂修罗", "type": "melee", "category": "puppet", "desc": "拥有百条手臂的修罗傀", "power": 4},
        {"name": "灵炮傀儡", "type": "ranged", "category": "puppet", "desc": "蓄灵爆发的远程炮台傀儡", "power": 3},
        {"name": "铜墙铁壁", "type": "defense", "category": "puppet", "desc": "化为城墙护卫的巨型傀儡", "power": 3},
        {"name": "飞天战鹰", "type": "ranged", "category": "puppet", "desc": "空中俯冲攻击的大型傀儡", "power": 3},
        {"name": "寒冰巨蟹", "type": "defense", "category": "puppet", "desc": "全身覆冰的蟹形防御傀", "power": 3},
        {"name": "九幽魂傀", "type": "melee", "category": "puppet", "desc": "以怨魂驱动的恐怖傀儡", "power": 4},
        {"name": "机关龙", "type": "melee", "category": "puppet", "desc": "龙形机关傀儡，吐息伤敌", "power": 4},
        {"name": "幻术傀师", "type": "scout", "category": "puppet", "desc": "施放幻术的辅助型傀儡", "power": 3},
        {"name": "多足攻城车", "type": "melee", "category": "puppet", "desc": "改良攻城器械化的巨型傀儡", "power": 4},
        {"name": "天罗网体", "type": "defense", "category": "puppet", "desc": "布下天罗网困敌的巨型傀儡", "power": 3},
        {"name": "灵银刺客", "type": "melee", "category": "puppet", "desc": "极速刺杀的精密傀儡", "power": 3},
        {"name": "火山巨人", "type": "melee", "category": "puppet", "desc": "体内燃烧火山之力的巨傀", "power": 4},
        {"name": "蓄能波动炮", "type": "ranged", "category": "puppet", "desc": "蓄能开火的远程重炮傀儡", "power": 4},
        {"name": "复制傀儡", "type": "melee", "category": "puppet", "desc": "可复制敌人战斗风格的傀儡", "power": 4},
        {"name": "寒冰巨蟹", "type": "defense", "category": "puppet", "desc": "冰封万物的巨型蟹形傀儡", "power": 3},
        {"name": "天兵战僮", "type": "melee", "category": "puppet", "desc": "仿天兵制作的战斗傀儡", "power": 4},
        {"name": "灵网巨蛛", "type": "defense", "category": "puppet", "desc": "吐灵力丝网困敌的巨蛛傀儡", "power": 3},
        {"name": "破阵铁人", "type": "melee", "category": "puppet", "desc": "专门破坐阵法的特化傀儡", "power": 3},
        {"name": "风暴战鹰", "type": "ranged", "category": "puppet", "desc": "风系鹰形傀儡，羽刃如雨", "power": 4},
        {"name": "万刃铁刺猙", "type": "melee", "category": "puppet", "desc": "全身铁刺的刺猙形傀儡", "power": 3},
        {"name": "雷光巨蛎", "type": "ranged", "category": "puppet", "desc": "尾部释放雷光的巨蛎傀儡", "power": 4},
        {"name": "银甲守护者", "type": "defense", "category": "puppet", "desc": "精密银甲覆体的守卫傀儡", "power": 3},
        {"name": "毒焱术士", "type": "ranged", "category": "puppet", "desc": "喷射毒雾的术士型傀儡", "power": 3},
        {"name": "碰撞牡牛", "type": "melee", "category": "puppet", "desc": "重型冲撞的牛形战傀", "power": 4},
        {"name": "射日弩台", "type": "ranged", "category": "puppet", "desc": "聚能激发的巨型弩炮傀儡", "power": 4},
        {"name": "万象变化傀", "type": "melee", "category": "puppet", "desc": "可変换多种形态的变化傀儡", "power": 4},
    ],
    "high": [
        {"name": "天机神将", "type": "melee", "category": "puppet", "desc": "近乎化神级战力的终极傀儡", "power": 5},
        {"name": "万灵战偶", "type": "melee", "category": "puppet", "desc": "以万灵之力驱动的远古傀儡", "power": 5},
        {"name": "星辰巨人", "type": "melee", "category": "puppet", "desc": "体内封印星辰之力的巨型傀", "power": 5},
        {"name": "虚空蜃兽", "type": "scout", "category": "puppet", "desc": "穿行虚空的蜃龙傀儡", "power": 5},
        {"name": "灭世魔偶", "type": "melee", "category": "puppet", "desc": "上古魔族制造的灭世兵器", "power": 5},
        {"name": "九天神兵阵", "type": "ranged", "category": "puppet", "desc": "九具神兵傀儡组成阵法", "power": 5},
        {"name": "太古石魔", "type": "defense", "category": "puppet", "desc": "太古时期留下的不朽石魔", "power": 5},
        {"name": "天人战体", "type": "melee", "category": "puppet", "desc": "模仿天人体魄的完美傀儡", "power": 5},
        {"name": "混沌傀皇", "type": "melee", "category": "puppet", "desc": "混沌之气铸就的傀儡之王", "power": 5},
        {"name": "时空守卫", "type": "defense", "category": "puppet", "desc": "守护时空裂隙的远古造物", "power": 5},
        {"name": "彼岸灵船", "type": "melee", "category": "puppet", "desc": "渡彼岸的幽冥战船傀儡", "power": 5},
        {"name": "万灵仓储", "type": "defense", "category": "puppet", "desc": "可储存万灵之力的巨型傀儡", "power": 5},
        {"name": "灭世巨人组", "type": "melee", "category": "puppet", "desc": "多具灭世巨人组合作战", "power": 5},
        {"name": "九天禁制傀", "type": "ranged", "category": "puppet", "desc": "可释放九天禁术的傀儡", "power": 5},
        {"name": "天道傀儡", "type": "melee", "category": "puppet", "desc": "融入天道之力的终极傀儡", "power": 5},
        {"name": "彼岸花傀", "type": "ranged", "category": "puppet", "desc": "撞触即灭的绝命傀儡", "power": 5},
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# ██ SPIRIT BEAST POOL (灵兽) — 120+ entries
# ═══════════════════════════════════════════════════════════════════════════════

SPIRIT_BEAST_POOL = {
    "low": [
        {"name": "赤焰狐", "type": "fire", "category": "spirit_beast", "desc": "通体赤红的火狐，善用火焰", "power": 1},
        {"name": "翠翼雀", "type": "wind", "category": "spirit_beast", "desc": "翠绿小雀，速度奇快", "power": 1},
        {"name": "玄水龟", "type": "water", "category": "spirit_beast", "desc": "水系灵龟，防御极强", "power": 1},
        {"name": "铁背狼", "type": "melee", "category": "spirit_beast", "desc": "脊背坚硬如铁的灵狼", "power": 1},
        {"name": "金翅鹏", "type": "wind", "category": "spirit_beast", "desc": "金色翅膀的大鹏，可载人飞", "power": 2},
        {"name": "墨蛟", "type": "water", "category": "spirit_beast", "desc": "黑色蛟龙幼崽，潜力巨大", "power": 2},
        {"name": "雷隼", "type": "thunder", "category": "spirit_beast", "desc": "翼间带电的猎隼，闪电突袭", "power": 2},
        {"name": "寒冰蟒", "type": "ice", "category": "spirit_beast", "desc": "寒气逼人的大蟒", "power": 1},
        {"name": "灵猫", "type": "scout", "category": "spirit_beast", "desc": "灵巧小猫，善于侦察", "power": 1},
        {"name": "毒蜂王", "type": "poison", "category": "spirit_beast", "desc": "统领蜂群的蜂王", "power": 2},
        {"name": "地火蜥蜴", "type": "fire", "category": "spirit_beast", "desc": "栖于地火中的灵蜥", "power": 1},
        {"name": "风猿", "type": "wind", "category": "spirit_beast", "desc": "速度极快的灵猿", "power": 1},
        {"name": "铁角牛", "type": "melee", "category": "spirit_beast", "desc": "角坚如铁的灵牛，冲撞力强", "power": 1},
        {"name": "紫瞳鸦", "type": "scout", "category": "spirit_beast", "desc": "紫色眼瞳能看穿幻术", "power": 2},
        {"name": "青鬃马", "type": "mount", "category": "spirit_beast", "desc": "日行千里的灵马", "power": 1},
        {"name": "荆棘蛇", "type": "poison", "category": "spirit_beast", "desc": "鳞如荆棘的毒蛇", "power": 1},
        {"name": "月兔", "type": "auxiliary", "category": "spirit_beast", "desc": "月华灵兔，助人恢复灵力", "power": 1},
        {"name": "石甲犀", "type": "melee", "category": "spirit_beast", "desc": "皮若磐石的灵犀", "power": 2},
        {"name": "夜枭", "type": "scout", "category": "spirit_beast", "desc": "暗夜中无声飞行的灵枭", "power": 1},
        {"name": "碧眼狸", "type": "auxiliary", "category": "spirit_beast", "desc": "碧眼能辨识灵药的灵狸", "power": 1},
        {"name": "沙虫", "type": "earth", "category": "spirit_beast", "desc": "沙漠中穿行的巨型灵虫", "power": 1},
        {"name": "绿翠蜂", "type": "poison", "category": "spirit_beast", "desc": "翠绿灵蜂，毒刺麻痹", "power": 1},
        {"name": "霜角鹿", "type": "ice", "category": "spirit_beast", "desc": "角覆霜冰的灵鹿", "power": 1},
        {"name": "火羽鸡", "type": "fire", "category": "spirit_beast", "desc": "羽毛可燃的灵禽", "power": 1},
        {"name": "双头蛇", "type": "poison", "category": "spirit_beast", "desc": "双头各含不同毒素", "power": 2},
        {"name": "金练蛇", "type": "melee", "category": "spirit_beast", "desc": "通体金鳞的灵蛇，绞杀力强", "power": 2},
        {"name": "灰羽鹤", "type": "wind", "category": "spirit_beast", "desc": "可载人飞行的灵鹤", "power": 1},
        {"name": "火焰蜥蜴", "type": "fire", "category": "spirit_beast", "desc": "能喷射火焰的灵蜥", "power": 1},
        {"name": "寒鸦", "type": "ice", "category": "spirit_beast", "desc": "可释放寒气的乌鸦", "power": 1},
        {"name": "铁影狼", "type": "melee", "category": "spirit_beast", "desc": "速度如影的铁灭狼", "power": 2},
        {"name": "霜牙虎", "type": "ice", "category": "spirit_beast", "desc": "牙齿如霜的白虎", "power": 2},
        {"name": "岩蜂群", "type": "earth", "category": "spirit_beast", "desc": "岩石组成的灵蜂群", "power": 1},
        {"name": "碧灵鱼", "type": "water", "category": "spirit_beast", "desc": "能在水中作战的灵鱼", "power": 1},
        {"name": "天火雀", "type": "fire", "category": "spirit_beast", "desc": "羽毛燃烧的火雀", "power": 2},
        {"name": "风刃螳螂", "type": "wind", "category": "spirit_beast", "desc": "刀足带风刃的巨型螳螂", "power": 2},
        {"name": "灵光蛎蛱", "type": "scout", "category": "spirit_beast", "desc": "夜晚发光照明的灵蛎", "power": 1},
        {"name": "血蜡蛛", "type": "poison", "category": "spirit_beast", "desc": "吐出粘稠毒网的巨蛛", "power": 2},
        {"name": "岩甲犁", "type": "earth", "category": "spirit_beast", "desc": "披岩石外壳的巨型犁牛", "power": 2},
        {"name": "紫霞鹿", "type": "auxiliary", "category": "spirit_beast", "desc": "鹿角可净化毒素的灵鹿", "power": 1},
        {"name": "巨岩蛤蟆", "type": "earth", "category": "spirit_beast", "desc": "身如小山的岩石蛤蟆", "power": 2},
        {"name": "风卷蟠蚣", "type": "wind", "category": "spirit_beast", "desc": "尾刃带风的巨型蟠蚣", "power": 2},
        {"name": "海螺灵", "type": "water", "category": "spirit_beast", "desc": "壳内储水的海中灵物", "power": 1},
        {"name": "火鸽", "type": "fire", "category": "spirit_beast", "desc": "可传递火焰消息的灵鸽", "power": 1},
        {"name": "灵石龟", "type": "earth", "category": "spirit_beast", "desc": "背负灵石的小型灵龟", "power": 1},
        {"name": "天雷鹰", "type": "thunder", "category": "spirit_beast", "desc": "翼间带电的小型灵鹰", "power": 2},
        {"name": "铁背狨", "type": "melee", "category": "spirit_beast", "desc": "背部坚硬如铁的灵狨", "power": 1},
        {"name": "火绛砂蛇", "type": "fire", "category": "spirit_beast", "desc": "栖于火山的绛红毒蛇", "power": 2},
        {"name": "灵玉蝶", "type": "auxiliary", "category": "spirit_beast", "desc": "翼粉可治愈伤口的灵蝶", "power": 1},
        {"name": "金眉蛇", "type": "melee", "category": "spirit_beast", "desc": "金色眉纹的剧毒灵蛇", "power": 2},
        {"name": "织雾蛛", "type": "illusion", "category": "spirit_beast", "desc": "可编织迷雾的灵蛛", "power": 1},
        {"name": "地心蛇", "type": "earth", "category": "spirit_beast", "desc": "在地下穿行的土系灵蛇", "power": 1},
        {"name": "风霈兽", "type": "wind", "category": "spirit_beast", "desc": "能召唤霜风的灵兽", "power": 2},
        {"name": "紫电蟹", "type": "thunder", "category": "spirit_beast", "desc": "螯间放电的灵蟹", "power": 1},
        {"name": "金铃鹿", "type": "auxiliary", "category": "spirit_beast", "desc": "角上铃铛可驱邪的灵鹿", "power": 1},
        {"name": "灰尘鹰", "type": "wind", "category": "spirit_beast", "desc": "灰色羽毛的侦察灵鹰", "power": 1},
    ],
    "mid": [
        {"name": "火麒麟", "type": "fire", "category": "spirit_beast", "desc": "通体烈焰的瑞兽", "power": 4},
        {"name": "天鹰", "type": "wind", "category": "spirit_beast", "desc": "翼展数丈的猛禽，可载人翱翔", "power": 3},
        {"name": "玄冰蛟", "type": "ice", "category": "spirit_beast", "desc": "蛟龙血脉，冰系之力", "power": 3},
        {"name": "九尾灵狐", "type": "illusion", "category": "spirit_beast", "desc": "九尾狐修炼成形，善幻术", "power": 4},
        {"name": "雷翼豹", "type": "thunder", "category": "spirit_beast", "desc": "背生雷翼的灵豹", "power": 3},
        {"name": "碧落凤凰", "type": "fire", "category": "spirit_beast", "desc": "带有凤凰血脉的灵禽", "power": 4},
        {"name": "万年灵龟", "type": "water", "category": "spirit_beast", "desc": "龟壳坚逾玄铁的万年老龟", "power": 3},
        {"name": "狴犴", "type": "melee", "category": "spirit_beast", "desc": "龙生九子之一，勇武善战", "power": 4},
        {"name": "金眼白虎", "type": "melee", "category": "spirit_beast", "desc": "白虎血脉，金眼洞察一切", "power": 4},
        {"name": "墨龙", "type": "water", "category": "spirit_beast", "desc": "黑龙亚种，能力翻江倒海", "power": 4},
        {"name": "千年蝎王", "type": "poison", "category": "spirit_beast", "desc": "千年毒蝎，剧毒无解", "power": 3},
        {"name": "紫电貂", "type": "thunder", "category": "spirit_beast", "desc": "速度极快的雷系灵貂", "power": 3},
        {"name": "岩魔猿", "type": "earth", "category": "spirit_beast", "desc": "身如岩石的巨猿", "power": 3},
        {"name": "幽冥蝶", "type": "poison", "category": "spirit_beast", "desc": "翅粉含幽冥剧毒的灵蝶", "power": 3},
        {"name": "血翼蝙", "type": "melee", "category": "spirit_beast", "desc": "吸血为生的巨型蝙蝠", "power": 3},
        {"name": "裂空鹰", "type": "wind", "category": "spirit_beast", "desc": "速度可撕裂空气的灵鹰", "power": 4},
        {"name": "角木蛟", "type": "water", "category": "spirit_beast", "desc": "蛟龙正宗血脉", "power": 4},
        {"name": "獣豸", "type": "auxiliary", "category": "spirit_beast", "desc": "能辨善恶的神兽", "power": 3},
        {"name": "蓝焰雕", "type": "fire", "category": "spirit_beast", "desc": "喷射蓝色火焰的大雕", "power": 3},
        {"name": "蓄雷羚羊", "type": "thunder", "category": "spirit_beast", "desc": "角中蓄雷的灵羊", "power": 3},
        {"name": "万年巨蛟", "type": "water", "category": "spirit_beast", "desc": "修炼万年的蛟龙", "power": 4},
        {"name": "恶鬼蟀蚣", "type": "poison", "category": "spirit_beast", "desc": "尾刃含剧毒的凶恶蟀蚣", "power": 3},
        {"name": "火翃大鹬", "type": "fire", "category": "spirit_beast", "desc": "巨型火系鹬禽可载人", "power": 3},
        {"name": "寒江江豚", "type": "ice", "category": "spirit_beast", "desc": "冰系灵豚，速度极快", "power": 3},
        {"name": "天罗大螨", "type": "melee", "category": "spirit_beast", "desc": "逾越天罗的巨型蜂群统帅", "power": 4},
        {"name": "暗影豹", "type": "melee", "category": "spirit_beast", "desc": "融于暗影的刺杀灵兽", "power": 3},
        {"name": "天火鹰", "type": "fire", "category": "spirit_beast", "desc": "喷射天火的巨型灵鹰", "power": 4},
        {"name": "五彩孔雀", "type": "illusion", "category": "spirit_beast", "desc": "开屏释放幻彩的灵雀", "power": 3},
        {"name": "玄冰巨鱼", "type": "ice", "category": "spirit_beast", "desc": "寒气逼人的巨型灵鱼", "power": 3},
        {"name": "山岩巨象", "type": "earth", "category": "spirit_beast", "desc": "体如山岩的强大灵象", "power": 4},
    ],
    "high": [
        {"name": "真龙", "type": "water", "category": "spirit_beast", "desc": "真龙现世，呼风唤雨", "power": 5},
        {"name": "凤凰", "type": "fire", "category": "spirit_beast", "desc": "涅槃重生的不死神鸟", "power": 5},
        {"name": "鲲鹏", "type": "wind", "category": "spirit_beast", "desc": "化鹏展翅九万里", "power": 5},
        {"name": "玄武", "type": "water", "category": "spirit_beast", "desc": "四象神兽之一，龟蛇合体", "power": 5},
        {"name": "白泽", "type": "auxiliary", "category": "spirit_beast", "desc": "知万物之情的上古神兽", "power": 5},
        {"name": "饕餮", "type": "melee", "category": "spirit_beast", "desc": "吞噬万物的凶兽", "power": 5},
        {"name": "麒麟", "type": "auxiliary", "category": "spirit_beast", "desc": "祥瑞之兆的仁兽", "power": 5},
        {"name": "九天玄女鸟", "type": "wind", "category": "spirit_beast", "desc": "九天之上的神鸟", "power": 5},
        {"name": "应龙", "type": "thunder", "category": "spirit_beast", "desc": "生有双翼的龙族", "power": 5},
        {"name": "混沌兽", "type": "melee", "category": "spirit_beast", "desc": "混沌未开时的原始凶兽", "power": 5},
        {"name": "毕方", "type": "fire", "category": "spirit_beast", "desc": "独脚神鸟，火焰化身", "power": 5},
        {"name": "烛龙", "type": "fire", "category": "spirit_beast", "desc": "睁眼为昼闭眼为夜的神龙", "power": 5},
        {"name": "九婴", "type": "melee", "category": "spirit_beast", "desc": "上古凶兽九婴，吞噩天地", "power": 5},
        {"name": "天禄鸿雁", "type": "wind", "category": "spirit_beast", "desc": "天禄之上的远古神禽", "power": 5},
        {"name": "金乌", "type": "fire", "category": "spirit_beast", "desc": "太阳中的三足金乌", "power": 5},
        {"name": "天马", "type": "wind", "category": "spirit_beast", "desc": "行于九天之上的神马", "power": 5},
        {"name": "混沌巨鹏", "type": "wind", "category": "spirit_beast", "desc": "混沌定的巨型神鹏", "power": 5},
        {"name": "天狗", "type": "melee", "category": "spirit_beast", "desc": "吞噩日月的神犬", "power": 5},
        {"name": "彼岸花灵", "type": "auxiliary", "category": "spirit_beast", "desc": "彼岸花化形的神奇灵物", "power": 5},
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# ██ ELEMENT POOL (天地精华) — 100+ entries
# ═══════════════════════════════════════════════════════════════════════════════

ELEMENT_POOL = {
    "low": [
        # ── 火类 ──
        {"name": "赤灵火", "type": "fire", "category": "element", "desc": "大地深处的灵火种", "power": 1},
        {"name": "噬骨焰", "type": "fire", "category": "element", "desc": "焚骨灼肉的凶焰", "power": 2},
        {"name": "玄阳火种", "type": "fire", "category": "element", "desc": "含纯阳之力的火焰种子", "power": 2},
        {"name": "地心炎浆", "type": "fire", "category": "element", "desc": "地心深处涌出的灵炎", "power": 1},
        {"name": "碧磷火", "type": "fire", "category": "element", "desc": "阴寒之火，焚烧灵魂", "power": 2},
        # ── 雷类 ──
        {"name": "紫霄雷种", "type": "thunder", "category": "element", "desc": "紫色雷霆的种子", "power": 2},
        {"name": "天罡雷气", "type": "thunder", "category": "element", "desc": "天罡之气凝聚的雷能", "power": 1},
        {"name": "引雷石", "type": "thunder", "category": "element", "desc": "可引天雷的特殊矿石", "power": 1},
        {"name": "电母精华", "type": "thunder", "category": "element", "desc": "蕴含雷电之力的精华", "power": 2},
        # ── 冰/水类 ──
        {"name": "千年寒冰", "type": "ice", "category": "element", "desc": "千年不化的极寒之冰", "power": 1},
        {"name": "玄冰精华", "type": "ice", "category": "element", "desc": "极北之地的冰之精华", "power": 2},
        {"name": "幽泉灵液", "type": "water", "category": "element", "desc": "深潭中的灵力之水", "power": 1},
        {"name": "寒潭之心", "type": "ice", "category": "element", "desc": "寒潭最深处凝结的冰晶", "power": 2},
        {"name": "天河水滴", "type": "water", "category": "element", "desc": "天河落下的一滴灵水", "power": 1},
        # ── 风类 ──
        {"name": "罡风精", "type": "wind", "category": "element", "desc": "高空罡风凝聚的精华", "power": 1},
        {"name": "飓风核心", "type": "wind", "category": "element", "desc": "飓风中心的风之结晶", "power": 2},
        {"name": "灵风珠", "type": "wind", "category": "element", "desc": "封存灵风的珠子", "power": 1},
        # ── 土/木类 ──
        {"name": "灵脉土", "type": "earth", "category": "element", "desc": "灵脉上的精华泥土", "power": 1},
        {"name": "万年灵木", "type": "wood", "category": "element", "desc": "万年灵木的一截枝条", "power": 2},
        {"name": "金刚石髓", "type": "earth", "category": "element", "desc": "最坚硬矿石的精华", "power": 2},
        {"name": "息壤", "type": "earth", "category": "element", "desc": "自行生长的神奇泥土", "power": 1},
        {"name": "太岁灵芝", "type": "wood", "category": "element", "desc": "千年太岁灵芝", "power": 1},
        # ── 光/暗类 ──
        {"name": "月华精", "type": "light", "category": "element", "desc": "月光凝聚的精华", "power": 1},
        {"name": "日精石", "type": "light", "category": "element", "desc": "吸收日光的灵石", "power": 1},
        {"name": "幽冥气", "type": "dark", "category": "element", "desc": "幽冥界溢出的阴气精华", "power": 2},
        {"name": "星辉砂", "type": "light", "category": "element", "desc": "星光凝聚成的细砂", "power": 1},
        {"name": "天地灵乳", "type": "dao", "category": "element", "desc": "天地产生的灵力乳汁", "power": 2},
        {"name": "万年火山岩浆", "type": "fire", "category": "element", "desc": "火山深处的万年灵岩浆", "power": 2},
        {"name": "天外陨铁", "type": "earth", "category": "element", "desc": "来自天外的神奇矿石", "power": 2},
        {"name": "鬼火", "type": "dark", "category": "element", "desc": "怖鬼火绿光幽幽", "power": 1},
        {"name": "三尾狐火", "type": "fire", "category": "element", "desc": "狐火精华，幻火之力", "power": 1},
        {"name": "清泉石", "type": "water", "category": "element", "desc": "在含灵泉之力的石头", "power": 1},
        {"name": "地火核", "type": "fire", "category": "element", "desc": "地心火焰的核心结晶", "power": 2},
        {"name": "寒铁精华", "type": "ice", "category": "element", "desc": "极寒之地凝结的铁精", "power": 1},
        {"name": "灵木种子", "type": "wood", "category": "element", "desc": "蕴含生命之力的古木种子", "power": 1},
        {"name": "蓝雷精", "type": "thunder", "category": "element", "desc": "蓝色雷电凝结的精华", "power": 2},
        {"name": "黄泉之气", "type": "dark", "category": "element", "desc": "黄泉路上的死亡之气", "power": 1},
        {"name": "威压石", "type": "earth", "category": "element", "desc": "含有威压之力的天然矿石", "power": 1},
        {"name": "风灵珠", "type": "wind", "category": "element", "desc": "缚锁一缕灵风的珠子", "power": 1},
        {"name": "火山灵石", "type": "fire", "category": "element", "desc": "火山口产出的灵石", "power": 1},
        {"name": "深海寒珠", "type": "ice", "category": "element", "desc": "深海压力下凝结的寒珠", "power": 2},
        {"name": "灵泉玉液", "type": "water", "category": "element", "desc": "灵泉最纯的玉质灵液", "power": 2},
        {"name": "风晰石", "type": "wind", "category": "element", "desc": "蜜封狂风的天然灵石", "power": 2},
        {"name": "青木灵汁", "type": "wood", "category": "element", "desc": "古树流出的灵力汁液", "power": 1},
        {"name": "龙脊沙", "type": "earth", "category": "element", "desc": "龙脉节点产出的灵沙", "power": 2},
        {"name": "冤魂之火", "type": "dark", "category": "element", "desc": "冤气凝结的幽火", "power": 2},
        {"name": "天霆之水", "type": "water", "category": "element", "desc": "雨后天霆中聚集的灵水", "power": 1},
        {"name": "冰魄石", "type": "ice", "category": "element", "desc": "极寒之地的万年冰晶石", "power": 2},
        {"name": "妖气精华", "type": "dark", "category": "element", "desc": "精纯的妖修之气精华", "power": 1},
        {"name": "晶火石", "type": "fire", "category": "element", "desc": "内含火焰的灵晶石", "power": 1},
    ],
    "mid": [
        # ── 火类 ──
        {"name": "三昧真火", "type": "fire", "category": "element", "desc": "燃烧万物的天地真火", "power": 4},
        {"name": "九幽冥火", "type": "fire", "category": "element", "desc": "九幽之下的毁灭之火", "power": 4},
        {"name": "南明离火", "type": "fire", "category": "element", "desc": "天地四大真火之一", "power": 3},
        {"name": "纯阳真炎", "type": "fire", "category": "element", "desc": "至阳至纯的天地真炎", "power": 3},
        {"name": "业火莲华", "type": "fire", "category": "element", "desc": "业火凝聚成的莲花", "power": 4},
        # ── 雷类 ──
        {"name": "紫霄神雷", "type": "thunder", "category": "element", "desc": "紫霄宫降下的天雷", "power": 4},
        {"name": "九天应雷", "type": "thunder", "category": "element", "desc": "九天之上的神雷精华", "power": 3},
        {"name": "雷劫残余", "type": "thunder", "category": "element", "desc": "天劫散去后残留的雷力", "power": 3},
        {"name": "五色神雷", "type": "thunder", "category": "element", "desc": "五行汇聚的五色雷霆", "power": 4},
        # ── 冰/水类 ──
        {"name": "太阴玄冰", "type": "ice", "category": "element", "desc": "太阴星辰凝聚的极寒之冰", "power": 4},
        {"name": "天一真水", "type": "water", "category": "element", "desc": "天一生水的原始之水", "power": 3},
        {"name": "玄霜精", "type": "ice", "category": "element", "desc": "玄天之霜凝结的精华", "power": 3},
        {"name": "弱水一滴", "type": "water", "category": "element", "desc": "鸿毛不浮的弱水精华", "power": 4},
        # ── 其他 ──
        {"name": "先天五行精", "type": "dao", "category": "element", "desc": "先天五行凝聚的精华", "power": 4},
        {"name": "先天罡气", "type": "wind", "category": "element", "desc": "先天级别的罡风之力", "power": 3},
        {"name": "九天息壤", "type": "earth", "category": "element", "desc": "九天之上的灵土精华", "power": 3},
        {"name": "混沌灵液", "type": "dao", "category": "element", "desc": "混沌未开时的灵液", "power": 4},
        {"name": "太阳真火", "type": "fire", "category": "element", "desc": "太阳星辰核心的真火", "power": 4},
        {"name": "天地玄黄", "type": "dao", "category": "element", "desc": "天地初开时的精华之气", "power": 3},
        {"name": "造化精华", "type": "dao", "category": "element", "desc": "蕴含造化之力的精元", "power": 4},
        {"name": "混沌之气", "type": "dao", "category": "element", "desc": "混沌世界泄露的原始之气", "power": 4},
        {"name": "天地玄黄气", "type": "dao", "category": "element", "desc": "天玄地黄的混合灵气", "power": 3},
        {"name": "太阴玄冰", "type": "ice", "category": "element", "desc": "太阴星辰凝聚的极寒之冰", "power": 4},
        {"name": "大地之灵", "type": "earth", "category": "element", "desc": "大地核心的原始灵力", "power": 3},
        {"name": "深渊冥水", "type": "water", "category": "element", "desc": "深渊之下的幽冥之水", "power": 3},
        {"name": "三界雷精", "type": "thunder", "category": "element", "desc": "天地人三界雷力融合", "power": 4},
        {"name": "古树精华", "type": "wood", "category": "element", "desc": "万年古树的生命精华", "power": 3},
        {"name": "真阳精火", "type": "fire", "category": "element", "desc": "至阳精纯的天火", "power": 3},
        {"name": "玲珑光华", "type": "light", "category": "element", "desc": "九天之上降下的神圣光华", "power": 4},
        {"name": "九幽阴火", "type": "dark", "category": "element", "desc": "九幽之下的阴冷之火", "power": 3},
        {"name": "宇宙尘埃", "type": "dao", "category": "element", "desc": "星辰毁灭后的宇宙精华", "power": 4},
        {"name": "血月精华", "type": "dark", "category": "element", "desc": "血月夜降下的妖异精华", "power": 3},
        {"name": "龙气", "type": "dao", "category": "element", "desc": "天地龙脉中流淌的灵气", "power": 3},
        {"name": "天池灵液", "type": "water", "category": "element", "desc": "天池中产生的纯净灵液", "power": 3},
        {"name": "火精火核", "type": "fire", "category": "element", "desc": "火精灭后残留的火核", "power": 4},
        {"name": "雷岩", "type": "thunder", "category": "element", "desc": "遭受雷击后蓄雷的岩石", "power": 3},
        {"name": "天远金精", "type": "earth", "category": "element", "desc": "极深矿脉的金属精华", "power": 3},
    ],
    "high": [
        {"name": "混沌之火", "type": "fire", "category": "element", "desc": "混沌初开时的第一缕火焰", "power": 5},
        {"name": "鸿蒙紫气", "type": "dao", "category": "element", "desc": "鸿蒙紫气，成圣之基", "power": 5},
        {"name": "天道雷罚", "type": "thunder", "category": "element", "desc": "天道降罚的终极雷霆", "power": 5},
        {"name": "造化之水", "type": "water", "category": "element", "desc": "可育万物的造化灵水", "power": 5},
        {"name": "先天一气", "type": "dao", "category": "element", "desc": "先天第一缕真气", "power": 5},
        {"name": "太初之木", "type": "wood", "category": "element", "desc": "太初时代的生命之木精华", "power": 5},
        {"name": "虚无之风", "type": "wind", "category": "element", "desc": "虚无中诞生的原始风力", "power": 5},
        {"name": "永恒寒冰", "type": "ice", "category": "element", "desc": "永恒不灭的绝对零度之冰", "power": 5},
        {"name": "天地本源", "type": "dao", "category": "element", "desc": "天地万物的最初本源", "power": 5},
        {"name": "劫雷本源", "type": "thunder", "category": "element", "desc": "天劫之力的终极本源", "power": 5},
        {"name": "涅槃圣火", "type": "fire", "category": "element", "desc": "浴火涅槃的不灭圣火", "power": 5},
        {"name": "时光之砂", "type": "dao", "category": "element", "desc": "凝固时光的远古砂粒", "power": 5},
        {"name": "大日精火", "type": "fire", "category": "element", "desc": "太阳核心的最纯之火", "power": 5},
        {"name": "太初木精", "type": "wood", "category": "element", "desc": "太初时代的原始木之精", "power": 5},
        {"name": "太极之力", "type": "dao", "category": "element", "desc": "阴阳太极的本源之力", "power": 5},
        {"name": "混沌之土", "type": "earth", "category": "element", "desc": "混沌初开时的原始之土", "power": 5},
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# ██ ALL POOLS COMBINED
# ═══════════════════════════════════════════════════════════════════════════════

ALL_POOLS = {
    "technique": TECHNIQUE_POOL,
    "treasure": TREASURE_POOL,
    "secret_art": SECRET_ART_POOL,
    "puppet": PUPPET_POOL,
    "spirit_beast": SPIRIT_BEAST_POOL,
    "element": ELEMENT_POOL,
}


# ── Public API ────────────────────────────────────────────────────────────────

def sample_acquisition_items(state: "GameState", count: int = 3) -> list[dict]:
    """Sample random items from ALL pools based on current realm.

    Filters out items the player already owns. Returns a diverse mix
    across all 6 categories.

    Args:
        state: Current game state (for realm and existing repertoire)
        count: Number of items to sample (default 3)

    Returns:
        List of item dicts from the combined pools
    """
    tier = get_tier_for_realm(state.realm)

    # Combine all pools for this tier
    pool = []
    for category_pool in ALL_POOLS.values():
        pool.extend(category_pool.get(tier, []))

    # Exclude already owned items
    owned_names = {r.get("name", "") for r in getattr(state, "combat_repertoire", [])}
    available = [x for x in pool if x["name"] not in owned_names]

    if not available:
        return []

    return random.sample(available, min(count, len(available)))


def get_tier_for_realm(realm: int) -> str:
    """Get pool tier string for a given realm."""
    if realm <= 2:
        return "low"
    elif realm <= 4:
        return "mid"
    return "high"


def get_pool_stats() -> dict:
    """Return counts for each pool and tier (debugging/info)."""
    stats = {}
    for name, pool in ALL_POOLS.items():
        stats[name] = {tier: len(items) for tier, items in pool.items()}
        stats[name]["total"] = sum(stats[name].values())
    stats["grand_total"] = sum(s["total"] for s in stats.values())
    return stats
