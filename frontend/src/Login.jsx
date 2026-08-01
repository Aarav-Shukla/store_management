import { useState } from 'react';

function Login({ onLoginSuccess }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    async function handleLogin() {
        const response = await fetch('http://127.0.0.1:8000/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: username, password: password })
        });
        const data = await response.json();
        onLoginSuccess(data.access_token, data.role, data.store_ids)
    }

    return (
        <div className="login-content">
            <div className="card">
                <h2>Log In</h2>
                <div className="form-stack">
                    <input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
                    <input
                        placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter') { handleLogin(); } }}
                    />
                    <button className="btn-primary" onClick={handleLogin}>Log In</button>
                </div>
            </div>
        </div>
    );
}

export default Login;