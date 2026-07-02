#!/usr/bin/env python3
"""
generate_dashboard.py — สร้าง HTML dashboard แบบ single-page จากข้อมูล social media

Usage:
  python src/generate_dashboard.py sample-data/Tiktok/Overview.csv
  python src/generate_dashboard.py sample-data/Facebook/
  python src/generate_dashboard.py sample-data/Instagram/
  python src/generate_dashboard.py sample-data/
"""

import json
import math
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

import update_log  # ระบบบันทึก audit log (อยู่ใน src/ เดียวกัน)

PROJECT_ROOT = Path(__file__).parent.parent

PLATFORM_LABELS = {
    "tiktok":    "TikTok",
    "facebook":  "Facebook",
    "instagram": "Instagram",
}

PLATFORM_COLORS = {
    "tiktok":    "#EE1D52",
    "facebook":  "#1877f2",
    "instagram": "#e1306c",
}

COL_LABELS_TH = {
    "date":           "วันที่",
    "reach":          "ยอดดู",
    "engagement":     "การมีส่วนร่วม",
    "likes":          "Likes",
    "comments":       "Comments",
    "shares":         "Shares",
    "new_followers":  "Followers ใหม่",
    "profile_visits": "เข้าชมโปรไฟล์",
    "link_clicks":    "คลิกลิงก์",
    "impressions":    "Impressions",
    "audience":       "ผู้ชม",
}

# doughnut composition per platform
DOUGHNUT_DEF = {
    "tiktok": [
        ("likes",    "Likes",           "#fd3e81"),
        ("comments", "Comments",        "#25f4ee"),
        ("shares",   "Shares",          "#a8b4c0"),
    ],
    "facebook": [
        ("engagement",   "การมีส่วนร่วม",  "#1877f2"),
        ("new_followers","ผู้ติดตามใหม่",  "#0d5dbf"),
        ("link_clicks",  "คลิกลิงก์",     "#47b0f5"),
    ],
    "instagram": [
        ("engagement",    "การมีส่วนร่วม",  "#e1306c"),
        ("impressions",   "Impressions",    "#833ab4"),
        ("profile_visits","เข้าชมโปรไฟล์", "#f56040"),
    ],
}


# ── Intel / Market Intelligence fallback data ──
INTEL_DATA_FALLBACK = [
    {
        "id": "competitor-amazon-coffee",
        "category": "competitor",
        "title": "Amazon Coffee สกลนคร (PTT)",
        "summary": "Chain ใหญ่สุดในไทย มีหลายสาขาในสกลนคร Facebook page active ราคาเข้าถึงได้ เมนูครบ",
        "source_url": "", "thumbnail_url": "",
        "tags": ["สกลนคร", "Chain", "Amazon", "PTT"],
        "relevance": "high",
        "detail": "Amazon Coffee จาก PTT เป็น chain กาแฟใหญ่สุดในไทย มีสาขาในสกลนครหลายจุด (ปั๊มน้ำมัน PTT และ standalone) Facebook page มีผู้ติดตามระดับชาติ ราคาเข้าถึงได้ latte เริ่มต้น 45-55 บาท cold brew 50-65 บาท มีเมนูประจำฤดูกาล loyalty app สะสมแต้มได้",
        "pricing": {
            "espresso":{"price":"35","note":"single shot"},"americano":{"price":"45","note":"hot/iced"},"latte":{"price":"55","note":"hot/iced"},
            "cappuccino":{"price":"55","note":""},"cold_brew":{"price":"65","note":""},"frappe":{"price":"65","note":""},
            "matcha":{"price":"60","note":""},"signature_drink":{"price":"65","note":"seasonal"},
            "food":{"price":"35","note":"เบเกอรี่"},
            "other": [{"name": "ช็อคโกแลต", "price": "55", "note": "hot/iced"}]
        },
        "strengths": ["Brand awareness สูงมาก", "Loyalty app สะสมแต้ม", "สาขาเยอะ ใกล้ปั๊มน้ำมัน", "ราคาเข้าถึงได้", "เมนูประจำฤดูกาล"],
        "promotions": ["สะสมแต้ม A Card", "ซื้อ 10 แก้ว ฟรี 1 แก้ว"],
        "weaknesses": ["Chain — ไม่มีความเป็น local", "บรรยากาศเหมือนกันทุกสาขา", "TikTok เป็น account กลาง ไม่ใช่ local"],
        "location": "หลายสาขา สกลนคร", "hours": "ตามสาขา 06:00-22:00",
        "social_trend": {"primary_platform":"Facebook","posting_frequency":"สม่ำเสมอ","content_style":"promotional","engagement_level":"medium"},
        "delivery": {
            "primary_app": "GrabFood",
            "apps": ["GrabFood", "LINE MAN"],
            "peak_hours": "07:00-09:00 (เช้าก่อนทำงาน), 14:00-16:00 (Coffee Break)",
            "active_promos": ["GrabUnlimited ส่งฟรีไม่จำกัด", "GrabRewards สะสมคะแนน", "Grab Flash Deal เป็นครั้งคราว"],
            "notes": "สาขาในปั๊ม PTT เชื่อมต่อ GrabFood ได้ดีมาก ลูกค้า GrabUnlimited นิยมสั่งช่วงเช้าก่อนถึงออฟฟิศ ยอดสั่งสูงสุดวันทำงาน"
        }
    },
    {
        "id": "competitor-inthanin",
        "category": "competitor",
        "title": "Inthanin Coffee สกลนคร",
        "summary": "Premium chain จาก PTT เน้น specialty beans Thai origin ราคาสูงกว่า Amazon บรรยากาศดี",
        "source_url": "", "thumbnail_url": "",
        "tags": ["สกลนคร", "Chain", "Specialty", "Premium"],
        "relevance": "high",
        "detail": "Inthanin Coffee เน้น Thai specialty beans จากดอยต่างๆ ราคา premium กว่า Amazon (latte 65-80 บาท) มีสาขาในห้างและปั๊ม PTT บรรยากาศดีกว่า Facebook page ระดับชาติ มีเมนู signature เช่น Doi Chaang Single Origin",
        "pricing": {
            "espresso":{"price":"50","note":""},"americano":{"price":"60","note":"hot/iced"},"latte":{"price":"75","note":"hot/iced"},
            "cappuccino":{"price":"75","note":""},"cold_brew":{"price":"85","note":""},"frappe":{"price":"80","note":""},
            "matcha":{"price":"80","note":""},"signature_drink":{"price":"85","note":"Thai origin beans"},
            "food":{"price":"45","note":"เบเกอรี่ premium"},
            "other": []
        },
        "strengths": ["Specialty Thai beans", "บรรยากาศดี", "Brand premium", "มีเมนู Single Origin"],
        "promotions": ["สะสมแต้ม PTT Blue Card"],
        "weaknesses": ["ราคาสูงกว่า Amazon", "Chain ไม่มีความ local", "TikTok content น้อย"],
        "location": "สาขาในห้างและปั๊ม PTT สกลนคร", "hours": "ตามสาขา 07:00-21:00",
        "social_trend": {"primary_platform":"Facebook","posting_frequency":"ปานกลาง","content_style":"promotional","engagement_level":"medium"},
        "delivery": {
            "primary_app": "GrabFood",
            "apps": ["GrabFood", "LINE MAN"],
            "peak_hours": "10:00-12:00 (ช่วงสาย), 14:00-16:00 (Coffee Break บ่าย)",
            "active_promos": ["GrabUnlimited ส่งฟรี", "PTT Blue Card campaign ตามเทศกาล"],
            "notes": "กลุ่มลูกค้า premium นิยม GrabFood เพราะบริการเสถียร รวดเร็ว ตรงกับ positioning ของร้าน ยอดสูงช่วงสาย-บ่ายวันทำงาน"
        }
    },
    {
        "id": "competitor-local-cafe",
        "category": "competitor",
        "title": "ร้านกาแฟ Local สกลนคร (Independent)",
        "summary": "ร้านกาแฟ local independent ในสกลนคร เน้นบรรยากาศ ราคากลาง มี Instagram/TikTok content น่าสนใจ",
        "source_url": "", "thumbnail_url": "",
        "tags": ["สกลนคร", "Local", "Independent", "Aesthetic"],
        "relevance": "high",
        "detail": "กลุ่มร้านกาแฟ independent ในสกลนคร เน้น aesthetic บรรยากาศ latte art content บน Instagram และ TikTok ราคา mid-range (latte 60-80 บาท) หลายร้านใช้ beans local จากภาคอีสาน มีเมนู signature เป็น USP",
        "pricing": {
            "espresso":{"price":"40","note":""},"americano":{"price":"55","note":""},"latte":{"price":"70","note":"hot/iced"},
            "cappuccino":{"price":"70","note":""},"cold_brew":{"price":"75","note":""},"frappe":{"price":"70","note":""},
            "matcha":{"price":"70","note":""},"signature_drink":{"price":"80","note":"แตกต่างตามร้าน"},
            "food":{"price":"50","note":"เค้ก/ขนม homemade"},
            "other": []
        },
        "strengths": ["บรรยากาศน่านั่ง", "Instagram-worthy", "Local vibe", "เมนู signature unique", "Latte art"],
        "promotions": ["บัตรสะสมแต้ม", "โปรนักศึกษา"],
        "weaknesses": ["ไม่มี brand awareness ระดับชาติ", "เปิดวันหยุดไม่สม่ำเสมอ", "TikTok ยังไม่ viral"],
        "location": "ย่านใจกลางเมืองสกลนคร", "hours": "08:00-20:00 (บางร้านปิดจันทร์)",
        "social_trend": {"primary_platform":"Instagram","posting_frequency":"สม่ำเสมอ","content_style":"latte art","engagement_level":"medium"},
        "delivery": {
            "primary_app": "LINE MAN",
            "apps": ["LINE MAN", "ShopeeFood"],
            "peak_hours": "10:00-15:00 (Specialty peak วันหยุด), 14:00-16:00 (Coffee Break วันทำงาน)",
            "active_promos": ["ShopeeFood Flash Sale 30-50% off ช่วง Payday/ต้นเดือน", "LINE MAN ส่งฟรีเมื่อสั่งครบ 150 บาท"],
            "notes": "LINE MAN ครอบคลุม local cafe ดีที่สุด เชื่อมกับ Wongnai นักล่าโปรหลั่งไหลเข้า ShopeeFood ช่วงแคมเปญ — โอกาสดึงลูกค้าใหม่ที่ยังไม่รู้จักร้าน"
        }
    },
    {
        "id": "competitor-wawee",
        "category": "competitor",
        "title": "Wawee Coffee สกลนคร",
        "summary": "Chain จากเชียงใหม่ขยายทั่วไทย เน้น beans คุณภาพดี ราคา mid-premium มี TikTok ระดับชาติ",
        "source_url": "", "thumbnail_url": "",
        "tags": ["สกลนคร", "Chain", "Wawee", "เชียงใหม่"],
        "relevance": "medium",
        "detail": "Wawee Coffee chain จากเชียงใหม่ เน้น Northern Thai beans ราคา mid-premium latte 65-80 บาท มีสาขาในหลายจังหวัด รวมถึงสกลนคร TikTok มีผู้ติดตามระดับชาติ content เน้น barista process และ beans story",
        "pricing": {
            "espresso":{"price":"45","note":""},"americano":{"price":"55","note":""},"latte":{"price":"75","note":""},
            "cappuccino":{"price":"75","note":""},"cold_brew":{"price":"80","note":""},"frappe":{"price":"75","note":""},
            "matcha":{"price":"75","note":""},"signature_drink":{"price":"80","note":"Northern Thai beans"},
            "food":{"price":"40","note":"เบเกอรี่"},
            "other": []
        },
        "strengths": ["Beans quality story ดี", "TikTok following ระดับชาติ", "Northern Thailand branding ชัด"],
        "promotions": ["สมาชิก 10% off", "นักศึกษา 15% off"],
        "weaknesses": ["Chain — local connection น้อย", "ราคากลาง-สูง"],
        "location": "สาขาสกลนคร", "hours": "07:00-21:00",
        "social_trend": {"primary_platform":"TikTok","posting_frequency":"สม่ำเสมอ","content_style":"barista process","engagement_level":"medium"},
        "delivery": {
            "primary_app": "LINE MAN",
            "apps": ["LINE MAN", "GrabFood"],
            "peak_hours": "07:00-09:00 (เช้า), 14:00-16:00 (Coffee Break)",
            "active_promos": ["LINE MAN แคมเปญตามเทศกาล", "ส่วนลดสมาชิกเมื่อสั่งผ่านแอป"],
            "notes": "Wawee ขยายสาขาต่างจังหวัดทั่วไทย LINE MAN ครอบคลุมได้ดี ยอดสั่งช่วงเช้าวันทำงานและบ่ายสูงใกล้เคียงกัน"
        }
    },
    {
        "id": "competitor-raintree",
        "category": "competitor",
        "title": "RAINTREE CAFE สกลนคร (Updated 24 May 2026)",
        "summary": "Destination cafe ระดับกลาง-บน Concept 'เขาใหญ่กลางเมือง' · Facebook 77K · Google 4.7/5 · Day cafe + Night cocktail bar · เปิดถึงเที่ยงคืน · ราคาเริ่ม 70฿ · Pet-friendly",
        "updated": "24 May 2026",
        "source_url": "https://www.facebook.com/p/Raintreecafe-61552983815422/", "thumbnail_url": "",
        "tags": ["สกลนคร", "Local", "Independent", "Destination", "Pet-friendly", "Cocktail"],
        "relevance": "high",
        "detail": "RAINTREE CAFE — 391 ถนนสกลนคร-กาฬสินธุ์ ต.ดงมะไฟ อ.เมือง จ.สกลนคร (ตรงข้าม ปตท.ศูนย์ราชการ)\nโทร: 065-391-4662 / 081-345-4643\n\nSocial Media (verified):\n• Facebook: ~77,000 followers — ใหญ่มากสำหรับ local cafe · crosspost TikTok content\n• Instagram: @raintree_sakon · 11,000 followers · 293 posts · Aesthetic nature photography\n• TikTok: @raintree91 · Comedy/personality-driven · 1 viral video 152,900 likes confirmed\n\nTikTok Content Strategy (verified):\n• Tone: Comedy + personality-driven ไม่ใช่ polished brand content\n• เจ้าของออกกล้องเอง · พนักงานเป็น recurring characters\n• Themes: staff humor ('เจ้านายอยู่ vs ไม่อยู่'), barista spotlight, customer comedy, photo tips\n• เนื้อหา night/bar segment: 'กาแฟดึกที่ Raintree' — promote evening visits\n\nHashtag Strategy:\n• Always-on: #raintreecafe #เรนทรีคาเฟ่ #คาเฟ่สกลนคร #สกลนคร\n• Branded UGC: #raintreemoments — เก็บ fan content\n• Secondary: #sakonnakhon #ร้านกาแฟสกลนคร\n\nReviews:\n• Google Maps: 4.7/5 จาก 246 รีวิว · #14 จาก 246 คาเฟ่สกลนคร\n• Wongnai: 4.1/5 · #3 จาก 181 คาเฟ่\n• Sentiment: 'ฟิลเขาใหญ่กลางเมือง' พูดถึงซ้ำทุก review\n\nจุดแข็ง:\n• Concept 'เขาใหญ่กลางเมือง' ชัดเจน ลูกค้าจำได้\n• พื้นที่ใหญ่มาก 81-150 ที่นั่ง Indoor+Outdoor (สนามหญ้า/สระน้ำ/ต้นจามจุรี)\n• Double segment: Day cafe (กาแฟ/ชา) + Night bar (Cocktail)\n• Pet-friendly — niche หายากในสกลนคร\n• เมนูดัง: มัทฉะน้ำส้มสด 'อร่อยที่สุดในเมือง'\n\nช่องว่างสำหรับคู่แข่ง:\n• Wongnai presence น้อย (3 รีวิว) — โอกาสสำหรับร้านที่ทำ Wongnai marketing\n• เวลาเปิดไม่สม่ำเสมอ (บางรีวิวระบุปิดก่อนเวลา)\n• Delivery Wongnai-direct เท่านั้น ไม่พบ LINE MAN/GrabFood\n• เน้น aesthetic + comedy มากกว่า specialty/origin beans story",
        "pricing": {
            "espresso":{"price":"","note":""},"americano":{"price":"80","note":"dark/medium roast ~80฿"},
            "latte":{"price":"","note":"ราคาเริ่มต้น 70฿"},"cappuccino":{"price":"","note":""},
            "cold_brew":{"price":"","note":""},"frappe":{"price":"","note":""},
            "matcha":{"price":"120","note":"น้ำส้มสด (ขายดี) / coconut matcha / orange matcha"},"signature_drink":{"price":"130","note":"มัทฉะมะพร้าว"},
            "food":{"price":"90","note":"Cheese pie, Carrot cake, Chocolate cake"},
            "other": [{"name":"คาราเมล มัคคิอาโต้","price":"110"},{"name":"เฉลี่ย/คน","price":"70-250"},{"name":"Caramel Macchiato","price":"110"}]
        },
        "strengths": ["Facebook 77K reach ใหญ่มาก", "TikTok viral (152K likes) comedy content", "Branded hashtag #raintreemoments สร้าง UGC", "Concept 'เขาใหญ่กลางเมือง' จำง่าย", "Google 4.7/5 Top of Mind", "Pet-friendly niche", "Day + Night double segment"],
        "promotions": [],
        "weaknesses": ["Wongnai ยังน้อยมาก (3 รีวิว)", "Delivery Wongnai-direct เท่านั้น ไม่อยู่บน LINE MAN/GrabFood", "เวลาเปิดบางครั้งไม่สม่ำเสมอ", "ไม่มี specialty/origin beans story"],
        "location": "391 ถนนสกลนคร-กาฬสินธุ์ ต.ดงมะไฟ อ.เมือง จ.สกลนคร", "hours": "จ-ศ 08:00-23:00 / ส-อา 08:00-00:00",
        "social_trend": {"primary_platform":"TikTok+Facebook","posting_frequency":"สม่ำเสมอ","content_style":"Comedy/personality-driven · staff humor · เจ้าของออกกล้อง · #raintreemoments UGC","engagement_level":"very high"},
        "delivery": {
            "primary_app": "Wongnai",
            "apps": ["Wongnai delivery (08:00-17:00)"],
            "peak_hours": "ไม่ทราบ — delivery เป็น secondary จาก dine-in",
            "active_promos": [],
            "notes": "Wongnai-direct delivery เท่านั้น (08:00-17:00) — LINE MAN และ GrabFood ไม่ verified ณ พ.ค. 2026 ร้านเน้น dine-in experience เป็นหลัก"
        }
    },
    {
        "id": "competitor-zmd",
        "category": "competitor",
        "title": "Z M d cafe' Specialty Coffee สกลนคร (Verified 22 May 2026)",
        "summary": "Dark aesthetic specialty café · Zignature (กาแฟส้ม) signature drink · LINE MAN delivery ✅ · Wongnai 5.0/5 #33/436 · ราคากลาง-ล่าง 75-150฿ · Community collab Soulrun",
        "updated": "22 May 2026",
        "source_url": "https://www.facebook.com/p/Z-M-d-cafe-Specialty-Coffee-100083302782620/", "thumbnail_url": "",
        "tags": ["สกลนคร", "Local", "Independent", "DarkAesthetic", "Specialty", "SlowBar", "SpeedBar"],
        "relevance": "high",
        "detail": "Z M d cafe' Specialty Coffee — 1268/6 ถ.กำจัดภัย ธาตุเชิงชุม เมืองสกลนคร (ใกล้โรงแรมสมเกียรติ แยกอารยา)\nโทร: 093-916-6399 | เปิด 07:30-18:00 ทุกวัน\n\nConcept: Dark aesthetic / specialty — 'มืด, แหลมคม, อินดี้'\nบริการ: Specialty // Speedbar // Slowbar\n\nSocial (verified):\n• Facebook: ~3,243 likes / ~1,798 check-ins\n• Instagram: @zmdcafe · TikTok: @zmdcafe\n• Wongnai: 5.0/5 (4 reviews) · #33 จาก 436 cafés สกลนคร\n\nSignature: Zignature (ส้ม + โซดา + Espresso Colombia) 95฿ — เป็น hero content\nCommunity: Soulrun x ZMd collab · Merch เสื้อ 444฿\nArtwork ซ่อนชั้น 2 — unique story content\n\nDelivery: LINE MAN ✅ (Wongnai x LINE MAN) · 07:30-17:30 · ค่าส่งเริ่ม 0฿\nFacebook ยืนยัน: 'มีเดลิเวอรี่ผ่าน LINE MAN หรือโทร 093-9166399'\n\nReviews: 'ร้านสวย เท่ มากกก' · 'พิถีพิถันในการทำทุกขั้นตอน' · 'บาริสต้า น่ารัก'\n\nช่องว่างสำหรับคู่แข่ง:\n• Google Maps ยังไม่ indexed → เสีย SEO search\n• Wongnai เพียง 4 reviews → credibility ต่ำ\n• Dark aesthetic ไม่ appeal กลุ่ม family/casual → niche แคบ",
        "pricing": {
            "espresso":{"price":"","note":""},"americano":{"price":"75","note":""},
            "latte":{"price":"85","note":""},"cappuccino":{"price":"85","note":""},
            "cold_brew":{"price":"150","note":"Cold Brew Fusion พีช+ไวน์"},"frappe":{"price":"","note":""},
            "matcha":{"price":"80","note":"Classic / 110฿ Premium"},"signature_drink":{"price":"95","note":"Zignature (กาแฟส้ม — hero menu)"},
            "food":{"price":"85","note":"Shio Pan / Saint Etoile / Cranberry CC"},
            "other": [{"name":"Dirty","price":"125"},{"name":"Drip Fusion สตรอว์เบอรี่","price":"130"},{"name":"เสื้อ Merch","price":"444"}]
        },
        "strengths": ["Dark aesthetic เป็น differentiator เดียวในสกลนคร", "Zignature signature ที่จดจำง่าย", "LINE MAN delivery ยืนยัน (07:30-17:30)", "Community Soulrun collab", "Wongnai 5.0/5 #33/436"],
        "promotions": ["ค่าส่ง LINE MAN เริ่ม 0฿ ในพื้นที่"],
        "weaknesses": ["Google Maps ไม่ indexed → เสีย SEO", "Wongnai 4 reviews credibility ต่ำ", "Dark niche ไม่ appeal กลุ่ม family", "วันหยุด (อังคาร?) ยังไม่ confirmed"],
        "location": "1268/6 ถ.กำจัดภัย ธาตุเชิงชุม เมืองสกลนคร", "hours": "07:30-18:00 ทุกวัน (ยังไม่ confirmed วันอังคาร)",
        "social_trend": {"primary_platform":"Facebook","posting_frequency":"สม่ำเสมอ","content_style":"Dark aesthetic + Signature drink reveals + Soulrun community collab","engagement_level":"low-medium"},
        "delivery": {
            "primary_app": "LINE MAN",
            "apps": ["LINE MAN", "Wongnai Delivery"],
            "peak_hours": "07:30-17:30 (ตามเวลาร้าน)",
            "active_promos": ["ค่าส่งเริ่ม 0฿ ในพื้นที่บริการ"],
            "notes": "LINE MAN verified ทั้งจาก Wongnai listing และ Facebook post · ครบเมนูทุกรายการ · link direct: lin.ee/2PPUiFB"
        }
    },
    {
        "id": "competitor-allofkk",
        "category": "competitor",
        "title": "All of KK สกลนคร (Limited Data — Re-verified 9 Jun 2026)",
        "summary": "Small local café · Facebook เท่านั้น (~700 likes) · Tagline 'You can taste the passion' · ไม่พบ delivery · ข้อมูลจำกัดมาก — re-verified 9 Jun 2026 ยังไม่ได้ข้อมูลเพิ่ม · ต้องการ field visit",
        "updated": "9 Jun 2026",
        "source_url": "https://www.facebook.com/allofkk", "thumbnail_url": "",
        "tags": ["สกลนคร", "Local", "Independent", "LimitedData"],
        "relevance": "medium",
        "detail": "All of KK — Facebook: facebook.com/allofkk\nTagline: 'You can taste the passion'\n\n⚠️ ข้อมูลจำกัดมาก — Facebook blocking crawlers:\n• Facebook: ~700 likes / ~205 check-ins (เท่านั้นที่ยืนยันได้)\n• ไม่พบ Instagram, TikTok, Wongnai, Google Maps listing\n• ไม่ทราบ: ที่อยู่, เวลาเปิด, เมนู, ราคา\n\nภาพรวม: ร้านเล็ก low-profile ยังไม่ถูก 'ค้นพบ' โดย community นักรีวิว\nCheck-in 205 คน บ่งชี้มีลูกค้าจริง แต่ social presence ต่ำที่สุดในบรรดาคู่แข่งที่ track\n\n⚠️ แนะนำ: เข้าดู facebook.com/allofkk โดยตรง หรือ field visit เพื่อ update ข้อมูล",
        "pricing": {
            "espresso":{"price":"","note":"ไม่ทราบ"},"americano":{"price":"","note":"ไม่ทราบ"},
            "latte":{"price":"","note":""},"cappuccino":{"price":"","note":""},
            "cold_brew":{"price":"","note":""},"frappe":{"price":"","note":""},
            "matcha":{"price":"","note":""},"signature_drink":{"price":"","note":"ไม่ทราบ"},
            "food":{"price":"","note":""},
            "other": []
        },
        "strengths": ["มีลูกค้าจริง (205 check-ins)", "Tagline passion-driven"],
        "promotions": [],
        "weaknesses": ["Facebook เท่านั้น (ไม่มี IG/TikTok)", "ไม่มี delivery platform", "ไม่มี Wongnai listing", "ข้อมูลสาธารณะน้อยมาก"],
        "location": "สกลนคร (ไม่ทราบที่อยู่ชัดเจน)", "hours": "ไม่ทราบ",
        "social_trend": {"primary_platform":"Facebook","posting_frequency":"ไม่ทราบ","content_style":"ไม่ทราบ — ต้องการ field visit","engagement_level":"low"},
        "delivery": {
            "primary_app": "ไม่มี",
            "apps": [],
            "peak_hours": "N/A",
            "active_promos": [],
            "notes": "ไม่พบบน LINE MAN, GrabFood, Wongnai Delivery — dine-in เท่านั้น (สันนิษฐาน)"
        }
    },
    {
        "id": "competitor-meesuk",
        "category": "competitor",
        "title": "มีสุขสโลว์บาร์หน้าบ้านแม่ สกลนคร (Verified 22 May 2026)",
        "summary": "Slow Bar + Uji Matcha authentic · Concept 'หน้าบ้านแม่' brand story แข็ง · Workshop ปั้นดิน differentiator · ปิด 15:00 · ไม่มี delivery แอปเลย",
        "updated": "22 May 2026",
        "source_url": "https://www.facebook.com/meesookslowbar/", "thumbnail_url": "",
        "tags": ["สกลนคร", "Local", "Independent", "SlowBar", "Matcha", "Workshop", "Minimalist"],
        "relevance": "high",
        "detail": "มีสุขสโลว์บาร์หน้าบ้านแม่ — ซอยเปิ้ลส้มตำ อ.เมือง จ.สกลนคร\nโทร: 090-343-8562\n\nConcept: 'หน้าบ้านแม่' — ตั้งอยู่หน้าบ้านแม่จริงๆ · Slow Bar · Homey minimalist + loft\nSlogan: 'มีสุขในทุกๆวัน' — emotional wellness + slow life positioning\n\nSocial (platforms verified, followers ไม่ทราบ — login required):\n• Facebook: meesookslowbar — active · videos + photos\n• Instagram: @meesuk_slowbar · active\n• TikTok: @meesuk_slowbar · active\n• Lemon8: organic viral (visitor reviews หลายชิ้น)\n\nSignature:\n• Matcha Latte ใช้ Uji matcha แท้จากญี่ปุ่น — differentiator ชัดที่สุด\n• MINOZ Es-yen (iced espresso signature)\n• Workshop ปั้นดิน ทุก พฤหัส + เสาร์ + อาทิตย์ (30฿/กรัม)\n• Banoffee, Shio Pan, Garlic bread with cream cheese อบสด\n\nReviews (Lemon8 organic):\n• 'มัทฉะลาเต้ หอมกลิ่นมัจฉะ ละมุนครีมมี่มาก'\n• 'คาเฟ่ลับๆ ที่ควรแวะ'\n• 'บรรยากาศสุดผ่อนคลาย ความอบอุ่นของบ้าน'\n\nช่องว่างสำหรับคู่แข่ง:\n• ปิด 15:00 — เสียตลาดบ่าย-เย็นทั้งหมด\n• ไม่มี delivery แอปใดเลย\n• ไม่มี LINE OA / loyalty program\n• Follower count ไม่ชัดเจน — reach อาจยังเล็ก",
        "pricing": {
            "espresso":{"price":"","note":"MINOZ Es-yen signature"},"americano":{"price":"","note":""},
            "latte":{"price":"","note":""},"cappuccino":{"price":"","note":""},
            "cold_brew":{"price":"","note":""},"frappe":{"price":"","note":""},
            "matcha":{"price":"","note":"Uji matcha แท้ญี่ปุ่น (signature)"},"signature_drink":{"price":"75","note":"เริ่มต้น ~75฿"},
            "food":{"price":"","note":"Banoffee / Shio Pan / Garlic bread อบสด"},
            "other": [{"name":"Workshop ปั้นดิน","price":"30/กรัม"}]
        },
        "strengths": ["Brand story 'หน้าบ้านแม่' authentic", "Uji matcha แท้จากญี่ปุ่น", "Workshop ปั้นดิน = experience differentiator", "Organic Lemon8 viral", "3 platforms active (FB/IG/TikTok)"],
        "promotions": [],
        "weaknesses": ["ปิด 15:00 เสียตลาดบ่าย-เย็น", "ไม่มี delivery แอปใดเลย", "ไม่มี LINE OA/loyalty", "Followers ไม่ทราบ อาจยังเล็ก", "ราคา workshop ไม่โปร่งใสออนไลน์"],
        "location": "ซอยเปิ้ลส้มตำ อ.เมือง จ.สกลนคร", "hours": "จ-ศ 08:00-15:00 / เสาร์-อาทิตย์ 09:00-15:00",
        "social_trend": {"primary_platform":"Facebook","posting_frequency":"สม่ำเสมอ","content_style":"Minimalist aesthetic + slow life · #มีสุขในทุกๆวัน","engagement_level":"low-medium"},
        "delivery": {
            "primary_app": "ไม่มี",
            "apps": [],
            "peak_hours": "N/A — ไม่มี delivery",
            "active_promos": [],
            "notes": "ไม่พบบน LINE MAN, GrabFood, Wongnai Delivery เลย — dine-in + takeaway เท่านั้น ปิด 15:00 ทำให้ delivery window แคบมาก"
        }
    },
    {
        "id": "competitor-alice",
        "category": "competitor",
        "title": "Alice Coffee and Bread สกลนคร (Verified 21 May 2026)",
        "summary": "Minimalist White + Rabbit Theme · ราคาเข้าถึงได้ (เริ่ม ~45฿) · ทำเลดีใกล้ศาลากลาง · LINE MAN delivery ยืนยัน · Instagram อ่อนมาก (29 followers) · ไม่มี TikTok official",
        "updated": "21 May 2026",
        "source_url": "https://www.facebook.com/p/Alice-Cafe-Sakonnakhon-61550985398170/", "thumbnail_url": "",
        "tags": ["สกลนคร", "Local", "Independent", "Minimalist", "Bakery", "Instagrammable"],
        "relevance": "high",
        "detail": "Alice Coffee and Bread Sakonnakhon — 1894/89 ถ.สุขสวัสดิ์ แขวงธาตุเชิงชุม เมืองสกลนคร (ใกล้ศาลากลางจังหวัด)\nเปิด: ม.ค. 2024 | โทร: 094-274-5558\n\nConcept: Minimalist White + Rabbit Theme — โทนขาวอบอุ่น Instagram-worthy\nสวนเล็กสไตล์ญี่ปุ่น (outdoor) + แอร์ (indoor) · Wi-Fi · Pet-friendly\n\nSocial Media (verified):\n• Facebook: ~2,629 likes / 3,378 check-ins — มี 2 หน้า (แยก follower)\n• Instagram: @alicecoffee.sakon · 29 followers · 16 posts (อ่อนมาก)\n• TikTok: ไม่มี official account — แต่ creator รีวิวเยอะ (@woranitbell ฯลฯ)\n• Wongnai: 5.0/5.0 (1 review เท่านั้น)\n\nDelivery: LINE MAN ยืนยัน, Wongnai x LINE MAN · จ-ศ 08:30-16:30 / เสาร์ 09:00-17:30\nเมนู delivery ยอดนิยม: Thai Tea Special Blend 65฿, Coco Dirty 95฿, Chocolate Hazelnut 90฿\n\nช่องว่างสำหรับคู่แข่ง:\n• TikTok official — Alice ยังไม่มีเลย ทั้งที่ organic viral มีแล้ว\n• Wongnai reviews — มีแค่ 1 review\n• GrabFood/ShopeeFood — ยังไม่อยู่บนแพลตฟอร์ม\n• ราคาเมนูโปร่งใสออนไลน์ — ระบุชัดแค่ 3 เมนู",
        "pricing": {
            "espresso":{"price":"","note":""},"americano":{"price":"","note":""},
            "latte":{"price":"","note":""},"cappuccino":{"price":"","note":""},
            "cold_brew":{"price":"","note":""},"frappe":{"price":"","note":""},
            "matcha":{"price":"","note":"Matcha Margarita"},"signature_drink":{"price":"95","note":"Coco Dirty (ขายดี)"},
            "food":{"price":"","note":"Chiffon/Tiramisu/Dirty Cake อบสด"},
            "other": [{"name":"Thai Tea Special Blend","price":"65"},{"name":"Chocolate Hazelnut","price":"90"},{"name":"ราคาเริ่มต้น","price":"~45"}]
        },
        "strengths": ["ราคาเข้าถึงได้ เริ่ม ~45฿", "Concept ชัด Rabbit+Minimalist", "Organic TikTok viral ไม่ต้องซื้อ ads", "ทำเลดีใกล้ศาลากลาง", "LINE MAN delivery ยืนยัน", "เบเกอรีอบสดหลากหลาย"],
        "promotions": [],
        "weaknesses": ["Instagram 29 followers (16 posts) อ่อนมาก", "ไม่มี TikTok official", "Wongnai 1 review credibility ต่ำ", "Facebook 2 หน้า — follower กระจัดกระจาย", "GrabFood/ShopeeFood ยังไม่มี"],
        "location": "1894/89 ถ.สุขสวัสดิ์ แขวงธาตุเชิงชุม เมืองสกลนคร", "hours": "จ-ศ 08:00-17:00 / พุธ,เสาร์-อาทิตย์ 09:00-18:00",
        "social_trend": {"primary_platform":"Facebook","posting_frequency":"ปานกลาง","content_style":"Minimalist aesthetic + เบเกอรี","engagement_level":"low"},
        "delivery": {
            "primary_app": "LINE MAN",
            "apps": ["LINE MAN", "Wongnai Delivery"],
            "peak_hours": "08:30-16:30 (ตามเวลาร้าน)",
            "active_promos": [],
            "notes": "LINE MAN verified, Wongnai x LINE MAN ยืนยัน · ไม่พบบน GrabFood/ShopeeFood · ค่าส่งเริ่ม 0 บาทในพื้นที่บริการ"
        }
    },
    {
        "id": "competitor-elemental",
        "category": "competitor",
        "title": "Elemental Haus สกลนคร (Updated 9 Jun 2026)",
        "summary": "Specialty Coffee + In-house Roastery \"Blanka\" · เล็กๆแต่เด็ด · ทำเลใกล้ มรภ.สกลนคร · LINE MAN ✅ เปิดถึง 19:00 · Facebook 101 likes (ต่ำสุดกลุ่ม) · Wongnai 0 reviews · TikTok @elemental.haus active (วาดแก้วเองไวรัล) · Instagram UGC พบแล้ว",
        "updated": "9 Jun 2026",
        "source_url": "https://www.facebook.com/elementalhaus/",
        "thumbnail_url": "",
        "tags": ["สกลนคร", "Local", "Independent", "Specialty", "Roastery", "Artisanal", "University"],
        "relevance": "high",
        "detail": "Elemental Haus (Specialty Coffee + Blanka roastery coffee)\n29/31 ถ.นิตโย พังขว้าง เมืองสกลนคร (บ้านเด่นธานี ใกล้โรงแรม Livable ตรงข้ามวิทยาลัยเทคนิคสกลนคร / หน้า มรภ.สกลนคร)\nโทร: 080-420-0088 · เปิด: ทุกวัน 08:00-19:00 · เปิดกิจการ: กุมภาพันธ์ 2024\n\nConcept: Specialty Coffee + In-house Roastery (Blanka roastery) — \"เล็กๆแต่เด็ด\"\nUSP: ทั้ง specialty coffee และ bar concept · wall art วาดเองทั้งร้าน (รวมห้องน้ำ) · handwritten labels บนแก้ว\n\nSocial Media (verified 9 Jun 2026):\n• Facebook: elementalhaus · ~101 likes (อ่อนที่สุดในกลุ่ม — ไม่เปลี่ยน)\n• TikTok: @elemental.haus · official active account · พบ creative content ใหม่: 'ร้านกาแฟที่เวลาแก้วสกรีนหมด ก็ต้องนั่งวาดเองไปก่อน' = personality-driven viral potential\n• Instagram: ไม่มี official account · แต่พบ UGC post 'มาสกลต้องมาชิม Elemental Haus คาเฟ่เล็กๆแต่เด็ดด้วย' (มิ.ย. 2026)\n• Wongnai: Listed (0 reviews, 0 ratings — ไม่เปลี่ยน)\n\nเมนู: กาแฟส้มคั่ว (หวานน้อย เปรี้ยวนิดๆ), Hojicha Latte iced · ฿ category (ต่ำกว่า 100 บาท)\nPromo: Own cup ลด 5 บาท · Loyalty: ระบบ points redeem\nAmenities: Wi-Fi · Pet-friendly · Credit card · Parking · 11-40 ที่นั่ง\n\nทำเลใกล้มหาวิทยาลัย: student/academic crowd เป็น core audience\n\nช่องว่างสำหรับคู่แข่ง:\n• Facebook 101 likes ต่ำสุดกลุ่ม — social awareness แทบไม่มี\n• Wongnai 0 reviews — credibility ต่ำที่สุด\n• ไม่มี Instagram official — visual platform ว่างเปล่า\n• ยังไม่มี signature drink ที่โดดเด่น\n• TikTok creative content กำลังพัฒนา — อาจ viral ถ้าลูกค้าแชร์",
        "pricing": {
            "espresso": {"price": "", "note": ""},
            "americano": {"price": "", "note": ""},
            "latte": {"price": "", "note": "฿ category (<100฿)"},
            "cappuccino": {"price": "", "note": ""},
            "cold_brew": {"price": "", "note": ""},
            "frappe": {"price": "", "note": ""},
            "matcha": {"price": "", "note": ""},
            "signature_drink": {"price": "", "note": "กาแฟส้มคั่ว (หวานน้อย เปรี้ยวนิดๆ)"},
            "food": {"price": "", "note": ""},
            "other": [{"name": "Hojicha Latte iced", "price": ""}, {"name": "Own cup discount", "price": "-5฿"}]
        },
        "strengths": ["Blanka in-house roastery = quality signal", "Artisanal identity ชัด (wall art + handwritten labels)", "ทำเลใกล้ มรภ.สกลนคร = student loyalty สูง", "LINE MAN ✅ เปิดถึง 19:00", "Loyalty points system", "Eco-friendly own-cup discount", "TikTok official active"],
        "promotions": ["Own cup ลด 5 บาท (Coffee + Non-Coffee)", "ระบบ points redeem (10 points)"],
        "weaknesses": ["Facebook 101 likes ต่ำที่สุดในกลุ่ม", "Wongnai 0 reviews credibility ต่ำสุด", "ไม่มี Instagram official", "ทำเลชานเมือง เข้าถึงยากจากใจกลาง", "ยังไม่มี signature drink ที่โดดเด่น"],
        "location": "29/31 ถ.นิตโย พังขว้าง เมืองสกลนคร (บ้านเด่นธานี หน้า มรภ.สกลนคร)",
        "hours": "ทุกวัน 08:00-19:00",
        "social_trend": {"primary_platform": "TikTok", "posting_frequency": "ปานกลาง", "content_style": "Artisanal craft · handmade aesthetic · specialty roastery story · personality-driven (วาดแก้วเอง)", "engagement_level": "low-medium (social presence ยังอ่อน แต่ TikTok content เริ่มมี personality)"},
        "delivery": {
            "primary_app": "LINE MAN",
            "apps": ["LINE MAN", "Wongnai Delivery"],
            "peak_hours": "08:00-19:00 (ตามเวลาร้าน)",
            "active_promos": ["ค่าส่งเริ่ม 0฿ ในพื้นที่บริการ"],
            "notes": "LINE MAN ✅ ยืนยัน (9 Jun 2026) via Wongnai · ไม่พบบน GrabFood/ShopeeFood/FoodPanda"
        }
    },
    {
        "id": "competitor-jumpot",
        "category": "competitor",
        "title": "จุมพฏ-kuckhang / กินกาแฟหรือยังครับ สกลนคร (Verified 22 May 2026)",
        "summary": "\"คาเฟ่ลับ\" + Art Toy collector's café · 2 สาขา (ต้นกำเนิด + บายพาส) · Latte 65฿ (ถูกสุดกลุ่ม) · TikTok @jumpotcoffee active · LINE MAN ✅ สั่ง LINE โดยตรงได้ · Wongnai credibility ต่ำมาก (1 review) · ปิด 16:00",
        "updated": "22 May 2026",
        "source_url": "https://www.facebook.com/profile?id=61555411775637",
        "thumbnail_url": "",
        "tags": ["สกลนคร", "Local", "Independent", "Hidden café", "Art Toy", "Nostalgia", "Specialty"],
        "relevance": "high",
        "detail": "จุมพฏ-kuckhang / กินกาแฟหรือยังครับ / คักแฮง\n\nสาขาต้นกำเนิด: 609 ถ.กำจัดภัย ธาตุเชิงชุม เมืองสกลนคร (ซอยข้างร้านเสริมสวยดุสิตา)\nโทร: 080-939-8210 · เปิด: ทุกวัน 07:30-16:00\n\nสาขาบายพาส: 116/11 ถ.บ้านโคกสว่าง ธาตุเชิงชุม เมืองสกลนคร\nโทร: 084-286-6471 · เปิด: ทุกวัน 08:30-16:00\n\nConcept: \"คาเฟ่ลับ\" + Art Toy Collectors' Café — ความ hidden/secret ใช้เป็น marketing tool หลัก\n\nบรรยากาศ (ต้นกำเนิด):\n• บ้านไม้วินเทจ ป้ายสีฟ้าเฟด เลข 609\n• ผนังอิฐ + โปสเตอร์หนัง vintage (Back to the Future, My Neighbor Totoro)\n• ของเล่น collector เยอะมาก: Peppa Pig, Toy Story (Lotso), Ted, Mazinger Z, N64, Hot Wheels, Transformer\n• ตู้โชว์เมล็ดกาแฟ + QR code สั่ง\n• เหมาะถ่ายรูป art/nostalgic style\n\nSocial Media:\n• Facebook: กินกาแฟหรือยังครับ (followers ไม่ทราบ)\n• TikTok: @jumpotcoffee — official active account\n• LINE: @jumpot — รับ order โดยตรง\n• Wongnai: Listed ทั้ง 2 สาขา (0-1 review — credibility ต่ำมาก)\n• Lemon8: organic viral — visitors review เยอะ\n\nPromotion: บัตรสมาชิกฟรี จำนวนจำกัด (LINE @jumpot)\nSpecial: ใช้นม mmilk (lactose-free) · ขาย retail beans\n\nช่องว่างสำหรับคู่แข่ง:\n• ปิด 16:00 — ตลาดช่วง 16:00-22:00 ว่างทั้งหมด\n• Wongnai credibility ต่ำมาก (1 review)\n• \"ลับ\" มากจนหาไม่เจอ = barrier สำหรับลูกค้าใหม่",
        "pricing": {
            "espresso": {"price": "", "note": ""},
            "americano": {"price": "", "note": ""},
            "latte": {"price": "65", "note": "ถูกสุดในกลุ่ม"},
            "cappuccino": {"price": "", "note": ""},
            "cold_brew": {"price": "", "note": ""},
            "frappe": {"price": "", "note": ""},
            "matcha": {"price": "", "note": ""},
            "signature_drink": {"price": "", "note": "Thai Tea (หอมมาก)"},
            "food": {"price": "", "note": "ขนมปังโทสต์ (\"อร่อยมาก\")"},
            "other": [{"name": "Retail beans", "price": "ไม่ทราบ"}, {"name": "บัตรสมาชิก", "price": "ฟรี (จำกัด)"}]
        },
        "strengths": ["\"คาเฟ่ลับ\" positioning สร้าง organic curiosity", "Art Toy aesthetic ไม่มีร้านใดในสกลนครทำ", "Latte 65฿ ถูกสุดในกลุ่ม", "TikTok @jumpotcoffee official active", "LINE order + LINE MAN ง่ายต่อ conversion", "Lactose-free milk option = thoughtful niche", "2 สาขา = brand กำลังเติบโต"],
        "promotions": ["บัตรสมาชิกฟรี จำนวนจำกัด (ลงทะเบียน LINE @jumpot)"],
        "weaknesses": ["ปิด 16:00 — ตลาดช่วงบ่ายเย็น-ค่ำว่างทั้งหมด", "Wongnai credibility ต่ำ (0-1 review)", "ความ 'ลับ' = barrier ลูกค้าใหม่หาไม่เจอ", "Facebook followers ไม่ทราบ"],
        "location": "ต้นกำเนิด: 609 ถ.กำจัดภัย ธาตุเชิงชุม | บายพาส: 116/11 ถ.บ้านโคกสว่าง ธาตุเชิงชุม",
        "hours": "ต้นกำเนิด: ทุกวัน 07:30-16:00 | บายพาส: ทุกวัน 08:30-16:00",
        "social_trend": {"primary_platform": "TikTok+LINE", "posting_frequency": "ปานกลาง", "content_style": "Hidden café discovery · Art Toy showcase · nostalgic aesthetic", "engagement_level": "medium (organic UGC สูง)"},
        "delivery": {
            "primary_app": "LINE MAN",
            "apps": ["LINE MAN", "Wongnai Delivery", "LINE @jumpot"],
            "peak_hours": "07:30-15:30 (ตามเวลาร้าน ปิด 16:00)",
            "active_promos": ["ค่าส่งเริ่ม 0฿ ในพื้นที่บริการ"],
            "notes": "LINE MAN verified via Wongnai (ทั้ง 2 สาขา) · สั่งได้ผ่าน LINE @jumpot โดยตรง · ไม่พบบน GrabFood/ShopeeFood"
        }
    },
    {
        "id": "competitor-sniff",
        "category": "competitor",
        "title": "SNIFF specialty coffee สกลนคร (Verified 22 May 2026)",
        "summary": "ใหญ่ที่สุดใน local specialty สกลนคร · FB 6,800 followers · 2 สาขา (สาขาหลัก + SNIFF Roastery บายพาส) · In-house roasting · LINE MAN delivery ✅ · Wongnai 4.1/5 (28 reviews) สูงสุดกลุ่ม · Instagram อ่อน (448 followers) · TikTok official ยังไม่มี",
        "updated": "22 May 2026",
        "source_url": "https://www.facebook.com/SNIFFspecialtycoffee",
        "thumbnail_url": "",
        "tags": ["สกลนคร", "Local", "Independent", "Specialty", "Roastery", "Multi-branch", "Blue-aesthetic"],
        "relevance": "high",
        "detail": "SNIFF specialty coffee (สนิฟ สเปเชียลตี้ คอฟฟี่)\nสาขาหลัก: 1748/25-26 ถ.ต.พัฒนา ต.ธาตุเชิงชุม อ.เมืองสกลนคร (ใกล้โรงเรียนเปลี่ยนชัย แยก 4 นาฬิกา)\nSNIFF Roastery: 985 ตำบลดงมะไฟ อ.เมืองสกลนคร (บายพาส — สาขาใหม่ ใหญ่กว่า)\nโทร: 096-946-4792 / 088-736-8446\nเวลา: สาขาหลัก ทุกวัน 07:30-19:00 | Roastery จ-ศ 07:30-19:00, เสาร์-อาทิตย์ 10:00-19:00\n\nConcept: In-house Roastery + Specialty Coffee — ย่างเมล็ดเอง, single-origin หลากหลาย (light-dark roast)\nSpecialty bean surcharge: +10฿ — signal คุณภาพที่ชัดเจน\n\nSocial Media (verified):\n• Facebook: SNIFFspecialtycoffee · 6,800 followers · 100% recommend (50 reviews) — ใหญ่ที่สุดใน local specialty สกลนคร\n• Instagram: @sniffspecialtycoffee · 448 followers (อ่อนมาก ไม่สัมพันธ์กับขนาดร้าน)\n• TikTok: ไม่มี official account — แต่ visitor content มีอยู่\n• Wongnai: 4.1/5 (35 ratings, 28 reviews) · WongnaiSpecialist + CoffeeSpecialist badge\n• TripAdvisor: Listed, 0 reviews\n\nบรรยากาศ: ผนังสีน้ำเงิน + ivy plants + pendant lights + artwork · Counter bar ชมบาริสต้าได้ · Indoor + Outdoor · 11-40 ที่นั่ง\nRoastery สาขาใหม่: ใหญ่กว่า มีสไตล์ บรรยากาศดี ถ่ายรูปสวย\n\nExtra: ขายเมล็ดกาแฟ retail · Pet-friendly · Wi-Fi · Credit card · Parking\n\nช่องว่างสำหรับคู่แข่ง:\n• TikTok official ยังไม่มี — blind spot ใหญ่ reach คนรุ่นใหม่\n• Instagram อ่อน (448 followers) ทั้งที่ร้านใหญ่ที่สุดในกลุ่ม\n• TripAdvisor 0 reviews — เสีย SEO นักท่องเที่ยวต่างชาติ",
        "pricing": {
            "espresso": {"price": "75", "note": ""},
            "americano": {"price": "75", "note": "+10฿ specialty bean surcharge"},
            "latte": {"price": "85", "note": "Ice Latte Special Blend"},
            "cappuccino": {"price": "", "note": ""},
            "cold_brew": {"price": "", "note": ""},
            "frappe": {"price": "", "note": ""},
            "matcha": {"price": "", "note": ""},
            "signature_drink": {"price": "99", "note": "Hojicha Latte"},
            "food": {"price": "", "note": "Croissant, Brownie"},
            "other": [{"name": "Hot Honey Latte", "price": "~95"}, {"name": "Americano Brazil", "price": "85"}, {"name": "Malagasy", "price": ""}]
        },
        "strengths": ["FB 6,800 followers ใหญ่สุดใน local specialty สกลนคร", "Wongnai 28 reviews credibility สูงสุดกลุ่ม", "2 สาขา = brand กำลังเติบโต", "In-house roastery = brand story ทรงพลัง", "Retail beans = รายได้เพิ่ม + loyalty", "LINE MAN ยืนยัน เปิด 07:30 (morning rush)"],
        "promotions": [],
        "weaknesses": ["Instagram 448 followers — อ่อนมากไม่สัมพันธ์ขนาดร้าน", "TikTok official ยังไม่มีเลย", "TripAdvisor 0 reviews เสีย SEO ท่องเที่ยว", "ราคาเมนูไม่ระบุครบออนไลน์"],
        "location": "สาขาหลัก: 1748/25-26 ถ.ต.พัฒนา ต.ธาตุเชิงชุม อ.เมืองสกลนคร | Roastery: 985 ตำบลดงมะไฟ อ.เมืองสกลนคร",
        "hours": "สาขาหลัก: ทุกวัน 07:30-19:00 | Roastery: จ-ศ 07:30-19:00 / เสาร์-อาทิตย์ 10:00-19:00",
        "social_trend": {"primary_platform": "Facebook", "posting_frequency": "ปานกลาง", "content_style": "Specialty coffee culture · Blue-tone aesthetic · barista content · multi-location expansion", "engagement_level": "medium-high"},
        "delivery": {
            "primary_app": "LINE MAN",
            "apps": ["LINE MAN", "Wongnai Delivery"],
            "peak_hours": "07:30-18:30",
            "active_promos": ["ค่าส่งเริ่ม 0฿ ในพื้นที่บริการ"],
            "notes": "LINE MAN verified via Wongnai · WongnaiSpecialist + CoffeeSpecialist badge · ไม่พบบน GrabFood/ShopeeFood"
        }
    },
    {
        "id": "competitor-roknroad",
        "category": "competitor",
        "title": "Rok 'n Road Coffee",
        "summary": "Vintage eclectic hidden gem · Hand-ground Arabica จากเชียงใหม่ · Beer + BBQ evenings · Google 4.6/5 · Facebook 4.8/5 · ต่ำกว่า 10 ที่นั่ง · ไม่มี official social",
        "updated": "22 May 2026",
        "source_url": "https://www.wongnai.com/restaurants/951527qf-rok-n-road-coffee",
        "thumbnail_url": "",
        "tags": ["specialty", "vintage", "hidden-gem", "bar", "hand-ground", "arabica"],
        "relevance": "high",
        "detail": "Vintage eclectic café ใน 291 ซอยมหาวงษ์ ใกล้ Robinson's · บรรยากาศ American flag + bowling pin sign + typewriter + bamboo beach bar + cat mascots · Hand-ground Arabica จากเชียงใหม่ (slow-drip) · Beer + BBQ Ribs + Cheeseburger ช่วงเย็น = Café & Bar hybrid ที่ unique ที่สุดในกลุ่ม · Google 4.6/5 (37 reviews) + Facebook 4.8/5 (74 reviews) = rating ดีที่สุดในกลุ่ม · ต่ำกว่า 10 ที่นั่ง = capacity limit สุดๆ · ไม่มี official social media แม้แต่แพลตฟอร์มเดียว",
        "pricing": {
            "espresso": {"price": "", "note": "฿ category (<100 บาท)"},
            "americano": {"price": "", "note": ""},
            "latte": {"price": "", "note": ""},
            "cappuccino": {"price": "", "note": ""},
            "cold_brew": {"price": "", "note": "Hand-ground Arabica จากเชียงใหม่"},
            "frappe": {"price": "", "note": ""},
            "matcha": {"price": "", "note": ""},
            "signature_drink": {"price": "", "note": "Hand-ground Arabica slow-drip"},
            "food": {"price": "", "note": "BBQ Ribs + Cheeseburger (evenings)"},
            "other": [{"name": "Beer", "price": "ไม่ทราบ"}]
        },
        "strengths": ["Google 4.6/5 (37 reviews) + Facebook 4.8/5 (74 reviews) = rating ดีที่สุดในกลุ่ม", "Hand-ground Arabica จากเชียงใหม่ + slow-drip = quality signal ชัด", "Beer + BBQ evenings = unique revenue stream ที่ไม่มีร้านไหนทำ", "Vintage eclectic aesthetic หายากมากในสกลนคร", "LINE MAN ✅"],
        "promotions": [],
        "weaknesses": ["ต่ำกว่า 10 ที่นั่ง — capacity limit ใหญ่ที่สุดในกลุ่ม", "ไม่มี official social media แม้แต่บัญชีเดียว — 0% proactive marketing", "ปิดวันอังคาร + เปิดเฉพาะ 10:00–17:00 — ไม่มี morning rush และ evening crowd", "GPS ยาก — barrier สูงสำหรับลูกค้าใหม่", "Wongnai 0 reviews — credibility delivery ต่ำมาก"],
        "location": "291 ซอยมหาวงษ์ ธาตุนาแวง เมืองสกลนคร (ใกล้ Robinson's, ซอยเดียวกับ O2 Hotel)",
        "hours": "จ. 10:30-16:30 · อ. ปิด · พ.-เสาร์ 10:00-17:00 · อาทิตย์ 11:00-17:00",
        "social_trend": {"primary_platform": "Facebook (personal)", "posting_frequency": "ไม่มี official content", "content_style": "Vintage eclectic · American flag · cat mascots · hidden gem · UGC-driven", "engagement_level": "low (no official account)"},
        "delivery": {
            "primary_app": "LINE MAN",
            "apps": ["LINE MAN", "Wongnai Delivery"],
            "peak_hours": "10:00-17:00 (window แคบ — ไม่มี morning rush)",
            "active_promos": ["ค่าส่งเริ่ม 0฿ ในพื้นที่บริการ"],
            "notes": "LINE MAN verified via Wongnai · ไม่พบ GrabFood/ShopeeFood · ปิดวันอังคาร"
        }
    },
    {
        "id": "competitor-chann",
        "category": "competitor",
        "title": "CHANN CAFE : ชานคาเฟ่",
        "summary": "บ้านเรือนไทยจากไม้เก่า 10+ ปี · Pet-friendly · ทำเลดี ถ.เสรีไทยใจกลางเมือง · ที่จอดรถ ~30 คัน · Instagram @chann.cafe 112 posts · UGC TikTok 8,414 likes · เปิด พ.ย. 2024",
        "updated": "22 May 2026",
        "source_url": "https://www.wongnai.com/restaurants/3633744Aj-chann-cafe",
        "thumbnail_url": "",
        "tags": ["thai-house", "pet-friendly", "aesthetic", "merchandise", "new-cafe", "fusion"],
        "relevance": "high",
        "detail": "CHANN CAFE ที่ 146/4 ถ.เสรีไทย ใจกลางเมือง · สร้างจากบ้านเรือนไทยเก่า ไม้สะสม 10+ ปีจากทั่วสกลนคร โดยช่างไม้เชื้อสายเวียดนาม · concept 'ชานบ้าน' = ความอบอุ่น เรือนไทย + modern · Pet-friendly (น้องหมาเข้าแอร์ได้) = differentiator ที่ไม่มีร้านไหนในกลุ่มทำ · ที่จอดรถ ~30 คัน ใหญ่ที่สุดในกลุ่ม · Instagram @chann.cafe 112 posts (brand investment สูง) · TikTok UGC viral 8,414+ likes · Merchandise line (แก้ว, กระเป๋า, หมวก, เสื้อ) · บิงซูชาไทยเกล็ดหิมะ = new menu · Wongnai 0 reviews แต่ OFFICIAL status · เปิด Soft Opening พ.ย. 2024",
        "pricing": {
            "espresso": {"price": "", "note": "เริ่ม 75฿"},
            "americano": {"price": "", "note": ""},
            "latte": {"price": "", "note": "~100฿"},
            "cappuccino": {"price": "", "note": ""},
            "cold_brew": {"price": "", "note": ""},
            "frappe": {"price": "", "note": ""},
            "matcha": {"price": "", "note": "Matcha latte available"},
            "signature_drink": {"price": "", "note": "ชาไทยคาราเมล · บิงซูชาไทย (new)"},
            "food": {"price": "", "note": "ครัวซอง 70฿ · Green tea cake · Chocolate cake · Tiramisu · Banoffee"},
            "other": [{"name": "ชาเขียว", "price": "50฿"}, {"name": "Merchandise (แก้ว/กระเป๋า/หมวก/เสื้อ)", "price": "ไม่ทราบ"}]
        },
        "strengths": ["Pet-friendly (น้องหมาเข้าแอร์) = differentiator ที่ไม่มีร้านอื่นในกลุ่ม", "ทำเลดี ถ.เสรีไทย ใจกลางเมือง + ที่จอดรถ ~30 คัน", "Brand story ทรงพลัง — ไม้เก่า 10+ ปี ช่างฝีมือเชื้อสายเวียดนาม", "Instagram 112 posts (6 เดือน) = brand commitment สูง", "TikTok UGC viral 8,414+ likes single video", "Merchandise line = brand loyalty + passive income"],
        "promotions": [],
        "weaknesses": ["Instagram 464 followers ยังต่ำ (112 posts แต่ follower น้อย = low conversion)", "Wongnai 0 reviews — credibility delivery ต่ำ", "ยังใหม่ (เปิด พ.ย. 2024) — brand recognition อยู่ระหว่างสร้าง", "ปิด 17:00/18:00 — ไม่มี evening crowd"],
        "location": "146/4 ถ.เสรีไทย ธาตุนาเวง เมืองสกลนคร (ติดร้านข้าวมันไก่แดงดำ)",
        "hours": "จ.–ศ. 08:00–17:00 · เสาร์–อาทิตย์ 08:00–18:00",
        "social_trend": {"primary_platform": "Instagram + TikTok", "posting_frequency": "สม่ำเสมอ (112 posts/6 เดือน IG)", "content_style": "Thai house aesthetic · ชานบ้าน warmth · pet-friendly · photo spots · merchandise", "engagement_level": "medium (growing rapidly)"},
        "delivery": {
            "primary_app": "LINE MAN",
            "apps": ["LINE MAN", "Wongnai Delivery"],
            "peak_hours": "08:00-17:00 จ-ศ · 08:00-18:00 เสาร์-อาทิตย์",
            "active_promos": ["ค่าส่งเริ่ม 0฿ ในพื้นที่บริการ"],
            "notes": "LINE MAN verified via Wongnai OFFICIAL · ไม่พบ GrabFood/ShopeeFood · เสาร์-อาทิตย์ window กว้างกว่า"
        }
    },
    {
        "id": "competitor-boonnar",
        "category": "competitor",
        "title": "BOONNAR ART SPACE (บุญหนา อาร์ต สเปซ)",
        "summary": "Art Gallery + Café + Art School ร้านเดียวในสกลนคร · Blue Bica Coffee ชั้น 1 · Gallery ชั้น 3 · Art class 390฿ · Mascot ก่ำบอย · ตั้งชื่อตามหลวงปู่บุญหนา · เปิด ก.ย. 2023",
        "updated": "23 May 2026",
        "source_url": "https://www.wongnai.com/restaurants/2681276cf-boonnar-art-space",
        "thumbnail_url": "",
        "tags": ["art-gallery", "art-space", "community", "cultural", "specialty", "creative"],
        "relevance": "high",
        "detail": "BOONNAR ART SPACE ที่ 1751/1 ถ.รอบเมือง ใกล้ รพ.รักษ์สกล · 3 floors: ชั้น 1 Blue Bica Coffee, ชั้น 2 Art class เด็ก, ชั้น 3 Gallery · ก่อตั้งโดยครูเตย (ไอรัตน์ดา มหาชัย) จิตรกร-ครูสอนศิลปะ · ตั้งชื่อตามหลวงปู่บุญหนา ธมฺมทินฺโน พระดังสกลนคร · Mascot 'ก่ำบอย' เด็กใส่ชุดปลาอีก่ำ (ปลาประจำจังหวัด) = street art ทั่วเมือง · NEA CRU exhibitions หมุนเวียน = เหตุผลกลับมาซ้ำ · Art class เด็ก 390฿/ครั้ง = revenue เพิ่ม · ร้านเดียวในสกลนครที่รวม gallery + café + school",
        "pricing": {
            "espresso": {"price": "", "note": "฿ category (<100 บาท)"},
            "americano": {"price": "", "note": ""},
            "latte": {"price": "", "note": "Blue Bica Coffee brand"},
            "cappuccino": {"price": "", "note": ""},
            "cold_brew": {"price": "", "note": ""},
            "frappe": {"price": "", "note": ""},
            "matcha": {"price": "", "note": "เมนูแนะนำ"},
            "signature_drink": {"price": "", "note": "Italian Soda: พีช, สตรอว์เบอร์รี, ลิ้นจี่"},
            "food": {"price": "", "note": ""},
            "other": [{"name": "Art class เด็ก (กับครูเตย)", "price": "390฿/ครั้ง"}]
        },
        "strengths": ["ร้านเดียวในสกลนครที่เป็น Art Gallery + Café + Art School = zero competition", "'ก่ำบอย' mascot + ปลาอีก่ำ = brand tie-in กับอัตลักษณ์สกลนครลึกมาก", "ตั้งชื่อตามหลวงปู่บุญหนา = cultural credibility สูงในชุมชน", "Art class 390฿ = revenue stream อิสระจากยอดกาแฟ", "NEA CRU rotating exhibitions = reason to return ทุก season", "เปิดเสาร์-อาทิตย์ถึง 19:00 · Wi-Fi · Parking · Pet-friendly"],
        "promotions": [],
        "weaknesses": ["Wongnai 0 reviews — credibility delivery ต่ำ", "Art class 390฿ = barrier สูงสำหรับ walk-in casual", "ที่ตั้ง ถ.รอบเมือง (ไม่ใช่ main street) — accessibility ต่ำกว่า CHANN", "Social followers ไม่ทราบ — ไม่รู้ actual reach", "Delivery ปิด 17:00 ทุกวัน แม้ร้านเปิดถึง 19:00 เสาร์-อาทิตย์"],
        "location": "1751/1 ถ.รอบเมือง ต.ธาตุเชิงชุม อ.เมืองสกลนคร (~50 ม. จาก รพ.รักษ์สกล)",
        "hours": "อ.–ศ. 07:00–17:00 · เสาร์–อาทิตย์ 07:00–19:00",
        "social_trend": {"primary_platform": "Facebook + Instagram + TikTok", "posting_frequency": "ปานกลาง (art content + exhibition updates)", "content_style": "Art gallery · ก่ำบอย mascot · NEA CRU exhibition · art class · local culture", "engagement_level": "medium (unknown followers)"},
        "delivery": {
            "primary_app": "LINE MAN",
            "apps": ["LINE MAN", "Wongnai Delivery"],
            "peak_hours": "07:00-17:00 (ทุกวัน)",
            "active_promos": ["ค่าส่งเริ่ม 0฿ ในพื้นที่บริการ"],
            "notes": "LINE MAN via Wongnai · delivery ปิด 17:00 แม้ร้านเปิด 19:00 เสาร์-อาทิตย์ · ไม่พบ GrabFood/ShopeeFood"
        }
    },
    {
        "id": "competitor-acupofjoycoffee",
        "category": "competitor",
        "title": "A Cup Of Joy Coffee",
        "summary": "Specialty coffee สำหรับคนพิเศษ · ถ.สุขเกษม ใกล้ Imperial Hotel · ต่ำกว่า 10 ที่นั่ง · เมล็ดกาแฟหลากหลาย (Americano Yellow Columbia) · ฿ category · LINE MAN ✅ · ไม่มี IG/TikTok",
        "updated": "23 May 2026",
        "source_url": "https://www.wongnai.com/restaurants/1226140rF-a-cup-of-joy-coffee",
        "thumbnail_url": "",
        "tags": ["specialty", "small-cafe", "coffee-bean", "affordable", "delivery"],
        "relevance": "high",
        "detail": "A Cup Of Joy Coffee ที่ 1305/40 ถ.สุขเกษม ดงมะไฟ เมืองสกลนคร (ทางเข้า Imperial Hotel) · specialty coffee ราคาเข้าถึงได้ (<100฿) · tagline 'กาแฟพิเศษ สำหรับคนพิเศษ' · เมล็ดกาแฟหลากหลาย เช่น Americano Yellow Columbia · ต่ำกว่า 10 ที่นั่ง · ปิด 16:00 · Facebook active แต่ไม่มี IG/TikTok · Wongnai 1-2 reviews (2021-2022) เท่านั้น · LINE MAN ✅ via Wongnai",
        "pricing": {
            "espresso": {"price": "", "note": ""},
            "americano": {"price": "", "note": "Americano Yellow Columbia — เมนูแนะนำ"},
            "latte": {"price": "", "note": "<100฿"},
            "cappuccino": {"price": "", "note": ""},
            "cold_brew": {"price": "", "note": ""},
            "frappe": {"price": "", "note": ""},
            "matcha": {"price": "", "note": ""},
            "signature_drink": {"price": "", "note": "Special Coffee (multiple bean selections)"},
            "food": {"price": "", "note": ""},
            "other": []
        },
        "strengths": ["'กาแฟพิเศษ สำหรับคนพิเศษ' = positioning ชัดสำหรับ specialty niche", "เมล็ดกาแฟหลากหลาย = differentiator สำหรับคนรู้กาแฟ", "ราคา <100฿ = accessible specialty", "LINE MAN ✅ + pre-order pickup", "Amenities ครบ: Wi-Fi, Parking, Pet-friendly"],
        "promotions": [],
        "weaknesses": ["ต่ำกว่า 10 ที่นั่ง — capacity จำกัดมาก", "ไม่มี Instagram/TikTok — visual marketing ศูนย์", "ปิด 16:00 — ไม่มี afternoon-evening market เลย", "Wongnai reviews น้อยมากและเก่า (2021-2022) — แทบไม่มี social proof", "ทำเล ถ.สุขเกษม — ไม่ใช่ main café street"],
        "location": "1305/40 ถ.สุขเกษม ดงมะไฟ เมืองสกลนคร (ทางเข้า Imperial Hotel)",
        "hours": "จ.–ศ. 08:00–16:00 · เสาร์–อาทิตย์ 09:00–16:00",
        "social_trend": {"primary_platform": "Facebook", "posting_frequency": "ต่ำ (ไม่สม่ำเสมอ)", "content_style": "Specialty coffee showcase · bean education · simple", "engagement_level": "low"},
        "delivery": {
            "primary_app": "LINE MAN",
            "apps": ["LINE MAN", "Wongnai Delivery"],
            "peak_hours": "08:00-16:00 (window แคบมาก)",
            "active_promos": ["ค่าส่งเริ่ม 0฿ ในพื้นที่บริการ"],
            "notes": "LINE MAN verified via Wongnai · ปิด 16:00 ทุกวัน · ไม่พบ GrabFood/ShopeeFood"
        }
    },
    {
        "id": "competitor-panacomehome",
        "category": "competitor",
        "title": "ป่านาคำหอม (Pa Na Come Home)",
        "summary": "Forest sanctuary 43 ไร่กลางเมืองสกลนคร · คาเฟ่เปิดเฉพาะเสาร์-อาทิตย์ 10:00-16:00 · กาแฟ Thai beans 20-40฿ (ราคาต่ำสุดในกลุ่ม) · ที่พัก 7 ห้อง 1,800-3,500฿/คืน · ไม่มี delivery เลย",
        "updated": "23 May 2026",
        "source_url": "https://panacomehome.com",
        "thumbnail_url": "",
        "tags": ["eco", "forest", "retreat", "organic", "ที่พัก", "slow-life", "สกลนคร"],
        "relevance": "high",
        "detail": "ป่านาคำหอม (Pa Na Come Home) — Forest sanctuary กลางเมืองสกลนคร\n\nเปิดกิจการ: 2013 · เจ้าของ: รัฐิกร ทองศิริ (นักอนุรักษ์ป่า/ผู้ประกอบการ)\n\nพื้นที่ 43 ไร่:\n• ป่าดิบแล้ง 20 ไร่ (walking trail ไม่แตะต้อง)\n• นาข้าวอินทรีย์ + สวนผลไม้ + บ่อน้ำ\n• บ้านพัก 7 ห้อง (Phon Samed 1-6 + Phon Makok 7)\n• Phon Samoa Cafe (เสาร์-อาทิตย์ 10:00-16:00)\n• Phon Khoi Activity Hall (Workshop/Event)\n\nBrand concept: 'Space of Allowing' — ชะลอจังหวะชีวิต สูดอากาศดี ท่ามวิวร่มรื่น\nPhilosophy: Eco conservation + slow living + ธรรมชาติกลางเมือง\n\nCafe Menu (Phon Samoa):\n• กาแฟ Thai beans 20-40฿ — ราคาต่ำสุดในกลุ่มทั้งหมด\n• ช็อกโกแลตไทย award-winning Thai origin\n• Matcha latte (non-dairy)\n• Latte + lemongrass mocktail (seasonal organic)\n• โซดาโฮมเมดจากพืชที่ปลูกเอง\n• อาหาร: ข้าวอินทรีย์ + ผักสวนสด\n• ไม่ใช้นมข้นหวาน ไม่ใช้สารปรุงแต่ง ความหวานจากน้ำตาลมะพร้าว\n• Keto-friendly · Vegan-friendly\n\nActivity Space (Phon Khoi): Day-use 8,000฿ / Overnight 12,000฿\nEvent: Workshop mindfulness, sustainability, film screening, ประชุม\n\nUnique experiences:\n• หิ่งห้อยในคืนฟ้าใส = ไม่มีร้านอื่นในสกลนครมี\n• สุนัขขาวฟู = mascot ธรรมชาติ\n• ข้าวอินทรีย์จากนาตัวเอง = farm-to-table จริง\n\nSocial: Facebook panacomehome (active) + UGC TikTok #ป่านาคำหอม 'คาเฟ่ลับสกลนคร นึกว่าอยู่บนภูพาน'\nDelivery: ไม่มีเลย — ธุรกิจหลักคือที่พัก ไม่ใช่คาเฟ่",
        "pricing": {
            "espresso": {"price": "", "note": ""},
            "americano": {"price": "", "note": ""},
            "latte": {"price": "", "note": ""},
            "cappuccino": {"price": "", "note": ""},
            "cold_brew": {"price": "", "note": ""},
            "frappe": {"price": "", "note": ""},
            "matcha": {"price": "ไม่ทราบ", "note": "non-dairy"},
            "signature_drink": {"price": "ไม่ทราบ", "note": "lemongrass mocktail"},
            "food": {"price": "ไม่ทราบ", "note": "ข้าวอินทรีย์ + ผักสวนสด"},
            "other": [
                {"name": "กาแฟ Thai beans", "price": "20-40฿"},
                {"name": "ช็อกโกแลตไทย award-winning", "price": "ไม่ทราบ"},
                {"name": "โซดาโฮมเมด", "price": "ไม่ทราบ"},
                {"name": "ที่พัก Phon Samed (38 ตร.ม.)", "price": "1,800-3,500฿/คืน"},
                {"name": "ที่พัก Phon Makok (28 ตร.ม.)", "price": "1,800-2,500฿/คืน"},
                {"name": "Phon Khoi Day-use", "price": "8,000฿"},
                {"name": "Phon Khoi Overnight", "price": "12,000฿"}
            ]
        },
        "strengths": [
            "ป่า 43 ไร่กลางเมือง = absolute uniqueness ในสกลนคร",
            "กาแฟ 20-40฿ = ราคาต่ำสุดในกลุ่มทั้งหมด",
            "Farm-to-table จริง (ข้าวอินทรีย์ + ผักสวน + น้ำตาลมะพร้าว)",
            "หิ่งห้อย + ดาว = ประสบการณ์ที่จำไม่ลืม",
            "Activity space Phon Khoi = B2B revenue stream",
            "เว็บไซต์ panacomehome.com ที่ดีมาก",
            "UGC organic แรง TikTok 'คาเฟ่ลับ นึกว่าอยู่บนภูพาน'"
        ],
        "promotions": [],
        "weaknesses": [
            "เปิดเฉพาะเสาร์-อาทิตย์ = ตลาด จ-ศ ว่างสนิท",
            "ไม่มี delivery เลย",
            "ไม่มี Wongnai listing = ไม่ปรากฏใน food discovery apps",
            "ไม่มี official Instagram/TikTok = UGC-dependent ทั้งหมด",
            "Target audience แคบ (eco-traveler/wellness) ไม่ใช่ daily coffee crowd"
        ],
        "location": "240/7 ชุมชนหนองแดง ซอยท่านขุน 1 ถ.รัฐบำรุง ต.ธาตุเชิงชุม เมืองสกลนคร",
        "hours": "คาเฟ่: เสาร์-อาทิตย์ 10:00-16:00 เท่านั้น · ที่พัก: ทุกวัน (จองล่วงหน้า 1 วัน)",
        "social_trend": {
            "primary_platform": "Facebook",
            "posting_frequency": "ไม่สม่ำเสมอ",
            "content_style": "Eco/nature documentary · forest preservation · slow life aesthetic",
            "engagement_level": "medium (UGC organic สูง บน TikTok/Lemon8)"
        },
        "delivery": {
            "primary_app": "ไม่มี",
            "apps": [],
            "peak_hours": "ไม่มี",
            "active_promos": [],
            "notes": "ไม่อยู่บน delivery apps เลย — คาเฟ่เปิดเฉพาะเสาร์-อาทิตย์ ธุรกิจหลักคือที่พักไม่ใช่คาเฟ่ ไม่พบ Wongnai/LINE MAN/GrabFood"
        }
    },
    {
        "id": "competitor-mokafox",
        "category": "competitor",
        "title": "MOKA FOX",
        "summary": "Homey wooden garden cafe · Wongnai 4.6/5 อันดับ #19/481 ในจังหวัด (ยังคงอันดับแม้คู่แข่งเพิ่ม 38 ร้าน) · จ-ศ 09:00-16:00 เสาร์-อาทิตย์ 09:00-17:00 · LINE MAN ✅ · Instagram @mokafox18 ✅ (พบใหม่) · TikTok UGC active มิ.ย. 2026",
        "updated": "9 Jun 2026",
        "source_url": "https://www.wongnai.com/restaurants/1053109Bs-moka-fox",
        "thumbnail_url": "",
        "tags": ["homey", "family-friendly", "garden", "wooden", "delivery", "Wongnai", "สกลนคร"],
        "relevance": "high",
        "detail": "MOKA FOX — Homey wooden garden cafe กลางเมืองสกลนคร\n\nที่ตั้ง: 691 ถ.รัฐบำรุง ธาตุนาเวง เมืองสกลนคร (ตรงข้ามร้านเหล้าเล็ก ก่อนถึงปั๊ม PTT แสงโฮม)\nRanking: #19 จาก 481 ร้านกาแฟ/ชา ในจังหวัดสกลนคร (Wongnai) — ยังคงอันดับเดิมแม้คู่แข่งเพิ่ม 38 ร้าน!\nFacebook: 3,762 likes · 3,922 visits\n\nConcept: Scandinavian + Thai homey aesthetic — บ้านไม้ 2 ชั้น + เฉลียง + สนามหญ้า\n\nZones:\n• ห้องปรับอากาศ (AC zone)\n• Semi-outdoor เฉลียง/ระเบียง\n• สนามหญ้า camping chairs\n• มุมถ่ายรูปหลายมุม\n• สนามเด็กเล่น\n\nAmenities: Wi-Fi, Parking, Pet-friendly, Credit card, LINE MAN Delivery ✅\nFamily-friendly สมบูรณ์ที่สุดในกลุ่ม = สนามเด็กเล่น + หลายโซน + pet-friendly\n\nMenu highlights:\n• Americano 85฿ / Latte 90฿ / Cappuccino 90฿ / Espresso 80฿\n• Iced Mocha 100฿ (เมนูแนะนำ)\n• Matcha Latte ice 150฿ / Hot Matcha 130฿\n• Signature Wake Up (กาแฟดำ + น้ำผลไม้ + syrup) 150฿\n• Hot Chocolate 90฿ / Milk drinks 70-95฿\n• Bakery & เค้ก\n\nSocial (updated 9 Jun 2026):\n• Facebook: 3,762 likes · 3,922 visits (ไม่เปลี่ยน)\n• **Instagram: @mokafox18 ✅ (พบใหม่! — previously missed, now confirmed)**\n• TikTok: UGC active (พบคลิปใหม่ มิ.ย. 2026 @nonnaina: 'คาเฟ่สกลนครบรรยากาศดี')\n• Lemon8/Trip.com: UGC organic active\n• Possible renovation: Instagram reel โดย @millimade.designstudio เรื่อง 'Moka fox cafe counter' — อาจมีการปรับปรุงร้าน\nDelivery: LINE MAN via Wongnai · จ-ศ 09:00-15:30 / เสาร์-อาทิตย์ 09:00-16:30",
        "pricing": {
            "espresso": {"price": "80฿", "note": "hot"},
            "americano": {"price": "85฿", "note": "hot/ice"},
            "latte": {"price": "90฿", "note": "hot/ice"},
            "cappuccino": {"price": "90฿", "note": "hot"},
            "cold_brew": {"price": "", "note": ""},
            "frappe": {"price": "", "note": ""},
            "matcha": {"price": "130-150฿", "note": "Hot Matcha 130฿ / Matcha Latte ice 150฿"},
            "signature_drink": {"price": "150฿", "note": "Wake Up — กาแฟดำ + น้ำผลไม้ + syrup"},
            "food": {"price": "ไม่ทราบ", "note": "Bakery & เค้ก"},
            "other": [
                {"name": "Iced Mocha", "price": "100฿"},
                {"name": "Hot Chocolate", "price": "90฿"},
                {"name": "Milk drinks", "price": "70-95฿"},
                {"name": "Pure Matcha", "price": "120฿"}
            ]
        },
        "strengths": [
            "Wongnai 4.6/5 — Ranked #19/481 ในจังหวัด = Top 4% แม้คู่แข่งเพิ่ม 38 ร้าน = โดดเด่นมาก",
            "Family-friendly สมบูรณ์ที่สุดในกลุ่ม (สนามเด็กเล่น, pet-friendly, หลายโซน)",
            "Delivery LINE MAN ✅ ทุกวัน — delivery hours กว้าง",
            "เปิดทุกวัน (เสาร์-อาทิตย์ ถึง 17:00) = เวลาบริการครอบคลุม",
            "หลายโซน (AC + semi-outdoor + สนามหญ้า) = รองรับลูกค้าหลากกลุ่ม",
            "Instagram @mokafox18 official (พบใหม่) — multi-platform ครบกว่าที่คิด"
        ],
        "promotions": [],
        "weaknesses": [
            "ราคา 85-150฿ สูงกว่า จุมพฏ/A Cup of Joy — ไม่ใช่ daily coffee",
            "Wongnai เพียง 2 reviews = social proof ยังน้อยเทียบกับ ranking สูง",
            "ปิด 16:00 (จ-ศ) = ไม่มี after-work market วันธรรมดา",
            "ไม่มี official TikTok account (มีแต่ UGC)"
        ],
        "location": "691 ถ.รัฐบำรุง ธาตุนาเวง เมืองสกลนคร สกลนคร (ตรงข้ามร้านเหล้าเล็ก ก่อนปั๊ม PTT แสงโฮม)",
        "hours": "จ.–ศ. 09:00–16:00 · เสาร์–อาทิตย์ 09:00–17:00",
        "social_trend": {
            "primary_platform": "Facebook",
            "posting_frequency": "ไม่สม่ำเสมอ (FB + IG อาจ active กว่าที่คิด)",
            "content_style": "Homey/garden aesthetic · family moments · seasonal themes (Christmas) · Instagram @mokafox18 official",
            "engagement_level": "medium-high (Facebook 3,762 likes · Instagram @mokafox18 official · TikTok UGC active Jun 2026)"
        },
        "delivery": {
            "primary_app": "LINE MAN",
            "apps": ["LINE MAN", "Wongnai Delivery"],
            "peak_hours": "09:00-15:30 (จ-ศ) / 09:00-16:30 (เสาร์-อาทิตย์)",
            "active_promos": [],
            "notes": "LINE MAN verified via Wongnai · Delivery ทุกวัน · GrabFood/ShopeeFood ไม่พบ · LINE Pay รับ"
        }
    },
    {
        "id": "competitor-cantocafe",
        "category": "competitor",
        "title": "CANTO CAFE สกลนคร",
        "summary": "ยังไม่มีข้อมูลออนไลน์ — ไม่พบบน Google, Facebook, TikTok, Wongnai, Lemon8 (ค้นหา 24 พ.ค. 2026) · คู่แข่งใหม่ที่ต้องติดตาม",
        "updated": "24 May 2026",
        "source_url": "",
        "thumbnail_url": "",
        "tags": ["สกลนคร", "ใหม่", "ติดตาม", "ไม่มีข้อมูลออนไลน์"],
        "relevance": "medium",
        "detail": "CANTO CAFE สกลนคร — คู่แข่งใหม่ที่เพิ่มเข้าระบบ 24 พ.ค. 2026\n\n⚠️ ข้อมูลจำกัด: ค้นหาออนไลน์แล้วไม่พบ (Google/Facebook/TikTok/Wongnai/Lemon8) อาจเป็นร้านใหม่มากที่ยังไม่มี digital footprint หรือชื่อออนไลน์อาจต่างจากชื่อที่รู้จักในท้องถิ่น\n\nสถานะ: ต้องการการยืนยันข้อมูลเพิ่มเติม (Facebook page URL, ที่ตั้ง, เมนู, เวลาเปิด)",
        "pricing": {
            "espresso": {"price": "ไม่ทราบ", "note": ""},
            "americano": {"price": "ไม่ทราบ", "note": ""},
            "latte": {"price": "ไม่ทราบ", "note": ""},
            "cappuccino": {"price": "ไม่ทราบ", "note": ""},
            "cold_brew": {"price": "ไม่ทราบ", "note": ""},
            "frappe": {"price": "ไม่ทราบ", "note": ""},
            "matcha": {"price": "ไม่ทราบ", "note": ""},
            "signature_drink": {"price": "ไม่ทราบ", "note": ""},
            "food": {"price": "ไม่ทราบ", "note": ""},
            "other": []
        },
        "strengths": ["ยังไม่ทราบ — ต้องการข้อมูลเพิ่มเติม"],
        "promotions": [],
        "weaknesses": ["ไม่มี online presence ที่พบได้ = ยากต่อการติดตาม"],
        "location": "ยังไม่ทราบ",
        "hours": "ยังไม่ทราบ",
        "social_trend": {
            "primary_platform": "ไม่ทราบ",
            "posting_frequency": "ไม่ทราบ",
            "content_style": "ไม่ทราบ",
            "engagement_level": "ไม่ทราบ"
        },
        "delivery": {
            "primary_app": "LINE MAN",
            "apps": ["LINE MAN"],
            "peak_hours": "ยังไม่มีข้อมูล",
            "active_promos": [],
            "notes": "ยังไม่มีข้อมูลเพียงพอ — ไม่พบบน Wongnai/LINE MAN/GrabFood/ShopeeFood"
        }
    },
    {
        "id": "competitor-wehugcafe",
        "category": "competitor",
        "title": "WE HUG CAFE (Wehug cafe) สกลนคร",
        "summary": "Minimalist cafe ถนนเส้น บขส.ใหม่ · Facebook 1,888 likes · Instagram @wehugcafe_sakon 95 followers · เปิด 08:00-19:00 ทุกวัน · LINE MAN + FoodPanda ✅ · ราคา <100฿ · Loyalty stamp 10 แก้ว = 1 ฟรี · TikTok UGC active Jun 2026",
        "updated": "9 Jun 2026",
        "source_url": "https://www.wongnai.com/restaurants/1298418Tu-wehug-cafe",
        "thumbnail_url": "",
        "tags": ["minimalist", "สกลนคร", "delivery", "Wongnai", "loyalty", "brunch", "bakery"],
        "relevance": "high",
        "detail": "WE HUG CAFE (Wehug cafe) สกลนคร — Minimalist coffee comfort zone\n\nที่ตั้ง: 272/17-18 ถ.นิตโย ธาตุเชิงชุม เมืองสกลนคร (ถนนเส้น บขส.ใหม่)\nโทร: 061-517-9957\nเวลาเปิด: ทุกวัน 08:00–19:00\nWongnai: 5/5 (1 review) · Delivery ✅ ส่งฟรีระยะหนึ่ง\n\nConcept: \"The coffee comfort zone\" — minimalist white-black tone, multiple seating zones, หลายมุมถ่ายรูป\n\nHighlights:\n• โซฟาสีดำสลับเบจ · โต๊ะกลมสีดำ/ขาว · ตุ๊กตาหมีตัวใหญ่\n• หลายโซน (window zone, chill zone, work zone)\n• Pet-friendly, family-friendly\n• Credit card ✅ · Delivery ✅\n\nMenu highlights:\n• Americano — เมนูยอดนิยม (featured บน Facebook)\n• Wehug Special (signature drink)\n• Matcha, Tea, Cocoa, Smoothies, Fresh Soda\n• Hokkaido Milk Cake 85฿\n• Choux cream + Blueberry, Crepe cake, Bakery\n\nSocial:\n• Facebook: @wehugcafe (1,888 likes) — Active, โพสต์เมนูแนะนำ\n• Instagram: @wehugcafe_sakon (95 followers, 447 posts)\n• TikTok: UGC #wehugcafe · ไม่มี official account\n• Lemon8: UGC หลายบทความ\n• Trip.com: UGC reviews\n\nPromotion:\n• Loyalty stamp: ซื้อครบ 10 แก้ว = แก้วฟรี 1 ใบ\n• วันพุธ: ส่วนลด 10%\n• วันเสาร์: ส่วนลด 5%\n• เค้กลด 20%\n• ใช้แก้วส่วนตัว: ลด 5 บาท",
        "pricing": {
            "espresso": {"price": "ไม่ทราบ", "note": ""},
            "americano": {"price": "ต่ำกว่า 100฿", "note": "เมนูยอดนิยม"},
            "latte": {"price": "ต่ำกว่า 100฿", "note": "price range <100฿"},
            "cappuccino": {"price": "ต่ำกว่า 100฿", "note": ""},
            "cold_brew": {"price": "ไม่ทราบ", "note": ""},
            "frappe": {"price": "ไม่ทราบ", "note": ""},
            "matcha": {"price": "ต่ำกว่า 100฿", "note": ""},
            "signature_drink": {"price": "ต่ำกว่า 100฿", "note": "Wehug Special"},
            "food": {"price": "85-100฿", "note": "Hokkaido Milk Cake 85฿ · Bakery เริ่ม ~100฿"},
            "other": [
                {"name": "Hokkaido Milk Cake", "price": "85฿"},
                {"name": "Choux cream + Blueberry", "price": "ไม่ทราบ"},
                {"name": "Crepe cake", "price": "ไม่ทราบ"}
            ]
        },
        "strengths": [
            "เปิดถึง 19:00 ทุกวัน = After-work + evening market ครอบคลุมที่สุดในกลุ่ม",
            "Loyalty stamp 10 แก้วฟรี 1 = retention program ชัดเจน",
            "ราคาต่ำกว่า 100฿ = accessible daily coffee destination",
            "Delivery Wongnai ✅ ส่งฟรี = ช่องทาง order เพิ่มเติม",
            "Instagram 447 posts = content volume สูง visual assets เยอะ",
            "Promotions หลากหลาย (วันพุธ/วันเสาร์/แก้วตัวเอง/เค้ก)"
        ],
        "promotions": [
            "Loyalty stamp ครบ 10 แก้ว = ฟรี 1 แก้ว",
            "วันพุธ ลด 10%",
            "วันเสาร์ ลด 5%",
            "ใช้แก้วส่วนตัวลด 5 บาท",
            "เค้กลด 20%",
            "โปรวันแม่ (Mother's Day) ลด 15% — seasonal promo พิสูจน์ว่าทำ occasion-based promotion"
        ],
        "weaknesses": [
            "Instagram followers เพียง 95 คน แม้จะโพสต์ 447 ครั้ง = engagement/follower ratio ต่ำ",
            "ไม่มี official TikTok = ขาด reach กลุ่ม Gen Z (แม้มี UGC หลายคลิป)",
            "ข้อมูลราคาจำเพาะยังไม่ชัดเจน"
        ],
        "location": "272/17-18 ถ.นิตโย ธาตุเชิงชุม เมืองสกลนคร (ถนนเส้น บขส.ใหม่)",
        "hours": "ทุกวัน 08:00–19:00",
        "social_trend": {
            "primary_platform": "Facebook",
            "posting_frequency": "สม่ำเสมอ (Facebook + Instagram active)",
            "content_style": "Minimalist aesthetic · เมนูแนะนำ · บรรยากาศร้าน · สไตล์ขาว-ดำ-เบจ",
            "engagement_level": "medium (Facebook 1,888 likes · IG 447 posts/95 followers)"
        },
        "delivery": {
            "primary_app": "LINE MAN",
            "apps": ["LINE MAN", "Wongnai Delivery", "FoodPanda"],
            "peak_hours": "08:00-11:00 (เช้า) / 14:00-17:00 (บ่าย)",
            "active_promos": [],
            "notes": "LINE MAN ✅ + FoodPanda ✅ ยืนยัน (9 Jun 2026) · Wongnai delivery ✅ ส่งฟรีระยะใกล้ · เปิด 08:00-19:00 ทุกวัน = delivery hours กว้างสุดในกลุ่ม · TikTok UGC ยังมีคลิปใหม่ มิ.ย. 2026 (@arissp_7)"
        }
    },
    {
        "id": "competitor-yepcafe",
        "category": "competitor",
        "title": "YEP Cafe & Bar สกลนคร (เย๊ปที่แปลว่าใช่)",
        "summary": "Day cafe + Night bar dual concept · ถ.คูเมือง กลางเมืองสกลนคร · เปิดทุกวัน 08:30-00:00 · Facebook 2,818 likes · TikTok @yep.cafeandbar 1,751 followers · LINE MAN ✅ · Signature: Tiramisu + ครัวซองต์กรอบ · DJ มุมถ่ายรูปเยอะ ดึง Gen Z",
        "updated": "28 May 2026",
        "source_url": "https://www.facebook.com/p/YEP-100095353186854/",
        "thumbnail_url": "",
        "tags": ["cafe-and-bar", "day-night", "Gen-Z", "TikTok", "DJ", "สกลนคร", "delivery"],
        "relevance": "high",
        "detail": "YEP Cafe & Bar สกลนคร — Dual concept Day Cafe + Night Bar\n\nที่ตั้ง: 287/3 ถ.คูเมือง ต.ธาตุเชิงชุม เมืองสกลนคร\nโทร: 082-295-6455\nเวลาเปิด: ทุกวัน\n• Cafe: 08:30-18:00 (เปิดเช้า เครื่องดื่ม/ขนม/อาหาร)\n• Bar: 18:00-00:00 (DJ + atmosphere + cocktail)\n• Alcohol service: 11:00-14:00 / 17:00-00:00 (ตามกฎหมาย)\n\nConcept: 'เย๊ปที่แปลว่าใช่' — Day cafe & Night bar กลางใจเมืองสกลนคร\nDifferentiator: 15.5 ชั่วโมง/วัน = longest operating window ในกลุ่มคู่แข่ง คาเฟ่กลางวัน + บาร์กลางคืน รวมในร้านเดียว\n\nZones:\n• ชั้น 1: indoor + outdoor seating\n• ชั้น 2: มุมถ่ายรูปสีสันสดใส (Gen Z friendly)\n• Decoration เปลี่ยนตามฤดู/trend\n• แมว mascot\n\nMenu highlights:\n• Tiramisu (signature ขายเร็วหมด)\n• ครัวซองต์กรอบ (signature)\n• กาแฟ + เครื่องดื่ม\n• ขนมและอาหารถึงเที่ยงคืน (ยกเว้นเมนูกาแฟ)\n• Cocktail / Beer (ช่วงค่ำ)\n• รับจัดเบรค น้ำ ขนม อาหาร (B2B catering)\n\nSocial Presence:\n• Facebook: YEP สกลนคร — 2,818 likes · 2,008 visits (Active)\n• TikTok: @yep.cafeandbar — 1,751 followers (Active video content)\n• Instagram: presence via tagged location (UGC strong)\n• Lemon8: UGC reviews หลายบทความ (preawmini88, mbbu236, nxmmkhingg)\n• Trip.com: UGC reviews 3+ บทความ\n• ไม่มี official IG account ของร้าน\n\nReviews:\n• Wongnai: ยังไม่มีรีวิว/ดาว (listing exists แต่ 0 reviews)\n• UGC tone บวก: 'คาเฟ่ลับ สุดชิค', 'มุมถ่ายรูปเยอะ', 'น่ารัก สีสันสดใส'\n• กลุ่มเป้าหมาย: Gen Z / วัยรุ่นสกลนคร / นักท่องเที่ยว\n\nDelivery: LINE MAN ✅ (via Wongnai integration) · ไม่พบ GrabFood/ShopeeFood",
        "pricing": {
            "espresso": {"price": "ไม่ทราบ", "note": ""},
            "americano": {"price": "ไม่ทราบ", "note": ""},
            "latte": {"price": "ไม่ทราบ", "note": ""},
            "cappuccino": {"price": "ไม่ทราบ", "note": ""},
            "cold_brew": {"price": "ไม่ทราบ", "note": ""},
            "frappe": {"price": "ไม่ทราบ", "note": ""},
            "matcha": {"price": "ไม่ทราบ", "note": ""},
            "signature_drink": {"price": "ไม่ทราบ", "note": "Tiramisu · ครัวซองต์กรอบ"},
            "food": {"price": "ไม่ทราบ", "note": "ขนม+อาหารถึงเที่ยงคืน"},
            "other": [
                {"name": "Tiramisu (signature)", "price": "ไม่ทราบ"},
                {"name": "ครัวซองต์กรอบ (signature)", "price": "ไม่ทราบ"},
                {"name": "Cocktail/Beer (ช่วง bar)", "price": "ไม่ทราบ"}
            ]
        },
        "strengths": [
            "Dual concept Day Cafe + Night Bar = unique ในตลาดสกลนคร",
            "เปิด 08:30-00:00 = 15.5 ชม. ครอบคลุม day + evening + night market",
            "TikTok @yep.cafeandbar 1,751 followers = official account active (>50% คู่แข่งไม่มี)",
            "Facebook 2,818 likes = social proof ระดับสูงในกลุ่ม",
            "DJ + atmosphere = entertainment value ดึง Gen Z วัยรุ่น",
            "มุมถ่ายรูปเยอะ + decoration ตามฤดู = UGC engine (Lemon8/Trip.com UGC แรง)",
            "Signature Tiramisu + ครัวซองต์กรอบ = brand recall ชัด",
            "B2B catering (รับจัดเบรค น้ำ ขนม อาหาร) = revenue stream เพิ่ม",
            "LINE MAN delivery ✅",
            "มี alcohol license = cross-sell daytime customer ไป evening"
        ],
        "promotions": [],
        "weaknesses": [
            "Wongnai 0 reviews/ratings = social proof ใน food discovery apps แทบไม่มี",
            "ราคาเมนูไม่ประกาศสาธารณะ — ลูกค้าตัดสินใจสั่งล่วงหน้าได้ยาก",
            "ไม่มี GrabFood/ShopeeFood = พลาดกลุ่มลูกค้านอก LINE MAN",
            "ไม่มี official Instagram = visual platform หลักของ café niche ขาด",
            "เน้น Bar concept ตอนค่ำ — อาจไม่ตรงกับกลุ่ม specialty coffee enthusiast"
        ],
        "location": "287/3 ถ.คูเมือง ต.ธาตุเชิงชุม เมืองสกลนคร",
        "hours": "ทุกวัน · Cafe 08:30-18:00 · Bar 18:00-00:00 (Alcohol 11:00-14:00 / 17:00-00:00)",
        "social_trend": {
            "primary_platform": "Facebook",
            "posting_frequency": "สม่ำเสมอ (Facebook + TikTok active)",
            "content_style": "Cafe-by-day & bar-by-night · มุมถ่ายรูปสีสันสดใส · DJ night vibe · seasonal decor",
            "engagement_level": "medium-high (FB 2,818 likes · TikTok 1,751 followers · UGC แรง)"
        },
        "delivery": {
            "primary_app": "LINE MAN",
            "apps": ["LINE MAN"],
            "peak_hours": "10:00-12:00 (สาย) / 14:00-17:00 (บ่าย) — window กาแฟก่อน bar เปิด",
            "active_promos": [],
            "notes": "LINE MAN ผ่าน Wongnai integration · ไม่พบ GrabFood/ShopeeFood · หลัง 18:00 เน้น dine-in bar service ไม่ใช่ delivery · B2B catering รับจัดเบรคโทรสั่งตรง 082-295-6455"
        }
    },
    {
        "id": "competitor-cafejackies",
        "category": "competitor",
        "title": "Café Jackies สกลนคร",
        "summary": "คาเฟ่เปิดใหม่ปี 2025 · สี่แยกโฮมพลัส ทางไปราชภัฏ · จ-ศ 08:30-17:30 / เสาร์-อาทิตย์ 10:30-19:30 · Facebook @jackiescafe · TikTok+IG @cafejackies · ราคาต่ำกว่า 100฿ · Delivery via Wongnai (LINE MAN) · มุมถ่ายรูปเยอะ สไตล์ Scandi",
        "updated": "8 Jun 2026",
        "source_url": "https://www.facebook.com/jackiescafe/",
        "thumbnail_url": "",
        "tags": ["สกลนคร", "local", "new-opening", "aesthetic", "photo-spot", "Instagram", "TikTok", "delivery"],
        "relevance": "high",
        "detail": "Café Jackies สกลนคร — คาเฟ่เปิดใหม่ปี 2025 (เดิมเป็นร้านเน็ต)\n\nที่ตั้ง: 333/11 ธาตุนาเวง เมืองสกลนคร (สี่แยกโฮมพลัส ทางไปราชภัฏสกลนคร)\nโทร: 094-656-8787\nเวลาเปิด:\n• จ-ศ: 08:30-17:30\n• เสาร์-อาทิตย์: 10:30-19:30\nDelivery hours: 09:30-19:30 (vary by day)\n\nBranding / Positioning: มุมถ่ายรูปเยอะมาก · บรรยากาศ Scandi ไม้+กระจก · ฟีลร่มรื่น · โซนใน+โซน Open Air · ราคาเข้าถึงได้ (<100 บาท)\nกลุ่มเป้าหมาย: นักศึกษา ม.ราชภัฏสกลนคร, คนทำงาน, สายถ่ายรูป, ท่องเที่ยว\n\nสิ่งอำนวยความสะดวก: Wi-Fi ✅ · ที่จอดรถ ✅ · Pet-friendly ✅ · บัตรเครดิต ✅ · 41-80 ที่นั่ง\n\nSocial Presence:\n• Facebook: @jackiescafe — active (UGC แรง, โพสต์รีวิวหลายบทความ)\n• TikTok: @cafejackies — active content (Reels บรรยากาศ + vibes)\n• Instagram: @cafejackies — active Reels\n• UGC review: TikTok หลายคลิป (supkadoukmoo, callmepxxch) · Facebook reviews/shares (43 reactions, 15 shares ต่อโพสต์)\n• Hashtags ที่พบ: #คาเฟ่สกลนคร #สกลนคร #ที่เที่ยวสกลนคร #เลาะไปโลดสกลนคร\n\nMenu highlights:\n• Matcha Latte (75฿) · Espresso Cold (70฿) · Americano Cold (65฿)\n• Café Latte (70฿) · Cappuccino Cold (70฿)\n• Orange Cake (เค้กส้ม — พบในรีวิว)\n• หมวด: กาแฟ, มัทฉะ, ชานมญี่ปุ่น, กาแฟดริป, โซดา, สมูทตี้, ของหวาน\n\nReviews:\n• Wongnai: ลงทะเบียนแล้ว แต่ 0 รีวิว (ใหม่)\n• Facebook UGC: 'mood ดีมาก กาแฟอร่อย บรรยากาศน่านั่งทำงาน'\n• TikTok UGC: 'Vibes ดีมากกกก แนะนำให้มา'\n\nDelivery: Wongnai ✅ delivery (ส่งฟรี 0฿ ในรัศมีใกล้) → LINE MAN likely · ไม่พบ GrabFood/ShopeeFood",
        "pricing": {
            "espresso": {"price": "70", "note": "cold"},
            "americano": {"price": "65", "note": "cold"},
            "latte": {"price": "70", "note": "hot/iced"},
            "cappuccino": {"price": "70", "note": "cold"},
            "cold_brew": {"price": "ไม่ทราบ", "note": ""},
            "frappe": {"price": "ไม่ทราบ", "note": ""},
            "matcha": {"price": "75", "note": "Matcha Latte"},
            "signature_drink": {"price": "ไม่ทราบ", "note": "ชานมญี่ปุ่น, สมูทตี้"},
            "food": {"price": "ไม่ทราบ", "note": "เค้กส้ม + ขนม"},
            "other": [
                {"name": "Orange Cake (เค้กส้ม)", "price": "ไม่ทราบ", "note": "พบในรีวิว"},
                {"name": "ชานมญี่ปุ่น", "price": "ไม่ทราบ", "note": ""},
                {"name": "โซดา / สมูทตี้", "price": "ไม่ทราบ", "note": ""}
            ]
        },
        "strengths": [
            "ทำเลดี — สี่แยกโฮมพลัส ทางไปราชภัฏ ใกล้กลุ่มนักศึกษา",
            "ราคาเข้าถึงได้สูงมาก (<100฿) เทียบกับคู่แข่ง",
            "Multi-platform social: Facebook + TikTok + Instagram ทำงานพร้อมกัน",
            "UGC แรง — visitors รีวิว/แชร์เอง ทั้ง TikTok และ Facebook",
            "มุมถ่ายรูปเยอะ = content engine ฟรีจากลูกค้า",
            "บรรยากาศ Scandi aesthetic น่านั่งทำงาน = dwell time สูง",
            "Delivery via Wongnai ✅ ส่งฟรีในรัศมีใกล้"
        ],
        "promotions": [],
        "weaknesses": [
            "เพิ่งเปิด ยังไม่มี reviews บน Wongnai (0 ดาว)",
            "ชั่วโมงเปิด weekday สั้น (08:30-17:30) พลาดลูกค้าตอนเย็น",
            "ราคาบางรายการยังไม่ชัดเจนในสาธารณะ",
            "ยังไม่มี GrabFood/ShopeeFood = พลาดกลุ่ม delivery นอก Wongnai",
            "ไม่มี loyalty program / บัตรสะสมแต้ม (ยังไม่พบ)"
        ],
        "location": "333/11 ธาตุนาเวง เมืองสกลนคร (สี่แยกโฮมพลัส ทางไปราชภัฏ)",
        "hours": "จ-ศ 08:30-17:30 · เสาร์-อาทิตย์ 10:30-19:30",
        "social_trend": {
            "primary_platform": "TikTok/Instagram",
            "posting_frequency": "active (UGC + official)",
            "content_style": "aesthetic vibes · photo spots · new cafe announcement · บรรยากาศ Scandi",
            "engagement_level": "medium (UGC แรง — visitors share เอง)"
        },
        "delivery": {
            "primary_app": "LINE MAN",
            "apps": ["LINE MAN"],
            "peak_hours": "ยังไม่มีข้อมูล",
            "active_promos": [],
            "notes": "Wongnai delivery ✅ ส่งฟรีในรัศมีใกล้ (0฿ starting fee) · delivery hours 09:30-19:30 · LINE MAN likely via Wongnai integration · ไม่พบ GrabFood/ShopeeFood"
        }
    },
    {
        "id": "competitor-hokkaido-craft",
        "category": "competitor",
        "title": "Hokkaido Craft Cafe' & Studio สาขา ปตท.มะขามป้อม สกลนคร",
        "summary": "Japanese ice cream & specialty beverages · สาขา ปตท.มะขามป้อม สกลนคร · ทุกวัน 10:00-19:30 · Facebook active · Instagram @hokkaido_craftcafe_studio · FoodPanda ✅ · Signature: TARA TORA + Hokkaido milk · Wongnai 3.8⭐ · ราคา 50-130฿",
        "updated": "8 Jun 2026",
        "source_url": "https://www.facebook.com/hokkaido.craftcafeandstudio.ptt.makhampom/",
        "thumbnail_url": "",
        "tags": ["สกลนคร", "Japanese", "ice-cream", "specialty-drinks", "FoodPanda", "delivery", "ปตท"],
        "relevance": "high",
        "detail": "Hokkaido Craft Cafe' & Studio สาขา ปตท.มะขามป้อม สกลนคร — Japanese ice cream & craft beverages\n\nที่ตั้ง: ปตท.มะขามป้อม เมืองสกลนคร (สาขาที่ตั้งในปั๊มน้ำมัน PTT)\nโทร: 064-882-7455 / 091-865-5044\nเวลาเปิด: ทุกวัน 10:00-19:30\n\nสาขาหลัก (ถ.สุโขทัย ตรงข้ามศาลากลาง) — มีรายงานว่า permanently closed (restaurantguru/Google)\nสาขา ปตท.มะขามป้อม — active, Facebook page ยังมีการอัพเดท\n\nBranding / Positioning: Japanese-style ice cream café · ไอศกรีมญี่ปุ่น low-fat homemade · craft beverages · Japanese wood décor บรรยากาศชิล\nกลุ่มเป้าหมาย: สายหวาน, สายญี่ปุ่น, ครอบครัว, นักท่องเที่ยว\n\nสิ่งอำนวยความสะดวก: Wi-Fi ✅ · ที่จอดรถ ✅ · รับบัตรเครดิต ✅ · Pet-friendly ✅ · Takeaway ✅\n\nSocial Presence:\n• Facebook: @hokkaido.craftcafeandstudio.ptt.makhampom (PTT branch) + main page (@hokkaido.craftcafeandstudio) — Main FB: 291 reviews, 3.4/5\n• Instagram: @hokkaido_craftcafe_studio — active\n• TikTok: UGC หลายคลิป (#hokkaido #คาเฟ่สกลนคร)\n• YouTube: Hokkaido Craft cafe & Studio channel\n\nMenu highlights:\n• TARA TORA (Taro Tora) 75฿ — signature drink, ดังมาก\n• Hokkaido milk hot 50฿\n• Black cocoa 80฿\n• Yogurt ice cream with cantaloupe jelly 130฿+\n• ไอศกรีมโยเกิร์ต (vanilla/yogurt) — low-fat homemade\n• Taiwan bubble tea\n• Cheese bread / Cheese chicken\n• ช็อคโกแลต 5 แบบ\n\nReviews:\n• Wongnai: 3.8/5 · 13 ratings · 10 reviews (สาขาใจกลางเมือง)\n• Google (main): 4.4/5 · 83 reviews\n• Facebook: 3.4/5 · 291 reviews\n• Notable: 'TARA TORA อร่อยสมค่ำล่ำลือ' · 'ตกแต่งสวยมาก' · 'กาแฟช็อคโก้เข้มข้นกลมกล่อม'\n• Warning: สาขาถ.สุโขทัยอาจปิดแล้ว — ยืนยันเฉพาะสาขา ปตท.มะขามป้อม\n\nDelivery: FoodPanda ✅ (foodpanda.co.th/restaurant/j5ic) · ไม่พบ LINE MAN/GrabFood โดยตรง",
        "pricing": {
            "espresso": {"price": "ไม่ทราบ", "note": ""},
            "americano": {"price": "ไม่ทราบ", "note": ""},
            "latte": {"price": "ไม่ทราบ", "note": ""},
            "cappuccino": {"price": "ไม่ทราบ", "note": ""},
            "cold_brew": {"price": "ไม่ทราบ", "note": ""},
            "frappe": {"price": "ไม่ทราบ", "note": ""},
            "matcha": {"price": "ไม่ทราบ", "note": "Matcha drinks available"},
            "signature_drink": {"price": "75", "note": "TARA TORA (Taro Tora) — signature ดัง"},
            "food": {"price": "ไม่ทราบ", "note": "Cheese bread, Cheese chicken"},
            "other": [
                {"name": "Hokkaido milk (hot)", "price": "50", "note": ""},
                {"name": "Black cocoa", "price": "80", "note": ""},
                {"name": "Yogurt ice cream + cantaloupe jelly", "price": "130", "note": "low-fat homemade"},
                {"name": "Taiwan bubble tea", "price": "ไม่ทราบ", "note": ""},
                {"name": "ช็อคโกแลต (5 varieties)", "price": "ไม่ทราบ", "note": "เข้มข้นกลมกล่อม"}
            ]
        },
        "strengths": [
            "Unique positioning — Japanese ice cream + craft beverages แตกต่างจาก local cafés ทั้งหมด",
            "Signature TARA TORA viral — 'อร่อยสมค่ำล่ำลือ' ลูกค้าแนะนำต่อ",
            "FoodPanda ✅ — delivery platform ที่คู่แข่ง local ส่วนใหญ่ไม่มี",
            "ที่ตั้งในปั๊มน้ำมัน PTT = traffic สูงจากนักเดินทาง",
            "Multi-platform social: Facebook + Instagram + TikTok UGC",
            "Franchise brand recognition ระดับประเทศ (มีสาขาหลายจังหวัด)",
            "Google 4.4/5 จาก 83 รีวิว = social proof แข็งแกร่ง"
        ],
        "promotions": [],
        "weaknesses": [
            "สาขาหลัก (ถ.สุโขทัย) อาจปิดถาวรแล้ว — brand awareness ในพื้นที่อาจลดลง",
            "ราคาสูงกว่าคู่แข่ง (101-250฿/คน) — ไม่ใช่ทางเลือกสำหรับประหยัด",
            "เน้น dessert/ice cream ไม่ใช่ specialty coffee — ฐานลูกค้าต่างกับ coffee enthusiasts",
            "เวลาเปิดสั้น (10:00-19:30) ไม่ capture morning coffee market",
            "ไม่พบ LINE MAN = พลาด majority ของ delivery traffic ในจังหวัด"
        ],
        "location": "ปตท.มะขามป้อม เมืองสกลนคร",
        "hours": "ทุกวัน 10:00-19:30",
        "social_trend": {
            "primary_platform": "Facebook",
            "posting_frequency": "moderate (Facebook + IG active)",
            "content_style": "Japanese ice cream aesthetic · craft beverages · dessert showcase · บรรยากาศญี่ปุ่น",
            "engagement_level": "medium (FB 291 reviews · Google 4.4/5 · TikTok UGC)"
        },
        "delivery": {
            "primary_app": "FoodPanda",
            "apps": ["FoodPanda"],
            "peak_hours": "ยังไม่มีข้อมูล",
            "active_promos": [],
            "notes": "FoodPanda ✅ ยืนยัน (foodpanda.co.th/restaurant/j5ic/hokkaido-craft-cafe-and-studio) · ไม่พบ LINE MAN/GrabFood · ในปั๊ม PTT ทำให้ FoodPanda เหมาะกว่า Wongnai/LINE MAN สำหรับ takeaway traffic"
        }
    },
    {
        "id": "competitor-ebuai",
        "category": "competitor",
        "title": "อีบ๊วย (E BUAI) สกลนคร",
        "summary": "Home café + Workshop · ซอยตลาดบ้านธาตุ หน้าวัดพระธาตุนารายณ์เจงเวง · ทุกวัน 10:00-18:00 · Facebook + TikTok @ebuai120 · ราคา <100฿ · Wongnai delivery (LINE MAN) · มีแมว · Workshop สอนทำขนม+กาแฟ · E'BUAI V.2 (ขายข้าว) แยกต่างหาก",
        "updated": "8 Jun 2026",
        "source_url": "https://www.facebook.com/p/E-BUAI-100083137039984/",
        "thumbnail_url": "",
        "tags": ["สกลนคร", "home-cafe", "vintage", "workshop", "cat-cafe", "delivery", "ราคาถูก"],
        "relevance": "high",
        "detail": "อีบ๊วย (E BUAI) สกลนคร — Home Café + Workshop\n\nที่ตั้ง: ซอยตลาดบ้านธาตุ ซ.หน้าวัดพระธาตุ ถ.นิตโย ธาตุนาเวง เมืองสกลนคร (หน้าวัดพระธาตุนารายณ์เจงเวง ใกล้ ม.ราชภัฏสกลนคร)\nโทร: 064-019-9210 / 098-983-9494\nLINE: yoki2626\nเวลาเปิด: ทุกวัน 10:00-18:00\nDelivery hours: 11:00-17:30\n\nBranding / Positioning: 'คาเฟ่ลับ แต่ไม่ลับ' · Home café vintage style · ผนังสีเขียว เพดานไม้ · Outdoor ร่มรื่นสงบ · มีแมวประจำร้าน · Workshop สอนทำขนมและกาแฟ\nกลุ่มเป้าหมาย: นักศึกษา ม.ราชภัฏ, สายคาเฟ่ลับ, นักท่องเที่ยวสายธาตุเจงเวง, workshop seekers\n\nสิ่งอำนวยความสะดวก: Wi-Fi ✅ · ที่จอดรถ ✅ · Pet-friendly ✅ · บัตรเครดิต ✅ · ที่นั่ง <10 ที่ (intimate)\n\nSocial Presence:\n• Facebook: @E-BUAI (facebook.com/p/E-BUAI-100083137039984) — active\n• TikTok: @ebuai120 (official) + UGC หลายคลิป (#อีบ๊วย #ebuai)\n• Lemon8: UGC reviews หลายบทความ (นน้ำแพง, เพียรณัฏฐิกา, คุณดามิน, แพรวว)\n• LINE: yoki2626\n• ไม่พบ Instagram official\n• Hashtags: #อีบ๊วย #ebuai #คาเฟ่สกลนคร #คาเฟ่บ้านธาตุ #สกลนคร #ร้านดีบอกต่อ #matcha #reviewsakonnakhon #ซอมเบิ่งหม่อง\n\nMenu highlights:\n• กาแฟ + matcha + เครื่องดื่มทั่วไป\n• เบเกอรี่ homemade\n• อาหาร homemade (มื้อหลักด้วย)\n• Workshop สอนทำขนมและกาแฟ (unique — revenue stream เพิ่ม)\n• ราคา <100฿ ทุกรายการ\n\nBranching:\n• E'BUAI (café หลัก) — เครื่องดื่ม+เบเกอรี่+อาหาร+workshop\n• E'BUAI V.2 (อีบ๊วยขายข้าว🍚) — Wongnai listing แยก เน้นข้าว/อาหาร\n\nReviews:\n• Wongnai: 0 รีวิว / 0 ดาว (ใหม่มาก — listing exists)\n• TikTok UGC: 'คาเฟ่ลับ แต่ไม่ลับ', 'เครื่องดื่มมี อาหารมี เวิร์คช็อปมี', 'บรรยากาศฮิลใจ', 'ระวังแมวสวบ'\n• Lemon8: 'บรรยากาศน่ารัก รสชาติเด็ด ราคาน่ารัก'\n\nDelivery: Wongnai delivery ✅ (0฿ starting fee) · delivery 11:00-17:30 · LINE MAN likely via Wongnai · ไม่พบ GrabFood/ShopeeFood/FoodPanda",
        "pricing": {
            "espresso": {"price": "ไม่ทราบ", "note": ""},
            "americano": {"price": "ไม่ทราบ", "note": ""},
            "latte": {"price": "ไม่ทราบ", "note": ""},
            "cappuccino": {"price": "ไม่ทราบ", "note": ""},
            "cold_brew": {"price": "ไม่ทราบ", "note": ""},
            "frappe": {"price": "ไม่ทราบ", "note": ""},
            "matcha": {"price": "ไม่ทราบ", "note": "matcha available"},
            "signature_drink": {"price": "ไม่ทราบ", "note": "ราคา <100฿ ทุกรายการ"},
            "food": {"price": "ไม่ทราบ", "note": "อาหาร homemade + เบเกอรี่"},
            "other": [
                {"name": "Workshop สอนทำขนม", "price": "ไม่ทราบ", "note": "unique service"},
                {"name": "Workshop สอนทำกาแฟ", "price": "ไม่ทราบ", "note": "unique service"},
                {"name": "อาหาร homemade (E'BUAI V.2)", "price": "ไม่ทราบ", "note": "spin-off ขายข้าว"}
            ]
        },
        "strengths": [
            "ราคาต่ำมาก (<100฿) เทียบเท่า Café Jackies = budget-friendly สุดในตลาด",
            "Workshop สอนทำขนม+กาแฟ = unique revenue stream และ viral content ที่คู่แข่งไม่มี",
            "บรรยากาศ 'คาเฟ่ลับ' + มีแมว = strong photo content engine ดึง UGC",
            "Multi-platform UGC: TikTok + Lemon8 + Facebook review organic",
            "Wongnai delivery ✅ 0฿ starting fee · ส่งได้ช่วงกลางวัน 11:00-17:30",
            "ทำเลดี — ใกล้วัดพระธาตุนารายณ์เจงเวง = tourist traffic",
            "E'BUAI V.2 spin-off = expand revenue โดยไม่ต้องเพิ่ม seat",
            "Lemon8 presence แรง = กลุ่ม lifestyle content ที่ TikTok+FB ยังครอบไม่ถึง"
        ],
        "promotions": [],
        "weaknesses": [
            "ที่นั่งน้อยมาก (<10 ที่) — scaling จำกัดมาก",
            "Wongnai 0 รีวิว = ลูกค้าใหม่ตัดสินใจยาก",
            "ไม่มี Instagram official = เสีย visual platform หลักของ cafe niche",
            "ราคาต่ำมากอาจจำกัด margin",
            "เวลาเปิดสั้น (10:00-18:00) พลาด morning + evening market",
            "ไม่พบ GrabFood/ShopeeFood = พลาดกลุ่ม delivery นอก Wongnai"
        ],
        "location": "ซอยตลาดบ้านธาตุ หน้าวัดพระธาตุนารายณ์เจงเวง เมืองสกลนคร",
        "hours": "ทุกวัน 10:00-18:00 · Delivery 11:00-17:30",
        "social_trend": {
            "primary_platform": "TikTok",
            "posting_frequency": "active (TikTok @ebuai120 + Lemon8 UGC แรง)",
            "content_style": "vintage home café · คาเฟ่ลับ · มีแมว · workshop · outdoor ร่มรื่น · ราคาน่ารัก",
            "engagement_level": "medium (TikTok UGC หลายคลิป · Lemon8 หลายบทความ · FB active)"
        },
        "delivery": {
            "primary_app": "LINE MAN",
            "apps": ["LINE MAN"],
            "peak_hours": "11:00-17:30 (ตาม delivery window ของ Wongnai)",
            "active_promos": [],
            "notes": "Wongnai delivery ✅ 0฿ starting fee · delivery hours 11:00-17:30 · LINE MAN likely via Wongnai integration · ไม่พบ GrabFood/ShopeeFood/FoodPanda · window delivery แคบ (ไม่รวมเช้า)"
        }
    },
    {
        "id": "competitor-homeup",
        "category": "competitor",
        "title": "HOME UP Cafe สกลนคร",
        "summary": "Nature café + Activity · ถ.ชลประทาน ใกล้ มรภ.สกลนคร · ทุกวัน 10:00-19:00 · Facebook @homeupcafe active (294 shares/โพสต์) · ราคา <100฿ · Wongnai delivery ✅ · เรือพายฟรี + เรือก๋วยเตี๋ยว + ขายต้นไม้ = unique 3-in-1",
        "updated": "9 Jun 2026",
        "source_url": "https://www.facebook.com/homeupcafe/",
        "thumbnail_url": "",
        "tags": ["สกลนคร", "nature-cafe", "activity", "boat", "plants", "university", "delivery", "ราคาถูก"],
        "relevance": "high",
        "detail": "HOME UP Cafe สกลนคร — Nature Café + Paddleboat + Plant Shop\n\nที่ตั้ง: ซอยตรงข้ามโรงเรียนธาตุนารายณ์วิทยา ถ.ชลประทาน (Chaloem Phrakiat Canal Road) / ถ.นิตโย ตำบลพังขว้าง เมืองสกลนคร (ใกล้ มรภ.สกลนคร)\nโทร: 062-893-5288\nเวลาเปิด: ทุกวัน 10:00-19:00\n\nBranding / Positioning: Nature café ติดคลอง/บึง · บรรยากาศร่มรื่น ธรรมชาติ · แอร์เย็น หลายมุมถ่ายรูป\nกลุ่มเป้าหมาย: นักศึกษา มรภ.สกลนคร, ครอบครัว, นักท่องเที่ยวสายธรรมชาติ, สายถ่ายรูป, สายต้นไม้\n\n**Unique Differentiators (ไม่มีร้านไหนในสกลนครทำ):**\n• เรือพาย (Paddleboat) ฟรีสำหรับลูกค้า!\n• เรือก๋วยเตี๋ยว (Boat Noodles) — เมนูอาหาร authentic\n• ขายต้นไม้ประดับ — additional revenue stream\n\nสิ่งอำนวยความสะดวก: Wi-Fi ✅ · ที่จอดรถ ✅ · Pet-friendly ✅ · บัตรเครดิต ✅ · 11-40 ที่นั่ง · Bar counter + ที่ชาร์จโทรศัพท์\n\nSocial Presence:\n• Facebook: @homeupcafe — active · โพสต์ Dec 2021: 162 reactions, 61 comments, **294 shares** (viral สำหรับ local café)\n• Instagram: location page exists (ไม่ทราบ official account)\n• Wongnai: 0 รีวิว (ลงทะเบียนแล้ว)\n• ไม่พบ TikTok official\n• Hashtags: #สกลนคร #คาเฟ่สกลนคร #มุมถ่ายรูป #HOME_UP_Cafe\n\nMenu highlights:\n• กาแฟ, ชา, เครื่องดื่ม\n• ของหวาน/เบเกอรี่\n• **เรือก๋วยเตี๋ยว** (unique!)\n• ต้นไม้ประดับ (ขาย)\n• ราคา <100฿ ทุกรายการ\n\nDelivery: Wongnai delivery ✅ (ระบุใน Wongnai listing) → LINE MAN likely · ไม่พบ GrabFood/ShopeeFood",
        "pricing": {
            "espresso": {"price": "ไม่ทราบ", "note": ""},
            "americano": {"price": "ไม่ทราบ", "note": ""},
            "latte": {"price": "ไม่ทราบ", "note": "<100฿"},
            "cappuccino": {"price": "ไม่ทราบ", "note": ""},
            "cold_brew": {"price": "ไม่ทราบ", "note": ""},
            "frappe": {"price": "ไม่ทราบ", "note": ""},
            "matcha": {"price": "ไม่ทราบ", "note": ""},
            "signature_drink": {"price": "ไม่ทราบ", "note": "กาแฟ/ชา <100฿"},
            "food": {"price": "ไม่ทราบ", "note": "เรือก๋วยเตี๋ยว + ของหวาน"},
            "other": [
                {"name": "เรือก๋วยเตี๋ยว (Boat Noodles)", "price": "ไม่ทราบ", "note": "unique signature food"},
                {"name": "เรือพาย (Paddleboat)", "price": "ฟรี (สำหรับลูกค้า)", "note": "unique activity"},
                {"name": "ต้นไม้ประดับ", "price": "ไม่ทราบ", "note": "ขาย retail"}
            ]
        },
        "strengths": [
            "**เรือพายฟรี** — activity ที่ไม่มีคาเฟ่ไหนในสกลนครทำ = strong UGC trigger",
            "**เรือก๋วยเตี๋ยว** — differentiator ทั้งเมนูอาหาร unique",
            "**ขายต้นไม้** — revenue stream เพิ่ม + ดึงกลุ่ม plant lovers",
            "บรรยากาศธรรมชาติ ติดคลอง = Instagram-worthy สูง",
            "Facebook viral สูง (294 shares/โพสต์) = organic reach ดีมาก",
            "ทำเลใกล้ มรภ.สกลนคร = student customer base",
            "ราคา <100฿ = accessible ทุกกลุ่ม",
            "Wongnai delivery ✅ + แอร์เย็น ที่ชาร์จ = work-friendly"
        ],
        "promotions": [],
        "weaknesses": [
            "Wongnai 0 รีวิว = credibility ต่ำสุดกลุ่ม",
            "ไม่พบ TikTok official = ขาด Gen Z reach",
            "ข้อมูลราคาไม่เปิดเผยสาธารณะ",
            "ไม่พบ GrabFood/ShopeeFood"
        ],
        "location": "ซอยตรงข้ามโรงเรียนธาตุนารายณ์วิทยา ถ.ชลประทาน / ถ.นิตโย พังขว้าง เมืองสกลนคร",
        "hours": "ทุกวัน 10:00-19:00",
        "social_trend": {
            "primary_platform": "Facebook",
            "posting_frequency": "moderate (Facebook active)",
            "content_style": "Nature café · บรรยากาศริมคลอง · เรือพาย · มุมถ่ายรูป · ต้นไม้",
            "engagement_level": "medium-high (Facebook viral shares สูง 294/โพสต์)"
        },
        "delivery": {
            "primary_app": "LINE MAN",
            "apps": ["LINE MAN"],
            "peak_hours": "ยังไม่มีข้อมูล",
            "active_promos": [],
            "notes": "Wongnai delivery ✅ (ระบุใน listing) → LINE MAN likely via Wongnai integration · ไม่พบ GrabFood/ShopeeFood/FoodPanda · ต้องยืนยันด้วยการเปิดแอปในพื้นที่"
        }
    },
    {
        "id": "competitor-hookcafe",
        "category": "competitor",
        "title": "ฮูกคาเฟ่ (Hook cafe') สกลนคร",
        "summary": "Coffee & Cactus Garden · ถ.สกลนคร-นครพนม ห้วยฮ้อ · จ-ส 7:30-18:00 / อาทิตย์ 9:00-18:00 · Facebook active · ราคา <100฿ · Wongnai delivery ✅ · น้ำหมากเม่าไนโตร + สวนแคสตัส + ขายต้นไม้ + กิจกรรมเด็ก",
        "updated": "9 Jun 2026",
        "source_url": "https://th-th.facebook.com/pages/category/Product-Service/%E0%B8%AE%E0%B8%B9%E0%B8%81%E0%B8%84%E0%B8%B2%E0%B9%80%E0%B8%9F%E0%B9%88-2159563274319141/",
        "thumbnail_url": "",
        "tags": ["สกลนคร", "nature-cafe", "cactus", "plant-nursery", "activity", "family", "หมากเม่า", "delivery"],
        "relevance": "medium",
        "detail": "ฮูกคาเฟ่ (Hook cafe') สกลนคร — Coffee & Cactus Garden\n\nที่ตั้ง: 172 ถ.สกลนคร-นครพนม (ทางหลวง 22) บ้านฮางโฮง ต.ฮางโฮง อ.เมืองสกลนคร (นอกเมือง ใกล้ มก.ฉกส. - ม.เกษตรศาสตร์วิทยาเขตสกลนคร)\nโทร: 098-569-6346\nเวลาเปิด:\n• จ-ส: 7:30-18:00 (เปิดเช้าที่สุดในกลุ่ม = 7:30!)\n• อาทิตย์: 9:00-18:00\nDelivery hours: 10:00-17:00\n\nConcept: Coffee & Cactus — ร้านกาแฟ + สวนแคสตัส + ขายต้นไม้ประดับ + กิจกรรมเด็ก\nUSP: 'ฮูก' (Hug/นกฮูก) branding · ริมทางหลวง 22 จับ traffic นักเดินทาง + นักศึกษา มก.\n\nสิ่งอำนวยความสะดวก: ที่จอดรถ ✅ · เด็กเล่นได้ ✅ · กลุ่ม ✅ · บัตรเครดิต ✅ · ที่นั่ง <10\n\nSocial Presence:\n• Facebook: ฮูกคาเฟ่ (Page ID 2159563274319141) — active\n• TikTok: #ฮูกคาเฟ่ (UGC hashtag มี)\n• Instagram: ไม่พบ official account\n• Facebook UGC (ปลาหลดใหนดี, Nov 2021): 121 reactions, 17 shares\n• Wongnai: 1 รีวิว / 5 ดาว (Dec 2019)\n\nMenu highlights:\n• กาแฟอังขาง (Angkhang coffee) — signature\n• **น้ำหมากเม่าไนโตร** — local fruit Nitro drink ที่ unique มาก\n• เค้กทุเรียน (ต้องจองล่วงหน้า 1-2 วัน)\n• เค้กผลไม้ตามฤดูกาล\n• Pink milk, Honey lemon mocktail\n• ราคา <100฿\n\nPlant nursery:\n• แคสตัสและไม้อวบน้ำหลายชนิด ราคาถูก\n• ดินปลูก + อุปกรณ์\n• กระถางน่ารัก\n\nกิจกรรม: สำหรับเด็ก · มุมถ่ายรูปในสวนแคสตัส\n\nReviews:\n• Wongnai 5/5 (1 รีวิว): 'ร้านกาแฟน่ารัก ในสวนเกษตร มีร้านอาหารภายในสวย จอดรถสะดวก มีน้ำหมากเม่าไนโตรและกิจกรรมให้เด็ก'\n• UGC Facebook: 'ฮูกคาเฟ่ Coffee & Cactus ตั้งอยู่บ้านฮางโฮง'\n\nDelivery: Wongnai delivery ✅ (0฿) · delivery 10:00-17:00 · LINE MAN likely · ไม่พบ GrabFood/ShopeeFood",
        "pricing": {
            "espresso": {"price": "ไม่ทราบ", "note": ""},
            "americano": {"price": "ไม่ทราบ", "note": ""},
            "latte": {"price": "ไม่ทราบ", "note": "<100฿"},
            "cappuccino": {"price": "ไม่ทราบ", "note": ""},
            "cold_brew": {"price": "ไม่ทราบ", "note": ""},
            "frappe": {"price": "ไม่ทราบ", "note": ""},
            "matcha": {"price": "ไม่ทราบ", "note": ""},
            "signature_drink": {"price": "ไม่ทราบ", "note": "น้ำหมากเม่าไนโตร + กาแฟอังขาง"},
            "food": {"price": "ไม่ทราบ", "note": "เค้กทุเรียน 200-400฿ (half/full pound)"},
            "other": [
                {"name": "กาแฟอังขาง (Angkhang)", "price": "ไม่ทราบ", "note": "signature coffee"},
                {"name": "น้ำหมากเม่าไนโตร", "price": "ไม่ทราบ", "note": "local fruit Nitro — unique!"},
                {"name": "เค้กทุเรียน", "price": "200-400", "note": "half/full pound, จองล่วงหน้า"},
                {"name": "แคสตัส/ไม้อวบน้ำ", "price": "ราคาถูก", "note": "ขาย retail"}
            ]
        },
        "strengths": [
            "เปิดเช้าที่สุดในกลุ่ม (7:30 น.) = ตลาด morning coffee นักเดินทาง",
            "**น้ำหมากเม่าไนโตร** — local fruit + Nitro tech ที่ไม่มีร้านไหนทำในสกลนคร",
            "**สวนแคสตัส** = unique attraction ไม่มีคู่แข่ง + photo content engine",
            "ทำเลริมทางหลวง 22 จับ traffic นักเดินทาง สกลนคร-นครพนม",
            "กิจกรรมเด็ก = ดึง family segment ที่คู่แข่งส่วนใหญ่ไม่มี",
            "Wongnai delivery ✅ 0฿",
            "เปิดทุกวัน = reliable destination"
        ],
        "promotions": [],
        "weaknesses": [
            "ทำเลนอกเมือง ถ.สกลนคร-นครพนม — เข้าถึงยากจากใจกลางเมือง",
            "ที่นั่ง <10 ที่ — scaling จำกัด",
            "Wongnai 1 รีวิว (2019) — outdated credibility",
            "ไม่พบ TikTok/Instagram official = ขาด visual reach ใน 2026",
            "ราคาจำเพาะไม่เปิดเผยสาธารณะ"
        ],
        "location": "172 ถ.สกลนคร-นครพนม (ทางหลวง 22) บ้านฮางโฮง เมืองสกลนคร (นอกเมือง ใกล้ มก.ฉกส.)",
        "hours": "จ-ส 7:30-18:00 · อาทิตย์ 9:00-18:00 · Delivery 10:00-17:00",
        "social_trend": {
            "primary_platform": "Facebook",
            "posting_frequency": "moderate (Facebook active)",
            "content_style": "Coffee & Cactus garden · plant showcase · family activity · local fruit drinks",
            "engagement_level": "low-medium (FB UGC มี · Wongnai credibility เก่า)"
        },
        "delivery": {
            "primary_app": "LINE MAN",
            "apps": ["LINE MAN"],
            "peak_hours": "10:00-17:00 (ตาม delivery window)",
            "active_promos": [],
            "notes": "Wongnai delivery ✅ 0฿ starting fee · delivery window 10:00-17:00 · LINE MAN likely via Wongnai · ไม่พบ GrabFood/ShopeeFood/FoodPanda"
        }
    },
    {
        "id": "competitor-themountain",
        "category": "competitor",
        "title": "The Mountain Coffee and Beverage สกลนคร",
        "summary": "Coffee + Food + Event Venue · ซอยธรรมอักษร ถ.รัฐบำรุง ใกล้ บขส.ใหม่ · จ-อ 08:00-20:30 (ปิดพุธ) · Wongnai 5/5 #16/481 (Top 3%) · Delivery ✅ · ไวน์หมากเม่า + กาแฟน้ำช่อดอกมะพร้าว + Event venue = 3-in-1",
        "updated": "9 Jun 2026",
        "source_url": "https://www.facebook.com/p/The-Mountain-Coffee-and-Beverage-100091151026132/",
        "thumbnail_url": "",
        "tags": ["สกลนคร", "coffee-restaurant", "event-venue", "local-ingredients", "delivery", "family", "b2b"],
        "relevance": "high",
        "detail": "The Mountain Coffee and Beverage สกลนคร — Coffee + Food + Event Venue\n\nที่ตั้ง: ซอยธรรมอักษร ถ.รัฐบำรุง ธาตุนาเวง เมืองสกลนคร (800 เมตรจากปั๊ม PTT ถ.ก๊อมสงฆ์ ใกล้ บขส.ใหม่ → เข้าซอยธรรมอักษร 100 เมตร)\nโทร: 092-621-1148, 094-997-9689\nEmail: themountain888999@gmail.com\nเวลาเปิด: จ-อ 08:00-20:30 (ปิดพุธ) / บางแหล่งระบุ 10:00-21:00\n\nConcept: Coffee + Full Restaurant + Event Venue กว้างโปร่ง มุมถ่ายรูป + ห้องจัดเลี้ยง\nRanking: **Wongnai #16 จาก 481 ร้านกาแฟ/ชาในจังหวัดสกลนคร = Top 3%!**\n\nSocial Presence:\n• Facebook: @The-Mountain-Coffee-and-Beverage (100091151026132) — active videos + photos\n• ไม่พบ Instagram / TikTok official\n• Lemon8: UGC review (gogoaround99) active\n• Trip.com: UGC reviews\n• Email: themountain888999@gmail.com\n• Hashtags: #สกลนคร #รีวิวสกลนคร #ร้านเด็ดสกลนคร #คาเฟ่สกลนคร #themountaincoffee\n\n**Unique Differentiators:**\n• **Event Venue** — สัมมนา, ประชุม, งานเลี้ยง, งานแต่ง, ทัวร์กลุ่ม (B2B revenue stream ที่ไม่มีคู่แข่งในกลุ่ม!)\n• **ไวน์หมากเม่า แบรนด์บ้านเอง** — local fruit wine สกลนคร\n• **กาแฟน้ำช่อดอกมะพร้าว** — specialty local ingredient coffee\n• **Budz Ice cream roll** — brand เฉพาะของร้าน\n• **Full food menu** — เสือย่างกระทะร้อน, ก๋วยเตี๋ยวหมูตุ๋น, ต้มยำทะเลรวม\n\nMenu highlights:\n• กาแฟน้ำช่อดอกมะพร้าว (หวานละมุน ฟิน)\n• Americano (เมนูแนะนำ)\n• เสือย่างกระทะร้อน + จิ้มแจ่ว\n• ก๋วยเตี๋ยวหมูตุ๋น\n• ต้มยำทะเลรวม\n• ไอศครีมโรล Budz\n• ไวน์หมากเม่า\n\nReviews:\n• Wongnai 5/5 (1 review): 'ร้านสวย กาแฟดีครับ'\n• Lemon8: 'เมนูอาหารเพียยบ แวะที่เดียวครบ จบ ปิ๊ง'\n\nDelivery: Wongnai delivery ✅ (0฿) → LINE MAN likely",
        "pricing": {
            "espresso": {"price": "ไม่ทราบ", "note": ""},
            "americano": {"price": "ไม่ทราบ", "note": "เมนูแนะนำ"},
            "latte": {"price": "ไม่ทราบ", "note": ""},
            "cappuccino": {"price": "ไม่ทราบ", "note": ""},
            "cold_brew": {"price": "ไม่ทราบ", "note": ""},
            "frappe": {"price": "ไม่ทราบ", "note": ""},
            "matcha": {"price": "ไม่ทราบ", "note": ""},
            "signature_drink": {"price": "ไม่ทราบ", "note": "กาแฟน้ำช่อดอกมะพร้าว + ไวน์หมากเม่า"},
            "food": {"price": "ไม่ทราบ", "note": "เสือย่าง, ก๋วยเตี๋ยวหมูตุ๋น, ต้มยำทะเล"},
            "other": [
                {"name": "กาแฟน้ำช่อดอกมะพร้าว", "price": "ไม่ทราบ", "note": "local signature"},
                {"name": "ไวน์หมากเม่า (แบรนด์บ้านเอง)", "price": "ไม่ทราบ", "note": "local fruit wine"},
                {"name": "ไอศครีมโรล Budz", "price": "ไม่ทราบ", "note": "brand เฉพาะ"},
                {"name": "Event Venue (B2B)", "price": "ไม่ทราบ", "note": "สัมมนา/งานแต่ง"}
            ]
        },
        "strengths": [
            "**Wongnai #16/481 = Top 3% ในจังหวัด** — สูงกว่า MOKA FOX (#19) = social proof แข็งสุดในกลุ่ม",
            "**Event Venue B2B** — สัมมนา/งานแต่ง = revenue stream ที่ไม่มีคู่แข่ง local cafe ทำ",
            "**Full food menu** (กาแฟ + อาหาร + ขนม) = dwell time สูง + ยอดบิลเฉลี่ยสูงกว่า",
            "**Local ingredients signature** — ไวน์หมากเม่า + กาแฟน้ำช่อดอกมะพร้าว = cultural branding ชัด",
            "เปิดถึง 20:30-21:00 = capture dinner + evening market ได้",
            "Delivery Wongnai ✅",
            "Facebook video content active"
        ],
        "promotions": [],
        "weaknesses": [
            "ปิดวันพุธ = พลาด 1 วัน/สัปดาห์",
            "Wongnai 1 review เท่านั้น — ranking สูงแต่ review count ต่ำ",
            "ราคาไม่เปิดเผยสาธารณะ",
            "ไม่พบ Instagram/TikTok official = visual platform gap",
            "ทำเลอาจเข้าถึงยากกว่าร้านริมถนนใหญ่ (เข้าซอย 100 เมตร)"
        ],
        "location": "ซอยธรรมอักษร ถ.รัฐบำรุง ธาตุนาเวง เมืองสกลนคร (800 เมตรจาก PTT ถ.ก๊อมสงฆ์ ใกล้ บขส.ใหม่)",
        "hours": "จ-อ 08:00-20:30 (ปิดพุธ) / บางแหล่งระบุ 10:00-21:00",
        "social_trend": {
            "primary_platform": "Facebook",
            "posting_frequency": "moderate (Facebook videos active)",
            "content_style": "Coffee + food showcase · event venue promo · local ingredients story",
            "engagement_level": "medium (Facebook active · Wongnai Top 3% · Lemon8/Trip.com UGC)"
        },
        "delivery": {
            "primary_app": "LINE MAN",
            "apps": ["LINE MAN"],
            "peak_hours": "ยังไม่มีข้อมูล",
            "active_promos": [],
            "notes": "Wongnai delivery ✅ 0฿ starting fee → LINE MAN likely via Wongnai integration · ไม่พบ GrabFood/ShopeeFood/FoodPanda · delivery window น่าจะตามเวลาร้าน (08:00-20:30)"
        }
    },
    {
        "id": "delivery-apps-overview",
        "category": "delivery",
        "title": "Delivery Apps ร้านกาแฟ สกลนคร — ภาพรวม 2026",
        "summary": "LINE MAN เบอร์ 1 ไทย (44%) · GrabFood เบอร์ 2 (40%) · ShopeeFood 77 จังหวัด · Peak เช้า 07:00-11:00 และบ่าย 14:00-16:00 · เมนูขายดี: ชาไทย + อเมริกาโน่เย็น",
        "updated": "21 May 2026",
        "source_url": "", "thumbnail_url": "",
        "tags": ["delivery", "LINE MAN", "GrabFood", "ShopeeFood", "สกลนคร"],
        "relevance": "high",
        "detail": "ส่วนแบ่งตลาด Delivery ไทย 2024 (verified):\n• LINE MAN: 44% — เบอร์ 1 ของไทย ครอบคลุม local cafe สูงสุด เชื่อมกับ Wongnai\n• GrabFood: 40% — เบอร์ 2 เสถียรสำหรับ chain (Amazon/Inthanin) มี GrabUnlimited ส่งฟรีไม่จำกัด\n• ShopeeFood: ~10% — ครอบคลุม 77 จังหวัด เปิด 24 ชม. นักล่าโปร Flash Sale\n• Robinhood: 0% GP! (ธนาคารไทยพาณิชย์) — Foodpanda: รอบนอก ~30%\n\nค่าคอมมิชชัน GP (ข้อมูลจาก web):\n• LINE MAN: ~25-30%\n• GrabFood: ~15-30% (ขึ้นกับสัญญา)\n• ShopeeFood: ~30%\n• Robinhood: 0% (แต่พื้นที่จำกัด)\n⚠️ ยืนยันกับทีม sales โดยตรงก่อนสมัคร\n\nPeak Coffee Delivery ไทย 2026 (verified):\n• เช้า 07:00-11:00 น. — peak หลัก รายได้สูงสุดต่อวัน\n• บ่าย 14:00-16:00 น. — peak รอง Coffee Break\n• เมนูขายดีปี 2026: ชาไทย และ อเมริกาโน่เย็น\n• กลยุทธ์: bundle กาแฟ + เบเกอรี่ เพิ่มมูลค่าต่อบิล\n\nแนะนำ: เริ่ม LINE MAN ก่อน ตั้งราคา delivery บวก 10-15% จากราคาหน้าร้าน",
        "pricing": {"espresso":{"price":"","note":""},"americano":{"price":"","note":""},"latte":{"price":"","note":""},"cappuccino":{"price":"","note":""},"cold_brew":{"price":"","note":""},"frappe":{"price":"","note":""},"matcha":{"price":"","note":""},"signature_drink":{"price":"","note":""},"food":{"price":"","note":""},"other":[]},
        "strengths": ["LINE MAN เบอร์ 1 ไทย 44% market share", "GrabUnlimited ดึงลูกค้า chain", "Robinhood 0% GP (ถ้าพื้นที่รองรับ)", "ShopeeFood Flash Sale สร้าง traffic burst"],
        "promotions": ["GrabFood x Café Amazon ลด 50-60 บาท โค้ด TRYAM60", "LINE MAN: ส่งฟรีครบ 150 บาท", "ShopeeFood: 30-50% off Payday/Flash Sale", "โครงการรัฐ: GP ลดเหลือ 7-9% ชั่วคราว (ตรวจสอบแคมเปญปัจจุบัน)"],
        "weaknesses": ["ค่าคอม 25-30% กระทบ margin ร้าน", "เครื่องดื่มเย็นละลายระหว่างส่ง", "ต้องมี packaging ที่ดีเพิ่มต้นทุน"],
        "social_trend": {"primary_platform":"LINE MAN","posting_frequency":"","content_style":"","engagement_level":"high"}
    },
    {
        "id": "delivery-local-cafes",
        "category": "delivery",
        "title": "ร้านกาแฟท้องถิ่นสกลนคร — สถานะ Delivery (Updated 24 May 2026)",
        "summary": "WE HUG (LINE MAN+FoodPanda ✅) · CHANN (LINE MAN ✅) · SNIFF (LINE MAN ✅) · จุมพฏ (LINE MAN ✅ 2 สาขา) · Elemental Haus (LINE MAN ✅) · Rok 'n Road (LINE MAN ✅) · Alice (LINE MAN ✅) · FIKA (LINE MAN ✅) · ZMd (LINE MAN ✅) · BOONNAR (LINE MAN ✅) · A Cup of Joy (LINE MAN ✅) · MOKA FOX (LINE MAN ✅) · RAINTREE (Wongnai direct) · ป่านาคำหอม (❌) · มีสุข (❌) · All of KK (❌) · CANTO (ไม่ทราบ) · Chains: Amazon/Wawee/Inthanin (GrabFood ✅)",
        "updated": "24 May 2026",
        "source_url": "https://www.wongnai.com/listings/sakonnakhon-coffee-cafe", "thumbnail_url": "",
        "tags": ["specialty", "local", "delivery", "สกลนคร", "Wongnai", "LINE MAN"],
        "relevance": "high",
        "detail": "ร้านกาแฟสกลนครและสถานะ Delivery (verified จาก Wongnai / LINE MAN — อัพเดท 24 พ.ค. 2026):\n\n✅ ยืนยันอยู่บน LINE MAN / Wongnai Delivery:\n• WE HUG CAFE — LINE MAN + FoodPanda + Wongnai Delivery · ทุกวัน 08:00-19:00 (กว้างสุด) · ส่งฟรีระยะใกล้\n• Alice Coffee and Bread — Wongnai x LINE MAN · จ-ศ 08:30-16:30 / เสาร์ 09:00-17:30 · เมนูดัง: Thai Tea 65฿, Coco Dirty 95฿\n• FIKA Cafè & Coworking — Wongnai x LINE MAN ยืนยัน\n• ZMd cafe' Specialty Coffee — Wongnai x LINE MAN ยืนยัน\n• Café Amazon (สาขาสกลนคร) — GrabFood ยืนยัน chain ใหญ่\n\n⚠️ มีตัวตนบน Social/Wongnai แต่ยังไม่ verified บน delivery app:\n• RAINTREE Cafe — Facebook 77K, Instagram @raintree_sakon · เน้น dine-in day cafe + night bar · Wongnai ระบุ delivery 08:00-17:00 แต่ยังไม่พบบน LINE MAN/GrabFood โดยตรง\n\n❓ ยังไม่มีข้อมูล:\n• CANTO CAFE — เพิ่งเพิ่มเข้าระบบ ยังไม่มีข้อมูลออนไลน์\n\n🆕 เปิดใหม่ 2025-2026:\n• CHANN CAFE — เปิดใหม่ พ.ย. 2568 · LINE MAN ✅\n• supa.cafe — บรรยากาศ homestyle · ยังไม่ verified delivery\n\nหมายเหตุ: Web search ไม่สามารถดึงรายการร้านจาก LINE MAN/GrabFood โดยตรงได้ (แสดงตาม GPS เท่านั้น) ต้องเปิดแอปในพื้นที่สกลนครเพื่อยืนยัน\n\nWongnai รวมร้านกาแฟสกลนคร: https://www.wongnai.com/listings/sakonnakhon-coffee-cafe\n\nเทรนด์ใหม่: LINE MAN แซงหน้า GrabFood เป็นเบอร์ 1 ระดับชาติ — ร้าน local ต่างจังหวัดเน้น Wongnai x LINE MAN มากกว่า GrabFood\nPeak delivery (national): 11:00-13:00 และ 17:00-20:00 น.\nกลยุทธ์: Bundle กาแฟ + เบเกอรี เพิ่มมูลค่าต่อบิล offset ค่า GP 30-35%",
        "pricing": {"espresso":{"price":"","note":""},"americano":{"price":"","note":""},"latte":{"price":"","note":""},"cappuccino":{"price":"","note":""},"cold_brew":{"price":"","note":""},"frappe":{"price":"","note":""},"matcha":{"price":"","note":""},"signature_drink":{"price":"","note":""},"food":{"price":"","note":""},"other":[]},
        "strengths": ["ร้าน local มี LINE MAN ครอบคลุม", "Specialty = differentiator ใน delivery", "GrabFood เร็ว ป้องกันเครื่องดื่มละลาย"],
        "promotions": ["LINE MAN ส่งฟรีครบ 150 บาท", "ShopeeFood Flash Sale ต้นเดือน"],
        "weaknesses": ["ข้อมูลร้านบน platform ยังไม่ verified real-time", "ต้องยืนยันว่า RAINTREE CAFE เปิด delivery จริง"],
        "social_trend": {"primary_platform":"LINE MAN","posting_frequency":"","content_style":"","engagement_level":"high"}
    },
    {
        "id": "knowledge-third-wave-2026",
        "category": "coffee_knowledge",
        "title": "Third Wave Coffee Trend ไทย 2026",
        "summary": "Specialty coffee ขยายตัวสู่ต่างจังหวัด คนอีสานสนใจ origin beans มากขึ้น cold brew + nitro coffee เป็น viral content",
        "source_url": "", "thumbnail_url": "",
        "tags": ["specialty", "thirdwave", "เทรนด์2026", "coldBrew"],
        "relevance": "high",
        "detail": "ปี 2026 Third Wave Coffee ขยายตัวจากกรุงเทพฯ สู่ต่างจังหวัด ผู้บริโภคอีสานสนใจ single origin, processing method มากขึ้น TikTok content เกี่ยวกับ 'กาแฟไทย' มียอดวิวสูง Cold brew + Nitro Cold Brew เป็น trending เมนู Signature drink unique ต่างร้านเป็น differentiator สำคัญ",
        "pricing": {"espresso":{"price":"","note":""},"americano":{"price":"","note":""},"latte":{"price":"","note":""},"cappuccino":{"price":"","note":""},"cold_brew":{"price":"","note":""},"frappe":{"price":"","note":""},"matcha":{"price":"","note":""},"signature_drink":{"price":"","note":""},"food":{"price":"","note":""},"other":[]},
        "strengths": [], "promotions": [],
        "social_trend": {"primary_platform":"TikTok","posting_frequency":"","content_style":"educational","engagement_level":"high"}
    },
    {
        "id": "knowledge-hashtags-coffee",
        "category": "coffee_knowledge",
        "title": "Hashtags กาแฟ ยืนยันจาก TikTok/IG จริง",
        "summary": "#กาแฟสกลนคร #คาเฟ่สกลนคร #latteart #กาแฟไทย #barista #specialtycoffee #คาเฟ่ไทย",
        "source_url": "", "thumbnail_url": "",
        "tags": ["hashtag", "TikTok", "Instagram", "สกลนคร"],
        "relevance": "high",
        "detail": "Hashtags สำหรับร้านกาแฟในสกลนคร แนะนำใช้ทุกโพสต์: Local (#กาแฟสกลนคร #คาเฟ่สกลนคร #ร้านกาแฟสกลนคร) + National (#latteart #กาแฟไทย #barista #specialtycoffee #coffeeaddict #coffeelovers #คาเฟ่ไทย) ควร mix ทั้ง local + national เพื่อ reach ทั้ง 2 กลุ่ม",
        "pricing": {"espresso":{"price":"","note":""},"americano":{"price":"","note":""},"latte":{"price":"","note":""},"cappuccino":{"price":"","note":""},"cold_brew":{"price":"","note":""},"frappe":{"price":"","note":""},"matcha":{"price":"","note":""},"signature_drink":{"price":"","note":""},"food":{"price":"","note":""},"other":[]},
        "strengths": [], "promotions": [],
        "social_trend": {"primary_platform":"TikTok","posting_frequency":"","content_style":"educational","engagement_level":"high"}
    },
    {
        "id": "event-coffee-fest-2026",
        "category": "news_events",
        "title": "Thailand Coffee Fest 2026",
        "summary": "งาน coffee festival ประจำปีในไทย โอกาสเรียนรู้เทรนด์ พบ supplier เมล็ดกาแฟและอุปกรณ์ใหม่",
        "source_url": "", "thumbnail_url": "",
        "tags": ["expo", "coffee festival", "Thailand", "2026"],
        "relevance": "high",
        "detail": "Thailand Coffee Fest เป็นงานกาแฟใหญ่ในไทยจัดขึ้นทุกปี มี specialty roasters, equipment suppliers, barista competition โอกาสดีในการหา single origin beans ใหม่ และพบ equipment ราคาดี มักจัดในกรุงเทพฯ ช่วงกลางปี",
        "pricing": {"espresso":{"price":"","note":""},"americano":{"price":"","note":""},"latte":{"price":"","note":""},"cappuccino":{"price":"","note":""},"cold_brew":{"price":"","note":""},"frappe":{"price":"","note":""},"matcha":{"price":"","note":""},"signature_drink":{"price":"","note":""},"food":{"price":"","note":""},"other":[]},
        "strengths": [], "promotions": [],
        "social_trend": {"primary_platform":"","posting_frequency":"","content_style":"","engagement_level":""}
    },
    {
        "id": "equipment-espresso-machine-2026",
        "category": "equipment",
        "title": "Semi-Auto Espresso Machine + Grinder Bundle 2026",
        "summary": "ราคา entry-level espresso machine ลดลงมาก Breville/DeLonghi ราคาเริ่มต้น 15,000 บาท grinder + machine bundle คุ้มค่า",
        "source_url": "", "thumbnail_url": "",
        "tags": ["อุปกรณ์", "เครื่องชงกาแฟ", "grinder", "espresso"],
        "relevance": "high",
        "detail": "ปี 2026 ราคา semi-auto espresso machine ระดับ entry (Breville Bambino, DeLonghi Dedica) ลดลงเหลือ 15,000-25,000 บาท grinder ดีระดับ Baratza Encore ~8,000 บาท bundle ทั้งคู่ ~23,000 บาท เป็นจุดเริ่มต้นดีสำหรับร้านกาแฟเล็กๆ การถ่าย content latte art จาก machine สวยงาม viral ได้ง่าย",
        "pricing": {"espresso":{"price":"","note":""},"americano":{"price":"","note":""},"latte":{"price":"","note":""},"cappuccino":{"price":"","note":""},"cold_brew":{"price":"","note":""},"frappe":{"price":"","note":""},"matcha":{"price":"","note":""},"signature_drink":{"price":"","note":""},"food":{"price":"","note":""},"other":[]},
        "strengths": [], "promotions": [],
        "social_trend": {"primary_platform":"","posting_frequency":"","content_style":"","engagement_level":""}
    },
]


def load_intel_json() -> list:
    """Load intel data from latest reports/intel-*.json; fall back to hardcoded data."""
    reports_dir = PROJECT_ROOT / "reports"
    if reports_dir.exists():
        json_files = sorted(reports_dir.glob("intel-*.json"), reverse=True)
        if json_files:
            try:
                with open(json_files[0], encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return INTEL_DATA_FALLBACK


def load_logos() -> dict:
    """สแกน dashboard/assets/logos/ → {competitor-id: 'assets/logos/<file>'}"""
    logos = {}
    logo_dir = PROJECT_ROOT / "dashboard" / "assets" / "logos"
    exts = {".png", ".jpg", ".jpeg", ".webp", ".avif", ".svg", ".gif"}
    if logo_dir.exists():
        for f in sorted(logo_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in exts:
                logos[f.stem] = f"assets/logos/{f.name}"
    return logos


def load_drink_costs() -> dict:
    """Load ต้นทุนเครื่องดื่ม จาก data/drink-costs.json (สร้างจาก parse_drink_costs.py)."""
    f = PROJECT_ROOT / "data" / "drink-costs.json"
    if f.exists():
        try:
            with open(f, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            pass
    return {}  # empty — view shows empty state


def load_tracker_json() -> dict:
    """Load competitor tracking data from data/competitor-tracking-latest.json."""
    tracking_file = PROJECT_ROOT / "data" / "competitor-tracking-latest.json"
    if tracking_file.exists():
        try:
            with open(tracking_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}  # empty — tracker view will show "ยังไม่มีข้อมูล"


# ─────────────────────────────────────────────────────────────
# Step 1: Run normalize.py for each detected platform path
# ─────────────────────────────────────────────────────────────

def _run_one_normalize(input_path: str) -> tuple[str, Path] | None:
    """Run normalize.py on a single path. Returns (platform, json_path) or None."""
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "normalize.py"), input_path],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    if result.returncode != 0:
        print(f"[warn] normalize.py failed for {input_path}:\n{result.stderr.strip()}")
        return None

    platform = None
    for line in result.stdout.splitlines():
        if line.startswith("Platform"):
            platform = line.split(":", 1)[-1].strip().lower()
            break
    if not platform:
        print(f"[warn] ตรวจจับ platform ไม่ได้จาก output ของ {input_path}")
        return None

    today = datetime.now().strftime("%Y%m%d")
    json_path = PROJECT_ROOT / "data" / "history" / f"{platform}_{today}.json"
    if not json_path.exists():
        print(f"[warn] ไม่พบ normalized file: {json_path}")
        return None

    print(f"[normalize] platform={platform}  file={json_path.name}")
    return platform, json_path


def run_normalize_all(input_path: str) -> list[tuple[str, Path]]:
    """
    Handles three cases:
      1. Single CSV file → normalize once
      2. Single platform folder (e.g. sample-data/Facebook/) → normalize once
      3. Root folder with sub-folders (e.g. sample-data/) → normalize each sub-folder
    Returns list of (platform, json_path) pairs.
    """
    p = Path(input_path)
    results = []

    if p.is_file():
        r = _run_one_normalize(input_path)
        if r:
            results.append(r)
        return results

    # Check if any immediate child is itself a directory (root-of-platforms case)
    subdirs = [c for c in sorted(p.iterdir()) if c.is_dir()]
    csvs_in_root = list(p.glob("*.csv"))

    if subdirs and not csvs_in_root:
        # Treat each subdir as a platform folder
        for sub in subdirs:
            r = _run_one_normalize(str(sub))
            if r:
                results.append(r)
    else:
        # Single platform folder
        r = _run_one_normalize(input_path)
        if r:
            results.append(r)

    return results


# ─────────────────────────────────────────────────────────────
# Step 2: Load all available normalized JSONs for today
# ─────────────────────────────────────────────────────────────

def load_all_history(today: str) -> dict[str, dict]:
    """Load all platform JSONs from data/history/ for today. Returns {platform: {...}}."""
    history_dir = PROJECT_ROOT / "data" / "history"
    loaded = {}
    for platform in PLATFORM_LABELS:
        json_path = history_dir / f"{platform}_{today}.json"
        if json_path.exists():
            with open(json_path, encoding="utf-8") as f:
                loaded[platform] = json.load(f)
            print(f"[load] {json_path.name}  ({loaded[platform]['row_count']} rows)")
    return loaded


# ─────────────────────────────────────────────────────────────
# Step 3: Compute metrics
# ─────────────────────────────────────────────────────────────

def _safe_int(v):
    try:
        return int(v) if not math.isnan(float(v)) else 0
    except Exception:
        return 0


def compute_metrics(df: pd.DataFrame, platform: str) -> dict:
    m = {}
    m["days"] = len(df)
    m["total_reach"] = _safe_int(df["reach"].sum()) if "reach" in df.columns else 0
    m["avg_reach"] = round(float(df["reach"].mean()), 1) if "reach" in df.columns else 0.0

    # engagement rate
    if "engagement" in df.columns and "reach" in df.columns:
        active = df[df["reach"] > 0]
        if not active.empty:
            m["avg_er"] = round(float((active["engagement"] / active["reach"] * 100).mean()), 2)
        else:
            m["avg_er"] = 0.0
        m["total_engagement"] = _safe_int(df["engagement"].sum())
    elif all(c in df.columns for c in ["likes", "comments", "shares"]):
        active = df[df["reach"] > 0]
        if not active.empty:
            eng = active["likes"] + active["comments"] + active["shares"]
            m["avg_er"] = round(float((eng / active["reach"] * 100).mean()), 2)
        else:
            m["avg_er"] = 0.0
        m["total_engagement"] = _safe_int((df["likes"] + df["comments"] + df["shares"]).sum())
    else:
        m["avg_er"] = 0.0
        m["total_engagement"] = 0

    m["new_followers"] = _safe_int(df["new_followers"].sum()) if "new_followers" in df.columns else 0
    return m


# ─────────────────────────────────────────────────────────────
# Step 4: Build JS DATA object
# ─────────────────────────────────────────────────────────────

def build_platform_data(platform: str, raw: dict) -> dict:
    df = pd.DataFrame(raw["data"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    metrics = compute_metrics(df, platform)

    dates = df["date"].dt.strftime("%d %b").tolist()
    reach = [_safe_int(v) for v in df["reach"].tolist()] if "reach" in df.columns else []

    # doughnut
    dough_def = DOUGHNUT_DEF.get(platform, [])
    dough_labels = []
    dough_data = []
    dough_colors = []
    for col, label, color in dough_def:
        dough_labels.append(label)
        dough_colors.append(color)
        if col in df.columns:
            dough_data.append(_safe_int(df[col].sum()))
        else:
            dough_data.append(0)

    # table rows (sorted newest first)
    table_df = df.sort_values("date", ascending=False)
    table_rows = []
    for _, row in table_df.iterrows():
        r = {}
        for col in df.columns:
            if col == "date":
                r["date"] = row["date"].strftime("%Y-%m-%d")
            else:
                try:
                    r[col] = _safe_int(row[col])
                except Exception:
                    r[col] = 0
        table_rows.append(r)

    # peak reach for highlighting
    peak_reach = _safe_int(df["reach"].max()) if "reach" in df.columns else 0

    return {
        "dates":      dates,
        "reach":      reach,
        "columns":    df.columns.tolist(),
        "peak_reach": peak_reach,
        "metrics":    metrics,
        "doughnut": {
            "labels": dough_labels,
            "data":   dough_data,
            "colors": dough_colors,
        },
        "table": table_rows,
    }


def build_data_json(all_history: dict[str, dict]) -> tuple[str, str]:
    """Returns (DATA_json_str, COMP_json_str)."""
    data_obj = {}
    for platform, raw in all_history.items():
        data_obj[platform] = build_platform_data(platform, raw)

    # COMP for home comparison
    platforms_available = list(data_obj.keys())
    comp = {
        "platforms":        platforms_available,
        "labels":           [PLATFORM_LABELS.get(p, p) for p in platforms_available],
        "avg_reach":        [data_obj[p]["metrics"]["avg_reach"] for p in platforms_available],
        "avg_er":           [data_obj[p]["metrics"]["avg_er"] for p in platforms_available],
        "total_reach":      [data_obj[p]["metrics"]["total_reach"] for p in platforms_available],
        "total_engagement": [data_obj[p]["metrics"]["total_engagement"] for p in platforms_available],
        "colors":           [PLATFORM_COLORS.get(p, "#888") for p in platforms_available],
    }

    return json.dumps(data_obj, ensure_ascii=False), json.dumps(comp, ensure_ascii=False)


# ─────────────────────────────────────────────────────────────
# Step 5: Build HTML chunks
# ─────────────────────────────────────────────────────────────

def _fmt(n, decimals=0):
    if n is None:
        return "—"
    if decimals:
        return f"{float(n):,.{decimals}f}"
    return f"{int(n):,}" if isinstance(n, (int, float)) else str(n)


def build_sidebar_nav(all_history: dict[str, dict]) -> str:
    items = []
    for platform in PLATFORM_LABELS:
        if platform not in all_history:
            continue
        label = PLATFORM_LABELS[platform]
        color = PLATFORM_COLORS[platform]
        items.append(
            '<button onclick="showView(\'view-{p}\')" id="nav-{p}" '
            'class="nav-btn w-full text-left px-4 py-2.5 rounded-xl flex items-center gap-3 '
            'text-slate-600 hover:bg-slate-50 transition-colors text-sm">'
            '<span class="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0" '
            'style="background:{c}"></span>{l}'
            '</button>'.format(p=platform, c=color, l=label)
        )
    return "\n".join(items)


def build_platform_view(platform: str, raw: dict) -> str:
    df = pd.DataFrame(raw["data"])
    df["date"] = pd.to_datetime(df["date"])
    metrics = compute_metrics(df, platform)
    color = PLATFORM_COLORS.get(platform, "#888")
    label = PLATFORM_LABELS.get(platform, platform)
    days = metrics["days"]

    er_display = "{v}%".format(v=_fmt(metrics["avg_er"], 2))
    followers_display = _fmt(metrics["new_followers"])

    # Table HTML
    show_cols = ["date"] + [c for c in df.columns if c != "date"]
    peak_reach = _safe_int(df["reach"].max()) if "reach" in df.columns else 0

    th_cells = "".join(
        '<th class="px-4 py-3 text-left text-xs font-bold uppercase tracking-widest '
        'text-slate-500 whitespace-nowrap {align}">{label}</th>'.format(
            label=COL_LABELS_TH.get(c, c),
            align='text-right' if c != 'date' else '',
        )
        for c in show_cols
    )

    td_rows = []
    for _, row in df.sort_values("date", ascending=False).iterrows():
        is_peak = ("reach" in df.columns) and (_safe_int(row["reach"]) == peak_reach) and (peak_reach > 0)
        cells = ""
        for c in show_cols:
            val = row[c]
            if c == "date":
                cells += '<td class="px-4 py-3 text-slate-600 whitespace-nowrap">{v}</td>'.format(
                    v=pd.Timestamp(val).strftime("%d %b %Y")
                )
            else:
                try:
                    iv = _safe_int(val)
                    formatted = "{:,}".format(iv)
                except Exception:
                    formatted = str(val)
                extra_class = ""
                if is_peak and c == "reach":
                    extra_class = " font-bold"
                    style = ' style="color:{c}"'.format(c=color)
                else:
                    style = ""
                cells += (
                    '<td class="px-4 py-3 text-right tabular-nums{cls}"{style}>{v}</td>'.format(
                        cls=extra_class, style=style, v=formatted
                    )
                )
        td_rows.append("<tr class=\"hover:bg-slate-50 border-b border-slate-100 last:border-0\">{cells}</tr>".format(cells=cells))

    table_html = (
        '<div class="overflow-x-auto">'
        '<table class="w-full text-sm">'
        '<thead><tr class="border-b-2 border-slate-200">{th}</tr></thead>'
        '<tbody>{rows}</tbody>'
        '</table></div>'
    ).format(th=th_cells, rows="".join(td_rows))

    return (
        '<div id="view-{platform}" class="view">'
        '<div class="flex items-center gap-3 mb-6">'
        '<span class="text-xs font-bold uppercase tracking-widest px-3 py-1 rounded-full text-white" '
        'style="background:{color}">{label}</span>'
        '<h1 class="text-3xl font-black text-slate-800">Dashboard</h1>'
        '</div>'

        '<!-- KPI Cards -->'
        '<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">'

        '<div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">'
        '<div class="text-xs uppercase tracking-widest text-slate-400 mb-3">ยอดดูรวม</div>'
        '<div class="kpi-value text-4xl font-black text-slate-800">{total_reach}</div>'
        '<div class="text-xs text-slate-400 mt-1">{days} วัน</div>'
        '</div>'

        '<div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">'
        '<div class="text-xs uppercase tracking-widest text-slate-400 mb-3">ยอดดูเฉลี่ย/วัน</div>'
        '<div class="kpi-value text-4xl font-black text-slate-800">{avg_reach}</div>'
        '<div class="text-xs text-slate-400 mt-1">เฉลี่ย {days} วัน</div>'
        '</div>'

        '<div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">'
        '<div class="text-xs uppercase tracking-widest text-slate-400 mb-3">อัตราการมีส่วนร่วม</div>'
        '<div class="kpi-value text-4xl font-black" style="color:{color}">{avg_er}</div>'
        '<div class="text-xs text-slate-400 mt-1">เฉลี่ยวันที่ active</div>'
        '</div>'

        '<div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">'
        '<div class="text-xs uppercase tracking-widest text-slate-400 mb-3">ผู้ติดตามใหม่</div>'
        '<div class="kpi-value text-4xl font-black text-slate-800">{new_followers}</div>'
        '<div class="text-xs text-slate-400 mt-1">{days} วัน</div>'
        '</div>'

        '</div>'

        '<!-- Charts Grid -->'
        '<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">'

        '<div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">'
        '<h2 class="text-sm font-bold text-slate-700 mb-4">แนวโน้มยอดดูรายวัน</h2>'
        '<div class="relative h-64"><canvas id="{platform}LineChart"></canvas></div>'
        '</div>'

        '<div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">'
        '<h2 class="text-sm font-bold text-slate-700 mb-4">สัดส่วนการมีส่วนร่วม</h2>'
        '<div class="relative h-64"><canvas id="{platform}DoughnutChart"></canvas></div>'
        '</div>'

        '</div>'

        '<!-- Daily Table -->'
        '<div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">'
        '<h2 class="text-sm font-bold text-slate-700 mb-4">ข้อมูลรายวัน</h2>'
        '{table}'
        '</div>'

        '</div>'
    ).format(
        platform=platform,
        color=color,
        label=label,
        total_reach=_fmt(metrics["total_reach"]),
        avg_reach=_fmt(metrics["avg_reach"], 1),
        avg_er=er_display,
        new_followers=followers_display,
        days=days,
        table=table_html,
    )


# ─────────────────────────────────────────────────────────────
# HTML Template
# ─────────────────────────────────────────────────────────────

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="th" data-theme="coffee">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Social Analytics Dashboard — ร้านกาแฟ สกลนคร</title>
  <link href="https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <script>tailwind.config = {{ theme: {{ extend: {{}} }} }};</script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    /* ── Theme variables ── */
    :root {{
      --bg:           #f4f2ed;
      --sidebar:      #ffffff;
      --card:         #ffffff;
      --card-border:  #e8e2d8;
      --text:         #1c160f;
      --text-muted:   #6b6256;
      --grid:         #ece6dc;
      --nav-active:   #f1ebe2;
      --nav-text:     #1c160f;
      --fancy-body:   none;
    }}
    [data-theme="dark"] {{
      --bg:           #0f172a;
      --sidebar:      #1e293b;
      --card:         #1e293b;
      --card-border:  #334155;
      --text:         #f8fafc;
      --text-muted:   #94a3b8;
      --grid:         #334155;
      --nav-active:   #334155;
      --nav-text:     #f8fafc;
    }}
    [data-theme="fancy"] {{
      --bg:           transparent;
      --sidebar:      rgba(0,0,0,0.3);
      --card:         rgba(255,255,255,0.08);
      --card-border:  rgba(255,255,255,0.15);
      --text:         #ffffff;
      --text-muted:   rgba(255,255,255,0.6);
      --grid:         rgba(255,255,255,0.1);
      --nav-active:   rgba(255,255,255,0.15);
      --nav-text:     #ffffff;
    }}
    [data-theme="coffee"] {{
      --bg:           #0D0700;
      --sidebar:      #160C02;
      --card:         #2D1A08;
      --card-border:  #7A4A20;
      --text:         #F8EDD5;
      --text-muted:   #D4AC78;
      --grid:         #3D2010;
      --nav-active:   #3D2212;
      --nav-text:     #F8EDD5;
    }}

    /* ── Apply variables globally ── */
    body {{ background-color: var(--bg); color: var(--text); }}
    [data-theme="fancy"] body {{ background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%) fixed; background-attachment: fixed; }}
    [data-theme="coffee"] body {{ background: linear-gradient(160deg, #0D0700 0%, #160C02 55%, #0F0900 100%); min-height: 100vh; }}
    aside {{ background-color: var(--sidebar) !important; border-color: var(--card-border) !important; }}
    [data-theme="fancy"] aside {{ backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); }}
    .bg-white  {{ background-color: var(--card) !important; border-color: var(--card-border) !important; }}
    [data-theme="fancy"] .bg-white {{ backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); }}
    .bg-slate-100 {{ background-color: var(--bg) !important; }}
    .bg-slate-50 {{ background-color: var(--nav-active) !important; }}
    .border-slate-200, .border-slate-100 {{ border-color: var(--card-border) !important; }}
    .text-slate-800, .text-slate-900 {{ color: var(--text) !important; }}
    .text-slate-700, .text-slate-600 {{ color: var(--text-muted) !important; }}
    .text-slate-500, .text-slate-400 {{ color: var(--text-muted) !important; opacity: .85; }}
    th {{ color: var(--text-muted) !important; border-color: var(--card-border) !important; }}
    td {{ color: var(--text) !important; border-color: var(--card-border) !important; }}
    tr:hover td {{ background-color: var(--nav-active) !important; }}
    thead tr {{ background-color: var(--card) !important; }}

    /* nav active */
    .nav-btn.active {{ background: var(--nav-active) !important; color: var(--nav-text) !important; font-weight: 600; }}

    /* fancy KPI gradient text */
    [data-theme="fancy"] .kpi-value {{
      background: linear-gradient(135deg, #60a5fa, #a78bfa);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}
    /* coffee KPI accent + card header contrast */
    [data-theme="coffee"] .kpi-value {{ color: #F0C060 !important; }}
    [data-theme="coffee"] h1, [data-theme="coffee"] h2 {{ color: var(--text) !important; }}

    /* theme toggle button */
    .theme-btn {{
      cursor: pointer; border: none; background: transparent;
      font-size: 1.1rem; padding: 4px 6px; border-radius: 8px;
      transition: background .15s;
    }}
    .theme-btn:hover {{ background: var(--nav-active); }}
    .theme-btn.active-theme {{ background: var(--nav-active); outline: 2px solid var(--card-border); }}

    /* misc */
    .view {{ display: none; }}
    .view.active {{ display: block; }}
    .drop-zone {{ transition: border-color .2s, background .2s; }}
    .drop-zone.drag-over {{ border-color: #3b82f6; background: #eff6ff; }}
    .toast {{
      position: fixed; bottom: 24px; right: 24px; z-index: 9999;
      background: #10b981; color: #fff; padding: 14px 22px;
      border-radius: 12px; font-weight: 600; font-size: 0.875rem;
      box-shadow: 0 8px 24px rgba(0,0,0,.18);
      transform: translateY(80px); opacity: 0;
      transition: transform .3s, opacity .3s;
    }}
    .toast.show {{ transform: translateY(0); opacity: 1; }}

    /* ── Mobile responsive ── */
    #mobile-topbar {{
      display: none;
      position: fixed; top: 0; left: 0; right: 0; z-index: 30;
      background-color: var(--sidebar); border-bottom: 1px solid var(--card-border);
    }}
    #sidebar-overlay {{
      display: none;
      position: fixed; inset: 0; z-index: 40;
      background: rgba(0,0,0,.5);
    }}
    @media (max-width: 767px) {{
      #mobile-topbar {{ display: flex; }}
      #sidebar {{
        position: fixed; top: 0; left: 0; bottom: 0; z-index: 50;
        transform: translateX(-100%);
        transition: transform .28s cubic-bezier(.4,0,.2,1);
        box-shadow: 4px 0 24px rgba(0,0,0,.15);
      }}
      #sidebar.sidebar-open {{ transform: translateX(0); }}
      #sidebar-overlay.overlay-open {{ display: block; }}
      #sidebar-close-btn {{ display: block !important; }}
      #main-content {{ padding: 4.5rem 1rem 1.5rem; }}
      .compare-chart-wrap {{ height: 120px !important; }}
    }}

    /* ── Intel / Pricing view tabs ── */
    .intel-tab, .pricing-tab {{
      cursor: pointer; padding: 5px 14px; border-radius: 9999px;
      font-size: .78rem; font-weight: 600;
      border: 2px solid transparent; transition: all .18s;
      color: var(--text-muted); background: transparent;
    }}
    .intel-tab.active, .pricing-tab.active, .trk-tab.active {{
      box-shadow: 0 0 0 2px #f6ecda, 0 0 0 4px #75410a, 0 3px 10px rgba(70,37,6,.35);
      transform: translateY(-1px); font-weight: 800;
    }}
    .intel-tab:hover:not(.active), .pricing-tab:hover:not(.active), .trk-tab:hover:not(.active) {{
      filter: brightness(1.06);
    }}

    /* ── Intel accordion ── */
    .intel-accord {{
      border: 1px solid var(--card-border); border-radius: 14px;
      overflow: hidden; margin-bottom: 8px; background: var(--card);
    }}
    .intel-accord-hdr {{
      display: flex; align-items: center; justify-content: space-between;
      padding: 13px 18px; cursor: pointer; user-select: none;
    }}
    .intel-accord-hdr:hover {{ background: var(--nav-active); }}
    .intel-accord-body {{ display: none; padding: 0 18px 16px; }}
    .intel-accord-body.open {{ display: block; }}

    /* ── Update / last-updated badge ── */
    .update-badge {{
      display: flex; align-items: center; flex-wrap: wrap; gap: 10px;
      padding: 10px 16px; border-radius: 14px;
      background: var(--card); border: 1px solid var(--card-border);
      font-size: .8rem; color: var(--text-muted);
    }}
    .update-badge .ub-pill {{
      display: inline-flex; align-items: center; gap: 6px;
      padding: 3px 11px; border-radius: 9999px; font-weight: 700;
      background: #10b98122; color: #059669;
    }}
    .update-badge .ub-date {{ color: var(--text); font-weight: 600; }}
    .update-badge a {{ color: #059669; font-weight: 600; text-decoration: none; }}
    .update-badge a:hover {{ text-decoration: underline; }}

    /* ── Bullet list (อ่านง่าย: แตกข้อความยาวเป็นข้อ ๆ) ── */
    .bullet-list {{ list-style: none; padding: 0; margin: 0; }}
    .bullet-list li {{
      padding-left: 2px; margin-bottom: 6px; line-height: 1.6;
      display: flex; gap: 7px; align-items: flex-start;
    }}
    .bullet-list li:last-child {{ margin-bottom: 0; }}
    .bullet-list li .bl-mark {{ flex-shrink: 0; }}

    /* ════════ Overview (หน้าภาพรวม) — premium cafe bento ════════ */
    :root {{
      --ov-espresso-1: #241307;
      --ov-espresso-2: #4a2c17;
      --ov-caramel:    #e0a256;
      --ov-crema:      #f6ecda;
      --ov-accent-ink: #a55f17;
    }}
    .ov-h1 {{ font-size: clamp(1.7rem, 1.2rem + 1.6vw, 2.4rem); font-weight: 900;
      letter-spacing: -0.02em; color: var(--text); line-height: 1.05; }}
    .ov-sub-h {{ color: var(--text-muted); font-size: .9rem; margin-top: 4px; }}

    .ov-grid {{ display: grid; grid-template-columns: 1.65fr 1fr; gap: 16px; }}
    .ov-plats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
    @media (max-width: 1024px) {{ .ov-grid {{ grid-template-columns: 1fr; }} }}
    @media (max-width: 760px)  {{ .ov-plats {{ grid-template-columns: 1fr; }} }}

    .ov-tile {{
      background: var(--card); border: 1px solid var(--card-border);
      border-radius: 22px; padding: 24px; position: relative; overflow: hidden;
      transition: transform .35s cubic-bezier(.22,1,.36,1), box-shadow .35s cubic-bezier(.22,1,.36,1);
    }}
    .ov-tile-h {{ font-size: .82rem; font-weight: 700; color: var(--text-muted);
      margin-bottom: 16px; display: flex; align-items: center; gap: 7px; }}

    /* Hero — espresso drenched, ทำหน้าที่เป็น warmth anchor ทุกธีม */
    .ov-hero {{
      grid-row: span 1; border: none; color: var(--ov-crema);
      min-height: 248px; display: flex; flex-direction: column; gap: 18px;
      background:
        radial-gradient(130% 120% at 88% -10%, rgba(224,162,86,.34) 0%, rgba(224,162,86,0) 45%),
        linear-gradient(152deg, var(--ov-espresso-2) 0%, var(--ov-espresso-1) 72%);
      box-shadow: 0 18px 40px -18px rgba(36,19,7,.7);
    }}
    .ov-hero::after {{
      content: ""; position: absolute; inset: 0; pointer-events: none; opacity: .5;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.05'/%3E%3C/svg%3E");
      mix-blend-mode: overlay;
    }}
    .ov-hero > * {{ position: relative; z-index: 1; }}
    .ov-hero-top {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; }}
    .ov-hero-label {{ font-size: .82rem; font-weight: 600; color: var(--ov-caramel);
      letter-spacing: .01em; }}
    .ov-hero-chip {{ display: inline-flex; align-items: center; gap: 6px; text-decoration: none;
      font-size: .72rem; font-weight: 600; color: var(--ov-crema);
      background: rgba(246,236,218,.12); border: 1px solid rgba(246,236,218,.2);
      padding: 4px 11px; border-radius: 999px; transition: background .2s; }}
    .ov-hero-chip:hover {{ background: rgba(246,236,218,.22); }}
    .ov-hero-num {{ font-size: clamp(2.8rem, 2rem + 4vw, 4.4rem); font-weight: 900;
      line-height: .95; letter-spacing: -0.03em; font-variant-numeric: tabular-nums;
      color: var(--ov-crema); }}
    .ov-hero-sub {{ font-size: .9rem; color: rgba(246,236,218,.72); margin-top: 6px; }}
    .ov-contrib {{ display: flex; height: 12px; border-radius: 999px; overflow: hidden;
      background: rgba(246,236,218,.1); margin-top: auto; }}
    .ov-contrib-seg {{ height: 100%; width: 0; transition: width 1.1s cubic-bezier(.22,1,.36,1); }}
    .ov-contrib-legend {{ display: flex; flex-wrap: wrap; gap: 14px; font-size: .76rem;
      color: rgba(246,236,218,.82); }}
    .ov-contrib-legend .lg {{ display: inline-flex; align-items: center; gap: 6px; }}
    .ov-contrib-legend .dot {{ width: 9px; height: 9px; border-radius: 999px; }}

    /* Share donut tile */
    .ov-share-wrap {{ position: relative; height: 168px; }}
    .ov-share-center {{ position: absolute; inset: 0; display: flex; flex-direction: column;
      align-items: center; justify-content: center; pointer-events: none; }}
    .ov-share-center .v {{ font-size: 1.5rem; font-weight: 900; color: var(--text); line-height: 1; }}
    .ov-share-center .l {{ font-size: .68rem; color: var(--text-muted); margin-top: 2px; }}
    .ov-share-legend {{ display: flex; flex-direction: column; gap: 8px; margin-top: 14px; }}
    .ov-share-legend .row {{ display: flex; align-items: center; justify-content: space-between;
      gap: 8px; font-size: .8rem; }}
    .ov-share-legend .row .nm {{ display: inline-flex; align-items: center; gap: 7px; color: var(--text-muted); }}
    .ov-share-legend .row .pc {{ font-weight: 800; font-variant-numeric: tabular-nums; }}

    /* Platform tiles */
    .ov-plat {{ cursor: pointer; }}
    .ov-plat:hover {{ transform: translateY(-4px); box-shadow: 0 20px 36px -22px rgba(0,0,0,.45); }}
    .ov-plat-top {{ display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 14px; }}
    .ov-plat-name {{ display: inline-flex; align-items: center; gap: 9px; font-weight: 700;
      font-size: .95rem; color: var(--text); }}
    .ov-plat-dot {{ width: 11px; height: 11px; border-radius: 999px; flex-shrink: 0; }}
    .ov-plat-er {{ font-size: .72rem; font-weight: 700; padding: 3px 9px; border-radius: 999px;
      font-variant-numeric: tabular-nums; }}
    .ov-plat-num {{ font-size: 2rem; font-weight: 900; letter-spacing: -0.02em; line-height: 1;
      color: var(--text); font-variant-numeric: tabular-nums; }}
    .ov-plat-numl {{ font-size: .72rem; color: var(--text-muted); margin-top: 3px; }}
    .ov-spark {{ width: 100%; height: 42px; margin-top: 14px; display: block; }}
    .ov-spark path.line {{ fill: none; stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; }}

    /* Showdown */
    .ov-showdown-tabs {{ display: flex; flex-wrap: wrap; gap: 7px; margin-bottom: 18px; }}
    .ov-mtab {{ cursor: pointer; padding: 5px 13px; border-radius: 999px; font-size: .76rem;
      font-weight: 600; border: 1px solid var(--card-border); background: transparent;
      color: var(--text-muted); transition: all .18s; }}
    .ov-mtab.active {{ box-shadow: 0 0 0 2px #f6ecda, 0 0 0 4px #75410a, 0 3px 10px rgba(70,37,6,.35);
      transform: translateY(-1px); font-weight: 800; }}
    .ov-mtab:hover:not(.active) {{ filter: brightness(1.06); }}
    .ov-bars {{ display: flex; flex-direction: column; gap: 16px; }}
    .ov-bar-row {{ display: grid; grid-template-columns: 96px 1fr auto; align-items: center; gap: 14px; }}
    .ov-bar-name {{ display: inline-flex; align-items: center; gap: 8px; font-weight: 600;
      font-size: .85rem; color: var(--text); }}
    .ov-bar-track {{ height: 30px; border-radius: 9px; background: var(--nav-active); overflow: hidden; }}
    .ov-bar-fill {{ height: 100%; width: 0; border-radius: 9px;
      transition: width 1s cubic-bezier(.22,1,.36,1); }}
    .ov-bar-val {{ font-weight: 800; font-size: .9rem; font-variant-numeric: tabular-nums;
      color: var(--text); min-width: 72px; text-align: right; }}
    .ov-rank {{ display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px;
      border-radius: 999px; font-size: .68rem; font-weight: 800; flex-shrink: 0; }}

    /* Entrance — เล่นครั้งเดียวตอนโหลด (ผ่านคลาส .ov-play) */
    .ov-anim {{ opacity: 1; }}
    #view-home.ov-play .ov-anim {{ animation: ovUp .62s cubic-bezier(.22,1,.36,1) both;
      animation-delay: calc(var(--d, 0) * 75ms); }}
    @keyframes ovUp {{ from {{ opacity: 0; transform: translateY(16px) scale(.99); }}
      to {{ opacity: 1; transform: none; }} }}
    @keyframes ovDraw {{ to {{ stroke-dashoffset: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{
      #view-home.ov-play .ov-anim {{ animation: none; }}
      .ov-tile, .ov-contrib-seg, .ov-bar-fill, .ov-plat {{ transition: none; }}
    }}
    .ov-plat:active {{ transform: translateY(-1px); }}

    /* ── Focus visibility (a11y) — ใช้ทั้งแอป ── */
    :focus-visible {{ outline: 2px solid var(--ov-caramel); outline-offset: 2px; }}
    .ov-hero :focus-visible {{ outline-color: var(--ov-crema); }}
    .ov-plat:focus-visible {{ outline: 2px solid var(--ov-caramel); outline-offset: 3px; }}

    /* ── Touch targets ขั้นต่ำ 44px บนอุปกรณ์สัมผัส ── */
    @media (pointer: coarse) {{
      .ov-mtab, .intel-tab, .pricing-tab {{
        min-height: 44px; display: inline-flex; align-items: center; justify-content: center;
      }}
      .ov-hero-chip {{ min-height: 38px; }}
    }}

    /* ── Premium card surface ทั่วทั้งแอป (ให้ทุกหน้าเป็นชุดเดียวกับ Overview) ── */
    .bg-white.rounded-2xl {{ border-radius: 20px; }}
    .bg-white.shadow-sm {{ box-shadow: 0 12px 30px -22px rgba(60,40,20,.42); }}
    [data-theme="dark"]   {{ --ov-accent-ink: #e0a256; }}
    [data-theme="fancy"]  {{ --ov-accent-ink: #f0b878; }}
    [data-theme="coffee"] {{ --ov-accent-ink: #e8b06a; }}

    /* ── Coming soon (Backbar) ── */
    .ov-soon {{ display: flex; flex-direction: column; align-items: center; justify-content: center;
      text-align: center; padding: 64px 24px; min-height: 340px; }}
    .ov-soon-emoji {{ font-size: 3.2rem; margin-bottom: 16px; line-height: 1; }}
    .ov-soon-title {{ font-size: 1.55rem; font-weight: 900; color: var(--text); letter-spacing: -.02em; }}
    .ov-soon-sub {{ font-size: .9rem; color: var(--text-muted); margin-top: 8px; max-width: 38ch; }}
    .ov-soon-badge {{ display: inline-flex; align-items: center; gap: 8px; margin-top: 22px;
      padding: 7px 16px; border-radius: 999px; background: var(--ov-espresso-2); color: var(--ov-crema);
      font-size: .78rem; font-weight: 700; }}
    .ov-soon-dot {{ width: 8px; height: 8px; border-radius: 999px; background: var(--ov-caramel);
      animation: ovPulse 1.6s ease-in-out infinite; }}
    @keyframes ovPulse {{ 0%,100% {{ opacity: 1; transform: scale(1); }} 50% {{ opacity: .35; transform: scale(.75); }} }}
    @media (prefers-reduced-motion: reduce) {{ .ov-soon-dot {{ animation: none; }} }}
    /* ── App logo (GIF วงกลม + ปุ่มกลับ overview) ── */
    .app-logo-img {{ border-radius:999px; object-fit:cover; flex-shrink:0; background:var(--card);
      border:2px solid var(--card-border); }}
    .app-logo-btn {{ display:flex; align-items:center; gap:10px; cursor:pointer; background:none; border:none;
      padding:0; text-align:left; border-radius:12px; transition:opacity .15s; }}
    .app-logo-btn:hover {{ opacity:.78; }}
    .ov-h1-row {{ display:flex; align-items:center; gap:16px; }}
    /* ── Backbar status bar ── */
    .bb-status-bar {{ display:flex; flex-wrap:wrap; align-items:center; gap:8px 14px; margin:10px 0 6px; font-size:.8rem; }}
    .bb-status-pill {{ display:inline-flex; align-items:center; gap:7px; padding:5px 12px; border-radius:999px; font-weight:800; border:1px solid var(--card-border); background:var(--card); }}
    .bb-status-pill .dot {{ width:8px; height:8px; border-radius:999px; }}
    .bb-status-pill.soon .dot {{ background:var(--ov-caramel); }}
    .bb-status-pill.live .dot {{ background:var(--dc-profit); }}
    .bb-status-meta {{ color:var(--text-muted); }}
    .bb-status-meta b {{ color:var(--text); font-weight:800; }}

    /* ── Backbar: สต็อกหลังบ้าน ── */
    @keyframes stkBeat {{ 0%,100%{{transform:scale(1)}} 14%{{transform:scale(1.04)}} 28%{{transform:scale(1)}} 42%{{transform:scale(1.03)}} 56%{{transform:scale(1)}} }}
    @keyframes stkAura {{ 0%,100%{{box-shadow:0 0 0 0 transparent}} 50%{{box-shadow:0 0 22px 5px var(--stk-glow,rgba(220,40,40,.55))}} }}
    @media (prefers-reduced-motion:reduce) {{ .stk-warn-card:not(.dismissed) {{ animation:none!important;outline:2px solid var(--stk-glow,rgba(220,40,40,.45));background:var(--stk-bg,rgba(220,40,40,.06)); }} }}
    .stk-warn-section {{ margin-bottom:20px; }}
    .stk-warn-row {{ display:flex; align-items:center; gap:10px; margin-bottom:10px; }}
    .stk-warn-row-title {{ font-size:.75rem; font-weight:800; color:var(--dc-warn); text-transform:uppercase; letter-spacing:.06em; }}
    .stk-ok-note {{ font-size:.82rem; color:var(--dc-profit); font-weight:700; padding:8px 14px;
      background:rgba(21,128,61,.06); border:1px solid rgba(21,128,61,.18); border-radius:12px; display:inline-block; }}
    .stk-warn-grid {{ display:flex; flex-wrap:wrap; gap:10px; }}
    .stk-warn-card {{ background:var(--card); border:1.5px solid rgba(220,40,40,.28); border-radius:16px;
      padding:12px 14px 10px; display:flex; align-items:center; gap:12px; flex:1 1 140px; max-width:240px; }}
    .stk-warn-card.dismissed {{ border-color:var(--card-border)!important; opacity:.72; animation:none!important; box-shadow:none!important; }}
    .stk-thermo-wrap {{ display:flex; flex-direction:column; align-items:center; gap:4px; flex-shrink:0; }}
    .stk-thermo {{ width:18px; height:68px; border-radius:999px; background:var(--nav-active);
      border:1.5px solid rgba(0,0,0,.1); position:relative; overflow:hidden; }}
    .stk-thermo-fill {{ position:absolute; bottom:0; left:0; right:0; border-radius:999px;
      transition:height .6s cubic-bezier(.22,1,.36,1); }}
    .stk-thermo-pct {{ font-size:.68rem; font-weight:800; color:var(--text-muted); }}
    .stk-warn-info {{ flex:1; min-width:0; }}
    .stk-warn-name {{ font-weight:700; font-size:.85rem; color:var(--text); margin-bottom:2px;
      overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
    .stk-warn-qty {{ font-size:.75rem; color:var(--text-muted); margin-bottom:7px; }}
    .stk-warn-qty b {{ color:var(--text); }}
    .stk-warn-ack {{ font-size:.72rem; padding:4px 9px; border-radius:8px;
      border:1px solid var(--card-border); background:transparent; color:var(--text-muted);
      cursor:pointer; white-space:nowrap; }}
    .stk-warn-ack:hover {{ background:var(--nav-active); }}
    .stk-gtab-row {{ display:flex; flex-wrap:wrap; gap:6px; margin-bottom:12px; }}
    .stk-card {{ background:var(--card); border:1px solid var(--card-border); border-radius:14px;
      padding:12px 14px; display:flex; gap:12px; align-items:flex-start; margin-bottom:8px; }}
    .stk-card.low {{ border-color:rgba(194,65,12,.3); }}
    .stk-card-img {{ width:52px; height:52px; border-radius:10px; flex-shrink:0;
      background:var(--nav-active); display:flex; align-items:center; justify-content:center;
      font-size:1.4rem; overflow:hidden; }}
    .stk-card-img img {{ width:100%; height:100%; object-fit:cover; border-radius:10px; }}
    .stk-card-body {{ flex:1; min-width:0; }}
    .stk-top {{ display:flex; flex-wrap:wrap; align-items:center; gap:8px; margin-bottom:4px; }}
    .stk-name {{ font-weight:700; font-size:.92rem; color:var(--text); flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
    .stk-badge {{ display:inline-flex; align-items:center; padding:3px 10px; border-radius:999px;
      font-size:.72rem; font-weight:700; flex-shrink:0; }}
    .stk-badge.warn {{ background:rgba(194,65,12,.12); color:var(--dc-warn); }}
    .stk-badge.muted {{ background:var(--nav-active); color:var(--text-muted); }}
    .stk-nums {{ display:flex; flex-wrap:wrap; gap:3px 16px; font-size:.78rem; color:var(--text-muted); margin-bottom:8px; }}
    .stk-nums b {{ color:var(--text); }}
    .stk-bar-wrap {{ height:8px; border-radius:999px; background:var(--nav-active); overflow:hidden; margin-bottom:3px; }}
    .stk-bar-fill {{ height:100%; border-radius:999px; transition:width .6s cubic-bezier(.22,1,.36,1); }}
    .stk-bar-lbl {{ font-size:.74rem; font-weight:700; color:var(--text-muted); text-align:right; }}
    .stk-modal-group-label {{ font-size:.72rem; font-weight:800; color:var(--text-muted);
      text-transform:uppercase; letter-spacing:.06em; padding:10px 0 4px;
      margin-top:8px; border-top:1px solid var(--card-border); }}
    .stk-modal-group-label:first-child {{ border-top:none; margin-top:0; padding-top:0; }}
    .stk-sales-row {{ display:flex; align-items:center; gap:10px; padding:7px 0;
      border-bottom:1px solid var(--card-border); }}
    .stk-sales-row:last-child {{ border-bottom:none; }}
    .stk-sales-name {{ flex:1; font-size:.84rem; color:var(--text); min-width:0;
      overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
    .stk-sales-row .dc-inp {{ width:90px; flex-shrink:0; }}
    .stk-par-item {{ padding:10px 0; border-bottom:1px solid var(--card-border); }}
    .stk-par-item:last-child {{ border-bottom:none; }}
    .stk-par-head {{ display:flex; align-items:center; justify-content:space-between; gap:8px;
      margin-bottom:6px; flex-wrap:wrap; }}
    .stk-par-ingname {{ font-weight:700; font-size:.88rem; color:var(--text); flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
    .stk-par-fields {{ display:flex; flex-wrap:wrap; gap:6px 10px; align-items:flex-end; }}
    .stk-par-field {{ display:flex; flex-direction:column; gap:3px; }}
    .stk-par-field label {{ font-size:.7rem; color:var(--text-muted); font-weight:600; }}
    .stk-par-field .dc-inp {{ width:82px; }}
    .stk-par-field .url-inp {{ min-width:180px; width:100%; font-size:.78rem; }}
    .stk-par-bu {{ font-size:.72rem; color:var(--text-muted); padding:2px 6px;
      align-self:flex-end; margin-bottom:7px; }}
    .stk-preview {{ font-size:.8rem; color:var(--text-muted); padding:8px 12px;
      background:var(--nav-active); border-radius:10px; margin-top:8px; min-height:32px; }}
    .stk-preview b {{ color:var(--text); }}
    .stk-usage-ings {{ padding:4px 0; }}
    .stk-usage-ing {{ font-size:.78rem; color:var(--text-muted); padding:2px 0; }}
    .stk-usage-ing b {{ color:var(--text); }}
    .stk-hide {{ display:none!important; }}
    .stk-modal-tabs {{ display:flex; flex-wrap:wrap; gap:6px; padding:0 24px 12px;
      border-bottom:1px solid var(--card-border); flex-shrink:0; }}
    .stk-tab-badge {{ display:inline-block; min-width:16px; height:16px; padding:0 4px;
      border-radius:999px; background:var(--dc-profit); color:#fff; font-size:.62rem;
      font-weight:800; line-height:16px; text-align:center; margin-left:3px; vertical-align:middle; }}

    /* ── KPI tiles (Pricing) — โทนเดียวกัน ไม่ใช่สีรุ้ง ── */
    .ov-kpi {{ padding: 18px 20px; }}
    .ov-kpi-top {{ display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }}
    .ov-kpi-icon {{ font-size: 1.05rem; line-height: 1; }}
    .ov-kpi-label {{ font-size: .74rem; color: var(--text-muted); font-weight: 600; }}
    .ov-kpi-val {{ font-size: 2.1rem; font-weight: 900; line-height: 1; color: var(--text);
      font-variant-numeric: tabular-nums; letter-spacing: -.02em; }}
    .ov-kpi-val.accent {{ color: var(--ov-accent-ink); }}
    .ov-kpi-unit {{ font-size: .72rem; color: var(--text-muted); margin-top: 6px; }}

    /* ── ต้นทุนเครื่องดื่ม (Drink costs) ── */
    :root {{ --dc-cost: #c08a4a; --dc-profit: #2f9e6b; --dc-warn: #c2410c; }}
    [data-theme="dark"]   {{ --dc-cost: #b5793a; --dc-profit: #34b87e; --dc-warn: #fb923c; }}
    [data-theme="fancy"]  {{ --dc-cost: #d39a52; --dc-profit: #4cd6a0; --dc-warn: #fdba74; }}
    [data-theme="coffee"] {{ --dc-cost: #c89a5e; --dc-profit: #46c98c; --dc-warn: #f8a560; }}

    .dc-meta {{ display: flex; flex-wrap: wrap; align-items: center; gap: 8px 14px;
      font-size: .76rem; color: var(--text-muted); margin: -6px 0 22px; }}
    .dc-meta .src {{ display: inline-flex; align-items: center; gap: 6px; font-weight: 600; color: var(--text); }}
    .dc-meta .note {{ opacity: .9; }}

    /* ── view-cost-drinks: เลื่อนหน้าปกติ — chart ใหญ่อยู่บน, รายการไหลต่อด้านล่าง ── */
    #dc-root {{ display: block; }}
    .dc-sticky-header {{ padding: 2px 0 8px; margin-bottom: 6px;
      border-bottom: 1px solid var(--card-border); }}
    /* Polar chart: square, responsive, centered — ใหญ่สมส่วนทั้ง PC/มือถือ */
    .dc-polar-wrap {{ margin-bottom: 8px; }}
    .dc-polar-canvas-wrap {{ position: relative;
      width: clamp(240px, min(92vw, 62vh), 820px);
      aspect-ratio: 1 / 1; margin: 0 auto; }}
    @media (max-height: 560px) {{
      .dc-polar-canvas-wrap {{ width: clamp(200px, min(80vw, 70vh), 520px); }}
    }}
    .dc-polar-caption {{ text-align: center; font-size: .72rem; color: var(--text-muted);
      margin: 3px 0 0; line-height: 1.4; }}
    /* 5 สถิติเต็มความกว้าง 1 แถว */
    .dc-stats-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; }}
    .dc-stats-row .dc-stat {{ flex: 1 1 100px; min-width: 0; }}
    .dc-stat {{ background: var(--card); border: 1px solid var(--card-border); border-radius: 14px;
      padding: 10px 13px; display: flex; flex-direction: column; gap: 4px; overflow: hidden; }}
    .dc-st-lab {{ font-size: .68rem; color: var(--text-muted); font-weight: 600; white-space: nowrap;
      overflow: hidden; text-overflow: ellipsis; }}
    .dc-st-val {{ font-size: 1.45rem; font-weight: 900; color: var(--text); line-height: 1;
      font-variant-numeric: tabular-nums; letter-spacing: -.02em; }}
    .dc-st-val small {{ font-size: .8rem; font-weight: 700; color: var(--text-muted); }}
    .dc-st-sub {{ font-size: .67rem; color: var(--text-muted); white-space: nowrap;
      overflow: hidden; text-overflow: ellipsis; }}
    .dc-stat.hero {{ background: linear-gradient(152deg, var(--ov-espresso-2), var(--ov-espresso-1) 80%);
      border: none; }}
    .dc-stat.hero .dc-st-lab, .dc-stat.hero .dc-st-sub {{ color: rgba(246,236,218,.78); }}
    .dc-stat.hero .dc-st-val {{ color: var(--ov-crema); }}
    /* รายการเมนู — ไหลในหน้า (เลื่อนด้วย scroll หลัก ขึ้นบนสุดได้เสมอ) */
    .dc-list-scroll {{ padding: 0 2px 8px; }}
    @media (max-width: 720px) {{
      .dc-stats-row .dc-stat {{ flex: 1 1 80px; }}
    }}
    @media (max-width: 500px) {{
      .dc-stats-row .dc-stat {{ flex: 1 1 58px; padding: 6px 8px; gap: 2px; }}
      .dc-stats-row .dc-st-val {{ font-size: 1.15rem; }}
      .dc-controls {{ gap: 5px 12px; margin-bottom: 8px; }}
      .dc-controls .ov-mtab {{ padding: 3px 8px; font-size: .72rem; }}
      .dc-controls .grp > .lbl {{ font-size: .72rem; }}
    }}

    .dc-controls {{ display: flex; flex-wrap: wrap; align-items: center; gap: 10px 18px;
      margin-bottom: 18px; }}
    .dc-controls .grp {{ display: inline-flex; align-items: center; gap: 7px; }}
    .dc-controls .grp > .lbl {{ font-size: .74rem; color: var(--text-muted); font-weight: 600; }}

    .dc-group-title {{ display: flex; align-items: center; gap: 9px; font-size: .82rem;
      font-weight: 800; color: var(--text); margin: 26px 0 12px; letter-spacing: .01em;
      cursor: pointer; user-select: none; }}
    .dc-group-title:hover {{ color: var(--ov-accent-ink); }}
    .dc-group-title:focus-visible {{ outline: 2px solid var(--ov-caramel); outline-offset: 3px; border-radius: 6px; }}
    .dc-group-title .ct {{ font-size: .72rem; font-weight: 700; color: var(--text-muted); }}
    .dc-chev {{ display: inline-flex; font-size: .66rem; color: var(--text-muted); transition: transform .2s ease; }}
    .dc-group-title.dc-collapsed .dc-chev {{ transform: rotate(-90deg); }}
    .dc-group-body.dc-collapsed {{ display: none; }}
    @media (prefers-reduced-motion: reduce) {{ .dc-chev {{ transition: none; }} }}

    .dc-list {{ display: flex; flex-direction: column; gap: 10px; }}
    .dc-row {{ background: var(--card); border: 1px solid var(--card-border); border-radius: 16px;
      padding: 15px 18px; cursor: pointer; transition: border-color .18s, box-shadow .18s, transform .18s; }}
    .dc-row:hover {{ border-color: var(--ov-caramel); box-shadow: 0 14px 30px -24px rgba(60,40,20,.5); }}
    .dc-row:focus-visible {{ outline: 2px solid var(--ov-caramel); outline-offset: 2px; }}
    .dc-row-top {{ display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1.45fr) auto;
      align-items: center; gap: 16px; }}
    @media (max-width: 720px) {{ .dc-row-top {{ grid-template-columns: 1fr; gap: 12px; }} }}

    .dc-id {{ display: flex; align-items: center; gap: 10px; min-width: 0; }}
    .dc-rank {{ flex-shrink: 0; width: 20px; text-align: center; font-size: .72rem; font-weight: 800;
      color: var(--text-muted); font-variant-numeric: tabular-nums; }}
    .dc-name {{ font-weight: 700; font-size: .92rem; color: var(--text); line-height: 1.3;
      display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
      word-break: break-word; }}
    .dc-norec {{ font-size: .68rem; color: var(--text-muted); font-weight: 500; }}
    .dc-thumb {{ position: relative; flex-shrink: 0; width: 42px; height: 42px; border-radius: 50%;
      overflow: hidden; display: inline-flex; align-items: center; justify-content: center;
      background: var(--nav-active); border: 1px solid var(--card-border); }}
    .dc-thumb-fb {{ position: absolute; font-size: 1.15rem; line-height: 1; }}
    .dc-thumb img {{ position: relative; width: 100%; height: 100%; object-fit: cover; display: block; }}
    .dc-addcat {{ margin-left: 10px; cursor: pointer; font-size: .7rem; font-weight: 700;
      padding: 3px 11px; border-radius: 999px; border: 1px dashed var(--card-border);
      background: transparent; color: var(--text-muted); }}
    .dc-addcat:hover {{ background: var(--nav-active); color: var(--text); }}
    .dc-empty-cat {{ font-size: .8rem; color: var(--text-muted); padding: 8px 4px 6px; }}

    /* แถบ ต้นทุน → กำไร (สเกลตามราคาขายสูงสุดในกลุ่ม) */
    .dc-barwrap {{ min-width: 0; }}
    .dc-bar {{ display: flex; height: 26px; border-radius: 8px; overflow: hidden;
      background: var(--nav-active); }}
    .dc-seg-cost {{ height: 100%; width: 0; background: var(--dc-cost);
      transition: width .9s cubic-bezier(.22,1,.36,1); }}
    .dc-seg-profit {{ height: 100%; width: 0; background: var(--dc-profit);
      transition: width .9s cubic-bezier(.22,1,.36,1); }}
    .dc-barlabels {{ display: flex; justify-content: space-between; gap: 8px; margin-top: 6px;
      font-size: .7rem; color: var(--text-muted); }}
    .dc-barlabels b {{ color: var(--text); font-weight: 700; }}

    .dc-figs {{ text-align: right; min-width: 96px; }}
    .dc-margin {{ font-size: 1.5rem; font-weight: 900; line-height: 1; font-variant-numeric: tabular-nums;
      letter-spacing: -.02em; }}
    .dc-margin small {{ font-size: .8rem; font-weight: 800; }}
    .dc-profitline {{ font-size: .76rem; color: var(--text-muted); margin-top: 4px; }}
    .dc-profitline b {{ color: var(--dc-profit); font-weight: 800; }}

    /* รายละเอียดเมื่อกดเปิด */
    .dc-detail {{ display: none; margin-top: 15px; padding-top: 15px;
      border-top: 1px dashed var(--card-border); }}
    .dc-row.open .dc-detail {{ display: block; }}
    .dc-row.open {{ border-color: var(--ov-caramel); }}
    .dc-detail-grid {{ display: grid; grid-template-columns: 1.4fr 1fr; gap: 22px; }}
    @media (max-width: 720px) {{ .dc-detail-grid {{ grid-template-columns: 1fr; gap: 16px; }} }}
    .dc-sub {{ font-size: .74rem; font-weight: 700; color: var(--text-muted); margin-bottom: 11px;
      display: flex; align-items: center; gap: 7px; }}
    .dc-ing {{ display: grid; grid-template-columns: 1fr 56px; align-items: center; gap: 10px;
      margin-bottom: 9px; }}
    .dc-ing-nm {{ font-size: .8rem; color: var(--text); display: flex; align-items: baseline; gap: 8px; }}
    .dc-ing-nm .pc {{ font-size: .72rem; color: var(--text-muted); font-variant-numeric: tabular-nums; }}
    .dc-ing-track {{ grid-column: 1 / -1; height: 7px; border-radius: 999px; background: var(--nav-active);
      overflow: hidden; margin-top: -3px; }}
    .dc-ing-fill {{ height: 100%; width: 0; border-radius: 999px; background: var(--dc-cost);
      transition: width .8s cubic-bezier(.22,1,.36,1); }}
    .dc-ing-cost {{ text-align: right; font-size: .78rem; font-weight: 700; color: var(--text);
      font-variant-numeric: tabular-nums; }}
    .dc-ingfoot {{ font-size: .73rem; color: var(--text-muted); margin-top: 10px; padding-top: 10px;
      border-top: 1px solid var(--card-border); line-height: 1.5; }}
    .dc-ingfoot b {{ color: var(--text); font-weight: 700; }}
    .dc-be {{ background: var(--nav-active); border-radius: 14px; padding: 16px 18px; }}
    .dc-be .big {{ font-size: 1.7rem; font-weight: 900; color: var(--text); line-height: 1;
      font-variant-numeric: tabular-nums; }}
    .dc-be .big small {{ font-size: .85rem; font-weight: 700; color: var(--text-muted); }}
    .dc-be .cap {{ font-size: .74rem; color: var(--text-muted); margin-top: 7px; line-height: 1.5; }}
    .dc-chrow {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}
    .dc-chip {{ font-size: .72rem; padding: 4px 11px; border-radius: 999px; background: var(--nav-active);
      color: var(--text); display: inline-flex; align-items: center; gap: 6px;
      border: 1px solid var(--card-border); }}
    .dc-chip .ch-price {{ font-weight: 800; color: var(--ov-accent-ink); }}
    @media (prefers-reduced-motion: reduce) {{
      .dc-seg-cost, .dc-seg-profit, .dc-ing-fill, .dc-row {{ transition: none; }}
    }}

    /* ── ตัวแก้ไขเมนู/สูตร (editor) ── */
    .dc-toolbar {{ display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
      margin-bottom: 16px; }}
    .dc-btn {{ display: inline-flex; align-items: center; gap: 6px; cursor: pointer;
      font-size: .8rem; font-weight: 700; padding: 8px 14px; border-radius: 10px;
      border: 1px solid rgba(70,37,6,.2);
      background: linear-gradient(180deg,#ecdcab,#cfc196); color: #3a2410;
      transition: filter .15s, background .15s, transform .1s; }}
    .dc-btn:hover {{ filter: brightness(1.06); }}
    .dc-btn:active {{ transform: translateY(1px); }}
    .dc-btn.primary {{ background: linear-gradient(180deg,#75410a,#462506); border-color: rgba(70,37,6,.35); color: #f6ecda; }}
    .dc-btn.primary:hover {{ filter: brightness(1.14); }}
    .dc-btn.ghost {{ background: transparent; border-color: transparent; color: var(--text-muted); }}
    .dc-btn.ghost:hover {{ filter: none; background: var(--nav-active); color: var(--text); }}
    .dc-btn.danger {{ color: var(--dc-warn); border-color: rgba(194,65,12,.35); }}
    .dc-btn:focus-visible {{ outline: 2px solid var(--ov-caramel); outline-offset: 2px; }}
    .dc-edithint {{ font-size: .74rem; color: var(--text-muted); }}
    .dc-note {{ background: var(--nav-active); border: 1px solid var(--card-border); border-radius: 14px;
      padding: 13px 16px; margin-bottom: 18px; font-size: .82rem; color: var(--text); line-height: 1.6; }}
    .dc-note-h {{ font-weight: 800; margin-bottom: 3px; }}
    .dc-note b {{ color: var(--ov-accent-ink); font-weight: 700; }}
    .dc-note-sub {{ font-size: .76rem; color: var(--text-muted); margin-top: 5px; }}
    .dc-note-sub b {{ color: var(--text); }}
    .dc-rowacts {{ display: inline-flex; gap: 6px; margin-left: 10px; }}
    .dc-iconbtn {{ width: 30px; height: 30px; border-radius: 8px; display: inline-flex;
      align-items: center; justify-content: center; cursor: pointer; font-size: .85rem;
      border: 1px solid var(--card-border); background: var(--card); color: var(--text); }}
    .dc-iconbtn:hover {{ background: var(--nav-active); }}

    .dc-modal-bd {{ position: fixed; inset: 0; z-index: 200; background: rgba(20,12,4,.55);
      display: flex; align-items: flex-start; justify-content: center; padding: 28px 16px;
      overflow-y: auto; backdrop-filter: blur(2px); }}
    .dc-modal {{ background: var(--card); border: 1px solid var(--card-border); border-radius: 20px;
      width: 100%; max-width: 720px; box-shadow: 0 40px 90px -30px rgba(0,0,0,.6);
      animation: dcPop .26s cubic-bezier(.22,1,.36,1) both;
      display: flex; flex-direction: column; max-height: calc(100vh - 40px); overflow: hidden; }}
    .dc-modal-bd {{ align-items: flex-start; padding: 20px 16px; overflow: hidden; }}
    .dc-modal-scroll {{ flex: 1 1 auto; min-height: 0; overflow-y: auto; overscroll-behavior: contain;
      -webkit-overflow-scrolling: touch; padding: 6px 24px; }}
    @keyframes dcPop {{ from {{ opacity: 0; transform: translateY(14px) scale(.98); }} to {{ opacity: 1; transform: none; }} }}
    @media (prefers-reduced-motion: reduce) {{ .dc-modal {{ animation: none; }} }}
    .dc-modal h3 {{ font-size: 1.2rem; font-weight: 900; color: var(--text); letter-spacing: -.02em; }}
    .dc-modal-head {{ display: flex; align-items: center; justify-content: space-between; gap: 12px;
      flex-shrink: 0; padding: 22px 24px 14px; }}
    .dc-x {{ cursor: pointer; font-size: 1.2rem; color: var(--text-muted); background: none; border: none;
      width: 34px; height: 34px; border-radius: 9px; }}
    .dc-x:hover {{ background: var(--nav-active); color: var(--text); }}

    .dc-field {{ margin-bottom: 14px; }}
    .dc-field > label {{ display: block; font-size: .76rem; font-weight: 700; color: var(--text-muted); margin-bottom: 6px; }}
    .dc-inp, .dc-sel {{ width: 100%; font-family: inherit; font-size: .9rem; color: var(--text);
      background: var(--nav-active); border: 1px solid var(--card-border); border-radius: 10px;
      padding: 9px 12px; }}
    .dc-inp:focus, .dc-sel:focus {{ outline: 2px solid var(--ov-caramel); outline-offset: 0; border-color: transparent; }}
    .dc-grid3 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; }}
    @media (max-width: 560px) {{ .dc-grid3 {{ grid-template-columns: repeat(2, 1fr); }} }}
    .dc-pricewrap {{ position: relative; }}
    .dc-auto {{ position: absolute; right: 6px; top: 50%; transform: translateY(-50%);
      font-size: .66rem; font-weight: 700; padding: 4px 8px; border-radius: 7px; cursor: pointer;
      border: none; background: var(--nav-active); color: var(--ov-accent-ink); }}

    .dc-rrow {{ display: grid; grid-template-columns: 1fr 84px 64px 34px; gap: 8px; align-items: center;
      margin-bottom: 8px; }}
    @media (max-width: 560px) {{ .dc-rrow {{ grid-template-columns: 1fr 70px 56px 32px; }} }}
    .dc-rcost {{ font-size: .8rem; font-weight: 700; color: var(--text); text-align: right;
      font-variant-numeric: tabular-nums; }}
    .dc-ac {{ position: relative; min-width: 0; }}
    .dc-ac-inp {{ width: 100%; }}
    #dc-acpanel {{ position: fixed; z-index: 210; background: var(--card); border: 1px solid var(--card-border);
      border-radius: 12px; box-shadow: 0 22px 55px -20px rgba(0,0,0,.5); overflow-y: auto;
      max-height: 380px; padding: 0; }}
    .dc-ac-tabs {{ position: sticky; top: 0; z-index: 1; background: var(--card); display: flex; flex-wrap: wrap;
      gap: 5px; padding: 9px 9px 8px; border-bottom: 1px solid var(--card-border); }}
    .dc-ac-tab {{ font-size: .7rem; font-weight: 700; padding: 4px 10px; border-radius: 999px; cursor: pointer;
      border: 1px solid var(--card-border); background: transparent; color: var(--text-muted); white-space: nowrap; }}
    .dc-ac-tab:hover {{ background: var(--nav-active); }}
    .dc-ac-tab.active {{ background: var(--ov-espresso-2); border-color: var(--ov-espresso-2); color: var(--ov-crema); }}
    .dc-ac-body {{ padding: 6px; }}
    .dc-ac-grp {{ background: var(--card); font-size: .64rem; font-weight: 800;
      color: var(--ov-accent-ink); letter-spacing: .06em; padding: 8px 10px 4px; }}
    .dc-ac-item {{ display: flex; align-items: center; justify-content: space-between; gap: 10px;
      padding: 8px 10px; border-radius: 8px; cursor: pointer; font-size: .85rem; color: var(--text); }}
    .dc-ac-item:hover, .dc-ac-item.active {{ background: var(--nav-active); }}
    .dc-ac-item .uc {{ font-size: .7rem; color: var(--text-muted); font-variant-numeric: tabular-nums; flex-shrink: 0; }}
    .dc-ac-empty {{ padding: 12px 10px; font-size: .8rem; color: var(--text-muted); }}
    .dc-rdel {{ cursor: pointer; border: none; background: none; color: var(--dc-warn); font-size: 1rem; }}
    .dc-preview {{ background: var(--nav-active); border-radius: 14px; padding: 14px 16px; margin: 16px 0;
      display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }}
    @media (max-width: 560px) {{ .dc-preview {{ grid-template-columns: repeat(2, 1fr); }} }}
    .dc-pv .l {{ font-size: .68rem; color: var(--text-muted); }}
    .dc-pv .v {{ font-size: 1.15rem; font-weight: 900; color: var(--text); font-variant-numeric: tabular-nums; }}
    .dc-modal-foot {{ display: flex; flex-wrap: wrap; gap: 10px; justify-content: flex-end;
      flex-shrink: 0; padding: 14px 24px; border-top: 1px solid var(--card-border); background: var(--card); }}
    .dc-modal-foot .spacer {{ margin-right: auto; }}

    .dc-cat-row {{ display: grid; grid-template-columns: 1.6fr 70px 80px 70px 32px; gap: 8px;
      align-items: center; margin-bottom: 7px; }}
    .dc-cat-row .uc {{ font-size: .76rem; color: var(--text-muted); text-align: right; font-variant-numeric: tabular-nums; }}
    .dc-cat-head {{ font-size: .68rem; font-weight: 700; color: var(--text-muted); }}
    .dc-cat-list {{ padding-right: 4px; margin-top: 8px; }}
    .dc-catfilter {{ position: sticky; top: 0; z-index: 2; background: var(--card); display: flex;
      flex-wrap: wrap; gap: 6px; padding: 2px 0 10px; margin-bottom: 2px; }}
    .dc-pwwrap {{ position: relative; }}
    .dc-pwwrap .dc-inp {{ padding-right: 44px; }}
    .dc-eye {{ position: absolute; right: 6px; top: 50%; transform: translateY(-50%); border: none;
      background: none; cursor: pointer; font-size: 1.1rem; line-height: 1; width: 34px; height: 34px;
      border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; }}
    .dc-eye:hover {{ background: var(--nav-active); }}
    .dc-pwerr {{ display: none; margin-top: 8px; font-size: .78rem; color: var(--dc-warn); font-weight: 700; }}
    .dc-pwerr.show {{ display: block; }}

    /* ── History / update-log timeline ── */
    .log-summary-grid {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px; margin-bottom: 24px;
    }}
    .log-card {{
      background: var(--card); border: 1px solid var(--card-border);
      border-radius: 16px; padding: 18px 20px;
    }}
    .log-card .lc-label {{ font-size: .72rem; text-transform: uppercase;
      letter-spacing: .08em; color: var(--text-muted); margin-bottom: 6px; }}
    .log-card .lc-count {{ font-size: 2rem; font-weight: 900; color: var(--text); line-height: 1; }}
    .log-card .lc-sub {{ font-size: .75rem; color: var(--text-muted); margin-top: 6px; }}
    .log-item {{
      display: flex; gap: 14px; padding: 14px 0;
      border-bottom: 1px solid var(--card-border);
    }}
    .log-item:last-child {{ border-bottom: none; }}
    .log-dot {{ flex-shrink: 0; width: 10px; height: 10px; border-radius: 9999px; margin-top: 6px; }}
    .log-dot.platform {{ background: #3b82f6; }}
    .log-dot.intel {{ background: #f59e0b; }}
    .log-cat {{
      display: inline-block; font-size: .68rem; font-weight: 700;
      padding: 2px 9px; border-radius: 9999px; margin-right: 8px;
    }}
    .log-cat.platform {{ background: #3b82f622; color: #2563eb; }}
    .log-cat.intel {{ background: #f59e0b22; color: #d97706; }}
    .log-detail {{ font-size: .78rem; color: var(--text-muted); margin-top: 3px; padding-left: 12px;
      border-left: 2px solid var(--card-border); }}

    /* ── ต้นทุนผันแปรและคงที่ (Varfix) ── */
    .vf-summary {{ margin-bottom:18px; }}
    .vf-summary-head {{ display:flex; align-items:baseline; gap:10px; flex-wrap:wrap; margin-bottom:8px; }}
    .vf-summary-title {{ font-size:.95rem; font-weight:900; color:var(--text); }}
    .vf-summary-sub {{ font-size:.78rem; color:var(--text-muted); }}
    .vf-bar-wrap {{ height:20px; border-radius:999px; background:var(--nav-active); overflow:hidden;
      display:flex; margin-bottom:10px; }}
    .vf-bar-seg {{ height:100%; transition:width .4s cubic-bezier(.22,1,.36,1); flex-shrink:0; }}
    .vf-legend {{ display:flex; flex-wrap:wrap; gap:5px 12px; }}
    .vf-legend-item {{ display:flex; align-items:center; gap:5px; font-size:.75rem; color:var(--text-muted); }}
    .vf-legend-dot {{ width:8px; height:8px; border-radius:999px; flex-shrink:0; }}
    .vf-legend-pct {{ font-weight:700; color:var(--text); }}
    .vf-bills {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,400px)); gap:14px; align-items:start; justify-content:start; }}
    .vf-receipt-card {{ background:var(--card); border:1px solid var(--card-border); border-radius:16px;
      overflow:hidden; }}
    .vf-receipt-head {{ padding:10px 14px; display:flex; align-items:center; gap:8px; flex-wrap:wrap;
      min-height:38px; border-radius:14px 14px 0 0; text-shadow:0 1px 3px rgba(0,0,0,.25); }}
    .vf-receipt-chip {{ background:rgba(255,255,255,.22); color:#fff; font-size:.72rem; font-weight:800;
      padding:3px 9px; border-radius:999px; white-space:nowrap; }}
    .vf-pay-badge {{ background:rgba(255,255,255,.22); color:#fff; font-size:.66rem; font-weight:700;
      padding:2px 7px; border-radius:999px; white-space:nowrap; }}
    .vf-receipt-group {{ font-size:.7rem; color:rgba(255,255,255,.82); margin-left:auto; white-space:nowrap; }}
    .vf-receipt-date  {{ font-size:.7rem; color:rgba(255,255,255,.88); font-weight:700; white-space:nowrap; }}
    .vf-receipt-body {{ padding:10px 14px 6px; font-feature-settings:"tnum"; }}
    .vf-receipt-label {{ font-weight:700; font-size:.88rem; color:var(--text); margin-bottom:4px;
      display:flex; align-items:center; flex-wrap:wrap; gap:4px; }}
    .vf-vendor {{ font-size:.75rem; color:var(--text-muted); margin-bottom:5px; }}
    .vf-readonly-badge {{ font-size:.64rem; color:var(--text-muted); background:var(--nav-active);
      border-radius:6px; padding:2px 7px; font-weight:600; }}
    .vf-line-table {{ width:100%; border-collapse:collapse; font-size:.78rem; margin:4px 0 4px; }}
    .vf-line-table td {{ padding:3px 4px 3px 0; color:var(--text-muted); vertical-align:top; }}
    .vf-line-table td:last-child {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
    .vf-line-table tr:not(:last-child) td {{ border-bottom:1px dashed var(--card-border); }}
    .vf-receipt-note {{ font-size:.75rem; color:var(--text-muted); margin:4px 0; }}
    .vf-receipt-foot {{ padding:6px 14px 12px; border-top:1px dashed var(--card-border); margin-top:4px;
      display:flex; align-items:center; justify-content:space-between; }}
    .vf-receipt-total {{ font-size:1.15rem; font-weight:900; color:var(--text); font-variant-numeric:tabular-nums; }}
    .vf-slip-btn {{ font-size:.72rem!important; padding:4px 10px!important; }}
    .vf-slip-thumb {{ width:60px; height:45px; object-fit:cover; border-radius:6px; cursor:pointer; margin-right:6px; border:1px solid var(--card-border); vertical-align:middle; }}
    /* ── varfix history card ── */
    .vf-history-card {{ background:var(--card); border:1px solid var(--card-border); border-radius:16px; margin-top:22px; margin-bottom:22px; overflow:hidden; }}
    .vf-history-hdr {{ display:flex; align-items:center; justify-content:space-between; padding:12px 16px; cursor:pointer; user-select:none; font-weight:700; font-size:.9rem; color:var(--text); }}
    .vf-history-hdr:hover {{ background:var(--nav-hover); }}
    .vf-history-body {{ padding:16px; }}
    .vf-cmp-toolbar {{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:12px; font-size:.82rem; color:var(--text-muted); }}
    .vf-cmp-sel {{ background:var(--card); border:1px solid var(--card-border); color:var(--text); border-radius:8px; padding:5px 10px; font-size:.82rem; cursor:pointer; }}
    .vf-cmp-wrap {{ overflow-x:auto; -webkit-overflow-scrolling:touch; }}
    .vf-cmp-tbl {{ width:100%; border-collapse:collapse; font-size:.8rem; min-width:360px; }}
    .vf-cmp-tbl th {{ text-align:right; padding:6px 8px; color:var(--text-muted); font-weight:700; border-bottom:2px solid var(--card-border); white-space:nowrap; }}
    .vf-cmp-tbl th:first-child {{ text-align:left; }}
    .vf-cmp-tbl td {{ text-align:right; padding:5px 8px; border-bottom:1px solid var(--card-border); font-variant-numeric:tabular-nums; white-space:nowrap; }}
    .vf-cmp-tbl td:first-child {{ text-align:left; color:var(--text); }}
    .vf-cmp-tbl tfoot td {{ font-weight:800; background:var(--nav-active); border-bottom:none; padding:7px 8px; }}
    .vf-diff-up {{ color:#ef4444; font-weight:700; }}
    .vf-diff-dn {{ color:#22c55e; font-weight:700; }}
    .vf-diff-nu {{ color:var(--text-muted); }}
    .vf-trend-wrap {{ margin-top:20px; }}
    .vf-trend-title {{ font-size:.82rem; font-weight:700; color:var(--text-muted); margin-bottom:10px; }}
    .vf-trend-canvas-wrap {{ position:relative; height:200px; }}
    .vf-history-empty {{ color:var(--text-muted); font-size:.82rem; text-align:center; padding:20px 0; }}
    /* ── POS Import ── */
    .pos-card-row {{ display:flex; gap:12px; flex-wrap:wrap; margin:12px 0; }}
    .pos-card {{ flex:1; min-width:140px; background:var(--tile-bg); border-radius:12px; padding:14px 16px; border:1px solid var(--card-border); }}
    .pos-card.refund .pos-card-val {{ color:#ef4444; }}
    .pos-card.net .pos-card-val {{ color:#22c55e; }}
    .pos-card.net-neg .pos-card-val {{ color:#ef4444; }}
    .pos-card-label {{ font-size:.8rem; color:var(--text-muted); margin-bottom:4px; }}
    .pos-card-val {{ font-size:1.4rem; font-weight:800; }}
    .pos-card-sub {{ font-size:.75rem; color:var(--text-muted); margin-top:2px; }}
    .pos-section {{ margin:18px 0; }}
    .pos-section-title {{ font-size:1rem; font-weight:700; margin-bottom:10px; }}
    .pos-diag {{ background:var(--tile-bg); border-radius:12px; padding:16px; border:1px solid var(--card-border); }}
    .pos-diag-row {{ font-size:.875rem; margin-bottom:8px; line-height:1.6; }}
    .pos-cat-chip {{ display:inline-block; background:var(--nav-active); padding:2px 8px; border-radius:20px; font-size:.8rem; margin:2px; }}
    .pos-cat-chip.ok {{ background:rgba(34,197,94,.15); color:#16a34a; }}
    .pos-cat-chip.warn {{ background:rgba(245,158,11,.15); color:#b45309; }}
    .pos-best-row td {{ background:rgba(34,197,94,.06); }}
    .pos-custom-row {{ display:flex; gap:12px; flex-wrap:wrap; align-items:center; margin:8px 0; font-size:.875rem; }}
    .pos-custom-row label {{ display:flex; align-items:center; gap:6px; }}
    .pos-custom-row input[type=date] {{ border:1px solid var(--border); border-radius:8px; padding:4px 8px; background:var(--bg); color:var(--text); font-size:.875rem; }}
  </style>
</head>
<body style="font-family: 'Prompt', system-ui, sans-serif" class="text-slate-800">
<input type="file" id="vf-slip-file-input" accept="image/*" capture="environment" style="display:none" onchange="vfSlipFileSelected(this)">

<!-- Mobile top bar -->
<div id="mobile-topbar" class="items-center justify-between px-4 py-3">
  <button class="app-logo-btn" onclick="goHomeFresh()" aria-label="กลับหน้าภาพรวม">
    <img class="app-logo-img" src="assets/logo-anim.gif" alt="โลโก้" style="width:30px;height:30px">
    <div>
      <div class="text-sm font-black" style="color:var(--text)">Social Analytics</div>
      <div class="text-[10px]" style="color:var(--text-muted)">ร้านกาแฟ สกลนคร</div>
    </div>
  </button>
  <button onclick="openSidebar()" class="p-2 rounded-xl transition-colors"
    style="color:var(--text-muted);background:transparent" aria-label="เปิดเมนู">
    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
    </svg>
  </button>
</div>

<!-- Sidebar overlay -->
<div id="sidebar-overlay" onclick="closeSidebar()"></div>

<div class="flex h-screen overflow-hidden">

  <!-- Sidebar -->
  <aside id="sidebar" class="w-64 flex-shrink-0 bg-white border-r border-slate-200 flex flex-col">

    <!-- Logo -->
    <div class="p-5 border-b border-slate-100 flex items-center justify-between gap-2">
      <button class="app-logo-btn" onclick="goHomeFresh()" aria-label="กลับหน้าภาพรวม">
        <img class="app-logo-img" src="assets/logo-anim.gif" alt="โลโก้" style="width:40px;height:40px">
        <div>
          <div class="text-lg font-black leading-tight" style="color:var(--text)">Social Analytics</div>
          <div class="text-xs mt-0.5" style="color:var(--text-muted)">ร้านกาแฟ สกลนคร</div>
        </div>
      </button>
      <button onclick="event.stopPropagation(); closeSidebar();" id="sidebar-close-btn"
        class="p-1.5 rounded-lg hover:bg-slate-100 transition-colors text-slate-400"
        style="display:none;flex-shrink:0" aria-label="ปิดเมนู">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    </div>

    <!-- Nav -->
    <nav class="flex-1 p-4 space-y-1 overflow-y-auto">

      <button onclick="showView('view-home')" id="nav-home"
        class="nav-btn w-full text-left px-4 py-2.5 rounded-xl flex items-center gap-3
               text-slate-600 hover:bg-slate-50 transition-colors text-sm">
        <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
        </svg>
        ภาพรวม
      </button>

      <button onclick="showView('view-quest')" id="nav-quest"
        class="nav-btn w-full text-left px-4 py-2.5 rounded-xl flex items-center gap-3
               text-slate-600 hover:bg-slate-50 transition-colors text-sm">
        <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/>
        </svg>
        90 Days Quest
      </button>

      <div class="pt-2 pb-1">
        <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest px-4">Platforms</p>
      </div>

      {SIDEBAR_NAV_ITEMS}

      <div class="pt-2 pb-1">
        <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest px-4">Intelligence</p>
      </div>

      <button onclick="showView('view-intel')" id="nav-intel"
        class="nav-btn w-full text-left px-4 py-2.5 rounded-xl flex items-center gap-3
               text-slate-600 hover:bg-slate-50 transition-colors text-sm">
        <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
        </svg>
        ข่าวกรอง
      </button>

      <button onclick="showView('view-competitor-deep')" id="nav-competitor-deep"
        class="nav-btn w-full text-left px-4 py-2.5 rounded-xl flex items-center gap-3
               text-slate-600 hover:bg-slate-50 transition-colors text-sm">
        <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
        </svg>
        เชิงลึก
      </button>

      <button onclick="showView('view-tracker')" id="nav-tracker"
        class="nav-btn w-full text-left px-4 py-2.5 rounded-xl flex items-center gap-3
               text-slate-600 hover:bg-slate-50 transition-colors text-sm">
        <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
        </svg>
        ติดตามคู่แข่ง
      </button>

      <button onclick="showView('view-pricing')" id="nav-pricing"
        class="nav-btn w-full text-left px-4 py-2.5 rounded-xl flex items-center gap-3
               text-slate-600 hover:bg-slate-50 transition-colors text-sm">
        <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        ราคากลางร้านกาแฟ
      </button>

      <div class="pt-2 pb-1">
        <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest px-4">Backbar</p>
      </div>

      <button onclick="showView('view-bb-armory')" id="nav-bb-armory"
        class="nav-btn w-full text-left px-4 py-2.5 rounded-xl flex items-center gap-3
               text-slate-600 hover:bg-slate-50 transition-colors text-sm">
        <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
        </svg>
        คลังแสง
      </button>

      <button onclick="showView('view-bb-stock')" id="nav-bb-stock"
        class="nav-btn w-full text-left px-4 py-2.5 rounded-xl flex items-center gap-3
               text-slate-600 hover:bg-slate-50 transition-colors text-sm">
        <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
        </svg>
        สต็อกหลังบ้าน
      </button>

      <button onclick="showView('view-bb-varfix')" id="nav-bb-varfix"
        class="nav-btn w-full text-left px-4 py-2.5 rounded-xl flex items-center gap-3
               text-slate-600 hover:bg-slate-50 transition-colors text-sm">
        <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
        </svg>
        ต้นทุนผันแปรและคงที่
      </button>

      <button onclick="showView('view-cost-drinks')" id="nav-cost-drinks"
        class="nav-btn w-full text-left px-4 py-2.5 rounded-xl flex items-center gap-3
               text-slate-600 hover:bg-slate-50 transition-colors text-sm">
        <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M5 8h14M7 8l1 10a2 2 0 002 2h4a2 2 0 002-2l1-10M9 8V6a3 3 0 016 0v2"/>
        </svg>
        ต้นทุนเครื่องดื่ม
      </button>

      <button onclick="showView('view-pos-cost')" id="nav-pos-cost"
        class="nav-btn w-full text-left px-4 py-2.5 rounded-xl flex items-center gap-3
               text-slate-600 hover:bg-slate-50 transition-colors text-sm">
        <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 7h6m-6 4h6m-6 4h4M5 4h14a1 1 0 011 1v15l-3-2-2 2-2-2-2 2-2-2-3 2V5a1 1 0 011-1z"/>
        </svg>
        ตรวจสอบยอดขายจริง &amp; ทุนรวม
      </button>

      <button onclick="showView('view-bb-posimport')" id="nav-bb-posimport"
        class="nav-btn w-full text-left px-4 py-2.5 rounded-xl flex items-center gap-3
               text-slate-600 hover:bg-slate-50 transition-colors text-sm">
        <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
        </svg>
        บันทึกข้อมูลนำเข้า POS
      </button>

      <div class="pt-2 pb-1">
        <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest px-4">Tools</p>
      </div>

      <button onclick="requireImportAccess()" id="nav-import"
        class="nav-btn w-full text-left px-4 py-2.5 rounded-xl flex items-center gap-3
               text-slate-600 hover:bg-slate-50 transition-colors text-sm">
        <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
        </svg>
        นำเข้าข้อมูล
      </button>

      <button onclick="showView('view-updatelog')" id="nav-updatelog"
        class="nav-btn w-full text-left px-4 py-2.5 rounded-xl flex items-center gap-3
               text-slate-600 hover:bg-slate-50 transition-colors text-sm">
        <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        บันทึกอัปเดต
      </button>

    </nav>

    <!-- Footer: theme toggle + date -->
    <div class="p-4 border-t border-slate-100">
      <div id="sa-lock-wrap" style="display:none;margin-bottom:8px">
        <button id="sa-lock-chip" onclick="saLock()" style="width:100%;font-size:.68rem;padding:5px 10px;border-radius:8px;background:var(--nav-active);color:var(--text-muted);border:1px solid var(--card-border);cursor:pointer;text-align:left;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">🔓 ปลดล็อกแล้ว · กดเพื่อล็อก</button>
      </div>
      <div class="flex items-center justify-center gap-1 mb-2">
        <button class="theme-btn" id="theme-coffee" onclick="setTheme('coffee')" title="Coffee Mode">☕</button>
        <button class="theme-btn" id="theme-light" onclick="setTheme('light')"  title="Light Mode">☀️</button>
        <button class="theme-btn" id="theme-dark"  onclick="setTheme('dark')"   title="Dark Mode">🌙</button>
        <button class="theme-btn" id="theme-fancy" onclick="setTheme('fancy')"  title="Fancy Mode">✨</button>
      </div>
      <div class="text-[10px] text-slate-400 uppercase tracking-widest text-center">สร้างเมื่อ {GENERATED_AT}</div>
    </div>

  </aside>

  <!-- Main -->
  <main id="main-content" class="flex-1 overflow-y-auto bg-slate-100 p-8">

    <!-- ── Home View ── -->
    <div id="view-home" class="view">

      <div class="mb-6">
        <div class="ov-h1-row">
          <img class="app-logo-img" src="assets/overview-anim.gif" alt="" aria-hidden="true"
               style="width:60px;height:60px">
          <div>
            <h1 class="ov-h1" style="margin:0">ภาพรวม Social Media</h1>
            <p class="ov-sub-h" style="margin:0">ร้านกาแฟ สกลนคร · ภาพรวมผลงานทั้ง 3 แพลตฟอร์มในที่เดียว</p>
          </div>
        </div>
      </div>

      <!-- Row 1: Hero + Share donut -->
      <div class="ov-grid mb-4">
        <div class="ov-tile ov-hero ov-anim" style="--d:0">
          <div class="ov-hero-top">
            <span class="ov-hero-label">ยอดดูรวมทุกแพลตฟอร์ม</span>
            <a class="ov-hero-chip" href="#" onclick="showView('view-updatelog');return false;">🕐 <span id="ov-hero-upd">บันทึกอัปเดต</span></a>
          </div>
          <div>
            <div class="ov-hero-num"><span id="ov-total">0</span></div>
            <div class="ov-hero-sub" id="ov-hero-sub">ครั้งที่คนเห็นคอนเทนต์ของคุณ</div>
          </div>
          <div class="ov-contrib" id="ov-contrib"></div>
          <div class="ov-contrib-legend" id="ov-contrib-legend"></div>
        </div>

        <div class="ov-tile ov-anim" style="--d:1">
          <div class="ov-tile-h">🍩 สัดส่วนยอดดูแต่ละแพลตฟอร์ม</div>
          <div class="ov-share-wrap">
            <canvas id="ov-share-canvas"></canvas>
            <div class="ov-share-center">
              <span class="v" id="ov-share-top-v">—</span>
              <span class="l" id="ov-share-top-l">แพลตฟอร์มนำ</span>
            </div>
          </div>
          <div class="ov-share-legend" id="ov-share-legend"></div>
        </div>
      </div>

      <!-- Row 2: per-platform tiles (JS) -->
      <div class="ov-plats mb-4" id="ov-plats"></div>

      <!-- Row 3: head-to-head comparison -->
      <div class="ov-tile ov-anim" style="--d:5">
        <div class="ov-tile-h">⚔️ เทียบหมัดต่อหมัด · จัดอันดับ 3 แพลตฟอร์ม</div>
        <div class="ov-showdown-tabs" id="ov-showdown-tabs"></div>
        <div class="ov-bars" id="ov-showdown-bars"></div>
      </div>

    </div>

    <!-- ── Platform Views (injected) ── -->
    {PLATFORM_VIEWS}

    <!-- ── Intel View ── -->
    <div id="view-intel" class="view">
      <h1 class="text-3xl font-black text-slate-800 mb-4">ข่าวกรองตลาด</h1>

      <!-- Last-updated badge (Intelligence) -->
      <div id="intel-update-badge" class="update-badge mb-5"></div>

      <!-- Filter tabs -->
      <div class="flex flex-wrap gap-2 mb-5">
        <button class="intel-tab active" id="intel-tab-all"       onclick="setIntelTab('all')">ทั้งหมด</button>
        <button class="intel-tab"        id="intel-tab-competitor" onclick="setIntelTab('competitor')">☕ คู่แข่ง</button>
        <button class="intel-tab"        id="intel-tab-delivery"   onclick="setIntelTab('delivery')">🛵 Delivery</button>
        <button class="intel-tab"        id="intel-tab-coffee_knowledge" onclick="setIntelTab('coffee_knowledge')">💡 ความรู้</button>
        <button class="intel-tab"        id="intel-tab-news_events" onclick="setIntelTab('news_events')">📅 Events</button>
        <button class="intel-tab"        id="intel-tab-equipment"  onclick="setIntelTab('equipment')">⚙️ อุปกรณ์</button>
      </div>

      <!-- Accordion card grid -->
      <div id="intel-cards" class="space-y-2"></div>
    </div>

    <!-- ── Pricing View ── -->
    <div id="view-pricing" class="view">
      <div class="mb-6">
        <h1 class="ov-h1">ราคาเมนูกาแฟคู่แข่ง</h1>
        <p class="ov-sub-h">เทียบราคาแต่ละประเภทเมนูของร้านกาแฟใน จ.สกลนคร เพื่อวางราคาให้ได้เปรียบ</p>
      </div>

      <!-- KPI cards (4) -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6" id="pricing-kpi-cards"></div>

      <!-- Service tabs (6) -->
      <div class="flex flex-wrap gap-2 mb-4">
        <button class="pricing-tab active" id="pricing-tab-espresso"   onclick="setPricingTab('espresso')">☕ เอสเปรสโซ/อเมริกาโน</button>
        <button class="pricing-tab"        id="pricing-tab-latte"     onclick="setPricingTab('latte')">🥛 ลาเต้/คาปูชิโน</button>
        <button class="pricing-tab"        id="pricing-tab-cold_brew"  onclick="setPricingTab('cold_brew')">🧊 Cold Brew</button>
        <button class="pricing-tab"        id="pricing-tab-frappe"    onclick="setPricingTab('frappe')">🍦 Frappe/ปั่น</button>
        <button class="pricing-tab"        id="pricing-tab-signature"  onclick="setPricingTab('signature')">✨ Signature</button>
        <button class="pricing-tab"        id="pricing-tab-food"      onclick="setPricingTab('food')">🍰 อาหาร/เบเกอรี่</button>
      </div>

      <!-- Pricing table -->
      <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-6">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b-2 border-slate-200">
                <th class="px-4 py-3 text-left text-xs font-bold uppercase tracking-widest text-slate-500 whitespace-nowrap">ร้าน</th>
                <th class="px-4 py-3 text-right text-xs font-bold uppercase tracking-widest text-slate-500 whitespace-nowrap">ราคา (บาท)</th>
                <th class="px-4 py-3 text-left text-xs font-bold uppercase tracking-widest text-slate-500 whitespace-nowrap">หมายเหตุ</th>
              </tr>
            </thead>
            <tbody id="pricing-table-body"></tbody>
          </table>
        </div>
      </div>

      <!-- Social trend table -->
      <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
        <h2 class="text-sm font-bold text-slate-700 mb-4">📊 Social Trend — คู่แข่ง</h2>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b-2 border-slate-200">
                <th class="px-4 py-3 text-left text-xs font-bold uppercase tracking-widest text-slate-500 whitespace-nowrap">ร้าน</th>
                <th class="px-4 py-3 text-left text-xs font-bold uppercase tracking-widest text-slate-500 whitespace-nowrap">Platform หลัก</th>
                <th class="px-4 py-3 text-left text-xs font-bold uppercase tracking-widest text-slate-500 whitespace-nowrap">สไตล์ Content</th>
                <th class="px-4 py-3 text-left text-xs font-bold uppercase tracking-widest text-slate-500 whitespace-nowrap">Engagement</th>
              </tr>
            </thead>
            <tbody id="social-trend-body"></tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ── Competitor Deep View ── -->
    <div id="view-competitor-deep" class="view">
      <div class="mb-6">
        <h1 class="ov-h1">วิเคราะห์เชิงลึกคู่แข่ง</h1>
        <p class="ov-sub-h">6 มิติ: Social Presence · Content Strategy · Pricing · Services/Positioning · Reviews · Delivery</p>
      </div>

      <div class="flex flex-wrap gap-2 mb-6">
        <button class="intel-tab active" id="deep-tab-overview"  onclick="setDeepTab('overview')">📊 ภาพรวมการเปลี่ยนแปลง</button>
        <button class="intel-tab"        id="deep-tab-detail"    onclick="setDeepTab('detail')">☕ รายร้าน</button>
        <button class="intel-tab"        id="deep-tab-timeline"  onclick="setDeepTab('timeline')">📅 Timeline</button>
      </div>

      <div id="deep-content-overview"></div>
      <div id="deep-content-detail"   style="display:none"></div>
      <div id="deep-content-timeline" style="display:none"></div>
    </div>

    <!-- ── Tracker View ── -->
    <div id="view-tracker" class="view">

      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-3xl font-black mb-1" style="color:var(--text)">ติดตามคู่แข่ง</h1>
          <p class="text-sm" style="color:var(--text-muted)">เปรียบเทียบกิจกรรมคู่แข่งแต่ละช่วงเวลา</p>
        </div>
        <div class="flex gap-2" id="tracker-period-tabs">
          <button onclick="setTrackerPeriod('week')"  id="trk-week"  class="trk-tab px-4 py-2 rounded-xl text-sm font-semibold transition-all">สัปดาห์</button>
          <button onclick="setTrackerPeriod('month')" id="trk-month" class="trk-tab px-4 py-2 rounded-xl text-sm font-semibold transition-all">เดือน</button>
          <button onclick="setTrackerPeriod('year')"  id="trk-year"  class="trk-tab px-4 py-2 rounded-xl text-sm font-semibold transition-all">ปี</button>
        </div>
      </div>

      <div id="tracker-content"></div>

    </div>

    <!-- ── Import View ── -->
    <div id="view-import" class="view">

      <h1 class="text-3xl font-black text-slate-800 mb-6">นำเข้าข้อมูล</h1>

      <!-- Platform selector -->
      <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-6">
        <p class="text-sm font-semibold text-slate-700 mb-3">เลือก Platform</p>
        <div class="flex gap-3" id="platformBtns">
          <button onclick="selectPlatform('Facebook')"
            class="plat-btn px-5 py-2 rounded-xl border-2 text-sm font-semibold transition-all
                   border-slate-200 text-slate-600 hover:border-blue-400"
            style="--pc:#1877f2" id="plat-Facebook">Facebook</button>
          <button onclick="selectPlatform('Instagram')"
            class="plat-btn px-5 py-2 rounded-xl border-2 text-sm font-semibold transition-all
                   border-slate-200 text-slate-600 hover:border-pink-400"
            style="--pc:#e1306c" id="plat-Instagram">Instagram</button>
          <button onclick="selectPlatform('TikTok')"
            class="plat-btn px-5 py-2 rounded-xl border-2 text-sm font-semibold transition-all
                   border-slate-200 text-slate-600 hover:border-slate-900"
            style="--pc:#010101" id="plat-TikTok">TikTok</button>
        </div>
      </div>

      <!-- Drop zone -->
      <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-6">
        <div id="dropZone"
          class="drop-zone border-2 border-dashed border-slate-300 rounded-2xl p-12 text-center cursor-pointer"
          onclick="document.getElementById('fileInput').click()"
          ondragover="handleDragOver(event)"
          ondragleave="handleDragLeave(event)"
          ondrop="handleDrop(event)">
          <div class="text-4xl mb-3">📂</div>
          <p class="text-slate-600 font-semibold mb-1">ลากไฟล์มาวางที่นี่ หรือคลิกเพื่อเลือกไฟล์</p>
          <p class="text-xs text-slate-400">รองรับไฟล์ .csv จาก Facebook, Instagram, TikTok</p>
          <input type="file" id="fileInput" accept=".csv" multiple class="hidden"
            onchange="handleFileSelect(event)">
        </div>
      </div>

      <!-- Preview -->
      <div id="previewArea" class="hidden bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-6">
        <h2 class="text-sm font-bold text-slate-700 mb-4">ตัวอย่างข้อมูล (5 แถวแรก)</h2>
        <div id="previewTable" class="overflow-x-auto text-sm"></div>
        <button onclick="confirmImport()"
          class="mt-4 px-6 py-2.5 rounded-xl text-white text-sm font-semibold transition-colors"
          style="background:#10b981">
          ยืนยันการนำเข้า
        </button>
      </div>

    </div>

    <!-- ── Update Log / History View ── -->
    <div id="view-updatelog" class="view">
      <h1 class="text-3xl font-black text-slate-800 mb-1">บันทึกอัปเดต</h1>
      <p class="text-sm text-slate-500 mb-6">ประวัติการอัปเดตข้อมูลทั้งหมด — เมื่อไหร่ · กี่ครั้ง · อัปเดตอะไรไปบ้าง</p>

      <!-- Summary cards -->
      <div class="log-summary-grid" id="log-summary-cards"></div>

      <!-- Filter tabs -->
      <div class="flex flex-wrap gap-2 mb-5">
        <button class="intel-tab active" id="log-tab-all"      onclick="setLogTab('all')">ทั้งหมด</button>
        <button class="intel-tab"        id="log-tab-platform" onclick="setLogTab('platform')">📊 Platforms</button>
        <button class="intel-tab"        id="log-tab-intel"    onclick="setLogTab('intel')">🔍 Intelligence</button>
      </div>

      <!-- Timeline -->
      <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6" style="background:var(--card);border-color:var(--card-border)">
        <div id="log-timeline"></div>
      </div>
    </div>

    <!-- ── Backbar: ต้นทุนเครื่องดื่ม ── -->
    <div id="view-cost-drinks" class="view">
      <div class="mb-6">
        <div class="ov-h1-row">
          <img class="app-logo-img" src="assets/cost-anim.gif" alt="" aria-hidden="true"
               style="width:56px;height:56px">
          <div>
            <h1 class="ov-h1" style="margin:0">ต้นทุนเครื่องดื่ม</h1>
            <p class="ov-sub-h" style="margin:0">ต้นทุนต่อแก้ว กำไร และสัดส่วนวัตถุดิบของแต่ละเมนู — จากไฟล์ต้นทุนของร้าน</p>
          </div>
        </div>
        <div class="bb-status-bar">
          <span class="bb-status-pill live"><span class="dot"></span>🟢 ใช้งานอยู่</span>
          <span class="bb-status-meta">ใช้งานล่าสุด: <b>—</b></span>
          <span class="bb-status-meta">อัปเดตข้อมูลล่าสุด: <b id="bb-updated-cost">—</b></span>
        </div>
      </div>
      <div id="dc-root"></div>
    </div>

    <!-- ── Backbar: ตรวจสอบยอดขายจริง & ทุนรวม (Launching soon) ── -->
    <div id="view-pos-cost" class="view">
      <div class="mb-6">
        <h1 class="ov-h1">ตรวจสอบยอดขายจริง &amp; ทุนรวม</h1>
        <p class="ov-sub-h">ดึงข้อมูลจริงจาก POS วิเคราะห์ร่วมกับต้นทุนผันแปร&amp;คงที่ เพื่อดูอัตราคืนทุน/กำไร/ขาดทุน</p>
        <div class="bb-status-bar">
          <span class="bb-status-pill soon"><span class="dot"></span>🟡 เร็วๆ นี้</span>
          <span class="bb-status-meta">ใช้งานล่าสุด: <b>—</b></span>
          <span class="bb-status-meta">อัปเดตข้อมูลล่าสุด: <b>—</b></span>
        </div>
      </div>
      <div class="ov-tile ov-soon">
        <div class="ov-soon-emoji">🧾</div>
        <div class="ov-soon-title">Launching soon..</div>
        <div class="ov-soon-sub">ดึงข้อมูลจริงจาก POS วิเคราะห์ร่วมกับต้นทุนผันแปร&amp;คงที่ เพื่อดูอัตราคืนทุน/กำไร/ขาดทุน</div>
        <span class="ov-soon-badge"><span class="ov-soon-dot"></span>อยู่ระหว่างพัฒนา</span>
      </div>
    </div>

    <!-- ── Backbar: คลังแสง (Launching soon) ── -->
    <div id="view-bb-armory" class="view">
      <div class="mb-6">
        <h1 class="ov-h1">คลังแสง</h1>
        <p class="ov-sub-h">ศูนย์รวมข้อมูลทั้งหมดของ Backbar — สรุปรวมทุกหมวดให้เห็นผลลัพธ์ครอบคลุม พร้อม Insight เพื่อยกระดับและแก้จุดบกพร่องรอบด้าน</p>
        <div class="bb-status-bar">
          <span class="bb-status-pill soon"><span class="dot"></span>🟡 เร็วๆ นี้</span>
          <span class="bb-status-meta">ใช้งานล่าสุด: <b>—</b></span>
          <span class="bb-status-meta">อัปเดตข้อมูลล่าสุด: <b>—</b></span>
        </div>
      </div>
      <div class="ov-tile ov-soon">
        <div class="ov-soon-emoji">🏛️</div>
        <div class="ov-soon-title">Launching soon..</div>
        <div class="ov-soon-sub">ศูนย์รวมข้อมูลทั้งหมดของ Backbar — สรุปรวมทุกหมวดให้เห็นผลลัพธ์ครอบคลุม พร้อม Insight เพื่อยกระดับและแก้จุดบกพร่องรอบด้าน</div>
        <span class="ov-soon-badge"><span class="ov-soon-dot"></span>อยู่ระหว่างพัฒนา</span>
      </div>
    </div>

    <!-- ── Backbar: สต็อกหลังบ้าน (Launching soon) ── -->
    <div id="view-bb-stock" class="view">
      <div class="mb-6">
        <div class="ov-h1-row">
          <img class="app-logo-img" src="assets/stock-anim.gif" alt="" aria-hidden="true"
               style="width:56px;height:56px">
          <div>
            <h1 class="ov-h1" style="margin:0">สต็อกหลังบ้าน</h1>
            <p class="ov-sub-h" style="margin:0">วัตถุดิบคงเหลือ · ซื้อเข้า-ใช้จริง · เตือนเมื่อใกล้หมด</p>
          </div>
        </div>
        <div class="bb-status-bar">
          <span class="bb-status-pill live"><span class="dot"></span>🟢 ใช้งานอยู่</span>
          <span class="bb-status-meta">อัปเดตข้อมูลล่าสุด: <b id="stk-updated">—</b></span>
        </div>
      </div>
      <div id="stk-root"></div>
    </div>

    <!-- ── Backbar: ต้นทุนผันแปรและคงที่ (Launching soon) ── -->
    <div id="view-bb-varfix" class="view">
      <div class="mb-6">
        <div class="ov-h1-row">
          <img class="app-logo-img" src="assets/varfix-anim.gif" alt="" aria-hidden="true"
               style="width:56px;height:56px">
          <div>
            <h1 class="ov-h1" style="margin:0">ต้นทุนผันแปรและคงที่</h1>
            <p class="ov-sub-h" style="margin:0">Variable &amp; Fixed Cost — บันทึกค่าใช้จ่ายรวมร้านแบบแยกประเภท เห็นรายจ่ายประจำ/รายจ่ายจริง รายวัน/สัปดาห์/เดือน/ปี</p>
          </div>
        </div>
        <div class="bb-status-bar">
          <span class="bb-status-pill live"><span class="dot"></span>🟢 ใช้งานอยู่</span>
          <span class="bb-status-meta">อัปเดตข้อมูลล่าสุด: <b id="vf-updated">—</b></span>
        </div>
      </div>
      <div id="vf-root"></div>
    </div>

    <!-- ── Backbar: บันทึกข้อมูลนำเข้า POS ── -->
    <div id="view-bb-posimport" class="view">
      <div class="mb-6">
        <h1 class="ov-h1">บันทึกข้อมูลนำเข้า POS</h1>
        <p class="ov-sub-h">ดึงยอดขายจาก Loyverse POS · วิเคราะห์เมนู · diagnostic ชื่อเมนู</p>
        <div class="bb-status-bar">
          <span class="bb-status-pill live"><span class="dot"></span>🟢 ใช้งานอยู่</span>
          <span class="bb-status-meta">ดึงล่าสุด: <b id="pos-updated">—</b></span>
        </div>
      </div>
      <div id="pos-root"></div>
    </div>

    <!-- Quest & Achievement -->
    <div id="view-quest" class="view">
      <div class="mb-4">
        <h1 class="ov-h1">90 Days Quest</h1>
        <p class="ov-sub-h">ภารกิจและความสำเร็จ 90 วัน สู่การเปิด PENGTANG CAFE</p>
      </div>
      <div id="qst-root"></div>
    </div>

  </main>
</div>

<!-- Toast -->
<div id="toast" class="toast"></div>

<script>
// ── Injected data ──
const DATA = {DATA_JSON};
const COMP = {COMP_JSON};
const PLATFORMS = {PLATFORMS_JSON};
const INTEL = {INTEL_JSON};
const TRACKER = {TRACKER_JSON};
const UPDATE_LOG = {UPDATE_LOG_JSON};
const UPDATE_SUMMARY = {UPDATE_SUMMARY_JSON};
const LOGOS = {LOGOS_JSON};
const DRINK_COSTS = {DRINK_COSTS_JSON};

// ── Avatar โลโก้ร้าน (ขนาดเท่ากันทุกร้าน) — มีโลโก้ใช้โลโก้ ไม่มีใช้อักษรนำ ──
function avatarHTML(id, name, color, sizePx) {{
  var s = sizePx || 40;
  var nm = String(name || '');
  var initial = (nm.match(/[A-Za-z฀-๿0-9]/) || ['?'])[0];
  var box = 'width:' + s + 'px;height:' + s + 'px;flex-shrink:0;border-radius:50%;';
  var base = '<div style="position:relative;' + box + 'display:flex;align-items:center;justify-content:center;'
    + 'font-weight:800;color:#fff;font-size:' + Math.round(s * 0.4) + 'px;background:' + (color || '#7a4a20')
    + ';overflow:hidden;border:1px solid var(--card-border)">' + initial;
  var logo = (id && LOGOS && LOGOS[id])
    ? '<img src="' + LOGOS[id] + '" alt="โลโก้ ' + escapeHtml(nm) + '" loading="lazy" '
      + 'onerror="this.style.display=\\'none\\'" '
      + 'style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;background:#fff">'
    : '';
  return base + logo + '</div>';
}}
// resolve โลโก้จากชื่อร้าน (ใช้ในติดตามคู่แข่ง ที่อ้างชื่อ ไม่ใช่ id)
function logoIdForName(name) {{
  if (!name) return null;
  var norm = function(s) {{ return String(s).toLowerCase().replace(/\\s+/g, '').replace(/[^a-z0-9฀-๿]/g, ''); }};
  var n = norm(name);
  if (!n) return null;
  var hit = (INTEL || []).find(function(x) {{
    if (x.category !== 'competitor' || !x.title) return false;
    var t = norm(x.title);
    return t.indexOf(n) >= 0 || n.indexOf(t.slice(0, 8)) >= 0;
  }});
  return hit ? hit.id : null;
}}

// ── Chart instances cache ──
const chartInstances = {{}};

// ── Theme ──
const THEMES = ['light', 'dark', 'fancy', 'coffee'];

function setTheme(t) {{
  document.documentElement.setAttribute('data-theme', t);
  localStorage.setItem('sa-theme', t);
  document.querySelectorAll('.theme-btn').forEach(b => b.classList.remove('active-theme'));
  const btn = document.getElementById('theme-' + t);
  if (btn) btn.classList.add('active-theme');
  // Reinitialise all active charts with new colours
  Object.keys(chartInstances).forEach(id => {{
    chartInstances[id].destroy();
    delete chartInstances[id];
  }});
  initCharts(document.querySelector('.view.active')?.id || 'view-home');
}}

function getThemeChartCfg() {{
  const t = document.documentElement.getAttribute('data-theme') || 'light';
  if (t === 'dark')   return {{ grid: '#334155', tick: '#94a3b8', tooltipBg: '#0f172a', tooltipText: '#f8fafc', border: '#1e293b' }};
  if (t === 'fancy')  return {{ grid: 'rgba(255,255,255,0.1)', tick: 'rgba(255,255,255,0.65)', tooltipBg: 'rgba(15,12,41,0.92)', tooltipText: '#fff', border: 'rgba(255,255,255,0.15)' }};
  if (t === 'coffee') return {{ grid: '#3D2010', tick: '#D4AC78', tooltipBg: '#160C02', tooltipText: '#F8EDD5', border: '#2D1A08' }};
  return {{ grid: '#f1f5f9', tick: '#94a3b8', tooltipBg: '#1e293b', tooltipText: '#f8fafc', border: '#ffffff' }};
}}

function applyStoredTheme() {{
  const saved = localStorage.getItem('sa-theme') || 'coffee';
  document.documentElement.setAttribute('data-theme', saved);
  const btn = document.getElementById('theme-' + saved);
  if (btn) btn.classList.add('active-theme');
}}

// ── Mobile sidebar ──
function openSidebar() {{
  document.getElementById('sidebar').classList.add('sidebar-open');
  document.getElementById('sidebar-overlay').classList.add('overlay-open');
  const btn = document.getElementById('sidebar-close-btn');
  if (btn) btn.style.display = 'block';
}}
function closeSidebar() {{
  document.getElementById('sidebar').classList.remove('sidebar-open');
  document.getElementById('sidebar-overlay').classList.remove('overlay-open');
  const btn = document.getElementById('sidebar-close-btn');
  if (btn) btn.style.display = 'none';
}}

// ── Navigation ──
function goHomeFresh() {{
  var base = location.origin + location.pathname;
  location.replace(base + '?r=' + Date.now());
}}
function showView(id) {{
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  const target = document.getElementById(id);
  if (target) target.classList.add('active');

  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  const navId = 'nav-' + id.replace('view-', '');
  const navBtn = document.getElementById(navId);
  if (navBtn) navBtn.classList.add('active');

  closeSidebar();
  setTimeout(() => initCharts(id), 50);
}}

// ── Chart initializer ──
function initCharts(viewId) {{
  if (viewId === 'view-home')    {{ try {{ initHomeOverview(); }} catch(e) {{ console.error('initHomeOverview', e); }} return; }}
  if (viewId === 'view-intel')   {{ try {{ renderIntelCards(); renderIntelUpdateBadge(); }} catch(e) {{ console.error('renderIntelCards', e); }} return; }}
  if (viewId === 'view-updatelog') {{ try {{ renderUpdateLog(); }} catch(e) {{ console.error('renderUpdateLog', e); }} return; }}
  if (viewId === 'view-pricing') {{ try {{ renderPricingView(); }} catch(e) {{ console.error('renderPricingView', e); }} return; }}
  if (viewId === 'view-competitor-deep') {{ try {{ renderDeepTab(); }} catch(e) {{ console.error('renderDeepTab', e); }} return; }}
  if (viewId === 'view-tracker') {{ try {{ renderTrackerView(); }} catch(e) {{ console.error('renderTrackerView', e); }} return; }}
  if (viewId === 'view-cost-drinks') {{ try {{ renderDrinkCosts(); }} catch(e) {{ console.error('renderDrinkCosts', e); }} return; }}
  if (viewId === 'view-bb-stock') {{ try {{ renderStockView(); }} catch(e) {{ console.error('renderStockView', e); }} return; }}
  if (viewId === 'view-bb-varfix') {{ try {{ renderVarfixView(); }} catch(e) {{ console.error('renderVarfixView', e); }} return; }}
  if (viewId === 'view-bb-posimport') {{ try {{ renderPosImportView(); }} catch(e) {{ console.error('renderPosImportView', e); }} return; }}
  if (viewId === 'view-quest') {{ try {{ renderQuestView(); }} catch(e) {{ console.error('renderQuestView', e); }} return; }}
  if (viewId === 'view-bb-armory') {{ return; }}
  const platform = viewId.replace('view-', '');
  if (!DATA[platform]) return;
  try {{ initLineChart(platform); }} catch(e) {{ console.error('initLineChart', e); }}
  try {{ initDoughnutChart(platform); }} catch(e) {{ console.error('initDoughnutChart', e); }}
}}

let homeIntroPlayed = false;
let ovShowdownMetric = 'reach';

function ovTileKey(e, p) {{ if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); showView('view-' + p); }} }}

function ovFmtInt(v) {{ return Number(Math.round(v)).toLocaleString('th-TH'); }}
function ovFmt1(v) {{ return Number(v).toLocaleString('th-TH', {{minimumFractionDigits:1, maximumFractionDigits:1}}); }}

function ovAnimateCount(el, to, dur, fmt) {{
  if (!el) return;
  fmt = fmt || ovFmtInt;
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce || !dur) {{ el.textContent = fmt(to); return; }}
  const start = performance.now();
  function step(now) {{
    const p = Math.min(1, (now - start) / dur);
    const eased = 1 - Math.pow(1 - p, 3);
    el.textContent = fmt(to * eased);
    if (p < 1) requestAnimationFrame(step); else el.textContent = fmt(to);
  }}
  requestAnimationFrame(step);
}}

function ovSparkline(values, color, animate) {{
  const w = 240, h = 42, pad = 4;
  const vals = (values && values.length) ? values : [0, 0];
  const max = Math.max.apply(null, vals), min = Math.min.apply(null, vals);
  const span = (max - min) || 1;
  const n = vals.length;
  const pts = vals.map(function(v, i) {{
    const x = n > 1 ? pad + (i / (n - 1)) * (w - pad * 2) : w / 2;
    const y = h - pad - ((v - min) / span) * (h - pad * 2);
    return [x, y];
  }});
  const d = pts.map(function(p, i) {{ return (i === 0 ? 'M' : 'L') + p[0].toFixed(1) + ' ' + p[1].toFixed(1); }}).join(' ');
  const areaD = d + ' L ' + pts[n-1][0].toFixed(1) + ' ' + h + ' L ' + pts[0][0].toFixed(1) + ' ' + h + ' Z';
  const gid = 'ovsg-' + Math.random().toString(36).slice(2, 8);
  const drawCls = animate ? ' style="stroke-dasharray:1;stroke-dashoffset:1;animation:ovDraw 1.1s cubic-bezier(.22,1,.36,1) forwards"' : '';
  return '<svg class="ov-spark" viewBox="0 0 ' + w + ' ' + h + '" preserveAspectRatio="none">'
    + '<defs><linearGradient id="' + gid + '" x1="0" y1="0" x2="0" y2="1">'
    + '<stop offset="0%" stop-color="' + color + '" stop-opacity="0.26"/>'
    + '<stop offset="100%" stop-color="' + color + '" stop-opacity="0"/></linearGradient></defs>'
    + '<path d="' + areaD + '" fill="url(#' + gid + ')" stroke="none"/>'
    + '<path class="line" pathLength="1" d="' + d + '" stroke="' + color + '"' + drawCls + '/>'
    + '</svg>';
}}

const OV_METRICS = [
  {{ key:'reach', label:'ยอดดูรวม',        get:function(){{ return COMP.total_reach || []; }},     fmt:ovFmtInt }},
  {{ key:'er',    label:'Engagement Rate', get:function(){{ return COMP.avg_er || []; }},          fmt:function(v){{ return ovFmt1(v) + '%'; }} }},
  {{ key:'eng',   label:'การมีส่วนร่วมรวม', get:function(){{ return COMP.total_engagement || []; }}, fmt:ovFmtInt }},
  {{ key:'avg',   label:'ยอดดูเฉลี่ย/วัน',   get:function(){{ return COMP.avg_reach || []; }},        fmt:ovFmt1 }},
];

function ovRenderShareDonut(animate) {{
  const el = document.getElementById('ov-share-canvas');
  if (!el || typeof Chart === 'undefined') return;
  if (chartInstances['ov-share']) {{ chartInstances['ov-share'].destroy(); delete chartInstances['ov-share']; }}
  const tc = getThemeChartCfg();
  const labels = COMP.labels || [], data = COMP.total_reach || [], colors = COMP.colors || [];
  const total = data.reduce(function(a, b) {{ return a + b; }}, 0);
  chartInstances['ov-share'] = new Chart(el.getContext('2d'), {{
    type: 'doughnut',
    data: {{ labels: labels, datasets: [{{ data: data, backgroundColor: colors.map(function(c){{ return c + 'e6'; }}), borderColor: 'transparent', borderWidth: 0, hoverOffset: 7, spacing: 2 }}] }},
    options: {{
      responsive: true, maintainAspectRatio: false, cutout: '70%',
      animation: animate ? {{ animateRotate: true, duration: 1100 }} : false,
      plugins: {{ legend: {{ display: false }}, tooltip: {{ backgroundColor: tc.tooltipBg, titleColor: tc.tooltipText, bodyColor: tc.tooltipText,
        callbacks: {{ label: function(ctx) {{ return ' ' + ctx.label + ': ' + Number(data[ctx.dataIndex]).toLocaleString('th-TH') + ' (' + (total > 0 ? (ctx.parsed / total * 100).toFixed(1) : '0.0') + '%)'; }} }} }} }}
    }}
  }});
  let topI = 0; data.forEach(function(v, i) {{ if (v > data[topI]) topI = i; }});
  const vEl = document.getElementById('ov-share-top-v'), lEl = document.getElementById('ov-share-top-l');
  if (vEl) vEl.textContent = total > 0 ? (data[topI] / total * 100).toFixed(0) + '%' : '—';
  if (lEl) lEl.textContent = (labels[topI] || '') + ' นำ';
  const lg = document.getElementById('ov-share-legend');
  if (lg) lg.innerHTML = labels.map(function(lbl, i) {{
    const pc = total > 0 ? (data[i] / total * 100) : 0;
    return '<div class="row"><span class="nm"><span class="ov-plat-dot" style="background:' + colors[i] + '"></span>' + lbl + '</span><span class="pc" style="color:' + colors[i] + '">' + pc.toFixed(1) + '%</span></div>';
  }}).join('');
}}

function ovRenderShowdownTabs() {{
  const el = document.getElementById('ov-showdown-tabs');
  if (!el) return;
  el.innerHTML = OV_METRICS.map(function(m) {{
    return '<button class="ov-mtab' + (m.key === ovShowdownMetric ? ' active' : '') + '" onclick="ovSetShowdown(\\'' + m.key + '\\')">' + m.label + '</button>';
  }}).join('');
}}
function ovSetShowdown(key) {{ ovShowdownMetric = key; ovRenderShowdownTabs(); ovRenderShowdown(true); }}

function ovRenderShowdown(animate) {{
  const el = document.getElementById('ov-showdown-bars');
  if (!el) return;
  const m = OV_METRICS.filter(function(x) {{ return x.key === ovShowdownMetric; }})[0] || OV_METRICS[0];
  const labels = COMP.labels || [], colors = COMP.colors || [], vals = m.get();
  const maxV = Math.max.apply(null, vals.length ? vals : [0]) || 1;
  const order = vals.map(function(v, i) {{ return i; }}).sort(function(a, b) {{ return vals[b] - vals[a]; }});
  const rankColors = ['#d4a24a', '#9aa3ad', '#c08457'];
  el.innerHTML = order.map(function(idx, pos) {{
    const w = (vals[idx] / maxV * 100);
    return '<div class="ov-bar-row">'
      + '<span class="ov-bar-name"><span class="ov-rank" style="background:' + (rankColors[pos] || '#999') + '26;color:' + (rankColors[pos] || 'var(--text-muted)') + '">' + (pos + 1) + '</span>' + labels[idx] + '</span>'
      + '<div class="ov-bar-track"><div class="ov-bar-fill" data-w="' + w.toFixed(2) + '" style="background:' + colors[idx] + '"></div></div>'
      + '<span class="ov-bar-val">' + m.fmt(vals[idx]) + '</span>'
    + '</div>';
  }}).join('');
  const fills = el.querySelectorAll('.ov-bar-fill');
  requestAnimationFrame(function() {{
    fills.forEach(function(f) {{
      const w = f.getAttribute('data-w') + '%';
      if (animate) {{ f.style.width = '0%'; requestAnimationFrame(function() {{ f.style.width = w; }}); }}
      else f.style.width = w;
    }});
  }});
}}

function initHomeOverview() {{
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const intro = !homeIntroPlayed && !reduce;
  const platforms = COMP.platforms || [];
  const colors = COMP.colors || [], labels = COMP.labels || [];
  const totals = COMP.total_reach || [], ers = COMP.avg_er || [], engs = COMP.total_engagement || [];
  const grandReach = totals.reduce(function(a, b) {{ return a + b; }}, 0);

  const homeView = document.getElementById('view-home');
  if (homeView && intro) {{
    homeView.classList.add('ov-play');
    setTimeout(function() {{ homeView.classList.remove('ov-play'); }}, 1500);
  }}

  ovAnimateCount(document.getElementById('ov-total'), grandReach, intro ? 1100 : 0);

  let maxDays = 0;
  platforms.forEach(function(p) {{ const d = (DATA[p] && DATA[p].metrics && DATA[p].metrics.days) || 0; if (d > maxDays) maxDays = d; }});
  const subEl = document.getElementById('ov-hero-sub');
  if (subEl) subEl.textContent = 'ครั้งที่คนเห็นคอนเทนต์ของคุณ' + (maxDays ? (' · ' + maxDays + ' วันล่าสุด') : '');
  const updEl = document.getElementById('ov-hero-upd');
  if (updEl) updEl.textContent = (typeof UPDATE_SUMMARY !== 'undefined' && UPDATE_SUMMARY.all && UPDATE_SUMMARY.all.last_date_th) ? ('อัปเดต ' + UPDATE_SUMMARY.all.last_date_th) : 'บันทึกอัปเดต';

  const contrib = document.getElementById('ov-contrib');
  if (contrib) {{
    contrib.innerHTML = platforms.map(function(p, i) {{
      return '<div class="ov-contrib-seg" data-w="' + (grandReach > 0 ? (totals[i] / grandReach * 100) : 0).toFixed(2) + '" style="background:' + colors[i] + '"></div>';
    }}).join('');
    const segs = contrib.querySelectorAll('.ov-contrib-seg');
    requestAnimationFrame(function() {{
      segs.forEach(function(s) {{
        const w = s.getAttribute('data-w') + '%';
        if (intro) {{ s.style.width = '0%'; requestAnimationFrame(function() {{ s.style.width = w; }}); }} else s.style.width = w;
      }});
    }});
  }}
  const clg = document.getElementById('ov-contrib-legend');
  if (clg) clg.innerHTML = platforms.map(function(p, i) {{
    const pc = grandReach > 0 ? (totals[i] / grandReach * 100) : 0;
    return '<span class="lg"><span class="dot" style="background:' + colors[i] + '"></span>' + labels[i] + ' ' + pc.toFixed(0) + '%</span>';
  }}).join('');

  const plats = document.getElementById('ov-plats');
  if (plats) {{
    plats.innerHTML = platforms.map(function(p, i) {{
      const spark = ovSparkline((DATA[p] && DATA[p].reach) || [], colors[i], intro);
      return '<div class="ov-tile ov-plat ' + (intro ? 'ov-anim' : '') + '" style="--d:' + (i + 2) + '"'
        + ' role="button" tabindex="0" aria-label="ดูรายละเอียด ' + labels[i] + '"'
        + ' onclick="showView(\\'view-' + p + '\\')" onkeydown="ovTileKey(event,\\'' + p + '\\')">'
        + '<div class="ov-plat-top">'
          + '<span class="ov-plat-name"><span class="ov-plat-dot" style="background:' + colors[i] + '"></span>' + labels[i] + '</span>'
          + '<span class="ov-plat-er" style="background:' + colors[i] + '1f;color:' + colors[i] + '">ER ' + ovFmt1(ers[i]) + '%</span>'
        + '</div>'
        + '<div class="ov-plat-num" data-count="' + totals[i] + '">0</div>'
        + '<div class="ov-plat-numl">ยอดดูรวม · ' + ovFmtInt(engs[i]) + ' การมีส่วนร่วม</div>'
        + spark
      + '</div>';
    }}).join('');
    plats.querySelectorAll('.ov-plat-num').forEach(function(el) {{
      ovAnimateCount(el, Number(el.getAttribute('data-count')), intro ? 1100 : 0);
    }});
  }}

  ovRenderShareDonut(intro);
  ovRenderShowdownTabs();
  ovRenderShowdown(intro);

  homeIntroPlayed = true;
}}

function initLineChart(platform) {{
  const canvasId = platform + 'LineChart';
  if (chartInstances[canvasId]) {{ chartInstances[canvasId].destroy(); delete chartInstances[canvasId]; }}
  const el = document.getElementById(canvasId);
  if (!el) return;
  const pd = DATA[platform];
  const color = {{ tiktok: '#EE1D52', facebook: '#1877f2', instagram: '#e1306c' }}[platform] || '#2563eb';
  const tc = getThemeChartCfg();
  chartInstances[canvasId] = new Chart(el.getContext('2d'), {{
    type: 'line',
    data: {{
      labels: pd.dates,
      datasets: [{{
        label: 'ยอดดู', data: pd.reach,
        borderColor: color, backgroundColor: color + '22',
        borderWidth: 2.5, pointRadius: 3, pointHoverRadius: 7,
        fill: true, tension: 0.35,
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          backgroundColor: tc.tooltipBg, titleColor: tc.tooltipText, bodyColor: tc.tooltipText,
          callbacks: {{ label: ctx => 'ยอดดู: ' + ctx.parsed.y.toLocaleString('th-TH') }}
        }}
      }},
      scales: {{
        x: {{ grid: {{ display: false }}, ticks: {{ color: tc.tick, maxRotation: 45 }} }},
        y: {{ beginAtZero: true, grid: {{ color: tc.grid }}, ticks: {{ color: tc.tick, callback: v => v.toLocaleString('th-TH') }} }}
      }}
    }}
  }});
}}

function initDoughnutChart(platform) {{
  const canvasId = platform + 'DoughnutChart';
  if (chartInstances[canvasId]) {{ chartInstances[canvasId].destroy(); delete chartInstances[canvasId]; }}
  const el = document.getElementById(canvasId);
  if (!el) return;
  const pd = DATA[platform];
  const dough = pd.doughnut;
  const tc = getThemeChartCfg();

  /* ── fallback เมื่อยังไม่มีข้อมูล engagement ── */
  const total = dough.data.reduce((s, v) => s + v, 0);
  const isEmpty = total === 0;
  const chartData   = isEmpty ? [1] : dough.data;
  const chartColors = isEmpty ? ['rgba(128,128,128,0.18)'] : dough.colors;
  const chartLabels = isEmpty ? ['ยังไม่มีข้อมูล'] : dough.labels;

  chartInstances[canvasId] = new Chart(el.getContext('2d'), {{
    type: 'doughnut',
    data: {{
      labels: chartLabels,
      datasets: [{{
        data: chartData,
        backgroundColor: chartColors,
        borderWidth: isEmpty ? 0 : 2,
        borderColor: tc.border
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false, cutout: '60%',
      plugins: {{
        legend: {{ position: 'bottom', labels: {{ padding: 16, font: {{ size: 11 }}, color: tc.tick }} }},
        tooltip: {{
          enabled: !isEmpty,
          backgroundColor: tc.tooltipBg, titleColor: tc.tooltipText, bodyColor: tc.tooltipText,
          callbacks: {{
            label: ctx => ctx.label + ': ' + ctx.parsed.toLocaleString('th-TH')
          }}
        }},
        /* ── center label เมื่อไม่มีข้อมูล ── */
        beforeDraw: undefined
      }},
      animation: {{ animateRotate: !isEmpty }}
    }},
    plugins: [{{
      id: 'emptyLabel',
      afterDraw(chart) {{
        if (!isEmpty) return;
        const {{ ctx, chartArea: {{ width, height, left, top }} }} = chart;
        ctx.save();
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = tc.tick;
        ctx.font = '600 12px Prompt, system-ui';
        ctx.fillText('ยังไม่มีข้อมูล', left + width / 2, top + height / 2);
        ctx.restore();
      }}
    }}]
  }});
}}

// ── Intel view ──
const INTEL_BADGE = {{
  competitor:       {{ label: '☕ คู่แข่ง',   cls: 'bg-red-100 text-red-700' }},
  delivery:         {{ label: '🛵 Delivery',  cls: 'bg-orange-100 text-orange-700' }},
  coffee_knowledge: {{ label: '💡 ความรู้',   cls: 'bg-blue-100 text-blue-700' }},
  news_events:      {{ label: '📅 Events',    cls: 'bg-green-100 text-green-700' }},
  equipment:        {{ label: '⚙️ อุปกรณ์',  cls: 'bg-purple-100 text-purple-700' }},
}};
const RELEVANCE_CLS = {{
  high:   'bg-red-50 text-red-600',
  medium: 'bg-yellow-100 text-yellow-700',
  low:    'bg-slate-100 text-slate-500',
}};
const PRICE_LABELS = {{
  espresso:'เอสเปรสโซ', americano:'อเมริกาโน', latte:'ลาเต้',
  cappuccino:'คาปูชิโน', cold_brew:'Cold Brew', frappe:'Frappe',
  matcha:'มัทฉะ', signature_drink:'Signature Drink',
  food:'อาหาร/เบเกอรี่',
}};
const PRICING_TABS = {{
  espresso:  {{ keys: ['espresso','americano'], includeOther: false }},
  latte:     {{ keys: ['latte','cappuccino'] }},
  cold_brew: {{ keys: ['cold_brew'] }},
  frappe:    {{ keys: ['frappe'] }},
  signature: {{ keys: ['signature_drink','matcha'] }},
  food:      {{ keys: ['food'], includeOther: true }},
}};
let currentIntelTab = 'all';
let currentPricingTab = 'espresso';

function setIntelTab(tab) {{
  currentIntelTab = tab;
  document.querySelectorAll('.intel-tab').forEach(b => b.classList.remove('active'));
  const btn = document.getElementById('intel-tab-' + tab);
  if (btn) btn.classList.add('active');
  renderIntelCards();
}}

function toggleIntelAccord(id) {{
  const body = document.getElementById('accord-body-' + id);
  if (!body) return;
  const open = body.classList.toggle('open');
  const chev = document.getElementById('accord-chev-' + id);
  if (chev) chev.style.transform = open ? 'rotate(180deg)' : '';
  const hdr = document.getElementById('accord-hdr-' + id);
  if (hdr) hdr.setAttribute('aria-expanded', open ? 'true' : 'false');
}}

function renderPricingRows(pricing) {{
  if (!pricing) return '<span class="text-xs" style="color:var(--text-muted)">ไม่มีข้อมูลราคา</span>';
  let rows = '';
  Object.entries(PRICE_LABELS).forEach(([key, lbl]) => {{
    const p = pricing[key];
    if (p && p.price) rows += `<div class="flex gap-2 text-xs py-1 border-b" style="border-color:var(--card-border)">
      <span style="color:var(--text-muted)" class="w-28 flex-shrink-0">${{lbl}}</span>
      <span class="font-bold text-emerald-500">${{Number(p.price).toLocaleString('th-TH')}} บาท</span>
      ${{p.note ? `<span style="color:var(--text-muted)">${{p.note}}</span>` : ''}}
    </div>`;
  }});
  if (pricing.other && pricing.other.length) {{
    pricing.other.forEach(o => {{
      if (o.price) rows += `<div class="flex gap-2 text-xs py-1 border-b" style="border-color:var(--card-border)">
        <span style="color:var(--text-muted)" class="w-28 flex-shrink-0">${{o.name}}</span>
        <span class="font-bold text-emerald-500">${{Number(o.price).toLocaleString('th-TH')}} บาท</span>
        ${{o.note ? `<span style="color:var(--text-muted)">${{o.note}}</span>` : ''}}
      </div>`;
    }});
  }}
  return rows || '<span class="text-xs" style="color:var(--text-muted)">ไม่พบข้อมูลราคา</span>';
}}

function renderBulletList(items) {{
  if (!items || !items.length) return '<span class="text-xs" style="color:var(--text-muted)">—</span>';
  return items.map(i =>
    `<span class="inline-block text-xs px-2 py-0.5 rounded-full mr-1 mb-1"
      style="background:var(--nav-active);color:var(--text)">${{i}}</span>`
  ).join('');
}}

// ── ตัวช่วยอ่านง่าย: แตกข้อความยาว/array เป็นข้อ ๆ พร้อม emoji ──
function splitToItems(value) {{
  if (Array.isArray(value)) {{
    return value.map(function(v) {{ return String(v == null ? '' : v).trim(); }}).filter(Boolean);
  }}
  if (value == null) return [];
  var s = String(value).trim();
  if (!s || s === '—') return [];
  var parts;
  if (s.indexOf('\\n') !== -1)      parts = s.split('\\n');
  else if (s.indexOf(' · ') !== -1) parts = s.split(' · ');
  else if (s.indexOf(' • ') !== -1) parts = s.split(' • ');
  else if (s.indexOf('; ') !== -1)  parts = s.split('; ');
  else parts = [s];
  return parts.map(function(p) {{ return p.replace(/^[\\s•\\-\\*·]+/, '').trim(); }}).filter(Boolean);
}}
function bulletList(value, emoji) {{
  var items = splitToItems(value);
  if (!items.length) return '<span style="color:var(--text-muted)">—</span>';
  if (items.length === 1) return '<span>' + escapeHtml(items[0]) + '</span>';
  var mark = emoji || '🔹';
  return '<ul class="bullet-list">' + items.map(function(it) {{
    return '<li><span class="bl-mark">' + mark + '</span><span>' + escapeHtml(it) + '</span></li>';
  }}).join('') + '</ul>';
}}
function plainText(v) {{
  return escapeHtml((v == null || v === '') ? '—' : String(v));
}}
function chipList(arr) {{
  if (!arr || !arr.length) return '<span style="color:var(--text-muted)">—</span>';
  return '<div class="flex flex-wrap gap-1">' + arr.map(function(t) {{
    return '<span class="inline-block text-xs px-2 py-0.5 rounded-full" style="background:var(--nav-active);color:var(--text-muted)">#' + escapeHtml(t) + '</span>';
  }}).join('') + '</div>';
}}

function buildSocialSentence(st) {{
  if (!st || !st.primary_platform) return 'ไม่พบข้อมูล Social Media';
  let s = 'ใช้ ' + st.primary_platform + ' เป็นหลัก';
  if (st.posting_frequency) s += ' โพสต์' + st.posting_frequency;
  if (st.content_style) s += ' เน้น content แนว ' + st.content_style;
  if (st.engagement_level) {{
    const lvl = {{high:'สูง',medium:'ปานกลาง',low:'ต่ำ'}}[st.engagement_level] || st.engagement_level;
    s += ' การมีส่วนร่วมระดับ' + lvl;
  }}
  return s;
}}
function deriveOpportunity(item) {{
  const ops = [];
  const w = (item.weaknesses||[]).join(' ');
  const st = item.social_trend || {{}};
  if (w.includes('TikTok')) ops.push('ไม่มี TikTok — เปิดพื้นที่ให้เราครอง TikTok สกลนคร ก่อนคู่แข่งรายนี้');
  if (w.includes('Instagram') && !String(st.primary_platform||'').includes('Instagram')) ops.push('ไม่มี Instagram — สร้าง presence ก่อนได้');
  if (w.includes('ราคาสาธารณะ')) ops.push('ไม่มีราคาสาธารณะ — ประกาศราคาชัดเจนสร้างความน่าเชื่อถือและได้เปรียบทันที');
  if (st.engagement_level === 'low') ops.push('Engagement ต่ำ — content คุณภาพดีกว่าจะ outperform ได้ง่าย');
  if (w.includes('Social media อ่อนแอ')) ops.push('Social media อ่อนแอโดยรวม — ช่องว่างขนาดใหญ่ที่เราสามารถเข้าครองได้');
  return ops.length ? ops : ['ติดตามและวิเคราะห์เพิ่มเติมจากข้อมูลจริง'];
}}
function renderCompetitorCards() {{
  const items = INTEL.filter(x => x.category === 'competitor');
  if (!items.length) return '<div class="text-center py-12" style="color:var(--text-muted)">ไม่พบข้อมูลคู่แข่ง</div>';
  const palette = ['#6366f1','#0ea5e9','#10b981','#f59e0b','#ef4444','#8b5cf6','#ec4899','#14b8a6'];
  return `<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
${{items.map((item, idx) => {{
  const badge = INTEL_BADGE[item.category] || {{ label: item.category, cls: 'bg-slate-100 text-slate-600' }};
  const relCls = RELEVANCE_CLS[item.relevance] || RELEVANCE_CLS.low;
  const st = item.social_trend || {{}};
  const color = palette[idx % palette.length];
  const socialParts = [
    st.primary_platform || null,
    st.posting_frequency ? 'ความถี่: ' + st.posting_frequency : null,
    st.content_style ? 'สไตล์: ' + st.content_style : null,
    st.engagement_level ? 'engagement: ' + ({{high:'สูง',medium:'ปานกลาง',low:'ต่ำ'}}[st.engagement_level]||st.engagement_level) : null,
  ].filter(Boolean);
  const ops = deriveOpportunity(item);
  const mkList = (arr, mk) => arr.map(x=>`<li class="text-xs leading-relaxed flex gap-1.5" style="color:var(--text-muted)"><span class="flex-shrink-0">${{mk||'•'}}</span><span>${{x}}</span></li>`).join('');
  const mkSection = (emoji, title, arr, mk) => arr && arr.length
    ? `<div><div class="text-xs font-semibold mb-1" style="color:var(--text)">${{emoji}} ${{title}}</div><ul class="space-y-0.5">${{mkList(arr, mk)}}</ul></div>`
    : '';
  return `<div class="rounded-xl shadow-sm border flex flex-col" style="background:var(--card);border-color:var(--card-border)">
    <div class="p-5 border-b" style="border-color:var(--card-border)">
      <div class="flex items-start gap-3 mb-3">
        ${{avatarHTML(item.id, item.title, color, 44)}}
        <div class="min-w-0 flex-1">
          <div class="font-bold text-sm leading-snug mb-1.5" style="color:var(--text)">${{item.title}}</div>
          <div class="flex flex-wrap gap-1">
            <span class="text-xs px-2 py-0.5 rounded-full font-semibold ${{badge.cls}}">${{badge.label}}</span>
            <span class="text-xs px-2 py-0.5 rounded-full font-semibold ${{relCls}}">${{item.relevance}}</span>
          </div>
        </div>
      </div>
      <p class="text-xs leading-relaxed" style="color:var(--text-muted);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">${{item.summary}}</p>
    </div>
    <div class="p-5 flex-1 space-y-4">
      ${{mkSection('🗿','จุดแข็ง', item.strengths, '✅')}}
      ${{mkSection('🪫','จุดอ่อน', item.weaknesses, '⚠️')}}
      ${{mkSection('📱','การใช้ Social Media', socialParts, '🔹')}}
      ${{mkSection('💎','โอกาสที่เราแข่งได้', ops, '💎')}}
      ${{item.promotions && item.promotions.length ? mkSection('🎯','โปรโมชัน', item.promotions, '🎁') : ''}}
      ${{item.location ? `<div><div class="text-xs font-semibold mb-1" style="color:var(--text)">📍 ที่ตั้ง</div><p class="text-xs leading-relaxed" style="color:var(--text-muted)">${{item.location}}</p></div>` : ''}}
      ${{item.hours ? `<div><div class="text-xs font-semibold mb-1" style="color:var(--text)">⏰ เวลาทำการ</div><p class="text-xs" style="color:var(--text-muted)">${{item.hours}}</p></div>` : ''}}
      ${{item.delivery ? `<div>
        <div class="text-xs font-semibold mb-1.5" style="color:var(--text)">🛵 Delivery</div>
        <div class="rounded-xl p-3 space-y-1.5" style="background:var(--nav-active);border:1px solid var(--card-border)">
          <div class="flex items-center gap-2 text-xs"><span style="color:var(--text-muted)">แอปหลัก:</span><span class="font-semibold px-2 py-0.5 rounded-full bg-orange-100 text-orange-700">${{item.delivery.primary_app}}</span>
            ${{(item.delivery.apps||[]).filter(a=>a!==item.delivery.primary_app).map(a=>`<span class="px-2 py-0.5 rounded-full text-xs" style="background:var(--card);color:var(--text-muted)">${{a}}</span>`).join('')}}</div>
          <div class="text-xs" style="color:var(--text-muted)">⏰ Peak: <span style="color:var(--text)">${{item.delivery.peak_hours}}</span></div>
          ${{(item.delivery.active_promos||[]).length ? `<div class="text-xs" style="color:var(--text-muted)">🎟 โปร: ${{item.delivery.active_promos.join(' · ')}}</div>` : ''}}
          <div class="text-xs pt-0.5" style="color:var(--text-muted)">${{item.delivery.notes}}</div>
        </div>
      </div>` : ''}}
    </div>
  </div>`;
}}).join('')}}
  </div>`;
}}
function renderIntelCards() {{
  const container = document.getElementById('intel-cards');
  if (!container) return;
  if (currentIntelTab === 'competitor') {{
    container.innerHTML = renderCompetitorCards();
    return;
  }}
  const items = currentIntelTab === 'all' ? INTEL : INTEL.filter(x => x.category === currentIntelTab);
  if (!items.length) {{
    container.innerHTML = '<div class="text-center py-12" style="color:var(--text-muted)">ไม่พบข้อมูลในหมวดนี้</div>';
    return;
  }}
  container.innerHTML = items.map(item => {{
    const badge   = INTEL_BADGE[item.category] || {{ label: item.category, cls: 'bg-slate-100 text-slate-600' }};
    const relCls  = RELEVANCE_CLS[item.relevance] || RELEVANCE_CLS.low;
    const isComp  = item.category === 'competitor';
    const stTrend = item.social_trend || {{}};
    return `<div class="intel-accord">
      <div class="intel-accord-hdr" id="accord-hdr-${{item.id}}" role="button" tabindex="0"
           aria-expanded="false" aria-controls="accord-body-${{item.id}}"
           onclick="toggleIntelAccord('${{item.id}}')"
           onkeydown="if(event.key==='Enter'||event.key===' '){{event.preventDefault();toggleIntelAccord('${{item.id}}');}}">
        <div class="flex items-center gap-3 min-w-0">
          <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold ${{badge.cls}} flex-shrink-0">${{badge.label}}</span>
          <span class="font-semibold text-sm truncate" style="color:var(--text)">${{item.title}}</span>
        </div>
        <div class="flex items-center gap-2 flex-shrink-0 ml-3">
          <span class="text-xs px-2 py-0.5 rounded-full font-semibold ${{relCls}}">${{item.relevance}}</span>
          <svg id="accord-chev-${{item.id}}" class="w-4 h-4 flex-shrink-0 transition-transform"
            style="color:var(--text-muted)" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
          </svg>
        </div>
      </div>
      <div id="accord-body-${{item.id}}" class="intel-accord-body">
        ${{isComp ? `
          <p class="text-sm mb-5 leading-relaxed" style="color:var(--text-muted)">${{item.summary}}</p>
          ${{item.strengths && item.strengths.length ? `
            <div class="mb-4">
              <div class="text-sm font-semibold mb-1.5" style="color:var(--text)">💪 จุดแข็ง</div>
              <div class="text-sm" style="color:var(--text-muted)">${{bulletList(item.strengths, '✅')}}</div>
            </div>` : ''}}
          ${{item.weaknesses && item.weaknesses.length ? `
            <div class="mb-4">
              <div class="text-sm font-semibold mb-1.5" style="color:var(--text)">🪫 จุดอ่อน</div>
              <div class="text-sm" style="color:var(--text-muted)">${{bulletList(item.weaknesses, '⚠️')}}</div>
            </div>` : ''}}
          <div class="mb-4">
            <div class="text-sm font-semibold mb-1.5" style="color:var(--text)">📱 การใช้ Social Media</div>
            <p class="text-sm" style="color:var(--text-muted)">${{buildSocialSentence(item.social_trend)}}</p>
          </div>
          <div>
            <div class="text-sm font-semibold mb-1.5" style="color:var(--text)">💎 โอกาสที่เราแข่งได้</div>
            <div class="text-sm" style="color:var(--text-muted)">${{bulletList(deriveOpportunity(item), '💎')}}</div>
          </div>
        ` : `
          <p class="text-sm mb-3 leading-relaxed" style="color:var(--text-muted)">${{item.summary}}</p>
          ${{item.tags && item.tags.length ? `<div class="mb-4 flex flex-wrap gap-1">${{item.tags.map(t=>`<span class="inline-block text-xs px-2 py-0.5 rounded-full" style="background:var(--nav-active);color:var(--text-muted)">#${{t}}</span>`).join('')}}</div>` : ''}}
          ${{item.detail ? `<div class="text-xs leading-relaxed" style="color:var(--text-muted)">${{bulletList(item.detail, '📌')}}</div>` : ''}}
        `}}
      </div>
    </div>`;
  }}).join('');
}}

// ── Pricing view ──
function setPricingTab(tab) {{
  currentPricingTab = tab;
  document.querySelectorAll('.pricing-tab').forEach(b => b.classList.remove('active'));
  const btn = document.getElementById('pricing-tab-' + tab);
  if (btn) btn.classList.add('active');
  renderPricingView();
}}

function renderPricingView() {{
  const competitors = INTEL.filter(x => x.category === 'competitor');

  // KPI cards
  const kpiEl = document.getElementById('pricing-kpi-cards');
  if (kpiEl) {{
    const lattePrices = [];
    competitors.forEach(c => {{
      if (!c.pricing) return;
      ['latte','cappuccino'].forEach(k => {{
        const v = c.pricing[k];
        if (v && v.price) {{ const n = parseFloat(String(v.price).replace(/,/g,'')); if (!isNaN(n)) lattePrices.push(n); }}
      }});
    }});
    const avgLatte = lattePrices.length ? Math.round(lattePrices.reduce((a,b)=>a+b,0)/lattePrices.length) : 0;

    const coldBrewPrices = [];
    competitors.forEach(c => {{
      if (!c.pricing) return;
      const v = c.pricing['cold_brew'];
      if (v && v.price) {{ const n = parseFloat(String(v.price).replace(/,/g,'')); if (!isNaN(n)) coldBrewPrices.push(n); }}
    }});
    const avgColdBrew = coldBrewPrices.length ? Math.round(coldBrewPrices.reduce((a,b)=>a+b,0)/coldBrewPrices.length) : 0;

    const withPromo = competitors.filter(c => c.promotions && c.promotions.length > 0).length;

    const kpiItems = [
      {{ icon:'🏪', label:'ร้านคู่แข่งที่ติดตาม', value: String(competitors.length), unit:'ร้าน', accent:false }},
      {{ icon:'☕', label:'ราคาเฉลี่ย ลาเต้',     value: avgLatte ? avgLatte.toLocaleString('th-TH') : '—', unit:'บาท · เฉลี่ยตลาด', accent:true }},
      {{ icon:'🧊', label:'ราคาเฉลี่ย Cold Brew', value: avgColdBrew ? avgColdBrew.toLocaleString('th-TH') : '—', unit:'บาท · เฉลี่ยตลาด', accent:false }},
      {{ icon:'🎯', label:'ร้านที่มีโปรโมชัน',     value: String(withPromo), unit:'จาก ' + competitors.length + ' ร้าน', accent:false }},
    ];
    kpiEl.innerHTML = kpiItems.map(function(k) {{
      return '<div class="ov-tile ov-kpi">'
        + '<div class="ov-kpi-top"><span class="ov-kpi-icon">' + k.icon + '</span><span class="ov-kpi-label">' + k.label + '</span></div>'
        + '<div class="ov-kpi-val' + (k.accent ? ' accent' : '') + '">' + k.value + '</div>'
        + '<div class="ov-kpi-unit">' + k.unit + '</div>'
      + '</div>';
    }}).join('');
  }}

  // Pricing table
  const tbody = document.getElementById('pricing-table-body');
  if (tbody) {{
    const tab = PRICING_TABS[currentPricingTab];
    const rows = [];
    competitors.forEach(c => {{
      if (!c.pricing) return;
      tab.keys.forEach(key => {{
        const p = c.pricing[key];
        if (p && p.price) rows.push({{ clinic: c.title, price: p.price, note: p.note||'' }});
      }});
      if (tab.includeOther && c.pricing.other) {{
        c.pricing.other.forEach(o => {{
          if (o.price) rows.push({{ clinic: c.title, price: o.price, note: (o.note||'') + (o.name ? ' (' + o.name + ')' : '') }});
        }});
      }}
    }});
    rows.sort((a,b) => (parseFloat(String(a.price).replace(/,/g,''))||Infinity) - (parseFloat(String(b.price).replace(/,/g,''))||Infinity));
    const minPrice = rows.length ? parseFloat(String(rows[0].price).replace(/,/g,'')) : null;
    tbody.innerHTML = rows.length
      ? rows.map(r => {{
          const rPrice = parseFloat(String(r.price).replace(/,/g,''));
          const isMin = minPrice !== null && rPrice === minPrice;
          const rowCls = isMin ? 'bg-green-50' : 'hover:bg-slate-50';
          return `<tr class="${{rowCls}} border-b border-slate-100 last:border-0">
            <td class="px-4 py-3 font-semibold text-sm" style="color:var(--text)">${{r.clinic}}${{isMin ? ' <span class=\\"ml-1 text-xs text-green-600 font-bold\\">ถูกสุด</span>' : ''}}</td>
            <td class="px-4 py-3 text-right font-bold text-emerald-500 tabular-nums">${{Number(String(r.price).replace(/,/g,'')).toLocaleString('th-TH')}}</td>
            <td class="px-4 py-3 text-xs" style="color:var(--text-muted)">${{r.note||'—'}}</td>
          </tr>`;
        }}).join('')
      : `<tr><td colspan="3" class="px-4 py-8 text-center text-sm" style="color:var(--text-muted)">ไม่พบข้อมูลราคาในหมวดนี้</td></tr>`;
  }}

  // Social trend table
  const stbody = document.getElementById('social-trend-body');
  if (stbody) {{
    stbody.innerHTML = competitors.map(c => {{
      const st = c.social_trend || {{}};
      const engEmoji = st.engagement_level === 'high'   ? '🟢'
                     : st.engagement_level === 'medium' ? '🟡'
                     : '🔴';
      return `<tr class="hover:bg-slate-50 border-b border-slate-100 last:border-0">
        <td class="px-4 py-3 font-semibold text-sm" style="color:var(--text)">${{c.title}}</td>
        <td class="px-4 py-3 text-sm" style="color:var(--text)">${{st.primary_platform||'—'}}</td>
        <td class="px-4 py-3 text-sm" style="color:var(--text)">${{st.content_style||'—'}}</td>
        <td class="px-4 py-3 text-center">${{engEmoji}} <span class="text-xs" style="color:var(--text-muted)">${{st.engagement_level||'—'}}</span></td>
      </tr>`;
    }}).join('');
  }}
}}

// ── Import view ──
let selectedPlatform = null;

function selectPlatform(name) {{
  selectedPlatform = name;
  document.querySelectorAll('.plat-btn').forEach(b => {{
    b.style.borderColor = '#e2e8f0';
    b.style.color = '#475569';
    b.style.background = '';
  }});
  const btn = document.getElementById('plat-' + name);
  if (btn) {{
    const pc = btn.style.getPropertyValue('--pc');
    btn.style.borderColor = pc;
    btn.style.color = pc;
  }}
}}

function handleDragOver(e) {{
  e.preventDefault();
  document.getElementById('dropZone').classList.add('drag-over');
}}

function handleDragLeave(e) {{
  document.getElementById('dropZone').classList.remove('drag-over');
}}

function handleDrop(e) {{
  e.preventDefault();
  document.getElementById('dropZone').classList.remove('drag-over');
  const files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.csv'));
  if (files.length > 0) processFiles(files);
}}

function handleFileSelect(e) {{
  const files = Array.from(e.target.files);
  if (files.length > 0) processFiles(files);
}}

function processFiles(files) {{
  const file = files[0];
  const reader = new FileReader();

  reader.onload = function(e) {{
    let text = e.target.result;
    renderPreview(text, file.name);
  }};

  // Try utf-16 first (Facebook/Instagram), fall back handled by checking BOM
  const bom16 = new Uint8Array([0xFF, 0xFE]);
  const slice = file.slice(0, 2);
  const bomReader = new FileReader();
  bomReader.onload = function(ev) {{
    const arr = new Uint8Array(ev.target.result);
    const isUtf16 = (arr[0] === 0xFF && arr[1] === 0xFE) || (arr[0] === 0xFE && arr[1] === 0xFF);
    reader.readAsText(file, isUtf16 ? 'UTF-16' : 'UTF-8');
  }};
  bomReader.readAsArrayBuffer(slice);
}}

function parseCSV(text) {{
  const lines = text.split(/\\r?\\n/).filter(l => l.trim());
  let dataLines = lines;
  if (lines.length > 0 && lines[0].trim().startsWith('sep=')) {{
    // narrow format: skip sep= line + metric name line, header at index 2
    dataLines = lines.slice(2);
  }}
  if (dataLines.length === 0) return {{ headers: [], rows: [] }};
  const headers = dataLines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
  const rows = [];
  for (let i = 1; i < Math.min(dataLines.length, 6); i++) {{
    const cells = dataLines[i].split(',').map(c => c.trim().replace(/^"|"$/g, ''));
    rows.push(cells);
  }}
  return {{ headers, rows }};
}}

function renderPreview(text, filename) {{
  const {{ headers, rows }} = parseCSV(text);
  if (headers.length === 0) return;

  let tableHtml = '<table class="w-full border-collapse">';
  tableHtml += '<thead><tr>';
  headers.forEach(h => {{
    tableHtml += '<th class="border border-slate-200 px-3 py-2 bg-slate-50 text-xs font-bold text-slate-600 text-left whitespace-nowrap">' + escHtml(h) + '</th>';
  }});
  tableHtml += '</tr></thead><tbody>';
  rows.forEach(row => {{
    tableHtml += '<tr>';
    headers.forEach((_, i) => {{
      tableHtml += '<td class="border border-slate-200 px-3 py-1.5 text-slate-700 text-xs whitespace-nowrap">' + escHtml(row[i] || '') + '</td>';
    }});
    tableHtml += '</tr>';
  }});
  tableHtml += '</tbody></table>';

  document.getElementById('previewTable').innerHTML = tableHtml;
  document.getElementById('previewArea').classList.remove('hidden');
}}

function escHtml(s) {{
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}}

function confirmImport() {{
  showToast('นำเข้าสำเร็จ! รีเฟรชหน้าเพื่อดูข้อมูลใหม่ 🎉');
}}

function showToast(msg) {{
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 3500);
}}

// ── Competitor Deep View ──
const COMPETITOR_EVENTS = [
  {{ date:'2026-05-20', competitor:'Amazon Coffee สกลนคร', type:'new',     icon:'⚠️', text:'เริ่มต้น tracking — chain PTT ราคา latte 55 บ. cold brew 65 บ. มี loyalty app A Card' }},
  {{ date:'2026-05-20', competitor:'Inthanin Coffee',       type:'pricing', icon:'💰', text:'Specialty Thai beans latte 75 บ. cold brew 85 บ. บรรยากาศ premium กว่า Amazon' }},
  {{ date:'2026-05-20', competitor:'ร้านกาแฟ Local',        type:'content', icon:'📱', text:'Instagram/TikTok content latte art น่าสนใจ mid-range latte 70 บ. local vibe สูง' }},
  {{ date:'2026-05-20', competitor:'Wawee Coffee',          type:'platform', icon:'📸', text:'TikTok national following beans story เชียงใหม่ สมาชิก 10% off นักศึกษา 15% off' }},
];

let currentDeepTab = 'overview';
let selectedDeepComp = null;

function gotoDeepDetail(idx) {{
  var comps = INTEL.filter(function(x) {{ return x.category === 'competitor'; }});
  if (idx < comps.length) {{ selectedDeepComp = comps[idx].id; }}
  setDeepTab('detail');
}}

function setDeepTab(tab) {{
  currentDeepTab = tab;
  ['overview','detail','timeline'].forEach(function(t) {{
    var el = document.getElementById('deep-content-' + t);
    if (el) el.style.display = t === tab ? '' : 'none';
    var btn = document.getElementById('deep-tab-' + t);
    if (btn) btn.classList.toggle('active', t === tab);
  }});
  renderDeepTab();
}}

function renderDeepTab() {{
  if (currentDeepTab === 'overview') renderDeepOverview();
  else if (currentDeepTab === 'detail') renderDeepDetail();
  else renderDeepTimeline();
}}

function renderDeepOverview() {{
  var comps = INTEL.filter(function(x) {{ return x.category === 'competitor'; }});
  var palette = ['#6366f1','#0ea5e9','#10b981','#f59e0b','#ef4444','#8b5cf6','#ec4899','#14b8a6'];
  var el = document.getElementById('deep-content-overview');
  if (!el) return;
  var cards = comps.map(function(c, i) {{
    var col = palette[i % palette.length];
    var wkCount = (c.weaknesses || []).length;
    var badge = wkCount >= 3
      ? '<span style="background:rgba(239,68,68,0.12);color:#dc2626" class="text-xs px-2 py-0.5 rounded-full font-bold">🔴 สูง</span>'
      : wkCount >= 1
      ? '<span style="background:rgba(245,158,11,0.12);color:#d97706" class="text-xs px-2 py-0.5 rounded-full font-bold">🟡 กลาง</span>'
      : '<span style="background:rgba(16,185,129,0.12);color:#059669" class="text-xs px-2 py-0.5 rounded-full font-bold">🟢 ต่ำ</span>';
    var plat = (c.social_trend || {{}}).primary_platform || '—';
    var freq = (c.social_trend || {{}}).posting_frequency || '—';
    var strengths = (c.strengths || []).slice(0,2).map(function(s) {{
      return '<span class="text-xs px-2 py-0.5 rounded-full" style="background:rgba(16,185,129,0.1);color:#059669">+ ' + s + '</span>';
    }}).join('');
    var weakness = (c.weaknesses || []).slice(0,1).map(function(w) {{
      return '<span class="text-xs px-2 py-0.5 rounded-full" style="background:rgba(239,68,68,0.08);color:#dc2626">- ' + w + '</span>';
    }}).join('');
    var cid = c.id;
    return '<div class="rounded-xl border shadow-sm p-5 flex flex-col gap-3" style="background:var(--card);border-color:var(--card-border)">'
      + '<div class="flex items-start gap-3">'
        + avatarHTML(c.id, c.title, col, 40)
        + '<div class="flex-1 min-w-0">'
          + '<div class="font-bold text-sm leading-tight mb-0.5" style="color:var(--text)">' + c.title + '</div>'
          + '<div class="text-xs" style="color:var(--text-muted)">' + plat + ' · ' + freq + '</div>'
        + '</div>'
        + badge
      + '</div>'
      + '<p class="text-xs leading-relaxed" style="color:var(--text-muted);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">' + c.summary + '</p>'
      + '<div class="flex flex-wrap gap-1.5">' + strengths + weakness + '</div>'
      + '<button onclick="gotoDeepDetail(' + i + ')" class="text-xs font-semibold text-left mt-auto" style="color:#6366f1">ดูรายละเอียด →</button>'
    + '</div>';
  }});
  el.innerHTML = '<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">' + cards.join('') + '</div>';
}}

function selectDeepComp(id) {{
  selectedDeepComp = id;
  var sel = document.getElementById('deep-comp-select');
  if (sel) sel.value = id;
  renderDeepCompDetail();
}}

function renderDeepDetail() {{
  var comps = INTEL.filter(function(x) {{ return x.category === 'competitor'; }});
  var el = document.getElementById('deep-content-detail');
  if (!el) return;
  var opts = comps.map(function(c) {{
    return '<option value="' + c.id + '"' + (selectedDeepComp === c.id ? ' selected' : '') + '>' + c.title + '</option>';
  }}).join('');
  el.innerHTML = '<div class="mb-5">'
    + '<label class="text-xs font-bold uppercase tracking-widest text-slate-500 whitespace-nowrap mr-3">เลือกร้าน</label>'
    + '<select id="deep-comp-select" onchange="selectDeepComp(this.value)" class="text-sm px-4 py-2 rounded-xl border font-medium" style="background:var(--card);color:var(--text);border-color:var(--card-border)">'
    + opts + '</select></div>'
    + '<div id="deep-comp-detail"></div>';
  if (!selectedDeepComp && comps.length) selectedDeepComp = comps[0].id;
  renderDeepCompDetail();
}}

function renderDeepCompDetail() {{
  var comp = INTEL.find(function(x) {{ return x.id === selectedDeepComp; }});
  var el = document.getElementById('deep-comp-detail');
  if (!comp || !el) return;
  var st = comp.social_trend || {{}};
  var pricing = comp.pricing || {{}};
  var priceRows = [];
  var pkeys = ['espresso','americano','latte','cappuccino','cold_brew','frappe','matcha','signature_drink','food'];
  var pLabels = {{'espresso':'เอสเปรสโซ','americano':'อเมริกาโน','latte':'ลาเต้','cappuccino':'คาปูชิโน','cold_brew':'Cold Brew','frappe':'Frappe','matcha':'มัทฉะ','signature_drink':'Signature Drink','food':'อาหาร/เบเกอรี่'}};
  pkeys.forEach(function(k) {{
    var v = pricing[k];
    if (v && v.price) priceRows.push([pLabels[k] || k, plainText(v.price + ' บาท' + (v.note ? ' (' + v.note + ')' : ''))]);
  }});
  (pricing.other || []).forEach(function(o) {{
    if (o.price) priceRows.push([o.name, plainText(o.price + ' บาท' + (o.note ? ' (' + o.note + ')' : ''))]);
  }});
  var engMap = {{high:'สูง',medium:'ปานกลาง',low:'ต่ำ'}};
  var sections = [
    {{ title:'📱 1. Social Presence', rows:[
      ['Platform หลัก', plainText(st.primary_platform)],
      ['ความถี่โพสต์', plainText(st.posting_frequency)],
      ['Engagement Level', plainText(engMap[st.engagement_level] || st.engagement_level)],
      ['ที่ตั้ง', plainText(comp.location)],
      ['เวลาทำการ', plainText(comp.hours)],
    ]}},
    {{ title:'🎬 2. Content Strategy', rows:[
      ['สไตล์ Content', bulletList(st.content_style, '🎨')],
      ['Tags', chipList(comp.tags)],
      ['รายละเอียด', bulletList(comp.detail, '📝')],
    ]}},
    {{ title:'💰 3. Pricing', rows: priceRows.length ? priceRows : [['', plainText('ไม่พบราคาสาธารณะ')]] }},
    {{ title:'🎯 4. Services & Positioning', rows:[
      ['จุดแข็ง', bulletList(comp.strengths, '✅')],
      ['โปรโมชัน', bulletList(comp.promotions, '🎁')],
      ['Relevance', plainText(comp.relevance)],
    ]}},
    {{ title:'⭐ 5. Reviews & Weaknesses', rows:[
      ['จุดอ่อน', bulletList(comp.weaknesses, '⚠️')],
      ['สรุป', bulletList(comp.summary, '💬')],
    ]}},
    {{ title:'🛵 6. Delivery & Food Apps', rows: comp.delivery ? [
      ['แอปหลัก', plainText(comp.delivery.primary_app)],
      ['แอปทั้งหมด', plainText((comp.delivery.apps || []).join(', '))],
      ['Peak Hours', plainText(comp.delivery.peak_hours)],
      ['โปรโมชัน', bulletList(comp.delivery.active_promos, '🎁')],
      ['หมายเหตุ', bulletList(comp.delivery.notes, '📌')],
    ] : [['', plainText('ยังไม่มีข้อมูล Delivery')]]}},
  ];
  el.innerHTML = sections.map(function(sec) {{
    var rowHtml = sec.rows.map(function(r) {{
      return '<tr><td class="px-4 py-2.5 text-xs font-semibold align-top w-36 whitespace-nowrap" style="color:var(--text-muted)">' + r[0] + '</td>'
           + '<td class="px-4 py-2.5 text-sm align-top" style="color:var(--text)">' + r[1] + '</td></tr>';
    }}).join('');
    return '<div class="rounded-2xl border shadow-sm mb-4 overflow-hidden" style="background:var(--card);border-color:var(--card-border)">'
      + '<div class="px-5 py-3 border-b font-bold text-sm" style="border-color:var(--card-border);color:var(--text)">' + sec.title + '</div>'
      + '<table class="w-full"><tbody>' + rowHtml + '</tbody></table>'
    + '</div>';
  }}).join('');
}}

function renderDeepTimeline() {{
  var el = document.getElementById('deep-content-timeline');
  if (!el) return;
  var typeColors = {{ new:'#ef4444', pricing:'#10b981', expand:'#6366f1', content:'#f59e0b', platform:'#0ea5e9' }};
  var items = COMPETITOR_EVENTS.map(function(ev) {{
    var col = typeColors[ev.type] || '#94a3b8';
    return '<div class="flex gap-4 pb-6">'
      + '<div class="flex flex-col items-center">'
        + '<div class="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-sm" style="background:' + col + '22;border:2px solid ' + col + '">' + ev.icon + '</div>'
        + '<div class="w-0.5 flex-1 mt-1" style="background:var(--card-border)"></div>'
      + '</div>'
      + '<div class="pb-1">'
        + '<div class="text-xs font-bold mb-0.5" style="color:' + col + '">' + ev.date + '</div>'
        + '<div class="text-sm font-semibold mb-0.5" style="color:var(--text)">' + ev.competitor + '</div>'
        + '<div class="text-sm" style="color:var(--text-muted)">' + ev.text + '</div>'
      + '</div>'
    + '</div>';
  }});
  el.innerHTML = '<div class="rounded-2xl border shadow-sm p-6" style="background:var(--card);border-color:var(--card-border)">'
    + '<h2 class="text-sm font-bold mb-6" style="color:var(--text)">Timeline เหตุการณ์สำคัญของคู่แข่ง</h2>'
    + '<div>' + items.join('') + '</div>'
  + '</div>';
}}

// ── Tracker ──────────────────────────────────────────────────
let currentTrackerPeriod = 'week';

function setTrackerPeriod(period) {{
  currentTrackerPeriod = period;
  ['week','month','year'].forEach(function(p) {{
    var btn = document.getElementById('trk-' + p);
    if (!btn) return;
    btn.classList.toggle('active', p === period);
  }});
  renderTrackerContent(period);
}}

function renderTrackerView() {{
  setTrackerPeriod(currentTrackerPeriod);
}}

function renderTrackerContent(period) {{
  const el = document.getElementById('tracker-content');
  if (!el) return;

  // ยังไม่มีข้อมูล
  if (!TRACKER || !TRACKER.period) {{
    el.innerHTML = `
      <div class="rounded-2xl p-10 text-center" style="background:var(--card);border:1px solid var(--card-border)">
        <div class="text-4xl mb-4">📊</div>
        <div class="text-lg font-bold mb-2" style="color:var(--text)">ยังไม่มีข้อมูลการติดตาม</div>
        <div class="text-sm" style="color:var(--text-muted)">รัน <code class="px-2 py-0.5 rounded" style="background:var(--nav-active)">/track-competitors</code> เพื่อเริ่มวิเคราะห์</div>
        <div class="mt-3 text-xs" style="color:var(--text-muted)">
          /track-competitors &nbsp;·&nbsp; /track-competitors --month &nbsp;·&nbsp; /track-competitors --year
        </div>
      </div>`;
    return;
  }}

  const data = TRACKER;
  const periodLabel = data.period_label || period;
  const fromDate = data.from_date || '';
  const toDate = data.to_date || '';
  const mkt = data.market_summary || {{}};
  const competitors = data.competitors || [];

  // Alert level colors
  const alertColor = {{ high: '#ef4444', medium: '#f59e0b', low: '#22c55e' }};
  const alertLabel = {{ high: '🔴 น่าจับตา', medium: '🟡 น่าสังเกต', low: '🟢 ปกติ' }};
  const activityColor = {{ high: '#ef4444', medium: '#f59e0b', low: '#64748b' }};

  // Summary KPI bar
  const kpiHtml = `
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
      ${{[
        ['🏆 Active สูงสุด', mkt.most_active || '—'],
        ['📢 โปรโมชันใหม่', (mkt.new_promotions_count || 0) + ' รายการ'],
        ['🛵 Delivery เปลี่ยน', (mkt.delivery_changes_count || 0) + ' ร้าน'],
        ['🔴 น่าจับตา', (mkt.alert_high || []).length + ' ร้าน'],
      ].map(([label, val]) => `
        <div class="rounded-2xl p-4" style="background:var(--card);border:1px solid var(--card-border)">
          <div class="text-xs mb-1" style="color:var(--text-muted)">${{label}}</div>
          <div class="font-bold text-base" style="color:var(--text)">${{val}}</div>
        </div>`).join('')}}
    </div>`;

  // Key insight
  const insightHtml = mkt.key_insight ? `
    <div class="rounded-2xl p-4 mb-6 flex items-start gap-3"
         style="background:var(--card);border:1.5px solid var(--card-border)">
      <span class="text-xl">💡</span>
      <div>
        <div class="text-xs font-bold mb-1" style="color:var(--text-muted)">KEY INSIGHT — ${{periodLabel}}</div>
        <div class="text-sm font-medium" style="color:var(--text)">${{mkt.key_insight}}</div>
      </div>
    </div>` : '';

  // Competitor cards
  const cardsHtml = competitors.map(comp => {{
    const al = comp.alert_level || 'low';
    const promos = comp.promotions || {{}};
    const content = comp.content || {{}};
    const delivery = comp.delivery || {{}};
    const pricing = comp.pricing_changes || [];

    const promosNew = (promos.new_this_period || []).map(p =>
      `<span class="inline-block text-xs px-2 py-0.5 rounded-full bg-orange-100 text-orange-700 mr-1 mb-1">${{p}}</span>`
    ).join('');
    const promosActive = (promos.active || []).filter(p => !(promos.new_this_period || []).includes(p)).map(p =>
      `<span class="inline-block text-xs px-2 py-0.5 rounded-full mr-1 mb-1" style="background:var(--nav-active);color:var(--text-muted)">${{p}}</span>`
    ).join('');
    const platformBadges = (content.platforms || []).map(p =>
      `<span class="inline-block text-xs px-2 py-0.5 rounded-full mr-1" style="background:var(--nav-active);color:var(--text)">${{p}}</span>`
    ).join('');
    const topics = (content.topics || []).map(t =>
      `<span class="inline-block text-xs px-2 py-0.5 rounded-full mr-1 mb-1 bg-blue-100 text-blue-700">${{t}}</span>`
    ).join('');

    return `
      <div class="rounded-2xl p-5 mb-4" style="background:var(--card);border:2px solid ${{alertColor[al] || 'var(--card-border)'}}20">
        <!-- Header -->
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2.5">
            ${{avatarHTML(logoIdForName(comp.name), comp.name, alertColor[al] || '#7a4a20', 38)}}
            <div class="font-bold text-base" style="color:var(--text)">${{comp.name}}</div>
            <span class="text-xs px-2 py-0.5 rounded-full font-semibold"
                  style="background:${{alertColor[al] || '#64748b'}}20;color:${{alertColor[al] || '#64748b'}}">${{alertLabel[al] || al}}</span>
          </div>
          <div class="text-xs px-3 py-1 rounded-full font-semibold"
               style="background:${{activityColor[comp.activity_level || 'low']}}15;color:${{activityColor[comp.activity_level || 'low']}}">
            Activity: ${{comp.activity_level || '—'}}
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Promotions -->
          <div class="rounded-xl p-3" style="background:var(--nav-active);border:1px solid var(--card-border)">
            <div class="text-xs font-bold mb-2" style="color:var(--text-muted)">📢 โปรโมชัน</div>
            ${{promosNew ? `<div class="mb-1"><span class="text-xs" style="color:var(--text-muted)">ใหม่:</span> ${{promosNew}}</div>` : ''}}
            ${{promosActive ? `<div><span class="text-xs" style="color:var(--text-muted)">active:</span> ${{promosActive}}</div>` : ''}}
            ${{!promosNew && !promosActive ? `<div class="text-xs" style="color:var(--text-muted)">ไม่มีโปรโมชัน</div>` : ''}}
          </div>

          <!-- Content -->
          <div class="rounded-xl p-3" style="background:var(--nav-active);border:1px solid var(--card-border)">
            <div class="text-xs font-bold mb-2" style="color:var(--text-muted)">🎬 Content</div>
            ${{platformBadges ? `<div class="mb-1">${{platformBadges}}</div>` : ''}}
            ${{topics ? `<div class="mb-1">${{topics}}</div>` : ''}}
            ${{content.estimated_posts ? `<div class="text-xs" style="color:var(--text-muted)">~${{content.estimated_posts}} โพสต์ช่วงนี้</div>` : ''}}
            ${{content.notable_content ? `<div class="text-xs mt-1" style="color:var(--text)"><span class="font-semibold">✨ คอนเทนต์เด่น</span><div class="mt-0.5">${{bulletList(content.notable_content, '✨')}}</div></div>` : ''}}
          </div>

          <!-- Delivery -->
          <div class="rounded-xl p-3" style="background:var(--nav-active);border:1px solid var(--card-border)">
            <div class="text-xs font-bold mb-2" style="color:var(--text-muted)">🛵 Delivery</div>
            ${{delivery.changed
              ? `<span class="text-xs px-2 py-0.5 rounded-full bg-orange-100 text-orange-700">เปลี่ยนแปลง</span>
                 <div class="text-xs mt-1" style="color:var(--text)">${{delivery.note || ''}}</div>`
              : `<div class="text-xs" style="color:var(--text-muted)">ไม่มีการเปลี่ยนแปลง</div>`}}
          </div>

          <!-- Pricing -->
          <div class="rounded-xl p-3" style="background:var(--nav-active);border:1px solid var(--card-border)">
            <div class="text-xs font-bold mb-2" style="color:var(--text-muted)">💰 ราคา</div>
            ${{pricing.length > 0
              ? pricing.map(p => `<div class="text-xs" style="color:var(--text)">${{p}}</div>`).join('')
              : `<div class="text-xs" style="color:var(--text-muted)">ไม่มีการเปลี่ยนแปลง</div>`}}
          </div>
        </div>

        <!-- Summary -->
        ${{comp.summary ? `
        <div class="mt-3 pt-3 text-sm" style="border-top:1px solid var(--card-border);color:var(--text)">
          <span class="font-semibold">💬 สรุป</span>
          <div class="mt-0.5">${{bulletList(comp.summary, '🔹')}}</div>
        </div>` : ''}}
      </div>`;
  }}).join('');

  const headerInfo = fromDate && toDate
    ? `<div class="text-xs mb-4" style="color:var(--text-muted)">${{fromDate}} — ${{toDate}} · ${{data.snapshot_compared ? 'เปรียบเทียบกับ snapshot ก่อนหน้า' : 'ข้อมูลจาก web search'}}</div>`
    : '';

  el.innerHTML = headerInfo + kpiHtml + insightHtml
    + (competitors.length === 0
        ? `<div class="text-center py-10 text-sm" style="color:var(--text-muted)">ไม่มีข้อมูลคู่แข่งใน period นี้</div>`
        : `<div class="text-sm font-bold mb-3" style="color:var(--text-muted)">รายละเอียดแต่ละร้าน (${{competitors.length}} ร้าน)</div>` + cardsHtml);
}}

// ── Update log / History ──
const LOG_CAT_LABEL = {{ platform: '📊 Platforms', intel: '🔍 Intelligence' }};
let currentLogTab = 'all';

function escapeHtml(s) {{
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}}

function renderIntelUpdateBadge() {{
  const el = document.getElementById('intel-update-badge');
  if (!el) return;
  const s = (UPDATE_SUMMARY && UPDATE_SUMMARY.intel) || {{ count: 0 }};
  if (!s.count) {{
    el.innerHTML = '<span style="color:var(--text-muted)">🕐 ยังไม่มีประวัติการอัปเดต Intelligence</span>'
      + ' <a href="#" onclick="showView(\\'view-updatelog\\');return false;">ดูบันทึกอัปเดต →</a>';
    return;
  }}
  el.innerHTML =
    '<span>🕐 อัปเดตล่าสุด:</span>'
    + '<span class="ub-date">' + escapeHtml(s.last_date_th) + ' ' + escapeHtml(s.last_time_th || '') + '</span>'
    + '<span class="ub-pill">🔄 ' + s.count + ' ครั้ง</span>'
    + '<a href="#" onclick="showView(\\'view-updatelog\\');return false;">ดูประวัติทั้งหมด →</a>';
}}

function setLogTab(tab) {{
  currentLogTab = tab;
  document.querySelectorAll('[id^=log-tab-]').forEach(b => b.classList.remove('active'));
  const btn = document.getElementById('log-tab-' + tab);
  if (btn) btn.classList.add('active');
  renderLogTimeline();
}}

function renderLogSummaryCards() {{
  const el = document.getElementById('log-summary-cards');
  if (!el) return;
  const mk = (label, s, accent) => {{
    s = s || {{ count: 0 }};
    const sub = s.count
      ? ('ล่าสุด ' + escapeHtml(s.last_date_th) + ' ' + escapeHtml(s.last_time_th || ''))
      : 'ยังไม่มีการอัปเดต';
    return '<div class="log-card">'
      + '<div class="lc-label">' + label + '</div>'
      + '<div class="lc-count" style="color:' + accent + '">' + (s.count || 0)
      + ' <span style="font-size:1rem;font-weight:700;color:var(--text-muted)">ครั้ง</span></div>'
      + '<div class="lc-sub">' + sub + '</div></div>';
  }};
  el.innerHTML =
      mk('📊 Platforms', UPDATE_SUMMARY.platform, '#3b82f6')
    + mk('🔍 Intelligence', UPDATE_SUMMARY.intel, '#f59e0b')
    + mk('📈 รวมทั้งหมด', UPDATE_SUMMARY.all, '#10b981');
}}

function renderLogTimeline() {{
  const el = document.getElementById('log-timeline');
  if (!el) return;
  let items = UPDATE_LOG || [];
  if (currentLogTab !== 'all') items = items.filter(e => e.category === currentLogTab);
  if (!items.length) {{
    el.innerHTML = '<div class="text-center py-10" style="color:var(--text-muted)">ยังไม่มีรายการในหมวดนี้</div>';
    return;
  }}
  el.innerHTML = items.map(e => {{
    const cat = e.category === 'platform' ? 'platform' : 'intel';
    const cnt = (e.count != null) ? (' · ' + e.count) : '';
    const scope = e.scope ? (' <span style="color:var(--text-muted)">(' + escapeHtml(e.scope) + ')</span>') : '';
    const details = (e.details || []).map(d =>
      '<div class="log-detail">' + escapeHtml(d) + '</div>').join('');
    return '<div class="log-item">'
      + '<div class="log-dot ' + cat + '"></div>'
      + '<div style="flex:1;min-width:0">'
        + '<div style="font-size:.72rem;color:var(--text-muted);margin-bottom:3px">'
          + escapeHtml(e.date_th) + ' · ' + escapeHtml(e.time_th || '') + '</div>'
        + '<div style="font-size:.9rem;color:var(--text)">'
          + '<span class="log-cat ' + cat + '">' + (LOG_CAT_LABEL[cat] || cat) + '</span>'
          + '<span style="font-weight:600">' + escapeHtml(e.summary) + '</span>'
          + scope + cnt + '</div>'
        + details
      + '</div></div>';
  }}).join('');
}}

function renderUpdateLog() {{
  renderLogSummaryCards();
  renderLogTimeline();
}}

// ── ต้นทุนเครื่องดื่ม (Drink costs + editor) ──
var DC_CH = ['store', 'lineman', 'shoppee', 'grab'];
var DC_CH_FALLBACK = {{ store: 'หน้าร้าน', lineman: 'Lineman', shoppee: 'Shoppee', grab: 'Grab' }};
var DC_CATS = ['signature', 'coffee', 'tea', 'milk', 'soda'];
var DC_CAT_LABEL = {{ signature: 'Signature', coffee: 'Coffee', tea: 'Tea', milk: 'Milk', soda: 'Soda' }};
var DC_CAT_ICON = {{ signature: '⭐', coffee: '☕', tea: '🍵', milk: '🥛', soda: '🥤' }};
var DC_LS_KEY = 'pengtang_drink_costs_v1';

// จัดหมวดอัตโนมัติจากชื่อ (รองรับข้อมูลเก่า 'กาแฟ'/'ชา/นม' และเมนูใหม่)
function dcAutoCat(name) {{
  var n = (name || '').toLowerCase();
  if (n.indexOf('soda') >= 0 || name.indexOf('โซดา') >= 0) return 'soda';
  var coffeeKw = ['อเมริกาโน่', 'เอสเพรสโซ่', 'เอสเปรสโซ่', 'ลาเต้', 'มอคค่า', 'คาปู', 'กาแฟ', 'เอสเย็น', 'ช็อต'];
  for (var i = 0; i < coffeeKw.length; i++) if (name.indexOf(coffeeKw[i]) >= 0) return 'coffee';
  if (name.indexOf('ชา') >= 0 || name.indexOf('มัทฉะ') >= 0 || n.indexOf('matcha') >= 0) return 'tea';
  if (name.indexOf('นม') >= 0 || name.indexOf('โกโก้') >= 0 || n.indexOf('milk') >= 0 || n.indexOf('cocoa') >= 0) return 'milk';
  return 'coffee';
}}
function dcCategoryOf(m) {{ return (DC_CAT_LABEL[m.category]) ? m.category : dcAutoCat(m.name); }}

// จัดกลุ่มวัตถุดิบ (สำหรับ dropdown ค้นหา)
var DC_IGROUPS = [['bean', 'เมล็ดกาแฟ'], ['milk', 'นม'], ['cocoa', 'โกโก้'], ['tea', 'ผงชา'], ['sweet', 'ความหวาน'], ['syrup', 'ไซรัป'], ['pack', 'บรรจุภัณฑ์'], ['other', 'อื่นๆ']];
function dcIngGroup(name) {{
  var n = (name || '').toLowerCase();
  if (/แก้ว|ฝา|หลอด|ถุง|กระดาษ/.test(name)) return 'pack';
  if (/กาแฟ|เอสเพรสโซ|เอสเปรสโซ/.test(name) || /coffee|espresso/.test(n)) return 'bean';
  if (/โกโก้/.test(name) || /cho|tulip|cocoa/.test(n)) return 'cocoa';
  if (/ชา|มัทฉะ/.test(name) || /matcha/.test(n)) return 'tea';
  if (/ข้นหวาน|น้ำตาล|น้ำผึ้ง|น้ำเชื่อม|มิตรผล/.test(name) || /honey/.test(n)) return 'sweet';
  if (/นมสด|นมข้น|นมจืด|ฟองนม|ครีม|คอฟฟี่เมจ/.test(name) || /mmilk|milk|falcon|oat/.test(n)) return 'milk';
  if (/มังกรบิน/.test(name) || /monin|syrup|sunquick/.test(n)) return 'syrup';
  return 'other';
}}
function dcMenuImage(m) {{ return (m.image && m.image.trim()) ? m.image.trim() : ('assets/drink-icons/' + dcCategoryOf(m) + '.svg'); }}
function dcThumb(m, size) {{
  size = size || 42;
  var cat = dcCategoryOf(m);
  return '<span class="dc-thumb" style="width:' + size + 'px;height:' + size + 'px">'
    + '<span class="dc-thumb-fb">' + (DC_CAT_ICON[cat] || '🥤') + '</span>'
    + '<img src="' + escapeHtml(dcMenuImage(m)) + '" alt="" loading="lazy" onerror="this.style.display=\\'none\\'"></span>';
}}

// ── สถานะปลดล็อกกลาง (sessionStorage: คงอยู่ตอนรีเฟรช, หายเมื่อปิดแท็บ) ──
function saIsUnlocked() {{ return sessionStorage.getItem('pengtang_unlocked')==='1'; }}
function saUpdateChip() {{
  var wrap=document.getElementById('sa-lock-wrap');
  if (!wrap) return;
  wrap.style.display=saIsUnlocked()?'':'none';
}}
function saUnlock() {{ sessionStorage.setItem('pengtang_unlocked','1'); saUpdateChip(); }}
function saLock() {{
  sessionStorage.removeItem('pengtang_unlocked');
  dcEdit=false;
  try {{ dcCloseModal(); }} catch(e) {{}}
  saUpdateChip();
  renderActiveBackbar();
}}
function renderActiveBackbar() {{
  var viewMap={{
    'view-cost-drinks':renderDrinkCosts,
    'view-bb-stock':renderStockView,
    'view-bb-varfix':renderVarfixView,
    'view-bb-posimport':renderPosImportView
  }};
  Object.keys(viewMap).forEach(function(id) {{
    var v=document.getElementById(id);
    if (v&&v.classList.contains('active')) {{ try {{ viewMap[id](); }} catch(e) {{}} }}
  }});
}}

var dcChannel = 'store', dcSort = 'margin', dcEdit = saIsUnlocked();
var DCS = null;       // working state {{source, assumptions, catalog, menus}}
var dcDraft = null;   // เมนูที่กำลังแก้ใน modal
var dcPolarChart = null; // Chart.js instance (destroy ก่อน re-create เสมอ)
var DC_CH_COLORS = {{ store: '#00085f', lineman: '#648a23', shoppee: '#f86612', grab: '#056837' }};

// ---- state ----
function dcClone(o) {{ return JSON.parse(JSON.stringify(o || {{}})); }}
function dcDefaults() {{
  return {{ overhead: 0.30, margin_factor: 1.6, fixed_cost_monthly: 30000, days_per_month: 30,
    channels: {{ store: {{label:'หน้าร้าน',gp:0,vat:0}}, lineman: {{label:'Lineman',gp:0.30,vat:0.07}}, shoppee: {{label:'Shoppee',gp:0.32,vat:0.07}}, grab: {{label:'Grab',gp:0.251,vat:0.07}} }} }};
}}
function dcNormalize(s) {{
  s = s || {{}};
  s.catalog = s.catalog || {{}};
  s.menus = s.menus || [];
  s.assumptions = Object.assign(dcDefaults(), s.assumptions || {{}});
  s.assumptions.channels = Object.assign(dcDefaults().channels, s.assumptions.channels || {{}});
  s.purchases = s.purchases || [];
  s.sales = s.sales || [];
  s.stock = s.stock || {{}};
  if (s.stock.threshold_pct == null) s.stock.threshold_pct = 60;
  s.stock.par = s.stock.par || {{}};
  s.stock.images = s.stock.images || {{}};
  s.expenses = s.expenses || [];
  s.expense_slips = s.expense_slips || {{}};
  // posLast เก็บเฉพาะใน browser — Sheet sync ไม่มีฟิลด์นี้
  if (s.posLast === undefined) s.posLast = null;
  // Quest & Achievement — seed สำหรับ user ใหม่ที่ยังไม่มีข้อมูล
  if (s.quests === undefined) s.quests = dcClone(DEFAULT_QUESTS_SEED);
  if (s.achievements === undefined) s.achievements = dcClone(DEFAULT_ACHS_SEED);
  if (s.plans === undefined) s.plans = {{ daily: [], weekly: [], monthly: [] }};
  if (s.loops === undefined) s.loops = [];
  if (s.questLog === undefined) s.questLog = {{}};
  if (s.questHistory === undefined) s.questHistory = [];
  if (s.questMeta === undefined) s.questMeta = {{ startDate: '2026-05-31', totalDays: 90, targetOpenDay: 30 }};
  return s;
}}
function dcLoadState() {{
  try {{ var raw = localStorage.getItem(DC_LS_KEY); if (raw) {{ DCS = dcNormalize(JSON.parse(raw)); return; }} }} catch (e) {{}}
  DCS = dcNormalize(dcClone(DRINK_COSTS));
}}
function dcSave() {{ try {{ localStorage.setItem(DC_LS_KEY, JSON.stringify(DCS)); }} catch (e) {{}} }}
function dcResetToFile() {{
  if (!confirm('คืนค่ากลับเป็นข้อมูลจากไฟล์ Excel? การแก้ไขในเครื่องนี้จะถูกล้างทั้งหมด')) return;
  try {{ localStorage.removeItem(DC_LS_KEY); }} catch (e) {{}}
  DCS = dcNormalize(dcClone(DRINK_COSTS));
  renderDrinkCosts();
  showToast('คืนค่าจากไฟล์ Excel แล้ว');
}}
function dcChLabel(ch) {{ var c = DCS.assumptions.channels[ch]; return (c && c.label) || DC_CH_FALLBACK[ch] || ch; }}

// ---- compute ----
function dcUnitCost(name) {{ var c = DCS.catalog[name]; if (!c) return 0; if (c.unit_cost != null) return c.unit_cost; return c.qty ? c.price / c.qty : 0; }}
function dcMaterial(m) {{ var s = 0; (m.recipe || []).forEach(function(l) {{ s += dcUnitCost(l.ing) * (parseFloat(l.qty) || 0); }}); return s; }}
function dcCostCup(m) {{
  if (m.recipe && m.recipe.length) return dcMaterial(m) * (1 + DCS.assumptions.overhead);
  return (m.seed_cost_cup != null ? m.seed_cost_cup : 0);
}}
function dcChannelCalc(m, ch) {{
  var price = m.prices ? m.prices[ch] : null;
  if (price == null || price === '') return null;
  price = parseFloat(price); if (isNaN(price)) return null;
  var cc = dcCostCup(m);
  var p = DCS.assumptions.channels[ch] || {{gp:0,vat:0}};
  var cost = cc + price * (p.gp || 0) + price * (p.vat || 0);
  var profit = price - cost;
  return {{ price: price, cost: cost, profit: profit, margin: price ? profit / price * 100 : null }};
}}
function dcSuggestPrice(m) {{ return Math.round(dcCostCup(m) * (DCS.assumptions.margin_factor || 1.6)); }}
function dcBreakeven(m) {{
  var st = dcChannelCalc(m, 'store');
  if (!st || st.profit <= 0) return null;
  var fixed = DCS.assumptions.fixed_cost_monthly || 0, days = DCS.assumptions.days_per_month || 30;
  var cm = Math.ceil(fixed / st.profit);
  return {{ cups_month: cm, cups_day: Math.ceil(cm / days) }};
}}
function dcUsedBy(name) {{ return DCS.menus.filter(function(m) {{ return (m.recipe||[]).some(function(l) {{ return l.ing === name; }}); }}).length; }}

// ---- format ----
function dcMoney(v) {{ return (v == null) ? '–' : Number(v).toLocaleString('th-TH', {{maximumFractionDigits: 0}}); }}
function dcF1(v) {{ return (v == null) ? '–' : Number(v).toLocaleString('th-TH', {{minimumFractionDigits: 1, maximumFractionDigits: 1}}); }}
function dcMargCol(m) {{ if (m == null) return 'var(--text-muted)'; if (m >= 60) return 'var(--dc-profit)'; if (m >= 45) return 'var(--ov-accent-ink)'; return 'var(--dc-warn)'; }}

function dcSetChannel(ch) {{ dcChannel = ch; renderDrinkCosts(); }}
function dcSetSort(s) {{ dcSort = s; renderDrinkCosts(); }}
function dcToggleEdit() {{ dcEdit = !dcEdit; renderDrinkCosts(); }}
// ล็อกโหมดแก้ไขด้วยรหัส (soft lock — เก็บเป็น SHA-256 ไม่ใช่ข้อความจริง)
var DC_EDIT_HASH = '7faf99673e7b404b5f83cd7ceb3b3093f65590e0545309f7efad769994f5b541';
function dcSha256(s) {{
  return crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)).then(function(buf) {{
    return Array.prototype.map.call(new Uint8Array(buf), function(b) {{ return ('0' + b.toString(16)).slice(-2); }}).join('');
  }});
}}
var dcPwOnOk = null;
function dcRequestEdit() {{
  if (dcEdit) {{ saLock(); return; }}
  dcOpenPwModal('🔒 ปลดล็อกการแก้ไข', 'ใส่รหัสเพื่อแก้ไขเมนู / สูตร', function() {{ dcEdit=true; saUnlock(); renderDrinkCosts(); showToast('ปลดล็อกแล้ว ✓'); }});
}}
// เรียกจากเมนู "นำเข้าข้อมูล" — ต้องใส่รหัสก่อนเข้า
function requireImportAccess() {{
  if (saIsUnlocked()) {{ showView('view-import'); return; }}
  dcOpenPwModal('🔒 เข้าระบบนำเข้าข้อมูล', 'ใส่รหัสเพื่อเข้าระบบนำเข้าข้อมูล', function() {{ saUnlock(); showView('view-import'); }});
}}
function dcOpenPwModal(title, label, onOk) {{
  dcPwOnOk = onOk || null;
  var html = '<div class="dc-modal-head"><h3>' + (title || '🔒 ใส่รหัส') + '</h3><button class="dc-x" onclick="dcCloseModal()" aria-label="ปิด">✕</button></div>'
    + '<div class="dc-modal-scroll">'
    + '<div class="dc-field" style="margin-bottom:6px"><label>' + (label || 'ใส่รหัสผ่าน') + '</label>'
    + '<div class="dc-pwwrap"><input class="dc-inp" id="dc-pw" type="password" placeholder="รหัสผ่าน" autocomplete="off" onkeydown="dcPwKey(event)" oninput="dcPwClearErr()">'
    + '<button class="dc-eye" type="button" id="dc-eye" onclick="dcPwToggle()" aria-label="แสดง/ซ่อนรหัส">👁</button></div>'
    + '<div class="dc-pwerr" id="dc-pwerr">รหัสไม่ถูกต้อง ลองใหม่อีกครั้ง</div></div>'
    + '</div>'
    + '<div class="dc-modal-foot"><span class="spacer"></span><button class="dc-btn" onclick="dcCloseModal()">ยกเลิก</button><button class="dc-btn primary" onclick="dcPwSubmit()">ปลดล็อก</button></div>';
  dcSetModalBody(html);
  setTimeout(function() {{ var i = document.getElementById('dc-pw'); if (i) i.focus(); }}, 60);
}}
function dcPwToggle() {{
  var i = document.getElementById('dc-pw'), e = document.getElementById('dc-eye');
  if (!i) return;
  if (i.type === 'password') {{ i.type = 'text'; if (e) e.textContent = '🙈'; }} else {{ i.type = 'password'; if (e) e.textContent = '👁'; }}
  i.focus();
}}
function dcPwClearErr() {{ var e = document.getElementById('dc-pwerr'); if (e) e.classList.remove('show'); }}
function dcPwKey(e) {{ if (e.key === 'Enter') {{ e.preventDefault(); dcPwSubmit(); }} }}
function dcPwSubmit() {{
  var i = document.getElementById('dc-pw'); if (!i) return;
  if (!window.crypto || !crypto.subtle) {{ showToast('เบราว์เซอร์ไม่รองรับการตรวจรหัส'); return; }}
  dcSha256((i.value || '').trim()).then(function(h) {{
    if (h === DC_EDIT_HASH) {{ var cb = dcPwOnOk; dcPwOnOk = null; dcCloseModal(); if (cb) cb(); }}
    else {{ var e = document.getElementById('dc-pwerr'); if (e) e.classList.add('show'); i.value = ''; i.focus(); }}
  }});
}}
function dcToggle(el) {{ var o = el.classList.toggle('open'); el.setAttribute('aria-expanded', o ? 'true' : 'false'); }}
function dcRowKey(e, el) {{ if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); dcToggle(el); }} }}

// หุบ/กางหมวด (จำสถานะ)
var dcCollapsed = null;
function dcLoadCollapsed() {{ if (dcCollapsed) return; try {{ dcCollapsed = JSON.parse(localStorage.getItem('pengtang_dc_collapsed') || '{{}}'); }} catch (e) {{ dcCollapsed = {{}}; }} if (!dcCollapsed) dcCollapsed = {{}}; }}
function dcSaveCollapsed() {{ try {{ localStorage.setItem('pengtang_dc_collapsed', JSON.stringify(dcCollapsed)); }} catch (e) {{}} }}
function dcToggleCat(cat) {{
  dcLoadCollapsed(); dcCollapsed[cat] = !dcCollapsed[cat]; dcSaveCollapsed();
  var body = document.querySelector('#dc-root .dc-group-body[data-cat="' + cat + '"]');
  var title = document.querySelector('#dc-root .dc-group-title[data-cat="' + cat + '"]');
  if (body) body.classList.toggle('dc-collapsed', dcCollapsed[cat]);
  if (title) {{ title.classList.toggle('dc-collapsed', dcCollapsed[cat]); title.setAttribute('aria-expanded', dcCollapsed[cat] ? 'false' : 'true'); }}
}}
function dcCatKey(e, cat) {{ if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); dcToggleCat(cat); }} }}
function dcCollapseAll(collapse) {{ dcLoadCollapsed(); DC_CATS.forEach(function(c) {{ dcCollapsed[c] = collapse; }}); dcSaveCollapsed(); renderDrinkCosts(); }}

function dcStats(menus, ch) {{
  var arr = [];
  menus.forEach(function(m) {{ var c = dcChannelCalc(m, ch); if (c && c.margin != null) arr.push({{m: m, c: c}}); }});
  var margins = arr.map(function(x) {{ return x.c.margin; }});
  var avg = margins.length ? margins.reduce(function(a, b) {{ return a + b; }}, 0) / margins.length : null;
  var costs = menus.map(function(m) {{ return dcCostCup(m); }}).filter(function(v) {{ return v > 0; }});
  var avgCost = costs.length ? costs.reduce(function(a, b) {{ return a + b; }}, 0) / costs.length : null;
  var sorted = arr.slice().sort(function(a, b) {{ return b.c.margin - a.c.margin; }});
  return {{ avg: avg, avgCost: avgCost, best: sorted[0], worst: sorted[sorted.length - 1] }};
}}

function dcEmpty() {{
  return '<div class="ov-tile ov-soon">'
    + '<div class="ov-soon-emoji">🧮</div>'
    + '<div class="ov-soon-title">ยังไม่มีข้อมูลต้นทุน</div>'
    + '<div class="ov-soon-sub">เริ่มจากกด <b>เพิ่มเมนู</b> หรือวางไฟล์ Excel ที่ import-data/cost/ แล้วรัน parse_drink_costs.py</div>'
    + '<div style="margin-top:18px"><button class="dc-btn primary" onclick="dcOpenMenu(null)">+ เพิ่มเมนูแรก</button></div>'
    + '</div>';
}}

function renderDrinkCosts() {{
  var root = document.getElementById('dc-root');
  if (!root) return;
  if (!DCS) dcLoadState();
  if (dcGsUrl() && !dcSyncedSession) {{ dcSyncedSession = true; dcSyncPull(true); }}
  // อัปเดตวันที่ใน bb-status-bar
  var bbEl = document.getElementById('bb-updated-cost');
  if (bbEl && DCS.parsed_at) {{
    try {{
      var d = new Date(DCS.parsed_at);
      bbEl.textContent = d.toLocaleDateString('th-TH', {{year:'numeric', month:'short', day:'numeric'}});
    }} catch(e) {{ bbEl.textContent = DCS.parsed_at.slice(0,10); }}
  }}
  var menus = DCS.menus;
  var ch = dcChannel;
  var fixed = DCS.assumptions.fixed_cost_monthly || 0;
  var connected = !!dcGsUrl();

  var h = [];

  // meta
  var withRec = menus.filter(function(m) {{ return m.recipe && m.recipe.length; }}).length;
  h.push('<div class="dc-meta">'
    + '<span class="src">📄 ' + escapeHtml(DCS.source || 'ต้นทุนเครื่องดื่ม') + '</span>'
    + '<span class="note">' + menus.length + ' เมนู · ' + withRec + ' เมนูมีสูตร · คลังวัตถุดิบ ' + Object.keys(DCS.catalog).length + ' รายการ</span>'
    + '<span class="note">ต้นทุน/แก้ว = วัตถุดิบ +' + Math.round(DCS.assumptions.overhead * 100) + '% (ต้นทุนแฝง)</span>'
    + (connected ? '<span class="note" style="color:var(--dc-profit);font-weight:700">🟢 เชื่อม Google Sheet</span>' : '<span class="note">⚪ เก็บในเครื่อง (ยังไม่เชื่อม Sheet)</span>')
    + '</div>');

  // toolbar (edit controls)
  if (!dcEdit) {{
    h.push('<div class="dc-toolbar"><button class="dc-btn primary" onclick="dcRequestEdit()">🔒 แก้ไขเมนู / สูตร</button></div>');
  }} else {{
    h.push('<div class="dc-toolbar">'
      + '<button class="dc-btn primary" onclick="dcOpenMenu(null)">+ เพิ่มเมนู</button>'
      + '<button class="dc-btn" onclick="dcOpenCatalog()">🧂 คลังวัตถุดิบ</button>'
      + '<button class="dc-btn" onclick="dcOpenConnect()">🔗 ' + (connected ? 'Google Sheet ✓' : 'เชื่อม Sheet') + '</button>'
      + (connected ? '<button class="dc-btn" onclick="dcSyncPull()">🔄 ซิงก์จาก Sheet</button>' : '')
      + '<button class="dc-btn" onclick="dcExport()">⬇️ Export</button>'
      + '<button class="dc-btn" onclick="dcImportClick()">⬆️ นำเข้า</button>'
      + '<button class="dc-btn ghost danger" onclick="dcResetToFile()">↺ คืนค่าจากไฟล์</button>'
      + '<button class="dc-btn" onclick="dcToggleEdit()">✓ เสร็จสิ้น</button>'
      + '<input type="file" id="dc-import-file" accept="application/json,.json" style="display:none" onchange="dcImportFile(this)">'
      + '<span class="dc-edithint">' + (connected ? 'แก้ในเว็บหรือใน Sheet ก็ได้ ซิงก์หากันอัตโนมัติ' : 'แก้ไขบันทึกในเบราว์เซอร์นี้ · เชื่อม Sheet เพื่อซิงก์สองทาง') + '</span>'
      + '</div>');
    h.push('<div class="dc-note">'
      + '<div class="dc-note-h">💡 วิธีเปลี่ยนรูปเมนู (กันลืม)</div>'
      + '<div>กดปุ่ม ✏️ ที่เมนู → วาง URL รูปในช่อง <b>“รูปภาพ (URL)”</b> → กดบันทึกเมนู (เว้นว่าง = ใช้ไอคอนหมวดอัตโนมัติ)</div>'
      + '<div class="dc-note-sub">ถ้าเชื่อม Google Sheet ไว้ การแก้จะเขียนกลับ Sheet อัตโนมัติ · <b>ครั้งแรกหลังอัปเดตระบบ</b> ต้องไปที่ Apps Script → Deploy → <b>New version</b> 1 ครั้ง เพื่อให้คอลัมน์ “รูปภาพ” ซิงก์ได้ (ดูวิธีใน google-sheets/README.md)</div>'
      + '</div>');
  }}

  if (!menus.length) {{ root.innerHTML = h.join('') + dcEmpty(); return; }}

  // สถิติ 5 ตัว (ใต้ Polar chart)
  var stats = dcStats(menus, ch);
  var k = [];
  k.push('<div class="dc-stat hero"><span class="dc-st-lab">🥤 จำนวนเมนู</span><span class="dc-st-val">' + menus.length + ' <small>เมนู</small></span><span class="dc-st-sub">' + withRec + ' มีสูตรแล้ว</span></div>');
  k.push('<div class="dc-stat"><span class="dc-st-lab">📈 กำไรเฉลี่ย · ' + escapeHtml(dcChLabel(ch)) + '</span><span class="dc-st-val" style="color:' + dcMargCol(stats.avg) + '">' + dcF1(stats.avg) + '<small>%</small></span><span class="dc-st-sub">เฉลี่ยทุกเมนู</span></div>');
  k.push('<div class="dc-stat"><span class="dc-st-lab">💧 ต้นทุนเฉลี่ย/แก้ว</span><span class="dc-st-val">' + dcF1(stats.avgCost) + '<small>฿</small></span><span class="dc-st-sub">วัตถุดิบ + ต้นทุนแฝง</span></div>');
  k.push(stats.best
    ? '<div class="dc-stat"><span class="dc-st-lab">🏆 กำไรดีสุด</span><span class="dc-st-val" style="color:var(--dc-profit)">' + dcF1(stats.best.c.margin) + '<small>%</small></span><span class="dc-st-sub">' + escapeHtml(stats.best.m.name) + '</span></div>'
    : '<div class="dc-stat"><span class="dc-st-lab">🏆 กำไรดีสุด</span><span class="dc-st-val" style="color:var(--text-muted)">–</span></div>');
  k.push(stats.worst
    ? '<div class="dc-stat"><span class="dc-st-lab">⚠️ ต้องระวัง</span><span class="dc-st-val" style="color:var(--dc-warn)">' + dcF1(stats.worst.c.margin) + '<small>%</small></span><span class="dc-st-sub">' + escapeHtml(stats.worst.m.name) + '</span></div>'
    : '<div class="dc-stat"><span class="dc-st-lab">⚠️ ต้องระวัง</span><span class="dc-st-val" style="color:var(--text-muted)">–</span></div>');

  // controls (เหลือแค่ เรียงตาม + หุบ/กาง — ช่องทางย้ายไปคลิกกลีบ chart)
  var sortDefs = [['margin', 'กำไร %'], ['profit', 'กำไร ฿'], ['cost', 'ต้นทุน/แก้ว']];
  var sortBtns = sortDefs.map(function(s) {{ return '<button class="ov-mtab' + (s[0] === dcSort ? ' active' : '') + '" onclick="dcSetSort(\\'' + s[0] + '\\')">' + s[1] + '</button>'; }}).join('');

  // sticky header: Polar chart (กึ่งกลาง) → stats แถวเต็ม → controls
  h.push('<div class="dc-sticky-header">'
    + '<div class="dc-polar-wrap">'
    + '<div class="dc-polar-canvas-wrap"><canvas id="dc-polar"></canvas></div>'
    + '</div>'
    + '<div class="dc-stats-row">' + k.join('') + '</div>'
    + '<div class="dc-controls">'
    + '<div class="grp"><span class="lbl">เรียงตาม</span>' + sortBtns + '</div>'
    + '<div class="grp"><button class="ov-mtab" onclick="dcCollapseAll(true)">⊟ หุบทั้งหมด</button><button class="ov-mtab" onclick="dcCollapseAll(false)">⊞ กางทั้งหมด</button></div>'
    + '</div>'
    + '</div>');

  // เริ่ม scroll container ของรายการ
  h.push('<div class="dc-list-scroll">');

  // max ราคา สำหรับสเกลแถบ
  var maxP = 1;
  menus.forEach(function(m) {{ var c = dcChannelCalc(m, ch); if (c && c.price > maxP) maxP = c.price; }});

  // sort key
  function key(m) {{
    if (dcSort === 'cost') return dcCostCup(m) || -1;
    var c = dcChannelCalc(m, ch);
    if (!c) return -Infinity;
    return dcSort === 'profit' ? c.profit : (c.margin == null ? -Infinity : c.margin);
  }}

  dcLoadCollapsed();
  DC_CATS.forEach(function(cat) {{
    var arr = menus.filter(function(m) {{ return dcCategoryOf(m) === cat; }}).sort(function(a, b) {{ return key(b) - key(a); }});
    var col = !!dcCollapsed[cat];
    h.push('<div class="dc-group-title' + (col ? ' dc-collapsed' : '') + '" data-cat="' + cat + '" role="button" tabindex="0" aria-expanded="' + (col ? 'false' : 'true') + '" onclick="dcToggleCat(\\'' + cat + '\\')" onkeydown="dcCatKey(event,\\'' + cat + '\\')">'
      + '<span class="dc-chev">▾</span> ' + (DC_CAT_ICON[cat] || '') + ' ' + DC_CAT_LABEL[cat] + ' <span class="ct">' + arr.length + ' เมนู</span>'
      + (dcEdit ? '<button class="dc-addcat" onclick="event.stopPropagation(); dcOpenMenu(null,\\'' + cat + '\\')">+ เพิ่ม</button>' : '') + '</div>');
    h.push('<div class="dc-group-body' + (col ? ' dc-collapsed' : '') + '" data-cat="' + cat + '">');
    if (!arr.length) {{ h.push('<div class="dc-empty-cat">— ยังไม่มีเมนูในหมวดนี้ —</div>'); }}
    else {{
      h.push('<div class="dc-list">');
      arr.forEach(function(m, idx) {{ h.push(dcRow(m, idx + 1, ch, maxP, fixed)); }});
      h.push('</div>');
    }}
    h.push('</div>');
  }});

  h.push('</div>'); // ปิด dc-list-scroll

  root.innerHTML = h.join('');
  requestAnimationFrame(function() {{
    root.querySelectorAll('[data-w]').forEach(function(el) {{ el.style.width = el.getAttribute('data-w'); }});
    dcRenderPolar(menus);
  }});
}}

function dcRenderPolar(menus) {{
  var canvas = document.getElementById('dc-polar');
  if (!canvas || typeof Chart === 'undefined') return;
  if (dcPolarChart) {{ dcPolarChart.destroy(); dcPolarChart = null; }}
  var textColor = getComputedStyle(document.documentElement).getPropertyValue('--text').trim() || '#1c160f';
  var mutedColor = getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim() || '#6b7280';
  var gridColor = 'rgba(128,128,128,0.18)';
  var labels = DC_CH.map(function(ch) {{ return dcChLabel(ch); }});
  var realValues = DC_CH.map(function(ch) {{ var s = dcStats(menus, ch); return s.avg; }});
  var displayValues = realValues.map(function(v) {{ return (v != null && v > 0) ? v : 0; }});
  var colors = DC_CH.map(function(ch) {{ return DC_CH_COLORS[ch] || '#888'; }});
  // กลีบ active = ทึบ + border ขาว; กลีบอื่น = จาง
  var bgColors = DC_CH.map(function(ch, i) {{
    return ch === dcChannel ? colors[i] + 'ee' : colors[i] + '44';
  }});
  var borderColors = DC_CH.map(function(ch, i) {{
    return ch === dcChannel ? textColor : colors[i] + '88';
  }});
  var borderWidths = DC_CH.map(function(ch) {{ return ch === dcChannel ? 3 : 1; }});
  dcPolarChart = new Chart(canvas, {{
    type: 'polarArea',
    data: {{
      labels: labels,
      datasets: [{{ data: displayValues, backgroundColor: bgColors,
        borderColor: borderColors, borderWidth: borderWidths }}]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      onClick: function(event, elements) {{
        if (!elements || !elements.length) return;
        var ch = DC_CH[elements[0].index];
        if (ch) dcSetChannel(ch);
      }},
      onHover: function(event, elements) {{
        if (event.native) event.native.target.style.cursor = elements.length ? 'pointer' : 'default';
      }},
      plugins: {{
        legend: {{
          position: 'top',
          onClick: function(e, item) {{ var ch = DC_CH[item.index]; if (ch) dcSetChannel(ch); }},
          labels: {{ color: textColor, font: {{ size: 12, weight: '700' }}, padding: 16, boxWidth: 14,
            generateLabels: function(chart) {{
              var ds = chart.data.datasets[0];
              return chart.data.labels.map(function(label, i) {{
                var ch = DC_CH[i];
                return {{
                  text: label,
                  fillStyle: ds.backgroundColor[i],
                  strokeStyle: ds.borderColor[i],
                  lineWidth: ds.borderWidth[i],
                  fontColor: ch === dcChannel ? textColor : mutedColor,
                  hidden: false, index: i
                }};
              }});
            }}
          }}
        }},
        tooltip: {{
          callbacks: {{
            label: function(ctx) {{
              var real = realValues[ctx.dataIndex];
              var ch = DC_CH[ctx.dataIndex];
              var active = ch === dcChannel ? ' ✓' : '';
              return ' ' + labels[ctx.dataIndex] + active + ': ' + (real != null ? real.toFixed(1) : '–') + '%';
            }}
          }}
        }}
      }},
      scales: {{
        r: {{
          ticks: {{ color: mutedColor, font: {{ size: 9 }}, backdropColor: 'transparent', maxTicksLimit: 4 }},
          grid: {{ color: gridColor }},
          pointLabels: {{ display: false }}
        }}
      }}
    }}
  }});
}}

function dcRow(m, rank, ch, maxP, fixed) {{
  var c = dcChannelCalc(m, ch);
  var loss = c && c.profit < 0;
  var costW = c ? (c.cost / maxP * 100) : 0;
  var profitW = c ? (Math.max(c.profit, 0) / maxP * 100) : 0;

  var bar;
  if (c) {{
    bar = '<div class="dc-bar"><div class="dc-seg-cost" data-w="' + costW.toFixed(1) + '%"></div><div class="dc-seg-profit" data-w="' + profitW.toFixed(1) + '%"></div></div>'
      + '<div class="dc-barlabels"><span>ต้นทุน <b>' + dcMoney(c.cost) + '฿</b></span>'
      + '<span>' + (loss ? '<b style="color:var(--dc-warn)">ขาดทุน ' + dcMoney(c.profit) + '฿</b>' : 'กำไร <b style="color:var(--dc-profit)">' + dcMoney(c.profit) + '฿</b>') + '</span>'
      + '<span>ราคา <b>' + dcMoney(c.price) + '฿</b></span></div>';
  }} else {{
    bar = '<div class="dc-norec">ไม่มีราคาในช่องทาง ' + dcChLabel(ch) + '</div>';
  }}

  var figs = (c && c.margin != null)
    ? '<div class="dc-margin" style="color:' + dcMargCol(c.margin) + '">' + dcF1(c.margin) + '<small>%</small></div><div class="dc-profitline">กำไร <b>' + dcMoney(c.profit) + '฿</b>/แก้ว</div>'
    : '<div class="dc-margin" style="color:var(--text-muted)">–</div>';

  var hasRec = m.recipe && m.recipe.length;
  var acts = dcEdit
    ? '<span class="dc-rowacts"><button class="dc-iconbtn" title="แก้ไข" onclick="event.stopPropagation(); dcOpenMenu(\\'' + m.id + '\\')">✏️</button>'
      + '<button class="dc-iconbtn" title="ลบ" onclick="event.stopPropagation(); dcDeleteMenu(\\'' + m.id + '\\')">🗑️</button></span>'
    : '';
  var nameBlock = '<div style="min-width:0"><div class="dc-name">' + escapeHtml(m.name) + acts + '</div>'
    + (hasRec ? '' : '<div class="dc-norec">ยังไม่ได้ตั้งสูตร (ใช้ต้นทุนตั้งต้น)</div>') + '</div>';

  return '<div class="dc-row" tabindex="0" role="button" aria-expanded="false" onclick="dcToggle(this)" onkeydown="dcRowKey(event,this)">'
    + '<div class="dc-row-top">'
    + '<div class="dc-id"><span class="dc-rank">' + rank + '</span>' + dcThumb(m) + nameBlock + '</div>'
    + '<div class="dc-barwrap">' + bar + '</div>'
    + '<div class="dc-figs">' + figs + '</div>'
    + '</div>'
    + dcDetail(m, fixed)
    + '</div>';
}}

function dcDetail(m, fixed) {{
  var material = dcMaterial(m), costCup = dcCostCup(m);
  var left;
  if (m.recipe && m.recipe.length) {{
    var items = m.recipe.map(function(l) {{ var cost = dcUnitCost(l.ing) * (parseFloat(l.qty) || 0); return {{name: l.ing, qty: l.qty, cost: cost, pct: material ? cost / material * 100 : 0}}; }})
      .sort(function(a, b) {{ return b.cost - a.cost; }});
    var maxc = items.length ? items[0].cost || 1 : 1;
    var rows = items.map(function(i) {{
      return '<div class="dc-ing"><div class="dc-ing-nm">' + escapeHtml(i.name) + '<span class="pc">' + dcF1(i.pct) + '% · ' + dcMoney(i.qty) + ' ' + ((DCS.catalog[i.name]||{{}}).unit || '') + '</span></div>'
        + '<div class="dc-ing-cost">' + i.cost.toFixed(2) + '฿</div>'
        + '<div class="dc-ing-track"><div class="dc-ing-fill" data-w="' + (i.cost / maxc * 100).toFixed(1) + '%"></div></div></div>';
    }}).join('');
    var foot = '<div class="dc-ingfoot">รวมวัตถุดิบ <b>' + dcF1(material) + '฿</b> · ต้นทุนต่อแก้ว <b>' + dcF1(costCup) + '฿</b> (รวมต้นทุนแฝง ' + Math.round(DCS.assumptions.overhead * 100) + '%)</div>';
    left = '<div><div class="dc-sub">🧪 องค์ประกอบต้นทุนวัตถุดิบ</div>' + rows + foot + '</div>';
  }} else {{
    left = '<div><div class="dc-sub">🧪 องค์ประกอบต้นทุนวัตถุดิบ</div><div class="dc-norec">ยังไม่ได้ตั้งสูตรของเมนูนี้'
      + '<br>ต้นทุนต่อแก้ว (ตั้งต้น) <b>' + dcF1(costCup) + '฿</b>'
      + (dcEdit ? '<br><button class="dc-btn ghost" style="margin-top:10px" onclick="event.stopPropagation(); dcOpenMenu(\\'' + m.id + '\\')">+ ตั้งสูตรเลย</button>' : '') + '</div></div>';
  }}

  var be = dcBreakeven(m);
  var beHtml = be
    ? '<div class="dc-be"><div class="big">' + dcMoney(be.cups_day) + ' <small>แก้ว/วัน</small></div>'
      + '<div class="cap">ขายเฉลี่ย ~' + dcMoney(be.cups_day) + ' แก้ว/วัน (' + dcMoney(be.cups_month) + ' แก้ว/เดือน) เพื่อคุ้มค่าใช้จ่ายคงที่ ' + dcMoney(fixed) + ' บาท/เดือน · อิงกำไรหน้าร้าน</div></div>'
    : '<div class="dc-be"><div class="cap">คำนวณจุดคุ้มทุนไม่ได้ (ไม่มีกำไร/ราคาหน้าร้าน)</div></div>';

  var chips = DC_CH.map(function(k) {{
    var cc = dcChannelCalc(m, k);
    if (!cc) return '';
    return '<div class="dc-chip">' + dcChLabel(k) + ' <span class="ch-price">' + dcMoney(cc.price) + '฿</span> · ' + dcF1(cc.margin) + '%</div>';
  }}).join('');

  var right = '<div><div class="dc-sub">⚖️ จุดคุ้มทุน</div>' + beHtml
    + '<div class="dc-sub" style="margin-top:14px">🏷️ ราคา/กำไรแต่ละช่องทาง</div><div class="dc-chrow">' + chips + '</div></div>';

  return '<div class="dc-detail"><div class="dc-detail-grid">' + left + right + '</div></div>';
}}

// ── Modal infra ──
function dcEscClose(e) {{ if (e.key === 'Escape') dcCloseModal(); }}
function dcCloseModal() {{ dcAcClose(false); _vfNewSlip=null; _vfEditId=null; var p = document.getElementById('dc-acpanel'); if (p) p.remove(); var b = document.getElementById('dc-modal-bd'); if (b) b.remove(); document.removeEventListener('keydown', dcEscClose); }}
function dcSetModalBody(html) {{
  var inner = document.querySelector('#dc-modal-bd .dc-modal');
  if (inner) {{ inner.innerHTML = html; return; }}
  var bd = document.createElement('div'); bd.className = 'dc-modal-bd'; bd.id = 'dc-modal-bd';
  bd.innerHTML = '<div class="dc-modal" role="dialog" aria-modal="true">' + html + '</div>';
  document.body.appendChild(bd);
  document.addEventListener('keydown', dcEscClose);
}}

// ── Menu editor ──
function dcIngOptions(selected) {{
  var keys = Object.keys(DCS.catalog).sort(function(a, b) {{ return a.localeCompare(b, 'th'); }});
  var opts = '<option value="">— เลือกวัตถุดิบ —</option>';
  var found = false;
  opts += keys.map(function(k) {{ if (k === selected) found = true; return '<option value="' + escapeHtml(k) + '"' + (k === selected ? ' selected' : '') + '>' + escapeHtml(k) + '</option>'; }}).join('');
  if (selected && !found) opts += '<option value="' + escapeHtml(selected) + '" selected>' + escapeHtml(selected) + ' (ไม่อยู่ในคลัง)</option>';
  return opts;
}}
function dcOpenMenu(id, presetCat) {{
  if (id) {{ var m = DCS.menus.filter(function(x) {{ return x.id === id; }})[0]; dcDraft = dcClone(m); dcDraft.category = dcCategoryOf(dcDraft); }}
  else dcDraft = {{ id: null, name: '', category: presetCat || 'coffee', image: '', recipe: [], prices: {{store:null,lineman:null,shoppee:null,grab:null}}, seed_cost_cup: null }};
  if (dcDraft.image == null) dcDraft.image = '';
  dcRenderMenuModal();
}}
function dcDraftRead() {{
  var g = function(id) {{ var el = document.getElementById(id); return el ? el.value : ''; }};
  dcDraft.name = g('dc-f-name');
  dcDraft.category = g('dc-f-cat');
  dcDraft.image = g('dc-f-image');
  DC_CH.forEach(function(ch) {{ var v = g('dc-p-' + ch); dcDraft.prices[ch] = (v === '' ? null : parseFloat(v)); }});
  var rows = document.querySelectorAll('#dc-recipe-rows .dc-rrow');
  var rec = [];
  rows.forEach(function(r) {{
    var ingEl = r.querySelector('.dc-ring');
    var ing = ingEl ? (ingEl.getAttribute('data-ing') || '') : '';
    var qty = r.querySelector('.dc-rqty').value;
    rec.push({{ ing: ing, qty: (qty === '' ? '' : parseFloat(qty)) }});
  }});
  dcDraft.recipe = rec;
}}
function dcOnInput() {{ dcDraftRead(); dcUpdatePreview(); }}
function dcImgPrev() {{
  var v = (document.getElementById('dc-f-image').value || '').trim();
  var cat = document.getElementById('dc-f-cat').value;
  var img = document.getElementById('dc-f-imgprev');
  if (!img) return;
  img.style.display = ''; img.src = v || ('assets/drink-icons/' + cat + '.svg');
  var fb = img.parentNode.querySelector('.dc-thumb-fb'); if (fb) fb.textContent = DC_CAT_ICON[cat] || '🥤';
}}

// ── Combobox ค้นหาวัตถุดิบ (แทน select ยาว ๆ) ──
var dcAcCtx = null, dcAcGroup = 'all', dcAcQuery = '';
function dcAcEnsurePanel() {{
  var p = document.getElementById('dc-acpanel');
  if (!p) {{
    p = document.createElement('div'); p.id = 'dc-acpanel'; p.style.display = 'none';
    p.addEventListener('mousedown', function(e) {{
      var tab = e.target.closest ? e.target.closest('.dc-ac-tab') : null;
      if (tab) {{ e.preventDefault(); var g = tab.getAttribute('data-g'); setTimeout(function() {{ dcAcGroup = g; dcAcBuild(); }}, 0); return; }}
      var it = e.target.closest ? e.target.closest('.dc-ac-item') : null;
      if (it) {{ e.preventDefault(); dcAcSelect(it.getAttribute('data-name')); }}
    }});
    document.body.appendChild(p);
  }}
  return p;
}}
function dcAcOpen(input, row) {{
  dcAcCtx = {{ input: input, row: row }};
  dcAcEnsurePanel();
  dcAcGroup = 'all'; dcAcQuery = '';
  dcAcBuild();
  dcAcPosition();
  document.getElementById('dc-acpanel').style.display = 'block';
  if (input.select) input.select();
  setTimeout(function() {{ document.addEventListener('mousedown', dcAcOutside); document.addEventListener('scroll', dcAcScroll, true); }}, 0);
}}
function dcAcOutside(e) {{ var p = document.getElementById('dc-acpanel'); if (!p || !dcAcCtx) return; if (e.target === dcAcCtx.input || p.contains(e.target)) return; dcAcClose(true); }}
function dcAcScroll() {{
  if (!dcAcCtx) return;
  var r = dcAcCtx.input.getBoundingClientRect();
  if (r.bottom < 4 || r.top > window.innerHeight - 4) {{ dcAcClose(true); return; }}  // ช่องเลื่อนพ้นจอ -> ปิด
  dcAcPosition();  // ไม่งั้นตาม input ไป
}}
function dcAcPosition() {{
  var p = document.getElementById('dc-acpanel'); if (!p || !dcAcCtx) return;
  var r = dcAcCtx.input.getBoundingClientRect();
  var vh = window.innerHeight;
  var spaceBelow = vh - r.bottom - 10, spaceAbove = r.top - 10, cap = 340;
  p.style.left = r.left + 'px';
  p.style.width = Math.max(r.width, 240) + 'px';
  if (spaceBelow >= 180 || spaceBelow >= spaceAbove) {{
    p.style.top = (r.bottom + 4) + 'px'; p.style.bottom = 'auto';
    p.style.maxHeight = Math.max(120, Math.min(cap, spaceBelow)) + 'px';
  }} else {{
    p.style.top = 'auto'; p.style.bottom = (vh - r.top + 4) + 'px';
    p.style.maxHeight = Math.max(120, Math.min(cap, spaceAbove)) + 'px';
  }}
}}
function dcAcFilter(input) {{ if (dcAcCtx && dcAcCtx.input === input) {{ dcAcQuery = input.value || ''; dcAcBuild(); }} }}
function dcAcBuild() {{
  var p = dcAcEnsurePanel();
  var query = (dcAcQuery || '').trim().toLowerCase();
  function itemHtml(k, active) {{
    var c = DCS.catalog[k]; var uc = (c.unit_cost != null ? c.unit_cost : (c.qty ? c.price / c.qty : 0));
    return '<div class="dc-ac-item' + (active ? ' active' : '') + '" data-name="' + escapeHtml(k) + '"><span>' + escapeHtml(k) + '</span><span class="uc">' + uc.toFixed(3) + ' ฿</span></div>';
  }}
  var keys = Object.keys(DCS.catalog).filter(function(k) {{
    if (query && k.toLowerCase().indexOf(query) < 0) return false;
    if (dcAcGroup !== 'all' && dcIngGroup(k) !== dcAcGroup) return false;
    return true;
  }});
  var tabs = '<div class="dc-ac-tabs"><button class="dc-ac-tab' + (dcAcGroup === 'all' ? ' active' : '') + '" data-g="all">ทั้งหมด</button>'
    + DC_IGROUPS.map(function(g) {{ return '<button class="dc-ac-tab' + (dcAcGroup === g[0] ? ' active' : '') + '" data-g="' + g[0] + '">' + g[1] + '</button>'; }}).join('') + '</div>';
  var body = '', first = true;
  if (dcAcGroup === 'all') {{
    var byG = {{}}; keys.forEach(function(k) {{ var g = dcIngGroup(k); (byG[g] = byG[g] || []).push(k); }});
    DC_IGROUPS.forEach(function(gr) {{
      var items = (byG[gr[0]] || []).sort(function(a, b) {{ return a.localeCompare(b, 'th'); }});
      if (!items.length) return;
      body += '<div class="dc-ac-grp">' + gr[1] + '</div>';
      items.forEach(function(k) {{ body += itemHtml(k, first); first = false; }});
    }});
  }} else {{
    keys.sort(function(a, b) {{ return a.localeCompare(b, 'th'); }}).forEach(function(k) {{ body += itemHtml(k, first); first = false; }});
  }}
  if (!body) body = '<div class="dc-ac-empty">ไม่พบรายการ — เพิ่มได้ที่ 🧂 คลังวัตถุดิบ</div>';
  p.innerHTML = tabs + '<div class="dc-ac-body">' + body + '</div>';
  p.scrollTop = 0;
}}
function dcAcSelect(name) {{
  if (!dcAcCtx) return;
  var inp = dcAcCtx.input;
  inp.value = name; inp.setAttribute('data-ing', name);
  var cb = dcAcCtx.onSelect;
  dcAcClose(false);
  if (cb) cb(name); else dcOnInput();
}}
function dcAcClose(restore) {{
  var p = document.getElementById('dc-acpanel'); if (p) p.style.display = 'none';
  document.removeEventListener('mousedown', dcAcOutside); document.removeEventListener('scroll', dcAcScroll, true);
  if (restore && dcAcCtx && dcAcCtx.input) dcAcCtx.input.value = dcAcCtx.input.getAttribute('data-ing') || '';
  dcAcCtx = null;
}}
function dcAcKey(e, input) {{
  var p = document.getElementById('dc-acpanel');
  if (e.key === 'Escape') {{ dcAcClose(true); input.blur(); return; }}
  if (e.key === 'Enter') {{ e.preventDefault(); if (p) {{ var act = p.querySelector('.dc-ac-item.active') || p.querySelector('.dc-ac-item'); if (act) dcAcSelect(act.getAttribute('data-name')); }} return; }}
  if ((e.key === 'ArrowDown' || e.key === 'ArrowUp') && p) {{
    e.preventDefault();
    var items = [].slice.call(p.querySelectorAll('.dc-ac-item')); if (!items.length) return;
    var idx = -1; items.forEach(function(x, j) {{ if (x.classList.contains('active')) idx = j; }});
    items.forEach(function(x) {{ x.classList.remove('active'); }});
    idx = (e.key === 'ArrowDown') ? Math.min(items.length - 1, idx + 1) : Math.max(0, idx - 1);
    if (idx < 0) idx = 0;
    items[idx].classList.add('active'); items[idx].scrollIntoView({{ block: 'nearest' }});
  }}
}}
function dcUpdatePreview() {{
  var clean = {{ recipe: dcDraft.recipe.filter(function(l) {{ return l.ing; }}), seed_cost_cup: dcDraft.seed_cost_cup, prices: dcDraft.prices }};
  var material = dcMaterial(clean), costCup = dcCostCup(clean), suggest = dcSuggestPrice(clean);
  var st = dcChannelCalc(clean, 'store');
  var set = function(id, v) {{ var el = document.getElementById(id); if (el) el.textContent = v; }};
  set('dc-pv-material', dcF1(material) + '฿');
  set('dc-pv-cost', dcF1(costCup) + '฿');
  set('dc-pv-suggest', dcMoney(suggest) + '฿');
  set('dc-pv-margin', st && st.margin != null ? dcF1(st.margin) + '%' : '–');
  var pm = document.getElementById('dc-pv-margin'); if (pm) pm.style.color = dcMargCol(st ? st.margin : null);
  document.querySelectorAll('#dc-recipe-rows .dc-rrow').forEach(function(r) {{
    var ingEl = r.querySelector('.dc-ring');
    var ing = ingEl ? (ingEl.getAttribute('data-ing') || '') : '';
    var qty = parseFloat(r.querySelector('.dc-rqty').value) || 0;
    var cell = r.querySelector('.dc-rcost'); if (cell) cell.textContent = (dcUnitCost(ing) * qty).toFixed(2) + '฿';
  }});
}}
function dcAddIng() {{ dcDraftRead(); dcDraft.recipe.push({{ ing: '', qty: '' }}); dcRenderMenuModal(); }}
function dcDelIng(i) {{ dcDraftRead(); dcDraft.recipe.splice(i, 1); dcRenderMenuModal(); }}
function dcAutoPrice(ch) {{ dcDraftRead(); var clean = {{ recipe: dcDraft.recipe.filter(function(l) {{ return l.ing; }}), seed_cost_cup: dcDraft.seed_cost_cup }}; dcDraft.prices[ch] = dcSuggestPrice(clean); dcRenderMenuModal(); }}
function dcSaveMenu() {{
  dcDraftRead();
  if (!dcDraft.name.trim()) {{ showToast('กรุณาใส่ชื่อเมนู'); return; }}
  dcDraft.recipe = dcDraft.recipe.filter(function(l) {{ return l.ing && (parseFloat(l.qty) || 0) > 0; }});
  if (!dcDraft.id) dcDraft.id = 'm' + Date.now();
  var i = -1;
  DCS.menus.forEach(function(m, idx) {{ if (m.id === dcDraft.id) i = idx; }});
  if (i >= 0) DCS.menus[i] = dcDraft; else DCS.menus.push(dcDraft);
  dcAfterChange(); dcCloseModal(); renderDrinkCosts(); showToast('บันทึกเมนู "' + dcDraft.name + '" แล้ว');
}}
function dcDeleteMenu(id) {{
  var m = DCS.menus.filter(function(x) {{ return x.id === id; }})[0];
  if (!m) return;
  if (!confirm('ลบเมนู "' + m.name + '" ?')) return;
  DCS.menus = DCS.menus.filter(function(x) {{ return x.id !== id; }});
  dcAfterChange(); dcCloseModal(); renderDrinkCosts(); showToast('ลบเมนูแล้ว');
}}
function dcRenderMenuModal() {{
  var d = dcDraft;
  var catOpts = DC_CATS.map(function(c) {{ return '<option value="' + c + '"' + (c === d.category ? ' selected' : '') + '>' + DC_CAT_ICON[c] + ' ' + DC_CAT_LABEL[c] + '</option>'; }}).join('');
  var priceFields = DC_CH.map(function(ch) {{
    return '<div class="dc-field"><label>' + dcChLabel(ch) + ' (฿)</label><div class="dc-pricewrap">'
      + '<input class="dc-inp" id="dc-p-' + ch + '" type="number" min="0" step="any" value="' + (d.prices[ch] == null ? '' : d.prices[ch]) + '" oninput="dcOnInput()">'
      + '<button class="dc-auto" type="button" onclick="dcAutoPrice(\\'' + ch + '\\')">auto</button></div></div>';
  }}).join('');
  var recRows = d.recipe.map(function(l, i) {{
    var cost = dcUnitCost(l.ing) * (parseFloat(l.qty) || 0);
    return '<div class="dc-rrow"><div class="dc-ac"><input class="dc-inp dc-ac-inp dc-ring" data-ing="' + escapeHtml(l.ing || '') + '" value="' + escapeHtml(l.ing || '') + '" placeholder="ค้นหา / เลือกวัตถุดิบ" autocomplete="off" onfocus="dcAcOpen(this,' + i + ')" oninput="dcAcFilter(this)" onkeydown="dcAcKey(event,this)"></div>'
      + '<input class="dc-inp dc-rqty" type="number" min="0" step="any" placeholder="ปริมาณ" value="' + (l.qty === '' || l.qty == null ? '' : l.qty) + '" oninput="dcOnInput()">'
      + '<span class="dc-rcost">' + cost.toFixed(2) + '฿</span>'
      + '<button class="dc-rdel" type="button" title="ลบ" onclick="dcDelIng(' + i + ')">✕</button></div>';
  }}).join('');

  var html = '<div class="dc-modal-head"><h3>' + (d.id ? 'แก้ไขเมนู' : 'เพิ่มเมนูใหม่') + '</h3><button class="dc-x" onclick="dcCloseModal()" aria-label="ปิด">✕</button></div>'
    + '<div class="dc-modal-scroll">'
    + '<div class="dc-grid3" style="grid-template-columns:2fr 1fr">'
    + '<div class="dc-field"><label>ชื่อเมนู</label><input class="dc-inp" id="dc-f-name" value="' + escapeHtml(d.name) + '" oninput="dcOnInput()"></div>'
    + '<div class="dc-field"><label>หมวด</label><select class="dc-sel" id="dc-f-cat" onchange="dcOnInput(); dcImgPrev()">' + catOpts + '</select></div>'
    + '</div>'
    + '<div class="dc-field"><label>รูปภาพ (URL) — เว้นว่าง = ใช้ไอคอนหมวดอัตโนมัติ</label>'
    + '<div style="display:flex;gap:11px;align-items:center">'
    + '<span class="dc-thumb" style="width:48px;height:48px"><span class="dc-thumb-fb">' + (DC_CAT_ICON[d.category] || '🥤') + '</span>'
    + '<img id="dc-f-imgprev" src="' + escapeHtml(d.image || ('assets/drink-icons/' + d.category + '.svg')) + '" alt="" onerror="this.style.display=\\'none\\'"></span>'
    + '<input class="dc-inp" id="dc-f-image" placeholder="https://...jpg / .png" value="' + escapeHtml(d.image || '') + '" oninput="dcImgPrev()"></div></div>'
    + '<div class="dc-field"><label>ราคาขายต่อช่องทาง</label><div class="dc-grid3">' + priceFields + '</div></div>'
    + '<div class="dc-field"><label>สูตร / วัตถุดิบ (เลือกจากคลัง + ใส่ปริมาณ)</label>'
    + '<div id="dc-recipe-rows">' + recRows + '</div>'
    + '<button class="dc-btn ghost" type="button" style="margin-top:6px" onclick="dcAddIng()">+ เพิ่มวัตถุดิบ</button></div>'
    + '<div class="dc-preview">'
    + '<div class="dc-pv"><div class="l">วัตถุดิบรวม</div><div class="v" id="dc-pv-material">–</div></div>'
    + '<div class="dc-pv"><div class="l">ต้นทุน/แก้ว</div><div class="v" id="dc-pv-cost">–</div></div>'
    + '<div class="dc-pv"><div class="l">ราคาแนะนำ</div><div class="v" id="dc-pv-suggest">–</div></div>'
    + '<div class="dc-pv"><div class="l">กำไร หน้าร้าน</div><div class="v" id="dc-pv-margin">–</div></div>'
    + '</div>'
    + '</div>'
    + '<div class="dc-modal-foot">'
    + (d.id ? '<button class="dc-btn ghost danger spacer" onclick="dcDeleteMenu(\\'' + d.id + '\\')">🗑️ ลบเมนู</button>' : '<span class="spacer"></span>')
    + '<button class="dc-btn" onclick="dcCloseModal()">ยกเลิก</button>'
    + '<button class="dc-btn primary" onclick="dcSaveMenu()">บันทึกเมนู</button>'
    + '</div>';
  dcSetModalBody(html);
  dcUpdatePreview();
}}

// ── Catalog editor ──
var dcCatFilter = 'all';
function dcCatFilterBtns() {{
  var b = '<button class="ov-mtab" data-g="all" onclick="dcCatFilterSet(\\'all\\')">ทั้งหมด</button>';
  b += DC_IGROUPS.map(function(g) {{ return '<button class="ov-mtab" data-g="' + g[0] + '" onclick="dcCatFilterSet(\\'' + g[0] + '\\')">' + g[1] + '</button>'; }}).join('');
  return b;
}}
function dcCatFilterSet(g) {{ dcCatFilter = g; dcApplyCatFilter(); }}
function dcApplyCatFilter() {{
  var g = dcCatFilter, shown = 0;
  document.querySelectorAll('#dc-cat-list .dc-cat-row').forEach(function(r) {{
    var ok = (g === 'all' || r.getAttribute('data-group') === g);
    r.style.display = ok ? '' : 'none'; if (ok) shown++;
  }});
  document.querySelectorAll('.dc-catfilter .ov-mtab').forEach(function(b) {{ b.classList.toggle('active', b.getAttribute('data-g') === g); }});
  var sc = document.querySelector('#dc-cat-list'); if (sc) sc.parentNode.scrollTop = 0;
}}
function dcOpenCatalog() {{ dcCatFilter = 'all'; dcRenderCatalogModal(); }}
function dcRenderCatalogModal() {{
  var keys = Object.keys(DCS.catalog).sort(function(a, b) {{ return a.localeCompare(b, 'th'); }});
  var rows = keys.map(function(k) {{
    var c = DCS.catalog[k];
    return '<div class="dc-cat-row" data-orig="' + escapeHtml(k) + '" data-group="' + dcIngGroup(k) + '">'
      + '<input class="dc-inp dc-c-name" value="' + escapeHtml(k) + '">'
      + '<input class="dc-inp dc-c-price" type="number" min="0" step="any" value="' + c.price + '" oninput="dcCatUC(this)">'
      + '<input class="dc-inp dc-c-qty" type="number" min="0" step="any" value="' + c.qty + '" oninput="dcCatUC(this)">'
      + '<span class="uc">' + (c.unit_cost != null ? c.unit_cost.toFixed(3) : (c.qty ? (c.price/c.qty).toFixed(3) : '0')) + '</span>'
      + '<button class="dc-rdel" type="button" title="ลบ" onclick="this.closest(\\'.dc-cat-row\\').remove()">✕</button></div>';
  }}).join('');
  var html = '<div class="dc-modal-head"><h3>🧂 คลังวัตถุดิบ</h3><button class="dc-x" onclick="dcCloseModal()" aria-label="ปิด">✕</button></div>'
    + '<div class="dc-modal-scroll">'
    + '<div class="dc-edithint" style="margin-bottom:10px">แก้ราคา/ปริมาณแพ็ก แล้วทุกเมนูที่ใช้วัตถุดิบนั้นจะคำนวณต้นทุนใหม่ทันที</div>'
    + '<div class="dc-catfilter">' + dcCatFilterBtns() + '</div>'
    + '<div class="dc-cat-row"><span class="dc-cat-head">ชื่อวัตถุดิบ</span><span class="dc-cat-head">ราคาแพ็ก</span><span class="dc-cat-head">ปริมาณ</span><span class="dc-cat-head" style="text-align:right">฿/หน่วย</span><span></span></div>'
    + '<div class="dc-cat-list" id="dc-cat-list">' + rows + '</div>'
    + '<button class="dc-btn ghost" type="button" style="margin-top:10px" onclick="dcAddCatalogRow()">+ เพิ่มวัตถุดิบใหม่</button>'
    + '</div>'
    + '<div class="dc-modal-foot"><span class="spacer"></span><button class="dc-btn" onclick="dcCloseModal()">ยกเลิก</button><button class="dc-btn primary" onclick="dcSaveCatalog()">บันทึกคลัง</button></div>';
  dcSetModalBody(html);
  dcApplyCatFilter();
}}
function dcCatUC(inp) {{
  var row = inp.closest('.dc-cat-row');
  var price = parseFloat(row.querySelector('.dc-c-price').value) || 0;
  var qty = parseFloat(row.querySelector('.dc-c-qty').value) || 0;
  row.querySelector('.uc').textContent = qty ? (price / qty).toFixed(3) : '0';
}}
function dcAddCatalogRow() {{
  var list = document.getElementById('dc-cat-list');
  var div = document.createElement('div'); div.className = 'dc-cat-row'; div.setAttribute('data-orig', '');
  div.setAttribute('data-group', dcCatFilter === 'all' ? 'other' : dcCatFilter);
  div.innerHTML = '<input class="dc-inp dc-c-name" placeholder="ชื่อวัตถุดิบ">'
    + '<input class="dc-inp dc-c-price" type="number" min="0" step="any" placeholder="ราคา" oninput="dcCatUC(this)">'
    + '<input class="dc-inp dc-c-qty" type="number" min="0" step="any" placeholder="ปริมาณ" oninput="dcCatUC(this)">'
    + '<span class="uc">0</span><button class="dc-rdel" type="button" onclick="this.closest(\\'.dc-cat-row\\').remove()">✕</button>';
  list.appendChild(div);
  div.querySelector('.dc-c-name').focus();
}}
function dcSaveCatalog() {{
  var cat = {{}};
  document.querySelectorAll('#dc-cat-list .dc-cat-row').forEach(function(r) {{
    var name = r.querySelector('.dc-c-name').value.trim();
    if (!name) return;
    var price = parseFloat(r.querySelector('.dc-c-price').value) || 0;
    var qty = parseFloat(r.querySelector('.dc-c-qty').value) || 0;
    var orig = r.getAttribute('data-orig');
    var unit = (orig && DCS.catalog[orig]) ? DCS.catalog[orig].unit : '';
    cat[name] = {{ price: price, qty: qty, unit_cost: qty ? +(price / qty).toFixed(5) : 0, unit: unit }};
  }});
  DCS.catalog = cat;
  dcAfterChange(); dcCloseModal(); renderDrinkCosts(); showToast('บันทึกคลังวัตถุดิบแล้ว');
}}

// ── Export / Import ──
function dcExport() {{
  var blob = new Blob([JSON.stringify(DCS, null, 2)], {{ type: 'application/json' }});
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url; a.download = 'drink-costs.json'; document.body.appendChild(a); a.click();
  setTimeout(function() {{ URL.revokeObjectURL(url); a.remove(); }}, 100);
  showToast('ดาวน์โหลด drink-costs.json แล้ว');
}}
function dcImportClick() {{ var el = document.getElementById('dc-import-file'); if (el) el.click(); }}
function dcImportFile(input) {{
  var f = input.files && input.files[0];
  if (!f) return;
  var rd = new FileReader();
  rd.onload = function() {{
    try {{
      var obj = JSON.parse(rd.result);
      if (!obj.menus) throw new Error('no menus');
      DCS = dcNormalize(obj); dcSave(); renderDrinkCosts(); showToast('นำเข้าข้อมูลแล้ว');
    }} catch (e) {{ showToast('ไฟล์ไม่ถูกต้อง'); }}
  }};
  rd.readAsText(f);
  input.value = '';
}}

// ── Google Sheet sync (สองทาง) ──
var dcSyncedSession = false;
function dcGsUrl() {{ try {{ return localStorage.getItem('pengtang_gs_url') || ''; }} catch (e) {{ return ''; }} }}
function dcSetGsUrl(u) {{ try {{ if (u) localStorage.setItem('pengtang_gs_url', u); else localStorage.removeItem('pengtang_gs_url'); }} catch (e) {{}} }}
function dcAfterChange() {{ dcSave(); dcMarkPending(); if (dcGsUrl()) dcSyncPush(); }}

function dcSyncPull(silent) {{
  var url = dcGsUrl();
  if (!url) {{ if (!silent) showToast('ยังไม่ได้เชื่อม Google Sheet'); return; }}
  if (!DCS) dcLoadState();
  fetch(url, {{ method: 'GET' }})
    .then(function(r) {{ return r.json(); }})
    .then(function(obj) {{
      if (!obj || !obj.menus) throw new Error('bad');
      // 🛡️ เกราะกันพลาด: Sheet ว่าง แต่ในเครื่องมีข้อมูล → ไม่ดึงมาทับ
      if (dcDataScore(obj) === 0 && dcDataScore(DCS) > 0) {{
        if (!silent) showToast('Sheet ว่าง — ไม่ดึงมาทับข้อมูลในเครื่อง');
        dcShowEmptySheetWarn();
        return;
      }}
      var prev = DCS ? dcClone(DCS) : {{}};
      DCS = dcNormalize(obj);
      // posLast + quest keys: ถ้า Sheet ยังไม่มี (obj ไม่มี key) ให้เก็บของ local ไว้
      DCS.posLast = prev.posLast !== undefined ? prev.posLast : null;
      ['quests','achievements','plans','loops','questLog','questHistory','questMeta'].forEach(function(k) {{
        if (obj[k] === undefined) DCS[k] = prev[k] !== undefined ? prev[k] : DCS[k];
      }});
      dcSave(); renderDrinkCosts(); stkRefreshIfActive(); vfRefreshIfActive();
      if (!silent) showToast('ซิงก์จาก Google Sheet แล้ว (' + DCS.menus.length + ' เมนู)');
    }})
    .catch(function(e) {{ if (!silent) showToast('ดึงข้อมูลไม่สำเร็จ — ตรวจ URL / สิทธิ์ Anyone'); }});
}}
function dcSyncPush() {{
  var url = dcGsUrl();
  if (!url) return;
  fetch(url, {{ method: 'POST', headers: {{ 'Content-Type': 'text/plain;charset=utf-8' }}, body: JSON.stringify(DCS) }})
    .then(function(r) {{ return r.json(); }})
    .then(function(res) {{ if (res && res.ok) dcClearPending(); showToast((res && res.ok) ? 'บันทึกขึ้น Google Sheet แล้ว' : 'เขียน Sheet ไม่สำเร็จ'); }})
    .catch(function(e) {{ showToast('เขียน Sheet ไม่สำเร็จ (เก็บในเครื่องแล้ว)'); }});
}}
// ── Auto-pull ตอนเปิดหน้า + ตัวกันข้อมูลค้างถูกทับ ──
function dcMarkPending() {{ try {{ localStorage.setItem('pengtang_push_pending','1'); }} catch(e) {{}} }}
function dcClearPending() {{ try {{ localStorage.removeItem('pengtang_push_pending'); }} catch(e) {{}} }}
function dcHasPending() {{ try {{ return localStorage.getItem('pengtang_push_pending')==='1'; }} catch(e) {{ return false; }} }}
function dcAutoPullOnBoot() {{
  if (!dcGsUrl()) return;                       // ยังไม่เชื่อม Sheet = ไม่ทำ
  if (dcHasPending()) {{ dcShowPendingWarn(); return; }}  // มีของค้างยังไม่ซิงก์ = ไม่ดึงทับ
  dcSyncPull(false);                            // สะอาด = ดึงข้อมูลล่าสุด
}}
function dcDataScore(o) {{
  if (!o) return 0;
  var pl = o.plans || {{}};
  return (o.menus||[]).length + Object.keys(o.catalog||{{}}).length
    + (o.expenses||[]).length + (o.purchases||[]).length
    + (o.quests||[]).length + (o.achievements||[]).length
    + (o.loops||[]).length + (o.questHistory||[]).length
    + (pl.daily||[]).length + (pl.weekly||[]).length + (pl.monthly||[]).length;
}}
function dcSyncGuardBanner(msgHtml) {{
  if (document.getElementById('dc-pending-warn')) return;
  var b = document.createElement('div');
  b.id = 'dc-pending-warn';
  b.style.cssText = 'position:fixed;top:12px;left:50%;transform:translateX(-50%);z-index:3000;max-width:520px;width:calc(100% - 32px);background:rgba(229,57,53,.13);border:1px solid rgba(229,57,53,.5);color:var(--text);border-radius:12px;padding:13px 16px;font-size:13px;line-height:1.55;box-shadow:0 10px 30px rgba(0,0,0,.18)';
  b.innerHTML = msgHtml
    + '<div style="margin-top:9px;display:flex;gap:8px">'
    + '<button id="dc-pw-go" style="background:#e53935;color:#fff;border:none;border-radius:8px;padding:6px 13px;font-size:12px;font-weight:600;cursor:pointer">🔗 ไปดันขึ้น Sheet</button>'
    + '<button id="dc-pw-x" style="background:var(--card);border:1px solid var(--card-border);border-radius:8px;padding:6px 13px;font-size:12px;cursor:pointer;color:var(--text)">ปิด</button>'
    + '</div>';
  document.body.appendChild(b);
  var go = document.getElementById('dc-pw-go'), x = document.getElementById('dc-pw-x');
  if (go) go.onclick = function() {{ b.remove(); dcOpenConnect(); }};
  if (x) x.onclick = function() {{ b.remove(); }};
}}
function dcShowPendingWarn() {{
  dcSyncGuardBanner('<b style="color:#e53935">⚠️ มีข้อมูลในเครื่องนี้ที่ยังไม่ได้ซิงก์ขึ้น Sheet</b>'
    + '<div style="margin-top:4px">ระบบยังไม่ดึงข้อมูลใหม่มาทับให้ (กันข้อมูลหาย) — แนะนำกด <b>⬆️ ดันข้อมูลขึ้น Sheet</b> ก่อน แล้วค่อยซิงก์</div>');
}}
function dcShowEmptySheetWarn() {{
  dcSyncGuardBanner('<b style="color:#e53935">⚠️ Sheet ว่างเปล่า — ไม่ดึงข้อมูลมาทับ</b>'
    + '<div style="margin-top:4px">ข้อมูลในเครื่องยังอยู่ครบ (ระบบกันไว้ให้) — ถ้าต้องการเติมข้อมูลขึ้น Sheet กด <b>⬆️ ดันข้อมูลขึ้น Sheet</b></div>');
}}

function dcOpenConnect() {{
  var url = dcGsUrl();
  var html = '<div class="dc-modal-head"><h3>🔗 เชื่อม Google Sheet</h3><button class="dc-x" onclick="dcCloseModal()" aria-label="ปิด">✕</button></div>'
    + '<div class="dc-modal-scroll">'
    + '<div class="dc-field"><label>Google Apps Script — Web app URL</label>'
    + '<input class="dc-inp" id="dc-gs-url" placeholder="https://script.google.com/macros/s/.../exec" value="' + escapeHtml(url) + '"></div>'
    + '<div class="dc-edithint">วาง URL จากการ Deploy เป็น Web app (วิธีทำดูไฟล์ google-sheets/README.md) · '
    + 'URL เก็บในเบราว์เซอร์นี้เท่านั้น ไม่ฝังในเว็บสาธารณะ</div>'
    + '<div style="margin-top:12px;padding:11px 13px;border-radius:10px;background:rgba(229,57,53,.12);border:1px solid rgba(229,57,53,.45);font-size:13px;line-height:1.55;color:var(--text)">'
    + '<b style="color:#e53935">⚠️ ครั้งแรก: ดันก่อนดึงเสมอ</b><br>'
    + 'กด <b>⬆️ ดันข้อมูลขึ้น Sheet</b> ก่อน เพื่อเอารายจ่าย·สต็อก·เมนู ในเครื่องขึ้นไปเก็บบน Sheet<br>'
    + 'ปุ่ม <b>🔄 ดึงข้อมูล</b> จะ<b>เขียนทับข้อมูลในเครื่องทั้งหมด</b>ด้วยข้อมูลจาก Sheet — ถ้าดึงก่อนดัน ข้อมูลในเครื่องจะหาย'
    + '</div>'
    + '<div style="margin-top:10px;padding:10px 13px;border-radius:10px;background:rgba(37,99,235,.10);border:1px solid rgba(37,99,235,.35);font-size:12.5px;line-height:1.55;color:var(--text)">'
    + '<b>🔄 ซิงก์อัตโนมัติตอนเปิดหน้า:</b> ทุกครั้งที่เปิดเว็บใหม่ ระบบจะดึงข้อมูลล่าสุดจาก Sheet ให้เอง<br>'
    + '<b>กันลืม:</b> ถ้าเครื่องนี้มีของแก้ที่ยังไม่ทันซิงก์ขึ้น ระบบจะ<b>ไม่ดึงมาทับ</b> + เตือนให้ดันขึ้นก่อน · แก้หลายเครื่องให้ "ดันขึ้น" ก่อนสลับเครื่องเสมอ'
    + '</div>'
    + '</div>'
    + '<div class="dc-modal-foot">'
    + '<button class="dc-btn ghost spacer" onclick="dcConnectTest()">🔄 ทดสอบ + ดึงข้อมูล</button>'
    + '<button class="dc-btn primary" onclick="dcConnectPush()">⬆️ ดันข้อมูลขึ้น Sheet</button>'
    + '<button class="dc-btn" onclick="dcConnectSave()">💾 บันทึก URL</button>'
    + '</div>';
  dcSetModalBody(html);
}}
function dcConnectSave() {{ var u = document.getElementById('dc-gs-url').value.trim(); dcSetGsUrl(u); dcCloseModal(); renderDrinkCosts(); stkRefreshIfActive(); vfRefreshIfActive(); showToast(u ? 'เชื่อม Google Sheet แล้ว' : 'ยกเลิกการเชื่อมต่อแล้ว'); }}
function dcConnectTest() {{
  dcSetGsUrl(document.getElementById('dc-gs-url').value.trim());
  if (!confirm('⚠️ การดึงข้อมูลจะเขียนทับข้อมูลในเครื่องนี้ทั้งหมดด้วยข้อมูลจาก Sheet\\n\\nถ้ายังไม่เคยกด "ดันข้อมูลขึ้น Sheet" รายจ่าย/สต็อกในเครื่องอาจหาย\\n\\nยืนยันการดึง?')) return;
  dcSyncPull();
}}
function dcConnectPush() {{ dcSetGsUrl(document.getElementById('dc-gs-url').value.trim()); dcSyncPush(); }}

// ── Backbar: สต็อกหลังบ้าน ──
var stkTab = 'remain';
var stkIgrpTab = 'all';
var STK_DISMISSED_KEY = 'pengtang_stk_dismissed';
var STK_UNITS = ['ชิ้น','อัน','ซอง','ขวด','แกลลอน','กล่อง','แพ็ค','ลัง','โหล','อื่นๆ'];

// ---- dismissed (localStorage แยก, ไม่ sync) ----
function stkGetDismissed() {{
  try {{ var r=localStorage.getItem(STK_DISMISSED_KEY); return r?JSON.parse(r):{{}};}} catch(e) {{ return {{}}; }}
}}
function stkSaveDismissed(d) {{ try {{ localStorage.setItem(STK_DISMISSED_KEY,JSON.stringify(d)); }} catch(e) {{}} }}
function stkDismiss(ing) {{ var d=stkGetDismissed(); d[ing]=true; stkSaveDismissed(d); renderStockView(); }}
function stkDismissMock(btn) {{ var card=btn.closest('.stk-warn-card'); card.classList.add('dismissed'); btn.style.display='none'; }}
function stkWarnCardHTML(o) {{
  var pct=Math.max(0,o.pct||0);
  var h=(pct*1.2).toFixed(1);
  var col='hsl('+h+',80%,45%)';
  var thr=(DCS.stock&&DCS.stock.threshold_pct)||60;
  var dur=(0.5+(pct/thr)*1.1).toFixed(2);
  var isDis=!!o.isDis;
  var animSt=isDis?'':'animation:stkBeat '+dur+'s ease-in-out infinite,stkAura '+dur+'s ease-in-out infinite;';
  var varSt='--stk-glow:hsla('+h+',80%,45%,.55);--stk-bg:hsla('+h+',80%,45%,.06);border-color:hsla('+h+',80%,45%,.32);';
  var disBtn=isDis?'':
    o.mock
      ? "<button class='stk-warn-ack' onclick='stkDismissMock(this)'>✓ ทราบแล้ว (ตัวอย่าง)</button>"
      : "<button class='stk-warn-ack' onclick='stkDismiss(&quot;"+escapeHtml(o.name)+"&quot;)'>✓ ทราบแล้ว</button>";
  var imgBit=o.imgBit||'';
  return '<div class="stk-warn-card'+(isDis?' dismissed':'')+'" style="'+varSt+animSt+'">'
    +'<div class="stk-thermo-wrap">'
    +'<div class="stk-thermo"><div class="stk-thermo-fill" style="height:'+Math.min(100,pct)+'%;background:'+col+'"></div></div>'
    +'<span class="stk-thermo-pct">'+Math.round(pct)+'%</span>'
    +'</div>'
    +'<div class="stk-warn-info">'
    +'<div class="stk-warn-name">'+imgBit+escapeHtml(o.name)+'</div>'
    +'<div class="stk-warn-qty">คงเหลือ <b>'+o.remainText+'</b></div>'
    +disBtn
    +'</div></div>';
}}
function stkAutoUnDismiss() {{
  var d=stkGetDismissed(); var ch=false;
  Object.keys(d).forEach(function(ing) {{
    var p=stkPct(ing);
    if (p!==null && p>=(DCS.stock.threshold_pct||60)) {{ delete d[ing]; ch=true; }}
  }});
  if (ch) stkSaveDismissed(d);
}}

// ---- compute ----
function stkRecordBase(p) {{
  if (p.qty!=null) return (parseFloat(p.qty)||0)*(parseFloat(p.size)||1);
  if (p.packs!=null) {{ var c=DCS.catalog[p.ing]; return (parseFloat(p.packs)||0)*(c&&parseFloat(c.qty)>0?parseFloat(c.qty):1); }}
  return 0;
}}
function stkBoughtBase(ing) {{
  return (DCS.purchases||[]).reduce(function(s,p) {{ return s+(p.ing===ing?stkRecordBase(p):0); }},0);
}}
function stkCupsForMenu(menuName) {{
  return (DCS.sales||[]).reduce(function(s,r) {{ return s+(r.menu===menuName?(parseFloat(r.cups)||0):0); }},0);
}}
function stkUsedBase(ing) {{
  var total=0;
  (DCS.menus||[]).forEach(function(m) {{
    var cups=stkCupsForMenu(m.name); if (!cups) return;
    (m.recipe||[]).forEach(function(l) {{ if (l.ing===ing) total+=cups*(parseFloat(l.qty)||0); }});
  }});
  return total;
}}
function stkRemainBase(ing) {{ return stkBoughtBase(ing)-stkUsedBase(ing); }}
function stkParBase(ing) {{
  var p=(DCS.stock.par||{{}})[ing];
  if (p==null) return 0;
  if (typeof p==='object') return (parseFloat(p.count)||0)*(parseFloat(p.size)||1);
  var c=DCS.catalog[ing]; return (parseFloat(p)||0)*(c&&parseFloat(c.qty)>0?parseFloat(c.qty):1);
}}
function stkPct(ing) {{ var pb=stkParBase(ing); if (!(pb>0)) return null; return stkRemainBase(ing)/pb*100; }}
function stkLow(ing) {{ var p=stkPct(ing); return p!==null&&p<(DCS.stock.threshold_pct||60); }}
function stkBaseUnit(ing) {{ var c=DCS.catalog[ing]; return (c&&c.unit)?c.unit:'กรัม/มล.'; }}
function fmtQty(base,baseUnit) {{
  var u=baseUnit||'กรัม/มล.';
  if (u==='กรัม/มล.'&&base>=1000) return dcF1(base/1000)+' ลิตร/กก.';
  return dcF1(base)+' '+u;
}}
function stkLastPPB(ing) {{
  var last=null;
  (DCS.purchases||[]).forEach(function(p) {{
    if (p.ing!==ing) return;
    var pr=parseFloat(p.price||''); var sz=parseFloat(p.size||'')||1;
    if (pr>0) last=pr/sz;
  }});
  return last||0;
}}
function stkTotalValue() {{
  return Object.keys(DCS.catalog).reduce(function(s,k) {{
    var r=stkRemainBase(k); if (!(r>0)) return s; return s+r*stkLastPPB(k);
  }},0);
}}
function stkIngIcon(ing) {{
  var icons={{bean:'☕',milk:'🥛',cocoa:'🍫',tea:'🍵',sweet:'🍯',syrup:'🧴',pack:'📦',other:'🫙'}};
  return icons[dcIngGroup(ing)]||'🫙';
}}
function stkUnitOpts(val) {{
  return STK_UNITS.map(function(u){{ return '<option value="'+u+'"'+(u===val?' selected':'')+'>'+u+'</option>'; }}).join('');
}}

// ---- render ----
function renderStockView() {{
  dcLoadState(); stkAutoUnDismiss();
  var root=document.getElementById('stk-root'); if (!root) return;
  var ings=Object.keys(DCS.catalog);
  var lowCount=ings.filter(stkLow).length;
  var totalVal=stkTotalValue();
  var kpi='<div class="dc-stats-row" style="margin-bottom:14px">'
    +'<div class="dc-stat"><span class="dc-st-lab">วัตถุดิบที่ติดตาม</span><span class="dc-st-val">'+ings.length+'</span></div>'
    +'<div class="dc-stat"><span class="dc-st-lab">⚠️ ใกล้หมด</span><span class="dc-st-val" style="color:'+(lowCount?'var(--dc-warn)':'var(--dc-profit)')+'">'+lowCount+'</span></div>'
    +'<div class="dc-stat"><span class="dc-st-lab">มูลค่าคงเหลือ</span><span class="dc-st-val">฿'+dcMoney(totalVal)+'</span></div>'
    +'</div>';
  var toolbar='<div class="dc-toolbar" style="margin-bottom:12px">'
    +'<button class="dc-btn primary" onclick="stkOpenPurchase()">📦 ซื้อเข้า</button>'
    +'<button class="dc-btn" onclick="stkOpenSales()">🧾 ยอดขาย</button>'
    +'<button class="dc-btn" onclick="stkOpenPar()">⚙️ ตั้งสต็อกเต็ม</button>'
    +(dcGsUrl()?'<button class="dc-btn" onclick="dcSyncPull()">🔄 ซิงก์</button>':'')
    +'</div>';
  var tabs='<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px">'
    +'<button class="ov-mtab'+(stkTab==='remain'?' active':'')+'" onclick="stkSetTab(\\'remain\\')">สต็อกคงเหลือ</button>'
    +'<button class="ov-mtab'+(stkTab==='usage'?' active':'')+'" onclick="stkSetTab(\\'usage\\')">การใช้ต่อเมนู</button>'
    +'</div>';
  root.innerHTML=kpi+toolbar+stkRenderWarnCards()+tabs+'<div>'+(stkTab==='remain'?stkRenderRemain():stkRenderUsage())+'</div>';
}}
function stkSetTab(t) {{ stkTab=t; renderStockView(); }}
function stkSetIgrp(g) {{ stkIgrpTab=g; renderStockView(); }}
function stkRefreshIfActive() {{ var v=document.getElementById('view-bb-stock'); if (v&&v.classList.contains('active')) renderStockView(); }}
function vfRefreshIfActive() {{ var v=document.getElementById('view-bb-varfix'); if (v&&v.classList.contains('active')) renderVarfixView(); }}
function stkSalesFilter(cat) {{
  document.querySelectorAll('[data-scat]').forEach(function(b) {{ b.classList.toggle('active',b.getAttribute('data-scat')===cat); }});
  document.querySelectorAll('.stk-sales-group').forEach(function(g) {{ g.classList.toggle('stk-hide',cat!=='all'&&g.getAttribute('data-cat')!==cat); }});
}}
function stkSalesBadge() {{
  var n=0;
  document.querySelectorAll('.stk-sales-qty').forEach(function(inp) {{ if (parseFloat(inp.value||'')>0) n++; }});
  var bdg=document.getElementById('stk-sales-bdg');
  if (!bdg) return;
  bdg.textContent=n; bdg.style.display=n?'':'none';
}}
function stkParFilter(igrp) {{
  document.querySelectorAll('[data-pigrp]').forEach(function(b) {{ b.classList.toggle('active',b.getAttribute('data-pigrp')===igrp); }});
  document.querySelectorAll('.stk-par-group').forEach(function(g) {{ g.classList.toggle('stk-hide',igrp!=='all'&&g.getAttribute('data-igrp')!==igrp); }});
}}

// ---- Phase B: warning cards ----
function stkRenderWarnCards() {{
  var ings=Object.keys(DCS.catalog);
  var thr=DCS.stock.threshold_pct||60;
  var lowIngs=ings.filter(function(k) {{ var p=stkPct(k); return p!==null&&p<thr; }});
  lowIngs.sort(function(a,b) {{ return (stkPct(a)||0)-(stkPct(b)||0); }});
  var top4=lowIngs.slice(0,4);
  if (top4.length) {{
    var dismissed=stkGetDismissed();
    var cards=top4.map(function(ing) {{
      var pct=Math.max(0,stkPct(ing)||0);
      var parB=stkParBase(ing); var rem=stkRemainBase(ing); var bu=stkBaseUnit(ing);
      var isDis=!!dismissed[ing];
      var imgUrl=(DCS.stock.images||{{}})[ing]||'';
      var imgBit=imgUrl?'<img src="'+escapeHtml(imgUrl)+'" style="width:16px;height:16px;border-radius:3px;object-fit:cover;vertical-align:middle;margin-right:4px" onerror="this.style.display=\\'none\\'">':'';
      return stkWarnCardHTML({{name:ing,pct:pct,remainText:fmtQty(rem,bu)+' / '+fmtQty(parB,bu),mock:false,isDis:isDis,imgBit:imgBit}});
    }}).join('');
    return '<div class="stk-warn-section">'
      +'<div class="stk-warn-row"><span class="stk-warn-row-title">⚠️ ใกล้หมด ('+top4.length+' รายการ)</span></div>'
      +'<div class="stk-warn-grid">'+cards+'</div>'
      +'</div>';
  }}
  var mockItems=[
    {{name:'นมสด (ตัวอย่าง)',pct:14,remainText:'0.7 / 5.0 ลิตร'}},
    {{name:'เมล็ดกาแฟคั่วเข้ม (ตัวอย่าง)',pct:33,remainText:'1.0 / 3.0 กก.'}},
    {{name:'ไซรัปคาราเมล (ตัวอย่าง)',pct:49,remainText:'490 / 1,000 มล.'}},
    {{name:'แก้ว 16oz (ตัวอย่าง)',pct:58,remainText:'116 / 200 ชิ้น'}}
  ];
  var cards=mockItems.map(function(m) {{
    return stkWarnCardHTML({{name:m.name,pct:m.pct,remainText:m.remainText,mock:true,isDis:false,imgBit:''}});
  }}).join('');
  return '<div class="stk-warn-section">'
    +'<div class="stk-warn-row"><span class="stk-warn-row-title" style="text-transform:none">🎭 ตัวอย่างระบบเตือน (mockup) — จะปิดเองอัตโนมัติเมื่อมีวัตถุดิบจริงต่ำกว่าเกณฑ์</span></div>'
    +'<div class="stk-warn-grid">'+cards+'</div>'
    +'</div>';
}}

// ---- tab: สต็อกคงเหลือ ----
function stkRenderRemain() {{
  var ings=Object.keys(DCS.catalog);
  if (!ings.length) return '<div class="ov-tile ov-soon"><div class="ov-soon-emoji">📦</div><div class="ov-soon-sub">ยังไม่มีวัตถุดิบ — ตั้งค่าที่หน้า ต้นทุนเครื่องดื่ม</div></div>';
  var grpTabs='<div class="stk-gtab-row">'
    +'<button class="ov-mtab'+(stkIgrpTab==='all'?' active':'')+'" onclick="stkSetIgrp(\\'all\\')">ทั้งหมด</button>'
    +DC_IGROUPS.map(function(g) {{ return '<button class="ov-mtab'+(stkIgrpTab===g[0]?' active':'')+'" onclick="stkSetIgrp(\\''+g[0]+'\\')" >'+g[1]+'</button>'; }}).join('')
    +'</div>';
  var filtered=stkIgrpTab==='all'?ings:ings.filter(function(k) {{ return dcIngGroup(k)===stkIgrpTab; }});
  if (!filtered.length) return grpTabs+'<div class="ov-tile ov-soon"><div class="ov-soon-emoji">📦</div><div class="ov-soon-sub">ไม่มีวัตถุดิบในหมวดนี้</div></div>';
  var withPar=filtered.filter(function(k) {{ return stkPct(k)!==null; }});
  var noPar=filtered.filter(function(k) {{ return stkPct(k)===null; }});
  withPar.sort(function(a,b) {{ return (stkPct(a)||0)-(stkPct(b)||0); }});
  noPar.sort(function(a,b) {{ return a.localeCompare(b,'th'); }});
  var cards=withPar.concat(noPar).map(function(k) {{
    var bu=stkBaseUnit(k);
    var bought=stkBoughtBase(k); var usedB=stkUsedBase(k);
    var rem=stkRemainBase(k); var parB=stkParBase(k);
    var pct=stkPct(k); var low=stkLow(k);
    var barC=pct===null?'var(--text-muted)':pct>=85?'var(--dc-profit)':pct>=60?'var(--ov-caramel)':'var(--dc-warn)';
    var barW=pct===null?0:Math.min(100,Math.max(0,pct));
    var badge=low?'<span class="stk-badge warn">⚠️ ควร restock</span>':pct===null?'<span class="stk-badge muted">ตั้งสต็อกเต็มก่อน</span>':'';
    var imgUrl=(DCS.stock.images||{{}})[k]||'';
    var icon=stkIngIcon(k);
    var imgEl=imgUrl
      ?'<div class="stk-card-img"><img src="'+escapeHtml(imgUrl)+'" alt="" onerror="this.parentElement.textContent=\\''+icon+'\\'"></div>'
      :'<div class="stk-card-img">'+icon+'</div>';
    return '<div class="stk-card'+(low?' low':'')+'">'
      +imgEl
      +'<div class="stk-card-body">'
      +'<div class="stk-top"><span class="stk-name">'+escapeHtml(k)+'</span>'+badge+'</div>'
      +'<div class="stk-nums">'
      +'<span>ซื้อเข้า <b>'+fmtQty(bought,bu)+'</b></span>'
      +'<span>ใช้ไป <b>'+fmtQty(usedB,bu)+'</b></span>'
      +'<span>คงเหลือ <b>'+fmtQty(rem,bu)+'</b></span>'
      +(parB>0?'<span>สต็อกเต็ม <b>'+fmtQty(parB,bu)+'</b></span>':'')
      +'</div>'
      +'<div class="stk-bar-wrap"><div class="stk-bar-fill" style="width:'+barW+'%;background:'+barC+'"></div></div>'
      +'<div class="stk-bar-lbl">'+(pct!==null?Math.round(pct)+'%':'—')+'</div>'
      +'</div></div>';
  }}).join('');
  return grpTabs+cards;
}}

// ---- tab: การใช้ต่อเมนู ----
function stkRenderUsage() {{
  var sold=(DCS.menus||[]).filter(function(m) {{ return stkCupsForMenu(m.name)>0; }});
  if (!sold.length) return '<div class="ov-tile ov-soon"><div class="ov-soon-emoji">🧾</div><div class="ov-soon-sub">ยังไม่มียอดขาย — กดปุ่ม 🧾 ยอดขาย เพื่อบันทึก</div></div>';
  return sold.map(function(m) {{
    var cups=stkCupsForMenu(m.name);
    var ir=(m.recipe||[]).map(function(l) {{
      var tb=cups*(parseFloat(l.qty)||0);
      var c=DCS.catalog[l.ing]||{{}};
      return '<div class="stk-usage-ing">'+escapeHtml(l.ing)+': <b>'+fmtQty(tb,c.unit||'กรัม/มล.')+'</b> ('+dcF1(cups)+' แก้ว)</div>';
    }}).join('');
    return '<div class="stk-card"><div class="stk-card-body"><div class="stk-top"><span class="stk-name">'+escapeHtml(m.name)+'</span>'
      +'<span class="stk-badge muted">'+dcF1(cups)+' แก้ว</span></div>'
      +(ir?'<div class="stk-usage-ings">'+ir+'</div>':'<div class="stk-nums">ยังไม่มีสูตรเมนูนี้</div>')
      +'</div></div>';
  }}).join('');
}}

// ---- modals ----
function stkTodayISO() {{ return new Date().toISOString().slice(0,10); }}
function stkNowTime() {{ var d=new Date(); return ('0'+d.getHours()).slice(-2)+':'+('0'+d.getMinutes()).slice(-2); }}
function stkAcOpenPurch(inp) {{ dcAcOpen(inp,null); dcAcCtx.onSelect=stkOnIngSelect; }}
function stkOnIngSelect(name) {{
  var c=DCS.catalog[name]||{{}};
  var sEl=document.getElementById('stk-p-size');
  if (sEl&&!sEl.value&&c.qty) sEl.value=c.qty;
  var buEl=document.getElementById('stk-p-bu');
  if (buEl) buEl.textContent='('+(c.unit||'กรัม/มล.')+')';
  stkPurchPreview();
}}
function stkPurchPreview() {{
  var ingEl=document.getElementById('stk-p-ing');
  var ing=ingEl?(ingEl.getAttribute('data-ing')||ingEl.value||'').trim():'';
  var qty=parseFloat((document.getElementById('stk-p-qty')||{{}}).value||'')||0;
  var size=parseFloat((document.getElementById('stk-p-size')||{{}}).value||'')||0;
  var price=parseFloat((document.getElementById('stk-p-price')||{{}}).value||'')||0;
  var pr=document.getElementById('stk-p-preview'); if (!pr) return;
  var base=qty*size;
  var c=ing?(DCS.catalog[ing]||{{}}):{{}};
  var bu=c.unit||'กรัม/มล.';
  var val=price*qty;
  pr.innerHTML=base>0?'รวม: <b>'+fmtQty(base,bu)+'</b>'+(val>0?' · มูลค่า <b>฿'+dcMoney(val)+'</b>':''):'กรอกจำนวนและปริมาณ/หน่วย';
}}
function stkUnitChange() {{
  var sel=document.getElementById('stk-p-unit');
  var cu=document.getElementById('stk-p-unit-custom');
  if (!sel||!cu) return;
  cu.style.display=sel.value==='อื่นๆ'?'':'none';
}}

function stkOpenPurchase() {{
  var html='<div class="dc-modal-head"><h3>📦 บันทึกซื้อเข้า</h3>'
    +'<button class="dc-x" onclick="dcCloseModal()" aria-label="ปิด">✕</button></div>'
    +'<div class="dc-modal-scroll">'
    +'<div class="dc-field"><label>🥛 วัตถุดิบ</label>'
    +'<input class="dc-inp dc-ring" id="stk-p-ing" placeholder="ค้นหาวัตถุดิบ..." autocomplete="off"'
    +' oninput="dcAcFilter(this)" onfocus="stkAcOpenPurch(this)" onkeydown="dcAcKey(event,this)" data-ing=""></div>'
    +'<div style="display:flex;gap:10px;flex-wrap:wrap">'
    +'<div class="dc-field" style="flex:1;min-width:100px"><label>จำนวน</label>'
    +'<input class="dc-inp" id="stk-p-qty" type="number" min="0.01" step="any" placeholder="เช่น 8" oninput="stkPurchPreview()"></div>'
    +'<div class="dc-field" style="flex:1;min-width:120px"><label>หน่วย</label>'
    +'<select class="dc-inp" id="stk-p-unit" onchange="stkUnitChange()"><option value="">—เลือกหน่วย—</option>'+stkUnitOpts('แพ็ค')+'</select>'
    +'<input class="dc-inp" id="stk-p-unit-custom" placeholder="พิมพ์หน่วย..." style="display:none;margin-top:4px"></div>'
    +'</div>'
    +'<div style="display:flex;gap:10px;flex-wrap:wrap">'
    +'<div class="dc-field" style="flex:1;min-width:110px"><label>ปริมาณ/หน่วย <span id="stk-p-bu" style="color:var(--text-muted)">(กรัม/มล.)</span></label>'
    +'<input class="dc-inp" id="stk-p-size" type="number" min="0.01" step="any" placeholder="เช่น 2000" oninput="stkPurchPreview()"></div>'
    +'<div class="dc-field" style="flex:1;min-width:110px"><label>💰 ราคา/หน่วย (฿)</label>'
    +'<input class="dc-inp" id="stk-p-price" type="number" min="0" step="any" placeholder="บาท" oninput="stkPurchPreview()"></div>'
    +'</div>'
    +'<div style="display:flex;gap:10px;flex-wrap:wrap">'
    +'<div class="dc-field" style="flex:1;min-width:110px"><label>📅 วันที่</label>'
    +'<input class="dc-inp" id="stk-p-date" type="date" value="'+stkTodayISO()+'"></div>'
    +'<div class="dc-field" style="flex:1;min-width:90px"><label>⏰ เวลา</label>'
    +'<input class="dc-inp" id="stk-p-time" type="time" value="'+stkNowTime()+'"></div>'
    +'<div class="dc-field" style="flex:1;min-width:100px"><label>วิธีจ่าย</label>'
    +'<select class="dc-inp" id="stk-p-pay"><option value="cash">💵 เงินสด</option><option value="transfer">🏦 โอน</option></select></div>'
    +'</div>'
    +'<div style="display:flex;gap:10px;flex-wrap:wrap">'
    +'<div class="dc-field" style="flex:1;min-width:150px"><label>🏪 ร้าน/แหล่งซื้อ (ไม่บังคับ)</label>'
    +'<input class="dc-inp" id="stk-p-vendor" type="text" placeholder="เช่น ตลาดสกลนคร"></div>'
    +'<div class="dc-field" style="flex:2;min-width:150px"><label>หมายเหตุ</label>'
    +'<input class="dc-inp" id="stk-p-note" placeholder="—"></div>'
    +'</div>'
    +'<div class="stk-preview" id="stk-p-preview">กรอกจำนวนและปริมาณ/หน่วย</div>'
    +'</div>'
    +'<div class="dc-modal-foot"><span class="spacer"></span>'
    +'<button class="dc-btn ghost" onclick="dcCloseModal()">ยกเลิก</button>'
    +'<button class="dc-btn primary" onclick="stkSavePurchase()">💾 บันทึก</button></div>';
  dcSetModalBody(html);
}}
function stkSavePurchase() {{
  var ingEl=document.getElementById('stk-p-ing');
  var ing=ingEl?(ingEl.getAttribute('data-ing')||ingEl.value||'').trim():'';
  var qty=parseFloat((document.getElementById('stk-p-qty')||{{}}).value||'');
  var unitEl=document.getElementById('stk-p-unit');
  var cuEl=document.getElementById('stk-p-unit-custom');
  var unit=unitEl?unitEl.value:'แพ็ค';
  if (unit==='อื่นๆ'&&cuEl) unit=cuEl.value.trim()||'อื่นๆ';
  var size=parseFloat((document.getElementById('stk-p-size')||{{}}).value||'');
  var prRaw=((document.getElementById('stk-p-price')||{{}}).value||'').trim();
  var price=prRaw===''?null:(parseFloat(prRaw)||null);
  var date=(document.getElementById('stk-p-date')||{{}}).value||stkTodayISO();
  var time=(document.getElementById('stk-p-time')||{{}}).value||'';
  var pay=(document.getElementById('stk-p-pay')||{{}}).value||'cash';
  var vendor=((document.getElementById('stk-p-vendor')||{{}}).value||'').trim();
  var note=((document.getElementById('stk-p-note')||{{}}).value||'').trim();
  if (!ing) {{ showToast('เลือกวัตถุดิบก่อน'); return; }}
  if (!(qty>0)) {{ showToast('ใส่จำนวนให้ถูกต้อง'); return; }}
  if (!(size>0)) {{ showToast('ใส่ปริมาณ/หน่วยให้ถูกต้อง'); return; }}
  var rec={{date:date,ing:ing,qty:qty,unit:unit,size:size,price:price,note:note,vendor:vendor,time:time,pay:pay}};
  var doSave=function() {{
    DCS.purchases.push(rec);
    dcAfterChange(); dcCloseModal(); renderStockView();
    showToast('บันทึกซื้อ '+escapeHtml(ing)+' '+qty+' '+unit+' ✓');
  }};
  if (!dcEdit) {{
    if (saIsUnlocked()) {{ dcEdit=true; doSave(); return; }}
    dcOpenPwModal('🔒 ปลดล็อกก่อนบันทึก','ใส่รหัสเพื่อแก้ไขข้อมูลสต็อก',function() {{ dcEdit=true; saUnlock(); showToast('ปลดล็อกแล้ว ✓'); doSave(); }});
  }} else {{ doSave(); }}
}}

function stkOpenSales() {{
  var rows=''; var catsWithMenus=[];
  DC_CATS.forEach(function(cat) {{
    var catMs=(DCS.menus||[]).filter(function(m) {{ return dcCategoryOf(m)===cat; }});
    if (!catMs.length) return;
    catsWithMenus.push(cat);
    rows+='<div class="stk-sales-group" data-cat="'+cat+'">';
    rows+='<div class="stk-modal-group-label">'+(DC_CAT_ICON[cat]||'')+' '+(DC_CAT_LABEL[cat]||cat)+'</div>';
    rows+=catMs.map(function(m) {{
      var sid='ss'+Math.random().toString(36).slice(2,8);
      var nm=escapeHtml(m.name);
      return '<div class="stk-sales-row" title="'+nm+'">'
        +'<label class="stk-sales-name" for="'+sid+'">'+nm+'</label>'
        +'<input class="dc-inp stk-sales-qty" id="'+sid+'" type="number" min="0" step="1"'
        +' placeholder="0" data-mname="'+nm+'" oninput="stkSalesBadge()"></div>';
    }}).join('');
    rows+='</div>';
  }});
  var tabBar='<div class="stk-gtab-row">'
    +'<button class="ov-mtab active" data-scat="all" onclick="stkSalesFilter(\\'all\\')">ทั้งหมด'
    +' <span class="stk-tab-badge" id="stk-sales-bdg" style="display:none">0</span></button>'
    +catsWithMenus.map(function(cat) {{
      return '<button class="ov-mtab" data-scat="'+cat+'" onclick="stkSalesFilter(\\''+cat+'\\')">'+
        (DC_CAT_ICON[cat]||'')+' '+(DC_CAT_LABEL[cat]||cat)+'</button>';
    }}).join('')
    +'</div>';
  var html='<div class="dc-modal-head"><h3>🧾 บันทึกยอดขาย</h3>'
    +'<button class="dc-x" onclick="dcCloseModal()" aria-label="ปิด">✕</button></div>'
    +'<div class="dc-modal-scroll">'
    +tabBar
    +'<div class="dc-field"><label>📅 วันที่</label>'
    +'<input class="dc-inp" id="stk-s-date" type="date" value="'+stkTodayISO()+'"></div>'
    +'<div>'+rows+'</div>'
    +'</div>'
    +'<div class="dc-modal-foot"><span class="spacer"></span>'
    +'<button class="dc-btn ghost" onclick="dcCloseModal()">ยกเลิก</button>'
    +'<button class="dc-btn primary" onclick="stkSaveSales()">💾 บันทึก</button></div>';
  dcSetModalBody(html); applyRoast();
}}
function stkSaveSales() {{
  var date=(document.getElementById('stk-s-date')||{{}}).value||stkTodayISO();
  var entries=[];
  document.querySelectorAll('.stk-sales-qty').forEach(function(inp) {{
    var cups=parseFloat(inp.value||'');
    if (cups>0) entries.push({{date:date,menu:inp.getAttribute('data-mname'),cups:cups}});
  }});
  if (!entries.length) {{ showToast('ใส่ยอดขายอย่างน้อย 1 เมนู'); return; }}
  var doSave=function() {{
    entries.forEach(function(e) {{ DCS.sales.push(e); }});
    dcAfterChange(); dcCloseModal(); renderStockView();
    showToast('บันทึกยอดขาย '+entries.length+' เมนู ✓');
  }};
  if (!dcEdit) {{
    if (saIsUnlocked()) {{ dcEdit=true; doSave(); return; }}
    dcOpenPwModal('🔒 ปลดล็อกก่อนบันทึก','ใส่รหัสเพื่อแก้ไขข้อมูลสต็อก',function() {{ dcEdit=true; saUnlock(); showToast('ปลดล็อกแล้ว ✓'); doSave(); }});
  }} else {{ doSave(); }}
}}

function stkOpenPar() {{
  var thr=DCS.stock.threshold_pct||60;
  var par=DCS.stock.par||{{}};
  var imgs=DCS.stock.images||{{}};
  var rows=''; var igrpsWithIngs=[];
  DC_IGROUPS.forEach(function(g) {{
    var gIngs=Object.keys(DCS.catalog).filter(function(k) {{ return dcIngGroup(k)===g[0]; }});
    if (!gIngs.length) return;
    igrpsWithIngs.push(g);
    rows+='<div class="stk-par-group" data-igrp="'+g[0]+'">';
    rows+='<div class="stk-modal-group-label">'+g[1]+'</div>';
    rows+=gIngs.map(function(k) {{
      var pObj=par[k]; var count='',pUnit='แพ็ค',pSize='';
      if (pObj!=null) {{
        if (typeof pObj==='object') {{ count=pObj.count||''; pUnit=pObj.unit||'แพ็ค'; pSize=pObj.size||''; }}
        else {{ count=pObj; var c2=DCS.catalog[k]; pSize=c2?(c2.qty||''):''; }}
      }}
      var imgUrl=imgs[k]||'';
      var kEsc=escapeHtml(k);
      return '<div class="stk-par-item">'
        +'<div class="stk-par-head" title="'+kEsc+'">'
        +'<span class="stk-par-ingname">'+kEsc+'</span>'
        +'<div class="stk-par-field"><label>🖼 URL รูป</label>'
        +'<input class="dc-inp url-inp stk-par-img" type="url" placeholder="https://..." value="'+escapeHtml(imgUrl)+'" data-ing="'+kEsc+'"></div>'
        +'</div>'
        +'<div class="stk-par-fields">'
        +'<div class="stk-par-field"><label>จำนวน</label>'
        +'<input class="dc-inp stk-par-count" type="number" min="0" step="any" value="'+(count||'')+'" placeholder="—" data-ing="'+kEsc+'"></div>'
        +'<div class="stk-par-field"><label>หน่วย</label>'
        +'<select class="dc-inp stk-par-unit" data-ing="'+kEsc+'"><option value="">—</option>'+stkUnitOpts(pUnit)+'</select></div>'
        +'<div class="stk-par-field"><label>ปริมาณ/หน่วย</label>'
        +'<input class="dc-inp stk-par-size" type="number" min="0" step="any" value="'+(pSize||'')+'" placeholder="—" data-ing="'+kEsc+'"></div>'
        +'<span class="stk-par-bu">'+stkBaseUnit(k)+'</span>'
        +'</div></div>';
    }}).join('');
    rows+='</div>';
  }});
  var tabBar='<div class="stk-gtab-row">'
    +'<button class="ov-mtab active" data-pigrp="all" onclick="stkParFilter(\\'all\\')">ทั้งหมด</button>'
    +igrpsWithIngs.map(function(g) {{
      return '<button class="ov-mtab" data-pigrp="'+g[0]+'" onclick="stkParFilter(\\''+g[0]+'\\')">'+g[1]+'</button>';
    }}).join('')
    +'</div>';
  var html='<div class="dc-modal-head"><h3>⚙️ ตั้งสต็อกเต็ม</h3>'
    +'<button class="dc-x" onclick="dcCloseModal()" aria-label="ปิด">✕</button></div>'
    +'<div class="dc-modal-scroll">'
    +tabBar
    +'<div class="dc-field" style="margin-bottom:16px"><label>🔔 เตือนเมื่อเหลือต่ำกว่า (%)</label>'
    +'<input class="dc-inp" id="stk-par-thr" type="number" min="1" max="99" step="1" value="'+thr+'"></div>'
    +'<div>'+rows+'</div>'
    +'</div>'
    +'<div class="dc-modal-foot"><span class="spacer"></span>'
    +'<button class="dc-btn ghost" onclick="dcCloseModal()">ยกเลิก</button>'
    +'<button class="dc-btn primary" onclick="stkSavePar()">💾 บันทึก</button></div>';
  dcSetModalBody(html); applyRoast();
}}
function stkSavePar() {{
  var thr=parseFloat((document.getElementById('stk-par-thr')||{{}}).value||'');
  if (!(thr>=1&&thr<=99)) {{ showToast('ใส่เกณฑ์เตือน 1–99%'); return; }}
  var newPar={{}}, newImgs={{}};
  document.querySelectorAll('.stk-par-count').forEach(function(inp) {{
    var ing=inp.getAttribute('data-ing');
    var cnt=parseFloat(inp.value||''); if (!(cnt>0)) return;
    var uEl=document.querySelector('.stk-par-unit[data-ing="'+ing+'"]');
    var sEl=document.querySelector('.stk-par-size[data-ing="'+ing+'"]');
    var unit=uEl?(uEl.value||'แพ็ค'):'แพ็ค';
    var size=parseFloat(sEl?(sEl.value||''):'')||1;
    newPar[ing]={{count:cnt,unit:unit,size:size}};
  }});
  document.querySelectorAll('.stk-par-img').forEach(function(inp) {{
    var ing=inp.getAttribute('data-ing');
    var url=(inp.value||'').trim(); if (url) newImgs[ing]=url;
  }});
  var doSave=function() {{
    DCS.stock.threshold_pct=thr; DCS.stock.par=newPar; DCS.stock.images=newImgs;
    dcAfterChange(); dcCloseModal(); renderStockView();
    showToast('บันทึกการตั้งค่าสต็อกแล้ว ✓');
  }};
  if (!dcEdit) {{
    if (saIsUnlocked()) {{ dcEdit=true; doSave(); return; }}
    dcOpenPwModal('🔒 ปลดล็อกก่อนบันทึก','ใส่รหัสเพื่อแก้ไขข้อมูลสต็อก',function() {{ dcEdit=true; saUnlock(); showToast('ปลดล็อกแล้ว ✓'); doSave(); }});
  }} else {{ doSave(); }}
}}

// ── Roast palette (ไล่เฉด อ่อน→เข้ม) ──
var ROAST = ['#ecdcab','#d8b26f','#daa755','#d2a941','#bf914a','#9e6924','#75410a','#523828','#462506'];
function roastAt(i,n){{ if(n<=1) return ROAST[4]; var idx=Math.round(i/(n-1)*(ROAST.length-1)); return ROAST[idx]; }}
function roastInk(hex){{ var r=parseInt(hex.substr(1,2),16),g=parseInt(hex.substr(3,2),16),b=parseInt(hex.substr(5,2),16);
  return (0.299*r+0.587*g+0.114*b) > 150 ? '#3a2410' : '#f6ecda'; }}
function roastDark(hex,p){{ var n=parseInt(hex.slice(1),16); var r=(n>>16)&255,g=(n>>8)&255,b=n&255;
  r=Math.round(r*(1-p)); g=Math.round(g*(1-p)); b=Math.round(b*(1-p));
  return '#'+((1<<24)+(r<<16)+(g<<8)+b).toString(16).slice(1); }}
function colorizeRow(btns){{ var n=btns.length; btns.forEach(function(b,i){{
  var c=roastAt(i,n);
  b.style.background='linear-gradient(180deg,'+c+','+roastDark(c,0.12)+')';
  b.style.color=roastInk(c); b.style.borderColor='rgba(70,37,6,.18)';
}}); }}
function applyRoast(){{ ['.ov-mtab','.intel-tab','.pricing-tab','.trk-tab'].forEach(function(cls){{
  var groups=new Map();
  document.querySelectorAll(cls).forEach(function(b){{ var p=b.parentElement; if(!groups.has(p)) groups.set(p,[]); groups.get(p).push(b); }});
  groups.forEach(function(btns){{ colorizeRow(btns); }});
}}); }}
var _roastTimer=null;
new MutationObserver(function(){{ clearTimeout(_roastTimer); _roastTimer=setTimeout(applyRoast,60); }}).observe(document.body,{{childList:true,subtree:true}});

// ── ต้นทุนผันแปรและคงที่ (Varfix) ──
var vfRange='month';
var vfTrendChart=null;
var vfHistoryCmpMonth=null;
var vfHistoryOpen=true;
var EXP_CATS={{
  fixed:[
    {{cat:'rent',label:'ค่าเช่าร้าน',color:'#e53935'}},
    {{cat:'salary',label:'เงินเดือนพนักงาน',color:'#8e24aa'}},
    {{cat:'utility',label:'ค่าน้ำ-ไฟ',color:'#fb8c00'}},
    {{cat:'internet',label:'อินเทอร์เน็ต',color:'#00897b'}},
    {{cat:'fixed_other',label:'อื่นๆ (คงที่)',color:'#607d8b'}}
  ],
  variable:[
    {{cat:'ingredient',label:'วัตถุดิบ',color:'#1e88e5'}},
    {{cat:'packaging',label:'บรรจุภัณฑ์',color:'#3949ab'}},
    {{cat:'delivery',label:'ค่าขนส่ง',color:'#00acc1'}},
    {{cat:'marketing',label:'การตลาด',color:'#d81b60'}},
    {{cat:'var_other',label:'อื่นๆ (ผันแปร)',color:'#546e7a'}}
  ]
}};
function vfCatLabel(cat) {{
  var all=EXP_CATS.fixed.concat(EXP_CATS.variable);
  var found=all.filter(function(c) {{ return c.cat===cat; }})[0];
  return found?found.label:cat;
}}
function vfCatColor(cat) {{
  var all=EXP_CATS.fixed.concat(EXP_CATS.variable);
  var found=all.filter(function(c) {{ return c.cat===cat; }})[0];
  return found?found.color:'#607d8b';
}}
function vfCatByColor(color) {{
  var all=EXP_CATS.fixed.concat(EXP_CATS.variable);
  var found=all.filter(function(c) {{ return c.color===color; }})[0];
  return found?found.label:'อื่นๆ';
}}
function vfTodayISO() {{ var d=new Date(); return d.toISOString().slice(0,10); }}
function vfFmtDate(iso) {{
  if (!iso) return '—';
  try {{ var d=new Date(iso+'T00:00:00'); return d.toLocaleDateString('th-TH',{{year:'numeric',month:'short',day:'numeric'}}); }}
  catch(e) {{ return iso; }}
}}
function vfFmtMoney(n) {{ return '฿'+(n||0).toLocaleString('en-US',{{maximumFractionDigits:2}}); }}
function vfInRange(dateStr,range) {{
  if (!dateStr) return false;
  var today=vfTodayISO();
  if (range==='day') return dateStr===today;
  if (range==='year') return dateStr.slice(0,4)===today.slice(0,4);
  if (range==='month') return dateStr.slice(0,7)===today.slice(0,7);
  if (range==='week') {{
    var d0=new Date(today+'T00:00:00'); d0.setDate(d0.getDate()-6);
    var dI=new Date(dateStr+'T00:00:00'); return dI>=d0;
  }}
  return true;
}}
function vfSetRange(r) {{ vfRange=r; renderVarfixView(); }}
function vfMonthTH(yyyymm) {{
  if (!yyyymm||yyyymm.length<7) return '—';
  var p=yyyymm.split('-'); var y=parseInt(p[0]||'0'); var m=parseInt(p[1]||'0');
  var names=['ม.ค.','ก.พ.','มี.ค.','เม.ย.','พ.ค.','มิ.ย.','ก.ค.','ส.ค.','ก.ย.','ต.ค.','พ.ย.','ธ.ค.'];
  return (names[m-1]||'?')+' '+(y+543);
}}
function vfMonthsWithData() {{
  var seen={{}};
  (DCS.expenses||[]).forEach(function(e) {{ if (e.date) seen[e.date.slice(0,7)]=true; }});
  return Object.keys(seen).sort();
}}
function vfCatTotalsMonth(yyyymm) {{
  var t={{}};
  (DCS.expenses||[]).forEach(function(e) {{
    if (!e.date||e.date.slice(0,7)!==yyyymm) return;
    t[e.category]=(t[e.category]||0)+(e.amount||0);
  }});
  return t;
}}
function vfTrendMonths() {{
  var now=new Date(); var months=[];
  for (var i=2;i>=0;i--) {{
    var d=new Date(now.getFullYear(),now.getMonth()-i,1);
    var mo=d.getMonth()+1;
    months.push(d.getFullYear()+'-'+(mo<10?'0':'')+mo);
  }}
  return months;
}}
function vfFmtDiff(diff,base) {{
  if (diff===0) return {{txt:'—',cls:'vf-diff-nu'}};
  var sign=diff>0?'+':'';
  var pctTxt=base===0?(diff>0?' (ใหม่)':''):(' ('+sign+(diff/base*100).toFixed(1)+'%)');
  if (diff>0) return {{txt:'↑'+vfFmtMoney(diff)+pctTxt,cls:'vf-diff-up'}};
  return {{txt:'↓'+vfFmtMoney(-diff)+pctTxt,cls:'vf-diff-dn'}};
}}
function vfPurchaseBills() {{
  var byKey={{}};
  (DCS.purchases||[]).forEach(function(p) {{
    var d=p.date||''; if (!d) return;
    var v=p.vendor||'';
    var key=d+'|'+v;
    if (!byKey[key]) {{ byKey[key]={{date:d,vendor:v,items:[],pay:p.pay||'cash',time:p.time||''}}; }}
    else {{
      if (!byKey[key].pay&&p.pay) byKey[key].pay=p.pay;
      if (p.time&&p.time>byKey[key].time) byKey[key].time=p.time;
    }}
    byKey[key].items.push(p);
  }});
  return Object.keys(byKey).map(function(key) {{
    var g=byKey[key];
    var total=g.items.reduce(function(s,p) {{ return s+(p.qty&&p.price?p.qty*p.price:0); }},0);
    var safeKey=key.replace('|','_');
    return {{id:'stock-'+safeKey,date:g.date,time:g.time,vendor:g.vendor,pay:g.pay,
      group:'variable',category:'ingredient',label:'ซื้อเข้าสต็อก',amount:total,
      color:'#1e88e5',slip:'',note:'',items:g.items,readonly:true,
      _vslipKey:'V|'+g.date+'|'+(g.vendor||'')}};
  }});
}}
function vfLineTable(items) {{
  if (!items||!items.length) return '';
  var rows=items.map(function(p) {{
    var lineAmt=p.qty&&p.price?p.qty*p.price:null;
    return '<tr><td>'+escapeHtml(p.ing||'—')+'</td>'
      +'<td style="padding-left:8px;text-align:center">'+(p.qty?p.qty+(p.unit?' '+p.unit:''):'—')+'</td>'
      +'<td>'+(lineAmt?vfFmtMoney(lineAmt):'—')+'</td></tr>';
  }}).join('');
  return '<table class="vf-line-table">'+rows+'</table>';
}}
function vfReceiptCard(b) {{
  var color=b.color||'#607d8b';
  var catLabel=vfCatLabel(b.category);
  var groupLabel=b.group==='fixed'?'📌 Fixed':'📦 Variable';
  var payText=b.pay==='transfer'?'🏦 โอน':(b.pay?'💵 เงินสด':'');
  var dateTime=vfFmtDate(b.date)+(b.time?' · '+b.time:'');
  var headHtml='<div class="vf-receipt-head" style="background:'+escapeHtml(color)+'">'
    +'<span class="vf-receipt-chip">'+escapeHtml(catLabel)+'</span>'
    +(payText?'<span class="vf-pay-badge">'+payText+'</span>':'')
    +'<span class="vf-receipt-group">'+groupLabel+'</span>'
    +'<span class="vf-receipt-date">'+dateTime+'</span>'
    +'</div>';
  var readonlyBadge=b.readonly?'<span class="vf-readonly-badge">สต็อก</span>':'';
  var vendorHtml=b.vendor?'<div class="vf-vendor">🏪 '+escapeHtml(b.vendor)+'</div>':'';
  var linesHtml=(b.items&&b.items.length)?vfLineTable(b.items):'';
  var noteHtml=b.note&&!b.readonly?'<div class="vf-receipt-note">📝 '+escapeHtml(b.note)+'</div>':'';
  var _vsk=b.readonly?(b._vslipKey||''):(b.id||'');
  var _viv=b.readonly?1:0;
  var _vsu=b.readonly?((DCS.expense_slips||{{}})[b._vslipKey||'']||''):(b.slip||'');
  var _vvu=vfThumbToView(_vsu);
  var slipBtn=_vsk?(_vsu
    ?('<a href="'+escapeHtml(_vvu)+'" target="_blank" rel="noopener"><img class="vf-slip-thumb" referrerpolicy="no-referrer" loading="lazy" src="'+escapeHtml(_vsu)+'" alt="สลิป" onerror="vfSlipImgErr(this)"></a>'
     +'<button class="vf-slip-btn dc-btn" data-slipkey="'+escapeHtml(_vsk)+'" data-isvar="'+_viv+'" onclick="vfAttachSlip(this)">🔄 เปลี่ยนสลิป</button>')
    :'<button class="vf-slip-btn dc-btn" data-slipkey="'+escapeHtml(_vsk)+'" data-isvar="'+_viv+'" onclick="vfAttachSlip(this)">📎 แนบสลิป</button>')
    :'';
  var editBtns=(!b.readonly&&b.id)
    ?'<button class="vf-slip-btn dc-btn" data-expid="'+escapeHtml(b.id)+'" onclick="vfEditExpenseBtn(this)" title="แก้ไขรายจ่าย">✏️ แก้ไข</button>'
     +'<button class="vf-slip-btn dc-btn" data-expid="'+escapeHtml(b.id)+'" onclick="vfDeleteExpenseBtn(this)" style="color:#ef4444" title="ลบรายจ่าย">🗑️ ลบ</button>'
    :'';
  return '<div class="vf-receipt-card">'
    +headHtml
    +'<div class="vf-receipt-body">'
    +'<div class="vf-receipt-label">'+escapeHtml(b.label||'')+(readonlyBadge?' '+readonlyBadge:'')+'</div>'
    +vendorHtml+linesHtml+noteHtml
    +'</div>'
    +'<div class="vf-receipt-foot">'
    +'<span class="vf-receipt-total">'+vfFmtMoney(b.amount||0)+'</span>'
    +slipBtn+editBtns
    +'</div>'
    +'</div>';
}}
function vfThumbToView(thumb) {{
  if (!thumb) return '#';
  var m=thumb.match(/[?&]id=([^&]+)/);
  return m?'https://drive.google.com/file/d/'+m[1]+'/view':thumb;
}}
var _vfSlipCtx=null;
function vfSlipImgErr(img) {{
  try {{ var a=img.parentNode; img.remove(); if (a) a.textContent='🧾 ดูสลิป'; }} catch(e) {{}}
}}
var _vfNewSlip=null;
var _vfEditId=null;
function vfAttachSlip(btn) {{
  if (!saIsUnlocked()) {{ dcRequestEdit(); return; }}
  if (!dcGsUrl()) {{ showToast('เชื่อม Google Sheet ก่อน — ไปที่เมนู "เชื่อม Sheet"'); return; }}
  _vfSlipCtx={{key:btn.dataset.slipkey,isVar:btn.dataset.isvar==='1'}};
  document.getElementById('vf-slip-file-input').click();
}}
function vfAttachSlipModal() {{
  if (!saIsUnlocked()) {{ dcRequestEdit(); return; }}
  if (!dcGsUrl()) {{ showToast('เชื่อม Google Sheet ก่อน — ไปที่เมนู "เชื่อม Sheet"'); return; }}
  _vfSlipCtx={{target:'modal'}};
  document.getElementById('vf-slip-file-input').click();
}}
function vfRemoveModalSlip() {{
  _vfNewSlip=null;
  var prev=document.getElementById('vf-e-slip-preview');
  if (prev) prev.innerHTML='<button class="dc-btn ghost" onclick="vfAttachSlipModal()" style="font-size:.8rem">📎 แนบสลิป</button>';
}}
function vfSlipFileSelected(input) {{
  if (!input.files||!input.files[0]||!_vfSlipCtx) return;
  var file=input.files[0];
  var ctx=_vfSlipCtx; _vfSlipCtx=null;
  input.value='';
  var isModal=ctx.target==='modal';
  var btn=isModal?document.querySelector('#vf-e-slip-preview .dc-btn'):document.querySelector('[data-slipkey="'+ctx.key+'"]');
  if (btn) {{ btn.textContent='⏳ กำลังอัป...'; btn.disabled=true; }}
  var reader=new FileReader();
  reader.onload=function(ev) {{
    var img=new Image();
    img.onload=function() {{
      var MAX=1200,w=img.width,h=img.height;
      if (w>MAX||h>MAX) {{ var sc=MAX/Math.max(w,h); w=Math.round(w*sc); h=Math.round(h*sc); }}
      var cv=document.createElement('canvas'); cv.width=w; cv.height=h;
      cv.getContext('2d').drawImage(img,0,0,w,h);
      var b64=cv.toDataURL('image/jpeg',0.8).split(',')[1];
      var fname=(file.name||'slip').replace(/\.[^.]+$/,'')+'.jpg';
      var slipDate='';
      if (isModal) {{ var _de=document.getElementById('vf-e-date'); slipDate=_de?_de.value:''; }}
      else if (!ctx.isVar) {{ var _ex=(DCS.expenses||[]).filter(function(e) {{ return e.id===ctx.key; }})[0]; slipDate=_ex?_ex.date:''; }}
      fetch(dcGsUrl(),{{method:'POST',headers:{{'Content-Type':'text/plain;charset=utf-8'}},
        body:JSON.stringify({{action:'uploadSlip',filename:fname,mime:'image/jpeg',data:b64,date:slipDate}})}})
      .then(function(r) {{ return r.json(); }})
      .then(function(res) {{
        if (!res||!res.ok) throw new Error(res&&res.error||'upload failed');
        if (isModal) {{
          _vfNewSlip=res.thumb;
          var prev=document.getElementById('vf-e-slip-preview');
          if (prev) prev.innerHTML='<a href="'+escapeHtml(vfThumbToView(res.thumb))+'" target="_blank" rel="noopener"><img class="vf-slip-thumb" referrerpolicy="no-referrer" loading="lazy" src="'+escapeHtml(res.thumb)+'" alt="สลิป" onerror="vfSlipImgErr(this)"></a>'
            +'<span style="color:#22c55e;font-size:.8rem;font-weight:600">แนบแล้ว ✓</span>'
            +'<button class="dc-btn ghost" onclick="vfAttachSlipModal()" style="font-size:.75rem">🔄 เปลี่ยน</button>'
            +'<button class="dc-btn ghost" onclick="vfRemoveModalSlip()" style="font-size:.75rem">✕ ลบ</button>';
        }} else if (ctx.isVar) {{
          if (!DCS.expense_slips) DCS.expense_slips={{}};
          DCS.expense_slips[ctx.key]=res.thumb;
          dcAfterChange(); renderVarfixView();
        }} else {{
          var exp=DCS.expenses.find(function(e) {{ return e.id===ctx.key; }});
          if (exp) exp.slip=res.thumb;
          dcAfterChange(); renderVarfixView();
        }}
        showToast('แนบสลิปแล้ว ✓');
      }})
      .catch(function() {{
        if (isModal) {{
          var prev=document.getElementById('vf-e-slip-preview');
          if (prev) prev.innerHTML='<button class="dc-btn ghost" onclick="vfAttachSlipModal()" style="font-size:.8rem">📎 แนบสลิป</button>';
        }} else {{
          if (btn) {{ btn.textContent='📎 แนบสลิป'; btn.disabled=false; }}
        }}
        showToast('อัปไม่สำเร็จ — ตรวจว่า re-deploy Apps Script + อนุญาต Drive แล้ว');
      }});
    }};
    img.src=ev.target.result;
  }};
  reader.readAsDataURL(file);
}}
function vfMockBills() {{
  var t=vfTodayISO();
  return [
    {{id:'mock1',date:t,time:'09:00',group:'fixed',category:'rent',label:'ค่าเช่าร้าน (ตัวอย่าง)',amount:8000,color:'#e53935',slip:'',note:'',pay:'transfer',vendor:'บ้านแม่มณี (ตัวอย่าง)',readonly:true}},
    {{id:'mock2',date:t,time:'14:30',group:'fixed',category:'utility',label:'ค่าน้ำ-ไฟ (ตัวอย่าง)',amount:1200,color:'#fb8c00',slip:'',note:'',pay:'transfer',vendor:'',readonly:true}},
    {{id:'mock3',date:t,time:'07:00',group:'variable',category:'ingredient',label:'ซื้อเข้าสต็อก (ตัวอย่าง)',amount:3500,color:'#1e88e5',slip:'',note:'',pay:'cash',vendor:'ตลาดสกลนคร (ตัวอย่าง)',readonly:true,
      items:[
        {{ing:'นมสด (ตัวอย่าง)',qty:10,unit:'ลิตร',price:150}},
        {{ing:'เมล็ดกาแฟ (ตัวอย่าง)',qty:2,unit:'กก.',price:1000}},
        {{ing:'ไซรัป (ตัวอย่าง)',qty:1,unit:'ขวด',price:350}}
      ]}},
    {{id:'mock4',date:t,time:'11:15',group:'variable',category:'packaging',label:'บรรจุภัณฑ์ (ตัวอย่าง)',amount:850,color:'#3949ab',slip:'',note:'',pay:'cash',vendor:'',readonly:true}}
  ];
}}
function vfSummaryBar(displayBills,totalAmt,fixedAmt,varAmt,isMock) {{
  var mockNote=isMock?' (ตัวอย่าง)':'';
  var headHtml='<div class="vf-summary-head">'
    +'<span class="vf-summary-title">รายจ่ายรวม '+vfFmtMoney(totalAmt)+mockNote+'</span>'
    +'<span class="vf-summary-sub">Fixed '+vfFmtMoney(fixedAmt)+' · Variable '+vfFmtMoney(varAmt)+'</span>'
    +'</div>';
  if (totalAmt===0) return '<div class="vf-summary">'+headHtml+'</div>';
  var colorTotals={{}};
  displayBills.forEach(function(b) {{
    var c=b.color||'#607d8b';
    colorTotals[c]=(colorTotals[c]||0)+(b.amount||0);
  }});
  var segs=Object.keys(colorTotals).map(function(c) {{
    return {{color:c,amount:colorTotals[c]}};
  }}).sort(function(a,b) {{ return b.amount-a.amount; }});
  var barHtml=segs.map(function(s) {{
    var pct=(s.amount/totalAmt*100).toFixed(2);
    return '<div class="vf-bar-seg" style="width:'+pct+'%;background:'+escapeHtml(s.color)+'"></div>';
  }}).join('');
  var legendHtml=segs.map(function(s) {{
    var pct=Math.round(s.amount/totalAmt*100);
    var lbl=vfCatByColor(s.color);
    return '<span class="vf-legend-item">'
      +'<span class="vf-legend-dot" style="background:'+escapeHtml(s.color)+'"></span>'
      +escapeHtml(lbl)+' <span class="vf-legend-pct">'+pct+'%</span> '+vfFmtMoney(s.amount)
      +'</span>';
  }}).join('');
  return '<div class="vf-summary">'
    +headHtml
    +'<div class="vf-bar-wrap">'+barHtml+'</div>'
    +'<div class="vf-legend">'+legendHtml+'</div>'
    +'</div>';
}}
function vfBuildCmpTable(cmpYM) {{
  if (!DCS) dcLoadState();
  if (!cmpYM) return '<div class="vf-history-empty">ยังไม่มีข้อมูลเดือนก่อนให้เทียบ</div>';
  var todayYM=vfTodayISO().slice(0,7);
  var cmpTotals=vfCatTotalsMonth(cmpYM);
  var thisTotals=vfCatTotalsMonth(todayYM);
  var allCatDefs=EXP_CATS.fixed.concat(EXP_CATS.variable);
  var seen={{}};
  Object.keys(cmpTotals).forEach(function(c) {{ seen[c]=true; }});
  Object.keys(thisTotals).forEach(function(c) {{ seen[c]=true; }});
  var rows='';
  var cmpFixed=0,thisFixed=0,cmpVar=0,thisVar=0;
  (DCS.expenses||[]).forEach(function(e) {{
    if (!e.date) return;
    var ym=e.date.slice(0,7), amt=e.amount||0;
    if (ym===cmpYM) {{ if (e.group==='fixed') cmpFixed+=amt; else cmpVar+=amt; }}
    else if (ym===todayYM) {{ if (e.group==='fixed') thisFixed+=amt; else thisVar+=amt; }}
  }});
  allCatDefs.forEach(function(c) {{
    if (!seen[c.cat]) return;
    var cAmt=cmpTotals[c.cat]||0,tAmt=thisTotals[c.cat]||0;
    if (cAmt===0&&tAmt===0) return;
    var d=vfFmtDiff(tAmt-cAmt,cAmt);
    var dot='<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:'+escapeHtml(c.color)+';vertical-align:middle;margin-right:5px"></span>';
    rows+='<tr><td>'+dot+escapeHtml(c.label)+'</td><td>'+(cAmt?vfFmtMoney(cAmt):'—')+'</td><td>'+(tAmt?vfFmtMoney(tAmt):'—')+'</td><td class="'+d.cls+'">'+d.txt+'</td></tr>';
  }});
  Object.keys(seen).forEach(function(cat) {{
    if (allCatDefs.some(function(x) {{ return x.cat===cat; }})) return;
    var cAmt=cmpTotals[cat]||0,tAmt=thisTotals[cat]||0;
    if (cAmt===0&&tAmt===0) return;
    var d=vfFmtDiff(tAmt-cAmt,cAmt);
    rows+='<tr><td>'+escapeHtml(cat)+'</td><td>'+(cAmt?vfFmtMoney(cAmt):'—')+'</td><td>'+(tAmt?vfFmtMoney(tAmt):'—')+'</td><td class="'+d.cls+'">'+d.txt+'</td></tr>';
  }});
  if (!rows) return '<div class="vf-history-empty">ไม่มีรายจ่ายทั้งสองเดือนที่เลือก</div>';
  function sumRow(lbl,cA,tA) {{
    var d=vfFmtDiff(tA-cA,cA);
    return '<tr><td>'+lbl+'</td><td>'+vfFmtMoney(cA)+'</td><td>'+vfFmtMoney(tA)+'</td><td class="'+d.cls+'">'+d.txt+'</td></tr>';
  }}
  var foot=sumRow('📌 รวม Fixed',cmpFixed,thisFixed)+sumRow('📦 รวม Variable',cmpVar,thisVar)+sumRow('💰 รวมทั้งหมด',cmpFixed+cmpVar,thisFixed+thisVar);
  return '<div class="vf-cmp-wrap"><table class="vf-cmp-tbl">'
    +'<thead><tr><th>หมวด</th><th>'+escapeHtml(vfMonthTH(cmpYM))+'</th><th>เดือนนี้ ('+escapeHtml(vfMonthTH(todayYM))+')</th><th>ผลต่าง</th></tr></thead>'
    +'<tbody>'+rows+'</tbody>'
    +'<tfoot>'+foot+'</tfoot>'
    +'</table></div>';
}}
function vfBuildHistoryCard() {{
  if (!DCS) dcLoadState();
  var todayYM=vfTodayISO().slice(0,7);
  var allMonths=vfMonthsWithData();
  var prevMonths=allMonths.filter(function(m) {{ return m<todayYM; }});
  if (!vfHistoryCmpMonth||allMonths.indexOf(vfHistoryCmpMonth)===-1) {{
    vfHistoryCmpMonth=prevMonths.length?prevMonths[prevMonths.length-1]:null;
  }}
  var chevron=vfHistoryOpen?'▲':'▼';
  var selectOpts=prevMonths.length===0
    ?'<option value="">ไม่มีข้อมูลเดือนก่อน</option>'
    :prevMonths.map(function(m) {{
      return '<option value="'+m+'"'+(m===vfHistoryCmpMonth?' selected':'')+'>'+escapeHtml(vfMonthTH(m))+'</option>';
    }}).join('');
  var cmpHtml=prevMonths.length===0
    ?'<div class="vf-history-empty">ยังไม่มีข้อมูลเดือนก่อน กรุณาบันทึกรายจ่ายอย่างน้อยสองเดือน</div>'
    :vfBuildCmpTable(vfHistoryCmpMonth);
  var trendHtml='<div class="vf-trend-wrap">'
    +'<div class="vf-trend-title">📊 เทรนด์ 3 เดือนย้อนหลัง (Fixed vs Variable)</div>'
    +'<div class="vf-trend-canvas-wrap"><canvas id="vf-trend-canvas"></canvas></div>'
    +'</div>';
  return '<div class="vf-history-card">'
    +'<div class="vf-history-hdr" onclick="vfToggleHistory()">'
    +'<span>📊 ประวัติ &amp; เปรียบเทียบย้อนหลัง</span>'
    +'<span id="vf-history-chevron">'+chevron+'</span>'
    +'</div>'
    +'<div id="vf-hist-body" class="vf-history-body">'
    +'<div class="vf-cmp-toolbar">'
    +'<label style="font-weight:700;color:var(--text)">เทียบกับ:</label>'
    +'<select class="vf-cmp-sel" onchange="vfCmpMonthChange(this.value)">'+selectOpts+'</select>'
    +'<span>vs เดือนนี้ ('+escapeHtml(vfMonthTH(todayYM))+')</span>'
    +'</div>'
    +'<div id="vf-cmp-body">'+cmpHtml+'</div>'
    +trendHtml
    +'</div>'
    +'</div>';
}}
function vfInitTrendChart() {{
  if (vfTrendChart) {{ try {{ vfTrendChart.destroy(); }} catch(e) {{}} vfTrendChart=null; }}
  var canvas=document.getElementById('vf-trend-canvas');
  if (!canvas||typeof Chart==='undefined') return;
  if (!DCS) dcLoadState();
  var months=vfTrendMonths();
  var fixedData=months.map(function(ym) {{
    return (DCS.expenses||[]).filter(function(e) {{ return e.date&&e.date.slice(0,7)===ym&&e.group==='fixed'; }}).reduce(function(s,e) {{ return s+(e.amount||0); }},0);
  }});
  var varData=months.map(function(ym) {{
    return (DCS.expenses||[]).filter(function(e) {{ return e.date&&e.date.slice(0,7)===ym&&e.group==='variable'; }}).reduce(function(s,e) {{ return s+(e.amount||0); }},0);
  }});
  var labels=months.map(vfMonthTH);
  var tc=getThemeChartCfg();
  vfTrendChart=new Chart(canvas,{{
    type:'bar',
    data:{{
      labels:labels,
      datasets:[
        {{label:'Fixed',data:fixedData,backgroundColor:'rgba(229,57,53,.75)',borderColor:'#e53935',borderWidth:1,stack:'s'}},
        {{label:'Variable',data:varData,backgroundColor:'rgba(30,136,229,.75)',borderColor:'#1e88e5',borderWidth:1,stack:'s'}}
      ]
    }},
    options:{{
      responsive:true,maintainAspectRatio:false,
      plugins:{{
        legend:{{labels:{{color:tc.tick,font:{{size:11}}}}}},
        tooltip:{{backgroundColor:tc.tooltipBg,titleColor:tc.tooltipText,bodyColor:tc.tooltipText,
          callbacks:{{label:function(ctx) {{ return ctx.dataset.label+': ฿'+ctx.parsed.y.toLocaleString('en-US',{{maximumFractionDigits:2}}); }}}}}}
      }},
      scales:{{
        x:{{stacked:true,grid:{{color:tc.grid}},ticks:{{color:tc.tick,font:{{size:10}}}}}},
        y:{{stacked:true,grid:{{color:tc.grid}},ticks:{{color:tc.tick,font:{{size:10}},callback:function(v) {{ return '฿'+Number(v).toLocaleString('en-US'); }}}}}}
      }}
    }}
  }});
}}
function vfToggleHistory() {{
  vfHistoryOpen=!vfHistoryOpen;
  var bodyEl=document.getElementById('vf-hist-body');
  var chevEl=document.getElementById('vf-history-chevron');
  if (bodyEl) bodyEl.style.display=vfHistoryOpen?'':'none';
  if (chevEl) chevEl.textContent=vfHistoryOpen?'▲':'▼';
  if (vfHistoryOpen) {{ vfInitTrendChart(); }}
  else {{ if (vfTrendChart) {{ try {{ vfTrendChart.destroy(); }} catch(e) {{}} vfTrendChart=null; }} }}
}}
function vfCmpMonthChange(ym) {{
  vfHistoryCmpMonth=ym;
  var el=document.getElementById('vf-cmp-body');
  if (el) el.innerHTML=vfBuildCmpTable(ym);
}}
function renderVarfixView() {{
  var root=document.getElementById('vf-root');
  if (!root) return;
  if (!DCS) dcLoadState();
  var manualBills=(DCS.expenses||[]).map(function(e) {{ return Object.assign({{}},e,{{readonly:false}}); }});
  var stockBills=vfPurchaseBills();
  var allBills=manualBills.concat(stockBills);
  allBills.sort(function(a,b) {{ return (b.date||'').localeCompare(a.date||''); }});
  var isMock=allBills.length===0;
  var displayBills=isMock?vfMockBills():allBills.filter(function(b) {{ return vfInRange(b.date,vfRange); }});
  var totalAmt=displayBills.reduce(function(s,b) {{ return s+(b.amount||0); }},0);
  var fixedAmt=displayBills.filter(function(b) {{ return b.group==='fixed'; }}).reduce(function(s,b) {{ return s+(b.amount||0); }},0);
  var varAmt=displayBills.filter(function(b) {{ return b.group==='variable'; }}).reduce(function(s,b) {{ return s+(b.amount||0); }},0);
  var ranges=[['day','วันนี้'],['week','7 วัน'],['month','เดือนนี้'],['year','ปีนี้']];
  var tabsHtml='<div class="stk-gtab-row">'
    +ranges.map(function(rg) {{
      return '<button class="ov-mtab'+(vfRange===rg[0]?' active':'')+'" onclick="vfSetRange(\\''+rg[0]+'\\')">'+rg[1]+'</button>';
    }}).join('')+'</div>';
  var summaryHtml=vfSummaryBar(displayBills,totalAmt,fixedAmt,varAmt,isMock);
  var vfConnected=!!dcGsUrl();
  var toolbarHtml='<div class="dc-toolbar">'
    +'<button class="dc-btn" onclick="dcOpenConnect()">🔗 '+(vfConnected?'Google Sheet ✓':'เชื่อม Sheet')+'</button>'
    +(vfConnected?'<button class="dc-btn" onclick="dcSyncPull()">🔄 ซิงก์</button>':'')
    +'<span class="spacer"></span>'
    +'<button class="dc-btn primary" onclick="vfBtnAddExpense()">+ บันทึกรายจ่าย</button></div>';
  var mockHeaderHtml=isMock
    ?'<div class="stk-warn-row" style="margin-bottom:10px"><span class="stk-warn-row-title" style="text-transform:none;color:var(--text-muted)">🎭 ตัวอย่างระบบ (mockup) — จะปิดเองเมื่อมีรายจ่ายจริง</span></div>'
    :'';
  var billsHtml=displayBills.length===0
    ?'<div class="ov-tile ov-soon"><div class="ov-soon-emoji">📋</div><div class="ov-soon-sub">ยังไม่มีรายจ่ายในช่วงนี้</div></div>'
    :displayBills.map(function(b) {{ return vfReceiptCard(b); }}).join('');
  root.innerHTML=tabsHtml+summaryHtml+vfBuildHistoryCard()+toolbarHtml+mockHeaderHtml+'<div class="vf-bills">'+billsHtml+'</div>';
  var histBody=document.getElementById('vf-hist-body');
  if (histBody&&!vfHistoryOpen) histBody.style.display='none';
  if (vfHistoryOpen) vfInitTrendChart();
  var upEl=document.getElementById('vf-updated');
  if (upEl) upEl.textContent=vfFmtDate(vfTodayISO());
  applyRoast();
}}
function vfCatOpts(group,selCat) {{
  var cats=EXP_CATS[group]||[];
  return cats.map(function(c) {{
    return '<option value="'+escapeHtml(c.cat)+'"'+(selCat===c.cat?' selected':'')+' data-color="'+escapeHtml(c.color)+'">'+escapeHtml(c.label)+'</option>';
  }}).join('');
}}
function vfUpdateCatOpts() {{
  var grp=(document.getElementById('vf-e-group')||{{}}).value||'fixed';
  var sel=document.getElementById('vf-e-cat');
  if (sel) {{ sel.innerHTML=vfCatOpts(grp); vfUpdateColor(); }}
}}
function vfUpdateColor() {{
  var sel=document.getElementById('vf-e-cat');
  var cInp=document.getElementById('vf-e-color');
  if (!sel||!cInp) return;
  var opt=sel.options[sel.selectedIndex];
  if (opt) cInp.value=opt.getAttribute('data-color')||'#607d8b';
}}
function vfBtnAddExpense() {{
  if (!dcEdit) {{
    if (saIsUnlocked()) {{ dcEdit=true; vfOpenExpense(); return; }}
    dcOpenPwModal('🔒 ปลดล็อกก่อนบันทึก','ใส่รหัสเพื่อบันทึกรายจ่าย',function() {{
      dcEdit=true; saUnlock(); showToast('ปลดล็อกแล้ว ✓'); vfOpenExpense();
    }});
  }} else {{ vfOpenExpense(); }}
}}
function vfEditExpenseBtn(btn) {{
  var id=btn.dataset.expid;
  if (!saIsUnlocked()) {{ dcRequestEdit(); return; }}
  vfOpenExpense(id);
}}
function vfDeleteExpenseBtn(btn) {{
  var id=btn.dataset.expid;
  vfDeleteExpense(id);
}}
function vfDeleteExpense(id) {{
  if (!saIsUnlocked()) {{ dcRequestEdit(); return; }}
  var exp=(DCS.expenses||[]).filter(function(e) {{ return e.id===id; }})[0];
  if (!exp) return;
  if (!confirm('ลบรายจ่าย "'+exp.label+'" จำนวน '+vfFmtMoney(exp.amount||0)+'?\\nกดตกลงเพื่อยืนยัน')) return;
  DCS.expenses=DCS.expenses.filter(function(e) {{ return e.id!==id; }});
  dcAfterChange(); renderVarfixView(); showToast('ลบรายจ่ายแล้ว ✓');
}}
function vfOpenExpense(id) {{
  var exp=id?(DCS.expenses||[]).filter(function(e) {{ return e.id===id; }})[0]:null;
  _vfEditId=exp?id:null;
  var defGroup=exp?(exp.group||'fixed'):'fixed';
  var defSlip=exp?(exp.slip||''):'';
  if (exp) _vfNewSlip=defSlip;
  var title=exp?'✏️ แก้ไขรายจ่าย':'📋 บันทึกรายจ่าย';
  var saveLabel=exp?'💾 อัปเดต':'💾 บันทึก';
  var groupOpts='<option value="fixed"'+(defGroup==='fixed'?' selected':'')+'>Fixed (ต้นทุนคงที่)</option>'
    +'<option value="variable"'+(defGroup==='variable'?' selected':'')+'>Variable (ต้นทุนผันแปร)</option>';
  var slipPrev=defSlip
    ?('<a href="'+escapeHtml(vfThumbToView(defSlip))+'" target="_blank" rel="noopener"><img class="vf-slip-thumb" referrerpolicy="no-referrer" loading="lazy" src="'+escapeHtml(defSlip)+'" alt="สลิป" onerror="vfSlipImgErr(this)"></a>'
      +'<span style="color:#22c55e;font-size:.8rem;font-weight:600">แนบแล้ว ✓</span>'
      +'<button class="dc-btn ghost" onclick="vfAttachSlipModal()" style="font-size:.75rem">🔄 เปลี่ยน</button>'
      +'<button class="dc-btn ghost" onclick="vfRemoveModalSlip()" style="font-size:.75rem">✕ ลบ</button>')
    :'<button class="dc-btn ghost" onclick="vfAttachSlipModal()" style="font-size:.8rem">📎 แนบสลิป</button>';
  var html='<div class="dc-modal-head"><h3>'+title+'</h3><button class="dc-x" onclick="dcCloseModal()" aria-label="ปิด">✕</button></div>'
    +'<div class="dc-modal-scroll">'
    +'<div class="dc-field"><label>📅 วันที่</label><input class="dc-inp" id="vf-e-date" type="date" value="'+(exp?escapeHtml(exp.date||''):vfTodayISO())+'"></div>'
    +'<div class="dc-field"><label>กลุ่ม</label>'
    +'<select class="dc-inp" id="vf-e-group" onchange="vfUpdateCatOpts()">'+groupOpts+'</select></div>'
    +'<div class="dc-field"><label>หมวด</label>'
    +'<select class="dc-inp" id="vf-e-cat" onchange="vfUpdateColor()">'+vfCatOpts(defGroup,exp&&exp.category)+'</select></div>'
    +'<div class="dc-field"><label>รายการ</label><input class="dc-inp" id="vf-e-label" type="text" placeholder="เช่น ค่าเช่าร้าน มิถุนายน 2569" value="'+(exp?escapeHtml(exp.label||''):'')+'"></div>'
    +'<div class="dc-field"><label>จำนวนเงิน (฿)</label><input class="dc-inp" id="vf-e-amount" type="number" min="0" step="0.01" placeholder="0" value="'+(exp&&exp.amount?exp.amount:'')+'"></div>'
    +'<div class="dc-field"><label>สี (แสดงในบิล)</label><input class="dc-inp" id="vf-e-color" type="color" value="'+(exp?escapeHtml(exp.color||'#e53935'):'#e53935')+'" style="height:40px;padding:4px 6px;cursor:pointer"></div>'
    +'<div style="display:flex;gap:10px;flex-wrap:wrap">'
    +'<div class="dc-field" style="flex:1;min-width:110px"><label>วิธีจ่าย</label>'
    +'<select class="dc-inp" id="vf-e-pay">'
    +'<option value="cash"'+(!exp||exp.pay!=="transfer"?' selected':'')+'>💵 เงินสด</option>'
    +'<option value="transfer"'+(exp&&exp.pay==="transfer"?' selected':'')+'>🏦 โอน</option>'
    +'</select></div>'
    +'<div class="dc-field" style="flex:2;min-width:150px"><label>🏪 ร้าน/ผู้รับเงิน (ไม่บังคับ)</label>'
    +'<input class="dc-inp" id="vf-e-vendor" type="text" placeholder="—" value="'+(exp?escapeHtml(exp.vendor||''):'')+'"></div>'
    +'</div>'
    +'<div class="dc-field"><label>หมายเหตุ (ถ้ามี)</label><input class="dc-inp" id="vf-e-note" type="text" placeholder="—" value="'+(exp?escapeHtml(exp.note||''):'')+'"></div>'
    +'<div class="dc-field"><label>สลิปใบเสร็จ</label>'
    +'<div id="vf-e-slip-preview" style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">'+slipPrev+'</div></div>'
    +'</div>'
    +'<div class="dc-modal-foot"><span class="spacer"></span>'
    +'<button class="dc-btn ghost" onclick="dcCloseModal()">ยกเลิก</button>'
    +'<button class="dc-btn primary" onclick="vfSaveExpense()">'+saveLabel+'</button>'
    +'</div>';
  dcSetModalBody(html);
}}
function vfSaveExpense() {{
  var date=(document.getElementById('vf-e-date')||{{}}).value||vfTodayISO();
  var group=(document.getElementById('vf-e-group')||{{}}).value||'fixed';
  var category=(document.getElementById('vf-e-cat')||{{}}).value||'fixed_other';
  var label=((document.getElementById('vf-e-label')||{{}}).value||'').trim();
  var amount=parseFloat((document.getElementById('vf-e-amount')||{{}}).value||'');
  var color=(document.getElementById('vf-e-color')||{{}}).value||'#607d8b';
  var pay=(document.getElementById('vf-e-pay')||{{}}).value||'cash';
  var vendor=((document.getElementById('vf-e-vendor')||{{}}).value||'').trim();
  var note=((document.getElementById('vf-e-note')||{{}}).value||'').trim();
  if (!label) {{ showToast('ใส่ชื่อรายการก่อน'); return; }}
  if (!(amount>0)) {{ showToast('ใส่จำนวนเงินก่อน'); return; }}
  var doSave=function() {{
    if (_vfEditId) {{
      var found=(DCS.expenses||[]).filter(function(e) {{ return e.id===_vfEditId; }})[0];
      var capturedSlip=_vfNewSlip;
      _vfNewSlip=null; _vfEditId=null;
      if (found) {{
        found.date=date; found.group=group; found.category=category; found.label=label;
        found.amount=amount; found.color=color; found.slip=capturedSlip||'';
        found.note=note; found.pay=pay; found.vendor=vendor;
      }}
      dcAfterChange(); dcCloseModal(); renderVarfixView(); showToast('อัปเดตรายจ่ายแล้ว ✓');
    }} else {{
      var exp={{id:Date.now().toString(36)+Math.random().toString(36).slice(2,6),
        date:date,group:group,category:category,label:label,amount:amount,color:color,slip:_vfNewSlip||'',note:note,pay:pay,vendor:vendor}};
      _vfNewSlip=null;
      DCS.expenses.push(exp);
      dcAfterChange(); dcCloseModal(); renderVarfixView(); showToast('บันทึกรายจ่ายแล้ว ✓');
    }}
  }};
  if (!dcEdit) {{
    if (saIsUnlocked()) {{ dcEdit=true; doSave(); return; }}
    dcOpenPwModal('🔒 ปลดล็อกบันทึกรายจ่าย','ใส่รหัสเพื่อบันทึกรายจ่าย',function() {{ dcEdit=true; saUnlock(); doSave(); }});
  }} else {{
    doSave();
  }}
}}

// ── POS Import (Loyverse) ──────────────────────────────────────────────────
var posRange = 'today';
var posFromDate = '';
var posToDate = '';

function posSetRange(r) {{ posRange = r; renderPosImportView(); }}

function posTodayTH() {{
  var now = new Date();
  var d = new Date(now.getTime() + 7 * 3600000);
  var y = d.getUTCFullYear(), m = d.getUTCMonth() + 1, dd = d.getUTCDate();
  return y + '-' + (m < 10 ? '0' : '') + m + '-' + (dd < 10 ? '0' : '') + dd;
}}

// แปลง TH date string → UTC ISO (addDay=true → วันถัดไป เพื่อ exclusive end boundary)
function posThToUtcIso(dateStr, addDay) {{
  var p = dateStr.split('-');
  var ms = Date.UTC(+p[0], +p[1] - 1, +p[2], 0, 0, 0) - 7 * 3600000;
  if (addDay) ms += 86400000;
  return new Date(ms).toISOString();
}}

function posGetRange() {{
  var today = posTodayTH();
  if (posRange === 'today') {{
    return {{ from: posThToUtcIso(today, false), to: posThToUtcIso(today, true) }};
  }} else if (posRange === 'month') {{
    var p = today.split('-'); var y = +p[0], m = +p[1];
    var first = y + '-' + (m < 10 ? '0' : '') + m + '-01';
    var nm = m + 1, ny = y; if (nm > 12) {{ nm = 1; ny++; }}
    var nextM = ny + '-' + (nm < 10 ? '0' : '') + nm + '-01';
    return {{ from: posThToUtcIso(first, false), to: posThToUtcIso(nextM, false) }};
  }} else {{
    var fd = posFromDate || today, td = posToDate || today;
    return {{ from: posThToUtcIso(fd, false), to: posThToUtcIso(td, true) }};
  }}
}}

function posFmt(n) {{ return Number(n||0).toLocaleString('th-TH',{{minimumFractionDigits:2,maximumFractionDigits:2}}); }}
function posInt(n) {{ return Math.round(Number(n||0)).toLocaleString('th-TH'); }}

function renderPosImportView() {{
  if (!DCS) dcLoadState();
  var root = document.getElementById('pos-root');
  if (!root) return;
  var gsUrl = dcGsUrl();
  if (!gsUrl) {{
    root.innerHTML = '<div class="ov-tile ov-soon">'
      + '<div class="ov-soon-emoji">🔗</div>'
      + '<div class="ov-soon-title">ยังไม่ได้เชื่อม Google Sheet</div>'
      + '<div class="ov-soon-sub">กด "เชื่อม Sheet" ในหน้าต้นทุนเครื่องดื่ม หรือต้นทุนผันแปร แล้วใส่ Web App URL ของ Apps Script ที่ Deploy แล้ว</div>'
      + '<button class="dc-btn" style="margin-top:12px" onclick="dcOpenConnect()">🔗 เชื่อม Google Sheet</button>'
      + '</div>';
    return;
  }}
  var ranges = [['today','วันนี้'],['month','เดือนนี้'],['custom','ช่วงเอง']];
  var tabsHtml = '<div class="stk-gtab-row">'
    + ranges.map(function(rg) {{
      return '<button class="ov-mtab'+(posRange===rg[0]?' active':'')+'" onclick="posSetRange(\\''+rg[0]+'\\')">'+rg[1]+'</button>';
    }}).join('') + '</div>';
  var today = posTodayTH();
  if (!posFromDate) posFromDate = today;
  if (!posToDate)   posToDate   = today;
  var customHtml = posRange === 'custom'
    ? '<div class="pos-custom-row"><label>จาก'
      + ' <input type="date" id="pos-from" value="'+posFromDate+'" onchange="posFromDate=this.value"></label>'
      + '<label>ถึง'
      + ' <input type="date" id="pos-to" value="'+posToDate+'" onchange="posToDate=this.value"></label>'
      + '</div>'
    : '';
  var fetchBtn = '<div style="margin:14px 0 10px">'
    + '<button class="dc-btn primary" id="pos-fetch-btn" onclick="posFetch()">📥 ดึงยอดขายจาก POS</button>'
    + '</div>';
  root.innerHTML = tabsHtml + customHtml + fetchBtn + '<div id="pos-result"></div>';
  if (DCS.posLast && DCS.posLast.data) posRenderResult(DCS.posLast.data, true);
  var upEl = document.getElementById('pos-updated');
  if (upEl && DCS.posLast && DCS.posLast.fetchedAt) {{
    upEl.textContent = new Date(DCS.posLast.fetchedAt).toLocaleString('th-TH');
  }}
}}

function posRenderResult(data, fromCache) {{
  var el = document.getElementById('pos-result');
  if (!el) return;
  if (!data.ok) {{
    var errMsg = data.error === 'no_token'
      ? '⚠️ ยังไม่ได้ตั้ง LOYVERSE_TOKEN ใน Apps Script<br>'
        + '<small style="font-weight:400">Apps Script → ⚙️ Project Settings → Script Properties'
        + ' → เพิ่ม key: <code>LOYVERSE_TOKEN</code> = token จาก Loyverse Back Office</small>'
      : '❌ ดึงข้อมูลไม่สำเร็จ: ' + escapeHtml(String(data.error));
    el.innerHTML = '<div class="stk-warn-row" style="padding:16px;border-radius:10px">'+errMsg+'</div>';
    return;
  }}
  var receipts  = data.receipts   || [];
  var items     = data.items      || [];
  var categories= data.categories || [];

  // lookup maps
  var catMap = {{}};
  categories.forEach(function(c) {{ catMap[c.id||''] = c.name || ''; }});
  var itemCatMap = {{}};
  items.forEach(function(it) {{ itemCatMap[it.id||''] = catMap[it.category_id||''] || ''; }});

  var sales   = receipts.filter(function(r) {{ return r.receipt_type === 'SALE'; }});
  var refunds = receipts.filter(function(r) {{ return r.receipt_type === 'REFUND'; }});
  var salesAmt  = sales.reduce(function(s,r) {{ return s + Number(r.total_money||0); }}, 0);
  var refundAmt = refunds.reduce(function(s,r) {{ return s + Math.abs(Number(r.total_money||0)); }}, 0);
  var netAmt    = salesAmt - refundAmt;

  // per-category: SALE adds, REFUND subtracts
  var catTotals = {{}};
  function addCatLine(lines, sign) {{
    lines.forEach(function(li) {{
      var cat = itemCatMap[li.item_id||''] || '(ไม่มีหมวด)';
      if (!catTotals[cat]) catTotals[cat] = {{cups:0, amt:0}};
      catTotals[cat].cups += sign * Math.abs(Number(li.quantity||0));
      catTotals[cat].amt  += sign * Math.abs(Number(li.total_money||0));
    }});
  }}
  sales.forEach(function(r)   {{ addCatLine(r.line_items||[], +1); }});
  refunds.forEach(function(r) {{ addCatLine(r.line_items||[], -1); }});

  // per-menu
  var menuTotals = {{}};
  function addMenuLine(lines, sign) {{
    lines.forEach(function(li) {{
      var mn  = li.item_name || li.item_id || '?';
      var cat = itemCatMap[li.item_id||''] || '(ไม่มีหมวด)';
      if (!menuTotals[mn]) menuTotals[mn] = {{cat:cat, cups:0, amt:0}};
      menuTotals[mn].cups += sign * Math.abs(Number(li.quantity||0));
      menuTotals[mn].amt  += sign * Math.abs(Number(li.total_money||0));
    }});
  }}
  sales.forEach(function(r)   {{ addMenuLine(r.line_items||[], +1); }});
  refunds.forEach(function(r) {{ addMenuLine(r.line_items||[], -1); }});

  var catKeys  = Object.keys(catTotals).sort(function(a,b) {{ return catTotals[b].amt - catTotals[a].amt; }});
  var menuKeys = Object.keys(menuTotals).sort(function(a,b) {{ return menuTotals[b].amt - menuTotals[a].amt; }});
  var bestCat  = catKeys.length ? catKeys[0] : '';

  // name-match
  var dcsNames = (DCS && DCS.menus ? DCS.menus : [])
    .map(function(m) {{ return (m.name||'').trim().toLowerCase(); }});
  var lvNames  = items.map(function(it) {{ return (it.item_name||'').trim(); }});
  var matched = [], unmatched = [];
  lvNames.forEach(function(n) {{
    (dcsNames.indexOf(n.toLowerCase()) >= 0 ? matched : unmatched).push(n);
  }});

  if (receipts.length === 0) {{
    el.innerHTML = '<div class="ov-tile ov-soon" style="margin-top:12px">'
      + '<div class="ov-soon-emoji">📭</div>'
      + '<div class="ov-soon-sub">ไม่มียอดขายในช่วงที่เลือก</div></div>';
    return;
  }}

  var cacheHtml = fromCache
    ? '<div style="color:var(--text-muted);font-size:.8rem;margin-bottom:8px">⏱ แสดง cache — กด ดึงยอดขาย เพื่ออัปเดต</div>'
    : '';
  var noCatWarn = catKeys.indexOf('(ไม่มีหมวด)') >= 0
    ? '<div class="stk-warn-row" style="margin-bottom:8px">⚠️ มีเมนูที่ยังไม่ตั้งหมวดหมู่ใน Loyverse — แนะนำตั้ง กาแฟ / ชา / นม / โซดา</div>'
    : '';

  var cardsHtml = '<div class="pos-card-row">'
    + '<div class="pos-card"><div class="pos-card-label">ยอดขาย</div>'
    +   '<div class="pos-card-val">฿'+posFmt(salesAmt)+'</div>'
    +   '<div class="pos-card-sub">'+sales.length+' บิล</div></div>'
    + '<div class="pos-card refund"><div class="pos-card-label">คืนเงิน</div>'
    +   '<div class="pos-card-val">฿'+posFmt(refundAmt)+'</div>'
    +   '<div class="pos-card-sub">'+refunds.length+' บิล</div></div>'
    + '<div class="pos-card '+(netAmt >= 0 ? 'net' : 'net-neg')+'">'
    +   '<div class="pos-card-label">ยอดสุทธิ</div>'
    +   '<div class="pos-card-val">฿'+posFmt(netAmt)+'</div>'
    +   '<div class="pos-card-sub">API '+data.pages+' หน้า</div></div>'
    + '</div>';

  var catRowsHtml = catKeys.map(function(cat) {{
    var isBest = cat === bestCat;
    return '<tr'+(isBest?' class="pos-best-row"':'')+'>'+
      '<td>'+(isBest?'🏆 ':'')+(cat==='(ไม่มีหมวด)'?'<span style="color:var(--text-muted)">'+cat+'</span>':escapeHtml(cat))+'</td>'+
      '<td style="text-align:right">'+posInt(catTotals[cat].cups)+'</td>'+
      '<td style="text-align:right">'+posFmt(catTotals[cat].amt)+'</td></tr>';
  }}).join('');
  var catTableHtml = '<div class="pos-section"><h3 class="pos-section-title">ยอดขายตามหมวดหมู่</h3>'
    + (catKeys.length
      ? '<table class="dc-table" style="width:100%"><thead><tr><th>หมวด</th><th style="text-align:right">แก้ว</th><th style="text-align:right">ยอด (฿)</th></tr></thead><tbody>'+catRowsHtml+'</tbody></table>'
      : '<div class="ov-soon-sub">ยังไม่มีหมวดหมู่ใน Loyverse</div>')
    + '</div>';

  var menuShow = menuKeys.slice(0, 30);
  var menuRowsHtml = menuShow.map(function(mn) {{
    var t = menuTotals[mn];
    return '<tr><td>'+escapeHtml(mn)+'</td>'
      +'<td style="color:var(--text-muted);font-size:.85em">'+escapeHtml(t.cat)+'</td>'
      +'<td style="text-align:right">'+posInt(t.cups)+'</td>'
      +'<td style="text-align:right">'+posFmt(t.amt)+'</td></tr>';
  }}).join('');
  var moreRowHtml = menuKeys.length > 30
    ? '<tr><td colspan="4" style="color:var(--text-muted);text-align:center;font-size:.85em">... และอีก '+(menuKeys.length-30)+' รายการ</td></tr>'
    : '';
  var menuTableHtml = '<div class="pos-section">'
    + '<h3 class="pos-section-title">ยอดขายตามเมนู ('+menuKeys.length+' รายการ)</h3>'
    + (menuShow.length
      ? '<table class="dc-table" style="width:100%"><thead><tr><th>เมนู</th><th>หมวด</th><th style="text-align:right">แก้ว</th><th style="text-align:right">ยอด (฿)</th></tr></thead><tbody>'+menuRowsHtml+moreRowHtml+'</tbody></table>'
      : '')
    + '</div>';

  var catChipsHtml = categories.length
    ? categories.map(function(c) {{ return '<span class="pos-cat-chip">'+escapeHtml(c.name)+'</span>'; }}).join(' ')
    : '<span style="color:#f59e0b;font-weight:600">ยังไม่มีหมวดหมู่ — ตั้งค่าใน Loyverse POS ก่อน</span>';
  var matchHtml = ''
    + (matched.length
      ? '<div class="pos-diag-row">✅ จับคู่กับเมนูร้านได้ ('+matched.length+'): '
        +matched.map(function(n) {{ return '<span class="pos-cat-chip ok">'+escapeHtml(n)+'</span>'; }}).join(' ')+'</div>'
      : '')
    + (unmatched.length
      ? '<div class="pos-diag-row">⚠️ ชื่อยังไม่ตรงกับเมนูร้าน ('+unmatched.length+'): '
        +unmatched.map(function(n) {{ return '<span class="pos-cat-chip warn">'+escapeHtml(n)+'</span>'; }}).join(' ')+'</div>'
      : '');
  var diagHtml = '<div class="pos-section pos-diag">'
    + '<h3 class="pos-section-title">🔍 Diagnostic</h3>'
    + '<div class="pos-diag-row">ดึงมา <b>'+receipts.length+'</b> บิล'
    +   ' (SALE: <b>'+sales.length+'</b> · REFUND: <b>'+refunds.length+'</b>)'
    +   ' · ใช้ <b>'+data.pages+'</b> หน้า API</div>'
    + '<div class="pos-diag-row">หมวดหมู่ใน Loyverse: '+catChipsHtml+'</div>'
    + '<div class="pos-diag-row">เมนูใน Loyverse: <b>'+lvNames.length+'</b> รายการ'
    +   ' · จับคู่กับเมนูร้านได้: <b>'+matched.length+'</b> / '+lvNames.length+'</div>'
    + matchHtml
    + '</div>';

  el.innerHTML = cacheHtml + noCatWarn + cardsHtml + catTableHtml + menuTableHtml + diagHtml;
}}

function posFetch() {{
  if (!DCS) dcLoadState();
  var url = dcGsUrl();
  if (!url) {{ showToast('เชื่อม Google Sheet ก่อน'); return; }}
  var btn = document.getElementById('pos-fetch-btn');
  if (btn) {{ btn.disabled = true; btn.textContent = '⏳ กำลังดึง...'; }}
  var resEl = document.getElementById('pos-result');
  if (resEl) resEl.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted)">⏳ กำลังดึงข้อมูลจาก Loyverse...</div>';
  var rng = posGetRange();
  var fetchUrl = url + '?action=loyverse&from=' + encodeURIComponent(rng.from) + '&to=' + encodeURIComponent(rng.to);
  fetch(fetchUrl)
    .then(function(r) {{ return r.json(); }})
    .then(function(data) {{
      if (btn) {{ btn.disabled = false; btn.textContent = '📥 ดึงยอดขายจาก POS'; }}
      DCS.posLast = {{ range: posRange, fromDate: posFromDate, toDate: posToDate,
                       data: data, fetchedAt: new Date().toISOString() }};
      dcSave();
      posRenderResult(data, false);
      var upEl = document.getElementById('pos-updated');
      if (upEl) upEl.textContent = new Date(DCS.posLast.fetchedAt).toLocaleString('th-TH');
    }})
    .catch(function(err) {{
      if (btn) {{ btn.disabled = false; btn.textContent = '📥 ดึงยอดขายจาก POS'; }}
      if (resEl) resEl.innerHTML = '<div class="stk-warn-row">❌ เชื่อมต่อไม่ได้: '+escapeHtml(String(err))+'</div>';
    }});
}}

// ════════════════════════════════════
//  Quest & Achievement (90 Days)
// ════════════════════════════════════

var MOTIVATIONS = [
  '"วันนี้ดีกว่าเมื่อวาน — แค่นี้ก็พอ"',
  '"กาแฟดีทำจากความพิถีพิถัน — ธุรกิจดีก็เช่นกัน"',
  '"ทุกวันที่ลงมือทำ คือก้าวที่เข้าใกล้ฝันมากขึ้น"',
  '"อย่ารอให้พร้อม — เริ่มแล้วค่อยพร้อม"',
  '"ร้านกาแฟไม่ได้สร้างในวันเดียว แต่สร้างทีละวัน"',
  '"ความสม่ำเสมอคือพลังที่ยิ่งใหญ่กว่าแรงบันดาลใจ"',
  '"Focus on the process, not just the goal"',
  '"เจ้าของร้านกาแฟที่ดี คือคนที่ไม่หยุดเรียนรู้"',
  '"ทำทีละอย่าง แต่ทำให้ดี"',
  '"ลูกค้าคนแรกอาจเปลี่ยนชีวิตเราได้"',
  '"ทุก ขอบคุณ จากลูกค้า คือพลังงานที่เติมให้เราสู้ต่อ"',
  '"ธุรกิจที่ดีเริ่มจากการแก้ปัญหาให้คนอื่น"',
  '"วันที่ยากที่สุด มักเป็นวันที่สอนเราได้มากที่สุด"',
  '"Plan the work — Work the plan"',
  '"ร้านกาแฟคือพื้นที่แห่งความสุขของชุมชน"',
  '"คนที่ประสบความสำเร็จทำสิ่งที่คนอื่นไม่อยากทำ"',
  '"เริ่มต้นดี มีชัยไปกว่าครึ่ง"',
  '"ทำในสิ่งที่รัก รักในสิ่งที่ทำ"',
  '"ความสำเร็จไม่ได้มาในวันเดียว แต่ทุกวันที่ทำ คือการสร้างความสำเร็จ"',
  '"จงเป็นกาแฟที่ดีที่สุดในสกลนคร"',
  '"อุปสรรคคือโอกาสที่ยังไม่ได้เปิด"',
  '"เปิดร้านกาแฟ ≠ ขายกาแฟ — คือสร้างประสบการณ์"',
  '"คนที่รอจะไม่มีวันพร้อม — คนที่เริ่มจะค่อยๆ พร้อม"',
  '"ทบทวนทุกวัน เติบโตทุกสัปดาห์"',
  '"90 วัน = 90 โอกาสที่จะดีกว่าเดิม"',
  '"ร้านที่ดีไม่ใช่แค่รสชาติ — แต่คือความรู้สึก"',
  '"เป็นผู้ประกอบการ คือกล้าที่จะผิดพลาดและเรียนรู้"',
  '"ทุกเมนูที่ชงออกไป คือตัวแทนของความตั้งใจเรา"',
  '"สกลนครจะรู้จัก PENGTANG CAFE — เริ่มตั้งแต่วันนี้"',
  '"วันที่ 90 คือแค่จุดเริ่มต้น — ก้าวต่อไปไม่มีที่สิ้นสุด"'
];

var BUFFS = [
  '💪 Focus Mode — ปิด Noti ทำงานลึก 90 นาที',
  '🎵 Buff เพลง — เปิดเพลย์ลิสต์ที่ชอบแล้วลงมือทำ',
  '📝 Brain Dump — เขียนทุกอย่างที่ค้างในหัวออกมาก่อน',
  '🚶 Walk & Think — เดิน 10 นาที แล้วกลับมาตัดสินใจ',
  '☕ Coffee First — ชงกาแฟแก้วโปรด แล้วค่อยเริ่ม',
  '🧹 2-Minute Rule — งานไหนทำได้ใน 2 นาที ทำเลย',
  '📸 Document Day — ถ่ายรูป/วิดีโอ progress วันนี้',
  '🤝 Ask for Help — วันนี้ถามคนที่รู้มากกว่า 1 คน',
  '📊 Review Numbers — เช็คตัวเลขต้นทุนและรายรับวันนี้',
  '🎯 One Thing — เลือก 1 งานที่สำคัญที่สุด ทำให้เสร็จก่อน',
  '🌱 Learn Mode — อ่านหรือดูคอนเทนต์เกี่ยวกับร้านกาแฟ 15 นาที',
  '💬 Customer Story — คุยกับลูกค้า/คนรู้จัก เก็บ feedback',
  '🔧 Fix One Thing — แก้ปัญหาเล็กๆ ที่ค้างมาสักพัก',
  '📱 Content Day — สร้าง content ร้านอย่างน้อย 1 ชิ้น',
  '🧠 Strategy Hour — นั่งคิดแผน 1 ชั่วโมงโดยไม่มีสิ่งรบกวน',
  '💡 Idea Dump — เขียนไอเดียใหม่ๆ ออกมา 10 ข้อ',
  '🏃 Energy Boost — ออกกำลังกาย/ยืดเส้น 15 นาทีก่อนเริ่มงาน',
  '🗓️ Plan Tomorrow — วางแผนวันพรุ่งนี้ตั้งแต่คืนนี้',
  '🙏 Gratitude Mode — จด 3 สิ่งที่ขอบคุณวันนี้ก่อนนอน',
  '⚡ Sprint Day — ตั้งเวลา 25 นาที ทำงานไม่หยุด × 4 รอบ'
];

var QUEST_CAT = {{
  site:       {{icon:'🏗️', label:'หน้างาน'}},
  think:      {{icon:'🧠', label:'คิด/วางแผน'}},
  content:    {{icon:'📱', label:'คอนเทนต์'}},
  plan:       {{icon:'📋', label:'แผนงาน'}},
  cost:       {{icon:'💰', label:'ต้นทุน'}},
  system:     {{icon:'🔧', label:'ระบบ'}},
  legal:      {{icon:'📜', label:'กฎหมาย'}},
  brand:      {{icon:'🎨', label:'แบรนด์'}},
  supply:     {{icon:'🛒', label:'วัตถุดิบ'}},
  marketing:  {{icon:'📣', label:'การตลาด'}},
  hygiene:    {{icon:'🧼', label:'สุขลักษณะ'}},
  experience: {{icon:'🪑', label:'ประสบการณ์'}}
}};

var ACH_CAT = {{
  milestone: {{icon:'🎯', label:'Milestone'}},
  planning:  {{icon:'📋', label:'วางแผน'}},
  setup:     {{icon:'🏗️', label:'ติดตั้ง'}},
  legal:     {{icon:'📜', label:'กฎหมาย'}},
  brand:     {{icon:'🎨', label:'แบรนด์'}},
  system:    {{icon:'🔧', label:'ระบบ'}},
  marketing: {{icon:'📣', label:'การตลาด'}},
  launch:    {{icon:'🚀', label:'เปิดร้าน'}},
  financial: {{icon:'💰', label:'การเงิน'}}
}};

var LOOP_STG = {{
  learn:   {{icon:'📚', label:'หาความรู้'}},
  do:      {{icon:'🔨', label:'ลงมือทำ'}},
  improve: {{icon:'🔍', label:'ปรับปรุง'}},
  repeat:  {{icon:'♻️', label:'ทำซ้ำ'}}
}};

var DEFAULT_QUESTS_SEED = [
  {{id:'q01',title:'สำรวจร้านและถ่ายรูปสภาพปัจจุบัน',cat:'site',time:'🌅 เช้า',place:'หน้างานร้าน',pri:'high',repeat:'once',note:''}},
  {{id:'q02',title:'วัดขนาดพื้นที่และร่างแปลนจัดวาง',cat:'site',time:'🌅 เช้า',place:'หน้างานร้าน',pri:'high',repeat:'once',note:'Counter + โต๊ะ + ทางเดิน'}},
  {{id:'q03',title:'บันทึก 3 สิ่งที่ทำได้วันนี้',cat:'think',time:'🌙 ดึก',place:'บ้าน / ไหนก็ได้',pri:'med',repeat:'daily',note:'Progress Journal'}},
  {{id:'q04',title:'ทบทวนและอัปเดต Loop ที่กำลังทำ',cat:'think',time:'🌆 เย็น',place:'บ้าน / ไหนก็ได้',pri:'low',repeat:'daily',note:''}},
  {{id:'q05',title:'โพสต์ content ร้านกาแฟ 1 ชิ้น',cat:'content',time:'🌆 เย็น',place:'ออนไลน์',pri:'med',repeat:'daily',note:'TikTok / Facebook / IG'}},
  {{id:'q06',title:'ถ่ายรูป/วิดีโอ behind-the-scenes ร้าน',cat:'content',time:'🌅 เช้า',place:'หน้างานร้าน',pri:'low',repeat:'weekly',note:''}},
  {{id:'q07',title:'เช็ค Achievement ที่ต้องทำวันนี้',cat:'plan',time:'🌅 เช้า',place:'บ้าน / ไหนก็ได้',pri:'high',repeat:'daily',note:'ดูใน Tab ความสำเร็จ'}},
  {{id:'q08',title:'วางแผนงานสัปดาห์ถัดไป',cat:'plan',time:'🌙 ดึก',place:'บ้าน / ไหนก็ได้',pri:'med',repeat:'weekly',note:''}},
  {{id:'q09',title:'บันทึกรายจ่ายวันนี้',cat:'cost',time:'🌙 ดึก',place:'บ้าน / ไหนก็ได้',pri:'high',repeat:'daily',note:''}},
  {{id:'q10',title:'ตรวจสอบต้นทุนเมนูใหม่',cat:'cost',time:'🌆 เย็น',place:'บ้าน / ไหนก็ได้',pri:'med',repeat:'once',note:'ใช้หน้าต้นทุนเครื่องดื่ม'}},
  {{id:'q11',title:'Setup Loyverse POS — สร้าง account + เมนู',cat:'system',time:'🌙 ดึก',place:'ออนไลน์',pri:'high',repeat:'once',note:''}},
  {{id:'q12',title:'ทดสอบระบบ POS ก่อนเปิดร้าน',cat:'system',time:'🌅 เช้า',place:'หน้างานร้าน',pri:'high',repeat:'once',note:''}},
  {{id:'q13',title:'ตรวจสอบใบอนุญาตประกอบการที่ต้องมี',cat:'legal',time:'🌅 เช้า',place:'บ้าน / ไหนก็ได้',pri:'high',repeat:'once',note:''}},
  {{id:'q14',title:'ยื่นขอใบอนุญาตจำหน่ายอาหาร',cat:'legal',time:'🌅 เช้า',place:'อำเภอ/เทศบาล',pri:'high',repeat:'once',note:''}},
  {{id:'q15',title:'กำหนด Brand Identity — ชื่อ สี โลโก้',cat:'brand',time:'🌙 ดึก',place:'บ้าน / ไหนก็ได้',pri:'high',repeat:'once',note:''}},
  {{id:'q16',title:'ออกแบบ/สั่งทำป้ายร้านและบรรจุภัณฑ์',cat:'brand',time:'🌆 เย็น',place:'ออนไลน์',pri:'med',repeat:'once',note:''}},
  {{id:'q17',title:'ติดต่อซัพพลายเออร์วัตถุดิบหลัก',cat:'supply',time:'🌅 เช้า',place:'ออนไลน์/โทรศัพท์',pri:'high',repeat:'once',note:'เมล็ดกาแฟ นม ไซรัป'}},
  {{id:'q18',title:'เช็คสต็อกวัตถุดิบและสั่งเติม',cat:'supply',time:'🌆 เย็น',place:'หน้างานร้าน',pri:'med',repeat:'weekly',note:''}},
  {{id:'q19',title:'สร้างโปรโมชั่นเปิดร้านใหม่',cat:'marketing',time:'🌙 ดึก',place:'ออนไลน์',pri:'high',repeat:'once',note:''}},
  {{id:'q20',title:'แจกใบปลิว/โปรโมทในละแวกร้าน',cat:'marketing',time:'🌅 เช้า',place:'ในละแวกร้าน',pri:'med',repeat:'weekly',note:''}},
  {{id:'q21',title:'ทำความสะอาดอุปกรณ์และเครื่องทำกาแฟ',cat:'hygiene',time:'🌆 เย็น',place:'หน้างานร้าน',pri:'high',repeat:'daily',note:''}},
  {{id:'q22',title:'เช็ค SOP ความสะอาดและจัดเก็บอาหาร',cat:'hygiene',time:'🌅 เช้า',place:'หน้างานร้าน',pri:'med',repeat:'weekly',note:''}},
  {{id:'q23',title:'ทดสอบชง + ชิมสูตรใหม่',cat:'experience',time:'🌅 เช้า',place:'หน้างานร้าน',pri:'med',repeat:'once',note:''}},
  {{id:'q24',title:'รับ Feedback จากลูกค้า/คนรู้จัก',cat:'experience',time:'🌆 เย็น',place:'หน้างานร้าน',pri:'low',repeat:'weekly',note:''}}
];

var DEFAULT_ACHS_SEED = [
  {{id:'a01',title:'เจรจาและเซ็นสัญญาเช่าร้าน',cat:'milestone',day:7,icon:'📝',desc:'ตกลงเงื่อนไข ราคา ระยะเวลาเช่า',done:false,doneDate:'',doneNote:''}},
  {{id:'a02',title:'กำหนด Brand Identity ครบถ้วน',cat:'brand',day:10,icon:'🎨',desc:'ชื่อร้าน สี โลโก้ Font Tagline',done:false,doneDate:'',doneNote:''}},
  {{id:'a03',title:'วางแผนเมนูหลักและราคาทุกช่องทาง',cat:'planning',day:12,icon:'📋',desc:'เมนูทุกรายการ ราคา หน้าร้าน/Lineman/Shoppee',done:false,doneDate:'',doneNote:''}},
  {{id:'a04',title:'ยื่นขอใบอนุญาตจำหน่ายอาหาร',cat:'legal',day:14,icon:'📜',desc:'ยื่นเอกสารที่อำเภอ/เทศบาล',done:false,doneDate:'',doneNote:''}},
  {{id:'a05',title:'ซื้อ/เช่าเครื่องทำกาแฟและอุปกรณ์หลัก',cat:'setup',day:14,icon:'☕',desc:'เครื่อง espresso, grinder, เครื่องมือ',done:false,doneDate:'',doneNote:''}},
  {{id:'a06',title:'ติดต่อซัพพลายเออร์ครบทุกรายการ',cat:'setup',day:18,icon:'🛒',desc:'เมล็ดกาแฟ นม ไซรัป บรรจุภัณฑ์',done:false,doneDate:'',doneNote:''}},
  {{id:'a07',title:'ปรับปรุงตกแต่งร้านแล้วเสร็จ',cat:'setup',day:20,icon:'🏗️',desc:'สี ป้าย เฟอร์นิเจอร์ แสงไฟ',done:false,doneDate:'',doneNote:''}},
  {{id:'a08',title:'Setup Loyverse POS สมบูรณ์',cat:'system',day:20,icon:'📱',desc:'เมนูครบ ราคาถูกต้อง พนักงานเข้าได้',done:false,doneDate:'',doneNote:''}},
  {{id:'a09',title:'ออกแบบและสั่งทำบรรจุภัณฑ์ครบ',cat:'brand',day:22,icon:'🎁',desc:'แก้ว ถุง สติกเกอร์ ป้าย',done:false,doneDate:'',doneNote:''}},
  {{id:'a10',title:'ทดสอบสูตรเมนูทุกรายการ',cat:'setup',day:24,icon:'🧪',desc:'ชิม ปรับ อนุมัติสูตรสุดท้าย',done:false,doneDate:'',doneNote:''}},
  {{id:'a11',title:'ฝึกอบรมพนักงาน (ถ้ามี)',cat:'system',day:26,icon:'👥',desc:'SOP การชง บริการ POS ความสะอาด',done:false,doneDate:'',doneNote:''}},
  {{id:'a12',title:'ทดสอบ Soft Run — ชงให้คนรู้จัก',cat:'launch',day:27,icon:'🧑‍🍳',desc:'ทดสอบจริงก่อนเปิดสาธารณะ',done:false,doneDate:'',doneNote:''}},
  {{id:'a13',title:'สร้าง Social Media ครบทุก Platform',cat:'marketing',day:28,icon:'📣',desc:'Facebook Page, Instagram, TikTok',done:false,doneDate:'',doneNote:''}},
  {{id:'a14',title:'ได้รับใบอนุญาตประกอบการ',cat:'legal',day:28,icon:'✅',desc:'ใบอนุญาตถูกต้อง พร้อมเปิดร้าน',done:false,doneDate:'',doneNote:''}},
  {{id:'a15',title:'🚀 SOFT LAUNCH — เปิดร้านครั้งแรก!',cat:'launch',day:30,icon:'🚀',desc:'วันเปิดร้านอย่างเป็นทางการ PENGTANG CAFE',done:false,doneDate:'',doneNote:''}},
  {{id:'a16',title:'มีรายได้วันแรก > 0 บาท',cat:'financial',day:30,icon:'💰',desc:'มีรายได้จริงในวันเปิดร้าน',done:false,doneDate:'',doneNote:''}},
  {{id:'a17',title:'ติด Google Maps และ Facebook Check-in',cat:'marketing',day:35,icon:'📍',desc:'ลูกค้า check-in ได้ถูกต้อง',done:false,doneDate:'',doneNote:''}},
  {{id:'a18',title:'ระบบสต็อกและ PAR level ครบ',cat:'system',day:40,icon:'🔧',desc:'ระดับสต็อกต่ำสุด สั่งซื้อระบบ',done:false,doneDate:'',doneNote:''}},
  {{id:'a19',title:'มีลูกค้าประจำ 10 คนแรก',cat:'milestone',day:45,icon:'👑',desc:'ลูกค้าที่กลับมาซื้อมากกว่า 1 ครั้ง',done:false,doneDate:'',doneNote:''}},
  {{id:'a20',title:'ยอดขาย TikTok/Reel แตะ 1,000 views',cat:'marketing',day:45,icon:'🎬',desc:'คอนเทนต์ร้านไวรัลครั้งแรก',done:false,doneDate:'',doneNote:''}},
  {{id:'a21',title:'มีรีวิวบน Google Maps 5 รีวิวขึ้นไป',cat:'marketing',day:50,icon:'⭐',desc:'คะแนนและรีวิวจากลูกค้าจริง',done:false,doneDate:'',doneNote:''}},
  {{id:'a22',title:'Review และปรับแผน 90 วัน',cat:'planning',day:60,icon:'🔄',desc:'ทบทวนสิ่งที่เรียนรู้ ปรับ SOP',done:false,doneDate:'',doneNote:''}},
  {{id:'a23',title:'ยอดขาย 30 วันหลังเปิด — รายได้ > ต้นทุนผันแปร',cat:'financial',day:60,icon:'📈',desc:'สัญญาณว่าร้านอยู่ได้',done:false,doneDate:'',doneNote:''}},
  {{id:'a24',title:'กำไรสุทธิเดือนแรกเป็นบวก',cat:'financial',day:75,icon:'💸',desc:'หลังหักต้นทุนคงที่และผันแปรทั้งหมด',done:false,doneDate:'',doneNote:''}},
  {{id:'a25',title:'👑 ครบ 90 วัน — PENGTANG CAFE พร้อมสู้!',cat:'launch',day:90,icon:'👑',desc:'ผ่าน 90 วันแรก ร้านมั่นคง ระบบพร้อม',done:false,doneDate:'',doneNote:''}}
];

// ── Quest helpers ──
var qstActiveTab = 'quest';
var qstCatFilter = 'all';
var qstAchCatFilter = 'all';
var qstPlanType = 'daily';
var qstHistFilter = 'all';
var _qstPushTimer = null;

function qstToday() {{ return new Date().toISOString().slice(0,10); }}
function qstGenId() {{ return 'q'+Date.now().toString(36)+Math.random().toString(36).slice(2,5); }}
function qstFmtDate(d) {{
  if (!d) return '';
  var dt = new Date(d); if (isNaN(dt)) return d;
  return dt.toLocaleDateString('th-TH', {{day:'numeric',month:'short',year:'numeric'}});
}}
function qstDayNum() {{
  if (!DCS || !DCS.questMeta) return 1;
  var s = new Date(DCS.questMeta.startDate), n = new Date();
  return Math.max(1, Math.min(Math.floor((n-s)/864e5)+1, 999));
}}
function qstStreak() {{
  if (!DCS || !DCS.questLog) return 0;
  var streak = 0, d = new Date();
  d.setHours(0,0,0,0);
  for (;;) {{
    var key = d.toISOString().slice(0,10);
    var day = DCS.questLog[key];
    if (!day || Object.keys(day).length === 0) break;
    streak++;
    d.setDate(d.getDate()-1);
  }}
  return streak;
}}
function qstIsDoneToday(qid) {{
  if (!DCS || !DCS.questLog) return false;
  var day = DCS.questLog[qstToday()];
  return !!(day && day[qid]);
}}
function qstDebouncePush() {{
  if (_qstPushTimer) clearTimeout(_qstPushTimer);
  _qstPushTimer = setTimeout(function() {{ if (dcGsUrl()) dcSyncPush(); }}, 2000);
}}
function qstAfterChange() {{ dcSave(); dcMarkPending(); qstDebouncePush(); }}

function qstShowTab(tab) {{
  qstActiveTab = tab;
  var root = document.getElementById('qst-root');
  if (root) renderQuestView();
}}

function qstSetCatFilter(cat) {{
  qstCatFilter = cat;
  var root = document.getElementById('qst-root');
  if (root) renderQuestView();
}}
function qstSetAchCatFilter(cat) {{
  qstAchCatFilter = cat;
  var root = document.getElementById('qst-root');
  if (root) renderQuestView();
}}
function qstSetPlanType(type) {{
  qstPlanType = type;
  var root = document.getElementById('qst-root');
  if (root) renderQuestView();
}}
function qstSetHistFilter(f) {{
  qstHistFilter = f;
  var root = document.getElementById('qst-root');
  if (root) renderQuestView();
}}

// ── renderQuestView ──
function renderQuestView() {{
  if (!DCS) dcLoadState();
  var root = document.getElementById('qst-root');
  if (!root) return;
  var meta = DCS.questMeta || {{}};
  var day = qstDayNum();
  var total = meta.totalDays || 90;
  var pct = Math.min(Math.round(day/total*100),100);
  var streak = qstStreak();
  var moti = MOTIVATIONS[day % MOTIVATIONS.length];
  var buff = BUFFS[day % BUFFS.length];

  // Gamification header
  var headerHtml = '<div style="background:var(--card);border:1px solid var(--card-border);border-radius:16px;padding:18px 20px;margin-bottom:16px">'
    + '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">'
    + '<div style="display:flex;align-items:center;gap:12px">'
    + '<div style="background:var(--ov-accent-ink);color:#fff;border-radius:12px;padding:6px 14px;font-weight:800;font-size:15px">Day ' + day + '</div>'
    + (streak>0?'<div style="color:var(--ov-accent-ink);font-weight:700;font-size:15px">🔥 ' + streak + ' วัน</div>':'')
    + '</div>'
    + '<button onclick="qstEditMeta()" style="background:none;border:1px solid var(--card-border);border-radius:8px;padding:4px 10px;font-size:12px;cursor:pointer;color:var(--text-muted)">✏️ แก้ค่า</button>'
    + '</div>'
    + '<div style="background:var(--card-border,#e2e8f0);border-radius:8px;height:10px;margin-bottom:8px;overflow:hidden">'
    + '<div style="height:100%;width:'+pct+'%;background:var(--ov-accent-ink);border-radius:8px;transition:width .5s"></div>'
    + '</div>'
    + '<div style="display:flex;justify-content:space-between;font-size:12px;color:var(--text-muted);margin-bottom:12px">'
    + '<span>Day ' + day + ' / ' + total + '</span><span>' + pct + '%</span>'
    + '</div>'
    + '<div style="background:rgba(139,69,19,0.07);border-radius:10px;padding:10px 14px;font-size:13px;color:var(--text);margin-bottom:8px;line-height:1.5">'
    + '💬 ' + escapeHtml(moti) + '</div>'
    + '<div style="background:rgba(139,69,19,0.05);border-radius:10px;padding:8px 14px;font-size:12px;color:var(--text-muted)">'
    + '⚡ ' + escapeHtml(buff) + '</div>'
    + '</div>';

  // Sub-tabs (5 tabs, flex-wrap for small screens)
  var tabsHtml = '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px">'
    + '<button onclick="qstShowTab(\\'quest\\')" style="padding:7px 13px;border-radius:10px;border:none;cursor:pointer;font-size:13px;font-weight:600;'
    + (qstActiveTab==='quest' ? 'background:var(--ov-accent-ink);color:#fff;' : 'background:var(--card);border:1px solid var(--card-border);color:var(--text);')
    + '">⚔️ เควส</button>'
    + '<button onclick="qstShowTab(\\'ach\\')" style="padding:7px 13px;border-radius:10px;border:none;cursor:pointer;font-size:13px;font-weight:600;'
    + (qstActiveTab==='ach' ? 'background:var(--ov-accent-ink);color:#fff;' : 'background:var(--card);border:1px solid var(--card-border);color:var(--text);')
    + '">🏆 ความสำเร็จ</button>'
    + '<button onclick="qstShowTab(\\'plans\\')" style="padding:7px 13px;border-radius:10px;border:none;cursor:pointer;font-size:13px;font-weight:600;'
    + (qstActiveTab==='plans' ? 'background:var(--ov-accent-ink);color:#fff;' : 'background:var(--card);border:1px solid var(--card-border);color:var(--text);')
    + '">📋 แผน</button>'
    + '<button onclick="qstShowTab(\\'loops\\')" style="padding:7px 13px;border-radius:10px;border:none;cursor:pointer;font-size:13px;font-weight:600;'
    + (qstActiveTab==='loops' ? 'background:var(--ov-accent-ink);color:#fff;' : 'background:var(--card);border:1px solid var(--card-border);color:var(--text);')
    + '">🔄 Loop</button>'
    + '<button onclick="qstShowTab(\\'history\\')" style="padding:7px 13px;border-radius:10px;border:none;cursor:pointer;font-size:13px;font-weight:600;'
    + (qstActiveTab==='history' ? 'background:var(--ov-accent-ink);color:#fff;' : 'background:var(--card);border:1px solid var(--card-border);color:var(--text);')
    + '">📜 ประวัติ</button>'
    + '</div>';

  var panelHtml = '';
  if (qstActiveTab === 'quest') {{
    panelHtml = qstRenderQuestPanel();
  }} else if (qstActiveTab === 'ach') {{
    panelHtml = qstRenderAchPanel();
  }} else if (qstActiveTab === 'plans') {{
    panelHtml = qstRenderPlansPanel();
  }} else if (qstActiveTab === 'loops') {{
    panelHtml = qstRenderLoopsPanel();
  }} else {{
    panelHtml = qstRenderHistoryPanel();
  }}

  root.innerHTML = headerHtml + tabsHtml + panelHtml;
}}

// ── Quest panel ──
function qstRenderQuestPanel() {{
  var quests = DCS.quests || [];

  // Category filter chips
  var chips = '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px">'
    + '<button onclick="qstSetCatFilter(\\'all\\')" style="padding:4px 12px;border-radius:20px;border:1px solid var(--card-border);cursor:pointer;font-size:12px;'
    + (qstCatFilter==='all' ? 'background:var(--ov-accent-ink);color:#fff;border-color:var(--ov-accent-ink);' : 'background:var(--card);color:var(--text-muted);')
    + '">ทั้งหมด ('+quests.length+')</button>';
  Object.keys(QUEST_CAT).forEach(function(k) {{
    var c = QUEST_CAT[k];
    var cnt = quests.filter(function(q){{return q.cat===k;}}).length;
    if (!cnt) return;
    var active = qstCatFilter === k;
    chips += '<button onclick="qstSetCatFilter(\\''+k+'\\')" style="padding:4px 12px;border-radius:20px;border:1px solid var(--card-border);cursor:pointer;font-size:12px;'
      + (active ? 'background:var(--ov-accent-ink);color:#fff;border-color:var(--ov-accent-ink);' : 'background:var(--card);color:var(--text);')
      + '">' + c.icon + ' ' + c.label + ' (' + cnt + ')</button>';
  }});
  chips += '</div>';

  // Add button
  var addBtn = '<div style="margin-bottom:12px">'
    + '<button onclick="qstOpenForm(null)" style="background:var(--ov-accent-ink);color:#fff;border:none;border-radius:10px;padding:8px 16px;font-size:13px;cursor:pointer;font-weight:600">+ เพิ่มเควส</button>'
    + '</div>';

  // Quest list
  var filtered = qstCatFilter==='all' ? quests : quests.filter(function(q){{return q.cat===qstCatFilter;}});
  var today = qstToday();
  var cards = '';
  if (!filtered.length) {{
    cards = '<div style="text-align:center;padding:40px 20px;color:var(--text-muted);font-size:14px">ยังไม่มีเควสในหมวดนี้</div>';
  }} else {{
    filtered.forEach(function(q) {{
      var cat = QUEST_CAT[q.cat] || {{icon:'📌',label:q.cat}};
      var doneToday = qstIsDoneToday(q.id);
      var priColor = q.pri==='high' ? 'var(--dc-warn,#e53935)' : q.pri==='med' ? 'var(--ov-accent-ink,#8B4513)' : 'var(--text-muted)';
      var priLabel = q.pri==='high' ? '🔴 สำคัญมาก' : q.pri==='med' ? '🟡 ปานกลาง' : '🟢 ต่ำ';
      cards += '<div style="background:var(--card);border:1px solid var(--card-border);border-radius:14px;padding:14px 16px;margin-bottom:10px;display:flex;align-items:flex-start;gap:12px">'
        + '<button onclick="qstToggleToday(\\''+q.id+'\\')" title="'+(doneToday?'ยกเลิก':'ทำแล้ววันนี้')+'" style="flex-shrink:0;width:28px;height:28px;border-radius:50%;border:2px solid '+(doneToday?'var(--ov-accent-ink)':'var(--card-border)')+';background:'+(doneToday?'var(--ov-accent-ink)':'transparent')+';cursor:pointer;font-size:14px;display:flex;align-items:center;justify-content:center;color:'+(doneToday?'#fff':'var(--text-muted)')+'">'+( doneToday?'✓':'')+'</button>'
        + '<div style="flex:1;min-width:0">'
        + '<div style="font-weight:600;font-size:14px;color:var(--text);margin-bottom:4px">' + cat.icon + ' ' + escapeHtml(q.title) + '</div>'
        + '<div style="font-size:12px;color:var(--text-muted);display:flex;flex-wrap:wrap;gap:6px">'
        + '<span>' + escapeHtml(q.time) + '</span>'
        + (q.place ? '<span>📍 ' + escapeHtml(q.place) + '</span>' : '')
        + '<span style="color:'+priColor+'">'+priLabel+'</span>'
        + (q.repeat==='daily'?'<span style="background:rgba(139,69,19,0.1);border-radius:8px;padding:1px 8px">🔄 รายวัน</span>':q.repeat==='weekly'?'<span style="background:rgba(139,69,19,0.07);border-radius:8px;padding:1px 8px">📅 รายสัปดาห์</span>':'')
        + '</div>'
        + (q.note ? '<div style="font-size:12px;color:var(--text-muted);margin-top:4px">💬 '+escapeHtml(q.note)+'</div>' : '')
        + '</div>'
        + '<div style="display:flex;gap:6px;flex-shrink:0">'
        + '<button onclick="qstOpenForm(\\''+q.id+'\\')" style="background:none;border:none;cursor:pointer;padding:4px;color:var(--text-muted);font-size:15px" title="แก้ไข">✏️</button>'
        + '<button onclick="qstDelete(\\''+q.id+'\\')" style="background:none;border:none;cursor:pointer;padding:4px;color:var(--text-muted);font-size:15px" title="ลบ">🗑️</button>'
        + '</div>'
        + '</div>';
    }});
  }}

  return chips + addBtn + cards;
}}

// ── Achievement panel ──
function qstRenderAchPanel() {{
  var achs = DCS.achievements || [];
  var day = qstDayNum();
  var done = achs.filter(function(a){{return a.done;}}).length;
  var total = achs.length;

  // summary
  var summary = '<div style="display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap">';
  var statItems = [
    {{label:'ทั้งหมด',val:total,col:'var(--text)'}},
    {{label:'สำเร็จแล้ว',val:done,col:'var(--dc-profit,#2e7d32)'}},
    {{label:'เหลืออยู่',val:total-done,col:'var(--ov-accent-ink,#8B4513)'}},
    {{label:'เลยกำหนด',val:achs.filter(function(a){{return !a.done && a.day < day;}}).length,col:'var(--dc-warn,#e53935)'}}
  ];
  statItems.forEach(function(s) {{
    summary += '<div style="background:var(--card);border:1px solid var(--card-border);border-radius:12px;padding:10px 16px;min-width:80px;text-align:center">'
      + '<div style="font-size:20px;font-weight:800;color:'+s.col+'">'+s.val+'</div>'
      + '<div style="font-size:11px;color:var(--text-muted)">'+s.label+'</div>'
      + '</div>';
  }});
  summary += '</div>';

  // progress bar
  var pct = total ? Math.round(done/total*100) : 0;
  summary += '<div style="margin-bottom:14px">'
    + '<div style="font-size:12px;color:var(--text-muted);margin-bottom:4px">ความสำเร็จ '+done+'/'+total+' ('+pct+'%)</div>'
    + '<div style="background:var(--card-border,#e2e8f0);border-radius:8px;height:8px;overflow:hidden">'
    + '<div style="height:100%;width:'+pct+'%;background:var(--ov-accent-ink);border-radius:8px;transition:width .5s"></div>'
    + '</div>'
    + '</div>';

  // Add button
  var addBtn = '<div style="margin-bottom:12px">'
    + '<button onclick="qstOpenAchForm(null)" style="background:var(--ov-accent-ink);color:#fff;border:none;border-radius:10px;padding:8px 16px;font-size:13px;cursor:pointer;font-weight:600">+ เพิ่มความสำเร็จ</button>'
    + '</div>';

  // Category filter chips
  var achChips = '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px">'
    + '<button onclick="qstSetAchCatFilter(\\'all\\')" style="padding:4px 12px;border-radius:20px;border:1px solid var(--card-border);cursor:pointer;font-size:12px;'
    + (qstAchCatFilter==='all' ? 'background:var(--ov-accent-ink);color:#fff;border-color:var(--ov-accent-ink);' : 'background:var(--card);color:var(--text-muted);')
    + '">ทั้งหมด ('+achs.length+')</button>';
  Object.keys(ACH_CAT).forEach(function(k) {{
    var c = ACH_CAT[k];
    var cnt = achs.filter(function(a){{return a.cat===k;}}).length;
    if (!cnt) return;
    var active = qstAchCatFilter === k;
    achChips += '<button onclick="qstSetAchCatFilter(\\''+k+'\\')" style="padding:4px 12px;border-radius:20px;border:1px solid var(--card-border);cursor:pointer;font-size:12px;'
      + (active ? 'background:var(--ov-accent-ink);color:#fff;border-color:var(--ov-accent-ink);' : 'background:var(--card);color:var(--text);')
      + '">' + c.icon + ' ' + c.label + ' (' + cnt + ')</button>';
  }});
  achChips += '</div>';

  // Achievement list (filtered) sorted by day
  var filteredAchs = qstAchCatFilter==='all' ? achs : achs.filter(function(a){{return a.cat===qstAchCatFilter;}});
  var sorted = filteredAchs.slice().sort(function(a,b){{return (a.day||0)-(b.day||0);}});
  var cards = '';
  sorted.forEach(function(a) {{
    var overdue = !a.done && a.day < day;
    var ontime = a.done && a.day >= day;
    var early = a.done && a.day > day;
    var late = a.done && a.day < day;
    var statusColor = a.done ? 'var(--dc-profit,#2e7d32)' : overdue ? 'var(--dc-warn,#e53935)' : 'var(--text-muted)';
    var statusLabel = a.done ? (early?'✅ สำเร็จก่อนกำหนด':late?'✅ สำเร็จ (หลังกำหนด)':'✅ สำเร็จ') : overdue ? '⚠️ เลยกำหนดแล้ว' : '⏳ Day '+a.day;
    cards += '<div style="background:var(--card);border:1px solid '+(a.done?'rgba(46,125,50,0.3)':overdue?'rgba(229,57,53,0.3)':'var(--card-border)')+';border-radius:14px;padding:14px 16px;margin-bottom:10px;display:flex;gap:12px;align-items:flex-start">'
      + '<button onclick="qstTickAch(\\''+a.id+'\\')" title="'+(a.done?'ยกเลิก':'ทำสำเร็จแล้ว')+'" style="flex-shrink:0;width:32px;height:32px;border-radius:50%;border:2px solid '+(a.done?'var(--dc-profit,#2e7d32)':'var(--card-border)')+';background:'+(a.done?'var(--dc-profit,#2e7d32)':'transparent')+';cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center;color:'+(a.done?'#fff':'var(--text-muted)')+'">'+a.icon+'</button>'
      + '<div style="flex:1;min-width:0">'
      + '<div style="font-weight:700;font-size:14px;color:var(--text)">'+escapeHtml(a.title)+'</div>'
      + '<div style="font-size:12px;margin-top:3px;display:flex;flex-wrap:wrap;gap:8px">'
      + '<span style="color:'+statusColor+'">'+statusLabel+'</span>'
      + (a.doneDate ? '<span style="color:var(--text-muted)">'+qstFmtDate(a.doneDate)+'</span>' : '')
      + (a.desc ? '<span style="color:var(--text-muted)">'+escapeHtml(a.desc)+'</span>' : '')
      + '</div>'
      + (a.doneNote ? '<div style="font-size:12px;color:var(--text-muted);margin-top:4px;font-style:italic">💬 '+escapeHtml(a.doneNote)+'</div>' : '')
      + '</div>'
      + '<div style="display:flex;gap:6px;flex-shrink:0">'
      + '<button onclick="qstOpenAchForm(\\''+a.id+'\\')" style="background:none;border:none;cursor:pointer;padding:4px;color:var(--text-muted);font-size:15px" title="แก้ไข">✏️</button>'
      + '<button onclick="qstDeleteAch(\\''+a.id+'\\')" style="background:none;border:none;cursor:pointer;padding:4px;color:var(--text-muted);font-size:15px" title="ลบ">🗑️</button>'
      + '</div>'
      + '</div>';
  }});
  if (!sorted.length) cards = '<div style="text-align:center;padding:40px;color:var(--text-muted)">'+(qstAchCatFilter==='all'?'ยังไม่มีความสำเร็จ':'ยังไม่มีความสำเร็จในหมวดนี้')+'</div>';

  return summary + achChips + addBtn + cards;
}}

// ── Plans panel ──
function qstRenderPlansPanel() {{
  var plans = DCS.plans || {{daily:[],weekly:[],monthly:[]}};
  var typeItems = [{{t:'daily',l:'รายวัน'}},{{t:'weekly',l:'รายสัปดาห์'}},{{t:'monthly',l:'รายเดือน'}}];

  // Sub-filter
  var subFilter = '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px">';
  typeItems.forEach(function(ti) {{
    var active = qstPlanType === ti.t;
    subFilter += '<button onclick="qstSetPlanType(\\''+ti.t+'\\')" style="padding:6px 14px;border-radius:10px;border:1px solid var(--card-border);cursor:pointer;font-size:13px;font-weight:600;'
      + (active ? 'background:var(--ov-accent-ink);color:#fff;border-color:var(--ov-accent-ink);' : 'background:var(--card);color:var(--text);')
      + '">'+ti.l+'</button>';
  }});
  subFilter += '</div>';

  // Add button
  var addBtn = '<div style="margin-bottom:12px">'
    + '<button onclick="qstOpenPlanForm(null)" style="background:var(--ov-accent-ink);color:#fff;border:none;border-radius:10px;padding:8px 16px;font-size:13px;cursor:pointer;font-weight:600">+ เพิ่มรายการ</button>'
    + '</div>';

  // List
  var items = plans[qstPlanType] || [];
  var cards = '';
  if (!items.length) {{
    cards = '<div style="text-align:center;padding:40px 20px;color:var(--text-muted);font-size:14px">ยังไม่มีรายการ — กด + เพิ่มรายการ</div>';
  }} else {{
    items.forEach(function(p) {{
      var priColor = p.pri==='high' ? 'var(--dc-warn,#e53935)' : p.pri==='med' ? 'var(--ov-accent-ink)' : 'var(--text-muted)';
      var priLabel = p.pri==='high' ? '🔴 สำคัญมาก' : p.pri==='med' ? '🟡 ปานกลาง' : '🟢 ต่ำ';
      cards += '<div style="background:var(--card);border:1px solid '+(p.done?'rgba(46,125,50,0.3)':'var(--card-border)')+';border-radius:14px;padding:12px 16px;margin-bottom:8px;display:flex;align-items:center;gap:12px">'
        + '<button onclick="qstTickPlan(\\''+p.id+'\\')" title="'+(p.done?'ยกเลิก':'ทำเสร็จแล้ว')+'" style="flex-shrink:0;width:26px;height:26px;border-radius:50%;border:2px solid '+(p.done?'var(--dc-profit,#2e7d32)':'var(--card-border)')+';background:'+(p.done?'var(--dc-profit,#2e7d32)':'transparent')+';cursor:pointer;font-size:13px;display:flex;align-items:center;justify-content:center;color:'+(p.done?'#fff':'var(--text-muted)')+'">'+( p.done?'✓':'')+'</button>'
        + '<div style="flex:1;min-width:0">'
        + '<div style="font-size:14px;color:var(--text);'+(p.done?'text-decoration:line-through;opacity:0.6;':'')+'font-weight:500">'+escapeHtml(p.text)+'</div>'
        + '<div style="font-size:12px;margin-top:2px;color:'+priColor+'">'+priLabel+'</div>'
        + '</div>'
        + '<div style="display:flex;gap:4px;flex-shrink:0">'
        + '<button onclick="qstOpenPlanForm(\\''+p.id+'\\')" style="background:none;border:none;cursor:pointer;padding:4px;color:var(--text-muted);font-size:15px" title="แก้ไข">✏️</button>'
        + '<button onclick="qstDeletePlan(\\''+p.id+'\\')" style="background:none;border:none;cursor:pointer;padding:4px;color:var(--text-muted);font-size:15px" title="ลบ">🗑️</button>'
        + '</div>'
        + '</div>';
    }});
  }}
  return subFilter + addBtn + cards;
}}

// ── Loops panel ──
function qstRenderLoopsPanel() {{
  var loops = DCS.loops || [];
  var stgKeys = ['learn','do','improve','repeat'];

  // Legend (hardcoded to avoid map in template)
  var legend = '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px;background:var(--card);border:1px solid var(--card-border);border-radius:12px;padding:10px 14px">'
    + '<span style="font-size:12px;color:var(--text-muted)">📚 <b style="color:var(--text)">หาความรู้</b></span>'
    + '<span style="color:var(--card-border);margin:0 2px"> · </span>'
    + '<span style="font-size:12px;color:var(--text-muted)">🔨 <b style="color:var(--text)">ลงมือทำ</b></span>'
    + '<span style="color:var(--card-border);margin:0 2px"> · </span>'
    + '<span style="font-size:12px;color:var(--text-muted)">🔍 <b style="color:var(--text)">ปรับปรุง</b></span>'
    + '<span style="color:var(--card-border);margin:0 2px"> · </span>'
    + '<span style="font-size:12px;color:var(--text-muted)">♻️ <b style="color:var(--text)">ทำซ้ำ</b></span>'
    + '</div>';

  // Add button
  var addBtn = '<div style="margin-bottom:12px">'
    + '<button onclick="qstOpenLoopForm(null)" style="background:var(--ov-accent-ink);color:#fff;border:none;border-radius:10px;padding:8px 16px;font-size:13px;cursor:pointer;font-weight:600">+ เพิ่ม Loop</button>'
    + '</div>';

  // Cards
  var cards = '';
  if (!loops.length) {{
    cards = '<div style="text-align:center;padding:40px 20px;color:var(--text-muted);font-size:14px">ยังไม่มี Loop — เพิ่มหัวข้อที่ต้องฝึกซ้ำ</div>';
  }} else {{
    loops.forEach(function(lp) {{
      var pills = '';
      stgKeys.forEach(function(k) {{
        var s = LOOP_STG[k];
        var active = lp.stage === k;
        pills += '<button onclick="qstSetLoopStage(\\''+lp.id+'\\',\\''+k+'\\')" style="padding:4px 10px;border-radius:20px;border:none;cursor:pointer;font-size:12px;'
          + (active ? 'background:var(--ov-accent-ink);color:#fff;font-weight:700;' : 'background:var(--card-border,#e2e8f0);color:var(--text);')
          + '">'+s.icon+' '+s.label+'</button>';
      }});
      cards += '<div style="background:var(--card);border:1px solid var(--card-border);border-radius:14px;padding:14px 16px;margin-bottom:10px">'
        + '<div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:10px">'
        + '<div style="flex:1;min-width:0">'
        + '<div style="font-weight:700;font-size:14px;color:var(--text);margin-bottom:8px">'+escapeHtml(lp.title)+'</div>'
        + '<div style="display:flex;flex-wrap:wrap;gap:6px">'+pills+'</div>'
        + '</div>'
        + '<div style="display:flex;gap:4px;flex-shrink:0">'
        + '<button onclick="qstOpenLoopForm(\\''+lp.id+'\\')" style="background:none;border:none;cursor:pointer;padding:4px;color:var(--text-muted);font-size:15px" title="แก้ไข">✏️</button>'
        + '<button onclick="qstDeleteLoop(\\''+lp.id+'\\')" style="background:none;border:none;cursor:pointer;padding:4px;color:var(--text-muted);font-size:15px" title="ลบ">🗑️</button>'
        + '</div>'
        + '</div>'
        + (lp.note ? '<div style="font-size:12px;color:var(--text-muted);margin-bottom:6px">💬 '+escapeHtml(lp.note)+'</div>' : '')
        + '<div style="font-size:11px;color:var(--text-muted)">อัปเดตเมื่อ '+qstFmtDate(lp.updatedAt||'')+'</div>'
        + '</div>';
    }});
  }}
  return legend + addBtn + cards;
}}

// ── History panel ──
function qstRenderHistoryPanel() {{
  var history = (DCS.questHistory || []).slice().sort(function(a,b){{return (b.date||'').localeCompare(a.date||'');}});
  var typeColor = {{quest:'var(--ov-accent-ink)',achievement:'var(--dc-profit,#2e7d32)',plan:'#3b82f6',loop:'#a78bfa'}};
  var typeLabel = {{quest:'⚔️ เควส',achievement:'🏆 ความสำเร็จ',plan:'📋 แผน',loop:'🔄 Loop'}};

  // Filter chips
  var filterItems = [{{f:'all',l:'ทั้งหมด'}},{{f:'quest',l:'⚔️ เควส'}},{{f:'achievement',l:'🏆 ความสำเร็จ'}},{{f:'plan',l:'📋 แผน'}},{{f:'loop',l:'🔄 Loop'}}];
  var chips = '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px">';
  filterItems.forEach(function(fi) {{
    var active = qstHistFilter === fi.f;
    chips += '<button onclick="qstSetHistFilter(\\''+fi.f+'\\')" style="padding:4px 12px;border-radius:20px;border:1px solid var(--card-border);cursor:pointer;font-size:12px;'
      + (active ? 'background:var(--ov-accent-ink);color:#fff;border-color:var(--ov-accent-ink);' : 'background:var(--card);color:var(--text-muted);')
      + '">'+fi.l+'</button>';
  }});
  chips += '</div>';

  // Clear button
  var clearBtn = '<div style="margin-bottom:12px;text-align:right">'
    + '<button onclick="qstClearHistory()" style="background:none;border:1px solid var(--card-border);border-radius:8px;padding:5px 12px;font-size:12px;cursor:pointer;color:var(--text-muted)">🗑 ล้างประวัติ</button>'
    + '</div>';

  // List
  var filtered = qstHistFilter === 'all' ? history : history.filter(function(h){{return h.type===qstHistFilter;}});
  var items = '';
  if (!filtered.length) {{
    items = '<div style="text-align:center;padding:40px 20px;color:var(--text-muted);font-size:14px">ยังไม่มีประวัติ</div>';
  }} else {{
    filtered.forEach(function(h) {{
      var col = typeColor[h.type] || 'var(--text-muted)';
      var lbl = typeLabel[h.type] || h.type;
      items += '<div style="display:flex;align-items:flex-start;gap:10px;padding:10px 0;border-bottom:1px solid var(--card-border)">'
        + '<div style="flex-shrink:0;width:10px;height:10px;border-radius:50%;background:'+col+';margin-top:5px"></div>'
        + '<div style="flex:1;min-width:0">'
        + '<div style="font-size:14px;color:var(--text);font-weight:500">'+escapeHtml(h.title||'')+'</div>'
        + '<div style="font-size:12px;color:var(--text-muted);display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin-top:2px">'
        + '<span style="background:var(--card-border,#e2e8f0);border-radius:6px;padding:1px 7px;font-size:11px">'+lbl+'</span>'
        + '<span>'+qstFmtDate(h.date||'')+'</span>'
        + (h.note ? '<span>💬 '+escapeHtml(h.note)+'</span>' : '')
        + '</div>'
        + '</div>'
        + '</div>';
    }});
  }}
  return chips + clearBtn + items;
}}

// ── Quest CRUD ──
function qstToggleToday(qid) {{
  if (!saIsUnlocked()) {{
    dcOpenPwModal('🔒 ยืนยันตัวตน','กรอกรหัสเพื่อบันทึกเควส',function(){{saUnlock();qstToggleToday(qid);}});
    return;
  }}
  if (!DCS.questLog) DCS.questLog = {{}};
  var today = qstToday();
  if (!DCS.questLog[today]) DCS.questLog[today] = {{}};
  if (DCS.questLog[today][qid]) {{
    delete DCS.questLog[today][qid];
    if (!Object.keys(DCS.questLog[today]).length) delete DCS.questLog[today];
  }} else {{
    DCS.questLog[today][qid] = true;
  }}
  qstAfterChange(); renderQuestView();
}}

function qstOpenForm(id) {{
  if (!saIsUnlocked()) {{
    dcOpenPwModal('🔒 ยืนยันตัวตน','กรอกรหัสเพื่อแก้ไขเควส',function(){{saUnlock();qstOpenForm(id);}});
    return;
  }}
  var q = id ? (DCS.quests||[]).find(function(x){{return x.id===id;}}) : null;
  var catOpts = Object.keys(QUEST_CAT).map(function(k){{
    return '<option value="'+k+'"'+(q&&q.cat===k?' selected':'')+'>'+QUEST_CAT[k].icon+' '+QUEST_CAT[k].label+'</option>';
  }}).join('');
  var html = '<div class="dc-modal-head"><h3>'+(q?'แก้ไขเควส':'เพิ่มเควสใหม่')+'</h3><button class="dc-x" onclick="dcCloseModal()" aria-label="ปิด">✕</button></div>'
    + '<div class="dc-modal-scroll">'
    + '<div class="dc-field"><label>ชื่อภารกิจ</label><input class="dc-inp" id="qf-title" value="'+escapeHtml(q?q.title:'')+'"></div>'
    + '<div class="dc-field"><label>หมวด</label><select class="dc-inp" id="qf-cat">'+catOpts+'</select></div>'
    + '<div class="dc-field"><label>ช่วงเวลา</label><select class="dc-inp" id="qf-time">'
    + ['🌅 เช้า','🌞 กลางวัน','🌆 เย็น','🌙 ดึก'].map(function(t){{return '<option'+(q&&q.time===t?' selected':'')+'>'+t+'</option>';}}).join('')
    + '</select></div>'
    + '<div class="dc-field"><label>สถานที่</label><input class="dc-inp" id="qf-place" value="'+escapeHtml(q?q.place:'')+'"></div>'
    + '<div class="dc-field"><label>ความสำคัญ</label><select class="dc-inp" id="qf-pri">'
    + [{{v:'high',l:'🔴 สำคัญมาก'}},{{v:'med',l:'🟡 ปานกลาง'}},{{v:'low',l:'🟢 ต่ำ'}}].map(function(o){{return '<option value="'+o.v+'"'+(q&&q.pri===o.v?' selected':'')+'>'+o.l+'</option>';}}).join('')
    + '</select></div>'
    + '<div class="dc-field"><label>ทำซ้ำ</label><select class="dc-inp" id="qf-repeat">'
    + [{{v:'once',l:'ครั้งเดียว'}},{{v:'daily',l:'🔄 รายวัน'}},{{v:'weekly',l:'📅 รายสัปดาห์'}}].map(function(o){{return '<option value="'+o.v+'"'+(q&&q.repeat===o.v?' selected':'')+'>'+o.l+'</option>';}}).join('')
    + '</select></div>'
    + '<div class="dc-field"><label>หมายเหตุ</label><input class="dc-inp" id="qf-note" value="'+escapeHtml(q?q.note:'')+'"></div>'
    + '</div>'
    + '<div class="dc-modal-foot">'
    + '<button class="dc-btn ghost" onclick="dcCloseModal()">ยกเลิก</button>'
    + '<button class="dc-btn primary" onclick="qstSaveForm(\\''+( q?q.id:'')+'\\')" >💾 บันทึก</button>'
    + '</div>';
  dcSetModalBody(html);
  setTimeout(function(){{ var el=document.getElementById('qf-title'); if(el) el.focus(); }}, 100);
}}

function qstSaveForm(id) {{
  var title = (document.getElementById('qf-title')||{{}}).value||'';
  if (!title.trim()) {{ showToast('กรอกชื่อภารกิจด้วย'); return; }}
  if (!DCS.quests) DCS.quests = [];
  if (id) {{
    var idx = DCS.quests.findIndex(function(x){{return x.id===id;}});
    if (idx>=0) {{
      DCS.quests[idx].title  = title.trim();
      DCS.quests[idx].cat    = document.getElementById('qf-cat').value;
      DCS.quests[idx].time   = document.getElementById('qf-time').value;
      DCS.quests[idx].place  = document.getElementById('qf-place').value.trim();
      DCS.quests[idx].pri    = document.getElementById('qf-pri').value;
      DCS.quests[idx].repeat = document.getElementById('qf-repeat').value;
      DCS.quests[idx].note   = document.getElementById('qf-note').value.trim();
    }}
  }} else {{
    DCS.quests.push({{
      id: qstGenId(), title: title.trim(),
      cat:    document.getElementById('qf-cat').value,
      time:   document.getElementById('qf-time').value,
      place:  document.getElementById('qf-place').value.trim(),
      pri:    document.getElementById('qf-pri').value,
      repeat: document.getElementById('qf-repeat').value,
      note:   document.getElementById('qf-note').value.trim()
    }});
  }}
  dcCloseModal(); qstAfterChange(); renderQuestView();
  showToast(id ? 'อัปเดตเควสแล้ว' : 'เพิ่มเควสใหม่แล้ว');
}}

function qstDelete(id) {{
  if (!saIsUnlocked()) {{
    dcOpenPwModal('🔒 ยืนยันตัวตน','กรอกรหัสเพื่อลบเควส',function(){{saUnlock();qstDelete(id);}});
    return;
  }}
  if (!confirm('ลบเควสนี้?')) return;
  DCS.quests = (DCS.quests||[]).filter(function(q){{return q.id!==id;}});
  qstAfterChange(); renderQuestView();
  showToast('ลบเควสแล้ว');
}}

// ── Achievement CRUD ──
function qstTickAch(id) {{
  if (!saIsUnlocked()) {{
    dcOpenPwModal('🔒 ยืนยันตัวตน','กรอกรหัสเพื่อบันทึกความสำเร็จ',function(){{saUnlock();qstTickAch(id);}});
    return;
  }}
  var a = (DCS.achievements||[]).find(function(x){{return x.id===id;}});
  if (!a) return;
  if (a.done) {{
    // undo
    a.done = false; a.doneDate = ''; a.doneNote = '';
    qstAfterChange(); renderQuestView();
    showToast('ยกเลิกความสำเร็จแล้ว');
    return;
  }}
  // mark done — ask for note
  var html = '<div class="dc-modal-head"><h3>🏆 บันทึกความสำเร็จ</h3><button class="dc-x" onclick="dcCloseModal()">✕</button></div>'
    + '<div class="dc-modal-scroll">'
    + '<div style="text-align:center;font-size:24px;margin:12px 0">' + a.icon + '</div>'
    + '<div style="font-weight:700;text-align:center;color:var(--text);margin-bottom:16px">' + escapeHtml(a.title) + '</div>'
    + '<div class="dc-field"><label>วันที่สำเร็จ</label><input class="dc-inp" type="date" id="atick-date" value="' + qstToday() + '"></div>'
    + '<div class="dc-field"><label>บันทึกเพิ่มเติม (ถ้ามี)</label><textarea class="dc-inp" id="atick-note" rows="3" placeholder="ความรู้สึก สิ่งที่เรียนรู้..."></textarea></div>'
    + '</div>'
    + '<div class="dc-modal-foot">'
    + '<button class="dc-btn ghost" onclick="dcCloseModal()">ยกเลิก</button>'
    + '<button class="dc-btn primary" onclick="qstSaveTickAch(\\''+id+'\\')" >✅ บันทึก</button>'
    + '</div>';
  dcSetModalBody(html);
}}

function qstSaveTickAch(id) {{
  var a = (DCS.achievements||[]).find(function(x){{return x.id===id;}});
  if (!a) return;
  a.done = true;
  a.doneDate = (document.getElementById('atick-date')||{{}}).value || qstToday();
  a.doneNote = ((document.getElementById('atick-note')||{{}}).value||'').trim();
  if (!DCS.questHistory) DCS.questHistory = [];
  DCS.questHistory.push({{
    id: 'h'+Date.now().toString(36), type: 'achievement',
    title: a.title, date: a.doneDate, note: a.doneNote
  }});
  dcCloseModal(); qstAfterChange(); renderQuestView();
  showToast('🏆 บันทึกความสำเร็จแล้ว!');
}}

function qstOpenAchForm(id) {{
  if (!saIsUnlocked()) {{
    dcOpenPwModal('🔒 ยืนยันตัวตน','กรอกรหัสเพื่อแก้ไขความสำเร็จ',function(){{saUnlock();qstOpenAchForm(id);}});
    return;
  }}
  var a = id ? (DCS.achievements||[]).find(function(x){{return x.id===id;}}) : null;
  var catOpts = Object.keys(ACH_CAT).map(function(k){{
    return '<option value="'+k+'"'+(a&&a.cat===k?' selected':'')+'>'+ACH_CAT[k].icon+' '+ACH_CAT[k].label+'</option>';
  }}).join('');
  var html = '<div class="dc-modal-head"><h3>'+(a?'แก้ไขความสำเร็จ':'เพิ่มความสำเร็จ')+'</h3><button class="dc-x" onclick="dcCloseModal()">✕</button></div>'
    + '<div class="dc-modal-scroll">'
    + '<div class="dc-field"><label>ชื่อ</label><input class="dc-inp" id="af-title" value="'+escapeHtml(a?a.title:'')+'"></div>'
    + '<div class="dc-field"><label>หมวด</label><select class="dc-inp" id="af-cat">'+catOpts+'</select></div>'
    + '<div class="dc-field"><label>เป้าหมาย Day</label><input class="dc-inp" type="number" id="af-day" value="'+(a?a.day:30)+'" min="1" max="999"></div>'
    + '<div class="dc-field"><label>ไอคอน (emoji)</label><input class="dc-inp" id="af-icon" value="'+(a?a.icon:'🎯')+'" style="font-size:20px"></div>'
    + '<div class="dc-field"><label>รายละเอียด</label><input class="dc-inp" id="af-desc" value="'+escapeHtml(a?a.desc:'')+'"></div>'
    + '</div>'
    + '<div class="dc-modal-foot">'
    + '<button class="dc-btn ghost" onclick="dcCloseModal()">ยกเลิก</button>'
    + '<button class="dc-btn primary" onclick="qstSaveAchForm(\\''+( a?a.id:'')+'\\')" >💾 บันทึก</button>'
    + '</div>';
  dcSetModalBody(html);
  setTimeout(function(){{ var el=document.getElementById('af-title'); if(el) el.focus(); }}, 100);
}}

function qstSaveAchForm(id) {{
  var title = ((document.getElementById('af-title')||{{}}).value||'').trim();
  if (!title) {{ showToast('กรอกชื่อด้วย'); return; }}
  if (!DCS.achievements) DCS.achievements = [];
  if (id) {{
    var idx = DCS.achievements.findIndex(function(x){{return x.id===id;}});
    if (idx>=0) {{
      DCS.achievements[idx].title = title;
      DCS.achievements[idx].cat   = document.getElementById('af-cat').value;
      DCS.achievements[idx].day   = parseInt(document.getElementById('af-day').value)||30;
      DCS.achievements[idx].icon  = document.getElementById('af-icon').value.trim()||'🎯';
      DCS.achievements[idx].desc  = ((document.getElementById('af-desc')||{{}}).value||'').trim();
    }}
  }} else {{
    DCS.achievements.push({{
      id: 'a'+Date.now().toString(36), title: title,
      cat: document.getElementById('af-cat').value,
      day: parseInt(document.getElementById('af-day').value)||30,
      icon: document.getElementById('af-icon').value.trim()||'🎯',
      desc: ((document.getElementById('af-desc')||{{}}).value||'').trim(),
      done: false, doneDate: '', doneNote: ''
    }});
  }}
  dcCloseModal(); qstAfterChange(); renderQuestView();
  showToast(id ? 'อัปเดตแล้ว' : 'เพิ่มความสำเร็จแล้ว');
}}

function qstDeleteAch(id) {{
  if (!saIsUnlocked()) {{
    dcOpenPwModal('🔒 ยืนยันตัวตน','กรอกรหัสเพื่อลบ',function(){{saUnlock();qstDeleteAch(id);}});
    return;
  }}
  if (!confirm('ลบรายการนี้?')) return;
  DCS.achievements = (DCS.achievements||[]).filter(function(a){{return a.id!==id;}});
  qstAfterChange(); renderQuestView();
  showToast('ลบแล้ว');
}}

// ── Plans CRUD ──
function qstTickPlan(id) {{
  if (!saIsUnlocked()) {{
    dcOpenPwModal('🔒 ยืนยันตัวตน','กรอกรหัสเพื่อบันทึก',function(){{saUnlock();qstTickPlan(id);}});
    return;
  }}
  if (!DCS.plans) DCS.plans = {{daily:[],weekly:[],monthly:[]}};
  var found = null;
  ['daily','weekly','monthly'].forEach(function(t) {{
    (DCS.plans[t]||[]).forEach(function(p) {{
      if (p.id === id) found = p;
    }});
  }});
  if (!found) return;
  found.done = !found.done;
  if (found.done) {{
    if (!DCS.questHistory) DCS.questHistory = [];
    DCS.questHistory.push({{id:'h'+Date.now().toString(36),type:'plan',title:found.text,date:qstToday(),note:''}});
  }}
  qstAfterChange(); renderQuestView();
}}

function qstOpenPlanForm(id) {{
  if (!saIsUnlocked()) {{
    dcOpenPwModal('🔒 ยืนยันตัวตน','กรอกรหัสเพื่อแก้ไข',function(){{saUnlock();qstOpenPlanForm(id);}});
    return;
  }}
  if (!DCS.plans) DCS.plans = {{daily:[],weekly:[],monthly:[]}};
  var p = null;
  var foundType = qstPlanType;
  if (id) {{
    ['daily','weekly','monthly'].forEach(function(t) {{
      (DCS.plans[t]||[]).forEach(function(x) {{
        if (x.id === id) {{ p = x; foundType = t; }}
      }});
    }});
  }}
  var html = '<div class="dc-modal-head"><h3>'+(p?'แก้ไขรายการ':'เพิ่มรายการใหม่')+'</h3><button class="dc-x" onclick="dcCloseModal()">✕</button></div>'
    + '<div class="dc-modal-scroll">'
    + '<div class="dc-field"><label>รายการ</label><input class="dc-inp" id="pf-text" value="'+escapeHtml(p?p.text:'')+'"></div>'
    + '<div class="dc-field"><label>ความสำคัญ</label><select class="dc-inp" id="pf-pri">'
    + '<option value="high"'+(p&&p.pri==='high'?' selected':'')+'>🔴 สำคัญมาก</option>'
    + '<option value="med"'+(p&&p.pri==='med'?' selected':'')+'>🟡 ปานกลาง</option>'
    + '<option value="low"'+(!p||p.pri==='low'?' selected':'')+'>🟢 ต่ำ</option>'
    + '</select></div>'
    + '<div class="dc-field"><label>ประเภท</label><select class="dc-inp" id="pf-type">'
    + '<option value="daily"'+(foundType==='daily'?' selected':'')+'>รายวัน</option>'
    + '<option value="weekly"'+(foundType==='weekly'?' selected':'')+'>รายสัปดาห์</option>'
    + '<option value="monthly"'+(foundType==='monthly'?' selected':'')+'>รายเดือน</option>'
    + '</select></div>'
    + '</div>'
    + '<div class="dc-modal-foot"><button class="dc-btn ghost" onclick="dcCloseModal()">ยกเลิก</button>'
    + '<button class="dc-btn primary" onclick="qstSavePlanForm(\\''+( p?p.id:'')+'\\')" >💾 บันทึก</button></div>';
  dcSetModalBody(html);
  setTimeout(function(){{ var el=document.getElementById('pf-text'); if(el) el.focus(); }}, 100);
}}

function qstSavePlanForm(id) {{
  var text = ((document.getElementById('pf-text')||{{}}).value||'').trim();
  if (!text) {{ showToast('กรอกรายการด้วย'); return; }}
  var pri = (document.getElementById('pf-pri')||{{}}).value || 'low';
  var newType = (document.getElementById('pf-type')||{{}}).value || 'daily';
  if (!DCS.plans) DCS.plans = {{daily:[],weekly:[],monthly:[]}};
  if (id) {{
    var oldType = null;
    ['daily','weekly','monthly'].forEach(function(t) {{
      if ((DCS.plans[t]||[]).some(function(p){{return p.id===id;}})) oldType = t;
    }});
    if (oldType) {{
      var item = (DCS.plans[oldType]||[]).find(function(p){{return p.id===id;}});
      if (item) {{ item.text = text; item.pri = pri; }}
      if (oldType !== newType && item) {{
        DCS.plans[oldType] = DCS.plans[oldType].filter(function(p){{return p.id!==id;}});
        if (!DCS.plans[newType]) DCS.plans[newType] = [];
        DCS.plans[newType].push(item);
      }}
    }}
  }} else {{
    if (!DCS.plans[newType]) DCS.plans[newType] = [];
    DCS.plans[newType].push({{id:'p'+Date.now().toString(36), text:text, pri:pri, done:false}});
  }}
  qstPlanType = newType;
  dcCloseModal(); qstAfterChange(); renderQuestView();
  showToast(id?'อัปเดตแล้ว':'เพิ่มรายการแล้ว');
}}

function qstDeletePlan(id) {{
  if (!saIsUnlocked()) {{
    dcOpenPwModal('🔒 ยืนยันตัวตน','กรอกรหัสเพื่อลบ',function(){{saUnlock();qstDeletePlan(id);}});
    return;
  }}
  if (!confirm('ลบรายการนี้?')) return;
  if (!DCS.plans) return;
  ['daily','weekly','monthly'].forEach(function(t) {{
    DCS.plans[t] = (DCS.plans[t]||[]).filter(function(p){{return p.id!==id;}});
  }});
  qstAfterChange(); renderQuestView();
  showToast('ลบแล้ว');
}}

// ── Loops CRUD ──
function qstSetLoopStage(id, stage) {{
  if (!saIsUnlocked()) {{
    dcOpenPwModal('🔒 ยืนยันตัวตน','กรอกรหัสเพื่ออัปเดต',function(){{saUnlock();qstSetLoopStage(id,stage);}});
    return;
  }}
  var lp = (DCS.loops||[]).find(function(x){{return x.id===id;}});
  if (!lp) return;
  lp.stage = stage;
  lp.updatedAt = qstToday();
  if (!DCS.questHistory) DCS.questHistory = [];
  var s = LOOP_STG[stage] || {{icon:'🔄', label:stage}};
  DCS.questHistory.push({{
    id:'h'+Date.now().toString(36), type:'loop',
    title:lp.title+' → '+s.icon+' '+s.label,
    date:lp.updatedAt, note:''
  }});
  qstAfterChange(); renderQuestView();
}}

function qstOpenLoopForm(id) {{
  if (!saIsUnlocked()) {{
    dcOpenPwModal('🔒 ยืนยันตัวตน','กรอกรหัสเพื่อแก้ไข',function(){{saUnlock();qstOpenLoopForm(id);}});
    return;
  }}
  var lp = id ? (DCS.loops||[]).find(function(x){{return x.id===id;}}) : null;
  var stgOpts = ''
    + '<option value="learn"'+(lp&&lp.stage==='learn'?' selected':'')+'>📚 หาความรู้</option>'
    + '<option value="do"'+(lp&&lp.stage==='do'?' selected':'')+'>🔨 ลงมือทำ</option>'
    + '<option value="improve"'+(lp&&lp.stage==='improve'?' selected':'')+'>🔍 ปรับปรุง</option>'
    + '<option value="repeat"'+(lp&&lp.stage==='repeat'?' selected':'')+'>♻️ ทำซ้ำ</option>';
  var html = '<div class="dc-modal-head"><h3>'+(lp?'แก้ไข Loop':'เพิ่ม Loop ใหม่')+'</h3><button class="dc-x" onclick="dcCloseModal()">✕</button></div>'
    + '<div class="dc-modal-scroll">'
    + '<div class="dc-field"><label>หัวข้อ</label><input class="dc-inp" id="lf-title" value="'+escapeHtml(lp?lp.title:'')+'"></div>'
    + '<div class="dc-field"><label>Stage ปัจจุบัน</label><select class="dc-inp" id="lf-stage">'+stgOpts+'</select></div>'
    + '<div class="dc-field"><label>บันทึก</label><textarea class="dc-inp" id="lf-note" rows="3" placeholder="สิ่งที่กำลังเรียนรู้ / ทำ...">'+escapeHtml(lp?lp.note||'':'')+'</textarea></div>'
    + '</div>'
    + '<div class="dc-modal-foot"><button class="dc-btn ghost" onclick="dcCloseModal()">ยกเลิก</button>'
    + '<button class="dc-btn primary" onclick="qstSaveLoopForm(\\''+( lp?lp.id:'')+'\\')" >💾 บันทึก</button></div>';
  dcSetModalBody(html);
  setTimeout(function(){{ var el=document.getElementById('lf-title'); if(el) el.focus(); }}, 100);
}}

function qstSaveLoopForm(id) {{
  var title = ((document.getElementById('lf-title')||{{}}).value||'').trim();
  if (!title) {{ showToast('กรอกหัวข้อด้วย'); return; }}
  var stage = (document.getElementById('lf-stage')||{{}}).value || 'learn';
  var note = ((document.getElementById('lf-note')||{{}}).value||'').trim();
  if (!DCS.loops) DCS.loops = [];
  if (id) {{
    var idx = DCS.loops.findIndex(function(x){{return x.id===id;}});
    if (idx>=0) {{
      DCS.loops[idx].title = title;
      DCS.loops[idx].stage = stage;
      DCS.loops[idx].note  = note;
      DCS.loops[idx].updatedAt = qstToday();
    }}
  }} else {{
    DCS.loops.push({{id:'l'+Date.now().toString(36), title:title, stage:stage, note:note, updatedAt:qstToday()}});
  }}
  dcCloseModal(); qstAfterChange(); renderQuestView();
  showToast(id?'อัปเดตแล้ว':'เพิ่ม Loop แล้ว');
}}

function qstDeleteLoop(id) {{
  if (!saIsUnlocked()) {{
    dcOpenPwModal('🔒 ยืนยันตัวตน','กรอกรหัสเพื่อลบ',function(){{saUnlock();qstDeleteLoop(id);}});
    return;
  }}
  if (!confirm('ลบ Loop นี้?')) return;
  DCS.loops = (DCS.loops||[]).filter(function(x){{return x.id!==id;}});
  qstAfterChange(); renderQuestView();
  showToast('ลบแล้ว');
}}

// ── History CRUD ──
function qstClearHistory() {{
  if (!saIsUnlocked()) {{
    dcOpenPwModal('🔒 ยืนยันตัวตน','กรอกรหัสเพื่อล้างประวัติ',function(){{saUnlock();qstClearHistory();}});
    return;
  }}
  var n = (DCS.questHistory||[]).length;
  if (!n || !confirm('ล้างประวัติทั้งหมด '+n+' รายการ?')) return;
  DCS.questHistory = [];
  qstAfterChange(); renderQuestView();
  showToast('ล้างประวัติแล้ว');
}}

// ── Edit questMeta (password-gated) ──
function qstEditMeta() {{
  if (!saIsUnlocked()) {{
    dcOpenPwModal('🔒 ยืนยันตัวตน','กรอกรหัสเพื่อแก้ค่า',function(){{saUnlock();qstEditMeta();}});
    return;
  }}
  var m = DCS.questMeta || {{}};
  var html = '<div class="dc-modal-head"><h3>⚙️ ตั้งค่า 90 วัน</h3><button class="dc-x" onclick="dcCloseModal()">✕</button></div>'
    + '<div class="dc-modal-scroll">'
    + '<div class="dc-field"><label>วันเริ่มต้น (YYYY-MM-DD)</label><input class="dc-inp" type="date" id="qm-start" value="'+(m.startDate||'2026-05-31')+'"></div>'
    + '<div class="dc-field"><label>จำนวนวันทั้งหมด</label><input class="dc-inp" type="number" id="qm-total" value="'+(m.totalDays||90)+'" min="1" max="365"></div>'
    + '<div class="dc-field"><label>เป้าหมายเปิดร้าน (Day)</label><input class="dc-inp" type="number" id="qm-open" value="'+(m.targetOpenDay||30)+'" min="1"></div>'
    + '</div>'
    + '<div class="dc-modal-foot">'
    + '<button class="dc-btn ghost" onclick="dcCloseModal()">ยกเลิก</button>'
    + '<button class="dc-btn primary" onclick="qstSaveMeta()">💾 บันทึก</button>'
    + '</div>';
  dcSetModalBody(html);
}}

function qstSaveMeta() {{
  if (!DCS.questMeta) DCS.questMeta = {{}};
  DCS.questMeta.startDate     = (document.getElementById('qm-start')||{{}}).value || '2026-05-31';
  DCS.questMeta.totalDays     = parseInt((document.getElementById('qm-total')||{{}}).value)||90;
  DCS.questMeta.targetOpenDay = parseInt((document.getElementById('qm-open')||{{}}).value)||30;
  dcCloseModal(); qstAfterChange(); renderQuestView();
  showToast('บันทึกค่าแล้ว');
}}

// ── Boot ──
applyStoredTheme();
showView('view-home');
applyRoast();
saUpdateChip();
dcAutoPullOnBoot();
</script>

</body>
</html>
"""


# ─────────────────────────────────────────────────────────────
# Step 6: Assemble & save
# ─────────────────────────────────────────────────────────────

def build_html(all_history: dict[str, dict], generated_at: str) -> str:
    data_json, comp_json = build_data_json(all_history)
    platforms_json = json.dumps(list(all_history.keys()), ensure_ascii=False)
    intel_json = json.dumps(load_intel_json(), ensure_ascii=False)
    tracker_json = json.dumps(load_tracker_json(), ensure_ascii=False)

    # ── Update log / history (Platforms + Intelligence) ──
    log = update_log.load_log()
    log_entries = sorted(log.get("entries", []), key=lambda e: e.get("ts", ""), reverse=True)
    update_log_json = json.dumps(log_entries, ensure_ascii=False)
    update_summary_json = json.dumps(update_log.summarize(log), ensure_ascii=False)
    logos_json = json.dumps(load_logos(), ensure_ascii=False)
    drink_costs_json = json.dumps(load_drink_costs(), ensure_ascii=False)

    sidebar_nav = build_sidebar_nav(all_history)

    platform_views_parts = []
    for platform, raw in all_history.items():
        platform_views_parts.append(build_platform_view(platform, raw))
    platform_views = "\n\n".join(platform_views_parts)

    return HTML_TEMPLATE.format(
        DATA_JSON=data_json,
        COMP_JSON=comp_json,
        PLATFORMS_JSON=platforms_json,
        INTEL_JSON=intel_json,
        TRACKER_JSON=tracker_json,
        UPDATE_LOG_JSON=update_log_json,
        UPDATE_SUMMARY_JSON=update_summary_json,
        LOGOS_JSON=logos_json,
        DRINK_COSTS_JSON=drink_costs_json,
        GENERATED_AT=generated_at,
        SIDEBAR_NAV_ITEMS=sidebar_nav,
        PLATFORM_VIEWS=platform_views,
    )


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def generate_dashboard(input_path: str) -> Path:
    print(f"Input: {input_path}\n")

    today = datetime.now().strftime("%Y%m%d")
    generated_at = datetime.now().strftime("%d %B %Y")

    # Normalize all platforms found in the given path
    normalize_results = run_normalize_all(input_path)
    if not normalize_results:
        print("[warn] ไม่สามารถ normalize ได้เลย — จะพยายามโหลดจาก history ที่มีอยู่")

    # Load all available history for today
    all_history = load_all_history(today)

    # ── บันทึก update log: 1 รายการต่อ platform ที่นำเข้าจริงในรอบนี้ ──
    for platform, json_path in normalize_results:
        rows = all_history.get(platform, {}).get("row_count")
        rows_txt = f" ({rows} แถว)" if rows else ""
        update_log.log_update(
            category="platform",
            action="import",
            scope=platform,
            summary=f"นำเข้าข้อมูล {PLATFORM_LABELS.get(platform, platform)}{rows_txt}",
            count=rows,
        )

    if not all_history:
        raise RuntimeError(
            "ไม่พบข้อมูล normalized สำหรับวันนี้ใน data/history/ "
            "กรุณาตรวจสอบ path ที่ระบุ"
        )

    print(f"\nPlatforms available: {list(all_history.keys())}")

    html = build_html(all_history, generated_at)

    dashboard_dir = PROJECT_ROOT / "dashboard"
    dashboard_dir.mkdir(exist_ok=True)

    # Name after last successfully normalized platform (or first in history)
    if normalize_results:
        last_platform = normalize_results[-1][0]
    else:
        last_platform = list(all_history.keys())[-1]

    named_path = dashboard_dir / f"{last_platform}-{today}.html"
    index_path = dashboard_dir / "index.html"

    named_path.write_text(html, encoding="utf-8")
    shutil.copy(named_path, index_path)

    print(f"\n[ok] บันทึกแล้ว : {named_path}")
    print(f"[ok] index.html  : {index_path}")
    _check_js_syntax(index_path)
    return index_path


def _check_js_syntax(html_path: Path) -> None:
    checker = PROJECT_ROOT / "scripts" / "check_js_syntax.js"
    if shutil.which("node") and checker.exists():
        r = subprocess.run(["node", str(checker), str(html_path)])
        if r.returncode == 1:
            sys.exit("build หยุด: พบ JS syntax error ในผลลัพธ์ (ดูข้างบน) — แก้ก่อน deploy")
    else:
        print("[warn] ข้ามการเช็ค JS syntax (ไม่พบ node) — แนะนำติดตั้ง Node เพื่อความปลอดภัย")


def rebuild_dashboard() -> Path:
    """
    สร้าง index.html ใหม่จาก history ล่าสุดที่มีอยู่ — ไม่ normalize ใหม่ ไม่บันทึก log
    ใช้ refresh dashboard หลังอัปเดต Intelligence/log โดยไม่ต้อง import ข้อมูล platform ซ้ำ
    """
    history_dir = PROJECT_ROOT / "data" / "history"
    dates = set()
    for p in history_dir.glob("*_*.json"):
        stem = p.stem.rsplit("_", 1)
        if len(stem) == 2 and stem[1].isdigit():
            dates.add(stem[1])
    if not dates:
        raise RuntimeError("ไม่พบไฟล์ history ใน data/history/ — ยังไม่มีข้อมูลให้ rebuild")

    latest = max(dates)
    print(f"[rebuild] ใช้ข้อมูล history วันที่ {latest}")
    all_history = load_all_history(latest)
    if not all_history:
        raise RuntimeError(f"โหลด history วันที่ {latest} ไม่ได้")

    generated_at = datetime.now().strftime("%d %B %Y")
    html = build_html(all_history, generated_at)

    dashboard_dir = PROJECT_ROOT / "dashboard"
    dashboard_dir.mkdir(exist_ok=True)
    index_path = dashboard_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    print(f"[ok] index.html อัปเดตแล้ว : {index_path}")
    _check_js_syntax(index_path)
    return index_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/generate_dashboard.py <path|--rebuild>")
        print("  <path>     = ไฟล์ CSV / folder platform / root sample-data folder (นำเข้า + log)")
        print("  --rebuild  = สร้าง dashboard ใหม่จาก history ล่าสุด (ไม่ import, ไม่ log)")
        sys.exit(1)
    if sys.argv[1] in ("--rebuild", "-r"):
        rebuild_dashboard()
    else:
        generate_dashboard(sys.argv[1])
