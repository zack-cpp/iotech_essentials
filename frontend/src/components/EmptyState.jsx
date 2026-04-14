import React from 'react';

export default function EmptyState({ icon = '📡', title, message, action }) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">{icon}</div>
      <div className="empty-state-title">{title}</div>
      <div className="empty-state-text">{message}</div>
      {action}
    </div>
  );
}
