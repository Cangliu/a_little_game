import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import type { GameEvent, NextYearResponse, SectInfo } from '../utils/types';
import { REALM_NAMES, REALM_COLORS, GENDER_NAMES, CATEGORY_NAMES, CATEGORY_COLORS } from '../utils/types';
import { nextYear, nextYearStream, makeChoice } from '../utils/api';
import { SceneBg } from '../components/SceneBg';
import { SceneCG } from '../components/SceneCG';
import { BREAKTHROUGH_CG, EVENT_CG, pickRandom, getPortrait } from '../config/sceneConfig';

// Attribute display names for check_attribute
const ATTR_DISPLAY: Record<string, string> = {
  constitution: '根骨',
  comprehension: '悟性',
  fortune: '福缘',
  charisma: '魅力',
  willpower: '心性',
};

/**
 * Extract the character age referenced in event narrative text.
 */
function parseChineseNumber(s: string): number {
  const map: Record<string, number> = {
    零: 0, 一: 1, 二: 2, 两: 2, 三: 3, 四: 4,
    五: 5, 六: 6, 七: 7, 八: 8, 九: 9,
  };
  if (s === '十') return 10;
  if (s.startsWith('十')) return 10 + (map[s[1]] ?? 0);
  if (s.endsWith('十')) return (map[s[0]] ?? 0) * 10;
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
  const arab = text.match(/(\d+)\s*岁/);
  if (arab) return parseInt(arab[1], 10);
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
 * Highlight NPC names in narrative text by wrapping them in styled spans.
 */
function highlightNpcNames(text: string, npcNames: string[]): React.ReactNode {
  if (!text || npcNames.length === 0) return text;
  // Build regex from NPC names (escape special chars, sort by length desc for greedy match)
  const escaped = npcNames
    .filter((n) => n.length >= 2)
    .sort((a, b) => b.length - a.length)
    .map((n) => n.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  if (escaped.length === 0) return text;
  const regex = new RegExp(`(${escaped.join('|')})`, 'g');
  const parts = text.split(regex);
  if (parts.length === 1) return text;
  return parts.map((part, i) =>
    npcNames.includes(part)
      ? <span key={i} className="npc-highlight">{part}</span>
      : part
  );
}

function TypewriterEvent({
  event,
  speedMs = 35,
  onDone,
  npcNames = [],
}: {
  event: GameEvent;
  speedMs?: number;
  onDone?: () => void;
  npcNames?: string[];
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
          {done ? highlightNpcNames(shown, npcNames) : shown}
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
  // Player choice system
  const [isChoosing, setIsChoosing] = useState(false);
  const [choiceEvent, setChoiceEvent] = useState<GameEvent | null>(null);
  const [choiceResult, setChoiceResult] = useState<{
    is_success: boolean;
    result_text: string;
    choice_text: string;
    final_success_rate: number;
    effects: Record<string, number>;
  } | null>(null);
  // Sect info state
  const [sectInfo, setSectInfo] = useState<SectInfo | null>(null);
  const [aiEnhanced, setAiEnhanced] = useState(false);
  const [tension, setTension] = useState(0);
  const [npcNames, setNpcNames] = useState<string[]>([]);
  const [streamingNarrative, setStreamingNarrative] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState(false);
  // CG system (Layer 2)
  const [cgImage, setCgImage] = useState<string | null>(null);
  const [showCG, setShowCG] = useState(false);
  const [cgLabel, setCgLabel] = useState<string>('');
  const [cgDuration, setCgDuration] = useState(3000);
  const prevRealmRef = useRef(0);
  // Typing
  const [typingIdx, setTypingIdx] = useState<number>(-1);
  const logEndRef = useRef<HTMLDivElement>(null);
  const autoPlayRef = useRef(false);

  const dismissCG = useCallback(() => setShowCG(false), []);

  useEffect(() => {
    autoPlayRef.current = autoPlay;
  }, [autoPlay]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [eventLog, typingIdx]);

  // Auto-save game state to localStorage every time key state changes
  useEffect(() => {
    if (!gameId || isGameOver) return;
    try {
      const saveData = {
        gameId,
        age,
        realm,
        realmName,
        cultivation,
        cultivationMax,
        eventLogLength: eventLog.length,
        timestamp: Date.now(),
      };
      localStorage.setItem(`autosave_${gameId}`, JSON.stringify(saveData));
      // Also keep a "last active game" pointer
      localStorage.setItem('last_active_game', gameId);
    } catch {
      // localStorage full or unavailable, silently ignore
    }
  }, [gameId, age, realm, isGameOver]);

  const advanceYear = async () => {
    if (loading || isGameOver) return;
    setLoading(true);
    setStreamingNarrative('');
    setIsStreaming(false);
    try {
      // Try streaming first
      let streamSuccess = false;
      let streamStarted = false; // Track if server already mutated state
      try {
        await nextYearStream(
          gameId,
          // onState: update UI immediately with game state
          (stateData) => {
            streamStarted = true; // Server has advanced game state
            const s = stateData as Record<string, any>;
            if (s.age !== undefined) setAge(s.age);
            if (s.realm !== undefined) {
              const newRealm = s.realm as number;
              if (newRealm > prevRealmRef.current && prevRealmRef.current > 0) {
                const pool = BREAKTHROUGH_CG[newRealm] || [];
                if (pool.length > 0) {
                  setCgImage(pickRandom(pool));
                  setCgLabel(`突破 · ${REALM_NAMES[newRealm] || ''}`);
                  setCgDuration(3500);
                  setShowCG(true);
                }
              }
              prevRealmRef.current = newRealm;
              setRealm(newRealm);
            }
            if (s.realm_name) setRealmName(s.realm_name);
            if (s.cultivation !== undefined) setCultivation(s.cultivation);
            if (s.cultivation_max !== undefined) setCultivationMax(s.cultivation_max);
            // Add events (without expanded_text) to log
            if (s.events && Array.isArray(s.events)) {
              setEventLog((prev) => [...prev, ...s.events]);
            }
            if (s.tension !== undefined) setTension(s.tension);
            if (s.npc_relationships && Array.isArray(s.npc_relationships)) {
              setNpcNames(s.npc_relationships.map((n: any) => n.name).filter(Boolean));
            }
            setIsStreaming(true);
            setStreamingNarrative('');
          },
          // onNarrativeChunk: append text in real-time
          (chunk) => {
            setStreamingNarrative((prev) => prev + chunk);
          },
          // onDone: finalize
          (doneData) => {
            const d = doneData as Record<string, any>;
            if (d.ai_enhanced !== undefined) setAiEnhanced(d.ai_enhanced);
            if (d.is_dead || d.is_ascended) {
              setIsGameOver(true);
              setAutoPlay(false);
              setTimeout(() => onGameEnd(gameId), 2500);
            }
            if (d.has_choice && d.choice_event) {
              setChoiceEvent(d.choice_event as GameEvent);
              setIsChoosing(true);
              setAutoPlay(false);
              // CG for choice event
              const cat = (d.choice_event as GameEvent).category || 'fortune';
              const pool = EVENT_CG[cat] || EVENT_CG['fortune'];
              setCgImage(pickRandom(pool));
              setCgLabel('命运交叉点');
              setCgDuration(0); // Manual dismiss (stays until choice made)
              setShowCG(true);
            }
            // Commit streaming narrative into the last event's expanded_text
            setStreamingNarrative((narrative) => {
              if (narrative) {
                setEventLog((prev) => {
                  const updated = [...prev];
                  const lastIdx = updated.length - 1;
                  if (lastIdx >= 0) {
                    updated[lastIdx] = { ...updated[lastIdx], expanded_text: narrative };
                  }
                  return updated;
                });
              }
              return '';
            });
            setIsStreaming(false);
            // Auto-play continuation
            if (!d.is_dead && !d.is_ascended && !d.has_choice && autoPlayRef.current) {
              setTimeout(() => advanceYear(), 400);
            }
          },
        );
        streamSuccess = true;
      } catch (streamErr) {
        console.warn('Stream failed, falling back to sync:', streamErr);
        setIsStreaming(false);
        setStreamingNarrative('');
      }

      // Fallback to sync API ONLY if stream never started (server state unchanged)
      if (!streamSuccess && !streamStarted) {
        const result = await nextYear(gameId);
        setAge(result.age);
        setRealm(result.realm);
        // Breakthrough CG detection (fallback path)
        if (result.realm > prevRealmRef.current && prevRealmRef.current > 0) {
          const pool = BREAKTHROUGH_CG[result.realm] || [];
          if (pool.length > 0) {
            setCgImage(pickRandom(pool));
            setCgLabel(`突破 · ${REALM_NAMES[result.realm] || ''}`);
            setCgDuration(3500);
            setShowCG(true);
          }
        }
        prevRealmRef.current = result.realm;
        setRealmName(result.realm_name);
        setCultivation(result.cultivation);
        setCultivationMax(result.cultivation_max);
        if (result.sect_info !== undefined) setSectInfo(result.sect_info ?? null);
        if (result.ai_enhanced !== undefined) setAiEnhanced(result.ai_enhanced);
        if (result.tension !== undefined) setTension(result.tension);
        if (result.npc_relationships && Array.isArray(result.npc_relationships)) {
          setNpcNames(result.npc_relationships.map((n) => n.name).filter(Boolean));
        }

        setEventLog((prev) => {
          const next = [...prev, ...result.events];
          const firstNewIdx = prev.length;
          const firstWithExpanded = result.events.findIndex((e) => e.expanded_text);
          setTypingIdx(
            firstWithExpanded >= 0 ? firstNewIdx + firstWithExpanded : -1
          );
          return next;
        });

        if (result.has_choice && result.choice_event) {
          setChoiceEvent(result.choice_event);
          setIsChoosing(true);
          setAutoPlay(false);
          // CG for choice event (fallback path)
          const cat = result.choice_event.category || 'fortune';
          const pool = EVENT_CG[cat] || EVENT_CG['fortune'];
          setCgImage(pickRandom(pool));
          setCgLabel('命运交叉点');
          setCgDuration(0);
          setShowCG(true);
          setLoading(false);
          return;
        }

        if (result.is_dead || result.is_ascended) {
          setIsGameOver(true);
          setAutoPlay(false);
          setTimeout(() => onGameEnd(gameId), 2500);
        } else if (autoPlayRef.current) {
          const hasNarrative = result.events.some((e) => e.expanded_text);
          setTimeout(() => advanceYear(), hasNarrative ? 1800 : 400);
        }
      }
    } catch (err) {
      console.error('Error advancing year:', err);
      setAutoPlay(false);
    }
    setLoading(false);
  };

  const handleTyped = (idx: number) => {
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

  const handleChoice = async (index: number) => {
    if (!choiceEvent || !choiceEvent.id) return;
    try {
      const result = await makeChoice(gameId, choiceEvent.id, index);
      const branch = choiceEvent.branches?.[index];
      // Show result feedback overlay
      setIsChoosing(false);
      setShowCG(false); // Dismiss choice CG
      setChoiceResult({
        is_success: result.is_success,
        result_text: result.result_text,
        choice_text: result.choice_text,
        final_success_rate: result.final_success_rate,
        effects: result.is_success
          ? (branch?.effects || {})
          : (branch?.failure_effects || {}),
      });
      // After 2.5s, dismiss result and add to event log
      setTimeout(() => {
        setEventLog((prev) => [
          ...prev,
          {
            text: `── 你选择了「${result.choice_text}」——${result.is_success ? '成功' : '失败'}`,
            expanded_text: result.result_text,
            type: 'important' as const,
            category: 'common',
            age: age,
          },
        ]);
        setChoiceResult(null);
        setChoiceEvent(null);
      }, 2500);
    } catch (err) {
      console.error('Choice error:', err);
    }
  };

  const getEventLineClass = (type: string) => {
    switch (type) {
      case 'important': return 'event-line event-line-important';
      case 'danger': return 'event-line event-line-danger';
      case 'fortune': return 'event-line event-line-fortune';
      case 'special': return 'event-line event-line-fortune';
      case 'saga_omen': return 'event-line event-line-saga-omen';
      default: return 'event-line';
    }
  };

  const cultPercent = cultivationMax > 0 ? Math.min((cultivation / cultivationMax) * 100, 100) : 0;
  const genderLabel = GENDER_NAMES[gender] || '男';
  const genderColor = gender === 'female' ? 'text-pink-500' : 'text-blue-500';

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
      {/* Layer 1: Dynamic realm-based background */}
      <SceneBg realm={realm} />

      {/* Layer 2: CG illustration overlay */}
      <SceneCG
        show={showCG}
        imageSrc={cgImage}
        onDismiss={dismissCG}
        duration={cgDuration}
        label={cgLabel}
      />

      {/* Layer 3: Character portrait (subtle, right side) */}
      <img
        src={getPortrait(gender, realm)}
        alt=""
        className="character-portrait"
        loading="lazy"
        draggable={false}
      />

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

      {/* Top Status Bar — Enhanced */}
      <div className="border-b border-scroll-gold-dim/15 p-3 relative z-10"
           style={{ background: 'rgba(255,253,245,0.92)', backdropFilter: 'blur(12px)' }}>
        <div className="max-w-2xl mx-auto">
          {/* Row 1: Realm, Gender, Age, Sect badge */}
          <div className="flex items-center justify-between gap-3 mb-2">
            <div className="flex items-center gap-3">
              <span className={`text-2xl font-kai tracking-widest ${REALM_COLORS[realm] || 'text-scroll-gold'}`}>
                {realmName}
              </span>
              <span className={`text-base font-kai ${genderColor}`}>{genderLabel}</span>
              <span className="text-scroll-text-dim text-sm font-kai">
                <span className="text-scroll-gold tracking-wider">沧浪纪</span>
                <span className="mx-0.5 text-scroll-gold-dim font-bold text-base" style={{ textShadow: '0 0 3px rgba(139,105,20,0.2)' }}>{currentDisplayAge}</span>
                <span className="text-scroll-gold/80">年</span>
              </span>
            </div>
            {/* Sect badge (static display, no panel) */}
            <div className="flex items-center gap-2">
              {sectInfo ? (
                <span className="font-kai text-xs px-2 py-0.5 rounded border border-emerald-400/40 text-emerald-700 bg-emerald-50/50">
                  {sectInfo.name}·{sectInfo.rank}
                </span>
              ) : (
                <span className="font-kai text-xs text-stone-400/70 px-2 py-0.5">游方散修</span>
              )}
            </div>
          </div>
          {/* Row 2: Cultivation bar + quick buttons */}
          <div className="flex items-center gap-3">
            {/* Cultivation progress - 灵脉风格 */}
            <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(139,105,20,0.08)', boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.05)' }}>
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{
                  width: `${cultPercent}%`,
                  background: 'linear-gradient(90deg, #2d7a4f 0%, #3daa70 40%, #d4b96a 80%, #8b6914 100%)',
                  boxShadow: '0 0 4px rgba(61,170,112,0.3)',
                }}
              />
            </div>
            <span className="text-xs text-scroll-text-dim font-kai whitespace-nowrap">
              {cultivation}/{cultivationMax}
            </span>
            {/* 天劫气息指示器: 「煞」字 */}
            {tension > 0 && (
              <div
                className="flex items-center gap-1"
                title={`天劫气息: ${tension.toFixed(0)}`}
              >
                <span className={`font-kai text-xs transition-all duration-500 ${
                  tension >= 60 ? 'text-red-500 animate-pulse' :
                  tension >= 30 ? 'text-orange-400' :
                  'text-amber-300/70'
                }`}>
                  煞
                </span>
                <div className="w-6 h-1.5 rounded-full bg-stone-200/40 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${Math.min(tension, 100)}%`,
                      background: tension >= 60 ? '#ef4444' :
                                  tension >= 30 ? '#f97316' : '#fbbf24',
                    }}
                  />
                </div>
              </div>
            )}
            {/* 灵玉指示器: AI叙事状态 */}
            <div
              className="flex items-center gap-0.5"
              title={aiEnhanced ? '灵玉开光 · 天道演算中' : '灵玉暗淡 · 凡俗模式'}
            >
              <span
                className={`font-kai text-xs transition-all duration-700 ${
                  aiEnhanced
                    ? 'text-emerald-500 drop-shadow-[0_0_4px_rgba(52,211,153,0.6)] animate-pulse'
                    : 'text-stone-400/50'
                }`}
              >
                灵
              </span>
            </div>

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
                <p className="text-sm text-scroll-text-dim font-kai">点击「流年」开始你的旅程</p>
              </div>
            )}

            {eventLog.map((event, i) => {
              const dispAge = displayAges[i];
              const showAge = i === 0 || displayAges[i - 1] !== dispAge;
              const showCategory = !showAge && event.category && event.category !== 'common';
              const catName = CATEGORY_NAMES[event.category || 'common'] || '尘世';
              const catColor = CATEGORY_COLORS[event.category || 'common'] || 'text-stone-500';
              const isTyping = i === typingIdx;
              const isLastEvent = i === eventLog.length - 1;
              const shouldRenderExpanded =
                event.expanded_text && (typingIdx === -1 || i <= typingIdx);
              // Show streaming narrative for last event
              const showStreaming = isLastEvent && isStreaming && !event.expanded_text;
              return (
                <div key={i}>
                  {showAge && (
                    <div className="flex items-center gap-3 mt-4 mb-2">
                      <span className="text-scroll-gold font-kai text-sm whitespace-nowrap">
                        <span className="tracking-wider">沧浪纪</span>
                        <span className="mx-0.5 font-bold text-base" style={{ textShadow: '0 0 2px rgba(139,105,20,0.15)' }}>{dispAge}</span>
                        <span className="opacity-80">年</span>
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
                  {showStreaming && streamingNarrative && (
                    <div className="event-narrative">
                      {highlightNpcNames(streamingNarrative, npcNames)}
                      <span className="tw-cursor">▊</span>
                    </div>
                  )}
                  {shouldRenderExpanded && (
                    isTyping ? (
                      <TypewriterEvent
                        event={event}
                        speedMs={32}
                        onDone={() => handleTyped(i)}
                        npcNames={npcNames}
                      />
                    ) : (
                      <div className="event-narrative">
                        {highlightNpcNames(event.expanded_text!, npcNames)}
                      </div>
                    )
                  )}
                </div>
              );
            })}
            <div ref={logEndRef} />
          </div>
        </div>

        {/* Choice Panel Overlay — Enhanced with success rates */}
        {isChoosing && choiceEvent && choiceEvent.branches && (
          <div className="absolute inset-0 z-20 flex items-center justify-center"
               style={{ background: 'rgba(0,0,0,0.45)', backdropFilter: 'blur(4px)' }}>
            <div className="max-w-lg w-full mx-4 p-6 rounded-lg border border-scroll-gold/30"
                 style={{ background: 'rgba(255,253,245,0.97)' }}>
              <p className="text-center text-scroll-text font-kai text-lg mb-1 tracking-wider">
                命运交叉点
              </p>
              <p className="text-center text-scroll-text-dim font-kai text-sm mb-5">
                {choiceEvent.text}
              </p>
              <div className="space-y-3">
                {choiceEvent.branches.map((branch, i) => (
                  <button
                    key={i}
                    onClick={() => handleChoice(i)}
                    className="w-full text-left px-4 py-3 border border-scroll-gold-dim/30 rounded-sm
                               hover:border-scroll-gold hover:bg-scroll-gold/5 transition-all
                               font-kai text-scroll-text tracking-wide group"
                  >
                    <div className="flex items-start gap-2">
                      <span className="text-scroll-gold">{['⚔', '🛡', '✧'][i] || '❖'}</span>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span>{branch.text}</span>
                          {branch.success_rate != null && branch.success_rate < 100 && (
                            <span className={`text-xs px-1.5 py-0.5 rounded ${
                              branch.success_rate >= 70 ? 'bg-emerald-50 text-emerald-600' :
                              branch.success_rate >= 50 ? 'bg-amber-50 text-amber-600' :
                              'bg-red-50 text-red-500'
                            }`}>
                              {branch.success_rate}%
                            </span>
                          )}
                        </div>
                        {/* Success rate bar + check attribute hint */}
                        {branch.success_rate != null && branch.success_rate < 100 && (
                          <div className="mt-1.5 space-y-1">
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-1.5 rounded-full bg-stone-200/80 overflow-hidden">
                                <div
                                  className="h-full rounded-full transition-all"
                                  style={{
                                    width: `${branch.success_rate}%`,
                                    background: branch.success_rate >= 70 ? '#10b981' :
                                               branch.success_rate >= 50 ? '#f59e0b' : '#ef4444',
                                  }}
                                />
                              </div>
                              {branch.check_attribute && (
                                <span className="text-xs text-stone-400 whitespace-nowrap">
                                  {ATTR_DISPLAY[branch.check_attribute] || branch.check_attribute}越高越好
                                </span>
                              )}
                            </div>
                          </div>
                        )}
                        {/* Show effects on hover */}
                        <div className="mt-1 text-xs text-stone-400 opacity-0 group-hover:opacity-100 transition-opacity">
                          <span className="text-emerald-500 mr-2">成功:</span>
                          {branch.effects && Object.entries(branch.effects).map(([k, v]) => {
                            if (k === 'add_tag') return null;
                            const sign = (v as number) > 0 ? '+' : '';
                            const label: Record<string, string> = {
                              cultivation: '修为', constitution: '根骨', comprehension: '悟性',
                              fortune: '福缘', charisma: '魅力', willpower: '心性',
                            };
                            return (
                              <span key={k} className={`mr-1.5 ${(v as number) > 0 ? 'text-emerald-500' : 'text-red-400'}`}>
                                {label[k] || k}{sign}{v}
                              </span>
                            );
                          })}
                          {branch.failure_effects && Object.keys(branch.failure_effects).length > 0 && (
                            <>
                              <span className="text-red-400 ml-2 mr-1">失败:</span>
                              {Object.entries(branch.failure_effects).map(([k, v]) => {
                                if (k === 'add_tag') return null;
                                const sign = (v as number) > 0 ? '+' : '';
                                const label: Record<string, string> = {
                                  cultivation: '修为', constitution: '根骨', comprehension: '悟性',
                                  fortune: '福缘', charisma: '魅力', willpower: '心性',
                                };
                                return (
                                  <span key={k} className={`mr-1.5 ${(v as number) > 0 ? 'text-emerald-500' : 'text-red-400'}`}>
                                    {label[k] || k}{sign}{v}
                                  </span>
                                );
                              })}
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Choice Result Feedback Overlay */}
        {choiceResult && (
          <div className="absolute inset-0 z-30 flex items-center justify-center"
               style={{ background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)' }}>
            <div className="max-w-md w-full mx-4 p-6 rounded-lg border text-center"
                 style={{
                   background: 'rgba(255,253,245,0.97)',
                   borderColor: choiceResult.is_success ? 'rgba(16,185,129,0.4)' : 'rgba(239,68,68,0.4)',
                 }}>
              {/* Success/Failure badge */}
              <div className={`text-4xl mb-3 ${
                choiceResult.is_success ? 'animate-bounce' : 'animate-pulse'
              }`}>
                {choiceResult.is_success ? '✨' : '⚡'}
              </div>
              <p className={`text-2xl font-kai tracking-widest mb-2 ${
                choiceResult.is_success ? 'text-emerald-600' : 'text-red-500'
              }`}>
                {choiceResult.is_success ? '成功' : '失败'}
              </p>
              <p className="text-xs text-stone-400 font-kai mb-3">
                「{choiceResult.choice_text}」· 成功率 {choiceResult.final_success_rate}%
              </p>
              {/* Effect changes */}
              <div className="flex items-center justify-center gap-3 mb-4">
                {Object.entries(choiceResult.effects).map(([k, v]) => {
                  if (k === 'add_tag') return null;
                  const sign = (v as number) > 0 ? '+' : '';
                  const label: Record<string, string> = {
                    cultivation: '修为', constitution: '根骨', comprehension: '悟性',
                    fortune: '福缘', charisma: '魅力', willpower: '心性',
                  };
                  return (
                    <span key={k} className={`text-lg font-kai font-bold ${
                      (v as number) > 0 ? 'text-emerald-500' : 'text-red-400'
                    }`}>
                      {label[k] || k} {sign}{v}
                    </span>
                  );
                })}
              </div>
              {/* Result narrative preview */}
              <p className="text-sm text-scroll-text font-kai leading-relaxed">
                {choiceResult.result_text.slice(0, 80)}{choiceResult.result_text.length > 80 ? '...' : ''}
              </p>
            </div>
          </div>
        )}

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
                  {loading ? '光阴飞逝...' : '流年'}
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
                  命运终局 · 往事如烟，尘埃落定...
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
