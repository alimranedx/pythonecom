# PythonEcom — Production Software Features & Operations Guide

> **Enterprise E-Commerce Platform Benchmarked Against Chaldal.com (Bangladesh Market Standard)**  
> Built with Django 5, Bootstrap 5.3, Clean Architecture, and Granular Role-Based Access Control (RBAC).

---

## 📋 Table of Contents
1. [Platform Overview & Key Innovations](#1-platform-overview--key-innovations)
2. [Customer & Storefront Guide (How to Shop)](#2-customer--storefront-guide-how-to-shop)
   - [Product Catalog & Measurement Units](#product-catalog--measurement-units)
   - [Instant Cart Steppers & Floating Bag](#instant-cart-steppers--floating-bag)
   - [Free Delivery Progress Indicator](#free-delivery-progress-indicator)
   - [Delivery Slot Scheduling (Today / Tomorrow Windows)](#delivery-slot-scheduling)
   - [Delivery Zone Selection & Dynamic Fees](#delivery-zone-selection--dynamic-fees)
   - [Promo Codes & Coupon Vouchers](#promo-codes--coupon-vouchers)
   - [Payment Methods (COD, bKash/Nagad MFS, Card)](#payment-methods)
   - [Visual 4-Stage Order Tracking Timeline](#visual-4-stage-order-tracking-timeline)
3. [Administrator & Back-Office Guide (How to Manage)](#3-administrator--back-office-guide-how-to-manage)
   - [Role-Based Access Control (RBAC) & Staff Security](#role-based-access-control-rbac--staff-security)
   - [Orders Management & Adjustable Multi-Filter Panel](#orders-management--adjustable-multi-filter-panel)
   - [Interactive Dual-Calendar Date Range Picker](#interactive-dual-calendar-date-range-picker)
   - [CSV Export & Custom Rows-Per-Page Limits](#csv-export--custom-rows-per-page-limits)
   - [Delivery Slots & Logistics Setup](#delivery-slots--logistics-setup)
   - [Promotional Coupons & Campaign Engine](#promotional-coupons--campaign-engine)
   - [Catalog Management (Products, Units, Categories, Brands)](#catalog-management)
   - [Customer Reviews Moderation](#customer-reviews-moderation)
   - [Customer 360 Profiles & Account Moderation](#customer-360-profiles--account-moderation)
4. [Bangladesh Logistics & Currency Standards](#4-bangladesh-logistics--currency-standards)

---

## 1. Platform Overview & Key Innovations

PythonEcom is an enterprise-grade e-commerce platform engineered specifically to meet the high customer expectations and operational demands of the Bangladeshi e-commerce landscape, adopting the signature UX patterns pioneered by **Chaldal.com**:

* **Bangladeshi Taka (`৳` / BDT) Standardization**: All storefront and back-office prices are rendered in authentic currency notation.
* **Granular Measurement Units**: Products feature explicit unit sizes (`1 kg`, `500 gm`, `1 ltr`, `12 pcs`, `1 pack`, `1 pc`).
* **Instant Card Additions**: Zero-navigation cart additions with an offcanvas drawer and sticky floating shopping bag launcher.
* **Scheduled Time Slots**: Customers select delivery windows (e.g. *Morning 8-11 AM*, *Evening 6:30-9:30 PM*, *Express 60-min*).
* **Delivery Zone Fees**: Hyperlocal shipping rates (*Inside Dhaka: ৳49 / FREE above ৳500*, *Outside Dhaka: ৳99*).
* **Full Coupon Engine**: Flat and percentage discount vouchers with min-order thresholds and instant AJAX deduction.
* **Visual Order Lifecycle**: Real-time 4-stage tracking timeline (*Placed ➔ Packing ➔ Out for Delivery ➔ Delivered*).
* **Self-Contained RBAC**: Dynamic administrative sidebar with strict role permissions and complete session role isolation.

---

## 2. Customer & Storefront Guide (How to Shop)

### Product Catalog & Measurement Units
* Customers can browse items by **Categories** or **Brands**, or search using the live search bar.
* Every product card displays:
  * Effective price (with strike-through regular price if discounted).
  * Discount percentage badge (e.g. `-15% OFF`).
  * Packaging measurement unit (e.g. `1 kg`, `500 gm`, `1 ltr`).
  * In-stock or out-of-stock badge.

### Instant Cart Steppers & Floating Bag
* **Adding to Cart**: Click the **"Add to Cart"** / **"Add to Bag"** button on any product card or detail page.
* **Zero Reload**: Items are added via background AJAX without reloading or scrolling the page.
* **Floating Shopping Bag**: A sticky black-and-gold widget (`3 Items | ৳450`) stays docked at the bottom-right of the screen. Clicking it opens the full cart drawer instantly.
* **Drawer Quantity Stepper**: Inside the cart drawer, click `+` or `-` to adjust quantities in real time.

### Free Delivery Progress Indicator
* Inside the cart drawer, cart page, and checkout summary, a live progress bar informs customers:
  $$\text{"Add ৳ 120 more for FREE Delivery!"}$$
* When the subtotal reaches **৳ 500**, the bar turns green:
  $$\text{"🎉 You unlocked FREE Delivery!"}$$

### Delivery Slot Scheduling
During checkout (Step 2), customers schedule their delivery:
1. **Choose Delivery Date**: Click a date pill:
   * **Today** (e.g., *Thu, 29 Oct*)
   * **Tomorrow** (e.g., *Fri, 30 Oct*)
   * **Day After Tomorrow** (e.g., *Saturday*)
2. **Choose Delivery Time Slot**: Select a convenient time window:
   * **Morning Slot**: `08:00 AM – 11:00 AM`
   * **Noon Slot**: `11:30 AM – 02:30 PM`
   * **Afternoon Slot**: `03:00 PM – 06:00 PM`
   * **Evening Slot**: `06:30 PM – 09:30 PM`
   * **⚡ Express Delivery**: Dispatched within 60 minutes (+৳30 surcharge).

### Delivery Zone Selection & Dynamic Fees
In Checkout (Step 1), customers pick their delivery zone:
* **Inside Dhaka**: Gulshan, Banani, Dhanmondi, Uttara, Mirpur, Badda, Motijheel, Mohammadpur. Standard delivery fee is **৳49** (**FREE** for orders ৳500+).
* **Outside Dhaka / Nationwide**: Courier delivery to all 64 districts at a flat fee of **৳99**.

### Promo Codes & Coupon Vouchers
* Customers can enter promotional codes in the cart drawer or in Checkout:
  * `WELCOME50` ➔ ৳50 Flat OFF on orders above ৳300.
  * `CHALDAL10` ➔ 10% OFF on orders above ৳400 (up to ৳150 savings).
* The discount is immediately deducted from the grand total. Click `×` to remove an applied coupon.

### Payment Methods
Customers can select their preferred payment method:
1. **Cash On Delivery (COD)**: Pay cash to the delivery rider upon delivery.
2. **Mobile Banking (MFS)**: Instant settlement with bKash, Nagad, or Rocket.
3. **Credit / Debit Card**: Visa, Mastercard, or American Express.

### Visual 4-Stage Order Tracking Timeline
After placing an order (or via **My Orders** in customer account), customers see a visual tracking stepper:
1. `Placed`: Order received and confirmed.
2. `Packing`: Order packed at localized fulfillment center.
3. `On the Way`: Rider dispatched with package.
4. `Delivered`: Successfully handed over and payment settled.

---

## 3. Administrator & Back-Office Guide (How to Manage)

### Role-Based Access Control (RBAC) & Staff Security
* **Route**: `/app-admin/login/`
* **Role Types**:
  * **Super Administrator**: Complete system access, staff account creation, role editing.
  * **Custom Roles**: Tailored permissions per module (`Catalog`, `Orders`, `Customers`, `Reviews`).
* **Session Isolation**: Staff sessions are strictly isolated from customer storefront sessions; browser background requests (e.g. `/favicon.ico`) preserve staff authentication.

### Orders Management & Adjustable Multi-Filter Panel
* **Route**: `/app-admin/orders/`
* **Adjustable Filter Panel**:
  * Can be expanded or collapsed via **"Adjust Filters"** / **"Collapse Filters"**.
  * Shows an active badge: `X Active Filters`.
* **Multi-Criteria Filter Fields**:
  * **Date Range**: Interactive preset-based and custom datetime range.
  * **Trans. ID / Order Ref**: Search order numbers (e.g. `ORD-3FE9...`).
  * **Customer / Merchant**: Search across Name, Email, Phone, and Username.
  * **Fulfillment Status**: Filter by `Pending Approval`, `Processing`, `Shipped`, `Delivered`, `Cancelled`.
  * **Payment Status**: Filter by `Pending`, `Paid`, `Failed`, `Refunded`.
  * **Sale Type / Payment Method**: Filter by `COD`, `Mobile Banking`, `Card`.
  * **Amount Range**: Filter by `Min ৳` and `Max ৳`.

### Interactive Dual-Calendar Date Range Picker
Clicking the **Date Range** input reveals the specialized picker:
* **7 Quick Presets**: `Today`, `Yesterday`, `Last 7 Days`, `Last 30 Days`, `This Month`, `Last Month`, `Custom Range`.
* **Dual Month View**: Side-by-side calendars for start and end months with `<` and `>` month navigation.
* **Exact Time Spinners**: `HH : MM : SS` dropdown selectors for start and end times.
* **Apply / Cancel / Clear**: Formats as `YYYY/MM/DD HH:mm:ss - YYYY/MM/DD HH:mm:ss`.

### CSV Export & Custom Rows-Per-Page Limits
* **CSV Export**: Click the purple **"Export Report History (CSV)"** button to stream an instant UTF-8 CSV containing all matching filtered orders.
* **Page Limit Selectors**: Change `Show [ 10 v ] per page` (options: `5`, `10`, `20`, `50`, `100`).
* **Filter Retention**: Navigating to `Next ›`, `‹ Prev`, `First`, `Last`, or changing page sizes preserves 100% of selected filter inputs in the URL query string.

### Delivery Slots & Logistics Setup
* **Route**: `/app-admin/orders/delivery-slots/`
* **Capabilities**:
  * View active and inactive delivery windows.
  * Toggle slot status (*Activate / Deactivate*) with one click.
  * Set daily order caps (e.g., max 50 orders per slot).
  * Configure express surcharges (+৳30).

### Promotional Coupons & Campaign Engine
* **Route**: `/app-admin/orders/coupons/`
* **Capabilities**:
  * Create new campaigns: Code, Discount Type (`percent` or `fixed`), Value, Minimum Order Amount, Maximum Discount Cap, and Validity Days.
  * Monitor real-time redemption counts against total allowed limits.
  * One-click toggle between *Active* and *Inactive*.
  * Delete expired or cancelled promotional vouchers.

### Catalog Management
* **Products** (`/app-admin/products/`):
  * Create & edit products with packaging unit (`unit`), pricing, discount price, stock count, and active status.
  * Upload main featured image and multiple gallery angle photos.
* **Categories** (`/app-admin/categories/`):
  * Manage hierarchical parent-child category trees (e.g., *Fresh Produce ➔ Fruits*).
* **Brands** (`/app-admin/brands/`):
  * Manage partner brands with logo uploads and custom slugs.

### Customer Reviews Moderation
* **Route**: `/app-admin/reviews/`
* Filter customer reviews by star rating (1 to 5 stars) and delete abusive/inappropriate reviews.

### Customer 360 Profiles & Account Moderation
* **Route**: `/app-admin/customers/`
* View registered customer profiles, lifetime order count, total revenue settled, and toggle active/banned status.

---

## 4. Bangladesh Logistics & Currency Standards

| Standard | Implementation in PythonEcom |
| :--- | :--- |
| **Currency** | Bangladeshi Taka (`৳` / BDT) |
| **Inside Dhaka Delivery** | Flat ৳49 fee; **FREE Delivery** automatically unlocked at ৳500+ subtotal |
| **Outside Dhaka Delivery** | Flat ৳99 courier delivery nationwide across all 64 districts |
| **Express Fulfillment** | 60-Minute Rapid Dispatch slot (+৳30 express surcharge) |
| **Mobile Banking** | bKash, Nagad, and Rocket support alongside COD and Cards |
| **Packaging Units** | Explicit customer units: `1 kg`, `500 gm`, `1 ltr`, `12 pcs`, `1 pack`, `1 pc` |
