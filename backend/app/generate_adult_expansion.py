"""Generate expanded adult/romance events for higher cultivation realms."""
import json
import os

EVENTS_DIR = os.path.join(os.path.dirname(__file__), "events")

# ============================================================
# 练气层 (min_realm=1) — 初入修仙, 灵气初感, 基础双修
# ============================================================
QI_REFINING_EVENTS = [
    # Male (5)
    {
        "id": "adt_m_225",
        "text": "你与同门师姐在灵泉中双修，灵力交融。",
        "expanded_text": "灵泉温热如玉，氤氲的水汽中她的肩头隐约可见。她伸手覆上你的手背：「师弟，我引导灵气，你随我走。」灵力自她掌心渡入你体内，温柔而绵密。你感到丹田处有一股暖流被她的灵气牵引着旋转。她贴近你耳畔低语时，你闻到她发间淡淡的灵草香。那一夜灵泉水波不兴，两人灵力却如潮汐般彼此交融了无数回。",
        "conditions": {"min_realm": 1, "max_realm": 2, "min_age": 18, "gender": "male"},
        "effects": {"cultivation": 15, "comprehension": 1},
        "weight": 8
    },
    {
        "id": "adt_m_226",
        "text": "一名女修以采补之术接近你，你险些失了道心。",
        "expanded_text": "她生得极美，一袭薄纱若隐若现。她说是路过你的洞府借宿一夜——可入夜后她的手便不安分了。你感到体内灵力被一股奇异的吸力牵引，正朝她涌去。你猛地咬破舌尖，鲜血的痛楚让你回过神来。你将她推开时她嗤笑一声化作一道青烟消散。次日你发现修为竟折损了些许——但道心却比昨日更坚了。",
        "conditions": {"min_realm": 1, "max_realm": 2, "min_age": 18, "gender": "male"},
        "effects": {"cultivation": -5, "willpower": 2},
        "weight": 6
    },
    {
        "id": "adt_m_227",
        "text": "你与一位散修女子结为道侣，夜间互相引导灵气。",
        "expanded_text": "她不是宗门弟子，孤身一人走江湖。你们在一场兽潮后相识，从此再没分开。每晚她盘膝坐在你身后，将手贴在你背心，灵气像一条细溪流缓缓淌入你的经脉。你也回渡给她——两人灵力相融之时，你感到一种从未有过的安宁。她有时会伏在你肩上浅浅睡去，你便维持着引导灵气的姿势直到天明。",
        "conditions": {"min_realm": 1, "max_realm": 3, "min_age": 20, "gender": "male"},
        "effects": {"cultivation": 20, "willpower": 1},
        "weight": 8
    },
    {
        "id": "adt_m_228",
        "text": "你在修炼功法时意外引动情欲之火，险些走火入魔。",
        "expanded_text": "那本功法是你在坊市中淘来的残卷——修炼到第七层时，你忽然感到体内升起一股难以抑制的燥热。你知道这是走火入魔的前兆。你拼命运转心法压制，额上的汗一滴滴落在石地上。那一夜你与心魔缠斗至天明。破晓时分燥热终于退去——你浑身虚脱地倒在地上，却发现神识清明了许多。",
        "conditions": {"min_realm": 1, "max_realm": 2, "min_age": 16, "gender": "male"},
        "effects": {"cultivation": -10, "willpower": 2, "comprehension": 1},
        "weight": 6
    },
    {
        "id": "adt_m_229",
        "text": "你与邻洞的女修互生情愫，在月圆之夜共修阴阳之法。",
        "expanded_text": "她住在你隔壁的洞府，时常来借灵石和丹药。一来二去你们便熟了。月圆之夜她红着脸说有一门阴阳功法需要两人同修——你心跳如擂鼓般答应了。月光透过洞府的裂缝洒在你们身上，灵力在两人之间如月华般流转。她闭着眼轻轻靠在你胸前时，你觉得这条修仙路忽然不那么孤独了。",
        "conditions": {"min_realm": 1, "max_realm": 2, "min_age": 18, "gender": "male"},
        "effects": {"cultivation": 15, "fortune": 1},
        "weight": 8
    },
    # Female (5)
    {
        "id": "adt_f_225",
        "text": "你与同门师兄在丹房中共修，灵力相融之间情愫暗生。",
        "expanded_text": "丹房中丹火微明，他站在你身后为你护法。你全神贯注地炼丹，却忽然感到他的灵力温热地覆上了你的后背——那是在帮你疏通经脉中的一处淤塞。你微微颤了一下。他低声说「别动」，语气里带着一丝不易察觉的紧张。那一夜你们虽未越雷池——但他收回灵力时指尖划过你颈侧，你的心跳却骤然快了三分。",
        "conditions": {"min_realm": 1, "max_realm": 2, "min_age": 18, "gender": "female"},
        "effects": {"cultivation": 12, "comprehension": 1},
        "weight": 8
    },
    {
        "id": "adt_f_226",
        "text": "一名男修对你施展魅惑之术，你识破后反将他制服。",
        "expanded_text": "他自称是路过的游方散修——相貌堂堂，言语间尽是体贴。可你在他眼中看到了一丝不自然的紫光——那是魅惑术的痕迹。你假装中术，靠近他——在他得意放松的一瞬，你一掌拍碎了他的护体灵光。他趴在地上求饶时你才看清：他不过是个靠采补为生的三流修士。你没杀他，只废了他一成修为以作惩戒。",
        "conditions": {"min_realm": 1, "max_realm": 2, "min_age": 18, "gender": "female"},
        "effects": {"willpower": 2, "cultivation": 5},
        "weight": 6
    },
    {
        "id": "adt_f_227",
        "text": "你与一位剑修结为道侣，他以剑意为你温养经脉。",
        "expanded_text": "他是宗门里最沉默的剑修——平日不苟言笑。可私下里他会用剑指轻轻点在你的穴位上，以精纯的剑意为你梳理经脉。那感觉像一条清冽的溪流穿过体内——微微刺痛却极舒适。你咬着唇不让自己出声时他会微微勾起嘴角。你这才知道，他那副冰冷面孔下，藏着这样温柔的一面。",
        "conditions": {"min_realm": 1, "max_realm": 3, "min_age": 18, "gender": "female"},
        "effects": {"cultivation": 18, "constitution": 1},
        "weight": 8
    },
    {
        "id": "adt_f_228",
        "text": "你偶遇一位受伤的男修，以双修之法助他疗伤。",
        "expanded_text": "他倒在你洞府前——浑身是血，经脉尽断。你犹豫再三，终究不忍见死不救。古籍中记载的那道双修疗伤之法是最后的办法。你将灵力渡入他体内时感到他的经脉像干涸的河床——你的灵气便是填满它的水。他痛苦地抓紧你的手腕，可你没有退缩。天明时他终于脱险。他看着你红着脸说了声谢。你转过头不敢看他。",
        "conditions": {"min_realm": 1, "max_realm": 2, "min_age": 18, "gender": "female"},
        "effects": {"cultivation": -5, "fortune": 1, "charisma": 1},
        "weight": 7
    },
    {
        "id": "adt_f_229",
        "text": "你在灵泉疗伤时被同门撞见，竟因此结下一段缘。",
        "expanded_text": "灵泉中你正闭目养伤——忽听得一声惊呼。你睁眼，那个平日里总故意找你麻烦的师兄正呆站在泉边。你怒而掷出一道水刃，他慌忙后退却滑了一跤。你气得发抖却也无法起身——伤势未愈。他涨红着脸背过身去，半晌才闷声说：「……我帮你守着。」他在泉边坐了整整一夜。次日你们谁也没提这件事——可从那以后他再没找过你麻烦。",
        "conditions": {"min_realm": 1, "max_realm": 2, "min_age": 16, "gender": "female"},
        "effects": {"cultivation": 10, "charisma": 1},
        "weight": 8
    },
]

