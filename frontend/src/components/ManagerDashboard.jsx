import React, { useState, useEffect, useRef } from 'react';

const API_WS_URL = 'ws://localhost:8000/ws/manager';

const ManagerDashboard = () => {
  const [employees, setEmployees] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const abnormalTrackers = useRef({});
  const name = localStorage.getItem('name');

  const handleLogout = () => {
    localStorage.clear();
    window.location.href = '/';
  };

  useEffect(() => {
    let ws;
    let reconnectTimeout;

    const connectWebSocket = () => {
      try {
        ws = new WebSocket(API_WS_URL);

        ws.onopen = () => {
          setConnectionStatus('connected');
        };

        ws.onmessage = (event) => {
          try {
            const parsedData = JSON.parse(event.data);
            const now = Date.now();
            
            // Enforce default values for inactive employees
            const data = parsedData.map(emp => {
              if (emp.status === 'Inactive') {
                return {
                  ...emp,
                  emotion: 'Neutral',
                  fatigue: 'Neutral',
                  pulse_rate: 0,
                  work_duration: 0
                };
              }
              return emp;
            });
            
            data.forEach(emp => {
              const isPulseAbnormal = emp.pulse_rate > 0 && (emp.pulse_rate < 60 || emp.pulse_rate > 100);
              const isEmotionAbnormal = ['high stress', 'shock', 'anxious', 'angry', 'sad', 'fatigued'].includes(emp.emotion?.toLowerCase());
              const isFatigueAbnormal = ['tired', 'sleepy'].includes(emp.fatigue?.toLowerCase());
              const isAbnormal = emp.status === 'Active' && (isPulseAbnormal || isEmotionAbnormal || isFatigueAbnormal);
              
              if (isAbnormal) {
                if (!abnormalTrackers.current[emp.id]) {
                  abnormalTrackers.current[emp.id] = now;
                }
              } else {
                delete abnormalTrackers.current[emp.id];
              }
            });
            
            setEmployees(data);
          } catch (e) {
            console.error('Failed to parse WebSocket message:', e);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket Error:', error);
          setConnectionStatus('error');
        };

        ws.onclose = () => {
          setConnectionStatus('disconnected');
          // Attempt to reconnect after 3 seconds
          reconnectTimeout = setTimeout(connectWebSocket, 3000);
        };
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        setConnectionStatus('error');
        reconnectTimeout = setTimeout(connectWebSocket, 3000);
      }
    };

    connectWebSocket();

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (ws) ws.close();
    };
  }, []);

  const formatTime = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hrs.toString().padStart(2, '0')}h ${mins.toString().padStart(2, '0')}m`;
  };

  const getStatusBadge = (status) => {
    return status === 'Active' 
      ? <span className="px-3 py-1 text-xs font-bold bg-green-100 text-green-800 rounded-full">Active</span>
      : <span className="px-3 py-1 text-xs font-bold bg-gray-100 text-gray-800 rounded-full">Inactive</span>;
  };

  const getEmotionColor = (emotion) => {
    switch(emotion?.toLowerCase()) {
      case 'happy': return 'bg-green-50 border-green-200 text-green-700';
      case 'sad': return 'bg-blue-50 border-blue-200 text-blue-700';
      case 'angry': return 'bg-red-50 border-red-200 text-red-700';
      case 'stress': return 'bg-orange-50 border-orange-200 text-orange-700';
      default: return 'bg-gray-50 border-gray-200 text-gray-700';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-slate-900 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <h1 className="text-xl font-bold text-white">Manager Portal / Live Monitoring</h1>
            <div className="flex items-center gap-4">
              <span className="text-slate-300 font-medium">Manager: {name}</span>
              <button 
                onClick={handleLogout}
                className="text-sm bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-md font-medium transition"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-end mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Employee Overview</h2>
            <p className="text-gray-500 mt-1">Real-time status and emotion metrics.</p>
          </div>
          <div className="flex items-center gap-2">
            {connectionStatus === 'connected' && (
              <>
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                </span>
                <span className="text-sm text-green-600 font-medium">Live Connection</span>
              </>
            )}
            {connectionStatus === 'connecting' && (
              <>
                <span className="relative flex h-3 w-3">
                  <span className="animate-pulse absolute inline-flex h-full w-full rounded-full bg-yellow-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-yellow-500"></span>
                </span>
                <span className="text-sm text-yellow-600 font-medium">Connecting...</span>
              </>
            )}
            {(connectionStatus === 'disconnected' || connectionStatus === 'error') && (
              <>
                <span className="relative flex h-3 w-3">
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                </span>
                <span className="text-sm text-red-600 font-medium">Disconnected</span>
              </>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {employees.map(emp => {
            const abnormalStartTime = abnormalTrackers.current[emp.id];
            // Highlight if abnormal for more than 5 seconds
            const isHighlighted = abnormalStartTime && (Date.now() - abnormalStartTime > 5000);
            
            return (
            <div 
              key={emp.id} 
              className={`rounded-xl shadow-sm border overflow-hidden hover:shadow-md transition ${isHighlighted ? 'bg-red-50 border-red-400 ring-2 ring-red-400 ring-opacity-50' : 'bg-white border-gray-200'}`}
            >
              <div className={`p-5 border-b flex justify-between items-center ${isHighlighted ? 'border-red-200 bg-red-100/50' : 'border-gray-100 bg-gray-50/50'}`}>
                <h3 className={`font-bold text-lg ${isHighlighted ? 'text-red-900' : 'text-gray-900'}`}>{emp.name}</h3>
                {getStatusBadge(emp.status)}
              </div>
              <div className="p-5 space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500 font-medium">Current Emotion</span>
                  <span className={`px-3 py-1 rounded-md border font-semibold text-sm ${getEmotionColor(emp.emotion)}`}>
                    {emp.emotion || 'Unknown'}
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500 font-medium">Fatigue State</span>
                  <span className={`px-3 py-1 rounded-md border font-semibold text-sm ${emp.fatigue === 'Awake' ? 'bg-green-50 border-green-200 text-green-700' : emp.fatigue === 'Neutral' ? 'bg-gray-50 border-gray-200 text-gray-700' : emp.fatigue === 'Tired' ? 'bg-orange-50 border-orange-200 text-orange-700' : 'bg-red-50 border-red-200 text-red-700'}`}>
                    {emp.fatigue || 'Neutral'}
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500 font-medium">Pulse Rate</span>
                  <div className="flex items-center gap-1">
                    <span className="font-bold text-lg text-rose-500">{emp.pulse_rate || 0}</span>
                    <span className="text-xs text-gray-400 font-bold">BPM</span>
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500 font-medium">Session Duration</span>
                  <span className="font-mono text-sm text-gray-700 font-medium">
                    {formatTime(emp.work_duration || 0)}
                  </span>
                </div>
              </div>
            </div>
            );
          })}
          {employees.length === 0 && (
            <div className="col-span-full py-12 text-center text-gray-500 bg-white rounded-xl border border-dashed border-gray-300">
              No employees found in the system.
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default ManagerDashboard;
