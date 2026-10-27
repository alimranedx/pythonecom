# PythonEcom Architecture & Operations Manual

This document provides technical documentation covering the system architecture, GoF design pattern implementations, the Granular Role-Based Access Control (RBAC) engine, and testing guides.

---

## 1. System Overview & Technology Stack

- **Framework**: Django 5.1.1 (Python 3.12)
- **Database**: MySQL 8.0+ / MariaDB via Custom MySQL Connector
- **Design Philosophy**: Layered Clean Architecture (Thin Controllers, Rich Services, Atomic Unit of Work)
- **Front-End**: Bootstrap 5.3.3, Bootstrap Icons 1.11.3, Google Plus Jakarta Sans typography

---

## 2. Design Patterns Implemented

### 2.1 Strategy Pattern (Payment Processing)
- **Location**: `orders/strategies.py`
- **Interface**: `PaymentStrategy` (Abstract Base Class)
- **Implementations**:
  - `CashOnDeliveryStrategy`: Sets payment status to `pending`, prepares order for courier dispatch.
  - `CardPaymentStrategy`: Simulates payment gateway authorization and sets status to `paid`.
  - `MobileBankingStrategy`: Integrates mobile financial services (bKash/Nagad/Rocket).
- **Factory**: `PaymentStrategyFactory.get_strategy(payment_method: str)` dynamically instantiates the correct handler without conditional branching in controllers.

### 2.2 Service Layer & Unit of Work (Transactional Integrity)
- **Location**: `orders/services.py`, `cart/services.py`, `rbac/services.py`
- **Pattern**: `OrderService.create_order_from_cart(...)` uses `@transaction.atomic`.
- **Guarantees**:
  1. Validates inventory availability across all cart items.
  2. Atomically decrements `product.stock`.
  3. Freezes historical snapshot of customer address and product prices into `Order` and `OrderItem`.
  4. Triggers payment strategy execution.
  5. Empties the customer's cart.
  *If any step fails, all database modifications rollback completely.*

### 2.3 Decorator Pattern (Granular RBAC Guard)
- **Location**: `rbac/decorators.py`
- **Usage**: `@require_permission('catalog.products', 'edit')`
- **Workflow**:
  1. Checks if `request.user.is_authenticated` and `is_staff`.
  2. Short-circuits for `is_superuser` (unrestricted access).
  3. Evaluates granted permissions via `RBACService.user_has_permission(...)`.
  4. Raises `PermissionDenied` (HTTP 403) if unauthorized.

### 2.4 Dynamic Menu Generator (Flyweight / Cache Pattern)
- **Location**: `rbac/services.py` (`get_user_allowed_menu`), `rbac/templatetags/rbac_tags.py`
- **Behavior**: The staff sidebar is not hardcoded. It dynamically renders only the specific modules and submodules for which the logged-in user holds `can_view` permissions, caching the permission set on `request.user` per request lifecycle.

---

## 3. Seeded Accounts & Credentials

| Role | Username | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **Super Admin** | `superadmin` | `Admin@12345` | Global unrestricted access across all back-office modules and configurations. |
| **Catalog Manager** | `catalog_admin` | `Manager@12345` | Full Catalog and Inventory access (Products, Categories). Denied access to Orders & Roles. |
| **Order Dispatcher** | `orders_staff` | `Staff@12345` | View & update customer orders, fulfillment workflows. Denied access to Catalog creation and Roles. |
| **Customer** | `customer_user` | `User@12345` | Regular marketplace shopper with saved address and order history. |

---

## 4. Operational Endpoints

### Storefront Portal
- `GET /` — Marketplace homepage with hero slider, flash deals, categories, and trending products.
- `GET /product/` — Product catalog with keyword search, brand/category filters, and price sorting.
- `GET /product/<id>/` — Product showcase with stock status, ratings, tabs, and related products.
- `POST /cart/add/<id>/` — Add item to cart (supports both AJAX JSON and standard HTTP redirect).
- `GET /cart/` — Shopping cart overview with shipping threshold progress bar.
- `GET|POST /orders/checkout/` — One-page checkout with live address validation and payment method selection.
- `GET /orders/confirmation/<order_number>/` — Order receipt with live visual tracker.
- `GET /account/dashboard/` — Customer dashboard, order history, and saved addresses.
- `GET|POST /account/profile/edit/` — Profile update with avatar photo upload.
- `GET|POST /account/password-change/` — Secure password update form.
- `GET /account/addresses/` — Address book management (view, add, edit, delete, default).
- `GET /account/wishlist/` — Wishlist items management with 1-click move to cart.
- `GET /account/wishlist/toggle/<product_id>/` — AJAX wishlist toggle endpoint.
- `POST /product/<product_id>/review/` — Customer star rating and review submission.

