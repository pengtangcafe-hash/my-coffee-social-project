อัพเดทข้อมูลตลาดทุกส่วน ยกเว้นภาพรวม Social Media (ไม่ต้องมีไฟล์ CSV ใหม่)
ครอบคลุม: ข่าวกรอง + ราคากลาง + เชิงลึก แล้ว push ขึ้น GitHub

## ขั้นตอน

1. **อัพเดทข่าวกรองตลาด**
   - รัน `/intel` เพื่อค้นหาข้อมูลตลาด delivery trends และ market intel ใหม่

2. **อัพเดทราคากลาง**
   - ค้นหาราคาเมนูล่าสุดของคู่แข่งแต่ละร้านด้วย WebSearch
   - อัพเดท `PRICING_DATA` ใน `src/generate_dashboard.py` ถ้าพบราคาใหม่
   - บันทึก field `"last_updated"` เป็นวันที่วันนี้
   - **บันทึก log**: `python src/update_log.py add --category intel --action research --scope "ราคากลางร้านกาแฟ" --summary "อัปเดตราคาเมนูคู่แข่ง"`
   (ขั้นตอน 1 และ 3 จะบันทึก log โดย `/intel` และ `/intel-deep` เองอยู่แล้ว)

3. **อัพเดทเชิงลึกคู่แข่ง**
   - รัน `/intel-deep` เพื่อวิเคราะห์คู่แข่ง 6 มิติ รวม delivery

4. **Rebuild + Deploy**
   ```
   python src/generate_dashboard.py sample-data/
   copy dashboard\index.html docs\index.html
   ```

5. **Push ขึ้น GitHub**
   ```
   git add docs/ src/generate_dashboard.py data/ reports/
   git commit -m "Market update (intel + pricing + deep) — [YYYY-MM-DD]"
   git push
   ```

6. **สรุปใน chat:**
   - ✅/⏭️ แต่ละส่วนที่อัพเดท
   - highlights สำคัญ: ราคาที่เปลี่ยน, คู่แข่งที่น่าจับตา, delivery trends
   - GitHub Pages URL: `https://pengtangcafe-hash.github.io/my-coffee-social-project/`
