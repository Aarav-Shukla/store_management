import { useEffect, useState } from 'react';
import ManagerView from './ManagerView';

function RegionManagerView({ token, storeIds }) {
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
            <div>
                <button onClick={() => setSelectedStoreId(null)}>← Back to store list</button>
                <ManagerView token={token} storeId={selectedStoreId} />
            </div>
        );
    }

    return (
        <div>
            <h2>Region Manager Dashboard</h2>
            {stores.map((store) => (
                <button key={store.id} onClick={() => setSelectedStoreId(store.id)}>
                    {store.name}
                </button>
            ))}
        </div>
    );
}

export default RegionManagerView;