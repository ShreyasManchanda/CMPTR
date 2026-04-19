import { useEffect, useRef } from 'react';

export default function BackgroundPaths({ 
  variant = 'home', 
  hideOnDashboard = false,
  blur = false
}) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (hideOnDashboard) return;
    if (typeof window === 'undefined') return;
    if (window.matchMedia(
      '(prefers-reduced-motion: reduce)').matches) return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const isLogin = variant === 'login';
    const PARTICLE_COUNT = isLogin ? 25 : 80;
    const CONNECTION_DISTANCE = 150;
    const mouse = { x: -9999, y: -9999 };

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();

    const particles = Array.from(
      { length: PARTICLE_COUNT }, () => ({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        radius: 1.5 + Math.random() * 1.5,
        opacity: 0.3 + Math.random() * 0.4,
      })
    );

    const onMouseMove = (e) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    };

    if (!isLogin) {
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

      particles.forEach(p => {
        // Mouse attraction (home only)
        if (!isLogin) {
          const dx = mouse.x - p.x;
          const dy = mouse.y - p.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 150) {
            p.vx += dx * 0.00015;
            p.vy += dy * 0.00015;
          }
        }

        // Cap velocity
        const speed = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
        if (speed > 1.5) {
          p.vx = (p.vx / speed) * 1.5;
          p.vy = (p.vy / speed) * 1.5;
        }

        p.x += p.vx;
        p.y += p.vy;

        // Wrap around edges
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;

        // Draw particle
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(16,185,129,${p.opacity})`;
        ctx.fill();
      });

      // Draw connections
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < CONNECTION_DISTANCE) {
            const alpha = (1 - dist / CONNECTION_DISTANCE) * 0.25;
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(16,185,129,${alpha})`;
            ctx.lineWidth = 0.9;
            ctx.stroke();
          }
        }
      }

      raf = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('resize', onResize);
      clearTimeout(resizeTimeout);
    };
  }, [variant, hideOnDashboard]);

  if (hideOnDashboard) return null;

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        inset: 0,
        width: '100%',
        height: '100%',
        pointerEvents: variant === 'login' ? 'none' : 'auto',
        zIndex: 0,
        display: 'block',
        maskImage: variant === 'login'
          ? 'radial-gradient(ellipse 70% 70% at 50% 50%, transparent 25%, black 100%)'
          : 'none',
        WebkitMaskImage: variant === 'login'
          ? 'radial-gradient(ellipse 70% 70% at 50% 50%, transparent 25%, black 100%)'
          : 'none',
        filter: blur ? 'blur(2px)' : 'none',
      }}
    />
  );
}