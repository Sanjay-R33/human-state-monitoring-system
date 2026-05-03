import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

const EmployeeDashboard = () => {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [statusData, setStatusData] = useState({ emotion: 'Neutral', pulse_rate: 0, fatigue: 'Neutral' });
  const [timer, setTimer] = useState(0);
  
  const token = localStorage.getItem('token');
  const name = localStorage.getItem('name');

  const handleLogout = () => {
    localStorage.clear();
    window.location.href = '/';
  };

  const startMonitoring = async () => {
    try {
      await axios.post(`${API_URL}/start-monitoring`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setIsMonitoring(true);
    } catch (err) {
      console.error(err);
      alert('Failed to start monitoring');
    }
  };

  const stopMonitoring = async () => {
    try {
      await axios.post(`${API_URL}/stop-monitoring`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setIsMonitoring(false);
      setStatusData({ emotion: 'Neutral', pulse_rate: 0, fatigue: 'Neutral' });
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    let interval;
    if (isMonitoring) {
      interval = setInterval(async () => {
        setTimer(prev => {
          const newTimer = prev + 1;
          // Fire the API call with the updated timer
          axios.post(`${API_URL}/log-emotion?duration=${newTimer}`, {}, {
            headers: { Authorization: `Bearer ${token}` }
          }).then(res => {
            if (res.data.status === 'success') {
              const d = res.data.data;
              setStatusData({ 
                emotion: d.emotion, 
                pulse_rate: d.pulse_rate, 
                fatigue: d.dl_fatigue || 'Neutral' 
              });
            }
          }).catch(console.error);
          return newTimer;
        });
      }, 1000); // Poll and update every second
    } else {
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [isMonitoring, token]);

  const formatTime = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Dynamic styling based on emotion
  const getEmotionColor = (emotion) => {
    switch(emotion.toLowerCase()) {
      case 'happy': return 'text-green-500';
      case 'sad': return 'text-blue-500';
      case 'angry': return 'text-red-600';
      case 'stress': return 'text-orange-500';
      default: return 'text-gray-500';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <h1 className="text-xl font-bold text-indigo-600">Employee Portal</h1>
            <div className="flex items-center gap-4">
              <span className="text-gray-700 font-medium">Hello, {name}</span>
              <button 
                onClick={handleLogout}
                className="text-sm text-red-600 hover:text-red-800 font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8 flex flex-col items-center">
        <div className="w-full max-w-3xl bg-white rounded-2xl shadow-xl overflow-hidden transform transition-all">
          <div className="bg-gradient-to-r from-indigo-500 to-purple-600 p-6 text-white flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold">Current Status</h2>
              <p className="opacity-90">{isMonitoring ? 'Monitoring Active' : 'Monitoring Inactive'}</p>
            </div>
            <div className="text-right">
              <p className="text-sm opacity-90">Work Duration</p>
              <p className="text-3xl font-mono font-bold">{formatTime(timer)}</p>
            </div>
          </div>
          
          <div className="p-8 grid grid-cols-3 gap-8">
            <div className="col-span-3 flex flex-col items-center justify-center p-6 bg-gray-50 rounded-xl border border-gray-100">
              <span className="text-gray-500 font-medium mb-4">Live Camera Feed</span>
              {isMonitoring ? (
                <div className="w-full max-w-md rounded-lg overflow-hidden border-4 border-indigo-100 shadow-sm bg-black">
                  <img 
                    src={`${API_URL}/video-feed`} 
                    alt="Webcam Feed" 
                    className="w-full h-auto object-cover"
                  />
                </div>
              ) : (
                <div className="w-full max-w-md aspect-video bg-gray-200 rounded-lg flex items-center justify-center border-2 border-dashed border-gray-300">
                  <span className="text-gray-400 font-medium">Camera off. Start monitoring to view feed.</span>
                </div>
              )}
            </div>
            
            <div className="flex flex-col items-center justify-center p-6 bg-gray-50 rounded-xl border border-gray-100">
              <span className="text-gray-500 font-medium mb-2">Detected Emotion</span>
              <span className={`text-4xl font-extrabold ${getEmotionColor(statusData.emotion)}`}>
                {statusData.emotion}
              </span>
            </div>
            
            <div className="flex flex-col items-center justify-center p-6 bg-gray-50 rounded-xl border border-gray-100">
              <span className="text-gray-500 font-medium mb-2">Fatigue State</span>
              <span className={`text-4xl font-extrabold ${statusData.fatigue === 'Awake' ? 'text-green-500' : statusData.fatigue === 'Neutral' ? 'text-gray-500' : statusData.fatigue === 'Tired' ? 'text-orange-500' : 'text-red-600'}`}>
                {statusData.fatigue}
              </span>
            </div>

            <div className="flex flex-col items-center justify-center p-6 bg-gray-50 rounded-xl border border-gray-100">
              <span className="text-gray-500 font-medium mb-2">Pulse Rate</span>
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-extrabold text-rose-500">{statusData.pulse_rate}</span>
                <span className="text-gray-400 font-medium">BPM</span>
              </div>
            </div>
          </div>

          <div className="p-6 bg-gray-50 border-t border-gray-100 flex justify-center gap-4">
            {!isMonitoring ? (
              <button
                onClick={startMonitoring}
                className="px-8 py-3 rounded-full bg-indigo-600 text-white font-bold shadow-lg hover:bg-indigo-700 hover:shadow-indigo-500/30 transition-all transform hover:-translate-y-0.5"
              >
                Start Monitoring
              </button>
            ) : (
              <button
                onClick={stopMonitoring}
                className="px-8 py-3 rounded-full bg-red-600 text-white font-bold shadow-lg hover:bg-red-700 hover:shadow-red-500/30 transition-all transform hover:-translate-y-0.5"
              >
                Stop Monitoring
              </button>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default EmployeeDashboard;
