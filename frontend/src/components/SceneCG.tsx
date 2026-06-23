import { useEffect, useRef } from 'react';

interface SceneCGProps {
  show: boolean;
  imageSrc: string | null;
  onDismiss: () => void;
  duration?: number; // Auto-dismiss time in ms. 0 = manual only.
  label?: string;    // Optional label text overlay (e.g. "突破·筑基")
}

/**
 * Layer 2: Full-screen CG illustration overlay.
 * Shows on realm breakthrough and destiny choice events.
 * Auto-dismisses after `duration` ms or on click.
 */
export function SceneCG({ show, imageSrc, onDismiss, duration = 3000, label }: SceneCGProps) {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (show && duration > 0) {
      timerRef.current = setTimeout(() => {
        onDismiss();
      }, duration);
    }
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [show, duration, onDismiss]);

  if (!show || !imageSrc) return null;

  return (
    <div
      className="scene-cg-overlay"
      onClick={onDismiss}
      style={{ opacity: show ? 1 : 0 }}
    >
      <img
        src={imageSrc}
        alt={label || '场景'}
        className="scene-cg-img"
        draggable={false}
      />
      {label && (
        <div className="scene-cg-label">
          {label}
        </div>
      )}
      <div className="scene-cg-hint">
        点击继续
      </div>
    </div>
  );
}
