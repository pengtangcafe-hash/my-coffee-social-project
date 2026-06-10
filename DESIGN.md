# DESIGN.md — คู่มือดีไซน์ Social Analytics Dashboard

> ดึงจากโค้ดจริงใน `src/generate_dashboard.py` · อัปเดต 2026-06-10

---

## 1. สถาปัตยกรรม Single-file

### โครงสร้าง
`generate_dashboard.py` สร้าง HTML ไฟล์เดียว (`dashboard/index.html`) จาก `HTML_TEMPLATE` ผ่าน **`str.format()`**  
ทุก CSS, HTML, JS ฝังอยู่ใน template string เดียว

### กฎสำคัญ: double-brace escaping
| ใช้ใน | เขียนใน .py | เอาต์พุต HTML |
|---|---|---|
| CSS/JS block ทั่วไป | `{{ }}` | `{ }` |
| Placeholder ฉีดข้อมูล | `{DRINK_COSTS_JSON}` | ค่าจริง |
| onclick inline ที่มี `'` | `\\'` | `\'` |

ตัวอย่าง:
```python
# ถูก — CSS ใน template
.dc-btn {{ padding: 8px 14px; border-radius: 10px; }}

# ถูก — ฉีดข้อมูล
const DRINK_COSTS = {DRINK_COSTS_JSON};

# ถูก — onclick ใน Python f-string
'onclick="showView(\\'view-cost-drinks\\')"'
```

### ไฟล์ standalone
`google-sheets/Code.gs` ไม่ผ่าน `.format()` → ใช้ `{ }` เดี่ยวได้ตามปกติ

### Build ritual
```bash
python src/generate_dashboard.py --rebuild
cp dashboard/index.html docs/index.html   # GitHub Pages เสิร์ฟจาก docs/
```

---

## 2. ธีม

### ธีมที่มี
| id | emoji | ลักษณะ |
|---|---|---|
| `coffee` | ☕ | **ค่าเริ่มต้น** — dark espresso, warm amber |
| `light` | ☀️ | cream/sand neutral |
| `dark` | 🌙 | slate dark |
| `fancy` | ✨ | glass/blur gradient |

### setTheme()
```javascript
function setTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  localStorage.setItem('sa-theme', t);           // บันทึก preference
  // อัป active-theme class บนปุ่ม
  initCharts(activeViewId);                       // re-render chart สีใหม่
}
```
โหลดครั้งแรก: `applyStoredTheme()` → ดึงจาก `localStorage.getItem('sa-theme')` (default: `'coffee'`)

### getThemeChartCfg()
ส่ง config สีให้ Chart.js — เรียกก่อน `new Chart(...)` ทุกครั้ง

| ธีม | grid | tick | tooltipBg | tooltipText | border |
|---|---|---|---|---|---|
| light | `#f1f5f9` | `#94a3b8` | `#1e293b` | `#f8fafc` | `#ffffff` |
| dark | `#334155` | `#94a3b8` | `#0f172a` | `#f8fafc` | `#1e293b` |
| fancy | `rgba(255,255,255,0.1)` | `rgba(255,255,255,0.65)` | `rgba(15,12,41,0.92)` | `#fff` | `rgba(255,255,255,0.15)` |
| coffee | `#3D2010` | `#D4AC78` | `#160C02` | `#F8EDD5` | `#2D1A08` |

---

## 3. Color Tokens

### Base UI tokens

| Token | light | dark | fancy | coffee |
|---|---|---|---|---|
| `--bg` | `#f4f2ed` | `#0f172a` | `transparent` | `#0D0700` |
| `--sidebar` | `#ffffff` | `#1e293b` | `rgba(0,0,0,0.3)` | `#160C02` |
| `--card` | `#ffffff` | `#1e293b` | `rgba(255,255,255,0.08)` | `#2D1A08` |
| `--card-border` | `#e8e2d8` | `#334155` | `rgba(255,255,255,0.15)` | `#7A4A20` |
| `--text` | `#1c160f` | `#f8fafc` | `#ffffff` | `#F8EDD5` |
| `--text-muted` | `#6b6256` | `#94a3b8` | `rgba(255,255,255,0.6)` | `#D4AC78` |
| `--grid` | `#ece6dc` | `#334155` | `rgba(255,255,255,0.1)` | `#3D2010` |
| `--nav-active` | `#f1ebe2` | `#334155` | `rgba(255,255,255,0.15)` | `#3D2212` |
| `--nav-text` | `#1c160f` | `#f8fafc` | `#ffffff` | `#F8EDD5` |

