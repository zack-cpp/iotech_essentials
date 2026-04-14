import React, { useState, useEffect } from 'react';

const INITIAL = {
  node_id: '',
  cloud_uid: '',
  device_secret: '',
  total_sensor: 1,
  is_active: true,
};

export default function InspectorModal({ device, onSave, onClose }) {
  const isEdit = !!device?.id;
  const [form, setForm] = useState(INITIAL);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (device) {
      setForm({
        node_id: device.node_id || '',
        cloud_uid: device.cloud_uid || '',
        device_secret: device.device_secret || '',
        total_sensor: device.total_sensor ?? 1,
        is_active: device.is_active ?? true,
      });
    } else {
      setForm(INITIAL);
    }
    setErrors({});
  }, [device]);

  function validate() {
    const errs = {};
    if (!form.node_id.trim()) errs.node_id = 'Node ID is required';
    if (!form.cloud_uid.trim()) errs.cloud_uid = 'Cloud UID is required';
    if (!form.device_secret.trim()) errs.device_secret = 'Device Secret is required';
    if (form.total_sensor < 1) errs.total_sensor = 'Must have at least 1 sensor';
    return errs;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) {
      setErrors(errs);
      return;
    }
    setSaving(true);
    try {
      await onSave({
        ...form,
        total_sensor: Number(form.total_sensor),
      });
    } catch {
      // Parent handles error
    }
    setSaving(false);
  }

  function handleChange(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
    setErrors((e) => ({ ...e, [field]: undefined }));
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{isEdit ? '✏️ Edit Inspection Node' : '➕ New Inspection Node'}</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-group">
              <label className="form-label">Node ID</label>
              <input
                id="input-inspector-node-id"
                className={`form-input ${errors.node_id ? 'error' : ''}`}
                placeholder="e.g. Q005"
                value={form.node_id}
                onChange={(e) => handleChange('node_id', e.target.value)}
              />
              {errors.node_id && <span className="form-error">{errors.node_id}</span>}
            </div>

            <div className="form-group">
              <label className="form-label">Cloud UID</label>
              <input
                id="input-inspector-cloud-uid"
                className={`form-input ${errors.cloud_uid ? 'error' : ''}`}
                placeholder="e.g. dd880e00-xxxx-xxxx"
                value={form.cloud_uid}
                onChange={(e) => handleChange('cloud_uid', e.target.value)}
              />
              {errors.cloud_uid && <span className="form-error">{errors.cloud_uid}</span>}
            </div>

            <div className="form-group">
              <label className="form-label">Device Secret</label>
              <input
                id="input-inspector-device-secret"
                className={`form-input ${errors.device_secret ? 'error' : ''}`}
                placeholder="HMAC authentication token"
                value={form.device_secret}
                onChange={(e) => handleChange('device_secret', e.target.value)}
              />
              {errors.device_secret && <span className="form-error">{errors.device_secret}</span>}
            </div>

            <div className="form-group">
              <label className="form-label">Total Sensors</label>
              <input
                id="input-inspector-total-sensor"
                type="number"
                min="1"
                className={`form-input ${errors.total_sensor ? 'error' : ''}`}
                value={form.total_sensor}
                onChange={(e) => handleChange('total_sensor', e.target.value)}
              />
              {errors.total_sensor && <span className="form-error">{errors.total_sensor}</span>}
            </div>

            <div className="form-group">
              <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(e) => handleChange('is_active', e.target.checked)}
                />
                Active
              </label>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-ghost" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Saving...' : isEdit ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
