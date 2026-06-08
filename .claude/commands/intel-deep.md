วิเคราะห์คู่แข่งเชิงลึก **6 มิติ**: Social Presence, Content Strategy, Pricing, Services/Positioning, Reviews, **Delivery Apps**

ขั้นตอน:

1. โหลด context จาก:
   - docs/intelligence-brief.md (framework + ข้อมูลคู่แข่งหลัก)
   - reports/intel-summary-*.md ทุกไฟล์ที่มีอยู่ (ถ้ามี)
   - reports/intel-*.md ล่าสุด

2. ค้นหาคู่แข่งแต่ละราย **6 มิติ** โดยใช้ WebSearch สำหรับข้อมูลที่ไม่มีใน context:
   - มิติ 1 — Social Presence: platforms ที่ใช้, followers/likes, posting frequency, engagement level
   - มิติ 2 — Content Strategy: content type, tone, hashtags ที่ใช้, viral content ที่พบ
   - มิติ 3 — Pricing: ราคาเมนูที่ประกาศสาธารณะ, โปรโมชัน, แพ็กเกจ
   - มิติ 4 — Services/Positioning: เมนูหลัก, จุดขาย, tagline, กลุ่มเป้าหมาย, atmosphere
   - มิติ 5 — Reviews: Google Maps rating, Facebook reviews, คอมเม้น notable
   - **มิติ 6 — Delivery Apps**: ค้นหาด้วย WebSearch:
     - "[ชื่อร้าน] LINE MAN" / "[ชื่อร้าน] GrabFood" / "[ชื่อร้าน] ShopeeFood"
     - ดูว่าร้านอยู่บนแพลตฟอร์มไหนบ้าง
     - โปรโมชัน delivery ที่ active (ส่วนลด, ส่งฟรี, Flash Sale)
     - ช่วงเวลา peak ที่ลูกค้านิยมสั่ง (ถ้าหาได้)
     - Customer behavior หรือ review เรื่อง delivery

   ค้นหาใหม่เฉพาะคู่แข่งที่ข้อมูลอาจเก่า (>7 วัน) หรือขาดหายไปในบางมิติ

3. **อัพเดทข้อมูล delivery ในโค้ด** สำหรับคู่แข่งแต่ละราย:
   เปิด `src/generate_dashboard.py` หาส่วน `INTEL_DATA_FALLBACK`
   แต่ละ competitor dict มี field `"delivery"` — อัพเดทด้วยข้อมูลใหม่ที่ค้นพบ:
   ```python
   "delivery": {
       "primary_app": "LINE MAN",           # แอปหลักที่ร้านใช้/ลูกค้านิยม
       "apps": ["LINE MAN", "GrabFood"],     # ทุกแอปที่พบ
       "peak_hours": "...",                  # ช่วงเวลา peak
       "active_promos": ["..."],             # โปรโมชันที่ active ตอนนี้
       "notes": "..."                        # ข้อสังเกตอื่นๆ
   }
   ```
   ถ้าหาข้อมูลไม่ได้ให้ใส่ค่า default:
   ```python
   "delivery": {
       "primary_app": "LINE MAN",
       "apps": ["LINE MAN"],
       "peak_hours": "ยังไม่มีข้อมูล",
       "active_promos": [],
       "notes": "ยังไม่มีข้อมูลเพียงพอ"
   }
   ```

4. เรียก save_snapshot() บันทึก snapshot ใหม่:
   ```python
   import sys; sys.path.insert(0, 'src')
   from competitor_history import save_snapshot, load_history, diff_snapshots
   from generate_dashboard import INTEL_DATA_FALLBACK
   competitors = [c for c in INTEL_DATA_FALLBACK if c['category'] == 'competitor']
   filepath = save_snapshot(competitors, source='intel-deep-command')
   print(f'saved: {filepath}')
   ```

5. เปรียบเทียบกับ snapshot ก่อนหน้า (ถ้ามี):
   ```python
   snaps = load_history(days=90)
   if len(snaps) >= 2:
       changes = diff_snapshots(snaps[-2], snaps[-1])
       print(changes)
   ```

6. สร้าง reports/competitor-changes-YYYYMMDD.md โดยใช้ format:

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
   - 🛵 Delivery: แอปหลัก · โปรโมชัน · Peak hours
   ```

   - 🔴 สูง = มีการเปลี่ยนแปลง 3+ fields หรือพบคู่แข่งใหม่
   - 🟡 กลาง = เปลี่ยนแปลง 1-2 fields
   - 🟢 ต่ำ = ไม่มีการเปลี่ยนแปลง

7. อัปเดต dashboard:
   ```
   python src/generate_dashboard.py sample-data/
   ```
   แล้ว copy:
   ```
   copy dashboard\index.html docs\index.html
   ```

8. **บันทึก log การอัปเดต** (สำคัญ — ทำทุกครั้ง):
   ```
   python src/update_log.py add --category intel --action research \
     --scope "วิเคราะห์เชิงลึก 6 มิติ" \
     --summary "วิเคราะห์คู่แข่งเชิงลึก [จำนวน] ร้าน (6 มิติ)" \
     --count [จำนวนคู่แข่ง] \
     --detail "คู่แข่งเปลี่ยนแปลงมากสุด: ..." --detail "delivery: ..."
   ```

9. Git:
   ```
   git add docs/ reports/competitor-changes-*.md data/competitor-history/ src/generate_dashboard.py data/update-log.json
   git commit -m "Competitor deep analysis + delivery update [DATE]"
   git push
   ```

10. สรุปใน chat:
   - จำนวนคู่แข่งที่วิเคราะห์ (พร้อม 6 มิติ)
   - คู่แข่งที่มีการเปลี่ยนแปลงมากที่สุด (พร้อม badge)
   - **Delivery highlights**: ร้านไหนอยู่บนแอปไหน, โปรโมชันใหม่ที่พบ
   - path ของ report
   - "Dashboard + docs/ อัปเดตแล้ว"

ใช้ภาษาไทยในรายงาน ยกเว้น technical terms
