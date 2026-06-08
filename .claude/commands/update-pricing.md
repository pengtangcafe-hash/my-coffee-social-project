อัพเดทเฉพาะหน้า "ราคากลางร้านกาแฟ" แล้ว push ขึ้น GitHub

## ขั้นตอน

1. **ค้นหาราคาล่าสุดของคู่แข่งแต่ละร้าน**
   ใช้ WebSearch ค้นหา:
   - "[ชื่อร้าน] สกลนคร เมนู ราคา"
   - "[ชื่อร้าน] menu price"
   - ดู Facebook Page / LINE MAN / GrabFood ของแต่ละร้าน

   ร้านที่ต้องค้นหา (ดูรายชื่อจาก `PRICING_DATA` ใน `src/generate_dashboard.py`):
   - Amazon Coffee
   - Sniff Roastery
   - CHANN cafe
   - Rebellion Coffee
   - และร้านอื่นๆ ที่มีใน PRICING_DATA

2. **อัพเดท PRICING_DATA ใน src/generate_dashboard.py**
   เปิดไฟล์และอัพเดท field ต่อไปนี้ถ้าพบข้อมูลใหม่:
   - ราคาแต่ละเมนู
   - `"last_updated"` → วันที่วันนี้ format "DD MMM YYYY"
   - `"notes"` → ถ้ามีโปรโมชันหรือข้อสังเกตใหม่

3. **Rebuild + Deploy**
   ```
   python src/generate_dashboard.py sample-data/
   copy dashboard\index.html docs\index.html
   ```

4. **บันทึก log การอัปเดต** (สำคัญ — ทำทุกครั้ง):
   ```
   python src/update_log.py add --category intel --action research \
     --scope "ราคากลางร้านกาแฟ" \
     --summary "อัปเดตราคาเมนูคู่แข่ง [จำนวน] ร้าน" --count [จำนวนร้าน] \
     --detail "ร้านที่ราคาเปลี่ยน: ..."
   ```

5. **Push ขึ้น GitHub**
   ```
   git add docs/ src/generate_dashboard.py data/update-log.json
   git commit -m "Pricing update — [YYYY-MM-DD]"
   git push
   ```

6. **สรุปใน chat:**
   - ร้านที่ราคาเปลี่ยนแปลง (ถ้ามี)
   - ราคาเมนูหลักของแต่ละร้านสรุปสั้นๆ
   - GitHub Pages URL: `https://pengtangcafe-hash.github.io/my-coffee-social-project/`
