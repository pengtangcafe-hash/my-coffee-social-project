อัพเดทเฉพาะหน้า "ข่าวกรองตลาด" แล้ว push ขึ้น GitHub

## ขั้นตอน

1. **ค้นหา Market Intel ใหม่**
   - รัน `/intel` เพื่อค้นหาข้อมูลตลาด คู่แข่ง hashtags events และ delivery trends

2. **Rebuild + Deploy**
   ```
   python src/generate_dashboard.py sample-data/
   copy dashboard\index.html docs\index.html
   ```

3. **Push ขึ้น GitHub** (log อัปเดตถูกบันทึกโดย `/intel` ในขั้นตอน 1 แล้ว)
   ```
   git add dashboard/ docs/ src/generate_dashboard.py reports/intel-*.md data/update-log.json
   git commit -m "Intel update — [YYYY-MM-DD]"
   git push
   ```

4. **ยืนยันว่า push สำเร็จจริง** (⚠️ ห้ามข้าม — เคยเกิดเหตุการณ์อัปเดตข้อมูลสำเร็จ+บันทึก log แล้ว แต่ไฟล์ไม่เคยขึ้น GitHub จริง เว็บเลยค้างข้อมูลเก่าหลายวันโดยไม่มีใครรู้):
   ```
   git status --short
   git log origin/master..HEAD --oneline
   ```
   - `git status --short` ต้องไม่เหลือไฟล์ที่เกี่ยวข้องค้างเป็น modified/untracked — ถ้ามี ให้ย้อนกลับไป add+commit+push ให้ครบก่อน
   - `git log origin/master..HEAD` ต้อง**ว่างเปล่า** (ไม่มี commit ค้างที่ยังไม่ถึง remote) — ถ้ายังมีบรรทัดโผล่มา ให้ `git push` ซ้ำจนว่าง ห้ามสรุปผลให้ผู้ใช้ว่า "อัปเดตแล้ว" จนกว่าจะยืนยันขั้นนี้ผ่าน

5. **สรุปใน chat:**
   - highlights 3 จุดจากข่าวกรองใหม่
   - delivery trends ที่พบ
   - GitHub Pages URL: `https://pengtangcafe-hash.github.io/my-coffee-social-project/`
