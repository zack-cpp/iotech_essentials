const API_URL = '/api/devices';
let devices = [];

// DOM Elements
const deviceTableBody = document.getElementById('deviceTableBody');
const emptyState = document.getElementById('emptyState');
const modalOverlay = document.getElementById('deviceModal');
const deviceForm = document.getElementById('deviceForm');
const modalTitle = document.getElementById('modalTitle');
const saveButton = document.getElementById('saveButton');
const toastContainer = document.getElementById('toastContainer');

// Fetch initial data
async function fetchDevices() {
    try {
        const response = await fetch(API_URL);
        devices = await response.json();
        renderTable();
    } catch (error) {
        showToast('Failed to load devices', 'error');
    }
}

function renderTable() {
    deviceTableBody.innerHTML = '';
    
    if (devices.length === 0) {
        emptyState.classList.remove('hidden');
        document.getElementById('deviceTable').style.display = 'none';
        return;
    }
    
    emptyState.classList.add('hidden');
    document.getElementById('deviceTable').style.display = 'table';
    
    devices.forEach(device => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${device.gateway_id}</td>
            <td><strong>${device.device_id_from}</strong></td>
            <td><span class="secret-censor">${device.device_id_to}</span></td>
            <td><span class="secret-censor">••••${device.device_secret.slice(-4)}</span></td>
            <td>OK: ${device.ok_channel} | NG: ${device.ng_channel}</td>
            <td id="metric-${device.device_id_from}"><span style="opacity:0.3; font-size:0.8rem; font-style:italic;">Awaiting data...</span></td>
            <td style="display:flex; gap:0.5rem;">
                <button class="btn-icon" onclick="openModal('edit', ${device.id})">
                    <i data-lucide="edit-2"></i>
                </button>
                <button class="btn-icon btn-danger" onclick="deleteDevice(${device.id})">
                    <i data-lucide="trash-2"></i>
                </button>
            </td>
        `;
        deviceTableBody.appendChild(tr);
    });
    lucide.createIcons();
}

function openModal(mode, id = null) {
    deviceForm.reset();
    document.getElementById('deviceId').value = '';
    
    if (mode === 'add') {
        modalTitle.innerText = 'Add Device Mapping';
    } else {
        modalTitle.innerText = 'Edit Device Mapping';
        const device = devices.find(d => d.id === id);
        if (device) {
            document.getElementById('deviceId').value = device.id;
            document.getElementById('gatewayId').value = device.gateway_id;
            document.getElementById('deviceIdFrom').value = device.device_id_from;
            document.getElementById('deviceIdTo').value = device.device_id_to;
            document.getElementById('deviceSecret').value = device.device_secret;
            document.getElementById('okChannel').value = device.ok_channel;
            document.getElementById('ngChannel').value = device.ng_channel;
        }
    }
    modalOverlay.classList.remove('hidden');
    // slight delay for transition
    setTimeout(() => modalOverlay.classList.add('active'), 10);
}

function closeModal() {
    modalOverlay.classList.remove('active');
    setTimeout(() => {
        modalOverlay.classList.add('hidden');
    }, 300);
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const id = document.getElementById('deviceId').value;
    const isEdit = !!id;
    
    const data = {
        device_id_from: document.getElementById('deviceIdFrom').value,
        device_id_to: document.getElementById('deviceIdTo').value,
        device_secret: document.getElementById('deviceSecret').value,
        ok_channel: parseInt(document.getElementById('okChannel').value),
        ng_channel: parseInt(document.getElementById('ngChannel').value)
    };

    const gw = document.getElementById('gatewayId').value;
    if (gw.trim() !== '') {
        data.gateway_id = gw;
    }

    const originalButtonText = saveButton.innerText;
    saveButton.innerText = 'Saving...';
    saveButton.disabled = true;

    try {
        const method = isEdit ? 'PUT' : 'POST';
        const url = isEdit ? `${API_URL}/${id}` : API_URL;
        
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) throw new Error('API Error');
        
        showToast(`Device ${isEdit ? 'updated' : 'added'} successfully!`, 'success');
        closeModal();
        fetchDevices();
    } catch (error) {
        showToast('Failed to save device', 'error');
    } finally {
        saveButton.innerText = originalButtonText;
        saveButton.disabled = false;
    }
}

async function deleteDevice(id) {
    if (!confirm('Are you sure you want to delete this mapping?')) return;
    
    try {
        const response = await fetch(`${API_URL}/${id}`, { method: 'DELETE' });
        if (!response.ok) throw new Error();
        showToast('Device deleted', 'success');
        fetchDevices();
    } catch (e) {
        showToast('Failed to delete device', 'error');
    }
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icon = type === 'success' ? 'check-circle' : 'alert-circle';
    toast.innerHTML = `<i data-lucide="${icon}"></i> <span>${message}</span>`;
    
    toastContainer.appendChild(toast);
    lucide.createIcons();
    
    setTimeout(() => toast.classList.add('show'), 10);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// --- Live Telemetry WebSockets ---
const socket = io();
const socketStatus = document.getElementById('socketStatus');

socket.on('connect', () => {
    if(socketStatus) {
        socketStatus.className = 'tag tag-ok';
        socketStatus.innerHTML = '<span class="status-dot"></span> Live';
        socketStatus.style.opacity = '1';
    }
});

socket.on('disconnect', () => {
    if(socketStatus) {
        socketStatus.className = 'tag tag-ng';
        socketStatus.innerHTML = '<span class="status-dot" style="background:var(--danger); box-shadow:0 0 8px var(--danger);"></span> Offline';
        socketStatus.style.opacity = '0.7';
    }
});

socket.on('live_device_metric', (payload) => {
    const topicParts = payload.topic.split('/');
    if (topicParts.length > 0) {
        const deviceId = topicParts[0];
        const metricCell = document.getElementById(`metric-${deviceId}`);
        
        if (metricCell) {
            const tr = metricCell.closest('tr');
            
            // Flash effect on the row
            tr.classList.remove('flash-update');
            void tr.offsetWidth; // Trigger reflow to restart animation
            tr.classList.add('flash-update');
            
            // Render beautiful UI badge
            const channel = payload.data.channel !== undefined ? payload.data.channel : '-';
            const count = payload.data.count || 1;
            metricCell.innerHTML = `<span class="tag tag-ok" style="background: rgba(59, 130, 246, 0.15); color: #60a5fa; border-color: rgba(59, 130, 246, 0.3);">Ch${channel} | Cnt: ${count}</span>`;
        }
    }
});

// Init
document.addEventListener('DOMContentLoaded', fetchDevices);
