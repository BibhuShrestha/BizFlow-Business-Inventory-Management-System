# BizFlow Design System & UI/UX Standards

This document establishes the official Design System, visual direction, component patterns, and UX standards for the BizFlow platform.

---

## 1. Visual Direction & Principles

The interface adheres to an intentional, functional, enterprise-grade aesthetic:
- **Palette**: Blue and White
- **Tone**: Minimal, clean, professional, and confident
- **Ergonomics**: Responsive across all devices, easy to learn, and fast to navigate
- **Performance**: High contrast ratios, lightweight CSS, zero bloated frontend dependencies

### 1.1 Color Tokens

| Token Name | Hex Code | Visual Role & Usage Guidelines |
|:---|:---|:---|
| **Primary** | `#2563EB` | Interactive actions, active nav states, primary CTA buttons, focus indicators |
| **Dark Blue** | `#1E3A8A` | Sidebar background, brand headers, high-contrast dark accents |
| **White** | `#FFFFFF` | Content cards, modal dialogs, data table backgrounds, header background |
| **Background** | `#F8FAFC` | Primary viewport background (Slate 50), reducing eye fatigue |
| **Border** | `#E2E8F0` | Crisp 1px structural dividers, card outlines, form borders (Slate 200) |
| **Text** | `#0F172A` | Primary headings, body copy, data values (Slate 900) |
| **Secondary Text** | `#64748B` | Labels, metadata, table column headers, helper text (Slate 500) |

#### Semantic Accent Tokens
| Accent | Background | Text / Border | Purpose |
|:---|:---|:---|:---|
| **Success** | `#DCFCE7` | `#15803D` / `#16A34A` | Completed transactions, paid invoices, healthy stock levels |
| **Warning** | `#FEF9C3` | `#92400E` / `#D97706` | Approaching minimum stock thresholds, partial payments |
| **Danger** | `#FEE2E2` | `#B91C1C` / `#DC2626` | Destructive actions, out of stock alerts, overdue receivables |
| **Info** | `#E0F2FE` | `#0369A1` / `#0284C7` | Informational callouts, general system notices, audit tags |

---

## 2. Design Anti-Patterns (What to Avoid)

To maintain an uncluttered and highly productive user experience:
1. **Avoid Excessive Animations**: Use only instantaneous or 150ms transitions for hover/focus feedback. Do not use bouncing elements, parallax effects, or distracting entry animations.
2. **Avoid Excessive Gradients**: Use solid, high-contrast surfaces (`#FFFFFF` on `#F8FAFC`). Avoid multi-color gradients, neon glow effects, and complex radial patterns.
3. **Avoid Color Sprawl**: Restrict colors strictly to the core blue-and-white palette with muted, desaturated semantic status accents.
4. **Avoid Huge Cards**: Avoid excessive padding and heavy drop shadows. Keep cards compact (16px to 24px padding), with crisp 1px borders.
5. **Avoid Unnecessary Popups**: Do not disrupt user flows with unsolicited modals. Use inline form validation, subtle toast alerts, and persistent page headers.
6. **Avoid Overloaded Dashboards**: Present key metrics upfront and employ progressive disclosure for secondary reports and dense historical logs.
7. **No Decorative Elements Without Purpose**: Every button, badge, icon, and divider must provide functional value to business operations.

---

## 3. Typography & Spacing Scale

### 3.1 Typography
- **Primary Typeface**: `Inter` (via Google Fonts or system fallback: `system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`)
- **Monospace Typeface**: `'JetBrains Mono', 'Courier New', monospace` for SKUs, invoice numbers, currency values, and barcodes.

