import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import './BackgroundPaths.css';

function canRunParticles() {
  if (typeof window === 'undefined') return false;
  if (navigator.connection?.saveData) return false;
  return true;
}

function prefersReducedMotion() {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

export default function BackgroundPaths({
  variant = 'home',
  hideOnDashboard = false,
  blur = false,
  intensity = 1,
}) {
  const canvasRef = useRef(null);
  const [particlesEnabled, setParticlesEnabled] = useState(() => canRunParticles());
  const [reducedMotion, setReducedMotion] = useState(() => prefersReducedMotion());

  useLayoutEffect(() => {
    setParticlesEnabled(canRunParticles());
    setReducedMotion(prefersReducedMotion());
  }, []);

  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    const onChange = () => setReducedMotion(reduced.matches);
    reduced.addEventListener?.('change', onChange);
    return () => reduced.removeEventListener?.('change', onChange);
  }, []);

  useEffect(() => {
    if (hideOnDashboard || !particlesEnabled) return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const isLogin = variant === 'login';
    const PARTICLE_COUNT = isLogin ? 36 : reducedMotion ? 55 : 110;
    const CONNECTION_DISTANCE = 170;
    const mouse = { x: -9999, y: -9999 };
    const opacityScale = Math.min(Math.max(intensity, 0.5), 1);
    const animate = !reducedMotion;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();

    const particles = Array.from({ length: PARTICLE_COUNT }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * (animate ? 0.45 : 0),
      vy: (Math.random() - 0.5) * (animate ? 0.45 : 0),
      radius: 2 + Math.random() * 2.5,
      opacity: (0.55 + Math.random() * 0.4) * opacityScale,
    }));

    const onMouseMove = (e) => {
      if (reducedMotion || isLogin) return;
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    };

    if (!isLogin && !reducedMotion) {
      window.addEventListener('mousemove', onMouseMove);
    }

    let resizeTimeout;
    const onResize = () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(resize, 200);
    };
    window.addEventListener('resize', onResize);

    let raf;
    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particles.forEach((p) => {
        if (!isLogin && !reducedMotion) {
          const dx = mouse.x - p.x;
          const dy = mouse.y - p.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 160) {
            p.vx += dx * 0.00018;
            p.vy += dy * 0.00018;
          }
        }

        if (animate) {
          const speed = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
          if (speed > 1.6) {
            p.vx = (p.vx / speed) * 1.6;
            p.vy = (p.vy / speed) * 1.6;
          }

          p.x += p.vx;
          p.y += p.vy;

          if (p.x < 0) p.x = canvas.width;
          if (p.x > canvas.width) p.x = 0;
          if (p.y < 0) p.y = canvas.height;
          if (p.y > canvas.height) p.y = 0;
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(34, 230, 166, ${p.opacity})`;
        ctx.fill();
      });

      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < CONNECTION_DISTANCE) {
            const alpha = (1 - dist / CONNECTION_DISTANCE) * 0.42 * opacityScale;
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(34, 230, 166, ${alpha})`;
            ctx.lineWidth = 1.1;
            ctx.stroke();
          }
        }
      }

      if (animate) {
        raf = requestAnimationFrame(draw);
      }
    };

    draw();

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('resize', onResize);
      clearTimeout(resizeTimeout);
    };
  }, [variant, hideOnDashboard, particlesEnabled, intensity, reducedMotion]);

  if (hideOnDashboard) return null;

  const isLogin = variant === 'login';

  return (
    <>
      <div
        className={`bgpaths-fallback ${isLogin ? 'bgpaths-fallback--login' : ''} ${reducedMotion ? 'bgpaths-fallback--static' : ''}`}
        aria-hidden
      />
      <canvas
        ref={canvasRef}
        className={`bgpaths-canvas ${blur ? 'bgpaths-canvas--blur' : ''} ${isLogin ? 'bgpaths-canvas--login' : ''}`}
        aria-hidden
      />
    </>
  );
}
