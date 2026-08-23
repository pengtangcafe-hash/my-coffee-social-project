#!/usr/bin/env python3
"""
normalize.py — แปลงไฟล์ CSV จาก TikTok / Facebook / Instagram
ให้เป็น unified JSON ใน data/history/

Usage:
  python normalize.py sample-data/Tiktok/Overview.csv
  python normalize.py sample-data/Facebook/
  python normalize.py sample-data/Instagram/
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd


# ──────────────────────────────────────────────
# Schema
# ──────────────────────────────────────────────

def load_schema(schema_path="data/schema.json"):
    with open(schema_path, encoding="utf-8") as f:
        return json.load(f)


# ──────────────────────────────────────────────
# Platform detection
# ──────────────────────────────────────────────

def detect_platform(path: Path, schema: dict) -> str | None:
    """ตรวจจับ platform จาก path หรือ columns ของไฟล์"""

    # 1. ตรวจจาก path (เช่น keyword "Instagram" ใน folder name)
    for platform, cfg in schema["platforms"].items():
        det = cfg["detection"]
        if det["type"] == "path":
            if any(kw in str(path) for kw in det["keywords"]):
                return platform

    # 2. ตรวจจาก columns ของไฟล์ CSV
    candidates = [path] if path.is_file() else list(path.glob("*.csv"))
    for f in candidates:
        cols = _try_read_columns(f)
        if cols is None:
            continue
        for platform, cfg in schema["platforms"].items():
            det = cfg["detection"]
            if det["type"] == "columns":
                if all(kw in cols for kw in det["keywords"]):
                    return platform

    return None


def _try_read_columns(filepath: Path) -> list | None:
    """อ่าน header row เพื่อดู columns ลอง utf-8 และ utf-16
    รองรับทั้ง wide format (TikTok) และ narrow format (sep=, ของ Facebook/Instagram)
    """
    for enc in ("utf-8", "utf-16"):
        try:
            with open(filepath, encoding=enc) as f:
                lines = f.readlines()
            if not lines:
                continue
            # narrow format: บรรทัดแรกคือ sep=, → header จริงอยู่บรรทัดที่ 2 (index 2)
            if lines[0].strip().startswith("sep="):
                if len(lines) > 2:
                    header = [c.strip().strip('"') for c in lines[2].strip().split(",")]
                    return header
                continue
            # wide format: อ่านปกติ
            df = pd.read_csv(filepath, encoding=enc, nrows=0)
            return df.columns.tolist()
        except Exception:
            continue
    return None


# ──────────────────────────────────────────────
# TikTok (wide format)
# ──────────────────────────────────────────────

def normalize_tiktok(path: Path, schema: dict) -> pd.DataFrame:
    cfg = schema["platforms"]["tiktok"]
    col_map = cfg["column_mapping"]

    if path.is_dir():
        csvs = list(path.glob("*.csv"))
        if not csvs:
            raise FileNotFoundError(f"ไม่พบ CSV ใน {path}")
        path = csvs[0]

    df = pd.read_csv(path, encoding="utf-8")
    df = df.rename(columns=col_map)

    # เก็บเฉพาะ columns ที่ map แล้ว
    keep = [c for c in col_map.values() if c in df.columns]
    df = df[keep]

    # แปลง date: "April 19" → ใช้ปีจาก context (detect จากข้อมูล)
    year = _infer_year(df["date"].iloc[0])
    df["date"] = pd.to_datetime(
        df["date"].astype(str) + f" {year}", format="%B %d %Y"
    ).dt.strftime("%Y-%m-%d")

    df = df.fillna(0)
    return df.sort_values("date").reset_index(drop=True)


def _infer_year(date_str: str) -> int:
    """เดาปีจากชื่อเดือน — ถ้า Jan-Jun ใช้ปีปัจจุบัน, Jul-Dec ใช้ปีก่อน"""
    now = datetime.now()
    month_str = date_str.strip().split()[0].lower()
    late_months = {"july", "august", "september", "october", "november", "december",
                   "jul", "aug", "sep", "oct", "nov", "dec"}
    if month_str in late_months and now.month <= 6:
        return now.year - 1
    return now.year


# ──────────────────────────────────────────────
# Facebook / Instagram (narrow format)
# ──────────────────────────────────────────────

def normalize_narrow(folder: Path, platform: str, schema: dict) -> pd.DataFrame:
    cfg = schema["platforms"][platform]
    file_map = cfg["file_mapping"]

    merged: pd.DataFrame | None = None

    for stem_key, field_name in file_map.items():
        matched = _find_file(folder, stem_key)
        if matched is None:
            print(f"  [skip] ไม่พบไฟล์ที่ตรงกับ '{stem_key}'")
            continue

        try:
            df = _read_narrow_csv(matched)
        except Exception as e:
            print(f"  [skip] {matched.name}: {e}")
            continue

        if df.empty:
            print(f"  [skip] {matched.name}: ไม่มีข้อมูล")
            continue

        df = df.rename(columns={"value": field_name})
        merged = df if merged is None else merged.merge(df, on="date", how="outer")
        print(f"  [ok]   {matched.name} -> {field_name}")

    if merged is None or merged.empty:
        return pd.DataFrame()

    merged = merged.sort_values("date").reset_index(drop=True)
    merged = merged.fillna(0)

    # แปลง numeric columns ให้เป็น int ที่เหมาะสม
    for col in merged.columns:
        if col == "date":
            continue
        merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0)
        if merged[col].apply(lambda x: x == int(x)).all():
            merged[col] = merged[col].astype(int)

    return merged


def _find_file(folder: Path, stem_key: str) -> Path | None:
    """หาไฟล์ใน folder ที่ stem ตรงกับ key"""
    for f in folder.glob("*.csv"):
        if stem_key in f.stem:
            return f
    return None


def _read_narrow_csv(filepath: Path) -> pd.DataFrame:
    """อ่าน Facebook/Instagram narrow CSV (sep=, format) → DataFrame[date, value]"""
    with open(filepath, encoding="utf-16") as f:
        lines = f.readlines()

    # บรรทัด 0: sep=,  |  1: ชื่อ metric  |  2: header  |  3+: data
    rows = []
    for line in lines[3:]:
        parts = line.strip().split(",")
        if len(parts) < 2:
            continue
        date_str = parts[0].strip().strip('"')
        val_str = parts[1].strip().strip('"')
        try:
            date = pd.to_datetime(date_str).strftime("%Y-%m-%d")
            value = float(val_str) if val_str else 0.0
            rows.append({"date": date, "value": max(value, 0)})  # clip ค่าติดลบ
        except Exception:
            continue

    return pd.DataFrame(rows)


# ──────────────────────────────────────────────
# Save output
# ──────────────────────────────────────────────

def _detect_history_regression(df: pd.DataFrame, platform: str, output_dir: str, metric: str = "reach"):
    """🛡️ Safety check — เทียบกับไฟล์ history ล่าสุดที่มีอยู่ก่อนเขียนทับ
    เตือนถ้าวันที่ "เคยมีข้อมูลจริง" (metric > 0 ในไฟล์เดิม) กลายเป็นข้อมูลหาย/ตกฮวบในไฟล์ใหม่
    ที่กำลังจะบันทึก — สัญญาณของการ import ไฟล์ผิด/ไฟล์ไม่ครบทับข้อมูลถูกต้องแบบเงียบๆ
    (เคยเกิดจริง: ยอดดู TikTok วันที่ 14 ส.ค. หล่นจาก 450 เหลือ 0 เพราะ import CSV ผิดไฟล์ — แก้ 2026-08-23)
    เทียบทีละวันที่ทับซ้อนกัน แทนการเทียบผลรวม เพราะไฟล์ CSV แต่ละรอบอาจครอบคลุมช่วงวันที่ไม่เท่ากัน
    (เช่น export 60 วันล่าสุด vs 30 วันล่าสุด) — เทียบผลรวมตรงๆ จะ false-positive ได้ง่าย
    คืน (prev_filename, [(date, old_val, new_val), ...]) เรียงจากวันที่หายมากสุดก่อน หรือ None ถ้าไม่พบความผิดปกติ
    """
    if metric not in df.columns or "date" not in df.columns:
        return None
    files = sorted(Path(output_dir).glob(f"{platform}_*.json"))
    if not files:
        return None
    try:
        prev = json.loads(files[-1].read_text(encoding="utf-8"))
    except Exception:
        return None
    prev_rows = {r.get("date"): r.get(metric, 0) or 0 for r in prev.get("data", []) if r.get("date")}
    new_rows = dict(zip(df["date"], df[metric]))
    regressed = [
        (date, old_val, new_rows.get(date, 0))
        for date, old_val in prev_rows.items()
        if old_val >= 5 and new_rows.get(date, 0) < old_val * 0.5
    ]
    if not regressed:
        return None
    regressed.sort(key=lambda x: x[1], reverse=True)
    return files[-1].name, regressed


def save_history(df: pd.DataFrame, platform: str, output_dir="data/history", allow_regression=False) -> Path:
    os.makedirs(output_dir, exist_ok=True)

    regression = _detect_history_regression(df, platform, output_dir)
    if regression and not allow_regression:
        prev_name, regressed = regression
        # หมายเหตุ: ห้ามใช้ emoji/สัญลักษณ์นอก BMP (เช่น 🛑) ในข้อความนี้ — เคยทดสอบแล้วทำให้ Python
        # print/raise ล้มเหลวด้วย UnicodeEncodeError บน Windows console (คนละสาเหตุกับ Thai text
        # ซึ่ง cp874 รองรับได้ปกติ) ใช้ tag แบบ [SAFETY CHECK] ให้เหมือนสไตล์ [warn]/[ok]/[load] เดิม
        lines = [f"    {d}: {old:,.0f} -> {new:,.0f}" for d, old, new in regressed[:8]]
        more = f"\n    ...และอีก {len(regressed) - 8} วัน" if len(regressed) > 8 else ""
        raise ValueError(
            "\n[SAFETY CHECK] ล้มเหลว — ข้อมูล '" + platform + "' ที่กำลังจะบันทึกทำให้ยอดวันที่เคยมีข้อมูลจริง "
            f"หายไป/ตกฮวบ เทียบกับไฟล์เดิม ({prev_name}):\n" + "\n".join(lines) + more +
            "\n  -> มักเกิดจาก import ไฟล์ CSV ผิด/ไม่ครบ (เช่น ไฟล์ตัวอย่างว่างเปล่า) ทับข้อมูลจริงที่ถูกต้องไว้ก่อนหน้า\n"
            "  -> ตรวจสอบไฟล์ CSV ต้นทางก่อน — อย่าเพิ่ง rebuild/commit/push ต่อ\n"
            "  -> ถ้ามั่นใจว่าข้อมูลใหม่ถูกต้องจริง (เช่น ยอดตกลงจริงตามธรรมชาติ) ให้เรียก "
            "save_history(df, platform, allow_regression=True) แทน\n"
        )

    today = datetime.now().strftime("%Y%m%d")
    out_path = Path(output_dir) / f"{platform}_{today}.json"

    output = {
        "platform": platform,
        "generated_at": datetime.now().strftime("%Y-%m-%d"),
        "row_count": len(df),
        "columns": df.columns.tolist(),
        "data": df.to_dict(orient="records"),
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return out_path


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def normalize(input_path: str, schema_path="data/schema.json") -> Path | None:
    schema = load_schema(schema_path)
    path = Path(input_path)

    if not path.exists():
        print(f"ERROR: ไม่พบ path '{path}'")
        return None

    platform = detect_platform(path, schema)
    if not platform:
        print(f"ERROR: ตรวจจับ platform ไม่ได้จาก '{path}'")
        return None

    print(f"Platform : {platform}")
    print(f"Format   : {schema['platforms'][platform]['format']}")
    print()

    fmt = schema["platforms"][platform]["format"]
    if fmt == "wide":
        df = normalize_tiktok(path, schema)
    else:
        folder = path if path.is_dir() else path.parent
        df = normalize_narrow(folder, platform, schema)

    if df.empty:
        print("ERROR: ไม่มีข้อมูลหลัง normalize")
        return None

    # หมายเหตุ: ไม่ครอบ try/except ตรงนี้ — ปล่อยให้ ValueError จาก safety check ใน save_history()
    # หลุดขึ้นไปถึง __main__ เพื่อให้ exit code ไม่เป็น 0 (generate_dashboard.py เช็ค returncode
    # แล้วพิมพ์ stderr ทั้งก้อนให้เห็นรายละเอียดวันที่ข้อมูลหาย — ถ้า catch ไว้ตรงนี้แล้ว return None
    # เฉยๆ รายละเอียดจะหายไป เหลือแค่ "[warn] ไม่พบ normalized file" ซึ่งไม่บอกอะไรเลย)
    out_path = save_history(df, platform)

    print()
    print(f"บันทึกแล้ว : {out_path}")
    print(f"จำนวนแถว  : {len(df)}")
    print(f"Columns    : {df.columns.tolist()}")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python normalize.py <path>")
        print("  <path> = ไฟล์ CSV (TikTok) หรือ folder (Facebook/Instagram)")
        sys.exit(1)
    try:
        result = normalize(sys.argv[1])
    except ValueError as e:
        # จาก safety check ใน save_history() — พิมพ์ลง stderr + exit code != 0
        # ให้ generate_dashboard.py (เรียกผ่าน subprocess) เห็นและ skip platform นี้แทนที่จะเขียนทับข้อมูล
        print(str(e), file=sys.stderr)
        sys.exit(1)
    if result is None:
        sys.exit(1)
