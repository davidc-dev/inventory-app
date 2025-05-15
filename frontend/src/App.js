// frontend/src/App.js
import React, { useState, useEffect } from 'react';
import axios from 'axios'; // For making HTTP requests
import './App.css'; // You can create this file for basic styling or use Tailwind

// Define the base URL for your API.
// In development, the frontend (port 3000) and backend (port 8000) are different.
// Docker Compose network allows 'backend' to be resolved.
// For local development outside Docker, you might use 'http://localhost:8000'.
// When deployed, these might be the same domain or configured via environment variables.
const API_BASE_URL = '/api/v1'; // Using relative path, assuming proxy or same-origin

function App() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // --- Fetching Data ---
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        // Use Promise.all to fetch all data concurrently
        const [productsResponse, categoriesResponse, suppliersResponse] = await Promise.all([
          axios.get(`${API_BASE_URL}/products/?limit=10`), // Fetch first 10 products
          axios.get(`${API_BASE_URL}/categories/?limit=10`), // Fetch first 10 categories
          axios.get(`${API_BASE_URL}/suppliers/?limit=10`) // Fetch first 10 suppliers
        ]);
        setProducts(productsResponse.data);
        setCategories(categoriesResponse.data);
        setSuppliers(suppliersResponse.data);
      } catch (err) {
        console.error("Error fetching data:", err);
        let errorMessage = "Failed to fetch data. ";
        if (err.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          errorMessage += `Server responded with ${err.response.status}: ${JSON.stringify(err.response.data)}`;
        } else if (err.request) {
          // The request was made but no response was received
          errorMessage += "No response received from server. Is the backend running and accessible?";
        } else {
          // Something happened in setting up the request that triggered an Error
          errorMessage += err.message;
        }
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []); // Empty dependency array means this effect runs once on mount

  // --- Render Logic ---
  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-gray-100">
        <p className="text-xl text-gray-700">Loading inventory data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col justify-center items-center min-h-screen bg-red-100 p-4">
        <p className="text-xl text-red-700 font-semibold">Error:</p>
        <p className="text-red-600 mt-2 text-center">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 font-sans">
      <header className="bg-indigo-600 text-white p-6 rounded-lg shadow-lg mb-8">
        <h1 className="text-4xl font-bold text-center">Inventory Management System</h1>
      </header>

      {/* Products Section */}
      <section className="mb-8 p-6 bg-white rounded-lg shadow-md">
        <h2 className="text-2xl font-semibold mb-4 text-indigo-700 border-b-2 border-indigo-200 pb-2">Products</h2>
        {products.length > 0 ? (
          <ul className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {products.map(product => (
              <li key={product.id} className="bg-gray-50 p-4 rounded-lg shadow hover:shadow-xl transition-shadow duration-300">
                <h3 className="text-xl font-medium text-gray-800">{product.name} (SKU: {product.sku})</h3>
                <p className="text-sm text-gray-600">{product.description || "No description available."}</p>
                <div className="mt-2 text-sm">
                  <p><span className="font-semibold">Price:</span> ${product.sale_price.toFixed(2)}</p>
                  <p><span className="font-semibold">Stock:</span> {product.quantity_on_hand}</p>
                  {product.category && <p><span className="font-semibold">Category:</span> {product.category.name}</p>}
                  {product.supplier && <p><span className="font-semibold">Supplier:</span> {product.supplier.name}</p>}
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-600">No products found.</p>
        )}
      </section>

      {/* Categories Section */}
      <section className="mb-8 p-6 bg-white rounded-lg shadow-md">
        <h2 className="text-2xl font-semibold mb-4 text-green-700 border-b-2 border-green-200 pb-2">Categories</h2>
        {categories.length > 0 ? (
          <div className="flex flex-wrap gap-4">
            {categories.map(category => (
              <div key={category.id} className="bg-green-50 p-3 rounded-md shadow">
                <h3 className="text-lg font-medium text-green-800">{category.name}</h3>
                <p className="text-xs text-gray-600">{category.description || "No description"}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-600">No categories found.</p>
        )}
      </section>

      {/* Suppliers Section */}
      <section className="p-6 bg-white rounded-lg shadow-md">
        <h2 className="text-2xl font-semibold mb-4 text-purple-700 border-b-2 border-purple-200 pb-2">Suppliers</h2>
        {suppliers.length > 0 ? (
          <div className="space-y-3">
            {suppliers.map(supplier => (
              <div key={supplier.id} className="bg-purple-50 p-3 rounded-md shadow">
                <h3 className="text-lg font-medium text-purple-800">{supplier.name}</h3>
                {supplier.contact_person && <p className="text-sm text-gray-600">Contact: {supplier.contact_person}</p>}
                {supplier.email && <p className="text-sm text-gray-600">Email: {supplier.email}</p>}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-600">No suppliers found.</p>
        )}
      </section>

      <footer className="text-center mt-12 py-4 text-gray-500 text-sm">
        <p>&copy; {new Date().getFullYear()} Inventory Management Inc. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default App;