### Brand / Overview tokens (`:root` เดียวกันทุกธีม ยกเว้น accent-ink)

| Token | ค่า | หมายเหตุ |
|---|---|---|
| `--ov-espresso-1` | `#241307` | เข้มที่สุด |
| `--ov-espresso-2` | `#4a2c17` | พื้นหลัง badge/active |
| `--ov-caramel` | `#e0a256` | accent dot, focus outline |
| `--ov-crema` | `#f6ecda` | text บน espresso bg |
| `--ov-accent-ink` | `#a55f17` (light) / `#e0a256` (dark) / `#f0b878` (fancy) / `#e8b06a` (coffee) | hover/link |

### Drink-cost tokens

| Token | light | dark | fancy | coffee |
|---|---|---|---|---|
| `--dc-cost` | `#c08a4a` | `#b5793a` | `#d39a52` | `#c89a5e` |
| `--dc-profit` | `#2f9e6b` | `#34b87e` | `#4cd6a0` | `#46c98c` |
| `--dc-warn` | `#c2410c` | `#fb923c` | `#fdba74` | `#f8a560` |

### สีแบรนด์ช่องทาง (fixed — ไม่เปลี่ยนตามธีม)

| ช่องทาง | สี | ตัวแปร |
|---|---|---|
| หน้าร้าน (store) | `#00085f` | `DC_CH_COLORS.store` |
| Lineman | `#648a23` | `DC_CH_COLORS.lineman` |
| Shoppee | `#f86612` | `DC_CH_COLORS.shoppee` |
| Grab | `#056837` | `DC_CH_COLORS.grab` |

---

## 4. Typography

```
font-family: 'Prompt', sans-serif   (Google Fonts — weights 300–900)
```

| Class | CSS | ใช้ที่ |
|---|---|---|
| `.ov-h1` | `font-size: clamp(1.7rem, 1.2rem+1.6vw, 2.4rem); font-weight: 900; letter-spacing: -0.02em` | หัวทุกหน้า |
| `.ov-sub-h` | `font-size: .9rem; color: var(--text-muted); margin-top: 4px` | คำอธิบายใต้หัว |
| `.dc-group-title` | `font-size: .82rem; font-weight: 800; letter-spacing: .01em` | หัวหมวด accordion |
| `.dc-st-val` | `font-size: 1.45rem; font-weight: 900; font-variant-numeric: tabular-nums` | ตัวเลขสถิติ |
| `.dc-st-lab` | `font-size: .68rem; font-weight: 600` | ป้ายสถิติ |
| `.dc-name` | `font-size: .92rem; font-weight: 700` | ชื่อเมนูในรายการ |
| `.dc-btn` | `font-size: .8rem; font-weight: 700` | ปุ่มทั่วไป |
| `.ov-mtab` | `font-size: .76rem; font-weight: 600` | แท็บ/pill เลือก |

---

## 5. โครง Layout

### Sidebar
```
<div class="flex h-screen overflow-hidden">
  <aside>   ← nav sidebar (fixed width ~256px)
  <main id="main-content" class="flex-1 overflow-y-auto p-8">
    <div id="view-*" class="view">...   ← หน้าต่างๆ
```

