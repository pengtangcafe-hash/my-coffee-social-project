# คู่มือการใช้งาน — Coffee Social Analytics

## โปรเจคนี้ทำอะไร?

วิเคราะห์ข้อมูล Social Media (TikTok, Facebook, Instagram) ของร้านกาแฟ  
ติดตาม performance, เปรียบเทียบ platform, สอดส่องคู่แข่ง และข้อมูล Delivery Apps ในสกลนคร

---

## Links สำคัญ

| | URL |
|---|---|
| **Dashboard (online)** | https://pengtangcafe-hash.github.io/my-coffee-social-project/ |
| **GitHub Repo** | https://github.com/pengtangcafe-hash/my-coffee-social-project |
| **Dashboard (local)** | `http://localhost:8099/index.html` (ต้องเปิด Claude Code) |

---

## สิ่งที่ต้องมีก่อนเริ่ม

- **Python 3** + dependencies: `pip install -r requirements.txt`
- **Claude Code** (เปิดใน folder `my-coffee-social-project`)
- **ไฟล์ `.env`** (ถ้าต้องการดึงข้อมูลจาก API อัตโนมัติ — ดู `docs/API-SETUP.md`)

---

## คำสั่ง Update (อัพเดทข้อมูล + Push GitHub อัตโนมัติ)

### `/update-all` — อัพเดทครบทุกอย่าง
ดึงข้อมูลจาก API → วิเคราะห์ Social → ข่าวกรอง → ราคา → เชิงลึก → push GitHub  
**ต้องมี `.env` ที่ตั้งค่า API credentials แล้ว**

### `/update-overview` — อัพเดทภาพรวม Social (จาก CSV ที่ดาวน์โหลดมือ)
วางไฟล์ CSV ใน `data/imports/` ก่อน แล้วรันคำสั่งนี้  
วิเคราะห์ Social Media → push GitHub  
**ใช้เมื่อ: ดาวน์โหลด CSV จาก TikTok/Facebook/Instagram เอง**

### `/update-market` — อัพเดทข้อมูลตลาด (ไม่ต้องมี CSV)
ข่าวกรองตลาด + ราคากลาง + วิเคราะห์คู่แข่งเชิงลึก → push GitHub  
**ใช้เมื่อ: อยากอัพเดทตลาดโดยไม่มีข้อมูล Social ใหม่**

### `/update-intel` — อัพเดทแค่ข่าวกรอง
ค้นหาข้อมูลตลาด คู่แข่ง delivery trends → push GitHub

### `/update-pricing` — อัพเดทแค่ราคากลาง
ค้นหาราคาเมนูล่าสุดของคู่แข่งทุกร้าน → push GitHub

### `/update-deep` — อัพเดทแค่เชิงลึก
วิเคราะห์คู่แข่ง 6 มิติ (รวม Delivery) → push GitHub

---

## คำสั่งวิเคราะห์ (ไม่ push GitHub)

### `/analyze` — วิเคราะห์ข้อมูล Social Media ของตัวเอง

```
/analyze                              ← ใช้ข้อมูลใน sample-data/ (ทดลอง)
/analyze data/imports/tiktok.csv      ← วิเคราะห์ไฟล์เดียว
/analyze data/imports/Facebook/       ← วิเคราะห์ทั้ง folder
/analyze data/imports/ --refresh      ← วิเคราะห์ + ค้นหา intel ใหม่ทั้งหมด
```

### `/intel` — ค้นหา Market Intelligence + Delivery Trends

```
/intel                                ← ค้นหา "ร้านกาแฟ สกลนคร" (default)
/intel specialty coffee               ← เปลี่ยน topic
/intel กาแฟสด นครพนม                  ← เปลี่ยนทั้ง topic และ city
/intel --refresh                      ← ค้นหาใหม่ทั้งหมด (ลบ cache เก่า)
```

### `/intel-deep` — วิเคราะห์คู่แข่งเชิงลึก 6 มิติ

**6 มิติที่วิเคราะห์:**
1. Social Presence — platforms, followers, engagement
2. Content Strategy — รูปแบบ content, hashtags, tone
3. Pricing — ราคาเมนู, โปรโมชัน
4. Services/Positioning — จุดขาย, กลุ่มเป้าหมาย, atmosphere
5. Reviews — Google Maps, Facebook rating, คอมเม้น
6. **Delivery Apps** — แอปที่ใช้, โปรโมชัน, peak hours *(ใหม่)*

### `/compare` — เปรียบเทียบ Performance ระหว่าง Platforms
เปรียบเทียบ TikTok vs Facebook vs Instagram  
**ต้องมีข้อมูลใน `data/history/` ก่อน** (รัน `/analyze` อย่างน้อย 1 ครั้ง)

---

## Workflow แนะนำ

### เริ่มต้นครั้งแรก (ยังไม่มี API)
```
1. ดาวน์โหลด CSV จาก TikTok/Facebook/Instagram ใส่ใน data/imports/
2. /update-overview        ← วิเคราะห์ Social + push GitHub
3. /update-market          ← อัพเดทตลาด + push GitHub
```

### รายสัปดาห์ (อัตโนมัติ — ตั้งไว้แล้ว)
```
ทุกวันจันทร์ 04:01 น.  /update-market รันอัตโนมัติผ่าน Remote Routine
```

### รายสัปดาห์ (ทำมือ เมื่อมี CSV ใหม่)
```
1. ดาวน์โหลด CSV ใหม่จาก platform ใส่ใน data/imports/
2. /update-overview        ← อัพเดท Social overview
```

