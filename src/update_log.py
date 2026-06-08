#!/usr/bin/env python3
"""
update_log.py — ระบบบันทึก (audit log) การอัปเดตข้อมูลทั้งหมดในโปรเจกต์

เก็บทุกครั้งที่มีการ "หาข้อมูลใหม่" ทั้งฝั่ง Platforms (TikTok/Facebook/Instagram)
และฝั่ง Intelligence (คู่แข่ง, ตลาด, ราคา, ความรู้) ลงไฟล์เดียว:

    data/update-log.json

แต่ละ entry บันทึก: เมื่อไหร่ (ts/date_th), หมวด (category), อัปเดตอะไร (summary/details),
และนับได้ว่าอัปเดตไปกี่ครั้ง (count = จำนวน entry ในหมวดนั้น)

ใช้เป็น module:
    from update_log import log_update, load_log, summarize
    log_update("platform", "นำเข้า TikTok 9 แถว", action="import", scope="tiktok", count=9)

ใช้เป็น CLI (ให้ slash-command เรียกได้):
    python src/update_log.py add --category intel --action research \
        --scope "คู่แข่งสกลนคร" --summary "อัปเดตคู่แข่ง 3 ร้าน" --count 3 \
        --detail "Amazon Coffee: ราคาใหม่" --detail "Chann Cafe: โปรใหม่"
    python src/update_log.py show
    python src/update_log.py summary
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
LOG_PATH = PROJECT_ROOT / "data" / "update-log.json"

# หมวดที่รองรับ — แยก Platforms ออกจาก Intelligence ตามที่ผู้ใช้ต้องการ
VALID_CATEGORIES = {"platform", "intel"}

THAI_MONTHS_ABBR = [
    "", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
    "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค.",
]


# ─────────────────────────────────────────────────────────────
# Date helpers (พ.ศ. / เดือนไทยย่อ)
# ─────────────────────────────────────────────────────────────

def thai_date(dt: datetime) -> str:
    """2026-06-09 -> '9 มิ.ย. 2569'"""
    return f"{dt.day} {THAI_MONTHS_ABBR[dt.month]} {dt.year + 543}"


def thai_time(dt: datetime) -> str:
    """-> '14:05'"""
    return dt.strftime("%H:%M")


# ─────────────────────────────────────────────────────────────
# Load / save
# ─────────────────────────────────────────────────────────────

def load_log() -> dict:
    """อ่าน log; คืน {'entries': [...]} เสมอ (ว่างถ้ายังไม่มีไฟล์)."""
    if LOG_PATH.exists():
        try:
            with open(LOG_PATH, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and isinstance(data.get("entries"), list):
                return data
        except Exception:
            pass
    return {"entries": []}


def _save_log(log: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────────────────────
# Core API
# ─────────────────────────────────────────────────────────────

def log_update(
    category: str,
    summary: str,
    action: str = "update",
    scope: str = "",
    details=None,
    count=None,
    when: datetime = None,
) -> dict:
    """
    บันทึก 1 รายการลง log แล้วคืน entry ที่สร้าง

    category : 'platform' หรือ 'intel'
    summary  : สรุปสั้น ๆ ว่าอัปเดตอะไร (แสดงใน timeline)
    action   : import | research | track | compare | analyze | manual ...
    scope    : เจาะจง เช่นชื่อ platform / ชื่อหัวข้อ / ชื่อร้านคู่แข่ง
    details  : list[str] รายละเอียดเพิ่มเติม (optional)
    count    : จำนวนสิ่งที่อัปเดตในรอบนี้ เช่นจำนวนแถว/จำนวนร้าน (optional)
    """
    category = (category or "").strip().lower()
    if category not in VALID_CATEGORIES:
        raise ValueError(
            f"category ต้องเป็นหนึ่งใน {sorted(VALID_CATEGORIES)} (ได้รับ: {category!r})"
        )

    dt = when or datetime.now()
    if isinstance(details, str):
        details = [details]
    details = [d for d in (details or []) if d]

    entry = {
        "id": dt.strftime("%Y%m%d-%H%M%S"),
        "ts": dt.isoformat(timespec="seconds"),
        "date_th": thai_date(dt),
        "time_th": thai_time(dt),
        "category": category,
        "scope": scope or "",
        "action": action or "update",
        "summary": summary or "",
        "details": details,
        "count": count,
    }

    log = load_log()
    log["entries"].append(entry)
    _save_log(log)
    return entry


def backfill() -> int:
    """
    สร้าง log ย้อนหลังจาก 'ไฟล์จริง' ที่มีอยู่ในโปรเจกต์ (idempotent — รันซ้ำได้ ไม่ซ้ำรายการ):
      • data/history/{platform}_{YYYYMMDD}.json  → platform import
      • reports/intel-{YYYYMMDD}-*.md            → intel research
      • reports/competitor-changes-{YYYYMMDD}*.md → intel track
    คืนจำนวนรายการที่เพิ่มใหม่
    """
    plat_label = {"tiktok": "TikTok", "facebook": "Facebook", "instagram": "Instagram"}
    log = load_log()
    existing = {e.get("id") for e in log["entries"]}
    added = 0

    def _mk(eid, dt, category, action, scope, summary, count=None, details=None):
        nonlocal added
        if eid in existing:
            return
        log["entries"].append({
            "id": eid, "ts": dt.isoformat(timespec="seconds"),
            "date_th": thai_date(dt), "time_th": thai_time(dt),
            "category": category, "scope": scope, "action": action,
            "summary": summary, "details": details or [], "count": count,
        })
        existing.add(eid)
        added += 1

    def _dt(datestr, hh=9, mm=0):
        return datetime(int(datestr[:4]), int(datestr[4:6]), int(datestr[6:8]), hh, mm)

    # 1) Platforms
    hist = PROJECT_ROOT / "data" / "history"
    if hist.exists():
        for p in sorted(hist.glob("*_*.json")):
            name, _, datestr = p.stem.rpartition("_")
            if not datestr.isdigit() or len(datestr) != 8:
                continue
            try:
                rows = json.loads(p.read_text(encoding="utf-8")).get("row_count")
            except Exception:
                rows = None
            label = plat_label.get(name, name)
            rows_txt = f" ({rows} แถว)" if rows else ""
            _mk(f"bf-platform-{name}-{datestr}", _dt(datestr, 9, 0),
                "platform", "import", name,
                f"นำเข้าข้อมูล {label}{rows_txt}", count=rows)

    # 2) Intelligence — reports
    reports = PROJECT_ROOT / "reports"
    if reports.exists():
        for p in sorted(reports.glob("intel-*.md")):
            parts = p.stem.split("-", 2)  # intel-YYYYMMDD-slug
            if len(parts) >= 2 and parts[1].isdigit() and len(parts[1]) == 8:
                slug = parts[2] if len(parts) > 2 else ""
                _mk(f"bf-intel-{p.stem}", _dt(parts[1], 10, 0),
                    "intel", "research", slug,
                    f"ค้นข้อมูลตลาด/คู่แข่ง: {slug or p.stem}")
        for p in sorted(reports.glob("competitor-changes-*.md")):
            tail = p.stem.replace("competitor-changes-", "")
            datestr = tail[:8]
            if datestr.isdigit():
                _mk(f"bf-intel-{p.stem}", _dt(datestr, 11, 0),
                    "intel", "track", "ติดตามคู่แข่ง",
                    f"อัปเดตการเปลี่ยนแปลงคู่แข่ง ({tail})")

    if added:
        _save_log(log)
    return added


def summarize(log: dict = None) -> dict:
    """
    คืนสรุปต่อหมวด + รวม:
      {
        'platform': {'count': N, 'last_ts', 'last_date_th', 'last_time_th'},
        'intel':    {...},
        'all':      {...}
      }
    count = จำนวนครั้งที่อัปเดต (จำนวน entry) ในหมวดนั้น
    """
    log = log or load_log()
    entries = log.get("entries", [])

    def _summ(items):
        if not items:
            return {"count": 0, "last_ts": None, "last_date_th": None, "last_time_th": None}
        latest = max(items, key=lambda e: e.get("ts", ""))
        return {
            "count": len(items),
            "last_ts": latest.get("ts"),
            "last_date_th": latest.get("date_th"),
            "last_time_th": latest.get("time_th"),
        }

    return {
        "platform": _summ([e for e in entries if e.get("category") == "platform"]),
        "intel": _summ([e for e in entries if e.get("category") == "intel"]),
        "all": _summ(entries),
    }


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def _cli():
    # Windows console (cp874) เข้ารหัสอักขระไทย/บางสัญลักษณ์ไม่ได้ — บังคับ UTF-8
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="ระบบบันทึกการอัปเดตข้อมูล")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="เพิ่มรายการ log")
    p_add.add_argument("--category", required=True, choices=sorted(VALID_CATEGORIES))
    p_add.add_argument("--summary", required=True)
    p_add.add_argument("--action", default="update")
    p_add.add_argument("--scope", default="")
    p_add.add_argument("--count", type=int, default=None)
    p_add.add_argument("--detail", action="append", default=[], help="ระบุได้หลายครั้ง")

    sub.add_parser("show", help="แสดง log ทั้งหมด")
    sub.add_parser("summary", help="แสดงสรุปต่อหมวด")
    sub.add_parser("backfill", help="สร้าง log ย้อนหลังจากไฟล์จริงที่มีอยู่")

    args = parser.parse_args()

    if args.cmd == "backfill":
        n = backfill()
        print(f"[update-log] backfill: เพิ่ม {n} รายการจากไฟล์ที่มีอยู่")
        return

    if args.cmd == "add":
        entry = log_update(
            category=args.category,
            summary=args.summary,
            action=args.action,
            scope=args.scope,
            details=args.detail,
            count=args.count,
        )
        print(f"[update-log] บันทึกแล้ว: [{entry['category']}] {entry['date_th']} "
              f"{entry['time_th']} — {entry['summary']}")
        return

    if args.cmd == "show":
        log = load_log()
        entries = sorted(log.get("entries", []), key=lambda e: e.get("ts", ""), reverse=True)
        if not entries:
            print("(ยังไม่มีรายการ log)")
            return
        for e in entries:
            cnt = f" · {e['count']}" if e.get("count") is not None else ""
            print(f"{e['date_th']} {e['time_th']}  [{e['category']}/{e['action']}]"
                  f"  {e['summary']}{cnt}")
            for d in e.get("details", []):
                print(f"    - {d}")
        return

    if args.cmd == "summary":
        s = summarize()
        for k in ("platform", "intel", "all"):
            v = s[k]
            print(f"{k:9s}: {v['count']} ครั้ง"
                  + (f" · ล่าสุด {v['last_date_th']} {v['last_time_th']}" if v["last_ts"] else ""))
        return


if __name__ == "__main__":
    sys.exit(_cli())
