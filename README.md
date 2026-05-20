# 🛍️ Kels Dropshipping MVP

A high-performance, monolithic **Django dropshipping storefront MVP** meticulously optimized for the **Philippine market**. This storefront is specifically tailored for high-speed, bandwidth-friendly mobile rendering on local carriers (such as Globe, TM, Smart, and TNT) to maximize customer conversion.

---

## ✨ Project Essence & Features

*   **Mobile-First Design:** Optimized for low latency, smooth scrollbars, clean touch targets, and lightweight layout grids designed for mobile viewports.
*   **Premium Brand Aesthetic:** Uses a sleek modern typography design (`Inter` + `Outfit` Google Fonts), slate color schemes, and elegant glassmorphism headers.
*   **High-Conversion COD Checkout:** Native Cash on Delivery (COD) order capture form validating Philippine mobile numbers (e.g., `09XXXXXXXXX`).
*   **High-Contrast Action Button:** Primary Call-to-Action ("BUY NOW - CASH ON DELIVERY") styled with a dedicated accent color (`#FF5A00`) and a sticky bottom bar on mobile.
*   **Philippine Market Localization:**
    *   Time Zone set to `Asia/Manila`
    *   Language Code set to `en-ph`
    *   Currency formatted with `₱` (PHP)
*   **Dynamic Landing Pages:** Supports rich product listings, promotional video players, benefit lists, dynamic reviews, and FAQs.

---

## 🛠️ Tech Stack

*   **Backend Framework:** Python 3.x / Django 6.0+ (Monolithic Architecture)
*   **Database:** SQLite (local development and testing)
*   **Styling & UI:** Tailwind CSS (Premium Redesign integrated via CDN, using customized brand fonts and colors)

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Ensure you have **Python 3.10+** installed on your system.

### 2. Set Up the Virtual Environment
Activate the pre-configured virtual environment:

**On Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
.\venv\Scripts\activate.bat
```

**On macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. Run Database Migrations
Apply all migrations to synchronize the database schema:
```bash
python manage.py migrate
```

### 4. Run the Development Server
Start the local Django server:
```bash
python manage.py runserver
```
Visit the storefront locally at `http://127.0.0.1:8000/`.

### 5. Running the Test Suite
Ensure that all features and checkout validations are working correctly by running tests:
```bash
python manage.py test
```

---

## 🗄️ Database Schema & Active Models

### 1. `Product`
The core catalog item holding listing details:
*   `title`: Product name.
*   `slug`: Unique URL-friendly slug.
*   `description`: Rich text/HTML description.
*   `price`: Selling price in Philippine Pesos (₱).
*   `compare_at_price`: Original retail price to calculate discounts.
*   `cj_product_id`: CJ Dropshipping product identifier.
*   `video_url`: Promotional MP4/YouTube/TikTok video link.
*   `features_list`: Dynamic list of high-impact features (stored in JSON).
*   `is_active`: Toggle for storefront visibility.
*   `sku`: Stock Keeping Unit.

### 2. `ProductImage`
Carousel images supporting the gallery on the landing page:
*   `product`: Foreign key to parent product.
*   `image`: Local file upload for media assets.
*   `image_url`: External URL for high-performance content delivery.
*   `order`: Carousel sorting priority.

### 3. `Order`
Customer conversion leads captured via the COD checkout form:
*   `product`: Reference to the ordered product.
*   `full_name`: Customer recipient name.
*   `phone_number`: Validated Smart/Globe mobile number format.
*   `shipping_address`: Full delivery instructions.

---

## 🗺️ Roadmap & Next Steps

1.  **CJ Dropshipping API Integration:** Auto-sync product details, SKUs, inventory, and automate order forwarding.
2.  **Local Payment Gateway Integration:** Integrate local aggregators (such as PayMongo or Xendit) to support credit/debit card, GCash, Maya, and GrabPay payments alongside the native COD model.
