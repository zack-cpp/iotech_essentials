import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import CountingNodes from './pages/CountingNodes';
import InspectionNodes from './pages/InspectionNodes';
import { fetchStatus } from './api';

export default function App() {
  const [gatewayId, setGatewayId] = useState('');

  useEffect(() => {
    fetchStatus()
      .then((s) => setGatewayId(s.gateway_id))
      .catch(() => {});
  }, []);

  return (
    <BrowserRouter>
      <Layout gatewayId={gatewayId}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/counting" element={<CountingNodes />} />
          <Route path="/inspection" element={<InspectionNodes />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
