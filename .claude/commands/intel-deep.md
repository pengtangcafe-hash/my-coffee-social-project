วิเคราะห์คู่แข่งเชิงลึก 5 มิติ: Social Presence, Content Strategy, Pricing, Services/Positioning, Reviews

ขั้นตอน:

1. โหลด context จาก:
   - docs/intelligence-brief.md (framework + ข้อมูลคู่แข่งหลัก)
   - reports/intel-summary-*.md ทุกไฟล์ที่มีอยู่ (ถ้ามี)
   - reports/intel-*.md ล่าสุด

2. ค้นหาคู่แข่งแต่ละราย 5 มิติ โดยใช้ WebSearch สำหรับข้อมูลที่ไม่มีใน context:
   - มิติ 1 — Social Presence: platforms ที่ใช้, followers/likes, posting frequency, engagement level
   - มิติ 2 — Content Strategy: content type, tone, hashtags ที่ใช้, viral content ที่พบ
   - มิติ 3 — Pricing: ราคาเมนูที่ประกาศสาธารณะ, โปรโมชัน, แพ็กเกจ
   - มิติ 4 — Services/Positioning: เมนูหลัก, จุดขาย, tagline, กลุ่มเป้าหมาย, atmosphere
   - มิติ 5 — Reviews: Google Maps rating, Facebook reviews, คอมเม้น notable

   ค้นหาใหม่เฉพาะคู่แข่งที่ข้อมูลอาจเก่า (>7 วัน) หรือขาดหายไปในบางมิติ

3. เรียก save_snapshot() บันทึก snapshot ใหม่:
   ```python
   import sys; sys.path.insert(0, 'src')
   from competitor_history import save_snapshot, load_history, diff_snapshots
   from generate_dashboard import INTEL_DATA_FALLBACK
   competitors = [c for c in INTEL_DATA_FALLBACK if c['category'] == 'competitor']
   filepath = save_snapshot(competitors, source='intel-deep-command')
   print(f'saved: {filepath}')
   ```

4. เปรียบเทียบกับ snapshot ก่อนหน้า (ถ้ามี):
   ```python
   snaps = load_history(days=90)
   if len(snaps) >= 2:
       changes = diff_snapshots(snaps[-2], snaps[-1])
       print(changes)
   ```

5. สร้าง reports/competitor-changes-YYYYMMDD.md โดยใช้ format:

   ```markdown
   # Competitor Changes Report — [วันที่]
   
   ## สรุปการเปลี่ยนแปลง
   | ร้าน | สถานะ | การเปลี่ยนแปลง |
   |------|--------|----------------|
   | ชื่อ | ↑ เพิ่มขึ้น / ↓ ลดลง / ~ คงเดิม / ● ใหม่ | รายละเอียด |
   
   ## รายละเอียดแต่ละร้าน
   ### [ชื่อร้าน] [badge 🔴🟡🟢 ตามระดับการเปลี่ยนแปลง]
   - 📱 Social: ...
   - 🎬 Content: ...
   - 💰 Pricing: ...
   - 🎯 Positioning: ...
   - ⭐ Reviews: ...
   ```

   - 🔴 สูง = มีการเปลี่ยนแปลง 3+ fields หรือพบคู่แข่งใหม่
   - 🟡 กลาง = เปลี่ยนแปลง 1-2 fields
   - 🟢 ต่ำ = ไม่มีการเปลี่ยนแปลง

6. อัปเดต dashboard:
   ```
   python src/generate_dashboard.py sample-data/
   ```
   แล้ว copy:
   ```
   copy dashboard\index.html docs\index.html
   ```

7. Git:
   ```
   git add docs/ reports/competitor-changes-*.md data/competitor-history/
   git commit -m "Competitor deep analysis [DATE]"
   git push
   ```

8. สรุปใน chat:
   - จำนวนคู่แข่งที่วิเคราะห์
   - คู่แข่งที่มีการเปลี่ยนแปลงมากที่สุด (พร้อม badge)
   - path ของ report
   - "Dashboard + docs/ อัปเดตแล้ว"

ใช้ภาษาไทยในรายงาน ยกเว้น technical terms
