import './RunStatusBadge.css';

const STATUS_CONFIG = {
  idle: { label: 'Idle', className: 'rsb--idle' },
  running: { label: 'Running', className: 'rsb--running' },
  complete: { label: 'Complete', className: 'rsb--complete' },
  error: { label: 'Error', className: 'rsb--error' },
};

export default function RunStatusBadge({ status }) {
  if (!status || status === 'idle') return null;

  const config = STATUS_CONFIG[status] || STATUS_CONFIG.idle;
  return <span className={`rsb ${config.className}`}>{config.label}</span>;
}