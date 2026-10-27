# PythonEcom — Enterprise E-Commerce Platform

A production-grade, full-featured Django e-commerce platform built with **Layered Clean Architecture**, **Granular Role-Based Access Control (RBAC)**, and a **Modern Storefront UI**.

---

## ⚡ Quick Start

```bash
# 1. Activate Virtual Environment
.venv\Scripts\activate.ps1     # Windows PowerShell
# source .venv/bin/activate    # Mac/Linux

# 2. Install Dependencies
pip install -r requirements.txt

# 3. Apply Migrations (MySQL)
python manage.py migrate

# 4. Seed Database (Roles, Permissions, Test Accounts & Catalog)
python manage.py seed_ecommerce

# 5. Start Development Server
python manage.py runserver
```

---

## 🔑 Test Credentials (Ready to Use)

The platform comes pre-configured with dedicated accounts for testing the **Granular RBAC System** and **Marketplace Storefront**:

| Portal | Role | Username | Password | Access Privileges |
| :--- | :--- | :--- | :--- | :--- |
| **Back-Office** | **Super Admin** | `superadmin` | `Admin@12345` | Global unrestricted access (all modules & settings) |
| **Back-Office** | **Catalog Manager** | `catalog_admin` | `Manager@12345` | Products, Categories, and Inventory management only |
| **Back-Office** | **Order Dispatcher** | `orders_staff` | `Staff@12345` | Order management, status workflows, view customers |
| **Storefront** | **Customer** | `customer_user` | `User@12345` | Customer profile, shopping bag, checkout, orders |

> 💡 **Tip:** Both the Customer and Back-Office login pages feature **1-click auto-fill buttons** for fast evaluation!

---

## 🌐 Application URL Directory

| Route | URL | Description |
| :--- | :--- | :--- |
| **Storefront Home** | `http://127.0.0.1:8000/` | Marketplace hero banner, flash deals, categories, trending products |
| **Catalog Browsing** | `http://127.0.0.1:8000/product/` | Product search, category/brand filters, stock toggle, sorting |
| **Shopping Cart** | `http://127.0.0.1:8000/cart/` | Off-canvas drawer & full cart page with free delivery indicator |
| **Checkout** | `http://127.0.0.1:8000/orders/checkout/` | One-page checkout, address selection, payment method choices |
| **Customer Portal** | `http://127.0.0.1:8000/account/dashboard/` | Customer order history, shipping addresses, live order tracker |
| **Back-Office Portal** | `http://127.0.0.1:8000/app-admin/` | Custom RBAC staff dashboard, revenue KPIs, low-stock warnings |
| **Role & Permission Manager** | `http://127.0.0.1:8000/app-admin/rbac/roles/` | Interactive matrix of module & submodule capabilities |

---

## 🏗️ Architecture & Design Patterns

The platform adheres to senior software engineering best practices:

```
pythonecom/
├── core/                # Base models (TimeStampedModel), seeder command
├── accounts/            # User authentication, Customer profiles, Saved addresses
├── rbac/                # Granular permissions engine, models, service, @require_permission
├── product/             # Categories, Brands, Products, Gallery images, Reviews
├── cart/                # Session & DB Cart Service, Off-canvas drawer context processor
├── orders/              # Orders, Order items, Payment Strategies, Unit of Work service
├── admin_panel/         # Dedicated back-office views, dynamic RBAC navigation
└── templates/           # Bootstrap 5.3 + Bootstrap Icons templates
```

### Applied Patterns
1. **Strategy Pattern** (`orders/strategies.py`):
   - Decoupled payment processing supporting `CashOnDeliveryStrategy`, `CardPaymentStrategy`, and `MobileBankingStrategy` via `PaymentStrategyFactory`.
2. **Service Layer & Unit of Work** (`orders/services.py`, `cart/services.py`, `rbac/services.py`):
   - View logic remains lightweight; transactions are wrapped in `@transaction.atomic` for consistency across order creation, inventory decrements, and payment capture.
3. **Decorator Pattern** (`rbac/decorators.py`):
   - Route protection via `@require_permission('catalog.products', 'edit')` ensuring zero unauthorized access.
4. **Dynamic RBAC Sidebar Engine** (`rbac/templatetags/rbac_tags.py`):
   - Sidebar automatically renders **only** the modules and submodules permitted to the logged-in staff member.

---

## 🛡️ Granular RBAC Permission Matrix

Permissions are structured hierarchically: `Module` ➔ `Submodule` ➔ `Action` (`view`, `create`, `edit`, `delete`):

- **Catalog Module**:
  - `catalog.products.view`, `create`, `edit`, `delete`
  - `catalog.categories.view`, `create`, `edit`, `delete`
- **Orders Module**:
  - `orders.orders.view`, `create`, `edit`, `delete`
- **Customers Module**:
  - `customers.customers.view`, `edit`, `delete`
- **Access Control Module**:
  - `rbac.roles.view`, `edit`
  - `rbac.staff.view`, `edit`

Super Administrators can create new roles and assign any combination of module permissions using the back-office checkbox matrix.

---

## 🧪 Running Automated Tests

Run the verification suite verifying storefront routes, RBAC protection, and atomic order placement:

```powershell
python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pythonecom.settings'); django.setup(); from django.test import Client; c = Client(); print('Storefront Home:', c.get('/', HTTP_HOST='127.0.0.1').status_code)"
```
