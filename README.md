# PythonEcom — Enterprise E-Commerce Platform

A production-grade, full-featured Django e-commerce platform built with **Layered Clean Architecture**, **Granular Role-Based Access Control (RBAC)**, and a **Modern Storefront UI** benchmarked against **Chaldal.com** (Bangladesh market standard).

> 📖 **Complete Software Operations Manual:**  
> For full documentation of all storefront and back-office features (delivery time slots, promotional coupon engine, visual 4-stage order tracking, adjustable multi-criteria order filters, floating bag launcher, and staff RBAC), see the [Software Features & Operations Guide](docs/SOFTWARE_FEATURES_GUIDE.md).

---

## 🚀 Quick Start & Setup Guide

### 1. Prerequisites
- **Python**: 3.12+ (tested on Python 3.12)
- **Database**: MySQL 8.0+ / MariaDB (e.g., via Laragon, XAMPP, or native MySQL service)
- **Git**

---

### 2. Initial Setup (First Time Clone)

#### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd pythonecom
```

#### Step 2: Database Preparation
1. Ensure your local MySQL server is running (e.g., click **Start All** in **Laragon**, or start the **MySQL** module in **XAMPP Control Panel**).
2. Create the project database:
   ```sql
   CREATE DATABASE IF NOT EXISTS pythonecom_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
   > **Note:** The default connection settings in `pythonecom/settings.py` point to `localhost:3306`, database `pythonecom_db`, user `root`, and an empty password (`''`). If your local MySQL setup requires a password or different host/port, update `DATABASES` in `pythonecom/settings.py`.

#### Step 3: Create & Activate Virtual Environment
- **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
- **Windows (CMD):**
  ```cmd
  python -m venv .venv
  .venv\Scripts\activate.bat
  ```
- **macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

#### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 5: Apply Database Migrations
```bash
python manage.py migrate
```

#### Step 6: Seed Complete Database & Catalog
Populates complete marketplace data: store & brand settings, bilingual announcements, 24 categories, 38 brands, 72 products with specifications and gallery images, customer reviews, delivery slots, promo coupons, sample orders, and RBAC accounts:
```bash
python manage.py seed_ecommerce
```

> **Tip:** To capture your current database state into the version-controlled seed fixture at any time, run:
> ```bash
> python manage.py seed_ecommerce --export
> ```

#### Step 7: Run Development Server
```bash
python manage.py runserver
```
The application will be live at `http://127.0.0.1:8000/`.

---

### 🔄 Post-`git pull` Workflow

Whenever you pull updates from the repository, run this quick sequence to keep your environment and database synchronized:

```powershell
# 1. Pull the latest code
git pull

# 2. Activate virtual environment (if not already active)
.\.venv\Scripts\Activate.ps1

# 3. Synchronize any newly added dependencies
pip install -r requirements.txt

# 4. Apply new database migrations
python manage.py migrate

# 5. Synchronize RBAC permissions & seed data (safe to re-run; uses update_or_create)
python manage.py seed_ecommerce

# 6. Start the server
python manage.py runserver
```

---

## 🔐 Test Credentials & Access Matrix

After running `python manage.py seed_ecommerce`, the following pre-configured accounts are available:

| Portal | Role | Username | Password | Scope & Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| **Back-Office** | **Super Admin** | `superadmin` | `Admin@12345` | Global unrestricted access (all modules & settings) |
| **Back-Office** | **Catalog Manager** | `catalog_admin` | `Manager@12345` | Products, Categories, and Inventory management only |
| **Back-Office** | **Order Dispatcher** | `orders_staff` | `Staff@12345` | Order management, status workflows, view customers |
| **Storefront** | **Customer** | `customer_user` | `User@12345` | Customer profile, shopping bag, checkout, orders |
| **Native Admin** | **Superuser** | `superadmin` | `Admin@12345` | Standard Django admin interface (`/admin/`) |

> **Note:** For security, change these credentials before deploying to a production environment.

---

## 🌐 Application URL Directory

