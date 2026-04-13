import ReactMarkdown from 'react-markdown';
import './ExplanationPanel.css';

export default function ExplanationPanel({ content }) {
  if (!content) return null;
  return (
    <div className="explanation-panel">
      <h3 className="explanation-panel__header">Why this recommendation</h3>
      <div className="markdown-content">
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
    </div>
  );
}
