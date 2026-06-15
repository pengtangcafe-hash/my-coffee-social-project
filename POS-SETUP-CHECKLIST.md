# ✅ Checklist เชื่อม Loyverse POS (go-live Phase 1)

> สถานะ: **Phase 1 สร้าง + เทสผ่านแล้ว** (commit a1fe45b) — โค้ดพร้อม เหลือทำฝั่ง Google 5 สเต็ปนี้เพื่อดึงข้อมูลจริง
> ทำเสร็จแล้วเอา **diagnostic** กลับมาให้ Claude เพื่อสร้าง **Phase 2** (เชื่อมสต็อก + วิเคราะห์ทุนรวม)

---

## 🔧 5 สเต็ป (ติ๊กทีละข้อ)

- [ ] **1. สร้าง token ใหม่ใน Loyverse**
  - Loyverse Back Office (loyverse.com → login) → **Settings → Access tokens**
  - **ลบ token เก่า** (ตัวที่เคยส่งในแชต — ถือว่าเปิดเผยแล้ว) → **+ Add access token** → ตั้งชื่อ "dashboard" → Save
  - คัดลอก token ตัวใหม่เก็บไว้

- [ ] **2. อัปเดต Code.gs ล่าสุด**
  - Google Sheet → **Extensions → Apps Script**
  - ก็อปจากไฟล์ `google-sheets/Code.gs` → วางทับของเดิม → 💾 Save
  - *(ตัวนี้มี proxy ดึง Loyverse ที่เพิ่งเพิ่ม — ถ้าไม่อัปจะดึงไม่ได้)*

- [ ] **3. ใส่ token (เก็บฝั่ง server ปลอดภัย ไม่อยู่ในเว็บ)**
  - Apps Script → **⚙️ Project Settings** (รูปเฟือง เมนูซ้าย)
  - **Script Properties → Add script property**
  - Property = `LOYVERSE_TOKEN` · Value = token ใหม่จากข้อ 1 → **Save script properties**

- [ ] **4. ตั้งหมวดสินค้าใน Loyverse**
  - Loyverse Back Office → **Items → Categories** → สินค้าทุกตัวมีหมวด **กาแฟ / ชา / นม / โซดา**
  - *(ยังไม่ครบไม่เป็นไร — diagnostic จะบอกตัวที่ไม่มีหมวด)*

- [ ] **5. Deploy ใหม่ + ทดสอบ**
  - Apps Script → **Deploy → Manage deployments → ✏️ → Version: New version → Deploy**
  - ถ้าเด้งขอสิทธิ์ → **Allow** (ต้องการสิทธิ์เรียก external เพื่อต่อ Loyverse)
  - เว็บจริง → **Ctrl+Shift+R** → หน้า **"บันทึกข้อมูลนำเข้า POS"**
  - เลือกช่วง **"เดือนนี้"** → กด **📥 ดึงยอดขายจาก POS**

---

## 📤 เสร็จแล้วเอา diagnostic มาให้ Claude (แคปหน้าจอกล่อง 🔍 Diagnostic)
อยากเห็น 3 อย่าง:
1. **หมวดหมู่ใน Loyverse** มีอะไรบ้าง (ครบ กาแฟ/ชา/นม/โซดา ไหม)
2. **จับคู่ได้ X/Y** เมนู
3. รายการ **⚠️ "ชื่อยังไม่ตรงกับเมนูร้าน"** มีตัวไหนบ้าง

→ Claude จะออกแบบ **Phase 2** (POS เสนอ cups → กดยืนยัน → เขียนสต็อก-ยอดขาย + หน้าวิเคราะห์ทุนรวม/กำไร) ให้พอดีกับชื่อจริงของร้าน

---

## 🆘 ถ้าติดปัญหา
| อาการ | แก้ |
|---|---|
| ขึ้น **no_token** ทั้งที่ใส่แล้ว | เช็คชื่อ property เป๊ะ `LOYVERSE_TOKEN` + ต้อง Deploy **New version** (ข้อ 5) |
| ขึ้น **error 401** | token ผิด/หมดอายุ → สร้างใหม่ (ข้อ 1) |
| ขึ้น **"เชื่อม Google Sheet ก่อน"** | ยังไม่ได้ใส่ Web App URL — ไปหน้าต้นทุนเครื่องดื่ม กด 🔗 เชื่อม Sheet |
| per-หมวดขึ้น **"ไม่มีหมวด"** | ยังไม่ตั้ง category ใน Loyverse (ข้อ 4) |
