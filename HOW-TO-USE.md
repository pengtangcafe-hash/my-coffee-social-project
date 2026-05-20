# คู่มือการใช้งาน — Coffee Social Analytics

## โปรเจคนี้ทำอะไร?

วิเคราะห์ข้อมูล Social Media (TikTok, Facebook, Instagram) ของร้านกาแฟ  
ติดตาม performance, เปรียบเทียบ platform และสอดส่องคู่แข่งในสกลนคร

---

## สิ่งที่ต้องมีก่อนเริ่ม

- **Python 3** + **pandas** (`pip install pandas`)
- **Claude Code** (เปิดใน folder `my-coffee-social-project`)

---

## คำสั่งทั้งหมด

### `/analyze` — วิเคราะห์ข้อมูล Social Media ของตัวเอง

วิเคราะห์ไฟล์ CSV จาก TikTok / Facebook / Instagram พร้อมดึง market intelligence คู่ขนาน

```
/analyze                              ← ใช้ข้อมูลใน sample-data/ (ทดลอง)
/analyze data/imports/tiktok.csv      ← วิเคราะห์ไฟล์เดียว
/analyze data/imports/Facebook/       ← วิเคราะห์ทั้ง folder
/analyze data/imports/ --refresh      ← วิเคราะห์ + ค้นหา intel ใหม่ทั้งหมด
```

**Output ที่ได้:**
- `reports/full-report-YYYYMMDD.md` — รายงานรวม Data + Market Intel
- `dashboard/index.html` — Dashboard ดูได้ใน browser
- `data/history/` — ข้อมูล snapshot เก็บสะสมไว้เทียบในอนาคต

---

### `/intel` — ค้นหา Market Intelligence

ค้นหาข้อมูลตลาดกาแฟ คู่แข่ง hashtags events อุปกรณ์ใหม่

```
/intel                                ← ค้นหา "ร้านกาแฟ สกลนคร" (default)
/intel specialty coffee               ← เปลี่ยน topic
/intel กาแฟสด นครพนม                  ← เปลี่ยนทั้ง topic และ city
/intel --refresh                      ← ค้นหาใหม่ทั้งหมด (ลบ cache เก่า)
```

**Output ที่ได้:**
- `reports/intel-YYYYMMDD.md` — รายงาน intelligence

---

### `/intel-deep` — วิเคราะห์คู่แข่งเชิงลึก 5 มิติ

วิเคราะห์คู่แข่งแต่ละร้านแบบละเอียด พร้อมเทียบกับข้อมูลเดิม

```
/intel-deep
```

**5 มิติที่วิเคราะห์:**
1. Social Presence — platforms, followers, engagement
2. Content Strategy — รูปแบบ content, hashtags, tone
3. Pricing — ราคาเมนูที่ประกาศสาธารณะ, โปรโมชัน
4. Services/Positioning — จุดขาย, กลุ่มเป้าหมาย, atmosphere
5. Reviews — Google Maps, Facebook rating, คอมเม้น

**Output ที่ได้:**
- `reports/competitor-changes-YYYYMMDD.md` — รายงานการเปลี่ยนแปลง
- `data/competitor-history/` — snapshot เก็บประวัติคู่แข่ง
- `dashboard/index.html` — อัปเดต dashboard

---

### `/compare` — เปรียบเทียบ Performance ระหว่าง Platforms

```
/compare
```

เปรียบเทียบ TikTok vs Facebook vs Instagram ว่า platform ไหน perform ดีกว่า  
**ต้องมีข้อมูลใน `data/history/` ก่อน** (รัน `/analyze` อย่างน้อย 1 ครั้ง)

**Output ที่ได้:**
- `reports/comparison-YYYYMMDD.md` — รายงานเปรียบเทียบ
- Dashboard อัปเดตอัตโนมัติ

---

## Workflow แนะนำ — เริ่มต้นใช้งาน

```
ขั้นที่ 1: เปิด Claude Code ใน folder my-coffee-social-project
ขั้นที่ 2: ดาวน์โหลดข้อมูลจาก platform ใส่ใน data/imports/
ขั้นที่ 3: /analyze data/imports/       ← วิเคราะห์ครั้งแรก
ขั้นที่ 4: /intel-deep                  ← สำรวจคู่แข่ง
ขั้นที่ 5: เปิด dashboard/index.html   ← ดูผลใน browser
```

**ทำซ้ำรายสัปดาห์:**
```
/analyze data/imports/ --refresh   ← วิเคราะห์ + อัปเดต intel
/compare                           ← เทรนด์เทียบกับสัปดาห์ก่อน
```

---

## วิธีดาวน์โหลดข้อมูลจาก Social Platforms

### TikTok
1. เข้า TikTok Studio → Analytics → Overview
2. กด "Export Data" → เลือกช่วงเวลา
3. บันทึกไฟล์ CSV ไว้ที่ `data/imports/TikTok/`

### Facebook
1. เข้า Meta Business Suite → Insights
2. กด "Export" → เลือก metrics ที่ต้องการ
3. บันทึกไฟล์ CSV ไว้ที่ `data/imports/Facebook/`

### Instagram
1. เข้า Meta Business Suite → Insights → Instagram
2. กด "Export"
3. บันทึกไฟล์ CSV ไว้ที่ `data/imports/Instagram/`