### กลุ่มเมนูใน Sidebar
| กลุ่ม | รายการ |
|---|---|
| **Platforms** | TikTok · Facebook · Instagram (สร้างอัตโนมัติจาก `SIDEBAR_NAV_ITEMS`) |
| **Intelligence** | ภาพรวม · วิเคราะห์ · คู่แข่ง (Deep) · ติดตามคู่แข่ง · ราคากลาง |
| **Backbar** | คลังแสง · สต็อกหลังบ้าน · ต้นทุนผันแปรและคงที่ · ต้นทุนเครื่องดื่ม · ตรวจสอบยอดขายจริง & ทุนรวม · บันทึกข้อมูลนำเข้า POS |
| **Tools** | นำเข้าข้อมูล · บันทึกอัปเดต |

### ระบบ View
```css
.view { display: none; }
.view.active { display: block; }
```

### showView(id)
```javascript
function showView(id) {
  // 1. ซ่อนทุก .view → แสดง #<id>
  // 2. ถอด .active ทุก .nav-btn → ใส่ #nav-<id ตัด 'view->'>
  // 3. setTimeout(() => initCharts(id), 50)
}
```
**Convention:** view id = `view-<x>` → nav button id = `nav-<x>`  
ตัวอย่าง: `view-cost-drinks` ↔ `nav-cost-drinks`

### initCharts(viewId)
| viewId | เรียก |
|---|---|
| `view-home` | `initHomeOverview()` |
| `view-intel` | `renderIntelCards()` + `renderIntelUpdateBadge()` |
| `view-updatelog` | `renderUpdateLog()` |
| `view-pricing` | `renderPricingView()` |
| `view-competitor-deep` | `renderDeepTab()` |
| `view-tracker` | `renderTrackerView()` |
| `view-cost-drinks` | `renderDrinkCosts()` |
| `view-bb-armory/stock/varfix/posimport` | no-op (placeholder) |
| Platform views (tiktok/facebook/instagram) | `initLineChart()` + `initDoughnutChart()` |

---

## 6. Component Patterns

### หัวหน้า
```html
<div class="mb-6">
  <h1 class="ov-h1">ชื่อหน้า</h1>
  <p class="ov-sub-h">คำอธิบายย่อ</p>
</div>
```

### Coming-soon tile
```html
<div class="ov-tile ov-soon">
  <div class="ov-soon-emoji">📦</div>
  <div class="ov-soon-title">Launching soon..</div>
  <div class="ov-soon-sub">คำอธิบายสั้นๆ</div>
  <span class="ov-soon-badge">
    <span class="ov-soon-dot"></span>อยู่ระหว่างพัฒนา
  </span>
</div>
```
`.ov-soon-dot` มี animation `ovPulse` (fade+scale 1.6s) — off เมื่อ `prefers-reduced-motion`

### แถบสถานะ Backbar (`bb-status-bar`)
```html
<div class="bb-status-bar">
  <!-- placeholder: -->
  <span class="bb-status-pill soon">
    <span class="dot"></span>🟡 เร็วๆ นี้
  </span>
  <!-- live: -->
  <span class="bb-status-pill live">
    <span class="dot"></span>🟢 ใช้งานอยู่
  </span>
  <span class="bb-status-meta">ใช้งานล่าสุด: <b>—</b></span>
  <span class="bb-status-meta">อัปเดตข้อมูลล่าสุด: <b id="bb-updated-cost">—</b></span>
</div>
```
`.soon .dot` → `background: var(--ov-caramel)` · `.live .dot` → `background: var(--dc-profit)`  
วางใต้ `.ov-sub-h` ในทุกหน้า Backbar; หน้า `view-cost-drinks` → `renderDrinkCosts()` เซ็ต `#bb-updated-cost` จาก `DCS.parsed_at`

### การ์ดสถิติ
```html
<div class="dc-stats-row">
  <div class="dc-stat hero">     <!-- hero = gradient espresso -->
    <span class="dc-st-lab">ป้าย</span>
    <span class="dc-st-val">฿1,234 <small>บาท</small></span>
    <span class="dc-st-sub">รายละเอียดเพิ่ม</span>
  </div>
  <div class="dc-stat">...</div>
</div>
```
`.dc-stats-row .dc-stat { flex: 1 1 100px }` → ≤720px: `80px` → ≤500px: `58px` (1 แถว)