# ============================================================
# 金丹层 (min_realm=3) — 神识初成, 灵力浓郁, 双修有实质力量交换
# ============================================================
GOLDEN_CORE_EVENTS = [
    # Male (3)
    {
        "id": "adt_m_230",
        "text": "你与道侣以金丹互照之法共修，彼此丹田共鸣。",
        "expanded_text": "她盘膝坐在你对面，额间的神识之光与你的交织成一道金桥。你们各自的金丹在丹田中同时震颤——那是「金丹互照」的征兆。灵力循着那道桥在两人体内周天运转了三十六圈。每一圈都让你感到她的灵力越来越契合你的经脉。她微微喘息时，金丹表面竟多了一层细密的灵纹——那是道侣之间才有的「共鸣纹」。",
        "conditions": {"min_realm": 3, "max_realm": 4, "min_age": 40, "gender": "male"},
        "effects": {"cultivation": 40, "comprehension": 2},
        "weight": 7
    },
    {
        "id": "adt_m_231",
        "text": "一位化形的狐妖主动以身相许，要与你双修百日。",
        "expanded_text": "她现身时月光正好——一袭白裙，九尾在身后若隐若现。「我已修行三千年，需一位金丹修士助我最后一步。」她跪在你面前，坦然至极。百日双修——你知道这对你而言也是大机缘。她的妖力与你的灵力本不相容，可在每一次交融中那种排斥感都在消减。第九十九日你们的灵力终于毫无阻碍地流转在一起。她化形时的最后一根尾巴在月光下缓缓褪去。",
        "conditions": {"min_realm": 3, "max_realm": 4, "min_age": 50, "gender": "male"},
        "effects": {"cultivation": 50, "fortune": 2, "lifespan": 3},
        "weight": 5
    },
    {
        "id": "adt_m_232",
        "text": "你偷习禁术「九转还阳功」，需采阴补阳方能成就。",
        "expanded_text": "这门功法你犹豫了十年才下定决心修炼。「采阴补阳」说起来不好听——但其实是双方灵力互补的至高法门。你与道侣商议后她默然点头。第一转时你只觉体内多了一股至柔至阴的灵力在洗涤你的金丹；到第三转时你的金丹已变得温润如玉。她则从你体内得了至刚至阳之气，气色一日好过一日。九转功成那夜，你们的修为各自精进了一大截。",
        "conditions": {"min_realm": 3, "max_realm": 5, "min_age": 60, "gender": "male"},
        "effects": {"cultivation": 60, "willpower": 1, "constitution": 1},
        "weight": 5
    },
    # Female (3)
    {
        "id": "adt_f_230",
        "text": "你与道侣以心神交融之法双修，神识在对方识海中共舞。",
        "expanded_text": "金丹期的神识已足够强大到触碰另一人的识海。他闭目引导你的神识探入他的内心——你看见了他的记忆：少年时的孤苦、修道路上的坎坷、以及……他第一次看见你时心跳加速的那一刻。你的脸一下红了。他的神识也同时进入你的识海——你知道他也看见了你的一切。那一夜两人的神识如两尾游鱼般在彼此识海中缠绕嬉戏，是最深处的坦诚。",
        "conditions": {"min_realm": 3, "max_realm": 4, "min_age": 40, "gender": "female"},
        "effects": {"cultivation": 35, "comprehension": 2, "willpower": 1},
        "weight": 7
    },
    {
        "id": "adt_f_231",
        "text": "你以双修之法助道侣突破瓶颈，自身修为亦有精进。",
        "expanded_text": "他卡在金丹中期整整三十年——关隘如铜墙铁壁。你翻遍古籍终于找到一法：以双修之时灵力交汇的冲击波为他冲关。那一夜你将自己的灵力毫无保留地灌注入他体内。他的金丹裂开又合拢，裂开又合拢——第三次时终于「咔」的一声，隐隐有光从裂缝中透出。他突破了。你精疲力竭地倒在他怀中时，发现自己的金丹也多了一道灵纹。",
        "conditions": {"min_realm": 3, "max_realm": 4, "min_age": 50, "gender": "female"},
        "effects": {"cultivation": 45, "constitution": 1},
        "weight": 6
    },
    {
        "id": "adt_f_232",
        "text": "你修炼玄阴功法，需至阳之体为你淬炼丹田。",
        "expanded_text": "玄阴功法修至第六重便陷入瓶颈——需至阳之体的灵力为你淬炼丹田中过盛的阴气。你的道侣是天生纯阳之体，这让他成为最佳人选。他的灵力如烈日般灌入你体内，灼得你浑身发颤。可那些多余的阴气在纯阳之力的炙烤下一缕缕消散。你咬着他的肩忍住那一阵阵灼痛——直到丹田中阴阳终于归于平衡。他心疼地抱紧你，一夜未敢松手。",
        "conditions": {"min_realm": 3, "max_realm": 5, "min_age": 50, "gender": "female"},
        "effects": {"cultivation": 55, "constitution": 2},
        "weight": 5
    },
]

