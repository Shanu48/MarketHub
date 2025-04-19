# 🛒 MarketHub2 - Project To-Do List

This document outlines the pending tasks and features for the MarketHub2 application. It is organized by UI improvements and functionality for each user role: **Customer**, **Supplier**, and **Warehouse**.

---

## ✅ General UI Fixes

- [ ] Fix styling for existing pages.
- [ ] Move the **Logout** button to the right, make it smaller, and remove the highlight.
- [ ] Clicking on the **logo** should open the **profile page**.
- [ ] Replace the **Profile** button with a **Dashboard/Home** button.
- [ ] Ensure the **logo is visible** on all pages.

---

## 🧑‍💼 Customer Dashboard

- [ ] Enable the **"Add to Cart"** option for products.

---

## 🕒 Product Expiry Feature (Important)

- [ ] If **today is 3 days before expiry**, the product should be:
  - [ ] **Deleted**
  - [ ] **Supplier notified** on their dashboard

---

## 🧠 Business Logic Clarification

If we show that products are first sent to a warehouse before reaching the customer, it might imply the need for a **Warehouse Manager Interface**.

**Solution**:  
- Show that the **supplier directly ships the product**.
- Warehouses are just provided by the platform for storage — not as a separate management layer.

---

## 🏢 Warehouse

- [ ] Create the **Warehouse page**.
- [ ] Display a table of all products a supplier has stored across various warehouses.

---

## 🛒 Cart Page

- [ ] Display **added products** in the cart.
- [ ] Allow users to **change quantity** of products.
- [ ] On clicking **"Proceed to Checkout"**, open the **Payment Success** page.

---

## 💳 Payment Success Page

- [ ] Display the **final amount** of the order.
- [ ] Collect customer details:
  - Name
  - Address
  - Payment method
- [ ] Show a **"Payment Complete"** confirmation screen.

---

## 📦 Orders Page

- [ ] Display **all past orders** placed by the customer.
- [ ] Include:
  - Order ID
  - Final amount
  - **Track Order** button
- [ ] On clicking **Track**, show:
  - Link to shipping website
  - Shipping ID
  - Shipping status (`Processing`, `Shipped`, `Delivered`)

---

## 📤 Supplier Dashboard

- [ ] Enable suppliers to **add products** to the warehouse:
  - Product name
  - Image
  - Price
  - Discount
  - Expiry date
  - Warehouse location
- [ ] Show:
  - Total items sent to warehouses
  - Items sent to customers
  - Expired/wasted items

---

## 🚚 Supplier Transport Tab

- [ ] Show delivery status of goods sent to warehouses.

---

## 🏬 Warehouse Inventory

- [ ] Display available quantity of each product in every warehouse (per supplier).

---

## 📦 Manage Orders (Supplier Side)

- [ ] Once a customer places an order, show it in **Manage Orders** if it belongs to the supplier.
- [ ] Allow supplier to **confirm** their part of the order.
- [ ] Since an order may include items from multiple suppliers/warehouses:
  - When all relevant suppliers **confirm**, mark it as **"Shipped"**
  - Update quantities accordingly
  - Update **customer's Transport tab** with `Shipped` status

---

