import React, { useEffect, useState, useCallback } from 'react';
import { fetchInspectors, createInspector, updateInspector, deleteInspector } from '../api';
import InspectorCard from '../components/InspectorCard';
import InspectorModal from '../components/InspectorModal';
import EmptyState from '../components/EmptyState';

export default function InspectionNodes() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalDevice, setModalDevice] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [toast, setToast] = useState(null);

  const load = useCallback(async () => {
    try {
      const data = await fetchInspectors();
      setDevices(data);
    } catch (e) {
      showToast('error', 'Failed to load inspection devices');
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  function showToast(type, msg) {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 3000);
  }

  function openNew() {
    setModalDevice({});
    setShowModal(true);
  }

  function openEdit(device) {
    setModalDevice(device);
    setShowModal(true);
  }

  function closeModal() {
    setShowModal(false);
    setModalDevice(null);
  }

  async function handleSave(data) {
    try {
      if (modalDevice?.id) {
        await updateInspector(modalDevice.id, data);
        showToast('success', `${data.node_id} updated`);
      } else {
        await createInspector(data);
        showToast('success', `${data.node_id} created`);
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
      await deleteInspector(deleteTarget.id);
      showToast('success', `${deleteTarget.node_id} deleted`);
      setDeleteTarget(null);
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
                Are you sure you want to delete inspection node <strong>{deleteTarget.node_id}</strong>?
                This will remove the sensor mapping from the gateway.
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
        <InspectorModal
          device={modalDevice}
          onSave={handleSave}
          onClose={closeModal}
        />
      )}

      {/* Page Header */}
      <div className="page-header">
        <div className="page-header-left">
          <h1>🔬 Inspection Nodes</h1>
          <p>Manage quality control sensor array devices</p>
        </div>
        <button id="btn-add-inspector" className="btn btn-primary" onClick={openNew}>
          ➕ Add Node
        </button>
      </div>

      {/* Content */}
      {loading ? (
        <div className="devices-grid">
          {[1, 2, 3].map((i) => (
            <div key={i} className="device-card">
              <div className="skeleton" style={{ height: 24, width: '60%', marginBottom: 16 }} />
              <div className="skeleton" style={{ height: 16, width: '100%', marginBottom: 8 }} />
              <div className="skeleton" style={{ height: 16, width: '80%', marginBottom: 8 }} />
              <div className="skeleton" style={{ height: 16, width: '50%' }} />
            </div>
          ))}
        </div>
      ) : devices.length === 0 ? (
        <EmptyState
          icon="🔬"
          title="No Inspection Nodes"
          message="Add your first inspection device to start monitoring sensor arrays."
          action={
            <button className="btn btn-primary" onClick={openNew}>
              ➕ Add First Node
            </button>
          }
        />
      ) : (
        <div className="devices-grid">
          {devices.map((d) => (
            <InspectorCard
              key={d.id}
              device={d}
              onEdit={openEdit}
              onDelete={setDeleteTarget}
            />
          ))}
        </div>
      )}
    </div>
  );
}
