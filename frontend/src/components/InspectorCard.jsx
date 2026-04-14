import React from 'react';
import StatusBadge from './StatusBadge';

export default function InspectorCard({ device, onEdit, onDelete }) {
  return (
    <div className="device-card" onClick={() => onEdit(device)}>
      <div className="device-card-header">
        <span className="device-node-id">{device.node_id}</span>
        <StatusBadge online={device.is_active} />
      </div>

      <div className="device-card-body">
        <div className="device-field">
          <span className="device-field-label">Cloud UID</span>
          <span className="device-field-value" title={device.cloud_uid}>
            {device.cloud_uid}
          </span>
        </div>
        <div className="device-field">
          <span className="device-field-label">Secret</span>
          <span className="device-field-value">
            {'•'.repeat(8)}{device.device_secret.slice(-4)}
          </span>
        </div>
        <div className="device-field">
          <span className="device-field-label">Total Sensors</span>
          <span className="device-field-value" style={{ color: 'var(--accent-cyan)', fontWeight: 700, fontSize: '1rem' }}>
            {device.total_sensor}
          </span>
        </div>
      </div>

      <div className="device-card-actions">
        <button
          className="btn btn-ghost btn-sm"
          onClick={(e) => { e.stopPropagation(); onEdit(device); }}
        >
          ✏️ Edit
        </button>
        <button
          className="btn btn-danger btn-sm"
          onClick={(e) => { e.stopPropagation(); onDelete(device); }}
        >
          🗑 Delete
        </button>
      </div>
    </div>
  );
}
