"""
compare.py — เปรียบเทียบ social media performance ระหว่าง periods หรือ platforms

Usage (CLI):
  python src/compare.py periods facebook 2026-05 2026-06
  python src/compare.py platforms
  python src/compare.py report
"""

import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from history_store import load_history, list_available_history, HISTORY_DIR, _load_json, _history_path

# ──────────────────────────────────────────────
# Metric definitions
# ──────────────────────────────────────────────

# (summary_key, display_name_th, higher_is_better, format_fn)
METRICS = [
    ("avg_daily_reach",      "ยอดดูเฉลี่ย/วัน",   True,  lambda v: f"{v:,.0f}"),
    ("avg_engagement_rate",  "Engagement Rate",     True,  lambda v: f"{v:.2f}%"),
    ("total_new_followers",  "Followers ใหม่",      True,  lambda v: f"{int(v):,}"),
    ("total_reach",          "Reach รวม",            True,  lambda v: f"{int(v):,}"),
]

METRIC_KEYS = [m[0] for m in METRICS]


# ──────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────

def _snapshots_for_period(platform: str, period_label: str) -> list[dict]:
    """
    หา snapshots ที่ตรงกับ period_label
    period_label รับได้ 2 รูปแบบ:
      "YYYY-MM"       → snapshots ทั้งหมดในเดือนนั้น
      "YYYY-MM-DD"    → snapshots ที่มี import_date ตรงกับวันนั้น
    """
    if len(period_label) == 7:  # YYYY-MM
        year, month = int(period_label[:4]), int(period_label[5:7])
        path = _history_path(platform, year, month)
        if not path.exists():
            return []
        doc = _load_json(path)
        return doc.get("snapshots", [])
    else:  # YYYY-MM-DD
        all_snaps = load_history(platform, months=12)
        return [s for s in all_snaps if s.get("import_date") == period_label]


def _latest_snapshot(platform: str) -> dict | None:
    """โหลด snapshot ล่าสุดของ platform"""
    snaps = load_history(platform, months=3)
    if not snaps:
        snaps = load_history(platform, months=12)
    return snaps[-1] if snaps else None


def _period_summary(snapshots: list[dict]) -> dict | None:
    """
    รวม summary จากหลาย snapshots ใน period เดียวกัน
    ใช้ snapshot ล่าสุดเป็นตัวแทน (import_date สูงสุด)
    """
    if not snapshots:
        return None
    latest = max(snapshots, key=lambda s: s.get("import_date", ""))
    return latest.get("summary", {})


def _pct_change(old: float, new: float) -> float | None:
    if old == 0:
        return None
    return (new - old) / old * 100


def _arrow(pct: float | None, higher_is_better: bool = True) -> str:
    if pct is None:
        return "—"
    good = pct >= 0 if higher_is_better else pct <= 0
    symbol = "↑" if pct >= 0 else "↓"
    sign = "+" if pct >= 0 else ""
    color = "green" if good else "red"
    return f'<span style="color:{color}">{symbol} {sign}{pct:.1f}%</span>'


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def compare_periods(
    platform: str,
    period1_label: str,
    period2_label: str,
) -> dict:
    """
    เปรียบเทียบ metrics ระหว่าง 2 periods สำหรับ platform เดียว

    Parameters
    ----------
    platform      : 'facebook', 'instagram', 'tiktok'
    period1_label : "YYYY-MM" หรือ "YYYY-MM-DD" (period เก่า/baseline)
    period2_label : "YYYY-MM" หรือ "YYYY-MM-DD" (period ใหม่)

    Returns
    -------
    {
      "platform": "facebook",
      "period1":  "2026-04",
      "period2":  "2026-05",
      "metrics": {
        "avg_daily_reach": {
          "period1": 1800.0, "period2": 2176.0,
          "change_pct": 20.9, "arrow": "<span ...>↑ +20.9%</span>"
        },
        ...
      }
    }
    """
    snaps1 = _snapshots_for_period(platform, period1_label)
    snaps2 = _snapshots_for_period(platform, period2_label)

    s1 = _period_summary(snaps1)
    s2 = _period_summary(snaps2)

    result: dict = {
        "platform": platform,
        "period1":  period1_label,
        "period2":  period2_label,
        "period1_found": s1 is not None,
        "period2_found": s2 is not None,
        "metrics": {},
    }

    for key, label, higher_is_better, _ in METRICS:
        v1 = s1.get(key) if s1 else None
        v2 = s2.get(key) if s2 else None
        pct = _pct_change(v1, v2) if (v1 is not None and v2 is not None) else None
        result["metrics"][key] = {
            "label":   label,
            "period1": v1,
            "period2": v2,
            "change_pct": pct,
            "arrow": _arrow(pct, higher_is_better),
        }

    return result


