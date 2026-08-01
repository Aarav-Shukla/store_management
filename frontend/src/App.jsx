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
  const [name, setName] = useState('');

  function handleLogout() {
    setToken(null);
    setRole(null);
    setStoreIds([]);
    setName('');
  }

  let content;

  if (!token) {
    content = <Login onLoginSuccess={(token, role, storeIds, name) => {
      setToken(token);
      setRole(role);
      setStoreIds(storeIds);
      setName(name);
    }} />;
  } else if (role === 'employee') {
    content = <EmployeeView token={token} storeId={storeIds[0]} onLogout={handleLogout} darkMode={darkMode} setDarkMode={setDarkMode} name={name} />;
  } else if (role === 'manager') {
    content = <ManagerView token={token} storeId={storeIds[0]} onLogout={handleLogout} darkMode={darkMode} setDarkMode={setDarkMode} name={name} />;
  } else {
    content = <RegionManagerView token={token} storeIds={storeIds} onLogout={handleLogout} darkMode={darkMode} setDarkMode={setDarkMode} name={name} />;
  }

  return (
    <div className={`app-wrapper ${darkMode ? 'dark' : ''}`}>
      {content}
    </div>
  );
}

export default App;