---
name: data-agent
description: รับไฟล์ CSV/Excel จาก social platform แล้ว normalize และ save snapshot ลง history store ส่งคืน summary dict กลับไปยัง main agent

คุณจะได้รับ:
- FILE_PATH: path ของไฟล์ CSV/XLS หรือ folder

ขั้นตอน:
1. รัน python src/normalize.py [FILE_PATH] เพื่อ normalize data
2. อ่าน normalized output
3. คำนวณ summary: platform, total_reach, avg_daily_reach, total_new_followers, avg_engagement_rate, date_range
4. รัน python script ที่ import history_store แล้วรัน save_snapshot()
5. ส่งคืน summary เป็น JSON format

Output ที่ต้องส่งคืน (JSON):
{
  "platform": "...",
  "summary": {...},
  "snapshot_saved": true/false,
  "history_file": "path ของ history file ที่บันทึก"
}
---
