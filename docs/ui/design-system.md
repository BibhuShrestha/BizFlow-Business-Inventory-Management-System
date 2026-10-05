# UI Design System & Component Library

> **BizFlow Frontend Architecture**  
> *Authoritative specification for Color Tokens, Typography, Layout, Components, and Accessibility.*

---

## 1. Design Philosophy
BizFlow embodies a **Modern, Minimalist, Corporate** aesthetic tailored for high-efficiency cashier workflows and executive financial oversight.
- **Primary Brand**: Royal Blue (`#1E40AF` / `#2563EB`) communicating stability and trust.
- **Surface & Backgrounds**: Clean slate neutrals (`#F8FAFC` background, `#FFFFFF` cards, `#0F172A` text).
- **Zero Distraction**: High contrast, compact density, legible tables, and responsive mobile adaptation.

---

## 2. Design Tokens

### A. Color Palette
```css
:root {
  /* Brand Primary */
  --primary-50:  #EFF6FF;
  --primary-100: #DBEAFE;
  --primary-500: #3B82F6;
  --primary-600: #2563EB;
  --primary-700: #1D4ED8;
  --primary-800: #1E40AF;

  /* Neutrals */
  --slate-50:  #F8FAFC;
  --slate-100: #F1F5F9;
  --slate-200: #E2E8F0;
  --slate-500: #64748B;
  --slate-700: #334155;
  --slate-900: #0F172A;

  /* Semantic Feedback */
  --success: #10B981;
  --warning: #F59E0B;
  --danger:  #EF4444;
  --info:    #06B6D4;
}
```

### B. Typography
- **Font Family**: `'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`.
- **Scale**:
  - `h1`: 24px (1.5rem), font-weight 700.
  - `h2`: 20px (1.25rem), font-weight 600.
  - `h3`: 16px (1.0rem), font-weight 600.
  - `body`: 14px (0.875rem), font-weight 400, line-height 1.5.
  - `caption / badge`: 12px (0.75rem), font-weight 500.

---

## 3. Core Components

### A. Buttons (`.btn`)
- `.btn-primary`: Filled Royal Blue background (`#1E40AF`), white text, hover lift.
- `.btn-secondary`: Light slate background (`#F1F5F9`), slate-700 text, subtle border.
- `.btn-danger`: Red tone for destructive actions (Void invoice, Delete).
- `.btn-ghost`: Transparent background with border on hover.

### B. Tables (`.table`)
- Clean white rows, slate-100 subtle zebra striping.
- Dark header background (`#1E293B`) or crisp border-bottom slate-200.
- Sticky column headers for long ledgers.
- Right-aligned numerical and currency columns.

### C. Status Badges (`.badge`)
- `.badge-success`: Soft green background (`#DEF7EC`), dark green text (`#03543F`) — Paid.
- `.badge-warning`: Soft amber background (`#FEF08A`), amber-900 text — Partial / Low Stock.
- `.badge-danger`: Soft red background (`#FEE2E2`), red-900 text — Overdue / Out of Stock.
- `.badge-info`: Soft blue background (`#DBEAFE`), blue-900 text — Processing / Cheque.

---

## 4. Accessibility (WCAG 2.1 AA Compliance)
- **Contrast Ratio**: Normal text exceeds 4.5:1 against backgrounds; large text exceeds 3:1.
- **Keyboard Navigation**: Full focus ring visible on `:focus-visible` states across POS cash drawers, tables, and buttons.
- **Semantic Structure**: Single `<h1>` per view, paired `<label for="...">` on all inputs, `<meta name="robots" content="noindex, nofollow">` on private authenticated screens.
