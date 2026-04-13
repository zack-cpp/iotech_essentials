import { useState, useEffect } from 'react';
import { X } from 'lucide-react';

export default function InspectionModal({ isOpen, onClose, device, onSave }) {
  const [formData, setFormData] = useState({
    gateway_id: '',
    device_id_from: '',
    device_id_to: '',
    device_secret: '',
    total_sensor: 24,
  });

  useEffect(() => {
    if (device) {
      setFormData({
        gateway_id: device.gateway_id || '',
        device_id_from: device.device_id_from || '',
        device_id_to: device.device_id_to || '',
        device_secret: device.device_secret || '',
        total_sensor: device.total_sensor || 24,
      });
    } else {
      setFormData({
        gateway_id: '',
        device_id_from: '',
        device_id_to: '',
        device_secret: '',
        total_sensor: 24,
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
          <h2>{device ? "Edit Inspection Node" : "Add Inspection Node"}</h2>
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
            <label>Machine / Panel ID (MESIN_ID)</label>
            <input 
              value={formData.device_id_from} 
              onChange={e => setFormData({...formData, device_id_from: e.target.value})} 
              required placeholder="e.g. HAS-AI-0002" 
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
          <div className="form-group">
            <label>Total Required Sensors</label>
            <input type="number" value={formData.total_sensor} onChange={e => setFormData({...formData, total_sensor: parseInt(e.target.value)})} required min="1" />
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
