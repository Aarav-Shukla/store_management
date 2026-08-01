import { useState } from 'react';

function EmployeeView({ token, storeId, onLogout, darkMode, setDarkMode, name }) {
    const [barcode, setBarcode] = useState('');
    const [cart, setCart] = useState([]);
    const [message, setMessage] = useState('');
    const [availability, setAvailability] = useState(null);

    async function handleScan() {
        const url = `http://127.0.0.1:8000/products/${storeId}/${barcode}`;
        const response = await fetch(url, {
            headers: { 'authorization': `Bearer ${token}` }
        });
        const product = await response.json();

        if (!product || !product.id) {
            setMessage('Product not found');
            setBarcode('');
            return;
        }

        setMessage('');

        const existing = cart.find((item) => item.id === product.id);

        if (existing) {
            setCart(cart.map((item) =>
                item.id === product.id
                    ? { ...item, quantity: item.quantity + 1 }
                    : item
            ));
        } else {
            setCart([...cart, { ...product, quantity: 1 }]);
        }

        setBarcode('');
    }

    async function handleCheckout() {
        const items = cart.map((item) => ({ product_id: item.id, quantity: item.quantity }));
        const response = await fetch('http://127.0.0.1:8000/transactions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'authorization': `Bearer ${token}` },
            body: JSON.stringify({ items: items })
        });

        const data = await response.json();

        if (response.ok) {
            setMessage(`Sale Complete. Total: $${data.total}`);
            setCart([]);
            setAvailability(null);
            setBarcode('');
        } else {
            setMessage(`Error: ${data.detail}`);
        }
    }

    async function handleCheckAvailability() {
        const response = await fetch(
            `http://127.0.0.1:8000/products/availability/${barcode}?store_id=${storeId}`,
            { headers: { 'authorization': `Bearer ${token}` } }
        );
        const data = await response.json();
        setAvailability(data);
    }

    return (
        <div className="page-content">
            <div className="card">
                <div className="card-header">
                    <h2>Welcome, {name}</h2>
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
                <input
                    value={barcode}
                    onChange={(e) => setBarcode(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') { handleScan(); } }}
                />
                <button onClick={handleScan}>Scan</button>
                <button onClick={handleCheckAvailability} disabled={!barcode.trim()}>Check Other Stores</button>

                <ul>
                    {cart.map((item, index) => (
                        <li key={index}>{item.name} x{item.quantity} - ${item.price}</li>
                    ))}
                </ul>
                <button className="btn-primary" onClick={handleCheckout}>Complete Sale</button>
                <p>{message}</p>

                {availability && (
                    <div className="card">
                        <div className="card-header">
                            <h3>{availability.product_name} — Availability</h3>
                            <button onClick={() => setAvailability(null)}>✕</button>
                        </div>
                        <ul>
                            {availability.availability.map((store) => (
                                <li key={store.store_id}>
                                    {store.store_name} — {store.quantity_on_hand} in stock ({store.distance_miles} mi away)
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>
        </div>
    );
}

export default EmployeeView;