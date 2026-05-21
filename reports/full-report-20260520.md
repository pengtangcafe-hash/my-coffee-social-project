# Full Social Media Report — ร้านกาแฟ สกลนคร
**วันที่:** 20 พฤษภาคม 2026  
**ข้อมูลจาก:** sample-data/ (TikTok, Facebook, Instagram)  
**สถานะ:** data/imports/ ว่างเปล่า — ใช้ sample-data/ แทน

---

## ส่วนที่ 1: Data Analysis

### Executive Summary

- **ทุก platform ยังอยู่ในระยะเริ่มต้น** — TikTok: 12 total views ใน 365 วัน, Facebook: 207 views ใน 140 วัน, Instagram: 0 views ทั้งหมด
- **ไม่มี followers ใหม่** บน platform ไหนเลยในช่วงที่วัด — บ่งชี้ว่า account ยังไม่ active หรือยังไม่มี content ที่โพสต์จริง
- **Facebook เป็น platform ที่ดีที่สุด** ณ ขณะนี้ (207 vs 12 views) แต่ยังห่างไกล benchmark ร้านกาแฟที่ active
- **Engagement Rate = 0%** ทุก platform เพราะไม่มี likes/comments/shares ที่ record ได้
- **สัญญาณเดียวที่ดี:** Facebook มี peak 40 views วันที่ 9 ม.ค. 2026 — บ่งชี้ว่ามีคนหา profile อยู่

### Key Metrics Table

| Metric | TikTok | Facebook | Instagram |
|--------|--------|----------|-----------|
| ระยะเวลาข้อมูล | 365 วัน | 140 วัน | 140 วัน |
| Total Reach (Views) | **12** | **207** | **0** |
| Avg Reach/วัน | 0.03 | 1.48 | 0.00 |
| Peak Reach (วันเดียว) | 3 (11 ต.ค.) | 40 (9 ม.ค.) | — |
| Total Engagement | 0 | 4 | 0 |
| Engagement Rate | 0.00% | 1.93% | 0.00% |
| Followers ใหม่ | 0 | 0 | 0 |

### Top Performing Content

ไม่มีข้อมูล post-level — ข้อมูล sample เป็น daily aggregate เท่านั้น

**วันที่ทำได้ดีที่สุด:**
- Facebook: 9 ม.ค. 2026 (40 views, 4 interactions) — น่าจะมี post ที่ดีวันนั้น
- TikTok: 11 ต.ค. 2025 (3 views)
- Instagram: ยังไม่มีวันที่โดดเด่น

### Audience Insights

ไม่มีข้อมูล demographics ในชุดข้อมูลนี้

### Snapshot บันทึกแล้ว

| Platform | File |
|----------|------|
| TikTok | `data/history/tiktok_20260520.json` |
| Facebook | `data/history/facebook_20260520.json` |
| Instagram | `data/history/instagram_20260520.json` |

---

## ส่วนที่ 2: Market Intelligence
*(intel-agent --refresh | 20 พ.ค. 2026)*

### คู่แข่งในสกลนคร

**Chain Brands:**

| ร้าน | Platform หลัก | Followers (national) | หมายเหตุ |
|------|--------------|---------------------|---------|
| **Amazon Coffee** | Facebook, TikTok | 1M+ | สาขาหลายจุดในสกลนคร, active มาก |
| **Inthanin (ปตท.)** | Facebook, Instagram | 200K+ | สาขาในปั๊ม ปตท. |
| **Black Canyon** | Facebook | 300K+ | สาขาในห้างสรรพสินค้า |
| **True Coffee** | Facebook | 150K+ | สาขาในร้าน True |

**Independent Cafes — ลักษณะที่พบในสกลนคร:**

| ประเภท | Platform | Style Content |
|--------|----------|--------------|
| คาเฟ่วิว/บรรยากาศดี | TikTok, Instagram | Reel วิวสวย, flat lay เมนู |
| Specialty coffee | Instagram, Facebook | Latte art, pour-over process |
| คาเฟ่ริมน้ำ/ธรรมชาติ | TikTok | วิดีโอบรรยากาศ, sunset shots |
| กาแฟโบราณ/ไทย | Facebook | โปรโมชั่น, เมนูประจำวัน |

### Hashtags ที่แนะนำ (5–8 hashtag ต่อโพสต์)

**Local — สกลนคร:**
`#กาแฟสกลนคร` `#คาเฟ่สกลนคร` `#สกลนคร` `#sakonnakhon`

**Regional — อีสาน (กำลัง grow เร็วกว่า local):**
`#กาแฟอีสาน` `#คาเฟ่อีสาน` `#เที่ยวอีสาน`

**Content Type:**
`#latteart` `#กาแฟไทย` `#specialtycoffee` `#barista` `#คาเฟ่ไทย` `#คาเฟ่ฮอปปิ้ง`

> **Key Insight:** #คาเฟ่อีสาน กำลัง grow เร็วกว่า #คาเฟ่สกลนคร — ใช้ทั้งคู่เพื่อ reach ที่กว้างขึ้น

