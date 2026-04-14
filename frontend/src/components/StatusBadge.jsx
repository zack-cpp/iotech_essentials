import React from 'react';

export default function StatusBadge({ online }) {
  return (
    <span className={`status-badge ${online ? 'online' : 'offline'}`}>
      <span className={`status-dot ${online ? 'online' : 'offline'}`} />
      {online ? 'Active' : 'Idle'}
    </span>
  );
}
