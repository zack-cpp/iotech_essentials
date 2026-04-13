import { useState, useEffect } from 'react';
import { X } from 'lucide-react';

export default function DeviceModal({ isOpen, onClose, device, onSave }) {
  const [formData, setFormData] = useState({
    gateway_id: '',
    device_id_from: '',
    device_id_to: '',
    device_secret: '',
    ok_channel: 0,
    ng_channel: 1,
  });

  useEffect(() => {
    if (device) {
      setFormData({
        gateway_id: device.gateway_id || '',
        device_id_from: device.device_id_from || '',
        device_id_to: device.device_id_to || '',
        device_secret: device.device_secret || '',
        ok_channel: device.ok_channel || 0,
        ng_channel: device.ng_channel || 1,
      });
    } else {
      setFormData({
        gateway_id: '',
        device_id_from: '',
        device_id_to: '',
        device_secret: '',
        ok_channel: 0,
        ng_channel: 1,
      });
    }
  }, [device, isOpen]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay active">
      <div className="modal glass-panel">
        <div className="modal-header">
          <h2>{device ? "Edit Device" : "Add Device"}</h2>
          <button type="button" className="btn-icon" onClick={onClose}>
            <X size={20} />
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Gateway ID</label>
            <input 
              value={formData.gateway_id} 
              onChange={e => setFormData({...formData, gateway_id: e.target.value})} 
              placeholder="Leave blank for env default" 
            />
          </div>
          <div className="form-group">
            <label>Physical Node ID (From)</label>
            <input 
              value={formData.device_id_from} 
              onChange={e => setFormData({...formData, device_id_from: e.target.value})} 
              required placeholder="e.g. C071" 
            />
          </div>
          <div className="form-group">
            <label>Cloud UUID (To)</label>
            <input 
              value={formData.device_id_to} 
              onChange={e => setFormData({...formData, device_id_to: e.target.value})} 
              required placeholder="00000000-0000-0000-0000-000000000000" 
            />
          </div>
          <div className="form-group">
            <label>Device Secret (HMAC signature)</label>
            <input 
              value={formData.device_secret} 
              onChange={e => setFormData({...formData, device_secret: e.target.value})} 
              required placeholder="Base64 / JWT Secret" 
            />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>OK Channel</label>
              <input type="number" value={formData.ok_channel} onChange={e => setFormData({...formData, ok_channel: parseInt(e.target.value)})} required min="0" />
            </div>
            <div className="form-group">
              <label>NG Channel</label>
              <input type="number" value={formData.ng_channel} onChange={e => setFormData({...formData, ng_channel: parseInt(e.target.value)})} required min="0" />
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary">Save Mapping</button>
          </div>
        </form>
      </div>
    </div>
  );
}
