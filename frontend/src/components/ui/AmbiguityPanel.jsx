import ReactMarkdown from 'react-markdown';
import './AmbiguityPanel.css';

export default function AmbiguityPanel({ advice }) {
  if (!advice) return null;
  return (
    <div className="ambiguity-panel">
      <h3 className="ambiguity-panel__header">Human review needed</h3>
      <div className="markdown-content">
        <ReactMarkdown>{advice}</ReactMarkdown>
      </div>
    </div>
  );
}