### ปุ่ม dc-btn
```html
<button class="dc-btn primary">บันทึก</button>   <!-- espresso bg -->
<button class="dc-btn ghost">ยกเลิก</button>     <!-- transparent -->
<button class="dc-btn danger">ลบ</button>         <!-- dc-warn color -->
```
Base: `padding: 8px 14px; border-radius: 10px; font-size: .8rem; font-weight: 700`

### แท็บ ov-mtab
```html
<button class="ov-mtab active">เลือกอยู่</button>
<button class="ov-mtab">ตัวเลือกอื่น</button>
```
Active: `background: var(--ov-espresso-2); color: var(--ov-crema)`  
Touch target: `min-height: 44px` เมื่อ `pointer: coarse`

### Accordion (หมวดเมนู)
```html
<div class="dc-group-title" onclick="dcToggleGroup(cat)">
  ☕ Coffee <span class="ct">(5)</span>
  <span class="dc-chev">▾</span>
</div>
<div class="dc-group-body" id="dcg-coffee">
  <!-- รายการเมนู -->
</div>
```
`.dc-group-title.dc-collapsed .dc-chev { transform: rotate(-90deg) }`  
`.dc-group-body.dc-collapsed { display: none }`  
สถานะเก็บใน `localStorage['pengtang_dc_collapsed']`

### Modal มาตรฐาน
```html
<div class="dc-modal-bd">              <!-- backdrop: position:fixed, overflow-y:auto -->
  <div class="dc-modal">              <!-- flex column, max-height: calc(100vh - 40px) -->
    <div class="dc-modal-head">       <!-- flex-shrink: 0, padding: 22px 24px 14px -->
      <h3>ชื่อ modal</h3>
      <button class="dc-x" onclick="dcCloseModal()">✕</button>
    </div>
    <div class="dc-modal-scroll">     <!-- flex: 1 1 auto, min-height: 0, overflow-y: auto -->
      <!-- เนื้อหา form ทั้งหมด -->
    </div>
    <div class="dc-modal-foot">       <!-- flex-shrink: 0, border-top -->
      <button class="dc-btn">ยกเลิก</button>
      <button class="dc-btn primary">บันทึก</button>
    </div>
  </div>
</div>
```
> **⚠️ อย่าให้คลิก backdrop ปิด modal** — ผู้ใช้กรอกข้อมูลอยู่จะสูญหาย  
> ปิดได้ทาง: ปุ่ม ✕ · ปุ่มยกเลิก · Esc เท่านั้น  
> (ดู CLAUDE.md หัวข้อ "มาตรฐานการทดสอบ (QA)")

### Polar Chart (ต้นทุนเครื่องดื่ม)
```css
.dc-polar-canvas-wrap {
  position: relative;
  width: clamp(240px, min(92vw, 62vh), 820px);  /* ใหญ่สมส่วน PC/มือถือ */
  aspect-ratio: 1 / 1;
  margin: 0 auto;
}
@media (max-height: 560px) {
  .dc-polar-canvas-wrap { width: clamp(200px, min(80vw, 70vh), 520px); }
}
```
Chart.js options: `responsive: true, maintainAspectRatio: false`  
**ต้อง `dcPolarChart.destroy()` ก่อนสร้างใหม่เสมอ** (ป้องกัน memory leak + กราฟซ้อน)  
คลิกกลีบ → `onClick(event, elements)` → `dcSetChannel(DC_CH[elements[0].index])`

---

## 7. หลักเลื่อนหน้า / Responsive

- **เลื่อนหน้าปกติ** — `#main-content` (`overflow-y: auto`) ทำหน้าที่ scroll container หลัก  
  chart + stats + รายการเมนูไหลต่อกันตามปกติ ไม่ lock viewport ด้วย `overflow: hidden`
