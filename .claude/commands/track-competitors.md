วิเคราะห์กิจกรรมและการเปลี่ยนแปลงของคู่แข่งเทียบกับช่วงก่อนหน้า
แสดงผล: โปรโมชัน, คอนเทนต์, platform activity, delivery changes พร้อม push GitHub

ใช้งาน:
- `/track-competitors`          ← เปรียบเทียบ 7 วันล่าสุด (default)
- `/track-competitors --month`  ← เปรียบเทียบ 30 วันล่าสุด
- `/track-competitors --year`   ← เปรียบเทียบ 365 วันล่าสุด

## ขั้นตอน

### 1. Parse argument
- ไม่มี argument หรือ `--week` → period = "week", days = 7, label = "7 วันล่าสุด"
- `--month` → period = "month", days = 30, label = "30 วันล่าสุด"
- `--year`  → period = "year", days = 365, label = "365 วันล่าสุด"

### 2. โหลดข้อมูลคู่แข่งและ snapshots

```python
import sys, json
sys.path.insert(0, 'src')
from competitor_history import load_history
from generate_dashboard import INTEL_DATA_FALLBACK

competitors = [c for c in INTEL_DATA_FALLBACK if c['category'] == 'competitor']
snapshots = load_history(days=days*2)
print(f"พบ {len(competitors)} คู่แข่ง, {len(snapshots)} snapshots")
```

### 3. เรียก competitor-tracker-agent

ส่ง:
- `period`, `competitors`, `snapshots`
- ให้ agent ค้นหากิจกรรมล่าสุดและเปรียบเทียบกับ snapshot เก่า
- รับ tracking_data dict กลับมา

### 4. บันทึก tracking data

```python
import json
from datetime import datetime
from pathlib import Path

Path('data').mkdir(exist_ok=True)

# บันทึกแยกตาม period
output_path = f'data/competitor-tracking-{period}.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(tracking_data, f, ensure_ascii=False, indent=2)

# บันทึก latest (ใช้กับ dashboard)
with open('data/competitor-tracking-latest.json', 'w', encoding='utf-8') as f:
    json.dump(tracking_data, f, ensure_ascii=False, indent=2)

print(f'saved: {output_path}')
```

### 5. สร้าง report

บันทึกที่ `reports/competitor-tracking-{period}-YYYYMMDD.md`:

```markdown
# Competitor Tracking Report — [period_label] — [วันที่]

## Market Summary
- **Most Active**: [ร้านที่กิจกรรมมากที่สุด]
- **โปรโมชันใหม่**: [จำนวน] รายการ
- **Delivery เปลี่ยนแปลง**: [จำนวน] ร้าน
- **Key Insight**: [insight สำคัญที่สุด]

## 🔴 น่าจับตา
[ร้านที่ alert_level = high พร้อมรายละเอียด]

## รายงานแต่ละร้าน

### [ชื่อร้าน] [🔴/🟡/🟢 ตาม alert_level]
**Activity**: [high/medium/low]

**โปรโมชัน:**
- active: ...
- ใหม่ช่วงนี้: ...

**คอนเทนต์:**
- หัวข้อ: ...
- Platform: ...
- ยอดดู/engagement: ...

**Delivery:** ...

**สรุป:** ...
```

### 6. Rebuild + Deploy

```
python src/generate_dashboard.py sample-data/
copy dashboard\index.html docs\index.html
```

### 6.5 บันทึก log การอัปเดต (สำคัญ — ทำทุกครั้ง)

```
python src/update_log.py add --category intel --action track \
  --scope "ติดตามคู่แข่ง ([period])" \
  --summary "ติดตามคู่แข่ง [period_label] — [จำนวน] ร้าน" \
  --count [จำนวนคู่แข่งที่ติดตาม] \
  --detail "โปรโมชันใหม่: ..." --detail "ร้านน่าจับตา: ..."
```
(รัน `python src/generate_dashboard.py --rebuild` ใน step 6 อยู่แล้ว badge/ประวัติจะอัปเดตตาม)

### 7. Push GitHub

```
git add docs/ data/competitor-tracking-*.json reports/competitor-tracking-*.md data/update-log.json
git commit -m "Competitor tracking update ([period]) — [DATE]"
git push
```

### 8. สรุปใน chat

- period ที่วิเคราะห์ และจำนวน snapshots ที่ใช้เปรียบเทียบ
- 🔴 ร้านที่น่าจับตามากที่สุด พร้อมเหตุผล
- โปรโมชันใหม่ที่พบ
- Key insight ของช่วงนี้
- "Dashboard อัพเดทแล้ว → หน้า ติดตามคู่แข่ง"
- GitHub Pages URL
