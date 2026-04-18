import { useEffect, useState } from 'react';
import './BackgroundPaths.css';

function generateSinePaths(count, position = 1, widthScale = 1) {
  const paths = [];
  const step = 60; // fewer points -> lighter SVG path complexity
  for (let i = 0; i < count; i++) {
    const t = i / Math.max(count - 1, 1);
    const yBase = 80 + t * 240;
    const phase = i * (Math.PI / 4);
    let d = `M 0 ${yBase}`;
    for (let x = 0; x <= 1200; x += step) {
      const wave = Math.sin((x / 1200) * Math.PI * 2 + phase) * (20 + t * 60) * position;
      const y = Math.round(yBase + wave);
      d += ` L ${x} ${y}`;
    }
    const alpha = 0.06 + t * 0.28;
    const strokeW = (1 + t * 2) * widthScale;
    paths.push({ id: i, d, alpha, strokeW });
  }
  return paths;
}

export default function BackgroundPaths({ intensity = 1, hideOnDashboard = false }) {
  const [shouldAnimate, setShouldAnimate] = useState(false);
  const [isDesktop, setIsDesktop] = useState(true);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const mm = window.matchMedia('(min-width: 1024px)');
    const reducedQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => {
      const desktop = mm.matches;
      setIsDesktop(desktop);
      setShouldAnimate(desktop && !reducedQuery.matches);
    };
    update();
    mm.addEventListener?.('change', update);
    reducedQuery.addEventListener?.('change', update);
    return () => {
      mm.removeEventListener?.('change', update);
      reducedQuery.removeEventListener?.('change', update);
    };
  }, []);

  // Dashboard: subtle but visible blurred background — respects intensity prop
  if (hideOnDashboard) {
    const dashOpacity = Math.min(Math.max(intensity, 0.15), 1);
    const dashStrokeOpacity = Math.min(Math.max(intensity * 0.5, 0.1), 0.6);
    const soft = generateSinePaths(3, 0.6, 1.2);
    return (
      <div className="bgpaths" style={{ opacity: dashOpacity }}>
        <svg viewBox="0 0 1200 400" preserveAspectRatio="xMidYMid slice" className="bgpaths__svg" aria-hidden>
          <defs>
            <linearGradient id="bp-soft-dashboard" x1="0" x2="1">
              <stop offset="0%" stopColor="rgba(16,185,129,0)" />
              <stop offset="50%" stopColor="rgba(16,185,129,0.25)" />
              <stop offset="100%" stopColor="rgba(16,185,129,0)" />
            </linearGradient>
            <filter id="bp-blur-dashboard"><feGaussianBlur stdDeviation="12" /></filter>
          </defs>

          <g filter="url(#bp-blur-dashboard)" className="bgpaths__layer bgpaths__layer--soft">
            {soft.map((p, i) => (
              <path
                key={`db-${i}`}
                d={p.d}
                stroke="url(#bp-soft-dashboard)"
                strokeWidth={p.strokeW * 5}
                strokeOpacity={dashStrokeOpacity}
                fill="none"
                strokeLinecap="round"
                className="bgpaths__path"
              />
            ))}
          </g>
        </svg>
      </div>
    );
  }

  // Hero: different counts/blur on mobile vs desktop
  // Fewer paths on desktop to reduce overdraw
  const softCount = isDesktop ? 6 : 4;
  const brightCount = isDesktop ? 4 : 2;
  const soft = generateSinePaths(softCount, 1, isDesktop ? 2 : 2.2);
  const bright = generateSinePaths(brightCount, -1.2, isDesktop ? 1.6 : 1.8);

  // Reduced blur for crisp strokes
  const blurSoft = isDesktop ? 9 : 5;
  const blurBright = isDesktop ? 3.5 : 1.5;
  const softStrokeMul = isDesktop ? 2.2 : 2.8;
  const brightStrokeMul = isDesktop ? 1.4 : 1.8;
  const softOpacityMul = isDesktop ? 0.6 : 0.95;
  const brightOpacityMul = isDesktop ? 0.9 : 1.1;

  // Force stronger contrast via className if intensity > 0.75
  const forcedClass = intensity > 0.75 ? 'bgpaths bgpaths--strong bgpaths--contrast' : 'bgpaths';

  return (
    <div className={forcedClass} style={{ opacity: Math.min(Math.max(intensity, 0.35), 1) }}>
      <svg viewBox="0 0 1200 400" preserveAspectRatio="xMidYMid slice" className="bgpaths__svg" aria-hidden>
        <defs>
          <linearGradient id="bp-soft-grad" x1="0" x2="1">
            <stop offset="0%" stopColor="rgba(16,185,129,0)" />
            <stop offset="50%" stopColor="rgba(16,185,129,0.18)" />
            <stop offset="100%" stopColor="rgba(16,185,129,0)" />
          </linearGradient>
          <linearGradient id="bp-bright-grad" x1="0" x2="1">
            <stop offset="0%" stopColor="rgba(16,185,129,0)" />
            <stop offset="45%" stopColor="rgba(16,185,129,0.98)" />
            <stop offset="55%" stopColor="rgba(16,185,129,0.98)" />
            <stop offset="100%" stopColor="rgba(16,185,129,0)" />
          </linearGradient>
          <filter id="bp-blur-soft"><feGaussianBlur stdDeviation={blurSoft} /></filter>
          <filter id="bp-blur-bright"><feGaussianBlur stdDeviation={blurBright} /></filter>
        </defs>

        <g filter={`url(#bp-blur-soft)`} className="bgpaths__layer bgpaths__layer--soft">
          {soft.map((p, i) => (
            <path
              key={`soft-${i}`}
              d={p.d}
              stroke="url(#bp-soft-grad)"
              strokeWidth={p.strokeW * softStrokeMul}
              strokeOpacity={Math.max(0.04, Math.min(0.95, p.alpha * softOpacityMul))}
              fill="none"
              strokeLinecap="round"
              style={{
                transformOrigin: '600px 200px',
                animation: shouldAnimate ? `bg-drift ${30 + (i % 4) * 6}s ease-in-out ${i * 0.4}s infinite` : 'none',
              }}
              className="bgpaths__path bgpaths__path--soft"
            />
          ))}
        </g>

        <g filter={`url(#bp-blur-bright)`} className="bgpaths__layer bgpaths__layer--bright">
          {bright.map((p, i) => (
            <path
              key={`bright-${i}`}
              d={p.d}
              stroke="url(#bp-bright-grad)"
              strokeWidth={p.strokeW * brightStrokeMul}
              strokeOpacity={Math.max(0.06, Math.min(1, p.alpha * brightOpacityMul))}
              fill="none"
              strokeLinecap="round"
              style={{
                transformOrigin: '600px 200px',
                animation: shouldAnimate ? `bg-drift ${20 + (i % 3) * 5}s ease-in-out ${i * 0.35}s infinite` : 'none',
              }}
              className="bgpaths__path bgpaths__path--bright"
            />
          ))}
        </g>
      </svg>
    </div>
  );
}
