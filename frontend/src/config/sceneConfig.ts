/**
 * Scene image mapping configuration for the three-layer visual system.
 * Layer 1: Realm-based dynamic backgrounds
 * Layer 2: CG illustrations (breakthrough + choice events)
 * Layer 3: Character portraits
 */

// ── Layer 1: Realm → Background image pool ─────────────────────────────
export const REALM_BACKGROUNDS: Record<number, string[]> = {
  0: [
    '/scenes/bg/竹林秘境.png',
    '/scenes/bg/青石古道.png',
    '/scenes/bg/松间清泉.png',
    '/scenes/bg/幽谷兰溪.png',
    '/scenes/bg/古木灵林.png',
  ],
  1: [
    '/scenes/bg/竹林秘境.png',
    '/scenes/bg/青石古道.png',
    '/scenes/bg/松间清泉.png',
    '/scenes/bg/幽谷兰溪.png',
    '/scenes/bg/古木灵林.png',
  ],
  2: [
    '/scenes/bg/藏书阁.png',
    '/scenes/bg/翠微山居.png',
    '/scenes/bg/云梯天阶.png',
    '/scenes/bg/悬空栈道.png',
    '/scenes/bg/剑阁藏锋.png',
  ],
  3: [
    '/scenes/bg/仙山云海.png',
    '/scenes/bg/天池仙境.png',
    '/scenes/bg/仙境瀑布.png',
    '/scenes/bg/万木幽谷.png',
    '/scenes/bg/千仞绝壁.png',
  ],
  4: [
    '/scenes/bg/碧海仙岛.png',
    '/scenes/bg/银河天瀑.png',
    '/scenes/bg/云梦莲台.png',
    '/scenes/bg/仙府夜景.png',
    '/scenes/bg/琉璃灯河.png',
  ],
  5: [
    '/scenes/bg/渡劫雷云.png',
    '/scenes/bg/昆仑雪峰.png',
    '/scenes/bg/龙脊山脉.png',
    '/scenes/bg/云中楼阁.png',
    '/scenes/bg/雾中仙桥.png',
  ],
};

// ── Layer 2: Event category → CG image pool ────────────────────────────
export const EVENT_CG: Record<string, string[]> = {
  cultivation: [
    '/scenes/cg/修炼洞天.png',
    '/scenes/cg/丹房药圃.png',
    '/scenes/cg/炼器台.png',
    '/scenes/cg/星空竹林.png',
    '/scenes/cg/月下松涛.png',
  ],
  fortune: [
    '/scenes/cg/桃花源境.png',
    '/scenes/cg/仙人棋盘.png',
    '/scenes/cg/樱花溪谷.png',
    '/scenes/cg/云梦泽月.png',
    '/scenes/cg/花海草原.png',
  ],
  calamity: [
    '/scenes/cg/毒瘴沼泽.png',
    '/scenes/cg/龙泽深渊.png',
    '/scenes/cg/鬼谷幽涧.png',
    '/scenes/cg/赤炎荒漠.png',
    '/scenes/cg/风卷荒原.png',
  ],
  social: [
    '/scenes/cg/禅院钟声.png',
    '/scenes/cg/雾锁重楼.png',
    '/scenes/cg/灵湖荷塘.png',
    '/scenes/cg/月下荷塘.png',
    '/scenes/cg/枫林晚照.png',
  ],
  violence: [
    '/scenes/cg/深渊洞窟.png',
    '/scenes/cg/灵蛇幽谷.png',
    '/scenes/cg/莽荒大泽.png',
    '/scenes/cg/落日孤峰.png',
    '/scenes/cg/极寒冰原.png',
  ],
  world: [
    '/scenes/cg/山川飞流.png',
    '/scenes/cg/飞瀑虹桥.png',
    '/scenes/cg/大漠孤烟.png',
    '/scenes/cg/流沙古国.png',
    '/scenes/cg/沧海孤舟.png',
  ],
  // Fallback for categories without explicit mapping
  common: [
    '/scenes/cg/碧落草原.png',
    '/scenes/cg/梦泽云渚.png',
    '/scenes/cg/镜湖明月.png',
  ],
  adult: [
    '/scenes/cg/桃花源境.png',
    '/scenes/cg/樱花溪谷.png',
    '/scenes/cg/月下荷塘.png',
  ],
  sect: [
    '/scenes/cg/禅院钟声.png',
    '/scenes/cg/雾锁重楼.png',
    '/scenes/cg/枫林晚照.png',
  ],
};

// ── Layer 2: Breakthrough CG (per realm, 2 images each) ────────────────
export const BREAKTHROUGH_CG: Record<number, string[]> = {
  1: ['/scenes/cg/梦泽云渚.png', '/scenes/cg/碧落草原.png'],
  2: ['/scenes/cg/冰晶洞窟.png', '/scenes/cg/古殿遗迹.png'],
  3: ['/scenes/cg/幻雾云梦.png', '/scenes/cg/雪山冰宫.png'],
  4: ['/scenes/cg/紫竹林.png', '/scenes/cg/镜湖明月.png'],
  5: ['/scenes/cg/灵兽谷.png', '/scenes/cg/古塔残垣.png'],
};

// ── Layer 3: Character portraits (gender + realm tier) ──────────────────
export const CHARACTER_PORTRAITS: Record<string, Record<string, string>> = {
  male: {
    low: '/scenes/character/青发剑修背影.png',     // realm 0-2
    high: '/scenes/character/金发仙师背影.png',    // realm 3-4
    max: '/scenes/character/白发仙人背影.png',     // realm 5
  },
  female: {
    low: '/scenes/character/紫发女修背影.png',     // realm 0-2
    high: '/scenes/character/紫发女修背影.png',    // realm 3-4
    max: '/scenes/character/赤发魔修背影.png',     // realm 5
  },
};

// ── Summary screen backgrounds ──────────────────────────────────────────
export const SUMMARY_BACKGROUNDS: Record<string, string> = {
  ascended: '/scenes/bg/仙山云海.png',
  tribulation_failed: '/scenes/bg/渡劫雷云.png',
  combat_death: '/scenes/bg/落日孤峰.png',
  default: '/scenes/bg/云中楼阁.png',
};

// ── Helper: pick random from array ─────────────────────────────────────
export function pickRandom<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

// ── Helper: get character portrait for gender + realm ───────────────────
export function getPortrait(gender: string, realm: number): string {
  const g = gender === 'female' ? 'female' : 'male';
  const tier = realm >= 5 ? 'max' : realm >= 3 ? 'high' : 'low';
  return CHARACTER_PORTRAITS[g][tier];
}
