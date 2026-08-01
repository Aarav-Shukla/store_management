import { useState } from 'react';
import EmployeeView from './EmployeeView';
import Login from './Login';
import ManagerView from './ManagerView';

function App() {
  const [token, setToken] = useState(null);
  const [role, setRole] = useState(null);

  if (!token) {
    return (
      <div>
        <Login onLoginSuccess={(token, role) => { setToken(token); setRole(role); }} />
      </div>
    );
  }

  if (role === 'employee') {
    return <EmployeeView token={token} />;
  }

  return <ManagerView token={token} />;
}

export default App;