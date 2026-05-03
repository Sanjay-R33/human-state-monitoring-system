import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import EmployeeDashboard from './components/EmployeeDashboard';
import ManagerDashboard from './components/ManagerDashboard';

function App() {
  const token = localStorage.getItem('token');
  const role = localStorage.getItem('role');

  const getHomeRoute = () => {
    if (!token) return <Login />;
    if (role === 'Employee') return <Navigate to="/employee" />;
    if (role === 'Manager') return <Navigate to="/manager" />;
    
    // If token exists but role is invalid, clear and show login
    localStorage.clear();
    return <Login />;
  };

  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <Routes>
          <Route path="/" element={getHomeRoute()} />
          <Route path="/employee" element={
            token && role === 'Employee' ? <EmployeeDashboard /> : <Navigate to="/" />
          } />
          <Route path="/manager" element={
            token && role === 'Manager' ? <ManagerDashboard /> : <Navigate to="/" />
          } />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
