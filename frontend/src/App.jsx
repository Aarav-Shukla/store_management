import { useState } from 'react';
import EmployeeView from './EmployeeView';
import Login from './Login';
import ManagerView from './ManagerView';
import RegionManagerView from './RegionManagerView';
import './index.css';

function App() {
  const [token, setToken] = useState(null);
  const [role, setRole] = useState(null);
  const [storeIds, setStoreIds] = useState([]);
  const [darkMode, setDarkMode] = useState(false);

  function handleLogout() {
    setToken(null);
    setRole(null);
    setStoreIds([]);
  }

  let content;

  if (!token) {
    content = <Login onLoginSuccess={(token, role, storeIds) => {
      setToken(token);
      setRole(role);
      setStoreIds(storeIds);
    }} />;
  } else if (role === 'employee') {
    content = <EmployeeView token={token} storeId={storeIds[0]} onLogout={handleLogout} />;
  } else if (role === 'manager') {
    content = <ManagerView token={token} storeId={storeIds[0]} onLogout={handleLogout} />;
  } else {
    content = <RegionManagerView token={token} storeIds={storeIds} onLogout={handleLogout} />;
  }

  return (
    <div className={`app-wrapper ${darkMode ? 'dark' : ''}`}>
      <label className="theme-toggle">
        <input
          type="checkbox"
          checked={darkMode}
          onChange={() => setDarkMode(!darkMode)}
        />
        <span className="slider"></span>
      </label>
      {content}
    </div>
  );
}

export default App;