| Route | URL | Description |
| :--- | :--- | :--- |
| **Storefront Home** | `http://127.0.0.1:8000/` | Marketplace hero banner, flash deals, categories, trending products |
| **Catalog Browsing** | `http://127.0.0.1:8000/product/` | Product search, category/brand filters, stock toggle, sorting |
| **Shopping Cart** | `http://127.0.0.1:8000/cart/` | Off-canvas drawer & full cart page with free delivery indicator |
| **Checkout** | `http://127.0.0.1:8000/orders/checkout/` | One-page checkout, address selection, payment method choices |
| **Customer Portal** | `http://127.0.0.1:8000/account/dashboard/` | Customer order history, shipping addresses, live order tracker |
| **Customer Profile** | `http://127.0.0.1:8000/account/profile/edit/` | Avatar upload, personal info, phone number |
| **Customer Wishlist** | `http://127.0.0.1:8000/account/wishlist/` | Saved items, live heart badge, move-to-cart in 1-click |
| **Address Book** | `http://127.0.0.1:8000/account/addresses/` | Manage shipping destinations with default indicator |
| **Back-Office Portal** | `http://127.0.0.1:8000/app-admin/` | Custom RBAC staff dashboard, revenue KPIs, low-stock warnings |
| **Store & Brand Settings** | `http://127.0.0.1:8000/app-admin/settings/` | Dynamic store identity, announcements, contacts, social links, footer notices |
| **Role & Permission Manager** | `http://127.0.0.1:8000/app-admin/rbac/roles/` | Interactive matrix of module & submodule capabilities |
| **Django Admin** | `http://127.0.0.1:8000/admin/` | Default Django superuser admin portal |

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

## ✨ Advanced Production E-Commerce Features

- **Dynamic Store & Brand Settings Management (`/app-admin/settings/`)**:
  - Full RBAC-secured back-office management for marketplace brand name, logo, favicon, top announcement bar, 24/7 care hours, support phone/email, social media handles, payment badges, and copyright notices.
  - Changes reflect globally in real time across all customer storefront headers, meta tags, and footers.
- **Bilingual English & Bangla Storefront Localization**:
  - 1-click language switching between **English (EN)** and **বাংলা (BN)** on the customer storefront with cookie/session persistence.
  - Full localization covering navigation, announcement banner, search placeholders, filter badges, product details, delivery slots, cart, checkout, and footer.
  - Native Bengali numeral conversions (৳ prices, stock counts, rating values).
  - Administrative back-office strictly isolated in English for enterprise standardization.
- **Storefront Dark / Light Mode Theme**:
  - Customer storefront provides an instant **Dark / Light** theme toggle with persistent preferences in local storage.
  - High-contrast, accessibility-tested dark color palette.
  - Administrative back-office strictly isolated in professional Light theme.
- **Full Mobile Responsive Storefront**:
  - Native mobile app experience with bottom navigation bar (Home, Catalog, Wishlist, Bag with counter, Account).
  - Left off-canvas drawer for category browsing and language selection.
  - Dedicated mobile filter drawer for catalog browsing.
- **Back-Office Searchable Dropdowns with Real-Time Filtering**:
  - Custom searchable select UI for Brand and Category selection in product creation/editing.
  - Clean "Please Select" placeholder replacing raw `---------`.
- **Scrollable Admin Sidebar & Dynamic Navigation Tabs**:
  - Fixed-header admin sidebar with custom slim scrollbar preventing navigation links from being cut off on any screen size.
  - Dynamic active underline indicators on admin settings tabs that move smoothly across tabs with URL hash state preservation.
- **Complete Database Snapshot Seeder**:
  - `python manage.py seed_ecommerce` restores all 542 records (Settings, 24 Categories, 38 Brands, 72 Products, 246 Gallery Images, 15 Reviews, 5 Delivery Slots, 2 Coupons, 3 Orders, RBAC Roles, and Test Users).
  - `python manage.py seed_ecommerce --export` captures live database modifications into `core/fixtures/initial_seed_data.json`.
