import { useEffect, useState } from 'react';

function ManagerView({ token }) {
    const [products, setProducts] = useState([]);

    useEffect(() => {
        async function fetchProducts() {
            const response = await fetch('http://127.0.0.1:8000/products');
            const data = await response.json();
            setProducts(data);
        }
        fetchProducts();
    }, []);

    return (
        <div>
            <h2>Manager Dashboard</h2>
            <table>
                <thead>
                    <tr>
                    <th>Name</th>
                    <th>Barcode</th>
                    <th>Price</th>
                    <th>Stock</th>
                    </tr>
                </thead>
                <tbody>
                    {products.map((product) => (
                    <tr key={product.id}>
                        <td>{product.name}</td>
                        <td>{product.barcode}</td>
                        <td>${product.price}</td>
                        <td>{product.quantity_on_hand}</td>
                    </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export default ManagerView;