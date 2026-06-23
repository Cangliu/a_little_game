import { useState, useEffect, useRef } from 'react';
import { REALM_BACKGROUNDS, pickRandom } from '../config/sceneConfig';

interface SceneBgProps {
  realm: number;
}

/**
 * Layer 1: Dynamic realm-based background with cross-fade transition.
 * Uses two stacked img elements that alternate opacity for seamless switching.
 */
export function SceneBg({ realm }: SceneBgProps) {
  const [currentSrc, setCurrentSrc] = useState<string>('');
  const [nextSrc, setNextSrc] = useState<string>('');
  const [showNext, setShowNext] = useState(false);
  const prevRealmRef = useRef<number>(-1);
  const initializedRef = useRef(false);

  useEffect(() => {
    const pool = REALM_BACKGROUNDS[realm] || REALM_BACKGROUNDS[1];
    const newImg = pickRandom(pool);

    if (!initializedRef.current) {
      // First render: set current immediately
      setCurrentSrc(newImg);
      initializedRef.current = true;
      prevRealmRef.current = realm;
      return;
    }

    if (realm !== prevRealmRef.current) {
      // Realm changed: cross-fade to new image
      setNextSrc(newImg);
      setShowNext(true);

      // After transition completes, swap current and hide next
      const timer = setTimeout(() => {
        setCurrentSrc(newImg);
        setShowNext(false);
        setNextSrc('');
      }, 1600);

      prevRealmRef.current = realm;
      return () => clearTimeout(timer);
    }
  }, [realm]);

  return (
    <div className="scene-bg">
      {/* Current background */}
      {currentSrc && (
        <img
          src={currentSrc}
          alt=""
          className="scene-bg-img"
          style={{ opacity: showNext ? 0 : 1 }}
          loading="lazy"
          draggable={false}
        />
      )}
      {/* Next background (fades in on top) */}
      {nextSrc && (
        <img
          src={nextSrc}
          alt=""
          className="scene-bg-img"
          style={{ opacity: showNext ? 1 : 0 }}
          loading="lazy"
          draggable={false}
        />
      )}
      {/* Darkening overlay for text readability */}
      <div className="scene-bg-overlay" />
    </div>
  );
}
