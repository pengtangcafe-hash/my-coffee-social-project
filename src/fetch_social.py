"""
fetch_social.py — ดึงข้อมูล Social Media จาก API แล้วบันทึกเป็น CSV
ใช้แทนการ Export CSV จาก platform ด้วยมือ

ใช้งาน:
    python src/fetch_social.py              # ดึงทุก platform
    python src/fetch_social.py --facebook   # เฉพาะ Facebook
    python src/fetch_social.py --instagram  # เฉพาะ Instagram
    python src/fetch_social.py --tiktok     # เฉพาะ TikTok
    python src/fetch_social.py --days 7     # ย้อนหลัง 7 วัน (default: 30)
"""

import os
import sys
import csv
import argparse
from pathlib import Path
from datetime import datetime

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    # dotenv ไม่ได้ติดตั้ง — อ่านจาก environment variables โดยตรง
    pass


# ─── CSV Writers ─────────────────────────────────────────────────────────────

def write_meta_csv(rows: list, metric_name: str, output_dir: str):
    """
    เขียน CSV ในรูปแบบ Meta Business Suite export
    Format:
        sep=,
        "ชื่อ metric"
        "วันที่","Primary"
        "2026-01-01T00:00:00","16"
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    filepath = Path(output_dir) / f"{metric_name}.csv"

    with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
        f.write("sep=,\n")
        f.write(f'"{metric_name}"\n')
        f.write('"วันที่","Primary"\n')
        for row in rows:
            f.write(f'"{row["date"]}T00:00:00","{row["value"]}"\n')


def write_tiktok_csv(rows: list, output_dir: str):
    """
    เขียน CSV ในรูปแบบ TikTok Studio Overview export
    Format: Date, Video Views, Profile Views, Likes, Comments, Shares
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    filepath = Path(output_dir) / "Overview.csv"

    fieldnames = ["Date", "Video Views", "Profile Views", "Likes", "Comments", "Shares"]
    with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, 0) for k in fieldnames})


# ─── Platform Fetchers ────────────────────────────────────────────────────────

def fetch_facebook(days: int = 30) -> bool:
    token   = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
    page_id = os.getenv("FB_PAGE_ID", "")

    if not token or not page_id:
        print("  ❌ Facebook: ไม่พบ FB_PAGE_ACCESS_TOKEN หรือ FB_PAGE_ID ใน .env")
        return False

    sys.path.insert(0, str(Path(__file__).parent))
    from api.meta_api import MetaAPI

    api = MetaAPI(token, page_id)
    out = "data/imports/Facebook"

    print(f"  📘 Facebook: กำลังดึงข้อมูลย้อนหลัง {days} วัน...")
    try:
        data = api.fetch_page_insights(days=days)
        # ดึง Audience แยก
        audience_rows = api.fetch_page_audience(days=days)
        if audience_rows:
            write_meta_csv(audience_rows, "ผู้ชม", out)
            print(f"     ✅ ผู้ชม.csv ({len(audience_rows)} rows)")

        for metric_name, rows in data.items():
            if rows:
                write_meta_csv(rows, metric_name, out)
                print(f"     ✅ {metric_name}.csv ({len(rows)} rows)")
            else:
                print(f"     ⚠️  {metric_name}.csv — ไม่มีข้อมูล")

        print(f"  ✅ Facebook เสร็จแล้ว → {out}/")
        return True
    except Exception as e:
        print(f"  ❌ Facebook error: {e}")
        return False


