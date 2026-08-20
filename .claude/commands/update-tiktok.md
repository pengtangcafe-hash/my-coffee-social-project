ดึงข้อมูล TikTok อัตโนมัติผ่าน API (แทน export CSV มือ) แล้ว push ขึ้น GitHub

ใช้ `src/fetch_tiktok.py` ดึงยอดวิว/ไลค์/คอมเมนต์/แชร์จาก TikTok API จริง (เก็บ snapshot รายวันใน
`data/tiktok-raw-snapshots/` แล้วคำนวณผลต่างจากเมื่อวานเอง เพราะ API ให้แค่ยอดสะสม ไม่มีรายวัน)
credential อยู่ใน `.env` (TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET / TIKTOK_REFRESH_TOKEN — ห้าม commit)

## ขั้นตอน

1. **ดึงข้อมูล TikTok**
   ```
   python src/fetch_tiktok.py
   ```
   ถ้า error เรื่อง refresh token หมดอายุ/ใช้ไม่ได้ → ต้องขอ auth code ใหม่จากผู้ใช้ (ดูขั้นตอนใน
   ประวัติแชทที่ตั้งค่าครั้งแรก — ต้องเปิดลิงก์ authorize ใหม่ เพราะ refresh_token มีอายุ ~365 วัน)

2. **Rebuild + คัดลอกไป docs/** (⚠️ ห้ามลืม — GitHub Pages เสิร์ฟจาก `docs/` ไม่ใช่ `dashboard/`)
   ```
   python src/generate_dashboard.py --rebuild
   copy dashboard\index.html docs\index.html
   ```

3. **บันทึก log การอัปเดต**
   ```
   python src/update_log.py add --category platform --action "ดึงข้อมูล TikTok" --scope "TikTok" --summary "ดึงยอดวิว/ไลค์/คอมเมนต์/แชร์จาก TikTok API — [วันที่]" --count 1
   ```
   แล้ว rebuild ซ้ำหนึ่งครั้งให้ badge "อัปเดตล่าสุด" ขยับ:
   ```
   python src/generate_dashboard.py --rebuild
   copy dashboard\index.html docs\index.html
   ```

4. **Push ขึ้น GitHub**
   ```
   git add data/history/tiktok_*.json data/tiktok-raw-snapshots/ data/update-log.json dashboard/index.html docs/index.html
   git commit -m "feat: ดึงข้อมูล TikTok อัตโนมัติ — [YYYY-MM-DD]"
   git push origin master
   ```

5. **ยืนยันว่า push สำเร็จจริง** (⚠️ ห้ามข้าม — เคยเกิดเหตุการณ์ดึงข้อมูลสำเร็จ+บันทึก log แล้ว แต่ไฟล์ไม่เคยขึ้น GitHub จริง เว็บเลยค้างข้อมูลเก่าหลายวันโดยไม่มีใครรู้):
   ```
   git status --short
   git log origin/master..HEAD --oneline
   ```
   - `git status --short` ต้องไม่เหลือไฟล์ที่เกี่ยวข้อง (data/history/tiktok_*.json, dashboard/index.html, docs/index.html, data/update-log.json) ค้างเป็น modified/untracked — ถ้ามี ให้ย้อนกลับไป add+commit+push ให้ครบก่อน
   - `git log origin/master..HEAD` ต้อง**ว่างเปล่า** (ไม่มี commit ค้างที่ยังไม่ถึง remote) — ถ้ายังมีบรรทัดโผล่มา ให้ `git push origin master` ซ้ำจนว่าง ห้ามสรุปผลให้ผู้ใช้ว่า "อัปเดตแล้ว" จนกว่าจะยืนยันขั้นนี้ผ่าน

6. **สรุปใน chat:**
   - ยอดวันนี้ (reach/likes/comments/shares) ที่ดึงได้
   - GitHub Pages: `https://pengtangcafe-hash.github.io/my-coffee-social-project/`
   - เตือนกด Ctrl+Shift+R
