คุณจะได้รับ path ของไฟล์หรือ folder จาก social platform (optional) และ/หรือ flag `--refresh`

**ถ้าไม่มี argument → ใช้ `sample-data/` เป็น default อัตโนมัติ**
**ถ้ามี argument → parse แยก FILE_PATH และ --refresh flag:**
- ถ้า argument มี `--refresh` → ตั้ง FORCE_REFRESH = true
- argument ที่เหลือ (ไม่ใช่ --refresh) = INPUT_PATH
- ถ้าไม่มี INPUT_PATH หลังจาก parse → ใช้ `sample-data/`

ตัวอย่าง:
- `/analyze` → INPUT_PATH=sample-data/, FORCE_REFRESH=false
- `/analyze --refresh` → INPUT_PATH=sample-data/, FORCE_REFRESH=true
- `/analyze data/imports/tiktok.csv` → INPUT_PATH=data/imports/tiktok.csv, FORCE_REFRESH=false
- `/analyze data/imports/tiktok.csv --refresh` → INPUT_PATH=data/imports/tiktok.csv, FORCE_REFRESH=true

ขั้นตอน:

1. กำหนด INPUT_PATH และ FORCE_REFRESH ตามกฎ parse ด้านบน

2. เรียก **data-agent** และ **intel-agent** พร้อมกัน (parallel) โดยใช้ Task tool:

   **data-agent** — ส่ง:
   - FILE_PATH = INPUT_PATH

   **intel-agent** — ส่ง:
   - topic = "ร้านกาแฟ"
   - city = "สกลนคร"
   - platforms = ["tiktok", "facebook", "instagram"]
   - ถ้า FORCE_REFRESH = true: ส่ง force_refresh=true → intel-agent ต้องค้นหาใหม่ทั้งหมด ห้ามใช้ข้อมูลเดิม และลบไฟล์ reports/intel-summary-*.md เดิมก่อนสร้างใหม่
   - ถ้า FORCE_REFRESH = false: intel-agent ใช้ข้อมูลเดิมจาก reports/intel-summary-*.md หรือ reports/intel-*.md ถ้ามี (Caching rule ปกติ)

3. รอทั้งสอง agent เสร็จ แล้วเก็บ output:
   - `data_result` = JSON summary จาก data-agent (platform, summary, snapshot_saved, history_file)
   - `intel_result` = markdown report จาก intel-agent

4. นำ `data_result` ส่งต่อให้ **dashboard-agent** (ถ้ามี) หรือรัน:
   ```
   python src/generate_dashboard.py <INPUT_PATH>
   ```
   เพื่ออัปเดต dashboard

5. สร้าง Full Report รวมทุก section บันทึกที่ `reports/full-report-<YYYYMMDD>.md`:

   ```markdown
   # Full Social Media Report — ร้านกาแฟ สกลนคร
   **วันที่:** <วันที่ปัจจุบัน>

   ---

   ## ส่วนที่ 1: Data Analysis
   <Executive Summary, Key Metrics, Top/Bottom content จาก data-agent>
   <reach trend % change จาก snapshot ก่อนหน้า ถ้ามี>

   ---

   ## ส่วนที่ 2: Market Intelligence
   <ทั้งหมดจาก intel-agent: Competitor, Hashtags, News, Events, Equipment>

   ---

   ## ส่วนที่ 3: Combined Recommendations
   <รวม insights จาก data + intel แล้วสรุป 3-5 ข้อที่ actionable ที่สุด>
   <ระบุว่าแต่ละข้อมาจาก data หรือ intel หรือทั้งคู่>
   ```

6. **บันทึก log การอัปเดต** — ฝั่ง platform import จะถูก log อัตโนมัติโดย `generate_dashboard.py` แล้ว
   ส่วนฝั่ง intelligence ถ้า intel-agent ค้นข้อมูลใหม่ ให้บันทึกเพิ่ม:
   ```
   python src/update_log.py add --category intel --action analyze \
     --scope "ร้านกาแฟ สกลนคร" --summary "วิเคราะห์ + ข่าวกรองตลาด [YYYYMMDD]" \
     --detail "intel highlight 1" --detail "intel highlight 2"
   ```

7. สรุปผลใน chat:
   - platforms ที่ detect ได้และ snapshot path
   - "Full Report: reports/full-report-<YYYYMMDD>.md"
   - "Dashboard: C:\Users\...\dashboard\index.html" (full path)
   - Intelligence highlights 2-3 bullet จาก intel-agent ที่น่าสนใจที่สุด (เช่น คู่แข่งใหม่, event ที่มาถึง, เทรนด์กาแฟใหม่)

ใช้ภาษาไทยในรายงาน ยกเว้น technical terms
