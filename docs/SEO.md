# Search Engine Optimization (SEO) Strategy and Guidelines

> **SEO and Indexing Architecture for BizFlow**  
> Guidelines for public discoverability versus strict privacy for internal business application views.

---

## 1. Core Principles & Philosophy

BizFlow is a multi-tenant business ERP, inventory management, and financial accounting application.
Because it processes sensitive commercial, transactional, and customer records, its SEO posture is divided into two distinct zones:

1. **Public Zone (Discoverable & Search-Engine Friendly)**:
   - Login page (`/auth/login/`)
   - Register page (`/auth/register/`)
   - Forgot Password page (`/auth/forgot-password/`)
   - Marketing landing page (future public homepage)
2. **Private Zone (Strictly Non-Indexable & Confidential)**:
   - Dashboard, Inventory, Sales, Purchases, Accounting, Reports, Settings, and all REST API endpoints.
   - **Must NEVER be indexed, cached, or crawled by search engines.**

---

## 2. Public vs Private Indexing Rules

### 2.1 Private Pages Policy
Every authenticated view rendered by Django templates must include the following meta tag in the `<head>` block:

```html
<meta name="robots" content="noindex, nofollow, noarchive, nosnippet">
```

Additionally, the Django security middleware or view decorators should send the corresponding HTTP header for all authenticated paths:

```http
X-Robots-Tag: noindex, nofollow, noarchive
```

### 2.2 Public Pages Policy
Public authentication and informational pages must have:
- Descriptive, keyword-relevant `<title>` tags formatted as: `Page Title | BizFlow - Inventory & Business Management System`.
- Concise, unique `<meta name="description">` (120 - 155 characters).
- Explicit canonical URL link tag: `<link rel="canonical" href="https://yourdomain.com/auth/login/">`.
- Standard indexable robots directive: `<meta name="robots" content="index, follow">`.

---

## 3. Robots.txt Configuration

The target deployment must serve a `robots.txt` file at `/robots.txt` that prevents crawlers from scanning private application routes and API endpoints:

```txt
# robots.txt for BizFlow
User-agent: *
Disallow: /dashboard/
Disallow: /inventory/
Disallow: /sales/
Disallow: /purchases/
Disallow: /parties/
Disallow: /accounting/
Disallow: /reports/
Disallow: /settings/
Disallow: /companies/
Disallow: /admin/
Disallow: /api/

Allow: /auth/login/
Allow: /auth/register/
Allow: /auth/forgot-password/

Sitemap: https://yourdomain.com/sitemap.xml
```

---

## 4. Semantic HTML & Heading Hierarchy

Proper semantic hierarchy improves accessibility, browser parsing speed, and SEO crawlability:

1. **Single `<h1>` Tag**:
   - Each page must contain exactly one `<h1>` element representing the primary subject of the page (e.g. `<h1>Sign In to BizFlow</h1>` on login; `<h1>Dashboard Overview</h1>` on dashboard).
2. **Logical Subheadings**:
   - Use `<h2>` for major content sections, `<h3>` for cards or widgets, and `<h4>` for sub-panels.
   - Never skip heading levels (e.g. avoid jumping from `<h1>` directly to `<h4>`).
3. **Semantic Landmarks**:
   - Structure page shells with `<header>`, `<nav>`, `<main>`, `<aside>`, and `<footer>` elements.
4. **Form Accessibility**:
   - Every `<input>`, `<select>`, and `<textarea>` must have an explicit matching `<label for="element_id">`.

---

## 5. Performance & Core Web Vitals

Search engines and user experience prioritize fast-loading, responsive interfaces:

1. **Lightweight Assets**:
   - Vanilla CSS design system (`main.css`) avoids bulky CSS runtime overhead.
   - Avoid oversized JavaScript bundles on authentication pages.
2. **Font Optimization**:
   - Use system font stacks with Google Fonts (`Inter`, `Plus Jakarta Sans`) loaded with `font-display: swap;` and DNS pre-connect headers:
     ```html
     <link rel="preconnect" href="https://fonts.googleapis.com">
     <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
     ```
3. **Image Optimization**:
   - Include explicit `width` and `height` attributes on company logos and UI icons to prevent Cumulative Layout Shift (CLS).
   - Use SVG for vector icons and logos.

---

## 6. Open Graph & Social Sharing

Public pages include Open Graph and Twitter card metadata for professional appearance when shared via messaging apps or social networks:

```html
<meta property="og:type" content="website">
<meta property="og:site_name" content="BizFlow">
<meta property="og:title" content="BizFlow - Business Inventory & Management System">
<meta property="og:description" content="Streamline multi-company inventory, invoicing, sales, and accounting with native Nepali BS calendar support.">
<meta property="og:image" content="/static/images/bizflow-og-preview.png">
<meta name="twitter:card" content="summary_large_image">
```

---

## 7. Strict Anti-Spam Guidelines

In accordance with agent rules:
- **No Keyword Stuffing**: Never overload page footers or descriptions with unnatural repetition of keywords.
- **No Hidden Text**: Do not render text invisible via `display: none;` or matching background colors to game search algorithms.
- **No Deceptive Redirects**: Do not route crawlers to different content than regular human users.