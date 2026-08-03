# Store Management System

A full-stack, multi-store inventory and point-of-sale system with role-based access control, built to demonstrate backend data modeling, concurrency-safe transactions, and full-stack application design.

**Live Demo:** [store-management-beta-beryl.vercel.app](https://store-management-beta-beryl.vercel.app)

> Note: the backend runs on Render's free tier, which spins down after periods of inactivity. The first request after idle time may take 30–60 seconds to respond while the server wakes up.

## Overview

This application simulates a retail chain's internal management software, supporting three permission tiers — **Employee**, **Manager**, and **Region Manager** — each with tailored views and capabilities across a network of 5 stores.

- **Employees** scan/checkout items, view real-time cross-store product availability, and review transaction history.
- **Managers** oversee a single store's inventory, restocking, sales analytics, and transaction history.
- **Region Managers** oversee multiple stores, switching between store dashboards from a single interface.

## Tech Stack

- **Frontend:** React (Vite), Recharts for data visualization — deployed on Vercel
- **Backend:** FastAPI (Python) — deployed on Render
- **Database:** PostgreSQL — hosted on Supabase
- **Auth:** JWT-based authentication, bcrypt password hashing

## Architecture

```text
React (Vite)
      │
      ▼
FastAPI Backend
      │
      ▼
PostgreSQL (Supabase)
```

## Key Features

### Concurrency-Safe Checkout
Checkout transactions use PostgreSQL row-level locking (`SELECT ... FOR UPDATE`) inside atomic database transactions to prevent overselling when multiple checkouts target the same product simultaneously. Every stock change (sale or restock) is recorded in an append-only `inventory_log` table, providing a full audit trail.

### Multi-Store Architecture
The schema supports true multi-tenancy: products, transactions, and inventory are all scoped to a specific store. Region Managers are linked to multiple stores via a dedicated join table (`region_manager_stores`), while Employees and Managers belong to exactly one store. Every backend route enforces store-level authorization based on the requesting user's access.

### Cross-Store Product Availability
Given a product barcode, the system can look up which other stores have that same product (matched by a store-independent SKU) currently in stock, and calculate real-world distance to each using the Haversine formula applied to store latitude/longitude coordinates — sorted nearest to farthest.

### Role-Based Authorization
JWT tokens carry the user's role and accessible store IDs. Backend routes validate both authentication (is this a valid, non-expired token?) and authorization (does this specific user have access to this specific store/resource?) before processing any request.

### Sales Analytics
Managers and Region Managers can view a 30-day analytics summary per store: total revenue, transaction count, average transaction value, a daily revenue trend chart, and a top-products-by-volume chart — all computed via SQL aggregation queries.

### Persistent Sessions
Login state persists across page refreshes via localStorage, so the app behaves like a real production tool rather than losing session state on reload.

## Database Schema

- `stores` — store locations, including lat/lng for distance calculations
- `users` — employee/manager/region_manager accounts, bcrypt-hashed passwords
- `region_manager_stores` — join table for region manager → multi-store access
- `products` — store-scoped inventory, with a store-independent `sku` linking the same product across stores
- `transactions` / `transaction_items` — sales records and line items
- `inventory_log` — append-only audit trail of all stock changes (sales, restocks)

## Running Locally

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in `backend/`:
```
DATABASE_URL=your_postgres_connection_string
JWT_SECRET=your_secret_key
```

```bash
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
```

Create a `.env` file in `frontend/`:
```
VITE_API_URL=http://127.0.0.1:8000
```

```bash
npm run dev
```

### Seeding Test Data
```bash
cd backend
python seed_data.py
```
Populates 5 stores, 25 products per store, and ~60–100 randomized historical transactions per store over the past 60 days.

## Project Structure
```
store_management/
├── README.md
├── backend/
│   ├── main.py              # FastAPI app and all API routes
│   ├── database.py          # Async connection pool setup
│   ├── seed_data.py         # Realistic test data generator
│   ├── requirements.txt
│   └── .env                 # Local secrets (gitignored)
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── .env                 # Local API URL (gitignored)
│   └── src/
│       ├── main.jsx         # React entry point
│       ├── App.jsx          # Root component, auth state, routing
│       ├── config.js        # API URL configuration
│       ├── index.css        # Global styles, theming, design system
│       ├── Login.jsx
│       ├── EmployeeView.jsx
│       ├── ManagerView.jsx
│       └── RegionManagerView.jsx
```

## Development Workflow

Although this was a solo project, development followed a structured software engineering workflow. Work was organized using a [GitHub Projects Kanban board](https://github.com/users/Aarav-Shukla/projects/2), with individual features, enhancements, and bug fixes tracked as [GitHub Issues](https://github.com/Aarav-Shukla/store_management/issues). Each issue was tied to the commits that resolved it, providing a documented development history from planning through implementation.

## Future Enhancements

- Region-wide aggregated analytics view (across all stores, not just per-store)
- Employee-initiated inter-store transfer requests
- Bespoke schema and permission tiers, configurable for any small business's organizational structure

## Author

Aarav Shukla — built as a portfolio project to demonstrate full-stack development, relational database design, and concurrent transaction handling.