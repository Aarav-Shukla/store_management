import { useState } from 'react';
import Login from './Login';

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

  return (
    <div>
      <h2>Logged in as: {role}</h2>
    </div>
  );
}

export default App;