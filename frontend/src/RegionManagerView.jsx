import { useEffect, useState } from 'react';
import ManagerView from './ManagerView';
import { API_URL } from './config';

function RegionManagerView({ token, storeIds, onLogout, darkMode, setDarkMode, name }) {
    const [stores, setStores] = useState([]);
    const [selectedStoreId, setSelectedStoreId] = useState(null);

    useEffect(() => {
        async function fetchStores() {
            const response = await fetch(`${API_URL}/stores`, {
                headers: { 'authorization': `Bearer ${token}` }
            });
            const data = await response.json();
            setStores(data);
            if (data.length > 0 && !selectedStoreId) {
                setSelectedStoreId(data[0].id);
            }
        }
        fetchStores();
    }, [token]);

    if (!selectedStoreId) return null;

    return (
        <ManagerView
            token={token}
            storeId={selectedStoreId}
            onLogout={onLogout}
            darkMode={darkMode}
            setDarkMode={setDarkMode}
            name={name}
            stores={stores}
            onSwitchStore={setSelectedStoreId}
        />
    );
}

export default RegionManagerView;