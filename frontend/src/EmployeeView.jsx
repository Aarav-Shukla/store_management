import { useState } from 'react';

function EmployeeView({ token, storeId }) {
    const [barcode, setBarcode] = useState('');
    const [cart, setCart] = useState([]);
    const [message, setMessage] = useState('');

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
        } else {
            setMessage(`Error: ${data.detail}`);
        }
    }

    return (
        <div>
            <h2>Employee Checkout</h2>
            <input
                value={barcode}
                onChange={(e) => setBarcode(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') { handleScan(); } }}
            />
            <button onClick={handleScan}>Scan</button>
            <ul>
                {cart.map((item, index) => (
                    <li key={index}>{item.name} x{item.quantity} - ${item.price}</li>
                ))}
            </ul>
            <button onClick={handleCheckout}>Complete Sale</button>
            <p>{message}</p>
        </div>
    );
}

export default EmployeeView;