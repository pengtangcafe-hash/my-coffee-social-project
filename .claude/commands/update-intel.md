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
   git add docs/ src/generate_dashboard.py reports/intel-*.md data/update-log.json
   git commit -m "Intel update — [YYYY-MM-DD]"
   git push
   ```

4. **สรุปใน chat:**
   - highlights 3 จุดจากข่าวกรองใหม่
   - delivery trends ที่พบ
   - GitHub Pages URL: `https://pengtangcafe-hash.github.io/my-coffee-social-project/`
