import { useEffect, useState } from 'react';
import { io } from 'socket.io-client';

export function useTelemetry() {
  const [socketStatus, setSocketStatus] = useState('disconnected');
  const [metrics, setMetrics] = useState({});

  useEffect(() => {
    // Connect to Flask backend
    const socket = io('/', { transports: ['polling', 'websocket'] });

    socket.on('connect', () => {
      setSocketStatus('connected');
    });
    
    socket.on('disconnect', () => {
      setSocketStatus('disconnected');
    });

    socket.on('live_device_metric', (payload) => {
      let deviceId = null;
      let displayData = { ...payload.data };

      // Inspect Topic vs Count Topic
      if (payload.data && payload.data.MESIN_ID) {
        deviceId = payload.data.MESIN_ID;
        // Simplify arrays for inspect nodes visually
        displayData.status = "Sensors: " + (payload.data.SENSOR_ID ? payload.data.SENSOR_ID.length : 0);
      } else {
        const topicParts = payload.topic?.split('/');
        if (topicParts && topicParts.length > 0) {
          deviceId = topicParts[0];
          displayData.status = `Ch${payload.data.channel !== undefined ? payload.data.channel : '-'}`;
        }
      }

      if (deviceId) {
        setMetrics(prev => ({
          ...prev,
          [deviceId]: {
            ...displayData,
            timestamp: Date.now()
          }
        }));
      }
    });

    return () => socket.disconnect();
  }, []);

  return { socketStatus, metrics };
}