---

## โครงสร้าง Folder

```
my-coffee-social-project/
├── CLAUDE.md                   ← context โปรเจค (Claude อ่านอัตโนมัติ)
├── HOW-TO-USE.md               ← ไฟล์นี้
│
├── .claude/
│   ├── commands/
│   │   ├── analyze.md          ← logic ของ /analyze
│   │   ├── intel.md            ← logic ของ /intel
│   │   ├── intel-deep.md       ← logic ของ /intel-deep
│   │   └── compare.md          ← logic ของ /compare
│   └── agents/
│       ├── data-agent.md       ← agent วิเคราะห์ CSV
│       └── intel-agent.md      ← agent ค้นหาตลาด
│
├── sample-data/                ← ข้อมูลตัวอย่างสำหรับทดสอบ
│   ├── TikTok/
│   ├── Facebook/
│   └── Instagram/
│
├── data/
│   ├── imports/                ← วางไฟล์ CSV จริงที่นี่
│   ├── history/                ← snapshots สะสมอัตโนมัติ
│   ├── competitor-history/     ← snapshots คู่แข่งสะสมอัตโนมัติ
│   └── schema.json             ← mapping column ของแต่ละ platform
│
├── src/
│   ├── generate_dashboard.py   ← สร้าง HTML dashboard
│   ├── normalize.py (root)     ← แปลง CSV → JSON
│   ├── compare.py              ← เปรียบเทียบ platforms
│   ├── history_store.py        ← จัดการ history snapshots
│   └── competitor_history.py   ← จัดการ competitor snapshots
│
├── reports/                    ← รายงานทั้งหมด (สร้างอัตโนมัติ)
├── dashboard/                  ← HTML dashboard (เปิดใน browser)
└── docs/
    ├── intelligence-brief.md   ← framework วิเคราะห์คู่แข่ง
    └── index.html              ← dashboard สำหรับ GitHub Pages
```

---

## Dashboard — วิธีดู

เปิดไฟล์ `dashboard/index.html` ในเบราว์เซอร์ใดก็ได้  
ไม่ต้องมี server — เปิดจาก File Explorer ได้เลย

**หน้าที่มีใน Dashboard:**
| หน้า | เนื้อหา |
|------|---------|
| หน้าหลัก | ภาพรวม + เปรียบเทียบทุก platform |
| TikTok | กราฟ reach รายวัน, engagement, ตารางข้อมูล |
| Facebook | กราฟ reach, engagement, followers ใหม่ |
| Instagram | กราฟ reach, impressions, profile visits |
| ข่าวกรองตลาด | Competitor cards, Coffee trends, Events |
| ราคาเมนูกาแฟ | เปรียบเทียบราคาคู่แข่ง |
| วิเคราะห์เชิงลึก | Timeline การเปลี่ยนแปลงคู่แข่ง |

---

## Intel Agent — ข้อมูลที่ค้นหาได้

เมื่อรัน `/intel` หรือ `/analyze` ระบบจะค้นหา:

| หมวด | ตัวอย่าง |
|------|---------|
| **ร้านคู่แข่ง** | ราคาเมนู, social media activity, จุดแข็ง/อ่อน |
| **Coffee Knowledge** | เทรนด์กาแฟ 2026, hashtags ที่นิยม, content ideas |
| **Events** | Coffee Fest, barista competition, งาน expo |
| **อุปกรณ์** | เครื่องชงกาแฟใหม่, grinder, supplier โปรโมชัน |

---

## Tips การใช้งาน

**เพิ่มข้อมูลตัวอย่างเพื่อทดสอบ:**  
วาง CSV จาก TikTok/Facebook/Instagram ไว้ใน `sample-data/` แล้วรัน `/analyze`

**ค้นหาคู่แข่งเฉพาะร้าน:**  
```
/intel Amazon Coffee สกลนคร
/intel ร้านกาแฟ local
```

**ดูเทรนด์ตามเวลา:**  
รัน `/analyze` ทุกสัปดาห์ — ระบบจะ snapshot ข้อมูลสะสมไว้  
แล้วรัน `/compare` เพื่อเห็น % change

**Force ค้นหา intel ใหม่:**  
```
/analyze --refresh       ← ล้าง cache intel แล้วค้นหาใหม่
/intel --refresh         ← เฉพาะ intel ไม่มี data analysis
```

---

## คำถามที่พบบ่อย

**Q: ต้องมีข้อมูลจริงก่อนไหมถึงจะใช้ได้?**  
A: ไม่ต้อง — รัน `/intel-deep` ได้เลยเพื่อดูข้อมูลคู่แข่ง  
ส่วน `/analyze` และ `/compare` ต้องมี CSV ก่อน

**Q: ข้อมูลเก่าหายไปไหมเมื่อ import ใหม่?**  
A: ไม่หาย — ระบบ append snapshot ใหม่เข้า `data/history/` ทุกครั้ง

**Q: dashboard/index.html อัปเดตเมื่อไหร่?**  
A: อัปเดตทุกครั้งที่รัน `/analyze`, `/intel-deep`, หรือ `/compare`

**Q: รายงานเก่าหายไปไหมเมื่อสร้างใหม่?**  
A: ไม่หาย — ชื่อไฟล์มีวันที่กำกับ เช่น `full-report-20260520.md`
