import { useEffect, useState } from 'react';

function ManagerView({ token, storeId, onLogout, darkMode, setDarkMode, onBack, name }) {
    const [products, setProducts] = useState([]);
    const [restockAmounts, setRestockAmounts] = useState({});
    const [history, setHistory] = useState([]);
    const [expandedId, setExpandedId] = useState(null);
    const [expandedItems, setExpandedItems] = useState([]);
    const [page, setPage] = useState(0);
    const pageSize = 5;

    async function fetchProducts() {
        const response = await fetch(`http://127.0.0.1:8000/products?store_id=${storeId}`, {
            headers: { 'authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        setProducts(data);
    }

    async function fetchHistory() {
        const response = await fetch(
            `http://127.0.0.1:8000/transactions/history?store_id=${storeId}`,
            { headers: { 'authorization': `Bearer ${token}` } }
        );
        const data = await response.json();
        setHistory(data);
    }

    useEffect(() => {
        fetchProducts();
        fetchHistory();
        setPage(0);
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

    async function toggleTransaction(id) {
        if (expandedId === id) {
            setExpandedId(null);
            return;
        }
        const response = await fetch(
            `http://127.0.0.1:8000/transactions/${id}/items`,
            { headers: { 'authorization': `Bearer ${token}` } }
        );
        const data = await response.json();
        setExpandedItems(data);
        setExpandedId(id);
    }

    const paginatedHistory = history.slice(page * pageSize, (page + 1) * pageSize);
    const totalPages = Math.ceil(history.length / pageSize);

    function renderPageNumbers() {
        const pages = [];
        for (let i = 0; i < totalPages; i++) {
            if (i === 0 || i === totalPages - 1 || Math.abs(i - page) <= 1) {
                pages.push(i);
            } else if (pages[pages.length - 1] !== '...') {
                pages.push('...');
            }
        }
        return pages;
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

            <div className="card">
                <h3>Transaction History</h3>
                {paginatedHistory.map((tx) => (
                    <div key={tx.id} className="transaction-row">
                        <button className="transaction-header" onClick={() => toggleTransaction(tx.id)}>
                            <span>Transaction {tx.id} — ${tx.total}</span>
                            <span>{expandedId === tx.id ? 'v' : '^'}</span>
                        </button>
                        {expandedId === tx.id && (
                            <ul>
                                {expandedItems.map((item, index) => (
                                    <li key={index}>{item.name} x{item.quantity} - ${item.price_at_sale}</li>
                                ))}
                            </ul>
                        )}
                    </div>
                ))}
                <div className="pagination-controls">
                    <button onClick={() => setPage(page - 1)} disabled={page === 0}>Previous</button>
                    {renderPageNumbers().map((p, index) =>
                        p === '...' ? (
                            <span key={`ellipsis-${index}`}>...</span>
                        ) : (
                            <button
                                key={p}
                                className={p === page ? 'btn-primary' : ''}
                                onClick={() => setPage(p)}
                            >
                                {p + 1}
                            </button>
                        )
                    )}
                    <button onClick={() => setPage(page + 1)} disabled={page === totalPages - 1}>Next</button>
                </div>
            </div>
        </div>
    );
}

export default ManagerView;