# เอาแอปเมนูขึ้นเว็บจริง (Firebase Hosting)

ผมติดตั้ง Firebase CLI และเตรียมไฟล์ config (`coffee_app/firebase.json`) ให้แล้ว เหลือ 3 ขั้นตอนที่ต้อง**ทำเองในเทอร์มินัลของคุณ**
(ต้องล็อกอินด้วย Gmail ของร้าน — ผมเข้าบัญชีคุณแทนไม่ได้)

---

## ขั้นที่ 1 — ล็อกอิน Firebase

เปิดเทอร์มินัลใหม่ (cmd หรือ PowerShell) แล้วรัน:

```bash
firebase login
```

จะเปิดเบราว์เซอร์ให้ล็อกอิน → เลือก Gmail เดิมของร้าน (ที่ใช้กับ Google Sheets sync อยู่แล้ว) → กด Allow

## ขั้นที่ 2 — สร้างโปรเจกต์ Firebase

1. เปิด https://console.firebase.google.com → **Add project** (หรือ **สร้างโปรเจกต์**)
2. ตั้งชื่อ เช่น `pengtang-cafe-menu` (ระบบจะสร้างเป็น project ID ให้อัตโนมัติ ถ้าชื่อซ้ำคนอื่นจะเติมเลขต่อท้ายให้)
3. ปิด Google Analytics ได้เลย (ไม่จำเป็นสำหรับงานนี้) → Create project
4. เมื่อสร้างเสร็จ **คัดลอก Project ID** (มุมซ้ายบนของ Firebase console หรือใน Project settings)

## ขั้นที่ 3 — Deploy

ในเทอร์มินัล ไปที่โฟลเดอร์โปรเจกต์แล้วรันตามนี้ (แทน `YOUR_PROJECT_ID` ด้วย Project ID จากขั้นที่ 2):

```bash
cd C:\Users\COM Nitro\coffee_app
firebase deploy --project YOUR_PROJECT_ID
```

เสร็จแล้วจะได้ลิงก์แบบ `https://YOUR_PROJECT_ID.web.app` — **ส่งลิงก์นี้กับผมมาด้วย** ผมจะเอาไปทำ QR code แยกให้ครบทั้ง 8 โต๊ะ (ใน1ซ้าย / ใน1ขวา / โต๊ะ1-6) ให้เลย

> อัปเดตแอปครั้งต่อไป: ทุกครั้งที่ผมแก้โค้ดเสร็จ ต้องรัน `flutter build web` ก่อน แล้วค่อย `firebase deploy --project YOUR_PROJECT_ID` อีกที (2 คำสั่งนี้ผมรันเองได้ ไม่ต้องรบกวนคุณอีกหลังจากตั้งค่ารอบแรกเสร็จ)

---

## ทำไมต้อง Firebase Hosting (ไม่ใช้ GitHub Pages เหมือน dashboard เดิม)

Flutter web ทำงานกับ Firebase Hosting ได้ลื่นกว่า — ไม่ต้องตั้งค่า base-href ซับซ้อนแบบ GitHub Pages และ Firebase ฟรีเพียงพอสำหรับเมนูร้าน (10GB เก็บ + 360MB ต่อวัน)
