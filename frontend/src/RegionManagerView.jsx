import { useEffect, useState } from 'react';
import ManagerView from './ManagerView';

function RegionManagerView({ token, storeIds, onLogout, darkMode, setDarkMode }) {
    const [stores, setStores] = useState([]);
    const [selectedStoreId, setSelectedStoreId] = useState(null);

    useEffect(() => {
        async function fetchStores() {
            const response = await fetch('http://127.0.0.1:8000/stores', {
                headers: { 'authorization': `Bearer ${token}` }
            });
            const data = await response.json();
            setStores(data);
        }
        fetchStores();
    }, [token]);

    if (selectedStoreId) {
        return (
            <div className="page-content">
                <ManagerView
                    token={token}
                    storeId={selectedStoreId}
                    onLogout={onLogout}
                    darkMode={darkMode}
                    setDarkMode={setDarkMode}
                    onBack={() => setSelectedStoreId(null)}
                />
            </div>
        );
    }

    return (
        <div className="page-content">
            <div className="card">
                <div className="card-header">
                    <h2>Region Manager Dashboard</h2>
                    <div className="header-controls">
                        <label className="theme-toggle">
                            <input
                                type="checkbox"
                                checked={darkMode}
                                onChange={() => setDarkMode(!darkMode)}
                            />
                            <span className="slider"></span>
                        </label>
                        <button onClick={onLogout}>Log Out</button>
                    </div>
                </div>
                {stores.map((store) => (
                    <button key={store.id} onClick={() => setSelectedStoreId(store.id)}>
                        {store.name}
                    </button>
                ))}
            </div>
        </div>
    );
}

export default RegionManagerView;