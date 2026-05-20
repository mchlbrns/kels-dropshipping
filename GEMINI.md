# GEMINI.md — Project Memory & Context

Welcome! This file acts as our **long-term memory** for the `kels-dropshipping` project. It contains the essential architecture, tech stack, data models, design patterns, and roadmap for the application. 

Every time a new session starts, **always read this file first** to ensure complete alignment with our premium design standards, local Philippine localization, and specific logistical constraints.

---

## 🌟 Project Essence
A high-performance, monolithic **Django dropshipping MVP** meticulously optimized for the **Philippine market** (specifically tailored for high-speed, bandwidth-friendly mobile rendering on local carriers like Globe, TM, Smart, and TNT).

---

## 🛠️ Current Tech Stack
*   **Backend & Framework:** Python 3.x / Django 6.0+ (monolithic design)
*   **Database:** SQLite (local development and testing)
*   **Styling & UI:** Tailwind CSS (Premium Redesign via CDN integration, using customized fonts and strict brand colors)
*   **Localization (Philippine Market):**
    *   `TIME_ZONE = 'Asia/Manila'`
    *   `LANGUAGE_CODE = 'en-ph'`
    *   `DEFAULT_CURRENCY_SYMBOL = '₱'`
    *   `DEFAULT_CURRENCY_CODE = 'PHP'`
    *   Custom checkout form validating Philippine mobile numbers (e.g., `09XXXXXXXXX`).

---

## 🗄️ Active Data Models

### `Product`
The core catalog item containing the storefront landing page data.
*   **`title`** (`CharField`): Consumer-facing name of the product.
*   **`slug`** (`SlugField`): Unique URL-friendly slug (auto-generated from title if blank).
*   **`description`** (`TextField`): Rich text / HTML description detailing product specifications.
*   **`price`** (`DecimalField`): Selling price in Philippine Pesos (₱).
*   **`compare_at_price`** (`DecimalField`, optional): Original retail price to calculate discount percentages.
*   **`cj_product_id`** (`CharField`, optional): Unique CJ Dropshipping product identifier.
*   **`video_url`** (`URLField`, optional): Promotional video URL supporting `.mp4` direct links or platforms (YouTube, TikTok, etc.). Allows dynamic HTML5 video players on mobile.
*   **`features_list`** (`JSONField`): Dynamic JSON list of high-impact features (bullet points) shown in the benefits section.
*   **`is_active`** (`BooleanField`): Storefront visibility toggle.
*   **`sku`** (`CharField`, optional): Stock Keeping Unit.

### `ProductImage`
Carousel images supporting the gallery on the landing page.
*   **`product`** (`ForeignKey` to `Product`): Target product parent.
*   **`image`** (`ImageField`): Local file upload for media assets.
*   **`image_url`** (`URLField`): External URL for high-performance content delivery (CJ Dropshipping import integration).
*   **`order`** (`PositiveIntegerField`): Carousel sorting priority.

### `Order`
Customer conversion leads captured via the COD order form.
*   **`product`** (`ForeignKey` to `Product`): Ordered item.
*   **`full_name`** (`CharField`): Recipient name.
*   **`phone_number`** (`CharField`): Smart/Globe mobile format validation.
*   **`shipping_address`** (`TextField`): Full delivery details.

---

## 🎨 UI/UX Strategy
*   **Mobile-First Design:** Optimized for low latency, smooth scrollbars, clean touch targets, and lightweight layout grids designed for mobile viewports.
*   **Premium Brand Aesthetic:** Clean modern typography (`Inter` + `Outfit` Google Fonts), sleek white/slate color scheme, elegant glassmorphism headers, and standard hover scaling.
*   **Conversion Optimization:** The primary Call-to-Action (CTA) "BUY NOW - CASH ON DELIVERY" uses a distinct high-contrast accent color (`#FF5A00` / `brandAccent`) reserved strictly for action buttons, with a sticky bottom bar on mobile.
*   **Logistics & Shipping Transparency:** Direct notice in the checkout flow explaining that items are shipped directly from global manufacturing centers:
    > **Official Brand Notice:** To maintain the lowest possible prices for our customers and avoid expensive local warehouse overhead, all orders are shipped directly from our global manufacturing facility. Please allow 10–15 business days for delivery and quality inspection. Free insured tracking included!

---

## 🗺️ Roadmap
1.  **CJ Dropshipping API Integration:** Auto-sync product details, SKUs, inventory, and automate order forwarding.
2.  **Local Payment Gateway Setup:** Integrate local aggregators (PayMongo or Xendit) to support credit/debit card, GCash, Maya, and GrabPay payments alongside the native COD model.