# ============================================================
# 元婴层 (min_realm=4) — 元婴化形, 灵魂层次的亲密, 法则感悟
# ============================================================
NASCENT_SOUL_EVENTS = [
    # Male (10)
    {
        "id": "adt_m_233",
        "text": "你与道侣的元婴在识海中相拥，神魂层面的交融令你悟道。",
        "expanded_text": "元婴期的修士已能让元婴脱体。你与她各自催动元婴离体——两道三寸小人在你们眉心之间相会。她的元婴着白衣，你的元婴着青袍。两道元婴轻轻相拥时，你感到一种远超肉身接触的亲密——那是灵魂层面的触碰。你看见了她眼中蕴含的大道本源。悟道之感如电流般贯穿你全身。",
        "conditions": {"min_realm": 4, "max_realm": 5, "min_age": 80, "gender": "male"},
        "effects": {"cultivation": 80, "comprehension": 3},
        "weight": 7
    },
    {
        "id": "adt_m_234",
        "text": "你在秘境中遭遇一名女修，以双修渡过死劫。",
        "expanded_text": "秘境中毒雾侵体，你的元婴已裂开三道口子。她也好不到哪去——浑身灵力紊乱。「双修……是唯一的活路。」她咬着牙说。你们没有别的选择。灵力交融之际，两人的伤势在彼此灵力的滋养下缓缓弥合。她的元婴中有一股清泉般的灵力缝合了你的裂痕。天明时你们在秘境出口相对而坐——劫后余生，谁也没说话。",
        "conditions": {"min_realm": 4, "max_realm": 5, "min_age": 80, "gender": "male"},
        "effects": {"cultivation": 60, "constitution": 2, "willpower": 1},
        "weight": 6
    },
    {
        "id": "adt_m_235",
        "text": "你的道侣以元婴喂养你的本命法器，你愧疚万分。",
        "expanded_text": "你的本命法器在一场恶战中碎成三截——修复它需要元婴之力灌注百日。你还在犹豫时她已催动元婴将灵力注入残剑之中。你心疼得发抖：元婴灌注会让她折损十年修为。可她只是笑着摇头：「你的命比我的修为重要。」百日后残剑重铸——剑身上多了一道她的元婴灵纹。你将剑抵在额前发誓：此生不负她。",
        "conditions": {"min_realm": 4, "max_realm": 5, "min_age": 100, "gender": "male"},
        "effects": {"cultivation": 30, "willpower": 3, "lifespan": -3},
        "weight": 5
    },
    {
        "id": "adt_m_236",
        "text": "你以元婴之力为道侣渡过心魔劫，两人从此神魂相连。",
        "expanded_text": "她的心魔劫来得毫无预兆——一瞬间她的眼瞳变得漆黑如墨。你毫不犹豫地将元婴投入她的识海，与她体内的心魔正面交锋。心魔化作无数虚影——有她年少时的创伤，有修途中的恐惧。你一一斩碎它们。当最后一道心魔碎裂时你累得几乎元婴崩散。她醒来抱住你失声痛哭。从那夜起你们的神识再也分不开——如同一体。",
        "conditions": {"min_realm": 4, "max_realm": 5, "min_age": 100, "gender": "male"},
        "effects": {"cultivation": 70, "willpower": 2, "comprehension": 1},
        "weight": 6
    },
    {
        "id": "adt_m_237",
        "text": "你与一位元婴期女修论道至深夜，最终以双修印证各自所悟。",
        "expanded_text": "她是别宗的元婴长老——与你论道论了三天三夜。到最后你们发现各自对「道」的感悟恰好互补。她领悟的是「水之道」——至柔至静；你领悟的是「火之道」——至刚至烈。你们谁也没说话便各自催动元婴——水火交融之际你们同时大笑。原来道在阴阳——独修只得其半。",
        "conditions": {"min_realm": 4, "max_realm": 5, "min_age": 100, "gender": "male"},
        "effects": {"cultivation": 90, "comprehension": 3},
        "weight": 6
    },
    {
        "id": "adt_m_238",
        "text": "你沉迷于一位魔修的双修邀约，差点走入魔道。",
        "expanded_text": "她来自魔宗——一双桃花眼里全是勾引。她的魔功需要以正道修士的元婴之力滋养——可她给你的回报也极为可观：每一次双修后你的修为都会猛涨一截。你明知这是饮鸩止渴——可那种突破的快感让人欲罢不能。直到第七次你发现自己的元婴表面开始凝聚黑气。你惊出一身冷汗，当夜便斩断一切联系。",
        "conditions": {"min_realm": 4, "max_realm": 5, "min_age": 80, "gender": "male"},
        "effects": {"cultivation": 50, "willpower": -1, "fortune": -1},
        "weight": 5
    },
    {
        "id": "adt_m_239",
        "text": "你的道侣以命魂为你挡了一劫，你以双修之法为她续命。",
        "expanded_text": "那道杀招本是冲你来的——她挡在前面时你只来得及喊出半个字。她的元婴裂了，命魂摇摇欲坠。你把她抱回洞府，疯了一般翻遍所有功法。最后那道禁术写得明白：以元婴相融之法可渡命魂——代价是你折寿五百年。你没犹豫。那一夜你将自己半颗元婴都灌入了她的识海。天亮时她睁开眼——你已老了五百岁的容貌。她哭了。",
        "conditions": {"min_realm": 4, "max_realm": 5, "min_age": 100, "gender": "male"},
        "effects": {"cultivation": -30, "lifespan": -5, "willpower": 3},
        "weight": 4
    },
    {
        "id": "adt_m_240",
        "text": "你与道侣在雷池中以灵力护持彼此，共渡天雷。",
        "expanded_text": "雷池中的天雷足以劈碎元婴——你们却偏偏选在这里双修。「以雷炼体、以情固道」——古籍中这么写。你们背靠背坐在雷池中央，灵力在两人间形成一道光壁。雷劈下时你咬紧牙关将灵力推向她那一侧；她也在同一刻将灵力推向你。你们互相为对方挡了半道雷。池中雷光散尽时你们浑身焦黑——却相视而笑。",
        "conditions": {"min_realm": 4, "max_realm": 5, "min_age": 80, "gender": "male"},
        "effects": {"cultivation": 75, "constitution": 2, "willpower": 1},
        "weight": 6
    },
    {
        "id": "adt_m_241",
        "text": "你以梦境之术与道侣在梦中重温初遇，恍如隔世。",
        "expanded_text": "元婴期的你已能以神识构建梦境。你为她造了一场梦——梦里是你们初遇那一日的场景。她年轻时的模样出现在梦中街市上，回头对你笑了笑。你也恢复了少年模样——跟在她身后手足无措。梦中的你们重新走了一遍当年的路：买糖葫芦、逛灯会、在桥上看月亮。醒来时她枕在你臂弯里，脸上有泪也有笑。",
        "conditions": {"min_realm": 4, "max_realm": 5, "min_age": 120, "gender": "male"},
        "effects": {"cultivation": 20, "willpower": 2, "charisma": 1},
        "weight": 7
    },
    {
        "id": "adt_m_242",
        "text": "你闭关时道侣以身为炉为你温养元婴，你感激涕零。",
        "expanded_text": "闭关三年——你的元婴在冲击瓶颈时出了岔子，险些碎裂。她在关外感知到你的异常，不顾禁制闯了进来。她将自己的灵力全数灌入你体内稳住摇摇欲碎的元婴。整整七日她未曾阖眼——灵力耗尽又恢复，恢复又耗尽。你醒来时她已瘦得脱了相。你说不出一个字，只是抱住她哭了很久。",
        "conditions": {"min_realm": 4, "max_realm": 5, "min_age": 100, "gender": "male"},
        "effects": {"cultivation": 65, "constitution": 1, "willpower": 2},
        "weight": 6
    },
    # Female (10)
    {
        "id": "adt_f_233",
        "text": "你与道侣元婴相拥，灵魂交融之时你窥见了他的道。",
        "expanded_text": "他的元婴自眉心飞出时你有一瞬的恍惚——那三寸小人竟与他年轻时一模一样。你的元婴亦飘然而出，两道小人在虚空中缓缓靠近。当你的元婴触碰到他的那一刻——你看见了。你看见了他修了五百年的道：那是一条极致孤独的路。而在那条路的尽头，站着你。你的泪从元婴的眼中落下，化作金色的光点融入他体内。",
        "conditions": {"min_realm": 4, "max_realm": 5, "min_age": 80, "gender": "female"},
        "effects": {"cultivation": 85, "comprehension": 3},
        "weight": 7
    },
    {
        "id": "adt_f_234",
        "text": "你以双修之法助道侣凝聚元婴，自身也因此获益。",
        "expanded_text": "他卡在元婴凝聚的最后一步已有百年。你知道一法——以你的元婴之力为引，助他凝聚。那一夜你将元婴脱体，化作一缕金光没入他的丹田。你看见他的金丹在你元婴之力的催化下缓缓裂开——一道婴儿般的灵体从中升起。他的元婴睁开眼的第一刻便朝你的元婴伸出了手。你笑了。",
        "conditions": {"min_realm": 4, "max_realm": 5, "min_age": 100, "gender": "female"},
        "effects": {"cultivation": 70, "comprehension": 2},
        "weight": 6
    },
    {
        "id": "adt_f_235",
        "text": "你与一位元婴老祖论道，以阴阳互补之法共悟天道。",
        "expanded_text": "他已活了八百年——胡须皆白，可眼神清亮得像少年。你们论道论了七天七夜，最后他说：「我缺一味阴。」你看了他一眼：「我缺一味阳。」于是你们在星空下以最古老的双修之法互补阴阳。他的道如苍松——沉稳而深远；你的道如流水——灵动而变幻。阴阳交汇之际你们同时悟到了一丝天道之意。",
        "conditions": {"min_realm": 4, "max_realm": 5, "min_age": 100, "gender": "female"},
        "effects": {"cultivation": 95, "comprehension": 3},
        "weight": 5
    },
    {
        "id": "adt_f_236",
        "text": "你的道侣以神魂为你挡下心魔，你以双修为他疗伤。",
        "expanded_text": "心魔劫来时你已做好了独面的准备——可他的元婴却在那一刻闯入你的识海。你看着他在你的心魔群中左冲右突，神魂一道道碎裂又拼回。你哭着喊他出去——他不听。等心魔散尽时他的元婴已裂了七道口子。你花了三个月用自己的灵力一道道修补他的元婴。每一夜他都疼得浑身发抖，你只能抱紧他，不断地渡灵力过去。",
        "conditions": {"min_realm": 4, "max_realm": 5, "min_age": 100, "gender": "female"},
        "effects": {"cultivation": 50, "willpower": 3, "lifespan": -2},
        "weight": 5
    },
    {
        "id": "adt_f_237",
        "text": "你与道侣在万年寒冰之下双修，以情念融化坚冰。",
        "expanded_text": "万年寒冰之下封印着一株天材地宝——需阴阳双修之力方能融化封印。你们盘膝于冰面之上，灵力交融生出热量。寒冰一层层消融——冰水顺着你们的衣袍流下。他的体温透过灵力传入你体内——温暖得像冬日的火炉。当最后一层冰融化时那株灵药绽出的光芒照亮了整个冰洞。你靠在他肩上笑了。",
        "conditions": {"min_realm": 4, "max_realm": 5, "min_age": 80, "gender": "female"},
        "effects": {"cultivation": 80, "fortune": 2, "constitution": 1},
        "weight": 6
    },
    {
        "id": "adt_f_238",
        "text": "你修炼太阴真经，需至阳元婴之力为你开脉。",
        "expanded_text": "太阴真经第九重需开通「太阴命脉」——这条隐脉只有至阳之力能为你冲开。他将元婴脱体注入你的经脉时你感到一阵灼烈的阳气在体内横冲直撞。你咬紧牙关忍住——他的元婴精准地找到了那条隐脉，一寸寸地将它冲开。痛极之后是前所未有的通畅感——灵力运转比从前快了三倍。你喘息着握住他的手：「成了。」",
        "conditions": {"min_realm": 4, "max_realm": 5, "min_age": 80, "gender": "female"},
        "effects": {"cultivation": 75, "constitution": 2},
        "weight": 6
    },
    {
        "id": "adt_f_239",
        "text": "一位魔修以情惑之术困住你，你的道侣拼死救你脱险。",
        "expanded_text": "那名魔修以一道「情丝」捆住了你的元婴——你动弹不得。他的魔功每多缠一圈，你便多被抽走一分灵力。你的道侣赶到时你已奄奄一息。他发疯般斩断那些情丝——每斩一道自己也要受一道反噬。等他将你救出来时他的双手已经血肉模糊。他跪在地上抱住你的头低声说：「我来了。」你在他怀里哭得发不出声。",
        "conditions": {"min_realm": 4, "max_realm": 5, "min_age": 80, "gender": "female"},
        "effects": {"cultivation": -20, "willpower": 3, "fortune": 1},
        "weight": 5
    },
    {
        "id": "adt_f_240",
        "text": "你在渡劫前夜与道侣相守，以灵力为彼此温养元婴。",
        "expanded_text": "明日便要冲击瓶颈——成则元婴大成，败则前功尽弃。这一夜他什么也没说，只是将你拉入怀中。你们的元婴同时脱体，在识海中相对而坐。他的元婴握着你的元婴的手——灵力在两个小人之间缓缓流转。那不是双修——那是两个灵魂在互相说：「明天不管怎样，我都在。」你安心地闭上眼，一夜无梦。",
        "conditions": {"min_realm": 4, "max_realm": 5, "min_age": 100, "gender": "female"},
        "effects": {"cultivation": 40, "willpower": 2, "comprehension": 1},
        "weight": 7
    },
    {
        "id": "adt_f_241",
        "text": "你与道侣以梦境术重温旧事，他在梦中再一次向你表白。",
        "expanded_text": "你以神识为他织了一场梦——梦中是你们六百年前初遇的那条青石街。他恢复了少年模样，在街角看见你时怔了许久。你笑着走过去：「这位公子，可要一起看灯？」他红着耳根点了点头——分明已经与你做了几百年的道侣，在梦中却还是当年那个笨拙的少年。你拉起他的手时他说了和六百年前一模一样的话：「我……想一直和你看灯。」",
        "conditions": {"min_realm": 4, "max_realm": 5, "min_age": 120, "gender": "female"},
        "effects": {"cultivation": 25, "willpower": 2, "charisma": 1},
        "weight": 7
    },
    {
        "id": "adt_f_242",
        "text": "你的元婴在双修中进化，表面浮现道侣的灵纹印记。",
        "expanded_text": "那一夜的双修本无异常——可结束后你惊讶地发现自己元婴的衣袍上多了一枚极小的剑形灵纹。那是他的标记。你以神识探查——那灵纹深入元婴本源，与你的道果融为一体。他也在自己的元婴上发现了一枚属于你的莲花灵纹。古籍中说这叫「道侣烙印」——此生此世、乃至转世轮回，你们的灵魂都将互相铭记。",
        "conditions": {"min_realm": 4, "max_realm": 5, "min_age": 100, "gender": "female"},
        "effects": {"cultivation": 60, "fortune": 2, "comprehension": 1},
        "weight": 6
    },
]

