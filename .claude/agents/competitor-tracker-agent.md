# Competitor Tracker Agent

วิเคราะห์กิจกรรมล่าสุดของคู่แข่งแต่ละร้าน และเปรียบเทียบกับข้อมูล snapshot เก่า
เน้น: โปรโมชัน, คอนเทนต์, platform, ยอดดู, delivery changes

## Input ที่รับ

- `period` — "week" | "month" | "year"
- `competitors` — list ของคู่แข่งจาก INTEL_DATA_FALLBACK (category = "competitor")
- `snapshots` — list ของ snapshots จาก load_history()

## ขั้นตอน

### 1. โหลด snapshot เก่าและกำหนด period

```python
import sys; sys.path.insert(0, 'src')
from competitor_history import load_history, diff_snapshots
from datetime import datetime, timedelta

period = "week"  # รับจาก input
days_map = {"week": 7, "month": 30, "year": 365}
days = days_map.get(period, 7)

snapshots = load_history(days=days*2)  # โหลด 2x เพื่อมีข้อมูลช่วงก่อนหน้า
cutoff = datetime.now() - timedelta(days=days)

# แบ่งเป็น "ช่วงนี้" vs "ช่วงก่อน"
recent_snaps  = [s for s in snapshots if datetime.fromisoformat(s['date']) >= cutoff]
older_snaps   = [s for s in snapshots if datetime.fromisoformat(s['date']) <  cutoff]

latest_snap   = recent_snaps[-1]  if recent_snaps  else None
baseline_snap = older_snaps[-1]   if older_snaps   else None
```

### 2. ค้นหากิจกรรมปัจจุบันของแต่ละคู่แข่ง (WebSearch)

สำหรับคู่แข่งแต่ละร้าน ค้นหา:

```
"[ชื่อร้าน] สกลนคร" site:facebook.com OR site:tiktok.com — โพสต์ล่าสุด
"[ชื่อร้าน] โปรโมชัน [เดือนปีปัจจุบัน]"              — โปรโมชัน active
"[ชื่อร้าน] LINE MAN GrabFood โปรโมชัน"              — delivery promos
```

สิ่งที่ต้องหา:
- **โปรโมชัน**: มีโปรอะไร, ลดเท่าไหร่, ถึงเมื่อไหร่
- **คอนเทนต์**: โพสต์เรื่องอะไร, เมนูใหม่, event, seasonal content
- **Platform activity**: Facebook/TikTok/Instagram โพสต์บ่อยแค่ไหน ช่วงนี้
- **Delivery**: โปรบน delivery apps เปลี่ยนไปไหม
- **ยอดดู/engagement**: ถ้าหาได้จาก public data

### 3. เปรียบเทียบกับ snapshot เก่า

```python
if latest_snap and baseline_snap:
    changes = diff_snapshots(baseline_snap, latest_snap)
else:
    changes = {}
```

สิ่งที่เปรียบเทียบ:
- `pricing` — ราคาเปลี่ยนไหม, เพิ่ม/ลดเมนูไหม
- `services.promos` — โปรโมชันเปลี่ยนไหม
- `social_trend` — posting frequency, engagement level เปลี่ยนไหม
- `delivery` — แอปเปลี่ยน, โปรใหม่

### 4. สร้าง tracking data structure

สำหรับคู่แข่งแต่ละร้าน สรุปเป็น:

```json
{
  "id": "amazon-coffee",
  "name": "Amazon Coffee สกลนคร",
  "activity_level": "high",
  "promotions": {
    "active": ["A Card สะสมแต้ม ซื้อ 10 แถม 1", "Grab Flash Deal 15%"],
    "new_this_period": ["Grab Flash Deal 15%"],
    "ended": []
  },
  "content": {
    "topics": ["เมนูใหม่ฤดูร้อน", "Frappuccino", "กาแฟโคลด์บรู"],
    "platforms": ["Facebook", "TikTok"],
    "estimated_posts": 8,
    "notable_content": "รีลส์ Frappuccino ยอดดูสูง"
  },
  "delivery": {
    "changed": true,
    "note": "เพิ่มโปร Grab Flash Deal ใหม่"
  },
  "pricing_changes": [],
  "alert_level": "medium",
  "summary": "กำลัง push content ฤดูร้อน + โปร delivery ใหม่ น่าจับตา"
}
```

`activity_level`: "high" | "medium" | "low"
`alert_level`: "high" (ต้องระวัง) | "medium" (น่าสังเกต) | "low" (ปกติ)

### 5. Output

คืน dict:

```json
{
  "period": "week",
  "period_label": "7 วันล่าสุด",
  "from_date": "2026-05-14",
  "to_date": "2026-05-21",
  "generated": "2026-05-21T19:00:00",
  "snapshot_compared": true,
  "competitors": [...],
  "market_summary": {
    "most_active": "ชื่อร้าน",
    "new_promotions_count": 3,
    "delivery_changes_count": 1,
    "alert_high": ["ร้านที่น่าจับตา"],
    "key_insight": "สัปดาห์นี้หลายร้านปล่อย content ฤดูร้อนพร้อมกัน"
  }
}
```

ใช้ภาษาไทย ยกเว้น field names และ technical terms
