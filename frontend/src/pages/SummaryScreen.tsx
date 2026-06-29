import { useState, useEffect } from 'react';
import type { LifeSummary, SectInfo, ChoiceHistoryItem, NPCRelationship, LifeEvent, EmotionalToken } from '../utils/types';
import { REALM_COLORS, GENDER_NAMES, CATEGORY_NAMES, CATEGORY_COLORS } from '../utils/types';
import { getSummary, getGameState, getLifeEvents } from '../utils/api';
import { SUMMARY_BACKGROUNDS, getPortrait } from '../config/sceneConfig';

interface SummaryScreenProps {
  gameId: string;
  onRestart: () => void;
}

export default function SummaryScreen({ gameId, onRestart }: SummaryScreenProps) {
  const [summary, setSummary] = useState<LifeSummary | null>(null);
  const [show, setShow] = useState(false);
  const [sectInfo, setSectInfo] = useState<SectInfo | null>(null);
  const [choiceHistory, setChoiceHistory] = useState<ChoiceHistoryItem[]>([]);
  const [npcRelationships, setNpcRelationships] = useState<NPCRelationship[]>([]);
  const [emotionalTokens, setEmotionalTokens] = useState<EmotionalToken[]>([]);
  const [lifeEvents, setLifeEvents] = useState<LifeEvent[]>([]);
  const [showTimeline, setShowTimeline] = useState(false);

  useEffect(() => {
    getSummary(gameId).then((data) => {
      setSummary(data);
      setTimeout(() => setShow(true), 300);
    });
    // Fetch extended state for sect/choices
    getGameState(gameId).then((state) => {
      if (state.sect_info) setSectInfo(state.sect_info);
      if (state.choice_history) setChoiceHistory(state.choice_history);
      if (state.npc_relationships) setNpcRelationships(state.npc_relationships);
      if (state.emotional_tokens) setEmotionalTokens(state.emotional_tokens);
    }).catch(() => {});
  }, [gameId]);

  if (!summary) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-scroll-gold font-kai text-lg animate-pulse tracking-widest">
          天道推演中...
        </p>
      </div>
    );
  }

  const isAscended = summary.death_reason === '飞升成仙';
  const isTribulationFailed = summary.death_reason === '渡劫陨落';
  const isTrappedInWorld = summary.death_reason === '困死人间';
  const isCombatDeath = summary.death_reason === '斗法陨落';

  const headerLabel = isAscended
    ? '— 飞升成仙 —'
    : isCombatDeath
    ? '— 斗法陨落 —'
    : isTribulationFailed
    ? '— 渡劫陨落 —'
    : isTrappedInWorld
    ? '— 困死人间 —'
    : '— 生死簿 —';

  return (
    <div
      className={`min-h-screen p-4 md:p-8 transition-all duration-1000 relative ${
        show ? 'opacity-100' : 'opacity-0'
      }`}
    >
      {/* Scene background based on ending */}
      <div className="scene-bg">
        <img
          src={
            isAscended ? SUMMARY_BACKGROUNDS.ascended
            : isCombatDeath ? SUMMARY_BACKGROUNDS.combat_death
            : isTribulationFailed ? SUMMARY_BACKGROUNDS.tribulation_failed
            : SUMMARY_BACKGROUNDS.default
          }
          alt=""
          className="scene-bg-img"
          style={{ opacity: 1 }}
          loading="lazy"
          draggable={false}
        />
        <div className="scene-bg-overlay" />
      </div>

      {/* Character portrait */}
      <img
        src={getPortrait(summary.gender || 'male', summary.max_realm)}
        alt=""
        className="character-portrait summary-portrait"
        loading="lazy"
        draggable={false}
      />

      {/* Floating petals */}
      {isAscended && (
        <div className="absolute inset-0 overflow-hidden pointer-events-none z-10">
          {Array.from({ length: 15 }).map((_, i) => (
            <div
              key={i}
              className="petal"
              style={{
                left: `${Math.random() * 100}%`,
                backgroundColor: ['#a29bfe', '#fd79a8', '#74b9ff', '#55efc4', '#ffeaa7'][i % 5],
                animation: `floatUp ${6 + Math.random() * 8}s linear infinite`,
                animationDelay: `${Math.random() * 5}s`,
                width: `${6 + Math.random() * 6}px`,
                height: `${6 + Math.random() * 6}px`,
              }}
            />
          ))}
        </div>
      )}

      <div className="max-w-lg mx-auto relative z-20">
        {/* Title */}
        <div className="text-center mb-8">
          <div className="text-scroll-text-dim text-sm font-kai tracking-[0.5em] mb-2">
            {headerLabel}
          </div>
          <h2
            className={`text-4xl font-kai tracking-[0.3em] mb-2 ${
              isAscended
                ? 'text-scroll-gold glow-text'
                : isCombatDeath
                ? 'text-red-600'
                : isTribulationFailed
                ? 'text-orange-500'
                : isTrappedInWorld
                ? 'text-purple-400'
                : 'text-scroll-text'
            }`}
          >
            {summary.title}
          </h2>
          <div className="ink-divider mx-auto max-w-xs" />
        </div>

        {/* Summary Panel */}
        <div className="scroll-panel p-6 mb-6">
          {/* Core Stats */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="text-center">
              <div className="text-scroll-text-dim text-xs font-kai mb-1">享年</div>
              <div className="text-2xl text-scroll-gold font-kai">
                {summary.total_age} 岁
                {summary.gender && (
                  <span
                    className={`ml-2 text-base ${
                      summary.gender === 'female' ? 'text-pink-500' : 'text-blue-500'
                    }`}
                  >
                    · {GENDER_NAMES[summary.gender] || ''}
                  </span>
                )}
              </div>
            </div>
            <div className="text-center">
              <div className="text-scroll-text-dim text-xs font-kai mb-1">最高境界</div>
              <div className={`text-2xl font-kai ${REALM_COLORS[summary.max_realm] || 'text-scroll-gold'}`}>
                {summary.max_realm_name}
              </div>
            </div>
            <div className="text-center">
              <div className="text-scroll-text-dim text-xs font-kai mb-1">死因</div>
              <div className="text-sm text-scroll-text font-kai">{summary.death_reason}</div>
            </div>
            <div className="text-center">
              <div className="text-scroll-text-dim text-xs font-kai mb-1">评分</div>
              <div className="text-2xl text-scroll-gold font-kai">{summary.score}</div>
            </div>
          </div>

          <div className="ink-divider" />

          {/* Key Events */}
          <div className="mb-4">
            <h3 className="text-scroll-text-dim text-xs font-kai tracking-widest mb-3 text-center">
              大事记
            </h3>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {summary.key_events.map((event, i) => (
                <div
                  key={i}
                  className="text-sm text-scroll-text font-kai pl-3 border-l-2 border-scroll-gold/30"
                >
                  {event}
                </div>
              ))}
            </div>
          </div>

          {/* Sect Achievement */}
          {sectInfo && (
            <>
              <div className="ink-divider" />
              <div className="mb-4">
                <h3 className="text-scroll-text-dim text-xs font-kai tracking-widest mb-3 text-center">
                  宗门成就
                </h3>
                <div className="grid grid-cols-2 gap-2 text-xs font-kai">
                  <div className="text-center">
                    <div className="text-stone-500">宗门</div>
                    <div className="text-emerald-700">{sectInfo.name}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-stone-500">最高职位</div>
                    <div className="text-emerald-700">{sectInfo.rank}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-stone-500">类型</div>
                    <div className="text-scroll-text">{sectInfo.sect_type}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-stone-500">总贡献</div>
                    <div className="text-amber-700">{sectInfo.contribution}</div>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* Key Choices */}
          {choiceHistory.length > 0 && (
            <>
              <div className="ink-divider" />
              <div className="mb-4">
                <h3 className="text-scroll-text-dim text-xs font-kai tracking-widest mb-3 text-center">
                  关键抉择
                </h3>
                <div className="space-y-2 max-h-36 overflow-y-auto">
                  {choiceHistory.slice(-5).map((ch, i) => (
                    <div key={i} className="text-xs font-kai pl-3 border-l-2 border-amber-400/40">
                      <span className="text-stone-400">{ch.age}岁时</span>
                      <span className="text-stone-500 mx-1">·</span>
                      <span className="text-scroll-text">「{ch.choice_text}」</span>
                      {ch.consequence_tag && (
                        <span className="ml-1 text-amber-600">#{ch.consequence_tag}</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* NPC Relationships Retrospective */}
          {npcRelationships.length > 0 && (
            <>
              <div className="ink-divider" />
              <div className="mb-4">
                <h3 className="text-scroll-text-dim text-xs font-kai tracking-widest mb-3 text-center">
                  红尘缘分
                </h3>
                <div className="space-y-2 max-h-36 overflow-y-auto">
                  {npcRelationships.map((npc, i) => {
                    const sentimentLabel = npc.sentiment >= 50 ? '情深义重' : npc.sentiment >= 20 ? '有所交情' : npc.sentiment >= 0 ? '波澜不惊' : npc.sentiment >= -30 ? '心有嫌隙' : '仇深似海';
                    const sentimentColor = npc.sentiment >= 50 ? 'text-pink-500' : npc.sentiment >= 20 ? 'text-amber-500' : npc.sentiment >= 0 ? 'text-stone-400' : npc.sentiment >= -30 ? 'text-orange-500' : 'text-red-500';
                    return (
                      <div key={i} className="flex items-center justify-between text-xs font-kai px-2">
                        <span className="text-scroll-text">
                          {npc.name}
                          <span className="text-stone-500 ml-1">·{npc.relation_type}</span>
                        </span>
                        <span className="flex items-center gap-2">
                          <span className={sentimentColor}>{sentimentLabel}</span>
                          {!npc.is_alive && <span className="text-stone-600">（已陨落）</span>}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}

          {/* 随身之物 — 情感道具玉佩风格 */}
          {emotionalTokens.length > 0 && (
            <>
              <div className="ink-divider" />
              <div className="mb-4">
                <h3 className="text-scroll-text-dim text-xs font-kai tracking-widest mb-3 text-center">
                  随身之物
                </h3>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {emotionalTokens.map((token, i) => (
                    <div key={i} className="flex items-start gap-2 px-2 py-1.5 rounded bg-amber-50/40 border border-amber-200/30">
                      <span className="text-base shrink-0 mt-0.5" style={{ textShadow: '0 0 4px rgba(180,140,60,0.4)' }}>
                        🧊
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-kai text-amber-800 font-bold truncate">
                            {token.name}
                          </span>
                          <span className="text-xs text-stone-400 font-kai shrink-0 ml-1">
                            {token.source_age}岁得
                          </span>
                        </div>
                        <p className="text-xs text-stone-500 font-kai leading-relaxed mt-0.5 line-clamp-2">
                          {token.description}
                        </p>
                        {token.source_npc && (
                          <span className="text-xs text-amber-600/80 font-kai">
                            —— {token.source_npc} 所赠
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Score Rating */}
        <div className="text-center mb-8">
          <div className="text-scroll-text-dim text-xs font-kai tracking-widest mb-2">
            天道评语
          </div>
          <p className="text-scroll-gold font-kai text-lg italic">
            {summary.score >= 500
              ? '「此子逆天改命，已破碎虚空，飞升灵界！」'
              : summary.score >= 200
              ? '「道心坚定，修为不凡，已入大道之门。」'
              : summary.score >= 100
              ? '「颇有修道之资，可惜缘法不足。」'
              : summary.score >= 50
              ? '「虽踏入修途，终未得大道。」'
              : summary.score >= 20
              ? '「凡尘一世，碌碌无为。」'
              : '「如露亦如电，应作如是观。」'}
          </p>
        </div>

        {/* Life Timeline Toggle */}
        <div className="text-center mb-6">
          <button
            onClick={() => {
              if (!showTimeline && lifeEvents.length === 0) {
                getLifeEvents(gameId).then(setLifeEvents).catch(() => {});
              }
              setShowTimeline(!showTimeline);
            }}
            className="text-scroll-text-dim text-sm font-kai tracking-widest border border-scroll-gold/30 rounded px-4 py-2 hover:bg-scroll-gold/10 transition-colors"
          >
            {showTimeline ? '收起生平' : '翻看完整一生'}
          </button>
        </div>

        {/* Life Timeline */}
        {showTimeline && (
          <div className="scroll-panel p-4 mb-6">
            <h3 className="text-scroll-text-dim text-xs font-kai tracking-widest mb-4 text-center">
              — 一生回顾 —
            </h3>
            <div className="max-h-[60vh] overflow-y-auto space-y-1 pr-1">
              {lifeEvents.length === 0 ? (
                <p className="text-scroll-text-dim text-center text-sm font-kai animate-pulse">
                  天书展开中...
                </p>
              ) : (
                lifeEvents.map((ev, i) => {
                  const catName = CATEGORY_NAMES[ev.category || 'common'] || '尘世';
                  const catColor = CATEGORY_COLORS[ev.category || 'common'] || 'text-stone-500';
                  const isImportant = ev.event_type === 'important' || ev.event_type === 'danger';
                  return (
                    <div
                      key={i}
                      className={`flex items-start gap-2 text-xs font-kai py-1 ${
                        isImportant ? 'bg-scroll-gold/5 rounded px-1' : ''
                      }`}
                    >
                      <span className="text-scroll-text-dim shrink-0 w-12 text-right">
                        {ev.age}岁
                      </span>
                      <span className={`shrink-0 w-8 text-center ${catColor}`}>
                        {catName}
                      </span>
                      <span className={`flex-1 ${isImportant ? 'text-scroll-gold' : 'text-scroll-text'}`}>
                        {ev.text}
                      </span>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}

        {/* Restart Button */}
        <div className="text-center">
          <button
            onClick={onRestart}
            className="ancient-button text-lg tracking-[0.5em] font-kai animate-pulse-gold"
          >
            再入轮回
          </button>
          <p className="mt-4 text-scroll-text-dim/50 text-xs font-kai tracking-widest">
            也许下一世，你能走得更远
          </p>
        </div>
      </div>
    </div>
  );
}
