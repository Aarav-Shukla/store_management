import { useEffect, useState } from 'react';
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

function ManagerView({ token, storeId, onLogout, darkMode, setDarkMode, onBack, name }) {
    const [products, setProducts] = useState([]);
    const [restockAmounts, setRestockAmounts] = useState({});
    const [history, setHistory] = useState([]);
    const [expandedId, setExpandedId] = useState(null);
    const [expandedItems, setExpandedItems] = useState([]);
    const [page, setPage] = useState(0);
    const pageSize = 5;
    const [productPage, setProductPage] = useState(0);
    const productPageSize = 10;
    const [analytics, setAnalytics] = useState(null);

    async function fetchAnalytics() {
        const response = await fetch(
            `http://127.0.0.1:8000/analytics/summary?store_id=${storeId}`,
            { headers: { 'authorization': `Bearer ${token}` } }
        );
        const data = await response.json();
        setAnalytics(data);
    }

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
        fetchAnalytics();
        setPage(0);
        setProductPage(0);
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

    function renderPageNumbers(currentPage, total, onSelect) {
        const pages = [];
        for (let i = 0; i < total; i++) {
            if (i === 0 || i === total - 1 || Math.abs(i - currentPage) <= 1) {
                pages.push(i);
            } else if (pages[pages.length - 1] !== '...') {
                pages.push('...');
            }
        }
        return pages.map((p, index) =>
            p === '...' ? (
                <span key={`ellipsis-${index}`}>...</span>
            ) : (
                <button
                    key={p}
                    className={p === currentPage ? 'btn-primary' : ''}
                    onClick={() => onSelect(p)}
                >
                    {p + 1}
                </button>
            )
        );
    }

    const paginatedHistory = history.slice(page * pageSize, (page + 1) * pageSize);
    const totalPages = Math.ceil(history.length / pageSize);

    const paginatedProducts = products.slice(productPage * productPageSize, (productPage + 1) * productPageSize);
    const totalProductPages = Math.ceil(products.length / productPageSize);

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
            </div>

            <div className="dashboard-grid">
                <div className="dashboard-column">
                    {analytics && (
                        <div className="card card-flex">
                            <h3>Analytics (Last 30 Days)</h3>
                            <div className="kpi-row">
                                <div className="kpi">
                                    <span className="kpi-value">${analytics.total_revenue}</span>
                                    <span className="kpi-label">Total Revenue</span>
                                </div>
                                <div className="kpi">
                                    <span className="kpi-value">{analytics.transaction_count}</span>
                                    <span className="kpi-label">Transactions</span>
                                </div>
                                <div className="kpi">
                                    <span className="kpi-value">${analytics.average_transaction}</span>
                                    <span className="kpi-label">Avg. Transaction</span>
                                </div>
                            </div>

                            <div style={{ flex: 1, minHeight: 200 }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={analytics.daily_revenue}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                                        <XAxis dataKey="day" stroke="var(--text-secondary)" fontSize={12} />
                                        <YAxis stroke="var(--text-secondary)" fontSize={12} />
                                        <Tooltip
                                            contentStyle={{
                                                backgroundColor: 'var(--surface)',
                                                border: '1px solid var(--border)',
                                                borderRadius: '6px',
                                                color: 'var(--text)'
                                            }}
                                            labelStyle={{ color: 'var(--text)' }}
                                        />
                                        <Line type="monotone" dataKey="revenue" stroke="var(--accent)" strokeWidth={2} dot={false} />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    )}

                    {analytics && (
                        <div className="card card-flex">
                            <h3>Top Products (Last 30 Days)</h3>
                            <div style={{ flex: 1, minHeight: 200 }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={analytics.top_products} layout="vertical">
                                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                                        <XAxis type="number" stroke="var(--text-secondary)" fontSize={12} />
                                        <YAxis type="category" dataKey="name" stroke="var(--text-secondary)" fontSize={12} width={120} />
                                        <Tooltip
                                            contentStyle={{
                                                backgroundColor: 'var(--surface)',
                                                border: '1px solid var(--border)',
                                                borderRadius: '6px',
                                                color: 'var(--text)'
                                            }}
                                            labelStyle={{ color: 'var(--text)' }}
                                        />
                                        <Bar dataKey="quantity_sold" fill="var(--accent)" radius={[0, 4, 4, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    )}
                </div>

                <div className="dashboard-column">
                    <div className="card">
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
                                {paginatedProducts.map((product) => (
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
                        <div className="pagination-controls">
                            <button onClick={() => setProductPage(productPage - 1)} disabled={productPage === 0}>Previous</button>
                            {renderPageNumbers(productPage, totalProductPages, setProductPage)}
                            <button onClick={() => setProductPage(productPage + 1)} disabled={productPage === totalProductPages - 1}>Next</button>
                        </div>
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
                            {renderPageNumbers(page, totalPages, setPage)}
                            <button onClick={() => setPage(page + 1)} disabled={page === totalPages - 1}>Next</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default ManagerView;