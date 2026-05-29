import { useState, useEffect } from 'react';
import type { Attributes, Talent } from '../utils/types';
import { ATTR_NAMES, RARITY_COLORS, RARITY_NAMES } from '../utils/types';
import { fetchTalents } from '../utils/api';

interface CharacterCreationProps {
  onConfirm: (attributes: Attributes, talents: string[]) => void;
}

const MAX_POINTS = 20;
const DEFAULT_ATTRS: Attributes = {
  lifespan: 3,
  constitution: 3,
  comprehension: 3,
  fortune: 3,
  charisma: 3,
  willpower: 3,
};

export default function CharacterCreation({ onConfirm }: CharacterCreationProps) {
  const [attrs, setAttrs] = useState<Attributes>({ ...DEFAULT_ATTRS });
  const [talentPool, setTalentPool] = useState<Talent[]>([]);
  const [selectedTalents, setSelectedTalents] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [show, setShow] = useState(false);

  const totalPoints = Object.values(attrs).reduce((a, b) => a + b, 0);
  const remaining = MAX_POINTS - totalPoints;

  useEffect(() => {
    fetchTalents().then((talents) => {
      setTalentPool(talents);
      setLoading(false);
    });
    setTimeout(() => setShow(true), 100);
  }, []);

  const adjustAttr = (key: keyof Attributes, delta: number) => {
    const newVal = attrs[key] + delta;
    if (newVal < 0 || newVal > 10) return;
    if (delta > 0 && remaining <= 0) return;
    setAttrs({ ...attrs, [key]: newVal });
  };

  const toggleTalent = (id: string) => {
    if (selectedTalents.includes(id)) {
      setSelectedTalents(selectedTalents.filter((t) => t !== id));
    } else if (selectedTalents.length < 3) {
      setSelectedTalents([...selectedTalents, id]);
    }
  };

  const randomize = () => {
    const keys = Object.keys(DEFAULT_ATTRS) as (keyof Attributes)[];
    const newAttrs = { ...DEFAULT_ATTRS };
    let pts = MAX_POINTS - keys.length; // Start with 1 each = 6, distribute remaining 14
    keys.forEach((k) => (newAttrs[k] = 1));

    while (pts > 0) {
      const key = keys[Math.floor(Math.random() * keys.length)];
      if (newAttrs[key] < 10) {
        newAttrs[key]++;
        pts--;
      }
    }
    setAttrs(newAttrs);
  };

  const rerollTalents = () => {
    setLoading(true);
    setSelectedTalents([]);
    fetchTalents().then((talents) => {
      setTalentPool(talents);
      setLoading(false);
    });
  };

  const canStart = selectedTalents.length > 0 && remaining >= 0;

  return (
    <div
      className={`min-h-screen p-4 md:p-8 transition-all duration-700 relative ${
        show ? 'opacity-100' : 'opacity-0'
      }`}
    >
      {/* Mountain background */}
      <div className="mountain-bg" />

      <div className="max-w-2xl mx-auto relative z-10">
        {/* Header */}
        <div className="text-center mb-8">
          <h2 className="text-3xl font-kai text-scroll-gold tracking-[0.3em] mb-2">
            转世投胎
          </h2>
          <p className="text-scroll-text-dim text-sm font-kai tracking-widest">
            分配属性，选择天赋，开启新的一世
          </p>
        </div>

        {/* Attributes Panel */}
        <div className="scroll-panel p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-kai text-scroll-gold text-lg tracking-widest">
              六维属性
            </h3>
            <div className="flex items-center gap-3">
              <span
                className={`text-sm font-kai ${
                  remaining > 0
                    ? 'text-scroll-jade'
                    : remaining === 0
                    ? 'text-scroll-gold'
                    : 'text-red-500'
                }`}
              >
                剩余点数: {remaining}
              </span>
              <button
                onClick={randomize}
                className="text-xs px-3 py-1 border border-scroll-gold-dim/30 text-scroll-gold/70 
                         hover:bg-scroll-gold/8 transition-colors font-kai rounded-sm"
              >
                随机
              </button>
            </div>
          </div>

          <div className="space-y-3">
            {(Object.keys(ATTR_NAMES) as (keyof Attributes)[]).map((key) => (
              <div key={key} className="flex items-center gap-3">
                <span className="w-12 text-right text-scroll-text font-kai text-sm">
                  {ATTR_NAMES[key]}
                </span>
                <button
                  onClick={() => adjustAttr(key, -1)}
                  className="w-7 h-7 border border-scroll-gold-dim/30 text-scroll-gold hover:bg-scroll-gold/8 
                           flex items-center justify-center transition-colors text-sm rounded-sm"
                >
                  −
                </button>
                <div className="flex-1 relative h-6">
                  <div className="absolute inset-0 bg-scroll-cloud rounded-full border border-scroll-gold-dim/15" />
                  <div
                    className="absolute inset-y-0 left-0 rounded-full transition-all duration-300"
                    style={{
                      width: `${(attrs[key] / 10) * 100}%`,
                      background: 'linear-gradient(90deg, rgba(150,105,30,0.3), rgba(212,160,74,0.5))'
                    }}
                  />
                  <span className="absolute inset-0 flex items-center justify-center text-scroll-ink text-sm font-kai font-medium">
                    {attrs[key]}
                  </span>
                </div>
                <button
                  onClick={() => adjustAttr(key, 1)}
                  className="w-7 h-7 border border-scroll-gold-dim/30 text-scroll-gold hover:bg-scroll-gold/8 
                           flex items-center justify-center transition-colors text-sm rounded-sm"
                >
                  +
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Talents Panel */}
        <div className="scroll-panel p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-kai text-scroll-gold text-lg tracking-widest">
              选择天赋 ({selectedTalents.length}/3)
            </h3>
            <button
              onClick={rerollTalents}
              className="text-xs px-3 py-1 border border-scroll-gold-dim/30 text-scroll-gold/70 
                       hover:bg-scroll-gold/8 transition-colors font-kai rounded-sm"
            >
              换一批
            </button>
          </div>

          {loading ? (
            <div className="text-center py-8 text-scroll-text-dim font-kai">
              天命推演中...
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              {talentPool.map((talent) => {
                const isSelected = selectedTalents.includes(talent.id);
                const isDisabled =
                  !isSelected && selectedTalents.length >= 3;

                return (
                  <button
                    key={talent.id}
                    onClick={() => toggleTalent(talent.id)}
                    disabled={isDisabled}
                    className={`p-3 border rounded-lg text-left transition-all duration-200
                      ${
                        isSelected
                          ? 'border-scroll-gold-dim bg-scroll-gold/8 shadow-[0_2px_12px_rgba(150,100,30,0.12)]'
                          : isDisabled
                          ? 'border-scroll-cloud opacity-40 cursor-not-allowed bg-white/40'
                          : `border-scroll-cloud bg-white/60 hover:border-scroll-gold-dim/40 hover:bg-white/80 ${RARITY_COLORS[talent.rarity]}`
                      }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`text-xs px-1.5 py-0.5 border rounded-sm ${
                          RARITY_COLORS[talent.rarity]
                        }`}
                      >
                        {RARITY_NAMES[talent.rarity]}
                      </span>
                      <span className="font-kai text-sm text-scroll-text">
                        {talent.name}
                      </span>
                    </div>
                    <p className="text-xs text-scroll-text-dim leading-relaxed">
                      {talent.description}
                    </p>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Start Button */}
        <div className="text-center">
          <button
            onClick={() => canStart && onConfirm(attrs, selectedTalents)}
            disabled={!canStart}
            className={`ancient-button text-lg tracking-[0.5em] font-kai ${
              !canStart ? 'opacity-30 cursor-not-allowed' : 'animate-pulse-gold'
            }`}
          >
            入世修行
          </button>
          {!canStart && (
            <p className="mt-3 text-scroll-text-dim text-xs font-kai">
              {remaining < 0 ? '属性点数超出上限' : '请至少选择一个天赋'}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
