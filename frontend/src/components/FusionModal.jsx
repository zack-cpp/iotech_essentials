import React, { useState, useEffect } from 'react';
import { validateFusionFormula, fetchDevices } from '../api';

const INITIAL = {
  source_node_id: '',
  source_channel: 1,
  source_field: 'voltage',
  formula: '',
  destination_node_id: '',
  destination_channel: 1,
  is_active: true,
};

export default function FusionModal({ rule, onSave, onClose }) {
  const isEdit = !!rule?.id;
  const [form, setForm] = useState(INITIAL);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [countingNodes, setCountingNodes] = useState([]);

  useEffect(() => {
    fetchDevices().then(setCountingNodes).catch(console.error);
    
    if (rule) {
      setForm({
        source_node_id: rule.source_node_id || '',
        source_channel: rule.source_channel || 1,
        source_field: rule.source_field || 'voltage',
        formula: rule.formula || '',
        destination_node_id: rule.destination_node_id || '',
        destination_channel: rule.destination_channel || 1,
        is_active: rule.is_active ?? true,
      });
    } else {
      setForm(INITIAL);
    }
    setErrors({});
  }, [rule]);

  function validate() {
    const errs = {};
    if (!form.source_node_id.trim()) errs.source_node_id = 'Source Node ID is required';
    if (!form.formula.trim()) errs.formula = 'Formula is required';
    if (!form.destination_node_id.trim()) errs.destination_node_id = 'Destination Node ID is required';
    return errs;
  }

  async function handleValidateFormula() {
    try {
      setValidationResult(null);
      const res = await validateFusionFormula({
        formula: form.formula,
        source_field: form.source_field,
        dummy_value: 1.0
      });
      if (res.valid) {
        setValidationResult({ success: true, text: `Valid! Result: ${res.result}` });
      }
    } catch (e) {
      setValidationResult({ success: false, text: e.message });
    }
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
        source_channel: Number(form.source_channel),
        destination_channel: Number(form.destination_channel),
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

  function insertVariable() {
    handleChange('formula', form.formula + ' <source_1> ');
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 600 }}>
        <div className="modal-header">
          <h2>{isEdit ? '✏️ Edit Fusion Rule' : '🔗 New Fusion Rule'}</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
            
            {/* SOURCE CARD */}
            <div style={{ background: '#f8fafc', padding: 16, borderRadius: 8, marginBottom: 16, border: '1px solid #e2e8f0' }}>
              <h3 style={{ marginTop: 0, marginBottom: 16, fontSize: 14, color: '#475569' }}>Source Configuration</h3>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Source Node</label>
                  <select
                    className={`form-input ${errors.source_node_id ? 'error' : ''}`}
                    value={form.source_node_id}
                    onChange={(e) => handleChange('source_node_id', e.target.value)}
                  >
                    <option value="">-- Select Node --</option>
                    {countingNodes.map(n => <option key={n.id} value={n.node_id}>{n.node_id}</option>)}
                  </select>
                  {errors.source_node_id && <span className="form-error">{errors.source_node_id}</span>}
                </div>
                <div className="form-group">
                  <label className="form-label">Channel (1-4)</label>
                  <input
                    type="number"
                    min="1" max="4"
                    className="form-input"
                    value={form.source_channel}
                    onChange={(e) => handleChange('source_channel', e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">JSON Field</label>
                  <input
                    type="text"
                    className="form-input"
                    value={form.source_field}
                    onChange={(e) => handleChange('source_field', e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* FORMULA CARD */}
            <div style={{ background: '#f0fdf4', padding: 16, borderRadius: 8, marginBottom: 16, border: '1px solid #bbf7d0' }}>
              <h3 style={{ marginTop: 0, marginBottom: 16, fontSize: 14, color: '#166534' }}>Formula</h3>
              <div className="form-group">
                <textarea
                  className={`form-input ${errors.formula ? 'error' : ''}`}
                  rows="4"
                  style={{ fontFamily: 'monospace', resize: 'vertical' }}
                  placeholder="e.g. 1.2762 * log(<source_1>)"
                  value={form.formula}
                  onChange={(e) => handleChange('formula', e.target.value)}
                />
                {errors.formula && <span className="form-error">{errors.formula}</span>}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <span style={{ fontSize: 12, color: '#166534', marginRight: 8 }}>Available Variables:</span>
                  <button type="button" onClick={insertVariable} style={{ background: '#dcfce7', border: '1px solid #86efac', borderRadius: 4, padding: '2px 6px', fontSize: 12, cursor: 'pointer' }}>
                    &lt;source_1&gt;
                  </button>
                </div>
                <button type="button" className="btn" style={{ padding: '4px 12px', fontSize: 13 }} onClick={handleValidateFormula}>
                  Test Formula
                </button>
              </div>
              {validationResult && (
                <div style={{ marginTop: 12, padding: 8, borderRadius: 4, fontSize: 13, background: validationResult.success ? '#dcfce7' : '#fee2e2', color: validationResult.success ? '#166534' : '#991b1b' }}>
                  {validationResult.text}
                </div>
              )}
            </div>

            {/* DESTINATION CARD */}
            <div style={{ background: '#eff6ff', padding: 16, borderRadius: 8, marginBottom: 16, border: '1px solid #bfdbfe' }}>
              <h3 style={{ marginTop: 0, marginBottom: 16, fontSize: 14, color: '#1e40af' }}>Destination Configuration</h3>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Destination Node</label>
                  <select
                    className={`form-input ${errors.destination_node_id ? 'error' : ''}`}
                    value={form.destination_node_id}
                    onChange={(e) => handleChange('destination_node_id', e.target.value)}
                  >
                    <option value="">-- Select Node --</option>
                    {countingNodes.map(n => <option key={n.id} value={n.node_id}>{n.node_id}</option>)}
                  </select>
                  {errors.destination_node_id && <span className="form-error">{errors.destination_node_id}</span>}
                </div>
                <div className="form-group">
                  <label className="form-label">Channel (1-4)</label>
                  <input
                    type="number"
                    min="1" max="4"
                    className="form-input"
                    value={form.destination_channel}
                    onChange={(e) => handleChange('destination_channel', e.target.value)}
                  />
                </div>
              </div>
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
