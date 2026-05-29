import { useState, useEffect } from 'react';

interface StartScreenProps {
  onStart: () => void;
}

export default function StartScreen({ onStart }: StartScreenProps) {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setShow(true), 300);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden">
      {/* === Cover image background === */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: 'url(/cover.png)' }}
      />

      {/* Soft vignette overlay for text legibility (top dim, bottom dim) */}
      <div
        className="absolute inset-0"
        style={{
          background:
            'linear-gradient(180deg, rgba(20,15,10,0.15) 0%, transparent 25%, transparent 60%, rgba(20,15,10,0.45) 100%)',
        }}
      />

      {/* Subtle radial glow behind title */}
      <div
        className="absolute top-[20%] left-1/2 -translate-x-1/2 w-[800px] h-[400px] rounded-full pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse, rgba(255,230,170,0.25) 0%, rgba(255,200,140,0.1) 40%, transparent 70%)',
        }}
      />

      {/* Floating spiritual particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {Array.from({ length: 18 }).map((_, i) => {
          const colors = [
            { bg: 'rgba(255,230,160,0.7)', glow: 'rgba(255,210,100,0.5)' },
            { bg: 'rgba(255,255,255,0.7)', glow: 'rgba(255,250,200,0.5)' },
            { bg: 'rgba(255,200,210,0.6)', glow: 'rgba(255,180,200,0.4)' },
          ];
          const c = colors[i % 3];
          return (
            <div
              key={i}
              className="absolute rounded-full"
              style={{
                left: `${10 + Math.random() * 80}%`,
                bottom: `${5 + Math.random() * 60}%`,
                width: `${3 + Math.random() * 4}px`,
                height: `${3 + Math.random() * 4}px`,
                background: c.bg,
                boxShadow: `0 0 ${10 + Math.random() * 12}px ${c.glow}`,
                animation: `floatUp ${10 + Math.random() * 14}s linear infinite`,
                animationDelay: `${Math.random() * 10}s`,
              }}
            />
          );
        })}
      </div>

      {/* Main content */}
      <div
        className={`text-center transition-all duration-1000 relative z-20 ${
          show ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
        }`}
      >
        {/* Subtitle */}
        <div
          className="mb-3 text-sm tracking-[0.5em] font-kai"
          style={{
            color: 'rgba(255,240,210,0.95)',
            textShadow: '0 2px 8px rgba(60,30,10,0.7), 0 0 20px rgba(0,0,0,0.4)',
          }}
        >
          修仙 · 人生重开模拟器
        </div>

        {/* Title - warm golden calligraphy on cover image */}
        <h1
          className="text-7xl md:text-8xl font-kai mb-4 tracking-[0.3em]"
          style={{
            color: '#fff5dc',
            textShadow:
              '0 3px 8px rgba(60,30,10,0.85), 0 0 30px rgba(255,200,100,0.6), 0 0 60px rgba(255,180,80,0.4)',
          }}
        >
          觅长生
        </h1>

        {/* Divider - golden */}
        <div
          className="mx-auto max-w-[240px] h-[2px] mb-6 rounded-full"
          style={{
            background:
              'linear-gradient(90deg, transparent, rgba(255,210,140,0.7), rgba(255,230,170,0.95), rgba(255,210,140,0.7), transparent)',
            boxShadow: '0 0 12px rgba(255,200,120,0.5)',
          }}
        />

        <p
          className="font-kai text-base mb-12 tracking-widest max-w-md mx-auto leading-loose"
          style={{
            color: 'rgba(255,240,215,0.95)',
            textShadow: '0 2px 6px rgba(60,30,10,0.8), 0 0 16px rgba(0,0,0,0.3)',
          }}
        >
          天地不仁，以万物为刍狗<br />
          修仙之路，道阻且长<br />
          你，准备好了吗？
        </p>

        {/* Start button - golden game button */}
        <button
          onClick={onStart}
          className="relative px-12 py-4 text-xl tracking-[0.5em] font-kai cursor-pointer transition-all duration-300 rounded-lg"
          style={{
            background: 'linear-gradient(180deg, #f0c860 0%, #d4a040 50%, #b07820 100%)',
            color: '#fffef5',
            border: '2px solid rgba(255,230,150,0.8)',
            boxShadow:
              '0 4px 20px rgba(80,40,10,0.5), 0 0 30px rgba(255,200,80,0.3), inset 0 1px 0 rgba(255,255,255,0.5)',
            textShadow: '0 1px 2px rgba(120,70,0,0.6)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background =
              'linear-gradient(180deg, #ffd870 0%, #e0b050 50%, #c08828 100%)';
            e.currentTarget.style.boxShadow =
              '0 6px 30px rgba(80,40,10,0.6), 0 0 40px rgba(255,210,90,0.45), inset 0 1px 0 rgba(255,255,255,0.6)';
            e.currentTarget.style.transform = 'translateY(-2px)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background =
              'linear-gradient(180deg, #f0c860 0%, #d4a040 50%, #b07820 100%)';
            e.currentTarget.style.boxShadow =
              '0 4px 20px rgba(80,40,10,0.5), 0 0 30px rgba(255,200,80,0.3), inset 0 1px 0 rgba(255,255,255,0.5)';
            e.currentTarget.style.transform = 'translateY(0)';
          }}
        >
          开始新生
        </button>

        <div
          className="mt-16 font-kai"
          style={{
            color: 'rgba(255,240,215,0.75)',
            fontSize: '15px',
            letterSpacing: '0.35em',
            fontWeight: 500,
            textShadow: '0 2px 6px rgba(60,30,10,0.8)',
          }}
        >
          每一次轮回，皆是新的开始
        </div>
      </div>
    </div>
  );
}
