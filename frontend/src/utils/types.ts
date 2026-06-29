export interface Attributes {
  lifespan: number;
  constitution: number;
  comprehension: number;
  fortune: number;
  charisma: number;
  willpower: number;
}

export interface Talent {
  id: string;
  name: string;
  description: string;
  rarity: number;
  effects: Record<string, number>;
  tags: string[];
}

export interface EventBranch {
  text: string;
  effects: Record<string, number>;
  result_text: string;
  success_rate?: number;
  failure_effects?: Record<string, number>;
  failure_text?: string;
  check_attribute?: string;
  consequence_tag?: string;
  consequence_desc?: string;
}

export interface GameEvent {
  text: string;
  expanded_text?: string;
  type: 'normal' | 'important' | 'danger' | 'fortune' | 'special';
  category?: string;
  age: number;
  id?: string;
  branches?: EventBranch[];
}

export const CATEGORY_NAMES: Record<string, string> = {
  common: '尘世',
  cultivation: '修炼',
  fortune: '机缘',
  social: '际遇',
  calamity: '劫难',
  world: '天象',
  violence: '江湖',
  adult: '红尘',
  death: '命劫',
  sect: '宗门',
  sect_world: '宗门动态',
};

export const CATEGORY_COLORS: Record<string, string> = {
  common: 'text-stone-500',
  cultivation: 'text-indigo-600',
  fortune: 'text-amber-600',
  social: 'text-teal-600',
  calamity: 'text-red-600',
  world: 'text-sky-600',
  violence: 'text-rose-700',
  adult: 'text-pink-500',
  death: 'text-gray-700',
  sect: 'text-emerald-600',
  sect_world: 'text-cyan-600',
};

export interface GameState {
  game_id: string;
  age: number;
  realm: number;
  realm_name: string;
  cultivation: number;
  cultivation_max: number;
  attributes: Attributes;
  talents: string[];
  tags: string[];
  is_dead: boolean;
  death_reason: string;
  is_ascended: boolean;
}

export interface SectInfo {
  name: string;
  rank: string;
  contribution: number;
  sect_type: string;
}

export interface NPCRelationship {
  name: string;
  relation_type: string;
  sentiment: number;
  is_alive: boolean;
}

export interface ChoiceHistoryItem {
  age: number;
  event_text: string;
  choice_text: string;
  result_text: string;
  consequence_tag: string;
}

export interface EmotionalToken {
  name: string;
  description: string;
  source_npc: string;
  source_age: number;
  keywords: string[];
}

export interface NextYearResponse {
  age: number;
  realm: number;
  realm_name: string;
  cultivation: number;
  cultivation_max: number;
  events: GameEvent[];
  attributes: Attributes;
  is_dead: boolean;
  death_reason: string;
  is_ascended: boolean;
  space_node_found?: boolean;
  gender?: string;
  has_choice?: boolean;
  choice_event?: GameEvent;
  // New fields
  tension?: number;
  sect_info?: SectInfo;
  npc_relationships?: NPCRelationship[];
  ai_enhanced?: boolean; // LLM参与标识（灵玉指示器）
}

export interface LifeSummary {
  total_age: number;
  max_realm: number;
  max_realm_name: string;
  death_reason: string;
  key_events: string[];
  talents: string[];
  final_attributes: Attributes;
  score: number;
  title: string;
  gender?: string;
}

export interface LifeEvent {
  age: number;
  text: string;
  category?: string;
  event_type?: string;
}

export const GENDER_NAMES: Record<string, string> = {
  male: '男',
  female: '女',
};

export const REALM_NAMES: Record<number, string> = {
  0: '凡人',
  1: '练气',
  2: '筑基',
  3: '金丹',
  4: '元婴',
  5: '化神',
};

export const REALM_COLORS: Record<number, string> = {
  0: 'text-gray-500',
  1: 'text-green-600',
  2: 'text-blue-600',
  3: 'text-amber-600',
  4: 'text-purple-600',
  5: 'text-red-600',
};

export const ATTR_NAMES: Record<keyof Attributes, string> = {
  lifespan: '寿元',
  constitution: '根骨',
  comprehension: '悟性',
  fortune: '福缘',
  charisma: '魅力',
  willpower: '心性',
};

export const RARITY_COLORS: Record<number, string> = {
  1: 'border-gray-400 text-gray-600',
  2: 'border-green-500 text-green-700',
  3: 'border-purple-500 text-purple-700',
  4: 'border-amber-500 text-amber-700',
};

export const RARITY_NAMES: Record<number, string> = {
  1: '凡',
  2: '良',
  3: '极',
  4: '仙',
};
