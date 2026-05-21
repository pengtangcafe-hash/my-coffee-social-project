"""
Meta Graph API client — ดึงข้อมูล Facebook Page + Instagram Business Account
docs: https://developers.facebook.com/docs/graph-api
"""

import requests
from datetime import datetime, timedelta


class MetaAPI:
    BASE = "https://graph.facebook.com/v20.0"

    def __init__(self, page_access_token: str, page_id: str, ig_account_id: str = None):
        self.token = page_access_token
        self.page_id = page_id
        self.ig_account_id = ig_account_id

    def _get(self, endpoint: str, params: dict = None) -> dict:
        p = params or {}
        p["access_token"] = self.token
        r = requests.get(f"{self.BASE}/{endpoint}", params=p, timeout=30)
        r.raise_for_status()
        return r.json()

    # ─── FACEBOOK ───────────────────────────────────────────

    def fetch_page_insights(self, days: int = 30) -> dict:
        """
        ดึง Facebook Page insights ย้อนหลัง N วัน
        Return: dict { "ยอดดู": DataFrame, "การโต้ตอบ": DataFrame, ... }
        """
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        until = datetime.now().strftime("%Y-%m-%d")

        # Meta API metric → ชื่อไฟล์ CSV (ตรงกับ schema.json file_mapping)
        metric_map = {
            "page_impressions_unique": "ยอดดู",       # Unique daily reach
            "page_post_engagements":   "การโต้ตอบ",   # Post engagements
            "page_fan_adds":           "การติดตาม",    # New page likes
            "page_views_total":        "การเข้าชม",    # Page views
            "page_total_actions":      "การคลิกลิงก์", # CTA clicks
        }

        result = {}
        for metric_key, file_name in metric_map.items():
            try:
                data = self._get(f"{self.page_id}/insights", {
                    "metric": metric_key,
                    "period":  "day",
                    "since":   since,
                    "until":   until,
                })
                rows = []
                for item in data.get("data", []):
                    for v in item.get("values", []):
                        rows.append({
                            "date":  v["end_time"][:10],
                            "value": int(v["value"]) if isinstance(v["value"], (int, float)) else 0,
                        })
                result[file_name] = rows
            except requests.HTTPError as e:
                print(f"     ⚠️  Facebook metric '{metric_key}' failed: {e}")
                result[file_name] = []

        return result

    def fetch_page_audience(self, days: int = 30) -> list:
        """ดึงข้อมูล Audience (fans total รายวัน)"""
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        until = datetime.now().strftime("%Y-%m-%d")
        try:
            data = self._get(f"{self.page_id}/insights", {
                "metric": "page_fans",
                "period":  "day",
                "since":   since,
                "until":   until,
            })
            rows = []
            for item in data.get("data", []):
                for v in item.get("values", []):
                    rows.append({"date": v["end_time"][:10], "value": v["value"]})
            return rows
        except Exception:
            return []

    # ─── INSTAGRAM ──────────────────────────────────────────

    def fetch_instagram_insights(self, days: int = 30) -> dict:
        """
        ดึง Instagram Business Account insights
        Return: dict { "ยอดดู": [...], "การโต้ตอบ": [...], ... }
        """
        if not self.ig_account_id:
            return {}

        since = int((datetime.now() - timedelta(days=days)).timestamp())
        until = int(datetime.now().timestamp())

        # IG metric → ชื่อไฟล์ CSV (ตรงกับ schema.json file_mapping)
        metric_map = {
            "reach":            "ยอดดู",
            "accounts_engaged": "การโต้ตอบ",
            "follower_count":   "การติดตาม",
            "profile_views":    "การเข้าชม",
            "impressions":      "การเข้าถึง",
        }

        result = {}
        for metric_key, file_name in metric_map.items():
            try:
                data = self._get(f"{self.ig_account_id}/insights", {
                    "metric":      metric_key,
                    "period":      "day",
                    "since":       since,
                    "until":       until,
                    "metric_type": "total_value",
                })
                rows = []
                for item in data.get("data", []):
                    for v in item.get("values", []):
                        rows.append({
                            "date":  v["end_time"][:10],
                            "value": int(v["value"]) if isinstance(v["value"], (int, float)) else 0,
                        })
                result[file_name] = rows
            except requests.HTTPError as e:
                print(f"     ⚠️  Instagram metric '{metric_key}' failed: {e}")
                result[file_name] = []

        return result
