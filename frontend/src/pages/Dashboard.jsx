import React, { useEffect, useState } from 'react';
import { fetchStatus, fetchDevices, fetchInspectors } from '../api';

export default function Dashboard() {
  const [status, setStatus] = useState(null);
  const [devices, setDevices] = useState([]);
  const [inspectors, setInspectors] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  async function loadData() {
    try {
      const [s, d, i] = await Promise.all([
        fetchStatus(),
        fetchDevices(),
        fetchInspectors(),
      ]);
      setStatus(s);
      setDevices(d);
      setInspectors(i);
    } catch (e) {
      console.error('Dashboard load error:', e);
    }
    setLoading(false);
  }

  const activeDevices = devices.filter((d) => d.is_active).length;
  const activeInspectors = inspectors.filter((d) => d.is_active).length;

  function formatUptime(seconds) {
    if (!seconds) return '—';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
  }

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <div className="page-header-left">
            <h1>Dashboard</h1>
            <p>Gateway overview and system health</p>
          </div>
        </div>
        <div className="stats-grid">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="stat-card">
              <div className="skeleton" style={{ height: 20, width: 80, marginBottom: 12 }} />
              <div className="skeleton" style={{ height: 36, width: 60, marginBottom: 8 }} />
              <div className="skeleton" style={{ height: 14, width: 120 }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h1>📊 Dashboard</h1>
          <p>Gateway overview and system health</p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-card-header">
            <div className="stat-card-icon blue">🔢</div>
          </div>
          <div className="stat-card-value">{devices.length}</div>
          <div className="stat-card-label">Counting Nodes ({activeDevices} active)</div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <div className="stat-card-icon emerald">🔬</div>
          </div>
          <div className="stat-card-value">{inspectors.length}</div>
          <div className="stat-card-label">Inspection Nodes ({activeInspectors} active)</div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <div className="stat-card-icon indigo">📡</div>
          </div>
          <div className="stat-card-value" style={{ color: status?.mqtt_connected ? 'var(--status-ok)' : 'var(--status-ng)' }}>
            {status?.mqtt_connected ? 'Online' : 'Offline'}
          </div>
          <div className="stat-card-label">MQTT Broker Connection</div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <div className="stat-card-icon cyan">⏱</div>
          </div>
          <div className="stat-card-value">{formatUptime(status?.uptime_seconds)}</div>
          <div className="stat-card-label">Gateway Uptime</div>
        </div>
      </div>

      {/* Recent Devices Summary */}
      <div style={{ marginTop: '1rem' }}>
        <h2 style={{ marginBottom: '1rem' }}>Recent Counting Nodes</h2>
        {devices.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            No counting devices configured. Navigate to Counting Nodes to add one.
          </p>
        ) : (
          <div className="devices-grid">
            {devices.slice(0, 3).map((d) => (
              <div key={d.id} className="device-card" style={{ cursor: 'default' }}>
                <div className="device-card-header">
                  <span className="device-node-id">{d.node_id}</span>
                  <span className={`status-badge ${d.is_active ? 'online' : 'offline'}`}>
                    <span className={`status-dot ${d.is_active ? 'online' : 'offline'}`} />
                    {d.is_active ? 'Active' : 'Idle'}
                  </span>
                </div>
                <div className="device-card-body">
                  <div className="device-field">
                    <span className="device-field-label">Cloud UID</span>
                    <span className="device-field-value">{d.cloud_uid}</span>
                  </div>
                  <div className="device-field">
                    <span className="device-field-label">Channels</span>
                    <div className="channel-badges">
                      <span className="channel-badge ok">OK: {d.ok_channel}</span>
                      <span className="channel-badge ng">NG: {d.ng_channel}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Inspectors Summary */}
      <div style={{ marginTop: '2rem' }}>
        <h2 style={{ marginBottom: '1rem' }}>Recent Inspection Nodes</h2>
        {inspectors.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            No inspection devices configured. Navigate to Inspection Nodes to add one.
          </p>
        ) : (
          <div className="devices-grid">
            {inspectors.slice(0, 3).map((d) => (
              <div key={d.id} className="device-card" style={{ cursor: 'default' }}>
                <div className="device-card-header">
                  <span className="device-node-id">{d.node_id}</span>
                  <span className={`status-badge ${d.is_active ? 'online' : 'offline'}`}>
                    <span className={`status-dot ${d.is_active ? 'online' : 'offline'}`} />
                    {d.is_active ? 'Active' : 'Idle'}
                  </span>
                </div>
                <div className="device-card-body">
                  <div className="device-field">
                    <span className="device-field-label">Cloud UID</span>
                    <span className="device-field-value">{d.cloud_uid}</span>
                  </div>
                  <div className="device-field">
                    <span className="device-field-label">Total Sensors</span>
                    <span className="device-field-value" style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>
                      {d.total_sensor}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
