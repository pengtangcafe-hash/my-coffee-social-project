อัพเดทราคาวัตถุดิบตลาด Makro (หน้า "อัพเดทราคาวัตถุดิบ") แล้ว push ขึ้น GitHub

ไล่ดึงราคาล่าสุดจาก makro.pro ทีละรายการใน `data/ingredient-prices.json` → บันทึกสถิติเฉพาะเมื่อราคาเปลี่ยน → rebuild → deploy
(อ้างอิงกติกาเต็มใน CLAUDE.md หัวข้อ "Backbar — อัพเดทราคาวัตถุดิบ")

## ขั้นตอน

1. **อ่านไฟล์ `data/ingredient-prices.json`**
   - ไล่ทีละ item ที่ **มี `makro_url`** เท่านั้น (item ที่ `makro_url` ว่าง = แพ็คเกจจิ้ง/น้ำ 7-Eleven → **ข้าม ไม่แตะ**)
   - ถ้ามี argument ระบุคำ (เช่น `/update-makro นม`) ให้กรองเฉพาะ item ที่ `label`/`makro_name` มีคำนั้น; ไม่มี argument = ทำทุกตัวที่มี url

2. **WebFetch ทีละ `makro_url`** — ดึงจากหน้าสินค้า:
   - **ราคาปัจจุบัน** (บาท/แพ็ค)
   - ราคาเดิมถ้ามีขีดฆ่า (was) + %ลด (discount_pct) — ถ้าไม่มีให้ `was: null`, `discount_pct: 0`
   - ยืนยัน `pack_qty` (ปริมาณต่อแพ็ค) ยังตรงกับในไฟล์ไหม (ถ้า Makro เปลี่ยนขนาด ให้แก้ pack_qty + pack_label ตาม)
   - คำนวณ **`base_price = price / pack_qty`** (บาท/หน่วยฐาน) — ปัด 5 ตำแหน่ง

3. **เขียนกลับเข้า `history[]` ของ item นั้น** — กติกาสำคัญ:
   - เทียบ `base_price` ใหม่กับ **จุดล่าสุดใน history**
     - **ต่างกัน** → append entry ใหม่ (ดู schema ล่าง)
     - **เท่าเดิม** → ❌ ไม่ append (กันประวัติซ้ำ) แต่ ✅ อัปเดต `fetched_at` ของ entry ล่าสุดเป็นวันนี้ (บันทึกว่าเช็คแล้ววันนี้ ราคายังเท่าเดิม)
   - ⚠️ เทียบด้วย **base_price เท่านั้น** ห้ามเทียบราคาแพ็คดิบ (แพ็คขนาดต่างกันไม่ใช่ราคาขึ้น/ลง)
   - schema ของ entry ใหม่:
     ```json
     {
       "date": "<YYYY-MM-DD วันนี้>",
       "price": <ราคาแพ็ค>,
       "pack_qty": <ปริมาณต่อแพ็ค>,
       "pack_unit": "กรัม/มล.",
       "base_price": <price/pack_qty>,
       "was": <ราคาเดิม หรือ null>,
       "discount_pct": <int>,
       "source": "makro",
       "fetched_at": "<YYYY-MM-DD วันนี้>"
     }
     ```

4. **item ที่ WebFetch ล้มเหลว / หาราคาไม่เจอ** → **คงประวัติเดิมไว้** (ห้ามเขียน null/0 ทับ) แล้วจำชื่อไว้รายงานท้ายว่าไล่ตัวไหนไม่ได้

5. **อัปเดต `updated_at` บนสุดของไฟล์** เป็นวันนี้เสมอ

6. **Rebuild + คัดลอกไป docs/**
   ```
   python src/generate_dashboard.py --rebuild
   copy dashboard\index.html docs\index.html
   ```

7. **บันทึก log การอัปเดต** (สำคัญ — ทำทุกครั้งที่รีเฟรชสำเร็จ):
   ```
   python src/update_log.py add --category intel --action "อัพเดทราคาวัตถุดิบ" --scope "Makro" --summary "รีเฟรชราคา Makro [จำนวนที่ดึงได้] รายการ" --count [จำนวน] --detail "ราคาเปลี่ยน: [รายการที่ขึ้น/ลง]"
   ```
   แล้ว rebuild ซ้ำหนึ่งครั้งให้ badge "อัปเดตล่าสุด" ขยับ:
   ```
   python src/generate_dashboard.py --rebuild
   copy dashboard\index.html docs\index.html
   ```

8. **Push ขึ้น GitHub**
   ```
   git add data/ingredient-prices.json data/update-log.json dashboard/index.html docs/index.html
   git commit -m "prices: รีเฟรชราคา Makro — [YYYY-MM-DD]"
   git push origin master
   ```

9. **ยืนยันว่า push สำเร็จจริง** (⚠️ ห้ามข้าม — เคยเกิดเหตุการณ์อัปเดตข้อมูลสำเร็จ+บันทึก log แล้ว แต่ไฟล์ไม่เคยขึ้น GitHub จริง เว็บเลยค้างข้อมูลเก่าหลายวันโดยไม่มีใครรู้):
   ```
   git status --short
   git log origin/master..HEAD --oneline
   ```
   - `git status --short` ต้องไม่เหลือไฟล์ที่เกี่ยวข้อง (data/ingredient-prices.json, dashboard/index.html, docs/index.html, data/update-log.json) ค้างเป็น modified/untracked — ถ้ามี ให้ย้อนกลับไป add+commit+push ให้ครบก่อน
   - `git log origin/master..HEAD` ต้อง**ว่างเปล่า** (ไม่มี commit ค้างที่ยังไม่ถึง remote) — ถ้ายังมีบรรทัดโผล่มา ให้ `git push origin master` ซ้ำจนว่าง ห้ามสรุปผลให้ผู้ใช้ว่า "อัปเดตแล้ว" จนกว่าจะยืนยันขั้นนี้ผ่าน

10. **สรุปใน chat:**
   - รายการที่ราคา **เปลี่ยน** (ขึ้น▲/ลง▼/ลดราคา🔻) พร้อม base_price เก่า→ใหม่
   - รายการที่ราคาเท่าเดิม (นับจำนวน)
   - รายการที่ **ดึงไม่ได้** (ถ้ามี) — บอกชื่อให้ผู้ใช้รู้
   - เตือนผู้ใช้กด **Ctrl+Shift+R** แล้วเข้าหน้า "อัพเดทราคาวัตถุดิบ" เพื่อดูกราฟ/Δ ล่าสุด
   - GitHub Pages: `https://pengtangcafe-hash.github.io/my-coffee-social-project/`
