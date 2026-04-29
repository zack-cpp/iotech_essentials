import React, { useEffect, useState, useCallback } from 'react';
import { fetchFusionRules, createFusionRule, updateFusionRule, deleteFusionRule } from '../api';
import FusionModal from '../components/FusionModal';
import EmptyState from '../components/EmptyState';

export default function SensorFusion() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalRule, setModalRule] = useState(null); // null = closed, {} = new, {id:..} = edit
  const [showModal, setShowModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [toast, setToast] = useState(null);

  const load = useCallback(async () => {
    try {
      const data = await fetchFusionRules();
      setRules(data);
    } catch (e) {
      showToast('error', 'Failed to load fusion rules');
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  function showToast(type, msg) {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 3000);
  }

  function openNew() {
    setModalRule({});
    setShowModal(true);
  }

  function openEdit(rule) {
    setModalRule(rule);
    setShowModal(true);
  }

  function closeModal() {
    setShowModal(false);
    setModalRule(null);
  }

  async function handleSave(data) {
    try {
      if (modalRule?.id) {
        await updateFusionRule(modalRule.id, data);
        showToast('success', `Rule updated`);
      } else {
        await createFusionRule(data);
        showToast('success', `Rule created`);
      }
      closeModal();
      load();
    } catch (e) {
      showToast('error', e.message);
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    try {
      await deleteFusionRule(deleteTarget.id);
      showToast('success', `Rule deleted`);
      setDeleteTarget(null);
      load();
    } catch (e) {
      showToast('error', e.message);
    }
  }

  async function toggleActive(rule) {
    try {
      await updateFusionRule(rule.id, { is_active: !rule.is_active });
      load();
    } catch (e) {
      showToast('error', e.message);
    }
  }

  return (
    <div>
      {/* Toast */}
      {toast && (
        <div className="toast-container">
          <div className={`toast ${toast.type}`}>{toast.msg}</div>
        </div>
      )}

      {/* Delete Confirm */}
      {deleteTarget && (
        <div className="modal-overlay" onClick={() => setDeleteTarget(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 400 }}>
            <div className="modal-header">
              <h2>⚠️ Confirm Delete</h2>
              <button className="modal-close" onClick={() => setDeleteTarget(null)}>✕</button>
            </div>
            <div className="modal-body">
              <p className="confirm-text">
                Are you sure you want to delete this sensor fusion rule?
              </p>
            </div>
            <div className="modal-footer">
              <button className="btn btn-ghost" onClick={() => setDeleteTarget(null)}>Cancel</button>
              <button className="btn btn-danger" onClick={handleDelete}>Delete</button>
            </div>
          </div>
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <FusionModal
          rule={modalRule}
          onSave={handleSave}
          onClose={closeModal}
        />
      )}

      {/* Page Header */}
      <div className="page-header">
        <div className="page-header-left">
          <h1>🔗 Sensor Fusion</h1>
          <p>Transform raw sensor data into derived values and route to specific destinations.</p>
        </div>
        <button className="btn btn-primary" onClick={openNew}>
          ➕ Add Rule
        </button>
      </div>

      {/* Content */}
      {loading ? (
        <div style={{ padding: 20 }}>Loading...</div>
      ) : rules.length === 0 ? (
        <EmptyState
          icon="🔗"
          title="No Sensor Fusion Rules"
          message="Create rules to evaluate complex formulas from incoming node data."
          action={
            <button className="btn btn-primary" onClick={openNew}>
              ➕ Create First Rule
            </button>
          }
        />
      ) : (
        <div className="card" style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #e2e8f0' }}>
                <th style={{ padding: 12 }}>Status</th>
                <th style={{ padding: 12 }}>Source Node</th>
                <th style={{ padding: 12 }}>Formula</th>
                <th style={{ padding: 12 }}>Dest Node</th>
                <th style={{ padding: 12 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rules.map(rule => (
                <tr key={rule.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                  <td style={{ padding: 12 }}>
                    <div 
                      onClick={() => toggleActive(rule)}
                      style={{
                        display: 'inline-block',
                        width: 40, height: 20,
                        borderRadius: 10,
                        background: rule.is_active ? '#22c55e' : '#cbd5e1',
                        position: 'relative',
                        cursor: 'pointer',
                        transition: '0.2s'
                      }}
                    >
                      <div style={{
                        width: 16, height: 16,
                        background: '#fff',
                        borderRadius: '50%',
                        position: 'absolute',
                        top: 2,
                        left: rule.is_active ? 22 : 2,
                        transition: '0.2s'
                      }}/>
                    </div>
                  </td>
                  <td style={{ padding: 12 }}>
                    <div><strong>{rule.source_node_id}</strong></div>
                    <div style={{ fontSize: 12, color: '#64748b' }}>Ch: {rule.source_channel} | {rule.source_field}</div>
                  </td>
                  <td style={{ padding: 12 }}>
                    <code style={{ fontSize: 12, background: '#f1f5f9', padding: '2px 4px', borderRadius: 4 }}>
                      {rule.formula.length > 30 ? rule.formula.substring(0, 30) + '...' : rule.formula}
                    </code>
                  </td>
                  <td style={{ padding: 12 }}>
                    <div><strong>{rule.destination_node_id}</strong></div>
                    <div style={{ fontSize: 12, color: '#64748b' }}>Ch: {rule.destination_channel}</div>
                  </td>
                  <td style={{ padding: 12 }}>
                    <button className="btn btn-ghost" style={{ padding: '4px 8px' }} onClick={() => openEdit(rule)}>✏️</button>
                    <button className="btn btn-ghost" style={{ padding: '4px 8px', color: '#ef4444' }} onClick={() => setDeleteTarget(rule)}>🗑️</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
