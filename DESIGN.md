# Design System - Veridian OSINT Platform

This document outlines the design system specifications of the Veridian OSINT platform, including the standard dashboard and the graphic whiteboard views, mapped across Light and Dark themes.

---

## 1. Global Design Tokens

### Color Palette
The colors are optimized for high-contrast data visualization, supporting quick OSINT analysis.

| Token / Element | Light Mode Value | Dark Mode Value |
| :--- | :--- | :--- |
| **Page Background** | `#f8fafc` (Slate 50) / `#f1f5f9` (Slate 100) | `#0b0f19` (Deep Navy-Slate) |
| **Sidebar Background** | `#eef2ff` (Indigo 50) / `#e8ecf8` (Soft Gray) | `#151c2c` (Dark Slate Blue) |
| **Card / Container Background** | `#ffffff` (White) | `#1e293b` (Slate 800) |
| **Primary Brand Accent** | `#3b82f6` (Blue 500) / `#2563eb` (Blue 600) | `#3b82f6` (Blue 500) / `#2563eb` (Blue 600) |
| **Primary Accent Hover** | `#1d4ed8` (Blue 700) | `#1d4ed8` (Blue 700) |
| **Primary Accent Disabled**| `#bfdbfe` (Blue 200) | `#1e293b` (Slate 800) |
| **Danger / Lock Accent** | `#dc2626` (Red 600) / `#991b1b` (Red 800) | `#ef4444` (Red 500) / `#991b1b` (Red 800) |
| **Primary Heading Text** | `#0f172a` (Slate 900) | `#f8fafc` (Slate 50) |
| **Body Text / Secondary Labels** | `#475569` (Slate 600) | `#94a3b8` (Slate 400) |
| **Table Header Background** | `#f1f5f9` (Slate 100) | `#0f172a` (Slate 900) |
| **Borders & Dividers** | `#e2e8f0` (Slate 200) | `#334155` (Slate 700) |

### Spacing & Grid System
* **Outer Padding**: `32px` (`p-8`) for main content panes.
* **Component Inner Padding**: `24px` (`p-6`) or `32px` (`p-8`) for card contents.
* **Layout Gaps**: `24px` (`gap-6`) standard spacing between grid cards or list elements.
* **Responsive Breakpoints**: Standard flex wrap and grid auto-fill structures with `360px` minimum card widths.

### Shadows & Roundness
* **Corner Radius (Cards)**: `12px` to `16px` (`rounded-xl` / `rounded-2xl`).
* **Corner Radius (Buttons/Inputs)**: `8px` (`rounded-lg`).
* **Corner Radius (Pills/Tabs)**: `9999px` (`rounded-full`).
* **Box Shadows (Light Mode)**: Soft, diffuse shadow (`0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -4px rgba(0,0,0,0.1)`).
* **Box Shadows (Dark Mode)**: Flat styling; relies on color contrast and thin borders (`1px solid var(--card-border)`) rather than shadows.

---

## 2. Typography

* **Font Family**: Modern Sans-Serif stack (`Inter`, system-ui, or `-apple-system`).
* **Typography Scale**:
  * **H1 / Page Titles**: `24px` (`text-2xl`), bold (`font-bold`, `700` or `800` weight).
  * **H2 / Subheaders (e.g., node titles)**: `16px` (`text-base`) or `18px` (`text-lg`), semi-bold (`600` weight).
  * **Body / Label Text (menus, inputs)**: `14px` (`text-sm`) or `15px` (`text-normal`), regular/medium (`400`/`500` weight).
  * **Captions & Metadata**: `12px` (`text-xs`), regular (`400` weight).

---

## 3. Component specifications

### Buttons
1. **Primary Pill Button**:
   * Solid brand blue background (`#2563eb`), white text.
   * Icon on left, text on right.
   * Pill shape (`rounded-full`), padded `10px 24px`.
2. **Secondary Outline Button**:
   * Transparent background, blue text, thin blue outline (`1px solid #2563eb`).
   * Pill shape (`rounded-full`).
3. **Tab Selectors (Quick Queries)**:
   * Rectangular with rounded corners (`rounded-lg`, `8px`).
   * **Active**: Solid blue background, white text/icons.
   * **Inactive**: Transparent background, thin border, blue/gray text.

### Form Inputs & Search Boxes
* **Inputs**:
  * Light Mode: Very light gray background (`#f8fafc`), gray border.
  * Dark Mode: Deep dark slate background (`#0f172a`), dark-gray border.
  * Rounded corners (`8px`), full-width expansion support.

### Data Tables
* **Header**: Dark slate text, medium-bold, light grey background.
* **Row dividers**: Thin gray outline.
* **Padding**: Compact cells (`12px 16px`) for readable, data-dense tabular display.

---

## 4. Graphic Mode (Whiteboard Graph View) Specifics

### Graph Canvas
* **Background Color**: Light Mode: Pure white (`#ffffff`); Dark Mode: Deep navy (`#0b0f19`).

### Left Float Toolbar (Vertical Toolbox)
* Floating container containing square buttons (`~40px x 40px`).
* **Active tool**: Blue background, white icon.
* **Danger/Lock tool**: Deep red background (`#991b1b`), white icon.

### Nodes (React Flow)
1. **Entity Cards**:
   * Circular badge showing source origin (e.g., LinkedIn brand logo).
   * Rectangular content container below badge with rounded corners (`8px`), displaying Name (bold) and Address/Metadata (small, muted).
2. **Table/Data Nodes**:
   * Large container displaying reactions, comments, or data lists.
   * **Header**: Header banner with collapse toggle (`-`/`+`), utilizing red/crimson badge on left and dark-gray background.
   * **Footer**: Integrated pagination tracker (`1/3 - 12 resultados`) with back/forward arrow navigation buttons.