| Scale Token | Font Size | Weight | Line Height | Usage |
|:---|:---|:---|:---|:---|
| **Display / Hero** | 38px (2.75rem) | 800 (Bold) | 1.2 | Public marketing landing page hero title |
| **Page Title (h1)** | 22px (1.55rem) | 700 (Bold) | 1.3 | Main view titles in dashboard and app screens |
| **Section Title (h2)** | 18px (1.25rem) | 600 (Semibold) | 1.35 | Major card and section headings |
| **Subheading (h3)** | 15px (1.05rem) | 600 (Semibold) | 1.4 | Module cards, panel titles, report groupings |
| **Body Standard** | 13.5px (0.96rem) | 400 (Regular) | 1.5 | Standard page copy, table cell content, input values |
| **Caption / Helper** | 12px (0.85rem) | 400 / 500 | 1.4 | Input descriptions, timestamp stamps, table subtext |
| **Micro / Tag** | 11px (0.78rem) | 600 (Semibold) | 1.2 | Badges, table column headers (uppercase) |

### 3.2 Spacing System
Built strictly on a **4px modular grid**:
- `4px` (`--space-xs`): Micro gaps, badge inner padding, tight icon spacing
- `8px` (`--space-sm`): Form control label margins, button element gaps, inline items
- `12px` (`--space-md`): Card header padding, form group spacing, mobile margins
- `16px` (`--space-base`): Standard component gutters, stat card padding, alert boxes
- `20px` (`--space-lg`): Main card padding, table outer padding, modal inner body
- `24px` (`--space-xl`): Page layout container padding, dashboard metric grid gaps
- `32px` (`--space-2xl`): Major structural section separators
- `48px` (`--space-3xl`): Hero section spacing and landing page dividers

---

## 4. Components Specification

### 4.1 Buttons
Buttons are available in three standard sizes (`sm`, `base`, `lg`) and four semantic variants:
```html
<!-- Primary action -->
<button class="btn btn-primary">Save Changes</button>

<!-- Secondary action -->
<a href="/list/" class="btn btn-secondary">Cancel</a>

<!-- Destructive action -->
<button class="btn btn-danger">Delete Record</button>

<!-- Ghost / Subtle action -->
<button class="btn btn-ghost btn-sm">Export</button>
```

#### States:
- **Default**: Crisp 1px border, high-contrast text.
- **Hover**: Subtle brightness adjustment (`#1D4ED8` on primary, `#F8FAFC` on secondary).
- **Focus-Visible**: 2px outline in `#2563EB` with 2px offset.
- **Disabled**: `opacity: 0.55; cursor: not-allowed; pointer-events: none;`.

### 4.2 Form Controls & Validation
Labels are always placed above inputs with clear requirement indicators (`*`):
```html
<div class="form-group">
  <label class="form-label" for="id_sku">SKU Code <span class="required">*</span></label>
  <input type="text" id="id_sku" name="sku" class="form-control" placeholder="e.g. SKU-1001">
  <span class="form-hint">Unique alphanumeric identifier for stock tracking.</span>
</div>
```

#### Validation Feedback:
- `.form-control.is-invalid`: Red border (`#DC2626`) with `.invalid-feedback` text.
- `.form-control.is-valid`: Subtle green border (`#16A34A`).

#### Checkboxes & Radio Buttons:
Custom styled, keyboard-accessible SVG check indicators:
```html
<label class="form-check">
  <input type="checkbox" name="is_active" class="form-check-input" checked>
  <span class="form-check-label">Active Workspace</span>
</label>
```

### 4.3 Data Tables
Optimized for rapid scanning and dense business records:
- **Header**: `#F8FAFC` background with subtle `#E2E8F0` border and uppercase 11px headers.
- **Rows**: 11px-14px vertical padding with subtle hover row illumination (`#F8FAFC`).
- **Numbers & Currencies**: Right-aligned (`.text-right`) and rendered in monospace font (`.font-mono`).
- **Empty States**: Centered with dedicated `.table-empty` styling.

### 4.4 Cards & Stat Metrics
Cards group related fields and business data without visual distraction:
- Border: `1px solid #E2E8F0`
- Background: `#FFFFFF`
- Radius: `8px` (`--radius-md`)
- Stat Cards: Simple vertical stack of label $ightarrow$ large numeric value $ightarrow$ semantic delta badge.

