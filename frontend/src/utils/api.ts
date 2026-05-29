import type { NextYearResponse, LifeSummary } from './types';

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