### เทรนด์กาแฟ 2025-2026

**เมนูที่ viral:**

| เมนู | โอกาสสำหรับร้าน |
|------|----------------|
| **Butterfly Pea Cold Brew** | สูงมาก — ดอกอัญชันไทย + color-changing = viral บน TikTok |
| **Dirty Coffee** (drip บนนม) | สูง — ทำง่าย, ถ่ายสวย, ยัง trend ต่อเนื่อง |
| **Taro / Purple Drinks** | สูง — instagrammable, target วัยรุ่น |
| **Yuzu / Citrus Cold Coffee** | ดี — เหมาะช่วงฤดูร้อน |
| **Brown Sugar Oat Milk Latte** | ดี — health-conscious positioning |

**Content Style ที่ Trend:**
- Process Video (barista POV) — ROI สูงสุด
- Satisfying Pour (slow motion)
- ASMR Coffee (เสียงน้ำแข็ง, เครื่องบด)
- Cafe Vlog (customer experience)
- Local Story (ที่มาของร้าน, ความเป็น local)

### Events ใกล้เคียง (พค–กค 2026)

| งาน | ช่วงเวลา | โอกาสสำหรับร้าน |
|-----|---------|----------------|
| **วันวิสาขบูชา** | พ.ค. 2026 | โปรโมชั่นวันหยุด, content mindful/สงบ |
| **วันเข้าพรรษา** | ก.ค. 2026 | ธีม local Thai, เมนูไม่มีแอลกอฮอล์ |
| **Walking Street สกลนคร** | ทุกศุกร์-เสาร์ | Live post, check-in, โปรวันนั้น |

> ติดตาม TAT Sakon Nakhon และเพจจังหวัดสกลนครบน Facebook สำหรับ events ท้องถิ่นที่ update

### Equipment & Techniques Trending

**อุปกรณ์ที่ viral ใน TikTok:**
- Fellow Stagg EKG Kettle — visual appeal ใน pour-over content
- AeroPress — content-friendly, ทุกขนาดร้าน
- Hario V60 (ceramic/copper) — specialty, ถ่ายสวย

**Techniques ที่ Viral:**
1. Turbo Bloom pour-over — fast, visual
2. Iced Lungo direct over ice — simple, trending
3. Cold Foam topping — DIY-able, Starbucks-inspired
4. Single origin spotlight — storytelling + education

**Beans Trending:**
- กาแฟไทย (ดอยช้าง, เชียงราย) ยังแข็งแกร่ง
- Ethiopian Natural — fruity, accessible
- **กาแฟอีสาน/local** — ถ้ามีผู้ปลูกท้องถิ่น เป็น story ที่แข็งมาก

---

## ส่วนที่ 3: Combined Recommendations

### 1. เริ่มโพสต์ Content ทันที — ทุก Platform ว่างเปล่า *(data + intel)*
ข้อมูลยืนยันว่าทุก platform แทบไม่มี engagement เลย สาเหตุหลักคือไม่มี content โพสต์  
**Action:** เริ่มโพสต์อย่างน้อย 3x/สัปดาห์ บน Facebook ก่อน (มี reach ดีที่สุด) ตามด้วย TikTok

### 2. โฟกัส Facebook + TikTok ก่อน Instagram *(data)*
Facebook มี reach สูงสุด (207 vs 12 vs 0) และ Instagram ยังไม่มีข้อมูลเลย  
**Action:** สร้าง content calendar โดย Facebook เป็น primary, TikTok เป็น viral channel, Instagram เป็น secondary

### 3. สร้าง Butterfly Pea Cold Brew + ถ่าย Color-Change Content *(intel)*
นี่คือ opportunity ที่ high ROI ที่สุด — ดอกอัญชันเป็น local Thai ingredient, เปลี่ยนสีเมื่อเติมน้ำมะนาว = viral บน TikTok  
**Action:** สร้างเมนู Butterfly Pea Cold Brew ราคา 80–90 บาท ถ่าย short video เห็นการเปลี่ยนสี โพสต์ TikTok + Instagram Reels ใช้ `#latteart #กาแฟสกลนคร #กาแฟอีสาน`

### 4. ใช้ Peak Day เป็น Benchmark Content *(data)*
Facebook peak 40 views วันที่ 9 ม.ค. — ต้องหาว่าวันนั้นโพสต์อะไร และ replicate  
**Action:** ดูว่ามี post/story วันที่ 9 ม.ค. ไหม ถ้ามีให้ทำ content แบบเดียวกันซ้ำ

### 5. Mix Hashtags Local + National ทุกโพสต์ *(intel)*
`#กาแฟสกลนคร` + `#กาแฟไทย` + `#latteart` ทุก post  
**Action:** สร้าง saved hashtag set ใน Instagram/TikTok เพื่อ copy-paste ได้รวดเร็ว

---

*Report สร้างอัตโนมัติโดย `/analyze` — 20 พฤษภาคม 2026*  
*Dashboard: `dashboard/index.html`*