def compare_platforms(period: str = "last_30_days") -> pd.DataFrame:
    """
    เปรียบเทียบ latest snapshot ของทุก platform ที่มีใน history

    Parameters
    ----------
    period : ใช้ "last_30_days" (default) สำหรับ snapshot ล่าสุด
             หรือ "YYYY-MM" สำหรับเดือนที่ระบุ

    Returns
    -------
    DataFrame ที่มี metrics เป็น index, platforms เป็น columns
    พร้อม column "winner" ระบุ platform ที่ชนะ metric นั้น
    """
    available = list_available_history()
    if not available:
        return pd.DataFrame()

    platforms = sorted(available.keys())
    data: dict[str, dict] = {}

    for platform in platforms:
        if period == "last_30_days":
            snap = _latest_snapshot(platform)
            summary = snap.get("summary", {}) if snap else {}
        else:
            snaps = _snapshots_for_period(platform, period)
            summary = _period_summary(snaps) or {}
        data[platform] = summary

    rows = []
    for key, label, higher_is_better, fmt in METRICS:
        row: dict = {"metric_key": key, "metric": label}
        values: dict[str, float | None] = {}

        for platform in platforms:
            val = data[platform].get(key)
            row[platform] = fmt(val) if val is not None else "-"
            values[platform] = val

        valid = {p: v for p, v in values.items() if v is not None}
        if valid:
            winner = max(valid, key=lambda p: valid[p]) if higher_is_better \
                     else min(valid, key=lambda p: valid[p])
            row["winner"] = f"**{winner}**"
        else:
            row["winner"] = "-"

        rows.append(row)

    df = pd.DataFrame(rows).set_index("metric")
    return df


def generate_comparison_report(comparison_data: dict | pd.DataFrame) -> str:
    """
    สร้าง markdown report จาก comparison_data

    รับได้ 2 รูปแบบ:
    - dict  จาก compare_periods()  → Period Comparison Report
    - DataFrame จาก compare_platforms() → Platform Comparison Matrix
    """
    today = date.today().isoformat()

    if isinstance(comparison_data, pd.DataFrame):
        return _report_platform_matrix(comparison_data, today)
    else:
        return _report_period_comparison(comparison_data, today)


# ──────────────────────────────────────────────
# Report builders
# ──────────────────────────────────────────────