### 4.5 Alerts & System Notices
Inline flash messages with colored left border accent:
- `.alert-success`: Soft green with `#16A34A` left border.
- `.alert-danger`: Soft red with `#DC2626` left border.
- `.alert-warning`: Soft amber with `#D97706` left border.
- `.alert-info`: Soft sky blue with `#0284C7` left border.

### 4.6 Navigation Shell
- **Desktop Sidebar**: Fixed 240px drawer in Dark Blue (`#1E3A8A`), providing high contrast against the content viewport.
- **Header**: Sticky 56px white bar (`#FFFFFF`) with bottom border, showing page breadcrumb/title, active user profile, and session termination.
- **Mobile Navigation**: Collapsible off-canvas menu triggered via `#sidebar-toggle` with backdrop dismissal.

---

## 5. Responsive Breakpoints

| Breakpoint | Viewport Width | Target Devices | Layout Behavior |
|:---|:---|:---|:---|
| **Mobile (`sm`)** | `< 640px` | Phones | Sidebar hidden, single-column stat grids, stacked form rows, compressed table margins |
| **Tablet Portrait (`md`)** | `640px – 768px` | Small tablets | 2-column KPI cards, off-canvas navigation drawer |
| **Tablet Landscape (`lg`)** | `769px – 1024px` | Tablets, iPad | Collapsible sidebar, 2-to-3 column grids |
| **Desktop Standard (`xl`)** | `> 1024px` | Laptops & monitors | Persistent 240px sidebar, full responsive multi-column layouts |

---

## 6. UX Patterns & Usability Standards

### 6.1 Simple $ightarrow$ Fast $ightarrow$ Clear $ightarrow$ Predictable
- **Predictability**: Buttons that create resources always use `.btn-primary` and are located at the top-right of directories or bottom-left of forms.
- **Destructive Actions**: Delete and cancellation triggers use `.btn-ghost.text-danger` with native or modal confirmation guards.
- **Keyboard Friendliness**: Tab order is strictly linear. Modals trap focus and exit on `Escape`.
- **Search & Filters**: Search fields have clear submit buttons and a "Clear / Reset" anchor whenever query parameters are active.
- **Empty States**: If a table has zero records, an empty state clearly communicates the situation and provides an immediate CTA button (e.g. "+ Add Product").
- **Printing**: Print layout (`@media print`) hides navigation sidebars, headers, and buttons, rendering a clean, professional, computer-generated invoice document.

---

## 7. 5-Star UI/UX Component Specifications (Part 26)

Extracted and standardized from the Figma Make design specifications (`Create Business Inventory Website.make`):

### 7.1 Illuminated Brand Mark & Identity
- `.brand-mark`: 34×34px rounded badge (`#3B82F6`) with glowing shadow (`0 7px 18px rgba(37, 99, 235, 0.35)`) and 3 vertical white bar indicators (heights 9px, 16px, 12px) symbolizing dynamic inventory motion.
- Tagline: "Business, in motion".

### 7.2 Active Company Switcher Card
- `.company-switcher`: Elevated drawer card (`rgba(255, 255, 255, 0.06)`) displaying:
  - 32×32px company monogram logo (`.company-logo`) with 2-letter uppercase initials.
  - "CURRENT COMPANY" tracking label with active enterprise name.
  - Chevron dropdown indicator for instant tenant switching.

### 7.3 Omnipresent Topbar Ergonomics
- `.global-search`: Keyboard-accelerated global input (`Ctrl+K` / `⌘K`) for searching invoices, products, and parties.
- `.date-chip`: Dual Bikram Sambat (BS) and Gregorian (AD) calendar pill (e.g., `27 Ashwin 2083 | 13 Oct 2026`).
- `.notification-wrap` & `.notification-panel`: Interactive dropdown center with categorized priority alerts (`danger`, `warning`, `info`) and "Mark all read" action.

