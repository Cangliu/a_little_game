import { useState, useEffect, useRef, useMemo } from 'react';
import type { GameEvent, NextYearResponse } from '../utils/types';
import { REALM_NAMES, REALM_COLORS, GENDER_NAMES, CATEGORY_NAMES, CATEGORY_COLORS } from '../utils/types';
import { nextYear } from '../utils/api';

/**
 * Extract the character age referenced in event narrative text.
 * Events often hardcode phrasing like "你3岁时" / "三岁那年" which
 * doesn't always equal the engine's state.age. We use the in-text
 * age (when present) as the displayed Canglang Era year, so the
 * timeline label always matches the story.
 */
function parseChineseNumber(s: string): number {
  const map: Record<string, number> = {
    零: 0, 一: 1, 二: 2, 两: 2, 三: 3, 四: 4,
    五: 5, 六: 6, 七: 7, 八: 8, 九: 9,
  };
  // 十, 十二, 二十, 二十五, 一百零八...
  if (s === '十') return 10;
  if (s.startsWith('十')) return 10 + (map[s[1]] ?? 0); // 十三 = 13
  if (s.endsWith('十')) return (map[s[0]] ?? 0) * 10; // 二十 = 20
  if (s.includes('十')) {
    const [a, b] = s.split('十');
    return (map[a] ?? 0) * 10 + (map[b] ?? 0);
  }
  if (s.includes('百')) {
    const [h, rest] = s.split('百');
    return (map[h] ?? 0) * 100 + (rest ? parseChineseNumber(rest.replace(/^零/, '')) : 0);
  }
  return s in map ? map[s] : NaN;
}

function extractEventAge(text: string): number | null {
  if (!text) return null;
  // Arabic numerals: "3岁", "12岁时"
  const arab = text.match(/(\d+)\s*岁/);
  if (arab) return parseInt(arab[1], 10);
  // Chinese numerals: "三岁", "十六岁那年"
  const cn = text.match(/([零一二两三四五六七八九十百]+)\s*岁/);
  if (cn) {
    const n = parseChineseNumber(cn[1]);
    if (!isNaN(n) && n > 0) return n;
  }
  return null;
}

interface GameScreenProps {
  gameId: string;
  gender?: string;
  onGameEnd: (gameId: string) => void;
}

/**
 * Typewriter component: progressively reveals expanded narrative.
 * Renders the one-line summary fully, and types out the expanded narrative
 * character-by-character below it.
 */
function TypewriterEvent({
  event,
  speedMs = 35,
  onDone,
}: {
  event: GameEvent;
  speedMs?: number;
  onDone?: () => void;
}) {
  const expanded = event.expanded_text || '';
  const [shown, setShown] = useState(expanded ? '' : expanded);
  const [done, setDone] = useState(!expanded);
  const idxRef = useRef(0);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    if (!expanded) {
      setDone(true);
      onDone?.();
      return;
    }
    idxRef.current = 0;
    setShown('');
    setDone(false);
    const tick = () => {
      idxRef.current += 1;
      setShown(expanded.slice(0, idxRef.current));
      if (idxRef.current >= expanded.length) {
        if (timerRef.current) window.clearInterval(timerRef.current);
        timerRef.current = null;
        setDone(true);
        onDone?.();
        return;
      }
    };
    timerRef.current = window.setInterval(tick, speedMs);
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [expanded]);

  const skip = () => {
    if (done) return;
    if (timerRef.current) window.clearInterval(timerRef.current);
    timerRef.current = null;
    setShown(expanded);
    setDone(true);
    onDone?.();
  };

  return (
    <div onClick={skip} className={expanded && !done ? 'cursor-pointer' : ''}>
      {expanded && (
        <div className="event-narrative">
          {shown}
          {!done && <span className="tw-cursor">▊</span>}
        </div>
      )}
    </div>
  );
}

