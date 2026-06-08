อัพเดทเฉพาะหน้า "วิเคราะห์เชิงลึก" แล้ว push ขึ้น GitHub

## ขั้นตอน

1. **วิเคราะห์คู่แข่งเชิงลึก 6 มิติ**
   - รัน `/intel-deep` เพื่อวิเคราะห์คู่แข่งทุกร้าน รวมมิติ Delivery Apps

2. **Rebuild + Deploy**
   ```
   python src/generate_dashboard.py sample-data/
   copy dashboard\index.html docs\index.html
   ```

3. **Push ขึ้น GitHub** (log อัปเดตถูกบันทึกโดย `/intel-deep` ในขั้นตอน 1 แล้ว)
   ```
   git add docs/ src/generate_dashboard.py data/competitor-history/ reports/competitor-changes-*.md data/update-log.json
   git commit -m "Deep analysis update — [YYYY-MM-DD]"
   git push
   ```

4. **สรุปใน chat:**
   - คู่แข่งที่เปลี่ยนแปลงมากที่สุด (พร้อม badge 🔴🟡🟢)
   - delivery highlights: ร้านไหนมีโปรใหม่บน delivery apps
   - GitHub Pages URL: `https://pengtangcafe-hash.github.io/my-coffee-social-project/`
