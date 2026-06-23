import type { NextYearResponse, LifeSummary, SectInfo, NPCRelationship, ChoiceHistoryItem } from './types';

const API_BASE = '/api/game';

export async function startGame(): Promise<{
  game_id: string;
  age: number;
  realm: number;
  realm_name: string;
  gender: string;
}> {
  const res = await fetch(`${API_BASE}/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to start game');
  }
  return res.json();
}

export async function nextYear(gameId: string): Promise<NextYearResponse> {
  const res = await fetch(`${API_BASE}/next-year`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ game_id: gameId }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to advance year');
  }
  return res.json();
}

export async function getSummary(gameId: string): Promise<LifeSummary> {
  const res = await fetch(`${API_BASE}/summary/${gameId}`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to get summary');
  }
  return res.json();
}

export async function makeChoice(
  gameId: string,
  eventId: string,
  choiceIndex: number,
): Promise<{ result_text: string; event_id: string; choice_index: number; choice_text: string; is_success: boolean; final_success_rate: number }> {
  const res = await fetch(`${API_BASE}/choose`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ game_id: gameId, event_id: eventId, choice_index: choiceIndex }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to make choice');
  }
  return res.json();
}

export async function getGameState(gameId: string): Promise<{
  game_id: string;
  age: number;
  realm: number;
  tension: number;
  sect_info: SectInfo | null;
  npc_relationships: NPCRelationship[];
  choice_history: ChoiceHistoryItem[];
}> {
  const res = await fetch(`${API_BASE}/state/${gameId}`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to get game state');
  }
  return res.json();
}

export async function getSectWorld(gameId: string): Promise<{
  sects: Array<{
    sect_id: string;
    name: string;
    sect_type: string;
    tier: number;
    reputation: number;
    disciples_count: number;
    sect_master_name: string;
  }>;
  relations: Array<{ sect_a_id: string; sect_b_id: string; relation_type: string; tension: number }>;
  player_sect_id: string | null;
}> {
  const res = await fetch(`${API_BASE}/sect-world/${gameId}`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to get sect world');
  }
  return res.json();
}

/**
 * Streaming variant of nextYear. Consumes SSE events from /next-year-stream.
 * Falls through on any error (caller should fallback to nextYear).
 */
export async function nextYearStream(
  gameId: string,
  onState: (data: Record<string, unknown>) => void,
  onNarrativeChunk: (chunk: string) => void,
  onDone: (data: Record<string, unknown>) => void,
): Promise<void> {
  const res = await fetch(`${API_BASE}/next-year-stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ game_id: gameId }),
  });

  if (!res.ok) {
    throw new Error(`Stream request failed: ${res.status}`);
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // Parse SSE events from buffer (events separated by \n\n)
    const parts = buffer.split('\n\n');
    buffer = parts.pop() || '';

    for (const part of parts) {
      if (!part.trim()) continue;
      const lines = part.split('\n');
      let eventType = '';
      let dataStr = '';
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          eventType = line.slice(7);
        } else if (line.startsWith('data: ')) {
          dataStr = line.slice(6);
        }
      }
      if (!eventType || !dataStr) continue;

      const data = JSON.parse(dataStr);
      if (eventType === 'state') onState(data);
      else if (eventType === 'narrative_chunk') onNarrativeChunk(data);
      else if (eventType === 'done') onDone(data);
      else if (eventType === 'error') throw new Error(data.detail || 'Stream error');
    }
  }
}