### เมื่อตั้งค่า API แล้ว (ไม่ต้อง Export CSV มืออีกต่อไป)
```
/update-all                ← ดึงข้อมูลจาก API + ทุกอย่างเลย
```

---

## ดึงข้อมูลจาก API (อัตโนมัติ)

แทนการ Export CSV จาก platform ด้วยมือ:

```bash
# ติดตั้ง
pip install -r requirements.txt
copy .env.example .env
# แก้ไข .env ใส่ credentials จริง

# ทดสอบ
python src/fetch_social.py --days 7

# ดึงเฉพาะ platform
python src/fetch_social.py --facebook
python src/fetch_social.py --instagram
python src/fetch_social.py --tiktok
```

**ดูวิธีขอ API credentials:** `docs/API-SETUP.md`

---

## วิธีดาวน์โหลดข้อมูล CSV จาก Platform (กรณีไม่ใช้ API)

### TikTok
1. TikTok Studio → Analytics → Overview
2. กด "Export Data" → เลือกช่วงเวลา
3. บันทึกไฟล์ CSV ไว้ที่ `data/imports/TikTok/`

### Facebook
1. Meta Business Suite → Insights
2. กด "Export" → เลือก metrics
3. บันทึกไฟล์ CSV ไว้ที่ `data/imports/Facebook/`

### Instagram
1. Meta Business Suite → Insights → Instagram
2. กด "Export"
3. บันทึกไฟล์ CSV ไว้ที่ `data/imports/Instagram/`

---

## Dashboard — หน้าที่มี

| หน้า | เนื้อหา |
|------|---------|
| ภาพรวม | ภาพรวม + เปรียบเทียบทุก platform |
| TikTok | กราฟ reach รายวัน, engagement, ตารางข้อมูล |
| Facebook | กราฟ reach, engagement, followers ใหม่ |
| Instagram | กราฟ reach, impressions, profile visits |
| ข่าวกรองตลาด | Competitor cards, Coffee trends, Events, **Delivery Apps** |
| ราคากลางร้านกาแฟ | เปรียบเทียบราคาคู่แข่ง |
| วิเคราะห์เชิงลึก | Timeline คู่แข่ง + **Delivery & Food Apps section** |

---

## โครงสร้าง Folder

```
my-coffee-social-project/
├── CLAUDE.md                     ← context โปรเจค (Claude อ่านอัตโนมัติ)
├── HOW-TO-USE.md                 ← ไฟล์นี้
├── requirements.txt              ← Python dependencies
├── .env.example                  ← template credentials (copy เป็น .env)
│
├── .claude/
│   └── commands/
│       ├── analyze.md            ← /analyze
│       ├── intel.md              ← /intel
│       ├── intel-deep.md         ← /intel-deep
│       ├── compare.md            ← /compare
│       ├── update-all.md         ← /update-all
│       ├── update-overview.md    ← /update-overview
│       ├── update-market.md      ← /update-market
│       ├── update-intel.md       ← /update-intel
│       ├── update-pricing.md     ← /update-pricing
│       └── update-deep.md        ← /update-deep
│
├── src/
│   ├── fetch_social.py           ← ดึงข้อมูลจาก API
│   ├── api/
│   │   ├── meta_api.py           ← Facebook + Instagram API
│   │   └── tiktok_api.py         ← TikTok API
│   ├── generate_dashboard.py     ← สร้าง HTML dashboard
│   ├── normalize.py              ← แปลง CSV → JSON
│   ├── compare.py                ← เปรียบเทียบ platforms
│   ├── history_store.py          ← จัดการ history snapshots
│   └── competitor_history.py     ← จัดการ competitor snapshots
│
├── sample-data/                  ← ข้อมูลตัวอย่างสำหรับทดสอบ
├── data/
│   ├── imports/                  ← วางไฟล์ CSV จริงที่นี่
│   ├── history/                  ← snapshots สะสมอัตโนมัติ
│   ├── competitor-history/       ← snapshots คู่แข่งสะสมอัตโนมัติ
│   └── schema.json               ← mapping column ของแต่ละ platform
│
├── reports/                      ← รายงานทั้งหมด (สร้างอัตโนมัติ)
├── dashboard/                    ← HTML dashboard (local)
└── docs/
    ├── index.html                ← dashboard สำหรับ GitHub Pages
    ├── API-SETUP.md              ← คู่มือขอ API credentials
    └── intelligence-brief.md     ← framework วิเคราะห์คู่แข่ง
```

---

## คำถามที่พบบ่อย

**Q: ต้องมี API credentials ก่อนไหมถึงจะใช้ได้?**  
A: ไม่ต้อง — ใช้ `/update-market`, `/intel-deep` ได้เลย ไม่ต้องมี CSV หรือ API  
ส่วน `/update-overview` และ `/update-all` ต้องมีข้อมูลก่อน

**Q: ข้อมูลเก่าหายไปไหมเมื่อ import ใหม่?**  
A: ไม่หาย — ระบบ append snapshot ใหม่เข้า `data/history/` ทุกครั้ง

**Q: dashboard/index.html อัพเดทเมื่อไหร่?**  
A: อัพเดทอัตโนมัติทุกครั้งที่รัน update commands

**Q: GitHub Pages อัพเดทเมื่อไหร่?**  
A: ทุกครั้งที่รัน update commands — ทุก command จบด้วย git push อัตโนมัติ

**Q: Routine อัตโนมัติทำงานยังไง?**  
A: ตั้ง Remote Routine ไว้แล้ว — `/update-market` รันทุกวันจันทร์ 04:01 น.  
ทำงานบน Anthropic cloud แม้ปิดคอมอยู่
