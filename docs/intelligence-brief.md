# Intelligence Brief — Competitor Analysis
## ร้านกาแฟ สกลนคร
**อัปเดตล่าสุด:** ยังไม่มีข้อมูล (รัน /intel เพื่อเริ่มต้น)
**แหล่งที่มา:** โปรเจคใหม่ — ต้องการการค้นหาครั้งแรก

---

## วัตถุประสงค์ของ Intelligence Module

ระบบ `/intel` ในโปรเจกต์นี้มีเป้าหมาย 3 ด้าน:
1. **ติดตามคู่แข่ง** — Social media activity, content strategy, pricing, hashtags
2. **หา Market Gaps** — สิ่งที่คู่แข่งยังไม่ทำ เพื่อโอกาสทางการตลาด
3. **แจ้งเตือน Trends** — Hashtag trends, Coffee industry news, equipment innovation

---

## Framework การวิเคราะห์คู่แข่ง (5 มิติหลัก)

### มิติ 1: Social Media Presence
- แพลตฟอร์มที่ใช้ (Facebook / TikTok / Instagram / LINE OA / YouTube)
- แพลตฟอร์มไหน Active มากที่สุด / ทิ้งร้าง
- จำนวน Followers/Likes, Engagement Rate, ความถี่โพส
- โพสไหนมี Engagement สูงสุด
- ทิศทาง Comment (บวก/ลบ/ไม่มี)

### มิติ 2: Content Strategy
- รูปแบบ: วิดีโอ Latte Art, Barista Process, Reels, รูปภาพ+caption, Live, Stories
- Theme: โปรโมชัน, เมนูใหม่, Educational Brewing, บรรยากาศร้าน, ทีม Barista, Seasonal
- โทนการสื่อสาร: ทางการ vs กันเอง, ใช้ภาษาอีสานไหม, มี Presenter/Influencer
- Hashtags ที่ใช้บ่อย

### มิติ 3: Pricing & Promotions
- ราคาเมนูที่ประกาศในโซเชียล (เอสเปรสโซ, ลาเต้, โคลด์บรู, Signature ฯลฯ)
- โปรโมชัน (สมาชิก, Happy Hour, แพ็กเกจ, บัตรสะสมแต้ม)
- ราคาเทียบกับตลาด
- มีบัตรสมาชิก / Loyalty Program

### มิติ 4: Services & Positioning
- เมนูหลักที่เน้น
- Tagline / จุดขาย (ราคา, บาริสต้าเชี่ยวชาญ, specialty beans, บรรยากาศ)
- กลุ่มเป้าหมายที่ชัด (วัยรุ่น, คนทำงาน, นักเรียน/นักศึกษา, ครอบครัว)
- เวลาเปิด-ปิด / วันหยุด / ที่นั่ง

### มิติ 5: Reputation & Reviews
- Google Maps (ดาว, จำนวนรีวิว, คอมเม้น)
- รีวิวใน Facebook / TikTok / Wongnai
- วิธีตอบรีวิวแง่ลบ
- ช่องทาง Order (Walk-in / LINE / GrabFood / FoodPanda)

---

## ประเภทคู่แข่งในตลาดร้านกาแฟ สกลนคร

### กลุ่ม 1: Chain / Franchise
| ร้าน | ลักษณะ |
|------|--------|
| Amazon Coffee (PTT) | Chain ใหญ่สุด ราคาเข้าถึงได้ มีทั่วทุกปั๊ม |
| Inthanin (PTT) | Premium chain จาก PTT เน้น specialty beans |
| True Coffee | Chain ในห้างสรรพสินค้า |
| Wawee Coffee | Chain เชียงใหม่ขยายไทยทั้งประเทศ |

### กลุ่ม 2: Local Independent Cafe
- ร้านกาแฟสด local ที่มีเอกลักษณ์เฉพาะ
- Specialty Coffee ที่เน้น single origin beans
- Cafe + Co-working space

### กลุ่ม 3: Street / Take Away
- กาแฟถุง / กาแฟสดตลาด
- รถกาแฟ mobile

---

## Hashtag Master List (ต้องอัปเดตหลังรัน /intel)

### Local (สกลนคร)
`#กาแฟสกลนคร` `#คาเฟ่สกลนคร` `#ร้านกาแฟสกลนคร`

### ระดับประเทศ (High Engagement)
`#กาแฟไทย` `#specialty coffee` `#latteart` `#barista`
`#คาเฟ่ไทย` `#coffeeaddict` `#coffeelovers`

### Trend 2026
`#SpecialtyCoffee` `#ThirdWaveCoffee` `#ColdBrew` `#NitroColdbrew`

---

## Market Gaps (ต้องอัปเดตหลังรัน /intel-deep)

| Gap | โอกาส |
|-----|--------|
| TikTok Barista Process | คนดูชอบ behind-the-scenes การทำกาแฟ |
| Specialty Bean Education | อธิบาย single origin/processing method สร้าง authority |
| Latte Art Reels | Visual content สูง engagement |
| Coffee Pairing Content | กาแฟ + ขนม + อาหาร — ดึงลูกค้าใหม่ |
| LINE OA + Loyalty | บัตรสะสมแต้มดิจิทัล ลด friction |
| Google Business Profile | SEO "ร้านกาแฟสกลนคร" ต้องครอง |

---

## โครงสร้างที่มีอยู่แล้วใน .claude/

```
.claude/
  commands/
    intel.md      ← /intel [topic] [city] command
    analyze.md    ← /analyze FILE
    compare.md    ← /compare
    intel-deep.md ← /intel-deep
  agents/
    intel-agent.md   ← agent ค้นหา+ส่ง JSON structure
    data-agent.md
```

Intel-agent ส่งคืน JSON array ที่มี fields:
`id`, `category`, `title`, `summary`, `source_url`, `tags`, `relevance`,
`detail`, `pricing` (ราคาเมนูกาแฟ), `strengths`, `promotions`, `social_trend`

---

*ไฟล์นี้เป็น template เริ่มต้น รัน `/intel ร้านกาแฟ สกลนคร` เพื่อเติมข้อมูลจริง*
