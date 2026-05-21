"""
TikTok API client — ดึงข้อมูล TikTok Business Account analytics
docs: https://developers.tiktok.com/doc/tiktok-api-v2-video-list
"""

import requests
from datetime import datetime, timedelta


class TikTokAPI:
    BASE = "https://open.tiktokapis.com/v2"

    def __init__(self, access_token: str, open_id: str):
        self.token = access_token
        self.open_id = open_id

    def _get(self, endpoint: str, params: dict = None) -> dict:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type":  "application/json",
        }
        r = requests.get(f"{self.BASE}/{endpoint}", params=params or {}, headers=headers, timeout=30)
        r.raise_for_status()
        return r.json()

    def _post(self, endpoint: str, payload: dict = None) -> dict:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type":  "application/json",
        }
        r = requests.post(f"{self.BASE}/{endpoint}", json=payload or {}, headers=headers, timeout=30)
        r.raise_for_status()
        return r.json()

    def fetch_user_info(self) -> dict:
        """ดึงข้อมูล Profile (followers, following, likes)"""
        data = self._get("user/info/", {
            "fields": "open_id,display_name,follower_count,following_count,likes_count,video_count"
        })
        return data.get("data", {}).get("user", {})

    def fetch_video_list(self, days: int = 30) -> list:
        """
        ดึงรายการ Video พร้อม stats ย้อนหลัง N วัน
        Return: list ของ rows สำหรับ Overview.csv
        """
        rows_by_date = {}

        # ดึงวิดีโอล่าสุด (max 20 ต่อ request)
        payload = {
            "fields": [
                "id", "title", "create_time",
                "view_count", "like_count", "comment_count", "share_count"
            ],
            "max_count": 20,
        }

        try:
            data = self._post("video/list/", payload)
            videos = data.get("data", {}).get("videos", [])

            cutoff = datetime.now() - timedelta(days=days)

            for v in videos:
                ts = v.get("create_time", 0)
                dt = datetime.fromtimestamp(ts)
                if dt < cutoff:
                    continue

                date_str = dt.strftime("%b %-d")  # format: "May 19"
                if date_str not in rows_by_date:
                    rows_by_date[date_str] = {
                        "Date":          date_str,
                        "Video Views":   0,
                        "Profile Views": 0,
                        "Likes":         0,
                        "Comments":      0,
                        "Shares":        0,
                    }

                # รวม stats ของวันเดียวกัน
                rows_by_date[date_str]["Video Views"]   += v.get("view_count",    0)
                rows_by_date[date_str]["Likes"]         += v.get("like_count",    0)
                rows_by_date[date_str]["Comments"]      += v.get("comment_count", 0)
                rows_by_date[date_str]["Shares"]        += v.get("share_count",   0)

        except requests.HTTPError as e:
            print(f"     ⚠️  TikTok video list failed: {e}")

        return list(rows_by_date.values())

    def refresh_token(self, refresh_token: str) -> dict:
        """
        Refresh access token ก่อนหมดอายุ
        TikTok access token หมดอายุใน 24 ชม. ต้อง refresh ด้วย refresh_token (อายุ 365 วัน)
        """
        data = self._post("oauth/token/", {
            "grant_type":    "refresh_token",
            "refresh_token": refresh_token,
        })
        return data.get("data", {})
