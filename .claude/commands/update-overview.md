วิเคราะห์ไฟล์ CSV ที่วางไว้ใน data/imports/ แล้ว push ขึ้น GitHub
ใช้เมื่อ: ดาวน์โหลด CSV จาก TikTok/Facebook/Instagram มือแล้วต้องการอัพเดท dashboard

## ขั้นตอน

1. **ตรวจสอบไฟล์ใน data/imports/**
   - ถ้ามีไฟล์ CSV อยู่ → ดำเนินการต่อ
   - ถ้าไม่มีไฟล์เลย → แจ้งผู้ใช้ว่า:
     "ไม่พบไฟล์ใน data/imports/ — กรุณาวางไฟล์ CSV จาก TikTok/Facebook/Instagram ก่อนรันคำสั่งนี้
      ดูวิธีดาวน์โหลดได้ใน HOW-TO-USE.md"

2. **วิเคราะห์ข้อมูล Social Media**
   - รัน `/analyze data/imports/`

3. **Rebuild + Deploy**
   ```
   python src/generate_dashboard.py data/imports/
   copy dashboard\index.html docs\index.html
   ```

4. **Push ขึ้น GitHub** (การ import platform ถูกบันทึก log อัตโนมัติโดย generate_dashboard.py แล้ว)
   ```
   git add docs/ data/history/ data/update-log.json reports/
   git commit -m "Social overview update — [YYYY-MM-DD]"
   git push
   ```

5. **สรุปใน chat:**
   - platforms ที่ detect ได้ (TikTok / Facebook / Instagram)
   - จำนวนวันที่มีข้อมูล
   - highlights สำคัญ 2-3 จุด (เช่น reach สูงสุด, engagement rate)
   - GitHub Pages URL: `https://pengtangcafe-hash.github.io/my-coffee-social-project/`
