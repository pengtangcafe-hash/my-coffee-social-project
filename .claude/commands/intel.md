รัน intel-agent เพื่อค้นหาข้อมูลตลาด คู่แข่ง hashtags งาน events อุปกรณ์กาแฟ **และ Delivery Apps**

ขั้นตอน:
1. กำหนดค่า default:
   - topic = "ร้านกาแฟ"
   - city = "สกลนคร"
   - platforms = ["tiktok", "facebook", "instagram"]
   - ถ้ามี argument ให้ parse เป็น topic และ/หรือ city เช่น `/intel กาแฟสด` หรือ `/intel specialty coffee นครพนม`

2. เรียก intel-agent โดยส่ง:
   - topic, city, platforms ที่กำหนดไว้

3. **ค้นหา Delivery Intel เพิ่มเติม** (WebSearch):
   หัวข้อที่ต้องค้นหา:
   - "[city] ร้านกาแฟ delivery LINE MAN GrabFood ShopeeFood" — แอปที่ร้านกาแฟในเมืองนิยมใช้
   - "กาแฟ delivery โปรโมชัน [ปีปัจจุบัน]" — โปรโมชัน active
   - "LINE MAN GrabFood ร้านกาแฟ [city]" — ร้านในแพลตฟอร์ม
   - "coffee delivery peak hours Thailand" — พฤติกรรมลูกค้า

   สรุปข้อมูลที่ได้เป็น 2 ส่วน:
   - **ภาพรวม Delivery Apps**: แอปไหนยอดนิยมสำหรับกาแฟ, ช่วงเวลา peak, โปรโมชันที่น่าสนใจ
   - **ร้านกาแฟท้องถิ่นบน Delivery**: รายชื่อร้านที่พบบนแพลตฟอร์ม, ข้อสังเกต

4. **อัพเดทข้อมูล Delivery ใน dashboard** (ถ้าพบข้อมูลใหม่ที่ต่างจากเดิม):
   เปิดไฟล์ `src/generate_dashboard.py` หา `id: "delivery-apps-overview"` และ `id: "delivery-local-cafes"` ใน `INTEL_DATA_FALLBACK`
   อัพเดท fields:
   - `"summary"` — สรุปใหม่จากข้อมูลที่ค้นพบ
   - `"detail"` — รายละเอียดใหม่ (HTML string)
   - `"updated"` — วันที่วันนี้ format "DD MMM YYYY"

   จากนั้นรัน:
   ```
   python src/generate_dashboard.py sample-data/
   ```

5. บันทึก report ที่ได้จาก intel-agent ลงไฟล์:
   reports/intel-[YYYYMMDD].md
   (ถ้ามีไฟล์ชื่อเดิมอยู่แล้วให้ใช้ reports/intel-[YYYYMMDD]-[topic].md)

6. **บันทึก log การอัปเดต** (สำคัญ — ทำทุกครั้งที่ค้นข้อมูลใหม่สำเร็จ):
   ```
   python src/update_log.py add --category intel --action research \
     --scope "[topic] [city]" --summary "ค้นข้อมูลตลาด/คู่แข่ง: [topic] ที่ [city]" \
     --detail "highlight 1" --detail "highlight 2"
   ```
   แล้วรัน `python src/generate_dashboard.py --rebuild` เพื่อให้ badge "อัปเดตล่าสุด" และหน้า "บันทึกอัปเดต" อัปเดตตาม

7. สรุปสั้นๆ ใน chat:
   - topic และ city ที่ค้นหา
   - highlights 3 จุดที่น่าสนใจที่สุดจาก report
   - **Delivery highlights**: แอปหลัก + โปรโมชันที่น่าสนใจ
   - path ของ report ที่บันทึก
   - บอกด้วยว่าอัพเดทข้อมูล Delivery ใน dashboard หรือเปล่า (ถ้ามีการเปลี่ยนแปลง)
