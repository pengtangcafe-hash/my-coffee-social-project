# Social Analytics App — กาแฟ

## โปรเจกต์นี้คืออะไร
เครื่องมือวิเคราะห์ข้อมูล Social Media สำหรับร้านกาแฟ จังหวัดสกลนคร
สร้างด้วย Claude Code เพื่อนำเข้าข้อมูลจาก TikTok, Facebook, Instagram
แล้ววิเคราะห์ performance, เปรียบเทียบ platform และติดตามคู่แข่ง

## Business Context
- ธุรกิจ: ร้านกาแฟ จังหวัดสกลนคร
- เป้าหมาย: วิเคราะห์ social media เพื่อปรับกลยุทธ์การตลาด
- Platforms หลัก: TikTok, Facebook, Instagram
- พื้นที่ที่สนใจ: จังหวัดสกลนคร และจังหวัดใกล้เคียง
- คู่แข่ง: ร้านกาแฟอื่นๆ ในสกลนคร (ทั้ง chain และ independent)

## KPIs ที่สำคัญที่สุด
1. Follower Growth Rate (%) — ติดตามการเติบโตรายสัปดาห์/รายเดือน
2. Engagement Rate (%) = (Likes + Comments + Shares) / Views * 100
3. Video/Post View Count — ดูว่า content ไหน perform ดี
4. Reach per Post — เฉลี่ยคนที่เห็นต่อโพสต์
5. Best Posting Time — ช่วงเวลาที่ engagement สูงสุด

## Data Location
- sample-data/TikTok/ — ข้อมูล TikTok
- sample-data/Facebook/ — ข้อมูล Facebook
- sample-data/Instagram/ — ข้อมูล Instagram
- data/imports/ — ไฟล์ CSV/XLS ที่นำเข้าจริง
- data/history/ — ข้อมูล normalized เก็บย้อนหลัง
- data/schema.json — mapping ชื่อ column จากแต่ละ platform
- data/update-log.json — บันทึก audit log การอัปเดตทั้งหมด (Platforms + Intelligence)

## Update Log / History (ระบบบันทึกการอัปเดต)
ทุกครั้งที่ "หาข้อมูลใหม่" ต้องบันทึกลง log เสมอ — แสดงผลใน dashboard หน้า "บันทึกอัปเดต"
และ badge "อัปเดตล่าสุด · N ครั้ง" บนหน้าข่าวกรอง
- โมดูล: `src/update_log.py` (เก็บ `data/update-log.json`)
- ฝั่ง **Platforms**: `generate_dashboard.py` บันทึก log อัตโนมัติทุกครั้งที่ import CSV สำเร็จ
- ฝั่ง **Intelligence**: slash-command (/intel, /intel-deep, /track-competitors ฯลฯ) ต้องเรียก
  `python src/update_log.py add --category intel --action <action> --scope "..." --summary "..." [--count N] [--detail "..."]`
- รีเฟรช dashboard โดยไม่ import ใหม่: `python src/generate_dashboard.py --rebuild`
- ดู log: `python src/update_log.py show` · สรุป: `python src/update_log.py summary`

## Report Format
ทุก report ที่ /analyze สร้างต้องมี sections เหล่านี้เสมอ:
1. Executive Summary (3-5 bullet points ที่สำคัญที่สุด)
2. Key Metrics Table (ตาราง metrics หลัก)
3. Top Performing Content (ถ้ามีข้อมูล content)
4. Audience Insights (ถ้ามีข้อมูล demographics)
5. Recommendations (2-3 ข้อที่ทำได้จริง)

## Commands
- /analyze FILE — วิเคราะห์ไฟล์ CSV จาก social platform
- /intel [topic] [city] — ค้นหาข้อมูลตลาด คู่แข่ง hashtags สำหรับธุรกิจกาแฟ
- /intel-deep — วิเคราะห์คู่แข่งเชิงลึก 5 มิติ
- /compare — เปรียบเทียบ performance ระหว่าง platforms
- python src/update_log.py [add|show|summary|backfill] — จัดการ audit log การอัปเดต

## Tech Stack
- Python 3 + pandas สำหรับ data processing
- HTML + Chart.js สำหรับ dashboard visualization
- JSON สำหรับ historical data storage
