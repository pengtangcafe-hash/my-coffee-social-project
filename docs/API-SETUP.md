# วิธีขอ API Credentials — Facebook, Instagram, TikTok

## ขั้นตอนที่ต้องทำครั้งแรกครั้งเดียว

---

## 1. Facebook + Instagram (Meta Graph API)

### สิ่งที่ต้องมีก่อน
- Facebook Page (ไม่ใช่ Profile ส่วนตัว)
- Instagram Business Account ที่เชื่อมกับ Facebook Page แล้ว
- Facebook Developer Account (ฟรี)

### ขั้นตอน

**Step 1: สร้าง Facebook App**
1. ไปที่ https://developers.facebook.com/apps/
2. กด **Create App** → เลือก **Business** → กรอกชื่อ App
3. เพิ่ม Product: **Facebook Login** และ **Instagram Graph API**

**Step 2: หา Page ID**
1. เข้า Facebook Page ของร้าน
2. กด **About** → เลื่อนลงมาจะเห็น **Page ID** (ตัวเลข)
3. หรือไปที่ `https://graph.facebook.com/[your-page-name]?fields=id`

**Step 3: ขอ Long-Lived Page Access Token**
1. ไปที่ https://developers.facebook.com/tools/explorer/
2. เลือก App ที่สร้าง → เลือก **Page** ที่ต้องการ
3. เพิ่ม Permissions:
   - `pages_show_list`
   - `pages_read_engagement`  
   - `pages_read_user_content`
   - `instagram_basic`
   - `instagram_manage_insights`
4. กด **Generate Access Token** → อนุมัติ
5. กด **Exchange for long-lived token** (อายุ 60 วัน)
6. คัดลอก token ใส่ `.env` → `FB_PAGE_ACCESS_TOKEN`

**Step 4: หา Instagram Account ID**
รัน API call นี้ใน Graph Explorer:
```
GET /{page-id}?fields=instagram_business_account
```
จะได้ `"id": "17841xxxxxxxxx"` → ใส่ใน `IG_ACCOUNT_ID`

### ต่ออายุ Token
Token อายุ 60 วัน — ต้อง refresh ทุก 2 เดือน
ไปที่ https://developers.facebook.com/tools/debug_token/ เพื่อเช็คอายุ

---

## 2. TikTok API

### สิ่งที่ต้องมีก่อน
- TikTok Business Account หรือ Creator Account
- Email สำหรับ TikTok Developer Account

### ขั้นตอน

**Step 1: สมัคร TikTok Developer**
1. ไปที่ https://developers.tiktok.com/
2. กด **Get Started** → Login ด้วย TikTok account
3. สร้าง App ใหม่ → ชื่ออะไรก็ได้

**Step 2: ขอ Permissions**
ใน App Settings เพิ่ม Products:
- **Login Kit** (สำหรับ OAuth)
- **Research API** → `video.list` permission

**Step 3: Generate Access Token**
1. ไปที่ **Sandbox** ของ App
2. กด **Get Token** → Login ด้วย TikTok account ที่เป็นเจ้าของ content
3. Copy `access_token` และ `open_id`
4. ใส่ใน `.env`

> ⚠️ **หมายเหตุ**: TikTok access token มีอายุ **24 ชั่วโมง** เท่านั้น
> ต้อง refresh บ่อย หรือตั้ง cron job refresh อัตโนมัติ
> ใช้ refresh_token ที่ได้มาพร้อมกัน (อายุ 365 วัน)

---

## 3. ตั้งค่า .env

คัดลอกไฟล์ template:
```bash
copy .env.example .env
```

แล้วเปิดไฟล์ `.env` และใส่ค่าจริง:
```env
FB_PAGE_ID=123456789
FB_PAGE_ACCESS_TOKEN=EAAxxxxxxxx...
IG_ACCOUNT_ID=17841xxxxxxxxx
TIKTOK_ACCESS_TOKEN=act.xxxxxxxx...
TIKTOK_OPEN_ID=xxxxxxxxxxxxxxxx
FETCH_DAYS=30
```

---

## 4. ทดสอบ

```bash
# ติดตั้ง dependencies
pip install -r requirements.txt

# ทดสอบดึงข้อมูล
python src/fetch_social.py --facebook --days 7
python src/fetch_social.py --instagram --days 7
python src/fetch_social.py --tiktok --days 7

# ดึงทั้งหมด
python src/fetch_social.py --days 30
```

---

## สรุป Credentials ที่ต้องการ

| Platform | Variable | อายุ | หาได้จาก |
|----------|----------|------|-----------|
| Facebook | `FB_PAGE_ID` | ถาวร | Facebook Page → About |
| Facebook | `FB_PAGE_ACCESS_TOKEN` | 60 วัน | Graph API Explorer |
| Instagram | `IG_ACCOUNT_ID` | ถาวร | Graph API: `/{page-id}?fields=instagram_business_account` |
| TikTok | `TIKTOK_ACCESS_TOKEN` | 24 ชั่วโมง | TikTok Developer Portal |
| TikTok | `TIKTOK_OPEN_ID` | ถาวร | TikTok Developer Portal |
