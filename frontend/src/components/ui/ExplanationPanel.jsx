import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import './ExplanationPanel.css';

let hasTypewriterRun = false;

const CARD_VARIANTS = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, ease: 'easeOut' },
  },
};

export default function ExplanationPanel({ content }) {
  const [displayText, setDisplayText] = useState(content || '');

  useEffect(() => {
    if (!content) return;

    const prefersReducedMotion =
      typeof window !== 'undefined' &&
      window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReducedMotion || hasTypewriterRun) {
      setDisplayText(content);
      return;
    }

    hasTypewriterRun = true;
    setDisplayText('');

    let index = 0;
    let timer = null;
    const intervalMs = 20;

    const tick = () => {
      index += 1;
      setDisplayText(content.slice(0, index));
      if (index < content.length) {
        timer = window.setTimeout(tick, intervalMs);
      }
    };

    timer = window.setTimeout(tick, intervalMs);
    return () => window.clearTimeout(timer);
  }, [content]);

  if (!displayText && !content) return null;

  return (
    <motion.div className="explanation-panel" variants={CARD_VARIANTS}>
      <h3 className="explanation-panel__header">
        <span className="explanation-panel__dot">&bull;</span>
        WHY THIS RECOMMENDATION
      </h3>
      <div className="explanation-panel__markdown">
        <ReactMarkdown>{displayText}</ReactMarkdown>
      </div>
    </motion.div>
  );
}
