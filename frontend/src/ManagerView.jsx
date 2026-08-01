import { useEffect, useState } from 'react';

function ManagerView({ token, storeId, onLogout, darkMode, setDarkMode, onBack, name }) {
    const [products, setProducts] = useState([]);
    const [restockAmounts, setRestockAmounts] = useState({});

    async function fetchProducts() {
        const response = await fetch(`http://127.0.0.1:8000/products?store_id=${storeId}`, {
            headers: { 'authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        setProducts(data);
    }

    useEffect(() => {
        fetchProducts();
    }, [storeId]);

    async function handleRestock(productId) {
        const amount = parseInt(restockAmounts[productId] || 0);
        const response = await fetch(`http://127.0.0.1:8000/products/${productId}/restock`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'authorization': `Bearer ${token}` },
            body: JSON.stringify({ amount: amount })
        });
        if (response.ok) {
            fetchProducts();
        }
    }

    return (
        <div className="page-content">
            <div className="card">
                <div className="card-header">
                    <h2>Welcome, {name}</h2>
                    <div className="header-controls">
                        {onBack && <button onClick={onBack}>← Back</button>}
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
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Barcode</th>
                            <th>Price</th>
                            <th>Stock</th>
                            <th>Restock</th>
                        </tr>
                    </thead>
                    <tbody>
                        {products.map((product) => (
                            <tr key={product.id} style={{ backgroundColor: product.quantity_on_hand < product.reorder_threshold ? 'var(--danger-bg)' : 'transparent' }}>
                                <td>{product.name}</td>
                                <td>{product.barcode}</td>
                                <td>${product.price}</td>
                                <td>{product.quantity_on_hand}</td>
                                <td>
                                    <input
                                        type="number"
                                        value={restockAmounts[product.id] || ''}
                                        onChange={(e) => setRestockAmounts({ ...restockAmounts, [product.id]: e.target.value })}
                                    />
                                    <button onClick={() => handleRestock(product.id)}>Restock</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default ManagerView;