### Back-Office Admin Portal
- `GET|POST /app-admin/login/` — Staff sign-in page with 1-click test credential auto-fill buttons.
- `GET /app-admin/` — Dashboard KPIs (Settled Revenue, Total Orders, Active Catalog, Low Stock alerts).
- `GET /app-admin/products/` — Product inventory management with search and action buttons.
- `GET|POST /app-admin/products/create/` — Add new product with primary image + multiple gallery photos.
- `GET|POST /app-admin/products/<id>/edit/` — Edit product details, upload additional photos, manage existing gallery.
- `GET /app-admin/products/images/<id>/delete/` — Delete individual gallery image.
- `GET /app-admin/categories/` — Category taxonomy management.
- `GET /app-admin/orders/` — Order fulfillment queue filtered by status (`Pending`, `Processing`, `Shipped`, etc.).
- `GET|POST /app-admin/orders/<id>/` — Manage order status and payment verification.
- `GET /app-admin/customers/` — View registered customer list and order counts.
- `GET /app-admin/rbac/roles/` — Access Control role list and system role indicators.
- `GET|POST /app-admin/rbac/roles/create/` — Create custom administrative role.
- `GET|POST /app-admin/rbac/roles/<id>/edit/` — Interactive module/submodule permission checkbox matrix.
- `GET|POST /app-admin/rbac/staff/` — Staff user role assignment manager.

---

## 5. Security Architecture & Threat Modeling

### 5.1 Remote Code Execution (RCE) & Web Shell Defense
- **Command Whitelisting**: No subprocess or shell invocation utilities exist in application code.
- **File Upload Hardening**:
  - `core/validators.validate_image_file` implements three checks:
    1. Size validation: Rejects payloads exceeding 5 MB.
    2. Whitelist validation: Accepts only `['.jpg', '.jpeg', '.png', '.webp']`.
    3. Bytecode validation: Invokes Pillow's `Image.open(file).verify()` to inspect low-level headers and identify fake polyglot scripts.
  - `core/validators.get_safe_upload_path` generates non-deterministic UUID4 filenames, discarding user-supplied paths to eliminate path traversal (`../../`).

### 5.2 Denial of Service (DoS) Protections
- **Payload Constraints**: Maximum request body and file upload memory bounded at 5MB via `DATA_UPLOAD_MAX_MEMORY_SIZE` and `FILE_UPLOAD_MAX_MEMORY_SIZE`. Maximum form fields bounded to 1,000 via `DATA_UPLOAD_MAX_NUMBER_FIELDS`.
- **Query Complexity Protection**: Catalog search query parameters are truncated to 100 characters, preventing heavy regex/wildcard DB degradation.
- **Cart & Order Overflow Clamping**: Cart quantities are clamped to `max(1, min(qty, 100))` to prevent arithmetic overflow and negative stock exploitation.

### 5.3 Cross-Site Scripting (XSS) & Header Policies
- **Template Context Auto-Escaping**: Untrusted customer data is auto-escaped at the Django rendering layer. No `|safe` tags exist on user-generated inputs.
- **SVG Blocking**: Vector images are excluded from file uploads to eliminate SVG-embedded script execution.
- **HTTP Security Headers**:
  - `X_FRAME_OPTIONS = 'DENY'` (blocks framing/clickjacking)
  - `SECURE_CONTENT_TYPE_NOSNIFF = True` (prevents MIME-type confusion attacks)
  - `SECURE_BROWSER_XSS_FILTER = True` (activates browser XSS filters)
  - `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = 'Lax'` (mitigates session theft)

### 5.4 Open Redirect & IDOR Protection
- **Redirect Target Validation**: `core/validators.get_safe_redirect_url` verifies `next` query strings and `HTTP_REFERER` headers against `url_has_allowed_host_and_scheme(allowed_hosts={request.get_host()})`. Malicious external domains fall back to safe internal endpoints.
- **Direct Object Reference Scoping**: Order receipts (`order_confirmation`), address edits, and wishlist mutations strictly compare object ownership against `request.user` or verify active checkout session keys. Unauthorized attempts raise `PermissionDenied` (HTTP 403).
