"""
ดึงข้อมูล TikTok อัตโนมัติผ่าน TikTok API (แทนการ export CSV มือ)

ข้อจำกัดสำคัญ: TikTok API สาธารณะให้แค่ "ยอดสะสมทั้งหมด" ของแต่ละคลิป (ตั้งแต่โพสต์จนถึงตอนนี้)
ไม่มียอดรายวันแบบที่ TikTok Studio export ให้ — สคริปต์นี้เลยต้องเก็บ snapshot ยอดสะสมทุกวัน
แล้วคำนวณผลต่างจาก snapshot เมื่อวาน เพื่อประมาณยอด "วันนี้" เอง (ต้องรันทุกวันต่อเนื่องถึงจะแม่นยำ
ถ้าขาดไปวันไหน ผลต่างของวันถัดมาจะรวมยอดของวันที่ขาดไปด้วย ไม่ใช่ข้อมูลหาย)

ไม่มี "Profile Views" เทียบเท่าใน API สาธารณะ — คอลัมน์นี้จะเป็น 0 เสมอสำหรับข้อมูลจาก API
(ต่างจากตอน import CSV มือที่มีคอลัมน์นี้จริง)

ใช้งาน: python src/fetch_tiktok.py
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
SNAPSHOT_DIR = ROOT / "data" / "tiktok-raw-snapshots"
HISTORY_DIR = ROOT / "data" / "history"

sys.path.insert(0, str(ROOT))
from normalize import save_history  # noqa: E402


def load_env(path: Path) -> dict:
    env = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def save_env(path: Path, env: dict):
    lines = ["# Credentials สำหรับดึงข้อมูล API อัตโนมัติ — ห้าม commit ไฟล์นี้ (อยู่ใน .gitignore แล้ว)", ""]
    for key, value in env.items():
        lines.append(f"{key}={value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def refresh_access_token(env: dict) -> str:
    resp = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": env["TIKTOK_CLIENT_KEY"],
            "client_secret": env["TIKTOK_CLIENT_SECRET"],
            "grant_type": "refresh_token",
            "refresh_token": env["TIKTOK_REFRESH_TOKEN"],
        },
    )
    resp.raise_for_status()
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"Refresh token ล้มเหลว: {data}")

    # TikTok ออก refresh_token ใหม่ทุกครั้งที่ใช้ — ต้องบันทึกกลับไปแทนอันเก่า ไม่งั้นรันครั้งถัดไปจะพัง
    # นับอายุ refresh_token ใหม่จากวันนี้ทุกครั้ง (refresh_expires_in รีเซ็ตทุกครั้งที่ใช้จริง —
    # แปลว่าถ้าสคริปต์รันสม่ำเสมอ นับถอยหลังจะรีเซ็ตตลอด แทบไม่มีทางหมดอายุจริง
    # จะหมดอายุก็ต่อเมื่อ "ไม่ได้รันเลย" นานเกินจำนวนวันที่ TikTok กำหนดไว้)
    env["TIKTOK_REFRESH_TOKEN"] = data["refresh_token"]
    env["TIKTOK_TOKEN_ISSUED_AT"] = datetime.now().strftime("%Y-%m-%d")
    env["TIKTOK_REFRESH_VALID_DAYS"] = str(data.get("refresh_expires_in", 31536000) // 86400)
    save_env(ENV_PATH, env)

    return data["access_token"]


def fetch_all_videos(access_token: str) -> list[dict]:
    videos = []
    cursor = None
    while True:
        body = {"max_count": 20}
        if cursor:
            body["cursor"] = cursor
        resp = requests.post(
            "https://open.tiktokapis.com/v2/video/list/",
            params={"fields": "id,create_time,title,view_count,like_count,comment_count,share_count"},
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json=body,
        )
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("error", {}).get("code") != "ok":
            raise RuntimeError(f"video.list ล้มเหลว: {payload}")

        videos.extend(payload["data"]["videos"])
        if not payload["data"].get("has_more"):
            break
        cursor = payload["data"]["cursor"]
    return videos


def load_snapshot(date_str: str) -> dict | None:
    path = SNAPSHOT_DIR / f"{date_str}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_snapshot(date_str: str, videos: list[dict]):
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = {v["id"]: v for v in videos}
    (SNAPSHOT_DIR / f"{date_str}.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return snapshot


def find_previous_snapshot_date(before: str) -> str | None:
    if not SNAPSHOT_DIR.exists():
        return None
    dates = sorted(p.stem for p in SNAPSHOT_DIR.glob("*.json") if p.stem < before)
    return dates[-1] if dates else None


def compute_daily_row(today_snapshot: dict, prev_snapshot: dict | None, date_str: str) -> dict:
    reach = likes = comments = shares = 0
    for video_id, today_v in today_snapshot.items():
        prev_v = (prev_snapshot or {}).get(video_id)
        if prev_v is None:
            # คลิปใหม่ที่เพิ่งเจอวันนี้ (โพสต์ใหม่ หรือ snapshot แรกที่เคยเก็บ) — นับยอดสะสมทั้งหมดเป็นของวันนี้
            reach += today_v.get("view_count", 0)
            likes += today_v.get("like_count", 0)
            comments += today_v.get("comment_count", 0)
            shares += today_v.get("share_count", 0)
        else:
            reach += max(0, today_v.get("view_count", 0) - prev_v.get("view_count", 0))
            likes += max(0, today_v.get("like_count", 0) - prev_v.get("like_count", 0))
            comments += max(0, today_v.get("comment_count", 0) - prev_v.get("comment_count", 0))
            shares += max(0, today_v.get("share_count", 0) - prev_v.get("share_count", 0))

    return {
        "date": datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d"),
        "reach": reach,
        "profile_visits": 0,  # ไม่มีเทียบเท่าใน TikTok API สาธารณะ
        "likes": likes,
        "comments": comments,
        "shares": shares,
    }


def load_existing_history() -> pd.DataFrame:
    if not HISTORY_DIR.exists():
        return pd.DataFrame(columns=["date", "reach", "profile_visits", "likes", "comments", "shares"])
    files = sorted(HISTORY_DIR.glob("tiktok_*.json"))
    if not files:
        return pd.DataFrame(columns=["date", "reach", "profile_visits", "likes", "comments", "shares"])
    latest = json.loads(files[-1].read_text(encoding="utf-8"))
    return pd.DataFrame(latest["data"])


def main():
    env = load_env(ENV_PATH)
    missing = [k for k in ("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_REFRESH_TOKEN") if k not in env]
    if missing:
        print(f"ERROR: ไม่พบ {', '.join(missing)} ใน .env")
        sys.exit(1)

    today_str = datetime.now().strftime("%Y%m%d")

    print("กำลังขอ access token ใหม่...")
    access_token = refresh_access_token(env)

    print("กำลังดึงรายการคลิป...")
    videos = fetch_all_videos(access_token)
    print(f"  พบ {len(videos)} คลิป")

    today_snapshot = save_snapshot(today_str, videos)

    prev_date = find_previous_snapshot_date(today_str)
    prev_snapshot = load_snapshot(prev_date) if prev_date else None
    if prev_snapshot:
        print(f"  เทียบกับ snapshot วันที่ {prev_date}")
    else:
        print("  ยังไม่มี snapshot ก่อนหน้า — วันนี้จะนับยอดสะสมทั้งหมดเป็นยอด 'วันนี้' (ครั้งแรกที่รัน)")

    new_row = compute_daily_row(today_snapshot, prev_snapshot, today_str)

    history_df = load_existing_history()
    history_df = history_df[history_df["date"] != new_row["date"]]  # กันซ้ำถ้ารันมากกว่า 1 ครั้ง/วัน
    history_df = pd.concat([history_df, pd.DataFrame([new_row])], ignore_index=True)
    history_df = history_df.sort_values("date").reset_index(drop=True)

    out_path = save_history(history_df, "tiktok")
    print(f"บันทึกแล้ว: {out_path}")
    print(f"ยอดวันนี้ ({new_row['date']}): reach={new_row['reach']} likes={new_row['likes']} "
          f"comments={new_row['comments']} shares={new_row['shares']}")


if __name__ == "__main__":
    main()