- **อย่า** ทำ `overflow: hidden` บน container ใหญ่จนรายการ list ไม่มีพื้นที่
- Responsive breakpoints ที่ใช้จริง:
  - `≤1024px`: grid overview เปลี่ยนเป็น 1 column
  - `≤760px`: platform cards เปลี่ยนเป็น 1 column
  - `≤720px`: dc-stat flex-basis 80px, row-top grid → 1 col
  - `≤500px`: dc-stat flex-basis 58px (1 แถว), controls compact
  - `max-height: 560px`: polar chart เล็กลง
- **เทสจอเล็กเสมอ**: `~1366×600` (โน้ตบุ๊ก) + `~390×844` (มือถือ)

---

## 8. มาตรฐาน QA

สรุปจาก CLAUDE.md หัวข้อ "มาตรฐานการทดสอบ (QA)":

| หัวข้อ | มาตรฐาน |
|---|---|
| เทสแบบผู้ใช้จริง | ใช้ `dispatchEvent` จริง ไม่เรียกฟังก์ชันตรงๆ |
| จอเล็ก | เทสทุกครั้งที่ทำ modal/overlay/dropdown บน `~1366×600` + `~390×844` |
| Edge cases | เนื้อหายาวเกิน, dropdown ชนขอบล่าง, คลิกพลาด, event flow กลาง rebuild |
| เดิน flow ครบ | เปิด → กรอก → เลือก → เลื่อน → บันทึก |
| Console | `preview_console_logs --level error` ต้องสะอาด |
| Modal | หัว/ปุ่มตรึง (`flex-shrink:0`) + เนื้อหา `min-height:0; overflow:auto` |
| Build & deploy | `python src/generate_dashboard.py --rebuild` → `cp dashboard/index.html docs/index.html` |
| แจ้งผู้ใช้ | บอกสเต็ป "กดตรงนี้ ควรเห็นแบบนี้" + เตือน **Ctrl+Shift+R** ทุกครั้ง |

---

## 9. Gotchas

### localStorage keys
| Key | ใช้ที่ | ค่า |
|---|---|---|
| `sa-theme` | ธีม UI | `'coffee'` / `'light'` / `'dark'` / `'fancy'` |
| `pengtang_drink_costs_v1` | ข้อมูลต้นทุนเครื่องดื่ม (catalog + menus) | JSON ของ `DCS` |
| `pengtang_gs_url` | Google Sheet Web App URL | URL string หรือ `''` |
| `pengtang_dc_collapsed` | สถานะหุบ/กางหมวดเมนู | `{ "coffee": true, ... }` |

### รหัสล็อก
- รหัสแก้ไขเมนู/สูตรเก็บเป็น **SHA-256 เท่านั้น**  
  ค่าใน JS: `DC_EDIT_HASH = '7faf99673e7b...'`  
  ห้ามเก็บ plaintext ในโค้ด

### Google Sheet URL
- URL ของ Apps Script Web App เก็บใน `localStorage['pengtang_gs_url']` เท่านั้น  
  **ไม่ฝังในโค้ด** ที่ push ขึ้น GitHub เพราะ URL = สิทธิ์อ่าน+เขียน Sheet  
  ถ้า URL หลุด: ไป Apps Script → Archive deployment แล้ว Deploy ใหม่ (ได้ URL ใหม่)

### ข้อมูล DCS
- `DCS` (working state) โหลดจาก localStorage ก่อน ถ้าไม่มีค่อยใช้ `DRINK_COSTS` (seed จาก JSON)  
  การแก้ไขใน UI → `dcSave()` → override seed; กด "คืนค่าจากไฟล์" → ล้าง localStorage กลับเป็น seed

### Chart.js instances
- Platform charts เก็บใน `chartInstances[canvasId]` → `.destroy()` ก่อนสร้างใหม่เสมอ  
- Polar chart ใช้ `dcPolarChart` variable เดี่ยว → `if (dcPolarChart) { dcPolarChart.destroy(); dcPolarChart = null; }` ทุกครั้งก่อน `new Chart(...)`

### inline onclick ใน Python f-string
```python
# ใน generate_dashboard.py
'onclick="showView(\\'view-bb-armory\\')"'
# → HTML output
onclick="showView('view-bb-armory')"
```
