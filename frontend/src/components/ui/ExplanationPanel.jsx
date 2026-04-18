import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './ExplanationPanel.css';

// Module-level flag: run the typewriter only once per app session (PRD §8.7)
let hasTypewriterRun = false;

export default function ExplanationPanel({ content }) {
  const [displayText, setDisplayText] = useState(content || '');

  useEffect(() => {
    if (!content) return;
    const prefersReduced = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    // If user prefers reduced motion or we've already run the typewriter, render full content immediately
    if (prefersReduced || hasTypewriterRun) {
      setDisplayText(content);
      return;
    }

    hasTypewriterRun = true;
    setDisplayText('');
    let i = 0;
    const interval = 30; // ~30ms per character (PRD)
    let timer = null;

    function tick() {
      i += 1;
      setDisplayText(content.slice(0, i));
      if (i < content.length) {
        timer = window.setTimeout(tick, interval);
      }
    }

    timer = window.setTimeout(tick, interval);
    return () => window.clearTimeout(timer);
  }, [content]);

  if (!displayText) return null;

  return (
    <div className="explanation-panel">
      <h3 className="explanation-panel__header">Why this recommendation</h3>
      <div className="markdown-content">
        <ReactMarkdown>{displayText}</ReactMarkdown>
      </div>
    </div>
  );
}
