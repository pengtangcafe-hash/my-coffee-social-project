"""
competitor_history.py — บันทึกและวิเคราะห์ประวัติข้อมูลคู่แข่งตามเวลา

Usage:
  from competitor_history import save_snapshot, load_history, diff_snapshots, get_trend
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
HISTORY_DIR = PROJECT_ROOT / "data" / "competitor-history"


def save_snapshot(competitors_data: list, source: str = "manual") -> Path:
    """บันทึก snapshot ของข้อมูลคู่แข่ง → data/competitor-history/YYYYMMDD-HHMMSS.json"""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filepath = HISTORY_DIR / f"{timestamp}.json"
    snapshot = {
        "date": datetime.now().isoformat(),
        "source": source,
        "competitors": competitors_data,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    print(f"[competitor_history] saved -> {filepath.name}")
    return filepath


def load_history(days: int = 90) -> list:
    """โหลด snapshots ทั้งหมดใน N วันล่าสุด เรียงจากเก่าไปใหม่"""
    if not HISTORY_DIR.exists():
        return []
    cutoff = datetime.now() - timedelta(days=days)
    snapshots = []
    for f in sorted(HISTORY_DIR.glob("*.json")):
        try:
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)
            snap_date = datetime.fromisoformat(data["date"])
            if snap_date >= cutoff:
                snapshots.append(data)
        except Exception:
            pass
    return snapshots


def diff_snapshots(old: dict, new: dict) -> dict:
    """เปรียบเทียบ 2 snapshots คืน dict การเปลี่ยนแปลงแยกตามคู่แข่ง

    Returns:
        {
          "ชื่อคู่แข่ง": {
            "added": [...],      # fields ที่เพิ่มใหม่
            "removed": [...],    # fields ที่หายไป
            "changed": {         # fields ที่เปลี่ยนค่า
              "field": {"old": ..., "new": ...}
            }
          }
        }
    """
    old_map = {c["id"]: c for c in old.get("competitors", []) if "id" in c}
    new_map = {c["id"]: c for c in new.get("competitors", []) if "id" in c}
    result = {}

    # คู่แข่งใหม่ที่เพิ่มเข้ามา
    for cid, comp in new_map.items():
        if cid not in old_map:
            name = comp.get("title", cid)
            result[name] = {"added": list(comp.keys()), "removed": [], "changed": {}}

    # คู่แข่งที่หายไป
    for cid, comp in old_map.items():
        if cid not in new_map:
            name = comp.get("title", cid)
            result[name] = {"added": [], "removed": list(comp.keys()), "changed": {}}

    # คู่แข่งที่มีอยู่ทั้งคู่ — เปรียบเทียบ field
    for cid in set(old_map) & set(new_map):
        old_c = old_map[cid]
        new_c = new_map[cid]
        name = new_c.get("title", cid)
        changed = {}
        all_keys = set(list(old_c.keys()) + list(new_c.keys()))
        for key in all_keys:
            ov, nv = old_c.get(key), new_c.get(key)
            if ov != nv:
                changed[key] = {"old": ov, "new": nv}
        if changed:
            result.setdefault(name, {"added": [], "removed": [], "changed": {}})
            result[name]["changed"] = changed

    return result


def get_trend(competitor_name: str, field: str, snapshots: list) -> list:
    """คืน list ของ {"date": ..., "value": ...} ของ field นั้นตามเวลา

    Args:
        competitor_name: ชื่อ (title) หรือ id ของคู่แข่ง
        field: dot-separated path เช่น "pricing.implant.price" หรือ "social_trend.posting_frequency"
        snapshots: list จาก load_history()
    """
    trend = []
    for snap in snapshots:
        for comp in snap.get("competitors", []):
            if comp.get("title") == competitor_name or comp.get("id") == competitor_name:
                trend.append({
                    "date": snap.get("date"),
                    "value": _get_nested(comp, field),
                })
                break
    return trend


def _get_nested(d: dict, field: str):
    """ดึงค่าจาก dot-separated path เช่น 'pricing.implant.price'"""
    parts = field.split(".")
    val = d
    for p in parts:
        if isinstance(val, dict):
            val = val.get(p)
        else:
            return None
    return val
