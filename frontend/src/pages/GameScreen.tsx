import { useState, useEffect, useRef, useMemo } from 'react';
import type { GameEvent, NextYearResponse, SectInfo, NPCRelationship } from '../utils/types';
import { REALM_NAMES, REALM_COLORS, GENDER_NAMES, CATEGORY_NAMES, CATEGORY_COLORS } from '../utils/types';
import { nextYear, nextYearStream, makeChoice } from '../utils/api';

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

/** Tension indicator color */
function getTensionColor(t: number): string {
  if (t >= 70) return 'bg-red-500';
  if (t >= 40) return 'bg-amber-500';
  return 'bg-emerald-500';
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
  const [choiceResult, setChoiceResult] = useState<string | null>(null);
  // New: tension, sect, NPC state
  const [tension, setTension] = useState(0);
  const [sectInfo, setSectInfo] = useState<SectInfo | null>(null);
  const [npcRelationships, setNpcRelationships] = useState<NPCRelationship[]>([]);
  const [showNpcPanel, setShowNpcPanel] = useState(false);
  const [showSectPanel, setShowSectPanel] = useState(false);
  const [aiEnhanced, setAiEnhanced] = useState(false);
  const [streamingNarrative, setStreamingNarrative] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState(false);
  // Typing
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
            if (s.realm !== undefined) setRealm(s.realm);
            if (s.realm_name) setRealmName(s.realm_name);
            if (s.cultivation !== undefined) setCultivation(s.cultivation);
            if (s.cultivation_max !== undefined) setCultivationMax(s.cultivation_max);
            if (s.tension !== undefined) setTension(s.tension);
            // Add events (without expanded_text) to log
            if (s.events && Array.isArray(s.events)) {
              setEventLog((prev) => [...prev, ...s.events]);
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
        setRealmName(result.realm_name);
        setCultivation(result.cultivation);
        setCultivationMax(result.cultivation_max);
        if (result.tension !== undefined) setTension(result.tension);
        if (result.sect_info !== undefined) setSectInfo(result.sect_info ?? null);
        if (result.npc_relationships) setNpcRelationships(result.npc_relationships);
        if (result.ai_enhanced !== undefined) setAiEnhanced(result.ai_enhanced);

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
      if (result.result_text) {
        setEventLog((prev) => [
          ...prev,
          {
            text: `── 你选择了「${result.choice_text}」`,
            expanded_text: result.result_text,
            type: 'important' as const,
            category: 'common',
            age: age,
          },
        ]);
      }
      setChoiceEvent(null);
      setIsChoosing(false);
      setChoiceResult(null);
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
                沧浪纪 {currentDisplayAge} 年
              </span>
            </div>
            {/* Sect badge */}
            <div className="flex items-center gap-2">
              {sectInfo ? (
                <span className="sect-badge font-kai text-xs px-2 py-0.5 rounded border border-emerald-400/40 text-emerald-700 bg-emerald-50/50">
                  {sectInfo.name}·{sectInfo.rank}
                </span>
              ) : (
                <span className="font-kai text-xs text-stone-400 px-2 py-0.5">散修</span>
              )}
            </div>
          </div>
          {/* Row 2: Cultivation bar + Tension indicator + quick buttons */}
          <div className="flex items-center gap-3">
            {/* Cultivation progress */}
            <div className="flex-1 cultivation-bar h-2 rounded-full bg-stone-200/60 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${cultPercent}%`,
                  background: 'linear-gradient(90deg, #6366f1, #a78bfa, #f59e0b)',
                }}
              />
            </div>
            <span className="text-xs text-scroll-text-dim font-kai whitespace-nowrap">
              {cultivation}/{cultivationMax}
            </span>
            {/* Tension indicator */}
            <div className="flex items-center gap-1" title={`张力 ${Math.round(tension)}/100`}>
              <span className="text-xs">🔥</span>
              <div className="w-12 h-1.5 rounded-full bg-stone-200/60 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${getTensionColor(tension)}`}
                  style={{ width: `${tension}%` }}
                />
              </div>
            </div>
            {/* 灵玉指示器: AI叙事状态 */}
            <div
              className="flex items-center gap-0.5"
              title={aiEnhanced ? '灵玉开光 · AI叙事开启' : '灵玉暗淡 · 规则模式'}
            >
              <span
                className={`text-sm transition-all duration-700 ${
                  aiEnhanced
                    ? 'text-emerald-400 drop-shadow-[0_0_6px_rgba(52,211,153,0.8)] animate-pulse'
                    : 'text-stone-400/60 grayscale'
                }`}
                style={{ filter: aiEnhanced ? 'none' : 'saturate(0.2)' }}
              >
                💎
              </span>
            </div>
            {/* NPC / Sect toggle buttons */}
            <button
              onClick={() => setShowNpcPanel(!showNpcPanel)}
              className={`text-xs font-kai px-2 py-0.5 rounded border transition-all ${
                showNpcPanel ? 'border-teal-500 text-teal-600 bg-teal-50' : 'border-stone-300/50 text-stone-500 hover:text-teal-600'
              }`}
            >
              人脉
            </button>
            <button
              onClick={() => setShowSectPanel(!showSectPanel)}
              className={`text-xs font-kai px-2 py-0.5 rounded border transition-all ${
                showSectPanel ? 'border-emerald-500 text-emerald-600 bg-emerald-50' : 'border-stone-300/50 text-stone-500 hover:text-emerald-600'
              }`}
            >
              宗门
            </button>
          </div>
        </div>
      </div>

      {/* Collapsible Info Panels */}
      {(showNpcPanel || showSectPanel) && (
        <div className="border-b border-scroll-gold-dim/10 px-4 py-3 relative z-10"
             style={{ background: 'rgba(255,253,245,0.95)' }}>
          <div className="max-w-2xl mx-auto flex gap-4 flex-wrap">
            {/* NPC Panel */}
            {showNpcPanel && (
              <div className="info-panel flex-1 min-w-[200px]">
                <h4 className="text-xs font-kai text-teal-600 mb-2 tracking-wider">人际关系</h4>
                {npcRelationships.length > 0 ? (
                  <div className="space-y-1.5">
                    {npcRelationships.map((npc, i) => (
                      <div key={i} className="npc-card flex items-center gap-2 text-xs">
                        <span className={`font-kai ${npc.is_alive ? 'text-scroll-text' : 'text-stone-400 line-through'}`}>
                          {npc.name}
                        </span>
                        <span className="text-stone-400">·</span>
                        <span className="text-stone-500">{npc.relation_type}</span>
                        <div className="flex-1" />
                        <div className="w-12 h-1.5 rounded-full bg-stone-200 overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all"
                            style={{
                              width: `${npc.sentiment}%`,
                              background: npc.sentiment >= 70 ? '#f59e0b' : npc.sentiment >= 40 ? '#9ca3af' : '#ef4444',
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-stone-400 font-kai">尚无重要人际关系</p>
                )}
              </div>
            )}
            {/* Sect Panel */}
            {showSectPanel && (
              <div className="info-panel flex-1 min-w-[200px]">
                <h4 className="text-xs font-kai text-emerald-600 mb-2 tracking-wider">宗门信息</h4>
                {sectInfo ? (
                  <div className="space-y-1 text-xs font-kai">
                    <div className="flex justify-between">
                      <span className="text-stone-500">宗门</span>
                      <span className="text-scroll-text">{sectInfo.name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-stone-500">类型</span>
                      <span className="text-scroll-text">{sectInfo.sect_type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-stone-500">职位</span>
                      <span className="text-emerald-700">{sectInfo.rank}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-stone-500">贡献</span>
                      <span className="text-amber-700">{sectInfo.contribution}</span>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-stone-400 font-kai">散修 · 无宗门归属</p>
                )}
              </div>
            )}
          </div>
        </div>
      )}

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
                  {showStreaming && streamingNarrative && (
                    <div className="event-narrative">
                      {streamingNarrative}
                      <span className="tw-cursor">▊</span>
                    </div>
                  )}
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

        {/* Choice Panel Overlay — Enhanced */}
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
                        <span>{branch.text}</span>
                        {/* Show effect hints */}
                        {branch.effects && Object.keys(branch.effects).length > 0 && (
                          <div className="mt-1 text-xs text-stone-400 opacity-0 group-hover:opacity-100 transition-opacity">
                            {Object.entries(branch.effects).map(([k, v]) => {
                              if (k === 'add_tag') return null;
                              const sign = (v as number) > 0 ? '+' : '';
                              const label: Record<string, string> = {
                                cultivation: '修为', constitution: '根骨', comprehension: '悟性',
                                fortune: '福缘', charisma: '魅力', willpower: '心性',
                              };
                              return (
                                <span key={k} className={`mr-2 ${(v as number) > 0 ? 'text-emerald-500' : 'text-red-400'}`}>
                                  {label[k] || k}{sign}{v}
                                </span>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
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
