อัพเดทเฉพาะหน้า "วิเคราะห์เชิงลึก" แล้ว push ขึ้น GitHub

## ขั้นตอน

1. **วิเคราะห์คู่แข่งเชิงลึก 6 มิติ**
   - รัน `/intel-deep` เพื่อวิเคราะห์คู่แข่งทุกร้าน รวมมิติ Delivery Apps

2. **Rebuild + Deploy**
   ```
   python src/generate_dashboard.py sample-data/
   copy dashboard\index.html docs\index.html
   ```

3. **Push ขึ้น GitHub** (log อัปเดตถูกบันทึกโดย `/intel-deep` ในขั้นตอน 1 แล้ว)
   ```
   git add dashboard/ docs/ src/generate_dashboard.py data/competitor-history/ reports/competitor-changes-*.md data/update-log.json
   git commit -m "Deep analysis update — [YYYY-MM-DD]"
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
   - คู่แข่งที่เปลี่ยนแปลงมากที่สุด (พร้อม badge 🔴🟡🟢)
   - delivery highlights: ร้านไหนมีโปรใหม่บน delivery apps
   - GitHub Pages URL: `https://pengtangcafe-hash.github.io/my-coffee-social-project/`