def _report_period_comparison(data: dict, today: str) -> str:
    platform = data["platform"].capitalize()
    p1 = data["period1"]
    p2 = data["period2"]
    found1 = data["period1_found"]
    found2 = data["period2_found"]

    lines = [
        f"# รายงานเปรียบเทียบ {platform} — {p1} vs {p2}",
        f"**วันที่สร้างรายงาน:** {today}  ",
        "",
        "---",
        "",
    ]

    if not found1 or not found2:
        missing = []
        if not found1: missing.append(p1)
        if not found2: missing.append(p2)
        lines.append(f"> ⚠️ ไม่พบข้อมูลสำหรับ period: {', '.join(missing)}")
        return "\n".join(lines)

    lines += [
        "## เปรียบเทียบ Metrics",
        "",
        f"| Metric | {p1} | {p2} | เปลี่ยนแปลง |",
        "|--------|" + "-------|" * 3,
    ]

    for key, m in data["metrics"].items():
        _, _, _, fmt = next(x for x in METRICS if x[0] == key)
        v1 = fmt(m["period1"]) if m["period1"] is not None else "-"
        v2 = fmt(m["period2"]) if m["period2"] is not None else "-"
        lines.append(f"| {m['label']} | {v1} | {v2} | {m['arrow']} |")

    lines += [
        "",
        "---",
        "",
        "## สรุป",
        "",
    ]

    improved, declined, unchanged = [], [], []
    for key, m in data["metrics"].items():
        pct = m["change_pct"]
        if pct is None:
            continue
        label = m["label"]
        if pct > 0.5:
            improved.append(f"- **{label}** เพิ่มขึ้น {pct:+.1f}%")
        elif pct < -0.5:
            declined.append(f"- **{label}** ลดลง {pct:.1f}%")
        else:
            unchanged.append(f"- **{label}** ทรงตัว ({pct:+.1f}%)")

    if improved:
        lines.append("### ดีขึ้น")
        lines += improved
        lines.append("")
    if declined:
        lines.append("### แย่ลง")
        lines += declined
        lines.append("")
    if unchanged:
        lines.append("### ทรงตัว")
        lines += unchanged
        lines.append("")

    lines.append("*รายงานนี้สร้างโดย Claude Code | Social Analytics App — ร้านกาแฟ สกลนคร*")
    return "\n".join(lines)


def _report_platform_matrix(df: pd.DataFrame, today: str) -> str:
    if df.empty:
        return "# Platform Comparison\n\n> ⚠️ ไม่พบข้อมูล history\n"

    platforms = [c for c in df.columns if c not in ("metric_key", "winner")]

    lines = [
        "# Platform Comparison Matrix",
        f"**วันที่สร้างรายงาน:** {today}  ",
        f"**Platforms:** {' · '.join(p.capitalize() for p in platforms)}",
        "",
        "---",
        "",
        "## Platform Comparison Matrix",
        "",
    ]

    header = "| Metric | " + " | ".join(p.capitalize() for p in platforms) + " | Winner |"
    sep    = "|--------|" + "---------|" * len(platforms) + "--------|"
    lines += [header, sep]

    for metric, row in df.iterrows():
        cells = [str(row.get(p, "-")) for p in platforms]
        winner = str(row.get("winner", "-"))
        lines.append(f"| {metric} | " + " | ".join(cells) + f" | {winner} |")

    lines += [
        "",
        "---",
        "",
        "## Key Takeaways",
        "",
    ]

    # สรุป winner ต่อ metric
    for metric, row in df.iterrows():
        winner = str(row.get("winner", "-")).replace("**", "")
        if winner and winner != "-":
            lines.append(f"- **{metric}:** {winner.capitalize()} ครองอันดับ 1")

    lines += [
        "",
        "*รายงานนี้สร้างโดย Claude Code | Social Analytics App — ร้านกาแฟ สกลนคร*",
    ]
    return "\n".join(lines)


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "platforms"

    if cmd == "periods" and len(sys.argv) >= 5:
        platform  = sys.argv[2]
        period1   = sys.argv[3]
        period2   = sys.argv[4]
        result    = compare_periods(platform, period1, period2)
        report    = generate_comparison_report(result)
        print(report)

    elif cmd == "platforms":
        period = sys.argv[2] if len(sys.argv) >= 3 else "last_30_days"
        df     = compare_platforms(period)
        report = generate_comparison_report(df)
        print(report)

    elif cmd == "report":
        df     = compare_platforms()
        report = generate_comparison_report(df)
        out    = Path("reports") / f"comparison-{date.today().strftime('%Y%m%d')}.md"
        out.parent.mkdir(exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"บันทึกแล้ว: {out}")

    else:
        print("Usage:")
        print("  python src/compare.py platforms [YYYY-MM]")
        print("  python src/compare.py periods <platform> <YYYY-MM> <YYYY-MM>")
        print("  python src/compare.py report")
