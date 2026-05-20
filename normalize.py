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

def save_history(df: pd.DataFrame, platform: str, output_dir="data/history") -> Path:
    os.makedirs(output_dir, exist_ok=True)
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
    normalize(sys.argv[1])