def fetch_instagram(days: int = 30) -> bool:
    token      = os.getenv("FB_PAGE_ACCESS_TOKEN", "")   # IG ใช้ token เดียวกับ FB
    ig_acct_id = os.getenv("IG_ACCOUNT_ID", "")

    if not token or not ig_acct_id:
        print("  ❌ Instagram: ไม่พบ FB_PAGE_ACCESS_TOKEN หรือ IG_ACCOUNT_ID ใน .env")
        return False

    sys.path.insert(0, str(Path(__file__).parent))
    from api.meta_api import MetaAPI

    api = MetaAPI(token, page_id="", ig_account_id=ig_acct_id)
    out = "data/imports/Instagram"

    print(f"  📸 Instagram: กำลังดึงข้อมูลย้อนหลัง {days} วัน...")
    try:
        data = api.fetch_instagram_insights(days=days)
        for metric_name, rows in data.items():
            if rows:
                write_meta_csv(rows, metric_name, out)
                print(f"     ✅ {metric_name}.csv ({len(rows)} rows)")
            else:
                print(f"     ⚠️  {metric_name}.csv — ไม่มีข้อมูล")

        print(f"  ✅ Instagram เสร็จแล้ว → {out}/")
        return True
    except Exception as e:
        print(f"  ❌ Instagram error: {e}")
        return False


def fetch_tiktok(days: int = 30) -> bool:
    token   = os.getenv("TIKTOK_ACCESS_TOKEN", "")
    open_id = os.getenv("TIKTOK_OPEN_ID", "")

    if not token or not open_id:
        print("  ❌ TikTok: ไม่พบ TIKTOK_ACCESS_TOKEN หรือ TIKTOK_OPEN_ID ใน .env")
        return False

    sys.path.insert(0, str(Path(__file__).parent))
    from api.tiktok_api import TikTokAPI

    api = TikTokAPI(token, open_id)
    out = "data/imports/TikTok"

    print(f"  🎵 TikTok: กำลังดึงข้อมูลย้อนหลัง {days} วัน...")
    try:
        rows = api.fetch_video_list(days=days)
        if rows:
            write_tiktok_csv(rows, out)
            print(f"     ✅ Overview.csv ({len(rows)} rows)")
        else:
            print(f"     ⚠️  Overview.csv — ไม่มีข้อมูล")

        print(f"  ✅ TikTok เสร็จแล้ว → {out}/")
        return True
    except Exception as e:
        print(f"  ❌ TikTok error: {e}")
        return False


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ดึงข้อมูล Social Media จาก API")
    parser.add_argument("--facebook",  action="store_true", help="ดึงเฉพาะ Facebook")
    parser.add_argument("--instagram", action="store_true", help="ดึงเฉพาะ Instagram")
    parser.add_argument("--tiktok",    action="store_true", help="ดึงเฉพาะ TikTok")
    parser.add_argument("--days",      type=int, default=None, help="จำนวนวันย้อนหลัง")
    args = parser.parse_args()

    days = args.days or int(os.getenv("FETCH_DAYS", "30"))

    # ถ้าไม่ระบุ platform → ดึงทุก platform
    fetch_all = not (args.facebook or args.instagram or args.tiktok)

    print(f"\n{'='*50}")
    print(f"  Social Media API Fetch — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  ย้อนหลัง {days} วัน")
    print(f"{'='*50}\n")

    results = {}

    if fetch_all or args.facebook:
        results["facebook"]  = fetch_facebook(days)
        print()

    if fetch_all or args.instagram:
        results["instagram"] = fetch_instagram(days)
        print()

    if fetch_all or args.tiktok:
        results["tiktok"]    = fetch_tiktok(days)
        print()

    # สรุปผล
    print(f"{'='*50}")
    ok  = [p for p, s in results.items() if s]
    err = [p for p, s in results.items() if not s]
    if ok:
        print(f"  ✅ สำเร็จ: {', '.join(ok)}")
    if err:
        print(f"  ❌ ล้มเหลว: {', '.join(err)}")
        print(f"     → ตรวจสอบ .env และรันคำสั่งอีกครั้ง")
    print(f"{'='*50}\n")

    # Exit code 0 ถ้าสำเร็จทั้งหมด หรือบาง platform ไม่มี credentials
    sys.exit(0 if not err else 1)


if __name__ == "__main__":
    main()
