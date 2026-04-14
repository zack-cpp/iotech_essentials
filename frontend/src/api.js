/**
 * API client for the OEE IoT Gateway backend.
 * All endpoints are proxied via Nginx in production or Vite proxy in dev.
 */

const BASE = '/api';

async function request(url, options = {}) {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || err.error || 'Request failed');
  }
  return res.json();
}

// =============== Counting Devices ===============

export function fetchDevices() {
  return request('/devices');
}

export function createDevice(data) {
  return request('/devices', { method: 'POST', body: JSON.stringify(data) });
}

export function updateDevice(id, data) {
  return request(`/devices/${id}`, { method: 'PUT', body: JSON.stringify(data) });
}

export function deleteDevice(id) {
  return request(`/devices/${id}`, { method: 'DELETE' });
}

// =============== Inspection Devices ===============

export function fetchInspectors() {
  return request('/inspectors');
}

export function createInspector(data) {
  return request('/inspectors', { method: 'POST', body: JSON.stringify(data) });
}

export function updateInspector(id, data) {
  return request(`/inspectors/${id}`, { method: 'PUT', body: JSON.stringify(data) });
}

export function deleteInspector(id) {
  return request(`/inspectors/${id}`, { method: 'DELETE' });
}

// =============== Status ===============

export function fetchStatus() {
  return request('/status');
}
