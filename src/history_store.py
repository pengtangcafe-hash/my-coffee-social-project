"""
history_store.py — จัดการ historical snapshots ของ normalized social media data

File layout:
  data/history/[platform]-[YYYY]-[MM].json
  {
    "platform": "facebook",
    "year": 2026,
    "month": 5,
    "snapshots": [
      {
        "import_date": "2026-05-18",
        "summary": {
          "total_reach": 60927,
          "avg_daily_reach": 2176.0,
          "total_new_followers": 84,
          "avg_engagement_rate": 1.08
        },
        "daily_data": [{"date": "2026-04-19", "reach": 1526, ...}, ...]
      },
      ...
    ]
  }
"""

import json
from datetime import datetime, date
from pathlib import Path

import pandas as pd

HISTORY_DIR = Path(__file__).parent.parent / "data" / "history"


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _history_path(platform: str, year: int, month: int) -> Path:
    return HISTORY_DIR / f"{platform}-{year:04d}-{month:02d}.json"


def _load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _serialize_df(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame to JSON-serializable list of dicts."""
    out = []
    for _, row in df.iterrows():
        record = {}
        for col, val in row.items():
            if hasattr(val, "isoformat"):          # datetime / date
                record[col] = val.isoformat()
            elif hasattr(val, "item"):              # numpy scalar
                record[col] = val.item()
            else:
                record[col] = val
        out.append(record)
    return out


def _build_summary(df: pd.DataFrame, extra: dict | None = None) -> dict:
    """Build summary dict from DataFrame, merged with any extra values provided."""
    summary = {}

    if "reach" in df.columns:
        summary["total_reach"]       = int(df["reach"].sum())
        summary["avg_daily_reach"]   = round(float(df["reach"].mean()), 1)

    if "new_followers" in df.columns:
        summary["total_new_followers"] = int(df["new_followers"].sum())

    # Engagement rate
    if "engagement" in df.columns and "reach" in df.columns:
        active = df[df["reach"] > 0]
        if not active.empty:
            er = (active["engagement"] / active["reach"] * 100).mean()
            summary["avg_engagement_rate"] = round(float(er), 2)
    elif all(c in df.columns for c in ["likes", "comments", "shares"]):
        active = df[df["reach"] > 0]
        if not active.empty:
            eng = active["likes"] + active["comments"] + active["shares"]
            er = (eng / active["reach"] * 100).mean()
            summary["avg_engagement_rate"] = round(float(er), 2)

    if extra:
        summary.update(extra)

    return summary


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def save_snapshot(
    normalized_df: pd.DataFrame,
    platform: str,
    summary_dict: dict | None = None,
) -> Path:
    """
    บันทึก snapshot ลง data/history/[platform]-[YYYY]-[MM].json

    Parameters
    ----------
    normalized_df : DataFrame ที่ผ่าน normalize.py แล้ว (ต้องมี column 'date')
    platform      : ชื่อ platform เช่น 'facebook', 'instagram', 'tiktok'
    summary_dict  : dict เพิ่มเติมที่จะ merge เข้า summary (optional)
                    keys ที่รองรับ: total_reach, avg_daily_reach,
                    total_new_followers, avg_engagement_rate

    Returns
    -------
    Path ของไฟล์ที่บันทึก
    """
    today = date.today()
    year, month = today.year, today.month
    path = _history_path(platform, year, month)

    # Build snapshot
    summary = _build_summary(normalized_df, summary_dict)
    snapshot = {
        "import_date": today.isoformat(),
        "summary":     summary,
        "daily_data":  _serialize_df(normalized_df),
    }

    # Load existing file or create new structure
    if path.exists():
        doc = _load_json(path)
    else:
        doc = {
            "platform":  platform,
            "year":      year,
            "month":     month,
            "snapshots": [],
        }

    doc["snapshots"].append(snapshot)
    _save_json(path, doc)

    print(f"[history_store] saved snapshot -> {path.name}  "
          f"(total snapshots: {len(doc['snapshots'])})")
    return path


def load_history(platform: str, months: int = 3) -> list[dict]:
    """
    โหลด snapshots ของ platform ย้อนหลัง N เดือน

    Parameters
    ----------
    platform : ชื่อ platform
    months   : จำนวนเดือนที่ต้องการย้อนหลัง (default 3)

    Returns
    -------
    list ของ snapshot dicts เรียงตาม import_date (เก่าสุด → ใหม่สุด)
    """
    today = date.today()
    all_snapshots: list[dict] = []

    for delta in range(months):
        # คำนวณเดือนย้อนหลัง
        month = today.month - delta
        year  = today.year
        while month <= 0:
            month += 12
            year  -= 1

        path = _history_path(platform, year, month)
        if not path.exists():
            continue

        doc = _load_json(path)
        for snap in doc.get("snapshots", []):
            snap["_source_file"] = path.name
            all_snapshots.append(snap)

    all_snapshots.sort(key=lambda s: s.get("import_date", ""))
    return all_snapshots


def list_available_history() -> dict[str, list[str]]:
    """
    สรุปข้อมูล history ที่มีอยู่

    Returns
    -------
    dict: { "facebook": ["2026-04", "2026-05"], "tiktok": [...], ... }
    """
    if not HISTORY_DIR.exists():
        return {}

    result: dict[str, list[str]] = {}

    for path in sorted(HISTORY_DIR.glob("*-????-??.json")):
        # filename pattern: platform-YYYY-MM.json
        stem_parts = path.stem.rsplit("-", 2)
        if len(stem_parts) != 3:
            continue
        platform_name, year_str, month_str = stem_parts
        period = f"{year_str}-{month_str}"

        if platform_name not in result:
            result[platform_name] = []
        result[platform_name].append(period)

    return result


# ──────────────────────────────────────────────
# CLI (ทดสอบจาก command line)
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"

    if cmd == "list":
        avail = list_available_history()
        if not avail:
            print("ไม่มีข้อมูล history")
        else:
            for plat, periods in avail.items():
                print(f"  {plat}: {', '.join(periods)}")

    elif cmd == "load" and len(sys.argv) >= 3:
        platform = sys.argv[2]
        months   = int(sys.argv[3]) if len(sys.argv) >= 4 else 3
        snaps    = load_history(platform, months)
        print(f"พบ {len(snaps)} snapshots สำหรับ {platform} ({months} เดือน)")
        for s in snaps:
            print(f"  {s['import_date']}  reach={s['summary'].get('total_reach', '-'):,}  "
                  f"er={s['summary'].get('avg_engagement_rate', '-')}%")

    else:
        print("Usage:")
        print("  python src/history_store.py list")
        print("  python src/history_store.py load <platform> [months]")