# ============================================================
# 化神层 (min_realm=5) — 天地共鸣, 道与身心合一, 超脱之前的最后情念
# ============================================================
DEITY_EVENTS = [
    # Male (8)
    {
        "id": "adt_m_243",
        "text": "你与道侣在虚空中双修，引动天地法则共鸣。",
        "expanded_text": "化神期的你们已能在虚空中长立。这一夜你们悬浮于万丈高空之上——脚下是翻涌的云海，头顶是无尽星河。你们的灵力交融之际，天地法则竟为之共鸣——远处有雷鸣阵阵，近处有灵光绽放。你抱住她时感到自己的神识与天地融为了一体。在这一方天地的顶峰，唯一让你还牵挂红尘的——只有怀中这个人。",
        "conditions": {"min_realm": 5, "max_realm": 5, "min_age": 150, "gender": "male"},
        "effects": {"cultivation": 150, "comprehension": 3, "willpower": 2},
        "weight": 5
    },
    {
        "id": "adt_m_244",
        "text": "你欲渡劫飞升，道侣说要与你共赴空间节点。",
        "expanded_text": "你感知到了空间节点的气息——但你犹豫了。她站在你面前，目光坚定：「我与你同去。」你摇头：「我一人渡劫尚有三成把握，两人则——」她捂住你的嘴：「生同衾，死同穴。这条路我们走了千年，最后这一步——我不要你独行。」那一夜你们在洞府中相拥至天明，谁也没有睡。你决定了：若寻得节点，便携她同往。",
        "conditions": {"min_realm": 5, "max_realm": 5, "min_age": 200, "gender": "male"},
        "effects": {"cultivation": 100, "willpower": 3},
        "weight": 4
    },
    {
        "id": "adt_m_245",
        "text": "你以化神之力凝聚分身，令分身陪伴道侣修炼。",
        "expanded_text": "化神期你已能凝聚一道永久分身——虽只有本体三成修为，却有完整的意识和情感。你将分身留在道侣身边：「我去寻空间节点，此身替我陪你。」她抱住那道分身时落了泪。分身轻轻拍她的背：「我在呢。」数百年后你寻得节点归来时，分身正和她在院中品茶。你收回分身之际，她的千年记忆尽数涌入你识海——你感受到了她千年来每一个思念你的夜晚。",
        "conditions": {"min_realm": 5, "max_realm": 5, "min_age": 150, "gender": "male"},
        "effects": {"cultivation": 80, "willpower": 2, "charisma": 1},
        "weight": 5
    },
    {
        "id": "adt_m_246",
        "text": "你与道侣以法则之力双修，周身空间为之扭曲。",
        "expanded_text": "化神之境已能触碰空间法则。你们双修之时灵力浓郁到周围空间开始扭曲——洞府中的物件悬浮起来，时间似乎都慢了半拍。她的发丝在无重力中散开如墨。你们的灵力构成的光柱直冲云霄，方圆百里的修士都感受到了那股压迫感。你在这至高的境界中仍然选择与她相守——这便是你的道。",
        "conditions": {"min_realm": 5, "max_realm": 5, "min_age": 150, "gender": "male"},
        "effects": {"cultivation": 130, "comprehension": 2, "constitution": 1},
        "weight": 5
    },
    {
        "id": "adt_m_247",
        "text": "你在大限将至时与道侣做最后一次双修，将毕生修为尽数渡给她。",
        "expanded_text": "你的寿元将尽——你感知得到。可她还年轻——至少还有五百年。最后一夜你将她拉入怀中：「我有一物赠你。」你催动毕生修为如长河般灌入她体内。她惊恐地想推开你——可你已将她锁定。你的灵力像退潮的海水一般从体内流向她。你看着她的修为节节攀升，自己的意识却渐渐模糊。最后一丝灵光散去前你吻了她的额头：「替我去看那方天地。」",
        "conditions": {"min_realm": 5, "max_realm": 5, "min_age": 200, "gender": "male"},
        "effects": {"cultivation": -100, "lifespan": -10, "willpower": 4},
        "weight": 3
    },
    {
        "id": "adt_m_248",
        "text": "你以天道之眼窥见道侣的前世——你们已相守了九世。",
        "expanded_text": "化神期的神识足以回溯时间长河。那一夜双修之际你无意间开启了「天道之眼」——你看见了她的九世轮回。每一世你们都会相遇：第一世她是你的青梅竹马；第三世你是她的护道之人；第七世你们是敌对宗门的弟子却仍相爱……九世轮回，九世相守。你收回天道之眼时已泪流满面。她睡在你身旁，不知你看见了什么——可她梦中喃喃唤了你的名字。",
        "conditions": {"min_realm": 5, "max_realm": 5, "min_age": 200, "gender": "male"},
        "effects": {"cultivation": 120, "fortune": 3, "comprehension": 2},
        "weight": 4
    },
    {
        "id": "adt_m_249",
        "text": "你以神念凝聚一方小世界，在其中与道侣度过千年光阴。",
        "expanded_text": "化神修士可以在识海中凝聚一方微型世界。你花了十年为她造了一片桃花源——有山有水，有四季轮转。你们的分身在其中生活了一千年：春日看花，夏夜观萤，秋收稻谷，冬围炉火。那一千年没有修炼、没有争斗，只有两个人安静地过日子。当你收回那方小世界时——外界只过了一个月。她睁开眼时目光柔得像水。",
        "conditions": {"min_realm": 5, "max_realm": 5, "min_age": 150, "gender": "male"},
        "effects": {"cultivation": 60, "willpower": 3, "charisma": 2},
        "weight": 5
    },
    {
        "id": "adt_m_250",
        "text": "你感知到空间节点将现，与道侣在最后一夜以灵力相融为誓。",
        "expanded_text": "今夜虚空微微震颤——你知道空间节点不远了。也许明日，也许后日。她坐在你对面，一手覆上你的手背。「怕吗？」她问。你摇头。她将额头抵在你额上，灵力自她体内缓缓渡入你。不是双修——是誓言。她将自己一缕神念封入你的元婴深处：「带着我去。飞升也好、陨落也好——你不是一个人。」你闭上眼，握紧她的手。",
        "conditions": {"min_realm": 5, "max_realm": 5, "min_age": 200, "gender": "male"},
        "effects": {"cultivation": 100, "willpower": 4},
        "weight": 4
    },
    # Female (7)
    {
        "id": "adt_f_243",
        "text": "你与道侣在星河之下双修，天地灵气为你们旋转。",
        "expanded_text": "化神之境——天地已如你掌中之物。这一夜你们选在一处无人的山巅。他的灵力入体之时你感到周遭的天地灵气开始自发地向你们涌来——如同朝圣。漫天星辰在你们头顶旋转，银河仿佛低了三分。他的眼中映着星光，你的眼中也是。在这方天地的极致巅峰——能与他共享这一刻，你觉得修炼千年都值了。",
        "conditions": {"min_realm": 5, "max_realm": 5, "min_age": 150, "gender": "female"},
        "effects": {"cultivation": 140, "comprehension": 3, "willpower": 1},
        "weight": 5
    },
    {
        "id": "adt_f_244",
        "text": "你以化神之力为道侣重塑经脉，他以余生为你守道。",
        "expanded_text": "他在一场大战中经脉尽毁——对一个元婴修士而言这等于废了修为。你却不信。你以化神之力一根根为他重塑经脉——每一根都比原来更宽、更韧。那是一项需要极致精细的工程——你的神识如绣花针般在他体内穿梭了整整一年。他痊愈后跪在你面前：「此生余下的岁月——我只为你一人守道。」你扶起他时已泪眼婆娑。",
        "conditions": {"min_realm": 5, "max_realm": 5, "min_age": 150, "gender": "female"},
        "effects": {"cultivation": 50, "willpower": 3, "charisma": 1},
        "weight": 5
    },
    {
        "id": "adt_f_245",
        "text": "你修至化神巅峰，以最后一缕情念凝聚护道法器赠予道侣。",
        "expanded_text": "化神之巅——你已无情无欲，道心如镜。可你心底最后一缕牵挂是他。你以那一缕情念为引、以千年修为为材，凝聚出一枚玉佩。玉佩中封存着你的一丝神念——若他遇险，神念便会自动护主。你将玉佩挂在他胸前时他不知内情——只觉得那枚玉佩异常温暖。你笑了笑，没有告诉他：那是你为他留的最后一样东西。",
        "conditions": {"min_realm": 5, "max_realm": 5, "min_age": 200, "gender": "female"},
        "effects": {"cultivation": -50, "willpower": 4, "fortune": 2},
        "weight": 4
    },
    {
        "id": "adt_f_246",
        "text": "你与道侣在时间法则的缝隙中共度百年，外界只过一瞬。",
        "expanded_text": "化神之力已可触碰时间法则的边缘。你偶然撕开一道时间裂缝——裂缝内的时间流速与外界相差万倍。你拉着他的手跳了进去。在那方「慢世界」中你们度过了完整的一百年：种花、养鹤、看日出日落。他的鬓角在那一百年中添了几缕白——你也是。可当你们从裂缝中出来时——外界只过了半个时辰。他看着你笑：「赚了。」",
        "conditions": {"min_realm": 5, "max_realm": 5, "min_age": 150, "gender": "female"},
        "effects": {"cultivation": 100, "lifespan": 5, "willpower": 2},
        "weight": 4
    },
    {
        "id": "adt_f_247",
        "text": "你以天道之眼窥见自己与道侣的来世——他在等你飞升。",
        "expanded_text": "那一夜双修之际你无意间看见了未来的一线可能。你看见自己飞升成功——踏入那方更广阔的天地。而他——他站在仙门之后等你。他比你先去了三百年，可他没有走远。他就站在仙门入口处，一等就是三百年。你收回天眼时他正睡在你身旁。你轻轻握住他的手在心中发誓：我一定会去。一定。",
        "conditions": {"min_realm": 5, "max_realm": 5, "min_age": 200, "gender": "female"},
        "effects": {"cultivation": 110, "willpower": 3, "fortune": 2},
        "weight": 4
    },
    {
        "id": "adt_f_248",
        "text": "你在大限将至前与道侣做最后一次双修，将护道之力留给他。",
        "expanded_text": "你的寿元如沙漏般见底——可他还有路要走。最后一夜你将他拥入怀中，以最温柔的方式将自己一半修为渡入他体内。他感知到后拼命想推开你——你按住他的手：「别动。这是我最后能给你的东西。」你的灵力化作一层淡金色的光膜覆在他的元婴表面——那是你的护道之力。你笑着吻了他的眉心：「去替我看看那方天地长什么样。」",
        "conditions": {"min_realm": 5, "max_realm": 5, "min_age": 200, "gender": "female"},
        "effects": {"cultivation": -80, "lifespan": -8, "willpower": 4},
        "weight": 3
    },
    {
        "id": "adt_f_249",
        "text": "空间节点将现之夜，你与道侣以神念为誓——来世再续此缘。",
        "expanded_text": "虚空中传来微弱的震颤——空间节点快了。你们对坐于洞府中央，四目相对。他忽然从怀中取出一枚玉简：「我将神念封在里面了。无论飞升还是陨落——只要这枚玉简还在，来世我也能找到你。」你接过玉简贴在心口。你也做了同样的事——将一缕神念封入一枚暖玉递给他。「来世——若你忘了我，就握着它。你会想起来的。」他点头，轻轻将你拥入怀中。",
        "conditions": {"min_realm": 5, "max_realm": 5, "min_age": 200, "gender": "female"},
        "effects": {"cultivation": 90, "willpower": 4, "fortune": 1},
        "weight": 4
    },
]


