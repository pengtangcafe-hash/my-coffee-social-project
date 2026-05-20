สร้าง comparison report จาก history ที่มีอยู่ใน data/history/

ขั้นตอน:

1. ตรวจสอบ history ที่มีโดยรัน:
   ```python
   import sys; sys.path.insert(0, 'src')
   from history_store import list_available_history
   print(list_available_history())
   ```
   ถ้าไม่มีข้อมูลเลย ให้แจ้งผู้ใช้ให้รัน /analyze ก่อน แล้วหยุด

2. โหลด Platform Comparison Matrix โดยรัน:
   ```python
   import sys; sys.path.insert(0, 'src')
   from compare import compare_platforms
   import pandas as pd
   df = compare_platforms()
   print(df.to_string())
   ```

3. โหลด Period Comparison สำหรับแต่ละ platform ที่มี 2+ snapshots โดยรัน:
   ```python
   import sys, json; sys.path.insert(0, 'src')
   from history_store import list_available_history, load_history
   avail = list_available_history()
   for platform, periods in avail.items():
       snaps = load_history(platform, months=3)
       print(f'{platform}: {len(snaps)} snapshots')
       if len(snaps) >= 2:
           prev = snaps[-2]['summary']
           curr = snaps[-1]['summary']
           print(f'  prev_date={snaps[-2]["import_date"]} curr_date={snaps[-1]["import_date"]}')
           for key in ['avg_daily_reach','avg_engagement_rate','total_new_followers','total_reach']:
               v1 = prev.get(key)
               v2 = curr.get(key)
               if v1 and v2 and v1 > 0:
                   pct = (v2 - v1) / v1 * 100
                   print(f'  {key}: {v1} -> {v2} ({pct:+.1f}%)')
   ```

4. สร้าง markdown report ที่มี 3 ส่วน:

   **ส่วน 1: Platform Comparison Matrix**
   - ตารางเปรียบเทียบ metrics ทุก platform จาก step 2
   - ระบุ Winner ของแต่ละ metric ด้วย **bold**
   - ใช้ "-" สำหรับ platform ที่ไม่มีข้อมูล metric นั้น

   **ส่วน 2: Period Comparison**
   - ถ้า platform มี 2+ snapshots ให้แสดง % change ต่อ metric
   - format ลูกศร: `↑ +X.X%` (สีเขียว ใน HTML) หรือ `↓ -X.X%` (สีแดง)
   - ถ้า platform มี snapshot เดียว ให้ระบุ "ยังไม่มีข้อมูลเทียบ (snapshot แรก)"
   - แสดงทุก platform ที่มีใน history

   **ส่วน 3: Recommendations**
   - อ่านจาก comparison data จริง แล้วเขียน 2–3 ข้อที่ทำได้จริงสำหรับร้านกาแฟ สกลนคร
   - ระบุ platform และ metric ที่อ้างอิง เช่น "TikTok Reach +18% — ..."
   - ถ้า period data ยังไม่มีเทรนด์ ให้ recommend จาก Platform Matrix แทน

5. บันทึก report ที่ reports/comparison-[YYYYMMDD].md โดยใช้วันที่จาก currentDate ใน context

6. รัน `python src/generate_dashboard.py sample-data/` เพื่ออัปเดต dashboard

7. สรุปผลใน chat:
   - platforms ที่มีข้อมูล
   - platform ที่ win metrics มากที่สุด
   - path ของ report ที่บันทึก
   - "Dashboard อัปเดตแล้วที่: C:\Users\...\dashboard\index.html"

ใช้ภาษาไทยในรายงาน ยกเว้น technical terms
