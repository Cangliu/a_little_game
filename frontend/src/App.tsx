import { useState } from 'react';
import StartScreen from './pages/StartScreen';
import GameScreen from './pages/GameScreen';
import SummaryScreen from './pages/SummaryScreen';
import { startGame } from './utils/api';

type GamePhase = 'start' | 'playing' | 'summary';

function App() {
  const [phase, setPhase] = useState<GamePhase>('start');
  const [gameId, setGameId] = useState('');
  const [gender, setGender] = useState<string>('male');

  const handleStart = async () => {
    try {
      const result = await startGame();
      setGameId(result.game_id);
      setGender(result.gender || 'male');
      setPhase('playing');
    } catch (err) {
      console.error('Failed to start game:', err);
      alert('开启失败，请重试');
    }
  };

  const handleGameEnd = (endGameId: string) => {
    setGameId(endGameId);
    setPhase('summary');
  };

  const handleRestart = () => {
    setPhase('start');
    setGameId('');
  };

  return (
    <div className="min-h-screen bg-scroll-bg">
      {phase === 'start' && <StartScreen onStart={handleStart} />}
      {phase === 'playing' && (
        <GameScreen
          gameId={gameId}
          gender={gender}
          onGameEnd={handleGameEnd}
        />
      )}
      {phase === 'summary' && (
        <SummaryScreen gameId={gameId} onRestart={handleRestart} />
      )}
    </div>
  );
}

export default App;