export default function GameScreen({
  gameId,
  gender = 'male',
  onGameEnd,
}: GameScreenProps) {
  const [age, setAge] = useState(0);
  const [realm, setRealm] = useState(0);
  const [realmName, setRealmName] = useState('凡人');
  const [cultivation, setCultivation] = useState(0);
  const [cultivationMax, setCultivationMax] = useState(100);
  const [eventLog, setEventLog] = useState<GameEvent[]>([]);
  const [isGameOver, setIsGameOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [autoPlay, setAutoPlay] = useState(false);
  // Index of the latest event still typing; only one types at a time so older
  // events render fully and the newest one animates.
  const [typingIdx, setTypingIdx] = useState<number>(-1);
  const logEndRef = useRef<HTMLDivElement>(null);
  const autoPlayRef = useRef(false);

  useEffect(() => {
    autoPlayRef.current = autoPlay;
  }, [autoPlay]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [eventLog, typingIdx]);

  const advanceYear = async () => {
    if (loading || isGameOver) return;
    setLoading(true);
    try {
      const result: NextYearResponse = await nextYear(gameId);
      setAge(result.age);
      setRealm(result.realm);
      setRealmName(result.realm_name);
      setCultivation(result.cultivation);
      setCultivationMax(result.cultivation_max);
      setEventLog((prev) => {
        const next = [...prev, ...result.events];
        // First event with expanded text in this batch begins typing.
        const firstNewIdx = prev.length;
        const firstWithExpanded = result.events.findIndex((e) => e.expanded_text);
        setTypingIdx(
          firstWithExpanded >= 0 ? firstNewIdx + firstWithExpanded : -1
        );
        return next;
      });

      if (result.is_dead || result.is_ascended) {
        setIsGameOver(true);
        setAutoPlay(false);
        setTimeout(() => onGameEnd(gameId), 2500);
      } else if (autoPlayRef.current) {
        // Wait a bit longer when narrative is unfolding so it can be read.
        const hasNarrative = result.events.some((e) => e.expanded_text);
        setTimeout(() => advanceYear(), hasNarrative ? 1800 : 400);
      }
    } catch (err) {
      console.error('Error advancing year:', err);
      setAutoPlay(false);
    }
    setLoading(false);
  };

  const handleTyped = (idx: number) => {
    // When current narrative finishes, look for the next one with expanded text.
    setEventLog((cur) => {
      const next = cur.findIndex((e, i) => i > idx && e.expanded_text);
      setTypingIdx(next);
      return cur;
    });
  };

  const toggleAutoPlay = () => {
    if (!autoPlay) {
      setAutoPlay(true);
      advanceYear();
    } else {
      setAutoPlay(false);
    }
  };

  const getEventLineClass = (type: string) => {
    switch (type) {
      case 'important':
        return 'event-line event-line-important';
      case 'danger':
        return 'event-line event-line-danger';
      case 'fortune':
        return 'event-line event-line-fortune';
      case 'special':
        return 'event-line event-line-fortune';
      default:
        return 'event-line';
    }
  };

  const cultPercent = cultivationMax > 0 ? Math.min((cultivation / cultivationMax) * 100, 100) : 0;
  const genderLabel = GENDER_NAMES[gender] || '男';
  const genderColor = gender === 'female' ? 'text-pink-500' : 'text-blue-500';

  // Compute the displayed Canglang Era year for each event so it tracks
  // the in-narrative age rather than the engine's internal counter.
  // Monotonic non-decreasing: if a later event's text age would go backward,
  // we hold the previous high so the timeline never rewinds.
  const displayAges = useMemo(() => {
    let last = 0;
    return eventLog.map((e) => {
      const ext = extractEventAge(e.text) ?? extractEventAge(e.expanded_text || '');
      const candidate = ext ?? e.age;
      last = Math.max(last, candidate);
      return last;
    });
  }, [eventLog]);

  const currentDisplayAge =
    displayAges.length > 0 ? displayAges[displayAges.length - 1] : age;

  return (
    <div className="min-h-screen flex flex-col relative">
      {/* Aurora animated background */}
      <div className="aurora-bg" />

      {/* Floating golden particles */}
      <div className="aurora-particles">
        {Array.from({ length: 14 }).map((_, i) => (
          <div
            key={i}
            className="aurora-particle"
            style={{
              left: `${5 + Math.random() * 90}%`,
              bottom: `${Math.random() * 100}%`,
              width: `${3 + Math.random() * 4}px`,
              height: `${3 + Math.random() * 4}px`,
              animation: `floatUp ${14 + Math.random() * 16}s linear infinite`,
              animationDelay: `${Math.random() * 12}s`,
            }}
          />
        ))}
      </div>

      {/* Top Status Bar */}
      <div className="border-b border-scroll-gold-dim/15 p-4 relative z-10"
           style={{ background: 'rgba(255,253,245,0.92)', backdropFilter: 'blur(12px)' }}>
        <div className="max-w-2xl mx-auto flex items-center justify-between gap-4">
          {/* Realm & Age & Gender */}
          <div className="flex items-center gap-3">
            <span className={`text-2xl font-kai tracking-widest ${REALM_COLORS[realm] || 'text-scroll-gold'}`}>
              {realmName}
            </span>
            <span className={`text-base font-kai ${genderColor}`} title="性别">
              {genderLabel}
            </span>
            <span className="text-scroll-text-dim text-sm font-kai">
              沧浪纪 {currentDisplayAge} 年
            </span>
          </div>


        </div>
      </div>

      {/* Main Content - Event Log */}
      <div className="flex-1 flex flex-col relative z-10">
        <div className="flex-1 p-4 md:p-6 overflow-y-auto max-h-[calc(100vh-160px)]">
          <div className="max-w-2xl mx-auto">
            {eventLog.length === 0 && (
              <div className="text-center py-20">
                <p className="text-lg mb-2 font-kai text-scroll-text">
                  你以{gender === 'female' ? '女身' : '男身'}降生于世间...
                </p>
                <p className="text-sm text-scroll-text-dim font-kai">点击「下一年」开始你的旅程</p>
              </div>
            )}

            {eventLog.map((event, i) => {
              const dispAge = displayAges[i];
              const showAge = i === 0 || displayAges[i - 1] !== dispAge;
              // Show category tag when we don't show a new year label
              const showCategory = !showAge && event.category && event.category !== 'common';
              const catName = CATEGORY_NAMES[event.category || 'common'] || '尘世';
              const catColor = CATEGORY_COLORS[event.category || 'common'] || 'text-stone-500';
              // Show expanded narrative for events that have been typed already
              // (i.e. older than typingIdx, or no narrative left to type).
              const isTyping = i === typingIdx;
              const shouldRenderExpanded =
                event.expanded_text && (typingIdx === -1 || i <= typingIdx);
              return (
                <div key={i}>
                  {showAge && (
                    <div className="flex items-center gap-3 mt-4 mb-2">
                      <span className="text-scroll-gold font-kai text-sm whitespace-nowrap">
                        沧浪纪 {dispAge} 年
                      </span>
                      <div className="flex-1 h-px bg-scroll-gold/20" />
                      {event.category && (
                        <span className={`font-kai text-xs whitespace-nowrap ${catColor}`}>
                          {catName}
                        </span>
                      )}
                    </div>
                  )}
                  {showCategory && (
                    <div className="flex items-center gap-3 mt-3 mb-1">
                      <span className={`font-kai text-xs whitespace-nowrap ${catColor}`}>
                        {catName}
                      </span>
                      <div className="flex-1 h-px bg-scroll-gold/10" />
                    </div>
                  )}
                  <div
                    className={getEventLineClass(event.type)}
                    style={{ animationDelay: `${(i % 5) * 0.1}s` }}
                  >
                    {event.text}
                  </div>
                  {shouldRenderExpanded && (
                    isTyping ? (
                      <TypewriterEvent
                        event={event}
                        speedMs={32}
                        onDone={() => handleTyped(i)}
                      />
                    ) : (
                      <div className="event-narrative">
                        {event.expanded_text}
                      </div>
                    )
                  )}
                </div>
              );
            })}
            <div ref={logEndRef} />
          </div>
        </div>

        {/* Bottom Control Bar */}
        <div className="border-t border-scroll-gold-dim/15 p-4 relative"
             style={{ background: 'rgba(255,253,245,0.92)', backdropFilter: 'blur(12px)' }}>
          <div className="max-w-2xl mx-auto flex items-center justify-center gap-4">
            {!isGameOver ? (
              <>
                <button
                  onClick={advanceYear}
                  disabled={loading || autoPlay}
                  className={`ancient-button font-kai tracking-[0.3em] ${loading || autoPlay ? 'opacity-40 cursor-not-allowed' : ''}`}
                >
                  {loading ? '推演中...' : '流年'}
                </button>
                <button
                  onClick={toggleAutoPlay}
                  className={`px-4 py-2 border text-sm font-kai tracking-widest transition-all rounded-sm ${
                    autoPlay
                      ? 'border-scroll-red/40 text-scroll-red hover:bg-scroll-red/5'
                      : 'border-scroll-gold-dim/30 text-scroll-gold hover:bg-scroll-gold/5'
                  }`}
                >
                  {autoPlay ? '暂停' : '自动'}
                </button>
              </>
            ) : (
              <div className="text-center">
                <p className="text-scroll-gold font-kai text-lg animate-pulse tracking-widest">
                  命运终局 · 正在推演结果...
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