- **Multiple Image Upload**: Back-office product manager allows uploading a primary thumbnail plus multiple gallery photos simultaneously with individual deletion controls.
- **Circle Mirror Zoom**: Product detail page features a circular magnifying glass loupe (Amazon/Shopify-style) that tracks the cursor with 2.4x high-resolution optical zoom.
- **Interactive Image Thumbnails**: Hovering or clicking any gallery angle instantaneously switches the main showcase image and syncs the circle mirror zoom background.
- **User Wishlist Engine**:
  - Heart icon button on every product card (`Home`, `Catalog`, `Product Detail`) with instant AJAX toggle.
  - Live navbar heart counter badge (`#navWishlistBadge`).
  - Dedicated wishlist management page with 1-click **Move to Cart** action.
- **User Profile & Address Book**:
  - Avatar image upload, personal information editing, and password change.
  - Multi-address book management (Add, Edit, Delete, Primary Default Shipping).
- **Customer Product Reviews**: Star ratings (1-5) and feedback submission.

---

## 🔒 Enterprise Security & Vulnerability Defense Matrix

The platform underwent a full security audit and implements defense-in-depth mitigations:

| Attack Vector | Vulnerability Classification | Mitigation & Defense Architecture |
| :--- | :--- | :--- |
| **Shell Script / RCE** | Remote Code Execution | **Zero OS Execution:** No `os.system`, `subprocess`, `popen`, `eval()`, or `exec()` in codebase.<br>**Dual-Layer Upload Validation (`core/validators.py`):** Whitelists only `.jpg`, `.jpeg`, `.png`, `.webp`. Rejects executable extensions (`.php`, `.sh`, `.exe`). Deep Pillow bytecode verification (`img.verify()`) catches polyglot files disguised as images. |
| **Denial of Service (DoS)** | Resource Exhaustion | **Memory Caps (`settings.py`):** `DATA_UPLOAD_MAX_MEMORY_SIZE = 5MB`, `FILE_UPLOAD_MAX_MEMORY_SIZE = 5MB`, `DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000`.<br>**Bounded User Inputs:** Search queries capped at 100 chars, cart quantities strictly clamped to `1 <= qty <= 100`, product reviews capped at 1,000 chars. |
| **JavaScript Injection (XSS)** | Cross-Site Scripting | **Auto-Escaped Templates:** All dynamic variables contextually escaped by Django template engine. Zero unescaped `\|safe` filters on customer-supplied input.<br>**SVG Filtering:** SVG uploads rejected to prevent stored SVG-script injection.<br>**Security Headers:** `SECURE_CONTENT_TYPE_NOSNIFF = True`, `SECURE_BROWSER_XSS_FILTER = True`. |
| **Open Redirect** | CWE-601 | **Safe URL Resolution (`core/validators.py`):** All `next` login parameters and `HTTP_REFERER` headers validated against `url_has_allowed_host_and_scheme()` before issuing redirects. |
| **IDOR** | Insecure Direct Object Reference | **Scoped Receipts & Profiles:** Customer orders, address records, and wishlist queries strictly scoped to `user=request.user`. Order confirmation receipts require matching ownership or active checkout session; unauthorized attempts trigger `PermissionDenied` (HTTP 403). |
| **Clickjacking & CSRF** | UI Redressing / Session Hijacking | **Iframe Defense:** `X_FRAME_OPTIONS = 'DENY'` headers.<br>**CSRF Enforcement:** All POST mutations protected by CSRF tokens with `SameSite='Lax'` and `HttpOnly=True` session cookies. |

---

## 🧪 Running Automated Tests & Sanity Checks

The project includes an enterprise test suite with **58 automated unit and integration tests** verifying bilingual translation integrity, dark/light theme isolation, mobile responsive elements, RBAC security guards, order payment state machines, site settings singleton behavior, and database seeder loading:

```bash
# Run the complete test suite (58 tests)
python manage.py test

# Or run tests for specific apps
python manage.py test core
python manage.py test orders
python manage.py test rbac
```
