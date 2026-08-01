import { useState } from 'react';
import EmployeeView from './EmployeeView';
import Login from './Login';
import ManagerView from './ManagerView';
import RegionManagerView from './RegionManagerView';

function App() {
  const [token, setToken] = useState(null);
  const [role, setRole] = useState(null);
  const [storeIds, setStoreIds] = useState([]);

  if (!token) {
    return (
      <div>
        <Login onLoginSuccess={(token, role, storeIds) => {
          setToken(token);
          setRole(role);
          setStoreIds(storeIds);
        }} />
      </div>
    );
  }

  if (role === 'employee') {
    return <EmployeeView token={token} storeId={storeIds[0]} />;
  }

  if (role === 'manager') {
    return <ManagerView token={token} storeId={storeIds[0]} />;
  }

  return <RegionManagerView token={token} storeIds={storeIds} />;
}

export default App;