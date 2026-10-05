# SEO and Page Quality Checklist

> **Pre-Release Verification Checklist for BizFlow Web Views**  
> Use this checklist before completing frontend views, templates, and routing changes.

---

## 1. Page Indexing & Robots Directives

- [ ] **Private Application Views**:
  - [ ] Contains `<meta name="robots" content="noindex, nofollow, noarchive, nosnippet">` in `<head>`.
  - [ ] Returns `X-Robots-Tag: noindex, nofollow` HTTP header.
  - [ ] Path is excluded in `robots.txt` (`/dashboard/`, `/sales/`, `/purchases/`, `/inventory/`, `/reports/`, `/accounting/`, `/api/`).
- [ ] **Public Pages (Login / Register / Forgot Password)**:
  - [ ] Contains `<meta name="robots" content="index, follow">`.
  - [ ] Has explicit `<link rel="canonical" href="...">` tag matching canonical URL.
  - [ ] Does not require authentication cookies or redirect crawlers.

---

## 2. Meta Tags & Document Title

- [ ] **Title Tag**:
  - [ ] Present and non-empty on every template.
  - [ ] Follows convention: `{Page Name} | BizFlow - Inventory & Business Management System`.
  - [ ] Length between 35 and 65 characters.
- [ ] **Meta Description (Public Pages)**:
  - [ ] Present and concise (between 120 and 155 characters).
  - [ ] Accurately summarizes the page function.
  - [ ] Free of repetitive keywords or unnatural phrasing.
- [ ] **OpenGraph & Social (Public Pages)**:
  - [ ] `og:title`, `og:description`, `og:image`, `og:url`, and `og:type` defined.
  - [ ] `twitter:card` set to `summary_large_image`.

---

## 3. Semantic Hierarchy & Document Structure

- [ ] **Single `<h1>` Landmark**:
  - [ ] Exactly one `<h1>` tag present per page.
  - [ ] `<h1>` reflects the main page view title (e.g. `<h1>Sales Invoice #INV-2024-001</h1>`).
- [ ] **Heading Order**:
  - [ ] Subsections use `<h2>`, internal card headers use `<h3>`.
  - [ ] No skipped heading levels (e.g. no `<h1>` followed directly by `<h4>`).
- [ ] **HTML5 Landmarks**:
  - [ ] Page layout organized with `<header>`, `<nav>`, `<main id="main-content">`, and `<footer>`.
- [ ] **Forms & Controls**:
  - [ ] Every `<input>`, `<select>`, and `<textarea>` has a unique `id` and corresponding `<label for="...">`.
  - [ ] Buttons use `<button type="submit">` or `<button type="button">`, not non-semantic `<div>` or `<span>` click handlers.

---

## 4. Media & Asset Performance

- [ ] **Images**:
  - [ ] All `<img>` tags have descriptive `alt` attributes (e.g. `alt="Company Logo"`).
  - [ ] Explicit `width` and `height` attributes present to prevent Cumulative Layout Shift (CLS).
- [ ] **Fonts & CSS**:
  - [ ] Web fonts load with `font-display: swap;`.
  - [ ] No inline CSS `style="..."` attributes on structural elements.
  - [ ] CSS files linked in `<head>`; JavaScript scripts loaded with `defer` or at bottom of `<body>`.

---

## 5. Security & Anti-Spam Verification

- [ ] No deceptive hidden text (e.g. text styled with `display: none;` containing SEO keywords).
- [ ] No automated keyword stuffing in page footers or meta tags.
- [ ] Internal API endpoints (`/api/v1/...`) are never linked as public hyperlinks.
- [ ] All external outbound links include `rel="noopener noreferrer"`.