def main():
    all_new = QI_REFINING_EVENTS + GOLDEN_CORE_EVENTS + NASCENT_SOUL_EVENTS + DEITY_EVENTS

    # Add standard fields
    for e in all_new:
        e.setdefault("category", "adult")
        e.setdefault("tags", ["adult", "cultivation"])
        e.setdefault("event_type", "normal")

    print(f"Generated {len(all_new)} new adult events:")
    print(f"  练气 (realm 1): {len(QI_REFINING_EVENTS)}")
    print(f"  金丹 (realm 3): {len(GOLDEN_CORE_EVENTS)}")
    print(f"  元婴 (realm 4): {len(NASCENT_SOUL_EVENTS)}")
    print(f"  化神 (realm 5): {len(DEITY_EVENTS)}")

    # Append to adult.json
    adult_path = os.path.join(EVENTS_DIR, "adult.json")
    with open(adult_path, "r", encoding="utf-8") as f:
        adult_events = json.load(f)
    adult_events.extend(all_new)
    with open(adult_path, "w", encoding="utf-8") as f:
        json.dump(adult_events, f, ensure_ascii=False, indent=2)
    print(f"  adult.json: {len(adult_events)} total events")

    # Append to all_events.json
    all_path = os.path.join(EVENTS_DIR, "all_events.json")
    with open(all_path, "r", encoding="utf-8") as f:
        all_events = json.load(f)
    all_events.extend(all_new)
    with open(all_path, "w", encoding="utf-8") as f:
        json.dump(all_events, f, ensure_ascii=False, indent=2)
    print(f"  all_events.json: {len(all_events)} total events")


if __name__ == "__main__":
    main()
