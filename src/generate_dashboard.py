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
        "title": "RAINTREE CAFE สกลนคร (Verified 21 May 2026)",
        "summary": "Destination cafe ระดับกลาง-บน Concept 'เขาใหญ่กลางเมือง' · Facebook 77K · Google 4.7/5 · Day cafe + Night cocktail bar · Pet-friendly",
        "updated": "21 May 2026",
        "source_url": "https://www.facebook.com/p/Raintreecafe-61552983815422/", "thumbnail_url": "",
        "tags": ["สกลนคร", "Local", "Independent", "Destination", "Pet-friendly", "Cocktail"],
        "relevance": "high",
        "detail": "RAINTREE CAFE — 391 ถนนสกลนคร-กาฬสินธุ์ ต.ดงมะไฟ อ.เมือง จ.สกลนคร (ตรงข้าม ปตท.ศูนย์ราชการ)\nโทร: 065-391-4662 / 081-345-4643\n\nSocial Media (verified):\n• Facebook: ~77,000 followers — ใหญ่มากสำหรับ local cafe · crosspost TikTok content\n• Instagram: @raintree_sakon · 11,000 followers · 293 posts · Aesthetic nature photography\n• TikTok: @raintree91 · Comedy/personality-driven · 1 viral video 152,900 likes confirmed\n\nTikTok Content Strategy (verified):\n• Tone: Comedy + personality-driven ไม่ใช่ polished brand content\n• เจ้าของออกกล้องเอง · พนักงานเป็น recurring characters\n• Themes: staff humor ('เจ้านายอยู่ vs ไม่อยู่'), barista spotlight, customer comedy, photo tips\n• เนื้อหา night/bar segment: 'กาแฟดึกที่ Raintree' — promote evening visits\n\nHashtag Strategy:\n• Always-on: #raintreecafe #เรนทรีคาเฟ่ #คาเฟ่สกลนคร #สกลนคร\n• Branded UGC: #raintreemoments — เก็บ fan content\n• Secondary: #sakonnakhon #ร้านกาแฟสกลนคร\n\nReviews:\n• Google Maps: 4.7/5 จาก 246 รีวิว · #14 จาก 246 คาเฟ่สกลนคร\n• Wongnai: 4.1/5 · #3 จาก 181 คาเฟ่\n• Sentiment: 'ฟิลเขาใหญ่กลางเมือง' พูดถึงซ้ำทุก review\n\nจุดแข็ง:\n• Concept 'เขาใหญ่กลางเมือง' ชัดเจน ลูกค้าจำได้\n• พื้นที่ใหญ่มาก 81-150 ที่นั่ง Indoor+Outdoor (สนามหญ้า/สระน้ำ/ต้นจามจุรี)\n• Double segment: Day cafe (กาแฟ/ชา) + Night bar (Cocktail)\n• Pet-friendly — niche หายากในสกลนคร\n• เมนูดัง: มัทฉะน้ำส้มสด 'อร่อยที่สุดในเมือง'\n\nช่องว่างสำหรับคู่แข่ง:\n• Wongnai presence น้อย (3 รีวิว) — โอกาสสำหรับร้านที่ทำ Wongnai marketing\n• เวลาเปิดไม่สม่ำเสมอ (บางรีวิวระบุปิดก่อนเวลา)\n• Delivery Wongnai-direct เท่านั้น ไม่พบ LINE MAN/GrabFood\n• เน้น aesthetic + comedy มากกว่า specialty/origin beans story",
        "pricing": {
            "espresso":{"price":"","note":""},"americano":{"price":"80","note":"~ประมาณ"},
            "latte":{"price":"","note":""},"cappuccino":{"price":"","note":""},
            "cold_brew":{"price":"","note":""},"frappe":{"price":"","note":""},
            "matcha":{"price":"120","note":"น้ำส้มสด (ขายดี)"},"signature_drink":{"price":"130","note":"มัทฉะมะพร้าว"},
            "food":{"price":"90","note":"เค้กชาเขียว"},
            "other": [{"name":"คาราเมล มัคคิอาโต้","price":"110"},{"name":"เฉลี่ย/คน","price":"101-250"}]
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
        "title": "ร้านกาแฟท้องถิ่นสกลนคร — สถานะ Delivery (Updated 21 May 2026)",
        "summary": "Alice Cafe (LINE MAN ✅) · FIKA Cafè (LINE MAN ✅) · ZMd Specialty (LINE MAN ✅) · RAINTREE (ไม่ verified) · Café Amazon (GrabFood ✅) · supa.cafe (เปิดใหม่ 2025)",
        "updated": "21 May 2026",
        "source_url": "https://www.wongnai.com/listings/sakonnakhon-coffee-cafe", "thumbnail_url": "",
        "tags": ["specialty", "local", "delivery", "สกลนคร", "Wongnai", "LINE MAN"],
        "relevance": "high",
        "detail": "ร้านกาแฟสกลนครและสถานะ Delivery (verified จาก Wongnai / LINE MAN — 21 พ.ค. 2026):\n\n✅ ยืนยันอยู่บน LINE MAN / Wongnai Delivery:\n• Alice Coffee and Bread — Wongnai x LINE MAN · จ-ศ 08:30-16:30 / เสาร์ 09:00-17:30 · เมนูดัง: Thai Tea 65฿, Coco Dirty 95฿\n• FIKA Cafè & Coworking — Wongnai x LINE MAN ยืนยัน\n• ZMd cafe' Specialty Coffee — Wongnai x LINE MAN ยืนยัน\n• Café Amazon (สาขาสกลนคร) — GrabFood ยืนยัน chain ใหญ่\n\n⚠️ มีตัวตนบน Social/Wongnai แต่ยังไม่ verified บน delivery app:\n• RAINTREE Cafe — Facebook 77K, Instagram @raintree_sakon · เน้น dine-in day cafe + night bar · Wongnai ระบุ delivery 08:00-17:00 แต่ยังไม่พบบน LINE MAN/GrabFood โดยตรง\n\n🆕 เปิดใหม่ 2025-2026:\n• supa.cafe — บรรยากาศ homestyle · ยังไม่ verified delivery\n\nหมายเหตุ: Web search ไม่สามารถดึงรายการร้านจาก LINE MAN/GrabFood โดยตรงได้ (แสดงตาม GPS เท่านั้น) ต้องเปิดแอปในพื้นที่สกลนครเพื่อยืนยัน\n\nWongnai รวมร้านกาแฟสกลนคร: https://www.wongnai.com/listings/sakonnakhon-coffee-cafe\n\nเทรนด์ใหม่: LINE MAN แซงหน้า GrabFood เป็นเบอร์ 1 ระดับชาติ — ร้าน local ต่างจังหวัดเน้น Wongnai x LINE MAN มากกว่า GrabFood\nPeak delivery (national): 11:00-13:00 และ 17:00-20:00 น.\nกลยุทธ์: Bundle กาแฟ + เบเกอรี เพิ่มมูลค่าต่อบิล offset ค่า GP 30-35%",
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


def build_home_cards(all_history: dict[str, dict]) -> str:
    cards = []
    for platform, raw in all_history.items():
        df = pd.DataFrame(raw["data"])
        total_reach = _safe_int(df["reach"].sum()) if "reach" in df.columns else 0
        color = PLATFORM_COLORS.get(platform, "#888")
        label = PLATFORM_LABELS.get(platform, platform)
        cards.append(
            '<div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">'
            '<div class="text-xs uppercase tracking-widest text-slate-400 mb-2">{label}</div>'
            '<div class="text-4xl font-black" style="color:{color}">{reach}</div>'
            '<div class="text-xs text-slate-400 mt-1">ยอดดูรวม</div>'
            '</div>'.format(
                label=label,
                color=color,
                reach=_fmt(total_reach),
            )
        )
    return "\n".join(cards)


def build_home_comparison_rows(all_history: dict[str, dict]) -> str:
    rows = []
    for platform, raw in all_history.items():
        df = pd.DataFrame(raw["data"])
        metrics = compute_metrics(df, platform)
        color = PLATFORM_COLORS.get(platform, "#888")
        label = PLATFORM_LABELS.get(platform, platform)
        rows.append(
            '<tr class="hover:bg-slate-50 transition-colors">'
            '<td class="px-4 py-3 font-semibold flex items-center gap-2">'
            '<span class="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0" style="background:{color}"></span>'
            '{label}</td>'
            '<td class="px-4 py-3 text-right tabular-nums">{total_reach}</td>'
            '<td class="px-4 py-3 text-right tabular-nums">{avg_reach}</td>'
            '<td class="px-4 py-3 text-right tabular-nums">{avg_er}%</td>'
            '<td class="px-4 py-3 text-right tabular-nums">{total_eng}</td>'
            '</tr>'.format(
                color=color,
                label=label,
                total_reach=_fmt(metrics["total_reach"]),
                avg_reach=_fmt(metrics["avg_reach"], 1),
                avg_er=_fmt(metrics["avg_er"], 2),
                total_eng=_fmt(metrics["total_engagement"]),
            )
        )
    return "\n".join(rows)


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
      --bg:           #f1f5f9;
      --sidebar:      #ffffff;
      --card:         #ffffff;
      --card-border:  #e2e8f0;
      --text:         #0f172a;
      --text-muted:   #64748b;
      --grid:         #f1f5f9;
      --nav-active:   #f1f5f9;
      --nav-text:     #0f172a;
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
    .intel-tab.active, .pricing-tab.active {{
      background: var(--nav-active); color: var(--text);
      border-color: var(--card-border);
    }}
    .intel-tab:hover:not(.active), .pricing-tab:hover:not(.active) {{
      background: var(--nav-active);
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
  </style>
</head>
<body style="font-family: 'Prompt', system-ui, sans-serif" class="text-slate-800">

<!-- Mobile top bar -->
<div id="mobile-topbar" class="items-center justify-between px-4 py-3">
  <div>
    <div class="text-sm font-black" style="color:var(--text)">☕ Social Analytics</div>
    <div class="text-[10px]" style="color:var(--text-muted)">ร้านกาแฟ สกลนคร</div>
  </div>
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
      <div>
        <div class="text-lg font-black text-slate-800 leading-tight">☕ Social Analytics</div>
        <div class="text-xs text-slate-400 mt-0.5">ร้านกาแฟ สกลนคร</div>
      </div>
      <button onclick="closeSidebar()" id="sidebar-close-btn"
        class="p-1.5 rounded-lg hover:bg-slate-100 transition-colors text-slate-400"
        style="display:none" aria-label="ปิดเมนู">
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

      <button onclick="showView('view-pricing')" id="nav-pricing"
        class="nav-btn w-full text-left px-4 py-2.5 rounded-xl flex items-center gap-3
               text-slate-600 hover:bg-slate-50 transition-colors text-sm">
        <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        ราคากลางร้านกาแฟ
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

      <div class="pt-2 pb-1">
        <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest px-4">Tools</p>
      </div>

      <button onclick="showView('view-import')" id="nav-import"
        class="nav-btn w-full text-left px-4 py-2.5 rounded-xl flex items-center gap-3
               text-slate-600 hover:bg-slate-50 transition-colors text-sm">
        <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
        </svg>
        นำเข้าข้อมูล
      </button>

    </nav>

    <!-- Footer: theme toggle + date -->
    <div class="p-4 border-t border-slate-100">
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

      <h1 class="text-3xl font-black text-slate-800 mb-6">ภาพรวม Social Media</h1>

      <!-- Platform reach cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {HOME_CARDS}
      </div>

      <!-- Comparison table -->
      <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-6">
        <h2 class="text-sm font-bold text-slate-700 mb-4">Platform Comparison</h2>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b-2 border-slate-200">
                <th class="px-4 py-3 text-left text-xs font-bold uppercase tracking-widest text-slate-500 whitespace-nowrap">Platform</th>
                <th class="px-4 py-3 text-right text-xs font-bold uppercase tracking-widest text-slate-500 whitespace-nowrap">ยอดดูรวม</th>
                <th class="px-4 py-3 text-right text-xs font-bold uppercase tracking-widest text-slate-500 whitespace-nowrap">ยอดดูเฉลี่ย/วัน</th>
                <th class="px-4 py-3 text-right text-xs font-bold uppercase tracking-widest text-slate-500 whitespace-nowrap">อัตราการมีส่วนร่วม</th>
                <th class="px-4 py-3 text-right text-xs font-bold uppercase tracking-widest text-slate-500 whitespace-nowrap">การมีส่วนร่วมรวม</th>
              </tr>
            </thead>
            <tbody>
              {HOME_COMPARISON_ROWS}
            </tbody>
          </table>
        </div>
      </div>

      <!-- 4 doughnut charts: Platform Comparison -->
      <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5">
        <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 flex flex-col">
          <h2 class="text-sm font-semibold text-slate-700 mb-3">ยอดดูรวม</h2>
          <div class="relative compare-chart-wrap" style="height:140px"><canvas id="chart-compare-reach"></canvas></div>
          <div class="mt-3 space-y-1.5" id="legend-compare-reach"></div>
        </div>
        <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 flex flex-col">
          <h2 class="text-sm font-semibold text-slate-700 mb-3">ยอดดูเฉลี่ย/วัน</h2>
          <div class="relative compare-chart-wrap" style="height:140px"><canvas id="chart-compare-daily"></canvas></div>
          <div class="mt-3 space-y-1.5" id="legend-compare-daily"></div>
        </div>
        <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 flex flex-col">
          <h2 class="text-sm font-semibold text-slate-700 mb-3">อัตราการมีส่วนร่วม (%)</h2>
          <div class="relative compare-chart-wrap" style="height:140px"><canvas id="chart-compare-engagement-rate"></canvas></div>
          <div class="mt-3 space-y-1.5" id="legend-compare-engagement-rate"></div>
        </div>
        <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 flex flex-col">
          <h2 class="text-sm font-semibold text-slate-700 mb-3">การมีส่วนร่วมรวม</h2>
          <div class="relative compare-chart-wrap" style="height:140px"><canvas id="chart-compare-engagement-total"></canvas></div>
          <div class="mt-3 space-y-1.5" id="legend-compare-engagement-total"></div>
        </div>
      </div>

    </div>

    <!-- ── Platform Views (injected) ── -->
    {PLATFORM_VIEWS}

    <!-- ── Intel View ── -->
    <div id="view-intel" class="view">
      <h1 class="text-3xl font-black text-slate-800 mb-6">ข่าวกรองตลาด</h1>

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
      <h1 class="text-3xl font-black text-slate-800 mb-6">ราคาเมนูกาแฟ — เปรียบเทียบคู่แข่ง</h1>

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
      <h1 class="text-3xl font-black text-slate-800 mb-1">วิเคราะห์เชิงลึกคู่แข่ง</h1>
      <p class="text-sm text-slate-500 mb-6">5 มิติ: Social Presence · Content Strategy · Pricing · Services/Positioning · Reviews</p>

      <div class="flex flex-wrap gap-2 mb-6">
        <button class="intel-tab active" id="deep-tab-overview"  onclick="setDeepTab('overview')">📊 ภาพรวมการเปลี่ยนแปลง</button>
        <button class="intel-tab"        id="deep-tab-detail"    onclick="setDeepTab('detail')">☕ รายร้าน</button>
        <button class="intel-tab"        id="deep-tab-timeline"  onclick="setDeepTab('timeline')">📅 Timeline</button>
      </div>

      <div id="deep-content-overview"></div>
      <div id="deep-content-detail"   style="display:none"></div>
      <div id="deep-content-timeline" style="display:none"></div>
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
  if (viewId === 'view-home')    {{ try {{ initHomeBar(); }} catch(e) {{ console.error('initHomeBar', e); }} return; }}
  if (viewId === 'view-intel')   {{ try {{ renderIntelCards(); }} catch(e) {{ console.error('renderIntelCards', e); }} return; }}
  if (viewId === 'view-pricing') {{ try {{ renderPricingView(); }} catch(e) {{ console.error('renderPricingView', e); }} return; }}
  if (viewId === 'view-competitor-deep') {{ try {{ renderDeepTab(); }} catch(e) {{ console.error('renderDeepTab', e); }} return; }}
  const platform = viewId.replace('view-', '');
  if (!DATA[platform]) return;
  try {{ initLineChart(platform); }} catch(e) {{ console.error('initLineChart', e); }}
  try {{ initDoughnutChart(platform); }} catch(e) {{ console.error('initDoughnutChart', e); }}
}}

function initHomeBar() {{
  const PCOLORS = ['#EE1D52', '#3b82f6', '#ec4899'];
  const labels  = COMP.labels;
  const tc      = getThemeChartCfg();
  const metrics = [
    {{ id:'chart-compare-reach',            legId:'legend-compare-reach',            data:COMP.total_reach,      fmt:v=>Number(v).toLocaleString('th-TH') }},
    {{ id:'chart-compare-daily',            legId:'legend-compare-daily',            data:COMP.avg_reach,        fmt:v=>Number(v).toLocaleString('th-TH',{{minimumFractionDigits:1,maximumFractionDigits:1}}) }},
    {{ id:'chart-compare-engagement-rate',  legId:'legend-compare-engagement-rate',  data:COMP.avg_er,           fmt:v=>v+'%' }},
    {{ id:'chart-compare-engagement-total', legId:'legend-compare-engagement-total', data:COMP.total_engagement, fmt:v=>Number(v).toLocaleString('th-TH') }},
  ];
  metrics.forEach(({{id,legId,data,fmt}}) => {{
    if (chartInstances[id]) {{ chartInstances[id].destroy(); delete chartInstances[id]; }}
    const el = document.getElementById(id);
    if (!el) return;
    const total = data.reduce((a,b)=>a+b,0);
    chartInstances[id] = new Chart(el.getContext('2d'), {{
      type: 'doughnut',
      data: {{ labels, datasets: [{{ data, backgroundColor:PCOLORS.map(c=>c+'cc'), borderColor:PCOLORS, borderWidth:2, hoverOffset:5 }}] }},
      options: {{
        responsive:true, maintainAspectRatio:false, cutout:'68%',
        plugins: {{
          legend: {{ display:false }},
          tooltip: {{
            backgroundColor:tc.tooltipBg, titleColor:tc.tooltipText, bodyColor:tc.tooltipText,
            callbacks: {{ label: ctx => ' '+ctx.label+': '+fmt(data[ctx.dataIndex])+'  ('+(total>0?((ctx.parsed/total)*100).toFixed(1):'0.0')+'%)' }}
          }}
        }}
      }}
    }});
    const legEl = document.getElementById(legId);
    if (legEl) {{
      legEl.innerHTML = labels.map((lbl,i)=>
        `<div class="flex items-center justify-between gap-2 text-xs">
          <span class="flex items-center gap-1.5 min-w-0">
            <span class="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0" style="background:${{PCOLORS[i]}}"></span>
            <span class="text-slate-600 truncate">${{lbl}}</span>
          </span>
          <span class="font-semibold tabular-nums flex-shrink-0" style="color:${{PCOLORS[i]}}">${{fmt(data[i])}}</span>
        </div>`
      ).join('');
    }}
  }});
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
  body.classList.toggle('open');
  const chev = document.getElementById('accord-chev-' + id);
  if (chev) chev.style.transform = body.classList.contains('open') ? 'rotate(180deg)' : '';
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
  const initial = (item.title.match(/[฀-๿]/)||[item.title[0]||'?'])[0];
  const socialParts = [
    st.primary_platform || null,
    st.posting_frequency ? 'ความถี่: ' + st.posting_frequency : null,
    st.content_style ? 'สไตล์: ' + st.content_style : null,
    st.engagement_level ? 'engagement: ' + ({{high:'สูง',medium:'ปานกลาง',low:'ต่ำ'}}[st.engagement_level]||st.engagement_level) : null,
  ].filter(Boolean);
  const ops = deriveOpportunity(item);
  const mkList = arr => arr.map(x=>`<li class="text-xs leading-relaxed" style="color:var(--text-muted)">• ${{x}}</li>`).join('');
  const mkSection = (emoji, title, arr) => arr && arr.length
    ? `<div><div class="text-xs font-semibold mb-1" style="color:var(--text)">${{emoji}} ${{title}}</div><ul class="space-y-0.5">${{mkList(arr)}}</ul></div>`
    : '';
  return `<div class="rounded-xl shadow-sm border flex flex-col" style="background:var(--card);border-color:var(--card-border)">
    <div class="p-5 border-b" style="border-color:var(--card-border)">
      <div class="flex items-start gap-3 mb-3">
        <div class="w-10 h-10 rounded-full flex-shrink-0 flex items-center justify-center font-bold text-base text-white" style="background:${{color}}">${{initial}}</div>
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
      ${{mkSection('🗿','จุดแข็ง', item.strengths)}}
      ${{mkSection('🪫','จุดอ่อน', item.weaknesses)}}
      ${{mkSection('📱','การใช้ Social Media', socialParts)}}
      ${{mkSection('💎','โอกาสที่เราแข่งได้', ops)}}
      ${{item.promotions && item.promotions.length ? mkSection('🎯','โปรโมชัน', item.promotions) : ''}}
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
      <div class="intel-accord-hdr" onclick="toggleIntelAccord('${{item.id}}')">
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
              <div class="text-sm font-semibold mb-1.5" style="color:var(--text)">จุดแข็ง</div>
              <ul class="space-y-1">${{item.strengths.map(s=>`<li class="text-sm" style="color:var(--text-muted)">${{s}}</li>`).join('')}}</ul>
            </div>` : ''}}
          ${{item.weaknesses && item.weaknesses.length ? `
            <div class="mb-4">
              <div class="text-sm font-semibold mb-1.5" style="color:var(--text)">จุดอ่อน</div>
              <ul class="space-y-1">${{item.weaknesses.map(w=>`<li class="text-sm" style="color:var(--text-muted)">${{w}}</li>`).join('')}}</ul>
            </div>` : ''}}
          <div class="mb-4">
            <div class="text-sm font-semibold mb-1.5" style="color:var(--text)">การใช้ Social Media</div>
            <p class="text-sm" style="color:var(--text-muted)">${{buildSocialSentence(item.social_trend)}}</p>
          </div>
          <div>
            <div class="text-sm font-semibold mb-1.5" style="color:var(--text)">โอกาสที่เราแข่งได้</div>
            <ul class="space-y-1">${{deriveOpportunity(item).map(o=>`<li class="text-sm" style="color:var(--text-muted)">${{o}}</li>`).join('')}}</ul>
          </div>
        ` : `
          <p class="text-sm mb-3 leading-relaxed" style="color:var(--text-muted)">${{item.summary}}</p>
          ${{item.tags && item.tags.length ? `<div class="mb-4 flex flex-wrap gap-1">${{item.tags.map(t=>`<span class="inline-block text-xs px-2 py-0.5 rounded-full" style="background:var(--nav-active);color:var(--text-muted)">#${{t}}</span>`).join('')}}</div>` : ''}}
          ${{item.detail ? `<p class="text-xs leading-relaxed" style="color:var(--text-muted)">${{item.detail}}</p>` : ''}}
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

    kpiEl.innerHTML = `
      <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
        <div class="text-xs uppercase tracking-widest text-slate-400 mb-3">จำนวนร้านคู่แข่ง</div>
        <div class="kpi-value text-4xl font-black text-slate-800">${{competitors.length}}</div>
        <div class="text-xs text-slate-400 mt-1">ร้านที่พบ</div>
      </div>
      <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
        <div class="text-xs uppercase tracking-widest text-slate-400 mb-3">ราคาเฉลี่ยลาเต้</div>
        <div class="kpi-value text-4xl font-black text-emerald-500">${{avgLatte ? avgLatte.toLocaleString('th-TH') : '—'}}</div>
        <div class="text-xs text-slate-400 mt-1">บาท (เฉลี่ยตลาด)</div>
      </div>
      <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
        <div class="text-xs uppercase tracking-widest text-slate-400 mb-3">ราคาเฉลี่ย Cold Brew</div>
        <div class="kpi-value text-4xl font-black text-blue-500">${{avgColdBrew ? avgColdBrew.toLocaleString('th-TH') : '—'}}</div>
        <div class="text-xs text-slate-400 mt-1">บาท (เฉลี่ยตลาด)</div>
      </div>
      <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
        <div class="text-xs uppercase tracking-widest text-slate-400 mb-3">ร้านที่มีโปร</div>
        <div class="kpi-value text-4xl font-black text-purple-500">${{withPromo}}</div>
        <div class="text-xs text-slate-400 mt-1">จาก ${{competitors.length}} ร้าน</div>
      </div>
    `;
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
    var init = (c.title.match(/[฀-๿]/) || [c.title[0]])[0];
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
        + '<div class="w-9 h-9 rounded-full flex-shrink-0 flex items-center justify-center text-white font-bold text-sm" style="background:' + col + '">' + init + '</div>'
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
    if (v && v.price) priceRows.push([pLabels[k] || k, v.price + ' บาท' + (v.note ? ' (' + v.note + ')' : '')]);
  }});
  (pricing.other || []).forEach(function(o) {{
    if (o.price) priceRows.push([o.name, o.price + ' บาท' + (o.note ? ' (' + o.note + ')' : '')]);
  }});
  var sections = [
    {{ title:'📱 1. Social Presence', rows:[
      ['Platform หลัก', st.primary_platform || '—'],
      ['ความถี่โพสต์', st.posting_frequency || '—'],
      ['Engagement Level', st.engagement_level || '—'],
      ['ที่ตั้ง', comp.location || '—'],
      ['เวลาทำการ', comp.hours || '—'],
    ]}},
    {{ title:'🎬 2. Content Strategy', rows:[
      ['สไตล์ Content', st.content_style || '—'],
      ['Tags', (comp.tags || []).join(', ') || '—'],
      ['รายละเอียด', comp.detail || '—'],
    ]}},
    {{ title:'💰 3. Pricing', rows: priceRows.length ? priceRows : [['', 'ไม่พบราคาสาธารณะ']] }},
    {{ title:'🎯 4. Services & Positioning', rows:[
      ['จุดแข็ง', (comp.strengths || []).join(' · ') || '—'],
      ['โปรโมชัน', (comp.promotions || []).join(' · ') || '—'],
      ['Relevance', comp.relevance || '—'],
    ]}},
    {{ title:'⭐ 5. Reviews & Weaknesses', rows:[
      ['จุดอ่อน', (comp.weaknesses || []).join(' · ') || '—'],
      ['สรุป', comp.summary || '—'],
    ]}},
    {{ title:'🛵 6. Delivery & Food Apps', rows: comp.delivery ? [
      ['แอปหลัก', comp.delivery.primary_app || '—'],
      ['แอปทั้งหมด', (comp.delivery.apps || []).join(', ') || '—'],
      ['Peak Hours', comp.delivery.peak_hours || '—'],
      ['โปรโมชัน', (comp.delivery.active_promos || []).join(' · ') || '—'],
      ['หมายเหตุ', comp.delivery.notes || '—'],
    ] : [['', 'ยังไม่มีข้อมูล Delivery']]}},
  ];
  el.innerHTML = sections.map(function(sec) {{
    var rowHtml = sec.rows.map(function(r) {{
      return '<tr><td class="px-4 py-2.5 text-xs font-semibold align-top w-36 whitespace-nowrap" style="color:var(--text-muted)">' + r[0] + '</td>'
           + '<td class="px-4 py-2.5 text-sm" style="color:var(--text)">' + r[1] + '</td></tr>';
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

// ── Boot ──
applyStoredTheme();
showView('view-home');
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

    sidebar_nav = build_sidebar_nav(all_history)
    home_cards = build_home_cards(all_history)
    home_rows = build_home_comparison_rows(all_history)

    platform_views_parts = []
    for platform, raw in all_history.items():
        platform_views_parts.append(build_platform_view(platform, raw))
    platform_views = "\n\n".join(platform_views_parts)

    return HTML_TEMPLATE.format(
        DATA_JSON=data_json,
        COMP_JSON=comp_json,
        PLATFORMS_JSON=platforms_json,
        INTEL_JSON=intel_json,
        GENERATED_AT=generated_at,
        SIDEBAR_NAV_ITEMS=sidebar_nav,
        HOME_CARDS=home_cards,
        HOME_COMPARISON_ROWS=home_rows,
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
    return index_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/generate_dashboard.py <path>")
        print("  <path> = ไฟล์ CSV / folder platform / root sample-data folder")
        sys.exit(1)
    generate_dashboard(sys.argv[1])
