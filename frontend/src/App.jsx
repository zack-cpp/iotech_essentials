import { useState, useEffect } from 'react';
import { Cpu, Plus, Edit2, Trash2, Inbox, CheckCircle, AlertCircle, Inspect } from 'lucide-react';
import DeviceModal from './components/DeviceModal';
import InspectionModal from './components/InspectionModal';
import { useTelemetry } from './hooks/useTelemetry';

export default function App() {
  const [activeTab, setActiveTab] = useState('counters'); // 'counters' | 'inspectors'

  const [devices, setDevices] = useState([]);
  const [inspectors, setInspectors] = useState([]);

  const [isModalOpen, setModalOpen] = useState(false);
  const [editingDevice, setEditingDevice] = useState(null);
  const [toasts, setToasts] = useState([]);

  const { socketStatus, metrics } = useTelemetry();

  const API_URL = '/api/devices';
  const API_INSPECT_URL = '/api/inspectors';

  const fetchData = async () => {
    try {
      if (activeTab === 'counters') {
        const res = await fetch(API_URL);
        setDevices(await res.json());
      } else {
        const res = await fetch(API_INSPECT_URL);
        setInspectors(await res.json());
      }
    } catch {
      showToast('Failed to load data', 'error');
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const showToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 3000);
  };

  const handleSave = async (formData) => {
    try {
      const isEdit = !!editingDevice;
      const baseUrl = activeTab === 'counters' ? API_URL : API_INSPECT_URL;
      const url = isEdit ? `${baseUrl}/${editingDevice.id}` : baseUrl;

      const res = await fetch(url, {
        method: isEdit ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (!res.ok) throw new Error();
      showToast(`${activeTab === 'counters' ? 'Device' : 'Inspector'} ${isEdit ? 'updated' : 'added'} successfully!`);
      setModalOpen(false);
      fetchData();
    } catch {
      showToast('Failed to save data', 'error');
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this mapping?')) return;
    try {
      const baseUrl = activeTab === 'counters' ? API_URL : API_INSPECT_URL;
      const res = await fetch(`${baseUrl}/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error();
      showToast('Deleted successfully', 'success');
      fetchData();
    } catch {
      showToast('Failed to delete', 'error');
    }
  };

  const LiveMetricBadge = ({ deviceId }) => {
    const metric = metrics[deviceId];
    if (!metric) return <span style={{ opacity: 0.3, fontSize: '0.8rem', fontStyle: 'italic' }}>Awaiting data...</span>;
    return (
      <span key={metric.timestamp} className="tag tag-ok flash-update" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', borderColor: 'rgba(59, 130, 246, 0.3)' }}>
        {metric.status} {metric.count ? `| Cnt: ${metric.count}` : ''}
      </span>
    );
  };

  return (
    <>
      <div className="blob blob-1"></div>
      <div className="blob blob-2"></div>

      <div className="container">
        <header className="glass-panel header">
          <div className="header-title">
            <Cpu className="icon-lg" />
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div>
                <h1>Edge Gateway</h1>
                <p>OEE Node Configuration & Telemetry</p>
              </div>
              <div className={`tag ${socketStatus === 'connected' ? 'tag-ok' : 'tag-ng'}`} style={{ opacity: socketStatus === 'connected' ? 1 : 0.5 }}>
                <span className="status-dot" style={socketStatus !== 'connected' ? { background: 'var(--danger)', boxShadow: '0 0 8px var(--danger)' } : {}}></span>
                {socketStatus === 'connected' ? 'Live Telemetry' : 'Offline'}
              </div>
            </div>
          </div>
          <button className="btn btn-primary" onClick={() => { setEditingDevice(null); setModalOpen(true); }}>
            <Plus size={18} /> Add {activeTab === 'counters' ? 'Node' : 'Inspector'}
          </button>
        </header>

        <div style={{ display: 'flex', gap: '1rem', borderBottom: '1px solid var(--glass-border)', paddingBottom: '0.5rem' }}>
          <button
            onClick={() => setActiveTab('counters')}
            className={`btn ${activeTab === 'counters' ? 'btn-primary' : 'btn-secondary'}`}
          >
            Counting Nodes
          </button>
          <button
            onClick={() => setActiveTab('inspectors')}
            className={`btn ${activeTab === 'inspectors' ? 'btn-primary' : 'btn-secondary'}`}
          >
            Inspection Nodes
          </button>
        </div>

        <main className="glass-panel table-container">
          {activeTab === 'counters' && devices.length === 0 && (
            <div className="empty-state">
              <Inbox size={48} />
              <p>No Counting Devices mapped yet.</p>
            </div>
          )}
          {activeTab === 'inspectors' && inspectors.length === 0 && (
            <div className="empty-state">
              <Inbox size={48} />
              <p>No Inspection Nodes mapped yet.</p>
            </div>
          )}

          {activeTab === 'counters' && devices.length > 0 && (
            <table>
              <thead>
                <tr>
                  <th>Gateway</th>
                  <th>Node ID</th>
                  <th>Cloud UUID</th>
                  <th>Secret</th>
                  <th>OK/NG Channels</th>
                  <th>Live Metric</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {devices.map(dev => (
                  <tr key={dev.id} className={metrics[dev.device_id_from] ? 'flash-update' : ''} style={{ animation: metrics[dev.device_id_from]?.timestamp ? 'highlightFlash 1.5s ease-out forwards' : 'none' }}>
                    <td>{dev.gateway_id}</td>
                    <td><strong>{dev.device_id_from}</strong></td>
                    <td><span className="secret-censor">{dev.device_id_to}</span></td>
                    <td><span className="secret-censor">••••{dev.device_secret.slice(-4)}</span></td>
                    <td>OK: {dev.ok_channel} | NG: {dev.ng_channel}</td>
                    <td>
                      <LiveMetricBadge deviceId={dev.device_id_from} />
                    </td>
                    <td style={{ display: 'flex', gap: '0.5rem' }}>
                      <button className="btn-icon" onClick={() => { setEditingDevice(dev); setModalOpen(true); }}>
                        <Edit2 size={18} />
                      </button>
                      <button className="btn-icon btn-danger" onClick={() => handleDelete(dev.id)}>
                        <Trash2 size={18} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {activeTab === 'inspectors' && inspectors.length > 0 && (
            <table>
              <thead>
                <tr>
                  <th>Gateway</th>
                  <th>MESIN ID</th>
                  <th>Cloud UUID</th>
                  <th>Secret</th>
                  <th>Req. Sensors</th>
                  <th>Live Metric</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {inspectors.map(dev => (
                  <tr key={dev.id} className={metrics[dev.device_id_from] ? 'flash-update' : ''} style={{ animation: metrics[dev.device_id_from]?.timestamp ? 'highlightFlash 1.5s ease-out forwards' : 'none' }}>
                    <td>{dev.gateway_id}</td>
                    <td><strong>{dev.device_id_from}</strong></td>
                    <td><span className="secret-censor">{dev.device_id_to}</span></td>
                    <td><span className="secret-censor">••••{dev.device_secret.slice(-4)}</span></td>
                    <td>{dev.total_sensor} units</td>
                    <td>
                      <LiveMetricBadge deviceId={dev.device_id_from} />
                    </td>
                    <td style={{ display: 'flex', gap: '0.5rem' }}>
                      <button className="btn-icon" onClick={() => { setEditingDevice(dev); setModalOpen(true); }}>
                        <Edit2 size={18} />
                      </button>
                      <button className="btn-icon btn-danger" onClick={() => handleDelete(dev.id)}>
                        <Trash2 size={18} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </main>
      </div>

      {activeTab === 'counters' ? (
        <DeviceModal isOpen={isModalOpen} device={editingDevice} onClose={() => setModalOpen(false)} onSave={handleSave} />
      ) : (
        <InspectionModal isOpen={isModalOpen} device={editingDevice} onClose={() => setModalOpen(false)} onSave={handleSave} />
      )}

      <div className="toast-container">
        {toasts.map(t => (
          <div key={t.id} className={`toast toast-${t.type} show`}>
            {t.type === 'success' ? <CheckCircle size={20} /> : <AlertCircle size={20} />}
            <span>{t.message}</span>
          </div>
        ))}
      </div>
    </>
  );
}
