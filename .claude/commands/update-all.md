อัพเดทข้อมูลทุกส่วนของ dashboard ครบทั้งหมด แล้ว push ขึ้น GitHub

## ขั้นตอน

1. **ดึงข้อมูล Social Media จาก API** (อัตโนมัติ)
   ```
   python src/fetch_social.py --days 30
   ```
   - ถ้าสำเร็จ → ไฟล์ CSV ใหม่จะอยู่ใน `data/imports/`
   - ถ้า platform ไหนล้มเหลว → แจ้งผู้ใช้ตรวจสอบ `.env` แต่ทำขั้นตอนอื่นต่อ

2. **วิเคราะห์ Social Media** (ภาพรวม + Platforms)
   - รัน `/analyze data/imports/` เพื่อประมวลผลข้อมูลที่ดึงมา

2. **อัพเดทข่าวกรองตลาด**
   - รัน `/intel` เพื่อค้นหาข้อมูลตลาด delivery trends และ market intel ใหม่

3. **อัพเดทเชิงลึกคู่แข่ง**
   - รัน `/intel-deep` เพื่อวิเคราะห์คู่แข่ง 6 มิติ รวม delivery

4. **อัพเดทราคากลาง**
   - ค้นหาราคาเมนูล่าสุดของคู่แข่งแต่ละร้านด้วย WebSearch
   - อัพเดท `PRICING_DATA` ใน `src/generate_dashboard.py` ถ้าพบราคาใหม่
   - บันทึก field `"last_updated"` เป็นวันที่วันนี้

5. **เปรียบเทียบ Platforms** (ถ้ามีข้อมูลใน data/history/ อย่างน้อย 2 snapshots)
   - รัน `/compare`

6. **Rebuild + Deploy**
   ```
   python src/generate_dashboard.py sample-data/
   copy dashboard\index.html docs\index.html
   ```

7. **Push ขึ้น GitHub**
   ```
   git add docs/ src/generate_dashboard.py data/ reports/
   git commit -m "Full update — [YYYY-MM-DD]"
   git push
   ```

8. **สรุปใน chat:**
   - ✅/⏭️ แต่ละส่วนที่อัพเดท/ข้ามไป
   - highlights สำคัญที่สุด 3 จุด
   - GitHub Pages URL: `https://pengtangcafe-hash.github.io/my-coffee-social-project/`