### 7.4 4-Metric Executive KPI Cards
- `.metrics-grid` & `.metric-card`: 4 cards displaying Today's Sales, Receivables (Dr), Total Purchases / Payables (Cr), and Net Profit / Inventory Stock Value with:
  - Tinted icon badges (`.metric-icon.blue`, `.metric-icon.amber`, `.metric-icon.violet`, `.metric-icon.green`).
  - Trend percentages vs yesterday/month (`.trend.up`, `.trend.down`).
  - Secondary operational context tags.

### 7.5 Sales Overview & Dynamic Revenue Chart
- `.revenue-panel`: 7-day revenue overview with:
  - Segmented period filter (`7 days`, `30 days`, `3 months`).
  - Total revenue callout and percentage comparison.
  - Responsive pure CSS bar chart (`.bar-chart`, `.bar-column`, `.bar`) with peak day highlight and tooltip badge.

### 7.6 Cash Flow Visualization
- `.cashflow-panel`: Conic donut gauge (`.donut`) rendering real-time cash inflow vs outflow proportion with center net cashflow figure and operational health advisory note (`.cashflow-note`).

### 7.7 Invoices Toolbar & Stock Alerts
- Recent Invoices table with real-time text filter and party initials badge (`.party span`).
- Stock Alerts panel with visual progress tracks (`.stock-track i`) indicating remaining stock relative to safety reorder thresholds.

### 7.8 Keyboard Shortcut Tokens (`<kbd>`) & Cashier Rapid-Entry Ergonomics
- **Visual Key Badges (`kbd`)**: Standardized `<kbd>` typography tags featuring high-contrast rounded badges:
  - Font: Monospace (`'JetBrains Mono', 'Courier New', monospace`), 10px–11px, bold.
  - Border: Subtle 1px elevation border (`#cbd5e1` or `rgba(255,255,255,0.2)` on dark surfaces).
  - Background: Crisp neutral background (`#f1f5f9` on light, translucent on dark headers).
  - Placement: Inline on action CTA buttons (`Create Invoice <kbd>N</kbd>`) and form helper tips (`Tip: Press <kbd>Ctrl</kbd> + <kbd>Enter</kbd> to save anytime`).
- **Global Event Manager**: Built-in keydown interceptor in `base.html` that handles:
  - Accelerators: <kbd>Ctrl</kbd> + <kbd>K</kbd> (Search), <kbd>N</kbd> (Sale), <kbd>P</kbd> (Purchase), <kbd>I</kbd> (Product), <kbd>C</kbd> (Customer), <kbd>W</kbd> (Workspace), <kbd>D</kbd> (Dashboard), <kbd>?</kbd> (Cheatsheet), <kbd>Ctrl+Enter</kbd> (Save), <kbd>Esc</kbd> (Dismiss).
  - Input field isolation: Automatically disables single-key triggers when focus is within `input`, `textarea`, `select`, or `contenteditable` elements.

### 7.9 Interactive Workspace Switcher & Help Modal
- **Workspace Switcher Dropdown (`#company-dropdown-menu`)**:
  - Attached to the sidebar company card (`.company-switcher`).
  - Renders user companies dynamically via `user_companies` context processor.
  - Highlights active company with blue indicator (`#60a5fa`) and provides direct navigation link to switch active tenant.
- **Shortcuts Cheatsheet Modal (`#bizflow-shortcuts-modal`)**:
  - Backdrop blur modal (`rgba(15,23,42,0.65)` with `backdrop-filter: blur(4px)`).
  - Two-column grid grouping shortcuts into Quick Transactions, Navigation & Search, and Forms & Dialogs.
  - Accessible via <kbd>?</kbd> or topbar help trigger, dismissible via <kbd>Esc</kbd> or backdrop click.


